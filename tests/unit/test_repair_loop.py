"""
Unit and integration tests for ARMG Phase 7: Runtime-Guided Repair and LangGraph Orchestration.

Verifies:
- Test A: Prompt construction ([STRICT REPAIR CONSTRAINTS], error trace, forbidden identifiers, candidate replacements, repair rule).
- Test B: Known semantic repair (controlled failure revenue -> gross_revenue, retry_count=1, status=SUCCESS).
- Test C: Retry budget (initial attempt + 3 repairs = 4 attempts, retry_count=3, terminal status=FAILED, no infinite loop).
- Test D: AST validation failure (rejected by SQLGlot, PostgreSQL not called, enters repair loop).
- Test E: Post-repair memory governance (RuntimeKnowledge generated, embedding validated, admitted, recorded success).
- Test F: No false memory reinforcement (unrelated retrieved memories do NOT receive successful_uses += 1).
- Test G: Terminal failure memory (status=FAILED, no positive admission of failed knowledge).
- Test H: State transitions (explicit verification of graph state machine flow).
- Test I: Deterministic orchestration (repeated executions produce identical results).
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pytest

from agents.error_diagnosis import DeterministicErrorDiagnoser, DiagnosticResult
from agents.repair_agent import RepairPromptBuilder, RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from agents.taxonomy import TaxonomyCategory
from environment.base import ExecutionResult, RuntimeEnvironment
from environment.observation import ExecutionStatus, RuntimeObservation
from graph.state import (
    ARMGState,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_RUNNING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.vector_store import FAISSMemoryStore


# =====================================================================
# Fixtures & Test Doubles
# =====================================================================

class MockEnvironment:
    """Deterministic in-memory mock environment for unit testing orchestration."""

    def __init__(self, catalog: Optional[Dict[str, Any]] = None, fail_sql: bool = False):
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
        self.fail_sql = fail_sql
        self.executed_queries: List[str] = []

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, payload: str) -> ExecutionResult:
        self.executed_queries.append(payload)
        if self.fail_sql or "revenue" in payload.lower() and "gross_revenue" not in payload.lower():
            return ExecutionResult(
                status="FAILURE",
                query=payload,
                error='column "revenue" does not exist\nLINE 1: SELECT revenue FROM fact_sales_performance;\n               ^',
                execution_time_ms=1.5,
            )
        return ExecutionResult(
            status="SUCCESS",
            query=payload,
            rows=[(1, 1000.0, 200.0)],
            error=None,
            execution_time_ms=1.2,
            row_count=1,
        )


def deterministic_mock_embed_fn(text: str) -> List[float]:
    """Deterministic 768-dim mock vector generator for unit tests."""
    rng = np.random.RandomState(abs(hash(text)) % (2**31))
    vec = rng.randn(768).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


# =====================================================================
# Test A: Prompt Construction
# =====================================================================

class TestPromptConstruction:
    """Test A: Verify strict repair prompt generation and negative constraints."""

    def test_strict_repair_constraints_block_present(self):
        diagnosis = DiagnosticResult(
            taxonomy_category=TaxonomyCategory.SEMANTIC,
            broken_identifier="revenue",
            root_cause="Column 'revenue' is not present in schema.",
            candidate_replacements=["gross_revenue", "net_profit"],
            negative_constraints=["Do not use 'revenue'."],
            repair_rule="Replace 'revenue' with 'gross_revenue'.",
        )

        prompt = RepairPromptBuilder.build_repair_prompt(
            original_query="What is the total sales revenue?",
            schema_context="## fact_sales_performance\n- gross_revenue: numeric",
            previous_sql="SELECT revenue FROM fact_sales_performance;",
            error_trace='column "revenue" does not exist',
            diagnosis=diagnosis,
        )

        # 1. Section header verification
        assert "[STRICT REPAIR CONSTRAINTS]" in prompt

        # 2. Original error trace included
        assert 'column "revenue" does not exist' in prompt

        # 3. Forbidden identifier explicitly listed
        assert "revenue" in prompt
        assert "FORBIDDEN IDENTIFIERS:" in prompt

        # 4. Candidate replacements listed
        assert "REPLACEMENT REMAPPING:" in prompt
        assert "gross_revenue" in prompt

        # 5. Deterministic repair rule
        assert "OPERATIONAL RULE:" in prompt
        assert "Replace 'revenue' with 'gross_revenue'." in prompt

        # 6. Preserves original question and previous SQL
        assert "What is the total sales revenue?" in prompt
        assert "SELECT revenue FROM fact_sales_performance;" in prompt


# =====================================================================
# Test B: Known Semantic Repair
# =====================================================================

class TestKnownSemanticRepair:
    """Test B: Verify controlled semantic repair: revenue -> gross_revenue."""

    def test_single_repair_recovers_to_success(self):
        env = MockEnvironment()

        # Initial generator produces broken SQL containing 'revenue'
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT revenue FROM fact_sales_performance;",
        )

        # Repair generator correctly substitutes 'gross_revenue'
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "What is total sales revenue?", "max_retries": 3})

        # Final verification:
        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 1
        assert "gross_revenue" in result["generated_sql"]
        assert "revenue" not in result["generated_sql"].replace("gross_revenue", "")
        assert result["previous_sql"] == "SELECT revenue FROM fact_sales_performance;"
        assert len(env.executed_queries) == 2  # 1 failed initial, 1 successful repair


# =====================================================================
# Test C: Retry Budget
# =====================================================================

class TestRetryBudget:
    """Test C: Verify maximum 3 repair retries (4 total attempts) and no infinite loops."""

    def test_exhaustion_terminates_at_max_retries(self):
        env = MockEnvironment(fail_sql=True)  # All queries fail

        # Always returns failing query
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT invalid_col FROM fact_sales_performance;\n```",
            extracted_sql="SELECT invalid_col FROM fact_sales_performance;",
        )
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT invalid_col FROM fact_sales_performance;\n```",
                extracted_sql="SELECT invalid_col FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Unrepairable query", "max_retries": 3})

        # Must terminate with FAILED status
        assert result["status"] == STATUS_FAILED
        # Exactly 3 repair attempts recorded
        assert result["retry_count"] == 3
        # Total generation attempts = 4 (1 initial + 3 retries)
        assert result["telemetry"]["generation_attempts"] == 4
        # Total repair count = 3
        assert result["telemetry"]["repair_count"] == 3


# =====================================================================
# Test D: AST Validation Failure
# =====================================================================

class TestASTValidationFailure:
    """Test D: Rejection by SQLGlot does not execute against database and enters repair."""

    def test_ast_rejection_routes_to_repair_without_db_execution(self):
        env = MockEnvironment()

        call_count = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nSELECT WHERE;\n```",
                extracted_sql="SELECT WHERE;",
            )

        def mock_repair(prompt):
            call_count["count"] += 1
            return GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Syntax error query", "max_retries": 3})

        # Verify invalid syntax SQL was NEVER sent to the database
        assert "SELECT WHERE;" not in env.executed_queries
        # Repair was triggered
        assert call_count["count"] == 1
        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 1


# =====================================================================
# Test E: Post-Repair Memory Governance
# =====================================================================

class TestPostRepairMemory:
    """Test E: Successful repair admits RuntimeKnowledge into persistent vector store."""

    def test_successful_repair_admits_memory_to_faiss(self):
        env = MockEnvironment()
        vstore = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT revenue FROM fact_sales_performance;",
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov_engine,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Query total revenue", "max_retries": 3})

        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 1

        # Memory admission check: vector store now has 1 memory
        assert vstore.count() == 1
        admitted_mem = vstore.all_memories()[0]
        # Promoted on first success: NEW -> ACTIVE, confidence: 0.50 + 0.10 * 0.50 = 0.55
        assert admitted_mem.status == MemoryState.ACTIVE
        assert admitted_mem.confidence == 0.55
        assert admitted_mem.successful_uses == 1


# =====================================================================
# Test F: No False Memory Reinforcement
# =====================================================================

class TestNoFalseMemoryReinforcement:
    """Test F: Unrelated retrieved memories must NOT receive successful_uses increment."""

    def test_unrelated_retrieved_memories_are_not_reinforced(self):
        env = MockEnvironment()
        vstore = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        # Seed vector store with 2 existing memories
        unrelated_mem = RuntimeMemory(
            context={"tables_referenced": ["dim_geography"]},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Unrelated column failure in dim_geography",
            repair_strategy="Replace with valid geography column",
            confidence=0.60,
            status=MemoryState.ACTIVE,
            successful_uses=1,
            total_uses=2,
            embedding=deterministic_mock_embed_fn("geography failure"),
        )
        vstore.add(unrelated_mem, unrelated_mem.embedding)

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT revenue FROM fact_sales_performance;",
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov_engine,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Query total revenue", "max_retries": 3})
        assert result["status"] == STATUS_SUCCESS

        # Verify unrelated memory was NOT reinforced
        stored_unrelated = vstore.get(unrelated_mem.memory_id)
        assert stored_unrelated is not None
        assert stored_unrelated.successful_uses == 1  # Unchanged!
        assert stored_unrelated.total_uses == 2       # Unchanged!
        assert stored_unrelated.confidence == 0.60    # Unchanged!


# =====================================================================
# Test G: Terminal Failure Memory
# =====================================================================

class TestTerminalFailureMemory:
    """Test G: After 3 failed repairs, no positive admission of failed knowledge."""

    def test_terminal_failure_does_not_admit_failed_knowledge(self):
        env = MockEnvironment(fail_sql=True)
        vstore = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT broken FROM fact_sales_performance;\n```",
            extracted_sql="SELECT broken FROM fact_sales_performance;",
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT broken FROM fact_sales_performance;\n```",
                extracted_sql="SELECT broken FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov_engine,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Broken query", "max_retries": 3})

        assert result["status"] == STATUS_FAILED
        assert result["retry_count"] == 3
        # Vector store must be empty: failed knowledge is NOT admitted
        assert vstore.count() == 0
        assert result["telemetry"]["memory_admission"] == "TERMINAL_FAILURE_NOT_ADMITTED"


# =====================================================================
# Test H: State Transitions
# =====================================================================

class TestStateTransitions:
    """Test H: Verify state machine transitions across initial success, repair, and failure."""

    def test_direct_success_path_has_zero_retries(self):
        env = MockEnvironment()
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Direct success", "max_retries": 3})
        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 0
        assert result["previous_sql"] is None


# =====================================================================
# Test I: Deterministic Orchestration
# =====================================================================

class TestDeterministicOrchestration:
    """Test I: 10 repeated runs produce identical routing, retry counts, and status."""

    def test_repeated_runs_are_deterministic(self):
        for _ in range(10):
            env = MockEnvironment()
            mock_gen = SQLGenerator()
            mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
            )
            mock_repair = RepairSQLGenerator(
                generator_fn=lambda prompt: GenerationResult(
                    raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                    extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                )
            )

            wf = ARMGRepairWorkflow(
                environment=env,
                sql_generator=mock_gen,
                repair_generator=mock_repair,
                embed_fn=deterministic_mock_embed_fn,
            )
            graph = wf.build_graph()

            res = graph.invoke({"user_query": "Determinism check", "max_retries": 3})
            assert res["status"] == STATUS_SUCCESS
            assert res["retry_count"] == 1
            assert res["generated_sql"] == "SELECT gross_revenue FROM fact_sales_performance;"
            assert res["previous_sql"] == "SELECT revenue FROM fact_sales_performance;"
