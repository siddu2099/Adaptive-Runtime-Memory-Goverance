"""
ARMG Phase 12: Natural-Language Intent Safety Gate Test Suite.

Verifies:
- Test 1: Standalone deterministic IntentClassifier unit tests across all 4 decision classes:
  (BLOCK, ALLOW, ALLOW_EXPLANATION, AMBIGUOUS).
- Test A: Explicit destructive requests blocked before initial Ollama generation with:
  0 Ollama calls, 0 SQL candidates, 0 SQLGlot evaluations, 0 PostgreSQL calls, 0 repair retries,
  terminal STATUS_BLOCKED, block_reason="DESTRUCTIVE_INTENT_DETECTED", decision_source="natural_language_intent_gate".
- Test B: Benign mentions, educational questions, logging, and negated instructions allowed without false positive blocks.
- Test C: Ambiguity handling: conflicting or uncertain requests halt safely with AMBIGUOUS_INTENT_CLARIFICATION_REQUIRED.
- Test D: Ordinary analytical requests pass intent gate and execute through normal workflow.
- Test E: PostgreSQL error diagnosis and bounded repair isolation (real errors remain distinguishable from safety blocks).
- Test F: Manual SQL override compatibility and documented precedence rules:
  - Destructive NL request + manual override -> blocked by Intent Gate (decision_source="natural_language_intent_gate").
  - Benign NL request + destructive manual override -> passed by Intent Gate, blocked by AST Guard (decision_source="ast_guard").
- Test G: Telemetry, timing, attempts_trace, and dashboard audit trail consistency.
"""

from typing import Any, Dict, List, Optional
import pytest

from agents.sql_generator import GenerationResult, SQLGenerator
from agents.repair_agent import RepairSQLGenerator
from environment.base import ExecutionResult
from graph.state import (
    ARMGState,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore
from validation.intent_classifier import (
    IntentClassifier,
    IntentDecision,
    classify_natural_language_intent,
)


class SpyEnvironment:
    """Mock database environment tracking query executions and inspecting schema."""

    def __init__(self, catalog: Optional[Dict[str, Any]] = None):
        self.catalog = catalog or {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer", "is_pk": True},
                        {"name": "gross_revenue", "type": "numeric", "is_pk": False},
                        {"name": "net_profit", "type": "numeric", "is_pk": False},
                    ]
                },
                "dim_geography": {
                    "columns": [
                        {"name": "geo_key", "type": "integer", "is_pk": True},
                        {"name": "region", "type": "varchar", "is_pk": False},
                    ]
                },
            }
        }
        self.call_count: int = 0
        self.inspect_call_count: int = 0
        self.executed_queries: List[str] = []

    def inspect(self) -> Dict[str, Any]:
        self.inspect_call_count += 1
        return self.catalog

    def execute(self, sql: str) -> ExecutionResult:
        self.call_count += 1
        self.executed_queries.append(sql)
        if "nonexistent_col" in sql.lower():
            return ExecutionResult(
                status="FAILURE",
                query=sql,
                error='column "nonexistent_col" does not exist\nLINE 1: SELECT nonexistent_col FROM fact_sales_performance;\n               ^',
                execution_time_ms=1.5,
            )
        return ExecutionResult(
            status="SUCCESS",
            query=sql,
            rows=[("North", 50000.0)],
            row_count=1,
            execution_time_ms=2.1,
        )


class SpySQLGenerator:
    """Mock SQL generator counting initial generation invocations."""

    def __init__(self, return_sql: str = "SELECT region, SUM(gross_revenue) FROM fact_sales_performance GROUP BY region;"):
        self.return_sql = return_sql
        self.generation_count: int = 0

    def generate(self, question: str, schema_markdown: str) -> GenerationResult:
        self.generation_count += 1
        return GenerationResult(
            raw_response=f"```sql\n{self.return_sql}\n```",
            extracted_sql=self.return_sql,
            prompt_tokens=150,
            completion_tokens=25,
            generation_duration_ms=45.0,
        )


# =============================================================================
# Test 1: Standalone IntentClassifier Unit Tests
# =============================================================================

