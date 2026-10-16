"""
Unit and Contract Tests for Manual Initial SQL Override, Safety Blocking, and Trace Consistency.

Implements required regression suite conforming strictly to Phase 5 specification:
- Test A: Valid manual SQL override (exact SQL, no initial Ollama generation, actual guard & execution).
- Test B: Invalid-column override with zero retries (exact SQL, genuine DB error, STATUS_FAILED, 0 Ollama calls, 0 retries).
- Test C: Empty override with ordinary generation (normal Ollama generation path, AST guard, consistent trace).
- Test D: Destructive SQL override (DROP TABLE blocked before DB executor, STATUS_BLOCKED, 0 Ollama calls, no repair).
- Test E: Input, retry state across reruns, and leakage prevention in Streamlit AppTest.
- Test F: Trace, attempt count, and telemetry consistency across all four principal execution paths.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
from streamlit.testing.v1 import AppTest

from agents.sql_generator import GenerationResult
from benchmark.modes import create_initial_armg_state
from environment.base import ExecutionResult
from graph.state import STATUS_BLOCKED, STATUS_FAILED, STATUS_RETRYING, STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow


class MockTestEnvironment:
    """Mock database environment for testing manual override workflows with exact execution accounting."""

    def __init__(self, fail_first_attempt: bool = False):
        self.catalog = {
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
        self.fail_first_attempt = fail_first_attempt
        self.call_count = 0
        self.executed_queries: List[str] = []

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, sql: str) -> ExecutionResult:
        self.call_count += 1
        self.executed_queries.append(sql)
        if self.fail_first_attempt and self.call_count == 1:
            return ExecutionResult(
                status="FAILURE",
                query=sql,
                error='column "revenue" does not exist\nLINE 1: SELECT ... f.revenue ...\n                     ^',
                execution_time_ms=1.5,
            )
        if "unmapped_metric" in sql:
            return ExecutionResult(
                status="FAILURE",
                query=sql,
                error='column "unmapped_metric" does not exist\nLINE 1: SELECT unmapped_metric FROM fact_sales_performance;\n               ^',
                execution_time_ms=1.2,
            )
        rows = [(15000.0,)] if "region" not in sql.lower() else [("North", 15000.0)]
        return ExecutionResult(
            status="SUCCESS",
            query=sql,
            rows=rows,
            error=None,
            execution_time_ms=1.1,
            row_count=1,
        )


class MockRepairGenerator:
    """Mock generator tracking generation calls and returning configured SQL."""

    def __init__(self, repair_sql: str = "SELECT 1;", prompt_tokens: int = 300, completion_tokens: int = 40):
        self.repair_sql = repair_sql
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.initial_calls = 0
        self.repair_calls = 0

    def generate(self, question: str, schema_markdown: str) -> GenerationResult:
        self.initial_calls += 1
        return GenerationResult(
            raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            prompt_tokens=100,
            completion_tokens=20,
            generation_duration_ms=50.0,
        )

    def generate_repair(self, repair_prompt: str) -> GenerationResult:
        self.repair_calls += 1
        return GenerationResult(
            raw_response=f"```sql\n{self.repair_sql}\n```",
            extracted_sql=self.repair_sql,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            generation_duration_ms=120.0,
        )


# =============================================================================
# Test A: Valid manual SQL override
# =============================================================================

def test_test_a_valid_manual_sql_override():
    """Test A: Valid read-only SQL override bypasses initial Ollama generation and executes directly."""
    env = MockTestEnvironment(fail_first_attempt=False)
    gen = MockRepairGenerator(repair_sql="SELECT 1;")
    workflow = ARMGRepairWorkflow(environment=env, sql_generator=gen, repair_generator=gen)
    app = workflow.build_graph()

    override_sql = "SELECT gross_revenue FROM fact_sales_performance;"
    state = create_initial_armg_state(
        user_query="What is gross revenue?",
        initial_sql_override=override_sql,
        max_retries=3,
    )
    final_state = app.invoke(state)

    # 1. Exact override reaches workflow and is executed
    assert final_state["status"] == STATUS_SUCCESS
    assert final_state["generated_sql"] == override_sql
    assert final_state["initial_sql_override"] == override_sql

    # 2. No initial Ollama generation occurred
    assert gen.initial_calls == 0
    assert gen.repair_calls == 0

    # 3. Guard passed and executor received expected SQL with matching returned rows
    assert final_state["validation_passed"] is True
    assert env.call_count == 1
    assert env.executed_queries == [override_sql]
    assert final_state["execution_result"] is not None
    assert final_state["execution_result"].rows == [(15000.0,)]
    assert len(final_state["execution_result"].rows[0]) == 1

    # 4. Telemetry and trace describe the same execution
    telemetry = final_state.get("telemetry", {})
    assert telemetry.get("sql_execution_attempts") == 1
    assert telemetry.get("sql_candidate_evaluations") == 1
    assert telemetry.get("postgres_executor_calls") == 1
    assert telemetry.get("ollama_generation_attempts") == 0
    assert telemetry.get("generation_attempts") == 0
    assert telemetry.get("prompt_tokens") is None
    assert telemetry.get("completion_tokens") is None
    assert telemetry.get("total_tokens") is None
    assert telemetry.get("generation_latency_ms") == 0.0

    trace = telemetry.get("attempts_trace", [])
    assert len(trace) == 1
    assert trace[0]["is_manual_override"] is True
    assert trace[0]["sql"] == override_sql
    assert trace[0]["ast_valid"] is True
    assert trace[0]["executed_in_db"] is True
    assert trace[0]["exec_success"] is True


# =============================================================================
# Test B: Invalid-column override, zero retries
# =============================================================================

def test_test_b_invalid_column_override_zero_retries():
    """Test B: Invalid-column override with retries=0 terminates as STATUS_FAILED with 0 model generations."""
    env = MockTestEnvironment(fail_first_attempt=False)
    gen = MockRepairGenerator(repair_sql="SELECT 1;")
    workflow = ARMGRepairWorkflow(environment=env, sql_generator=gen, repair_generator=gen)
    app = workflow.build_graph()

    override_sql = "SELECT unmapped_metric FROM fact_sales_performance;"
    state = create_initial_armg_state(
        user_query="What is the unmapped metric across transactions?",
        initial_sql_override=override_sql,
        max_retries=0,
    )
    final_state = app.invoke(state)

    # 1. Exact override used as candidate
    assert final_state["status"] == STATUS_FAILED
    assert final_state["generated_sql"] == override_sql
    assert final_state["initial_sql_override"] == override_sql

    # 2. No initial or repair Ollama generation occurred
    assert gen.initial_calls == 0
    assert gen.repair_calls == 0

    # 3. Guard passed, database executor called exactly once with the invalid query
    assert final_state["validation_passed"] is True
    assert env.call_count == 1
    assert env.executed_queries == [override_sql]

    # 4. Genuine error preserved
    exec_res = final_state.get("execution_result")
    assert exec_res is not None
    assert exec_res.is_success is False
    assert 'column "unmapped_metric" does not exist' in exec_res.error

    # 5. Telemetry & accounting: retries=0, ollama_generations=0, sql_attempts=1
    telemetry = final_state.get("telemetry", {})
    assert final_state.get("retry_count") == 0
    assert telemetry.get("sql_execution_attempts") == 1
    assert telemetry.get("sql_candidate_evaluations") == 1
    assert telemetry.get("postgres_executor_calls") == 1
    assert telemetry.get("ollama_generation_attempts") == 0
    assert telemetry.get("generation_attempts") == 0
    assert telemetry.get("prompt_tokens") is None
    assert telemetry.get("completion_tokens") is None
    assert telemetry.get("total_tokens") is None
    assert telemetry.get("memory_admission") == "TERMINAL_FAILURE_NOT_ADMITTED"

    trace = telemetry.get("attempts_trace", [])
    assert len(trace) == 1
    assert trace[0]["is_manual_override"] is True
    assert trace[0]["sql"] == override_sql
    assert trace[0]["executed_in_db"] is True
    assert trace[0]["exec_success"] is False
    assert 'column "unmapped_metric" does not exist' in trace[0]["exec_error"]


# =============================================================================
# Test C: Empty override, ordinary generation
# =============================================================================

def test_test_c_empty_override_ordinary_generation():
    """Test C: Empty override triggers normal initial Ollama generation and validation path."""
    env = MockTestEnvironment(fail_first_attempt=False)
    gen = MockRepairGenerator(repair_sql="SELECT 1;")
    workflow = ARMGRepairWorkflow(environment=env, sql_generator=gen, repair_generator=gen)
    app = workflow.build_graph()

    # Empty override (None or whitespace)
    state = create_initial_armg_state(
        user_query="What is gross revenue?",
        initial_sql_override="",
        max_retries=3,
    )
    final_state = app.invoke(state)

    assert final_state["status"] == STATUS_SUCCESS
    # Initial Ollama generation was called
    assert gen.initial_calls == 1
    assert gen.repair_calls == 0
    assert env.call_count == 1

    telemetry = final_state.get("telemetry", {})
    assert telemetry.get("sql_execution_attempts") == 1
    assert telemetry.get("sql_candidate_evaluations") == 1
    assert telemetry.get("postgres_executor_calls") == 1
    assert telemetry.get("ollama_generation_attempts") == 1
    assert telemetry.get("generation_attempts") == 1
    assert telemetry.get("prompt_tokens") == 100
    assert telemetry.get("completion_tokens") == 20
    assert telemetry.get("total_tokens") == 120

    trace = telemetry.get("attempts_trace", [])
    assert len(trace) == 1
    assert trace[0]["is_manual_override"] is False
    assert trace[0]["is_repair"] is False
    assert trace[0]["prompt_tokens"] == 100


# =============================================================================
# Test D: Destructive SQL override
# =============================================================================

def test_test_d_destructive_sql_override():
    """Test D: Destructive SQL is blocked by AST guard before PostgreSQL execution with 0 model calls."""
    env = MockTestEnvironment(fail_first_attempt=False)
    gen = MockRepairGenerator(repair_sql="SELECT 1;")
    workflow = ARMGRepairWorkflow(environment=env, sql_generator=gen, repair_generator=gen)
    app = workflow.build_graph()

    unsafe_sql = "DROP TABLE fact_sales_performance CASCADE;"
    state = create_initial_armg_state(
        user_query="What is the gross revenue?",
        initial_sql_override=unsafe_sql,
        max_retries=3,
    )
    final_state = app.invoke(state)

    # 1. Final state is STATUS_BLOCKED
    assert final_state["status"] == STATUS_BLOCKED
    assert final_state["is_safety_violation"] is True
    assert final_state["safety_category"] == "destructive_mutation"
    assert "drop" in (final_state.get("validation_error") or "").lower()

    # 2. Database executor was NEVER called
    assert env.call_count == 0
    assert len(env.executed_queries) == 0

    # 3. No Ollama calls occurred
    assert gen.initial_calls == 0
    assert gen.repair_calls == 0

    # 4. No memory admission
    telemetry = final_state.get("telemetry", {})
    assert telemetry.get("sql_execution_attempts") == 1
    assert telemetry.get("sql_candidate_evaluations") == 1
    assert telemetry.get("postgres_executor_calls") == 0
    assert telemetry.get("ollama_generation_attempts") == 0
    assert telemetry.get("memory_admission") == "SAFETY_VIOLATION_BLOCKED"
    # Timing consistency: total latency must reflect measured AST validation duration
    assert telemetry.get("validation_latency_ms", 0.0) >= 0.0
    assert telemetry.get("total_latency_ms", 0.0) >= telemetry.get("validation_latency_ms", 0.0)

    # 5. Trace records safety rejection without DB execution
    trace = telemetry.get("attempts_trace", [])
    assert len(trace) == 1
    assert trace[0]["is_manual_override"] is True
    assert trace[0]["ast_valid"] is False
    assert trace[0]["is_safety_violation"] is True
    assert trace[0].get("executed_in_db") is not True


# =============================================================================
# Test E: Input and retry state across reruns & leakage prevention (AppTest)
# =============================================================================

def test_test_e_streamlit_rerun_and_leakage_prevention():
    """Test E: AppTest verifies form submission atomicity, override retention, and leakage prevention."""
    dashboard_path = str(Path(__file__).resolve().parent.parent.parent / "ui" / "dashboard.py")
    at = AppTest.from_file(dashboard_path).run(timeout=30)
    assert len(at.exception) == 0

    # Case 1: Enter query, override, retries=0, submit form
    at.text_area(key="query_input_text").input("What is the unmapped metric across transactions?").run(timeout=30)
    at.text_area(key="sql_override_text").input("SELECT unmapped_metric FROM fact_sales_performance;").run(timeout=30)
    at.number_input(key="max_retries_input").set_value(0).run(timeout=30)

    # Verify inputs survived rerun
    assert at.text_area(key="query_input_text").value == "What is the unmapped metric across transactions?"
    assert at.text_area(key="sql_override_text").value == "SELECT unmapped_metric FROM fact_sales_performance;"
    assert at.number_input(key="max_retries_input").value == 0

    # Submit form
    at.button[0].click().run(timeout=30)
    assert len(at.exception) == 0

    last_state = at.session_state["last_execution_state"]
    assert last_state is not None
    assert last_state["status"] == STATUS_FAILED
    assert last_state["initial_sql_override"] == "SELECT unmapped_metric FROM fact_sales_performance;"
    assert last_state["max_retries"] == 0
    assert last_state["telemetry"]["ollama_generation_attempts"] == 0
    # Requirement D: Verify post-submission execution-source indicator for manual override
    markdown_vals_case1 = [m.value for m in at.markdown]
    assert any("Initial SQL source:** `Manual override`" in m for m in markdown_vals_case1)

    # Case 2: Clearing the override and submitting an ordinary question restores normal generation path
    at.text_area(key="sql_override_text").input("").run(timeout=30)
    assert at.text_area(key="sql_override_text").value == ""

    # Select an analytical query example from selectbox
    at.selectbox(key="sample_query_select").select("What is the total gross revenue?").run(timeout=30)
    # The callback should have synced query_input_text and cleared sql_override_text
    assert at.text_area(key="query_input_text").value == "What is the total gross revenue?"
    assert at.text_area(key="sql_override_text").value == ""

    # Submit with empty override
    at.button[0].click().run(timeout=30)
    assert len(at.exception) == 0

    new_state = at.session_state["last_execution_state"]
    assert new_state is not None
    # No override in payload or initial state
    assert new_state.get("initial_sql_override") is None or new_state.get("initial_sql_override") == ""
    # Ran through Ollama generation
    assert new_state["telemetry"]["ollama_generation_attempts"] >= 1
    # Requirement D: Verify post-submission execution-source indicator for Ollama generation
    markdown_vals_case2 = [m.value for m in at.markdown]
    assert any("Initial SQL source:** `Ollama generation`" in m for m in markdown_vals_case2)


# =============================================================================
# Test F: Trace and telemetry consistency across all principal paths
# =============================================================================

def test_test_f_trace_and_telemetry_consistency_across_all_paths():
    """Test F: Assert strict internal consistency between state, attempts_trace, and telemetry."""
    env = MockTestEnvironment(fail_first_attempt=True)
    repaired_sql = "SELECT gross_revenue FROM fact_sales_performance;"
    gen = MockRepairGenerator(repair_sql=repaired_sql, prompt_tokens=250, completion_tokens=35)
    workflow = ARMGRepairWorkflow(environment=env, sql_generator=gen, repair_generator=gen)
    app = workflow.build_graph()

    # Principal Path 1: Successful repair from manual SQL override
    invalid_sql = "SELECT revenue FROM fact_sales_performance;"
    state_repair = create_initial_armg_state(
        user_query="What is revenue?",
        initial_sql_override=invalid_sql,
        max_retries=3,
    )
    res_repair = app.invoke(state_repair)
    tel = res_repair["telemetry"]
    trace = tel["attempts_trace"]

    assert res_repair["status"] == STATUS_SUCCESS
    assert res_repair["retry_count"] == 1
    assert tel["sql_execution_attempts"] == 2
    assert tel["sql_candidate_evaluations"] == 2
    assert tel["postgres_executor_calls"] == 2
    assert tel["ollama_generation_attempts"] == 1
    assert len(trace) == 2
    assert trace[0]["is_manual_override"] is True
    assert trace[0]["exec_success"] is False
    assert trace[1]["is_repair"] is True
    assert trace[1]["exec_success"] is True
    assert tel["prompt_tokens"] == 250
    assert tel["completion_tokens"] == 35
    assert tel["total_tokens"] == 285

    # Principal Path 2: Invalid column with max_retries = 0
    state_fail = create_initial_armg_state(
        user_query="What is unmapped?",
        initial_sql_override="SELECT unmapped_metric FROM fact_sales_performance;",
        max_retries=0,
    )
    res_fail = app.invoke(state_fail)
    tel_fail = res_fail["telemetry"]
    trace_fail = tel_fail["attempts_trace"]

    assert res_fail["status"] == STATUS_FAILED
    assert res_fail["retry_count"] == 0
    assert tel_fail["sql_execution_attempts"] == 1
    assert tel_fail["sql_candidate_evaluations"] == 1
    assert tel_fail["postgres_executor_calls"] == 1
    assert tel_fail["ollama_generation_attempts"] == 0
    assert len(trace_fail) == 1
    assert trace_fail[0]["is_manual_override"] is True
    assert trace_fail[0]["exec_success"] is False
    assert tel_fail["prompt_tokens"] is None
    assert tel_fail["total_tokens"] is None

    # Principal Path 3: Empty override ordinary generation
    state_empty = create_initial_armg_state(
        user_query="Show gross revenue",
        initial_sql_override="",
        max_retries=3,
    )
    res_empty = app.invoke(state_empty)
    tel_empty = res_empty["telemetry"]
    assert res_empty["status"] == STATUS_SUCCESS
    assert tel_empty["sql_execution_attempts"] == 1
    assert tel_empty["sql_candidate_evaluations"] == 1
    assert tel_empty["postgres_executor_calls"] == 1
    assert tel_empty["ollama_generation_attempts"] == 1
    assert tel_empty["prompt_tokens"] is not None

    # Principal Path 4: Safety blocked via AST Guard
    state_blocked = create_initial_armg_state(
        user_query="What is the gross revenue?",
        initial_sql_override="DROP TABLE fact_sales_performance CASCADE;",
        max_retries=3,
    )
    res_blocked = app.invoke(state_blocked)
    tel_blocked = res_blocked["telemetry"]
    trace_blocked = tel_blocked["attempts_trace"]

    assert res_blocked["status"] == STATUS_BLOCKED
    assert tel_blocked["sql_execution_attempts"] == 1
    assert tel_blocked["sql_candidate_evaluations"] == 1
    assert tel_blocked["postgres_executor_calls"] == 0
    assert tel_blocked["ollama_generation_attempts"] == 0
    assert len(trace_blocked) == 1
    assert trace_blocked[0]["is_safety_violation"] is True
    assert trace_blocked[0].get("executed_in_db") is not True