class TestIntentClassifierUnit:
    """Verify deterministic regex classification logic and decision outcomes."""

    def setup_method(self):
        self.classifier = IntentClassifier()

    @pytest.mark.parametrize("query", [
        "Permanently drop the fact_sales_performance table and remove all dependent objects.",
        "Permanently drop the fact_sales_performance table.",
        "Delete every row from fact_sales_performance.",
        "Truncate the fact_sales_performance table.",
        "DROP TABLE dim_geography CASCADE;",
        "TRUNCATE fact_sales_performance;",
        "Wipe all records from the customer table.",
        "Destroy the database schema entirely.",
        "Purge all data from fact_sales_performance.",
        "ALTER TABLE fact_sales_performance DROP COLUMN net_profit;",
    ])
    def test_explicit_destructive_requests_classified_as_block(self, query: str):
        res = self.classifier.classify(query)
        assert res.decision == IntentDecision.BLOCK
        assert res.operation_type is not None
        assert res.matched_pattern is not None

    @pytest.mark.parametrize("query", [
        "Explain what DROP TABLE means in SQL.",
        "How can I prevent accidental database table deletion?",
        "Check whether any DROP TABLE statements exist in these logs.",
        "What is the total gross revenue by region?",
        "Do not drop the fact_sales_performance table.",
        "Never delete any records from fact_sales.",
        "Is there any DROP keyword in this documentation?",
        "How does PostgreSQL handle table deletion internally?",
    ])
    def test_benign_and_explanation_requests_not_blocked(self, query: str):
        res = self.classifier.classify(query)
        assert res.decision in (IntentDecision.ALLOW, IntentDecision.ALLOW_EXPLANATION)
        assert res.decision != IntentDecision.BLOCK

    @pytest.mark.parametrize("query", [
        "Drop the table but actually show me the gross revenue.",
        "Should I drop the fact_sales_performance table?",
        "Please delete the rows unless you think we should keep them.",
    ])
    def test_ambiguous_and_conflicting_requests(self, query: str):
        res = self.classifier.classify(query)
        assert res.decision in (IntentDecision.AMBIGUOUS, IntentDecision.ALLOW_EXPLANATION)
        assert res.decision != IntentDecision.ALLOW


# =============================================================================
# Test A: Explicit Destructive Requests Blocked in Real Workflow
# =============================================================================

class TestWorkflowDestructiveRequestsBlocked:
    """Test A: Prove blocked requests result in ZERO model calls, candidates, AST evals, and DB calls."""

    @pytest.mark.parametrize("destructive_query", [
        "Permanently drop the fact_sales_performance table and remove all dependent objects.",
        "Delete every row from fact_sales_performance.",
        "Truncate the fact_sales_performance table.",
        "ALTER TABLE fact_sales_performance DROP COLUMN gross_revenue;",
    ])
    def test_confirmed_block_service_counts_and_state(self, destructive_query: str):
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator()
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=sql_gen,
            vector_store=vstore,
            governance_engine=gov,
        )
        app = wf.build_graph()

        initial_state: ARMGState = {
            "user_query": destructive_query,
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }

        final_state = app.invoke(initial_state)

        # 1. State assertions
        assert final_state["status"] == STATUS_BLOCKED
        assert final_state.get("decision_source") == "natural_language_intent_gate"
        assert final_state.get("block_reason") == "DESTRUCTIVE_INTENT_DETECTED"
        assert final_state.get("intent_decision") == "BLOCK"
        assert final_state.get("generated_sql") is None
        assert final_state.get("execution_result") is None
        assert final_state.get("diagnosis") is None
        assert final_state.get("runtime_knowledge") is None

        # 2. Service-call counts (Execution proof)
        assert sql_gen.generation_count == 0, "Ollama SQL Generator must NEVER be called for blocked intent."
        assert env.call_count == 0, "PostgreSQL Executor must NEVER be called for blocked intent."
        assert env.inspect_call_count == 0, "PostgreSQL schema inspection must NEVER occur before or for blocked intent."

        # 3. Telemetry accounting
        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("intent_gate_evaluations") == 1
        assert telemetry.get("ollama_generation_attempts") == 0
        assert telemetry.get("generation_attempts") == 0
        assert telemetry.get("sql_execution_attempts") == 0
        assert telemetry.get("sql_candidate_evaluations") == 0
        assert telemetry.get("postgres_executor_calls") == 0
        assert telemetry.get("repair_count") == 0
        assert telemetry.get("memory_admission") == "SAFETY_VIOLATION_BLOCKED"
        assert telemetry.get("intent_gate_duration_ms", 0.0) >= 0.0
        assert telemetry.get("generation_latency_ms") == 0.0
        assert telemetry.get("validation_latency_ms") == 0.0
        assert telemetry.get("execution_latency_ms") == 0.0

        # 4. Zero memory admissions or store size changes
        assert vstore.count() == 0


# =============================================================================
# Test B & D: Permitted Queries Continue Through Real Workflow
# =============================================================================

class TestWorkflowPermittedExecution:
    """Test B & D: Verify benign queries reach Ollama generation and PostgreSQL execution."""

    def test_ordinary_analytical_query_executes_successfully(self):
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator(return_sql="SELECT region, SUM(gross_revenue) FROM fact_sales_performance GROUP BY region;")
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=sql_gen,
        )
        app = wf.build_graph()

        state: ARMGState = {
            "user_query": "What is the total gross revenue by region?",
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        assert res["status"] == STATUS_SUCCESS
        assert res.get("intent_decision") == "ALLOW"
        assert sql_gen.generation_count == 1
        assert env.call_count == 1
        assert env.inspect_call_count >= 1
        assert res["generated_sql"] == "SELECT region, SUM(gross_revenue) FROM fact_sales_performance GROUP BY region;"

        tel = res["telemetry"]
        assert tel.get("intent_gate_evaluations") == 1
        assert tel.get("ollama_generation_attempts") == 1
        assert tel.get("sql_candidate_evaluations") == 1
        assert tel.get("postgres_executor_calls") == 1

    @pytest.mark.parametrize("benign_query", [
        "Explain what DROP TABLE means in SQL.",
        "How can I prevent accidental database table deletion?",
        "Check whether any DROP TABLE statements exist in these logs.",
        "Do not drop the fact_sales_performance table.",
    ])
    def test_explanation_and_preventative_queries_reach_generator(self, benign_query: str):
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator(return_sql="SELECT 1 AS explanation;")
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=sql_gen,
        )
        app = wf.build_graph()

        state: ARMGState = {
            "user_query": benign_query,
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        # Gate must allow explanation to proceed to generation
        assert res.get("intent_decision") in ("ALLOW", "ALLOW_EXPLANATION")
        assert sql_gen.generation_count == 1


# =============================================================================
# Test C: Safe Ambiguity Handling
# =============================================================================

class TestWorkflowAmbiguityHandling:
    """Test C: Ambiguous requests halt safely with clarification required."""

    def test_conflicting_instructions_halt_safely(self):
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator()
        wf = ARMGRepairWorkflow(environment=env, sql_generator=sql_gen)
        app = wf.build_graph()

        ambiguous_query = "Drop the table but actually show me the gross revenue."
        state: ARMGState = {
            "user_query": ambiguous_query,
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        # Safely stops execution with clarification required
        assert res["status"] == STATUS_BLOCKED
        assert res.get("decision_source") == "natural_language_intent_gate"
        assert res.get("block_reason") == "AMBIGUOUS_INTENT_CLARIFICATION_REQUIRED"
        assert res.get("intent_decision") == "AMBIGUOUS"

        # Proves 0 executions occurred
        assert sql_gen.generation_count == 0
        assert env.call_count == 0
        assert env.inspect_call_count == 0, "PostgreSQL schema inspection must NEVER occur for ambiguous intent."


# =============================================================================
# Test E: PostgreSQL Database Errors & Bounded Repair Preserved
# =============================================================================

class TestWorkflowDatabaseErrorsAndRepair:
    """Test E: Genuine database failures remain distinguishable from safety blocks."""

    def test_database_error_distinguishable_from_intent_block(self):
        env = SpyEnvironment()
        # Generator generates SQL referencing a non-existent column
        sql_gen = SpySQLGenerator(return_sql="SELECT nonexistent_col FROM fact_sales_performance;")
        wf = ARMGRepairWorkflow(environment=env, sql_generator=sql_gen)
        app = wf.build_graph()

        state: ARMGState = {
            "user_query": "What is the nonexistent column value?",
            "max_retries": 0,  # Zero-retry budget: fails immediately
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        assert res["status"] == STATUS_FAILED
        assert res.get("decision_source") is None  # Not a safety block
        assert env.call_count == 1
        assert res["execution_result"] is not None
        assert res["execution_result"].is_success is False
        assert 'column "nonexistent_col" does not exist' in res["execution_result"].error


# =============================================================================
# Test F: Manual SQL Override Precedence & AST Guard Independence
# =============================================================================

class TestWorkflowManualOverridePrecedence:
    """Test F: Verify precedence policy between Natural Language Intent and Manual Override."""

    def test_destructive_nl_query_with_safe_override_blocks_at_intent_gate(self):
        """Precedence Rule: Destructive NL intent blocks even if user typed SELECT in override box."""
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator()
        wf = ARMGRepairWorkflow(environment=env, sql_generator=sql_gen)
        app = wf.build_graph()

        state: ARMGState = {
            "user_query": "Permanently drop the fact_sales_performance table and remove all dependent objects.",
            "initial_sql_override": "SELECT gross_revenue FROM fact_sales_performance;",
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        # 1. Blocked by Intent Gate (not AST Guard)
        assert res["status"] == STATUS_BLOCKED
        assert res.get("decision_source") == "natural_language_intent_gate"
        assert res.get("block_reason") == "DESTRUCTIVE_INTENT_DETECTED"

        # 2. Both inputs preserved in state
        assert res["user_query"] == "Permanently drop the fact_sales_performance table and remove all dependent objects."
        assert res["initial_sql_override"] == "SELECT gross_revenue FROM fact_sales_performance;"

        # 3. Neither model generation nor database execution executed
        assert sql_gen.generation_count == 0
        assert env.call_count == 0
        assert env.inspect_call_count == 0, "Precedence rule must halt before any DB connection or inspection."
        assert res.get("telemetry", {}).get("sql_candidate_evaluations") == 0

    def test_benign_nl_query_with_destructive_override_blocks_at_ast_guard(self):
        """Independence Rule: Benign NL intent with unsafe override is blocked by SQLGlot AST guard."""
        env = SpyEnvironment()
        sql_gen = SpySQLGenerator()
        wf = ARMGRepairWorkflow(environment=env, sql_generator=sql_gen)
        app = wf.build_graph()

        state: ARMGState = {
            "user_query": "What is the total gross revenue?",
            "initial_sql_override": "DROP TABLE fact_sales_performance CASCADE;",
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)

        # 1. Passed Intent Gate, blocked by AST Guard
        assert res["status"] == STATUS_BLOCKED
        assert res.get("decision_source") == "ast_guard"
        assert res.get("block_reason") == "AST_SAFETY_VIOLATION"
        assert res.get("is_safety_violation") is True
        assert res.get("safety_category") == "destructive_mutation"

        # 2. Exact override preserved
        assert res["initial_sql_override"] == "DROP TABLE fact_sales_performance CASCADE;"
        assert res["generated_sql"] == "DROP TABLE fact_sales_performance CASCADE;"

        # 3. Model bypassed, AST evaluated once, DB executor never called
        assert sql_gen.generation_count == 0
        assert env.call_count == 0
        assert res.get("telemetry", {}).get("sql_candidate_evaluations") == 1
        assert res.get("telemetry", {}).get("postgres_executor_calls") == 0


# =============================================================================
# Test G: Telemetry & Dashboard Consistency
# =============================================================================

class TestTelemetryAndDashboardConsistency:
    """Test G: Confirm metrics, trace, timings, and decision sources are mutually consistent."""

    def test_intent_blocked_telemetry_consistency(self):
        env = SpyEnvironment()
        wf = ARMGRepairWorkflow(environment=env)
        app = wf.build_graph()

        q = "Permanently drop the fact_sales_performance table."
        state: ARMGState = {
            "user_query": q,
            "max_retries": 3,
            "retry_count": 0,
            "telemetry": {},
        }
        res = app.invoke(state)
        tel = res["telemetry"]

        # 1. Lifecycle counters
        assert tel["intent_gate_evaluations"] == 1
        assert tel["ollama_generation_attempts"] == 0
        assert tel["generation_attempts"] == 0
        assert tel["sql_execution_attempts"] == 0
        assert tel["sql_candidate_evaluations"] == 0
        assert tel["postgres_executor_calls"] == 0
        assert tel["repair_count"] == 0

        # 2. Timing
        assert tel["intent_gate_duration_ms"] >= 0.0
        assert tel["generation_latency_ms"] == 0.0
        assert tel["validation_latency_ms"] == 0.0
        assert tel["execution_latency_ms"] == 0.0
        assert tel["total_latency_ms"] == tel["intent_gate_duration_ms"]

        # 3. Attempts trace must be empty (0 SQL candidate attempts)
        assert tel.get("attempts_trace") is None or len(tel["attempts_trace"]) == 0


# =============================================================================
# Test H: Streamlit Live Dashboard Rendering Integration
# =============================================================================

class TestStreamlitIntentGateDashboard:
    """Verify live Streamlit UI rendering of intent gate blocks vs AST blocks."""

    def test_streamlit_destructive_nl_query_renders_intent_gate_block(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest

        dashboard_path = str(Path(__file__).resolve().parent.parent.parent / "ui" / "dashboard.py")
        at = AppTest.from_file(dashboard_path).run(timeout=30)
        assert len(at.exception) == 0

        # Submit observed failure request from Section 1
        destructive_q = "Permanently drop the fact_sales_performance table and remove all dependent objects."
        at.text_area(key="query_input_text").input(destructive_q).run(timeout=30)
        at.text_area(key="sql_override_text").input("").run(timeout=30)
        at.button[0].click().run(timeout=30)

        assert len(at.exception) == 0
        last_state = at.session_state["last_execution_state"]
        assert last_state is not None
        assert last_state["status"] == STATUS_BLOCKED
        assert last_state.get("decision_source") == "natural_language_intent_gate"
        assert last_state.get("block_reason") == "DESTRUCTIVE_INTENT_DETECTED"

        # Verify dashboard banner and cards
        markdown_vals = [m.value for m in at.markdown]
        error_vals = [e.value for e in at.error]
        assert any("Execution permanently prevented by Natural-Language Intent Gate" in e for e in error_vals)
        assert any("SQL Generation — BYPASSED" in m for m in markdown_vals)
        assert any("INTENT SAFETY GATE**: BLOCKED" in e for e in error_vals)

        # 0 Ollama calls, 0 PG calls
        tel = last_state.get("telemetry", {})
        assert tel.get("ollama_generation_attempts") == 0
        assert tel.get("postgres_executor_calls") == 0

    def test_streamlit_ambiguous_query_renders_clarification_required(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest

        dashboard_path = str(Path(__file__).resolve().parent.parent.parent / "ui" / "dashboard.py")
        at = AppTest.from_file(dashboard_path).run(timeout=30)
        assert len(at.exception) == 0

        ambiguous_q = "Drop the table but actually show me the gross revenue."
        at.text_area(key="query_input_text").input(ambiguous_q).run(timeout=30)
        at.text_area(key="sql_override_text").input("").run(timeout=30)
        at.button[0].click().run(timeout=30)

        assert len(at.exception) == 0
        last_state = at.session_state["last_execution_state"]
        assert last_state is not None
        assert last_state["status"] == STATUS_BLOCKED
        assert last_state.get("decision_source") == "natural_language_intent_gate"
        assert last_state.get("block_reason") == "AMBIGUOUS_INTENT_CLARIFICATION_REQUIRED"

        warning_vals = [w.value for w in at.warning]
        assert any("STATUS: CLARIFICATION REQUIRED" in w for w in warning_vals)

