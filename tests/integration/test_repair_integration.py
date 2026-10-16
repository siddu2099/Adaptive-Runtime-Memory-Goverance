"""
ARMG Integration Test Suite: Repair Workflow against Live PostgreSQL.
Phase 3 Test Architecture Implementation.

Validates end-to-end graph repair execution against live PostgreSQL database.
Requires live PostgreSQL on localhost:5432.
"""

import pytest
from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from environment.postgres import PostgreSQLEnvironment
from graph.state import STATUS_FAILED, STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow
from memory.vector_store import FAISSMemoryStore
import numpy as np

pytestmark = pytest.mark.integration


def is_postgres_online() -> bool:
    """Check if PostgreSQL server is reachable."""
    try:
        env = PostgreSQLEnvironment()
        res = env.execute("SELECT 1;")
        env.close()
        return res.is_success
    except Exception:
        return False


def deterministic_mock_embed_fn(text: str):
    """Deterministic normalized mock embed function for testing."""
    rng = np.random.RandomState(abs(hash(text)) % (2**31))
    vec = rng.randn(768).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def test_live_postgres_repair_execution():
    """Integration test with live PostgreSQL warehouse instance.

    Verifies Type 8 autonomous repair sequence:
    1. Initial candidate produces expected, non-destructive PostgreSQL error (column "revenue" does not exist).
    2. Repair loop is entered (diagnosis, knowledge extraction, repair prompt).
    3. Repaired candidate (gross_revenue) is executed against PostgreSQL.
    4. Run succeeds only after the corrected candidate executes successfully.
    5. Retry accounting (retry_count == 1) and PostgreSQL execution count (calls == 2) are verified.
    6. Memory governance admits valid repaired operational knowledge to FAISS vector store.
    """
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
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

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Show total sales revenue", "max_retries": 3})

        # 1. Run succeeds only after corrected candidate executes successfully
        assert res["status"] == STATUS_SUCCESS
        assert res["execution_result"] is not None
        assert res["execution_result"].is_success is True

        # 2. Retry accounting
        assert res["retry_count"] == 1
        telemetry = res.get("telemetry", {})
        assert telemetry.get("repair_count") == 1
        assert telemetry.get("generation_attempts") == 2

        # 3. Exactly two live PostgreSQL executions (attempt 1 failed, attempt 2 succeeded)
        assert telemetry.get("postgres_executor_calls") == 2

        # 4. Detailed trace verification of the whole sequence
        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 2

        # Attempt 1: First candidate produced expected non-destructive database error
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert attempts[0]["exec_error"] is not None
        assert 'column "revenue" does not exist' in attempts[0]["exec_error"]
        assert attempts[0]["is_repair"] is False

        # Attempt 2: Repair candidate was executed and succeeded
        assert attempts[1]["is_repair"] is True
        assert attempts[1]["executed_in_db"] is True
        assert attempts[1]["exec_success"] is True
        assert attempts[1]["sql"] == "SELECT gross_revenue FROM fact_sales_performance;"

        # 5. Repair history confirms repair loop was entered with diagnosis and rule
        repair_history = telemetry.get("repair_history", [])
        assert len(repair_history) == 1
        assert repair_history[0]["attempt"] == 1
        assert repair_history[0]["terminal_status"] == STATUS_SUCCESS

        # 6. Memory admission governance rule: repaired causal knowledge admitted
        assert telemetry.get("memory_admission") == "ADMITTED"
        assert telemetry.get("admitted_memory_id") is not None
        assert vector_store.count() == 1
    finally:
        env.close()


def test_live_postgres_constraint_preservation_rejects_substitutions():
    """Integration test against live PostgreSQL warehouse instance.

    Verifies that against a real running PostgreSQL instance:
    1. Initial query referencing non-existent 'fact_sales_performance_archive' passes constraint check.
    2. Live PostgreSQL returns genuine relation-not-found error.
    3. Proposed repair substituting 'fact_sales_performance' is rejected by AST constraint guard.
    4. Real PostgreSQL is NOT invoked a second time (zero repair execution on live DB).
    5. Terminal status is STATUS_FAILED and no memory is admitted.
    """
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
        user_query = (
            "Query the table named fact_sales_performance_archive and retrieve its gross_revenue "
            "column for every transaction. Use fact_sales_performance_archive as the exact source "
            "table name. Do not substitute fact_sales_performance, do not select from another table, "
            "and do not rename or alias a different table as this table."
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT * FROM fact_sales_performance_archive;\n```",
            extracted_sql="SELECT * FROM fact_sales_performance_archive;",
        )
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM fact_sales_performance;\n```",
                extracted_sql="SELECT * FROM fact_sales_performance;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 3})

        assert res["status"] == STATUS_FAILED
        assert res["decision_source"] == "constraint_validator"
        assert res["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert res.get("is_constraint_violation") is True

        telemetry = res.get("telemetry", {})
        assert telemetry.get("terminal_reason") == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert telemetry.get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"

        # Trace verification: exactly one live database execution occurred (the initial failure)
        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 2
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert "relation \"fact_sales_performance_archive\" does not exist" in attempts[0]["exec_error"]
        assert attempts[1]["is_repair"] is True
        assert attempts[1].get("executed_in_db") is not True

        assert vector_store.count() == 0
    finally:
        env.close()


def test_live_postgres_missing_column_zero_retries_fails():
    """Type 4: Deterministic missing-column failure integration test with live PostgreSQL.

    Verifies against designated PostgreSQL environment with max_retries=0:
    - Normal ARMG workflow with scripted SQL generator (no advanced SQL override).
    - PostgreSQL reports expected undefined-column error for 'unmapped_metric'.
    - Exactly one PostgreSQL execution is attempted.
    - No repair retry occurs (retry_count == 0).
    - Final status is STATUS_FAILED (not SUCCESS).
    - Database error and terminal outcome recorded truthfully.
    - Failed run is not admitted to successful memory.
    """
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
        user_query = "Retrieve the unmapped_metric column from fact_sales_performance for every transaction."
        scripted_sql = "SELECT unmapped_metric\nFROM fact_sales_performance;"

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{scripted_sql}\n```",
            extracted_sql=scripted_sql,
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            vector_store=vector_store,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 0})

        # 1. Final status is FAILED, not SUCCESS
        assert res["status"] == STATUS_FAILED

        # 2. PostgreSQL reports expected undefined-column error
        assert res["execution_result"] is not None
        assert res["execution_result"].is_success is False
        assert res["execution_result"].error is not None
        assert 'column "unmapped_metric" does not exist' in res["execution_result"].error

        # 3. Exactly one PostgreSQL execution attempted
        telemetry = res.get("telemetry", {})
        assert telemetry.get("postgres_executor_calls") == 1

        # 4. No repair retry occurs
        assert res.get("retry_count") == 0
        assert telemetry.get("repair_count", 0) == 0

        # 5. Database error and terminal outcome recorded truthfully
        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 1
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert 'column "unmapped_metric" does not exist' in attempts[0]["exec_error"]

        # 6. Failed run is not admitted to successful memory
        assert telemetry.get("memory_admission") == "TERMINAL_FAILURE_NOT_ADMITTED"
        assert telemetry.get("admitted_memory_id") is None
        assert vector_store.count() == 0
    finally:
        env.close()


def test_live_postgres_test4a_projection_omission_fails_before_execution():
    """Test 4A: Missing required output column rejected before live PostgreSQL execution.

    Verifies:
    - User query explicitly requests 'unmapped_metric' column value directly.
    - Scripted candidate includes 'unmapped_metric' only in WHERE clause, omitting it from projection.
    - Projection validation detects omission and rejects candidate before executor invocation.
    - Exactly 0 PostgreSQL executions occur.
    - 0 repair retries occur.
    - Final status is STATUS_FAILED with decision_source="constraint_validator".
    - Telemetry records EXPLICIT_CONSTRAINT_VIOLATION and CONSTRAINT_VIOLATION_NOT_ADMITTED.
    - 0 memory additions to FAISS store.
    """
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
        user_query = (
            "Retrieve the unmapped_metric column from fact_sales_performance for every transaction. "
            "Return the value of this column directly, rather than counting transactions with missing foreign keys."
        )
        scripted_sql = (
            "SELECT fact_key, gross_revenue, discount_applied, net_profit\n"
            "FROM fact_sales_performance\n"
            "WHERE unmapped_metric IS NOT NULL;"
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{scripted_sql}\n```",
            extracted_sql=scripted_sql,
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            vector_store=vector_store,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 3})

        # 1. Final status is FAILED with constraint validator attribution
        assert res["status"] == STATUS_FAILED
        assert res["decision_source"] == "constraint_validator"
        assert res["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert res.get("is_constraint_violation") is True
        assert "unmapped_metric" in res.get("violated_constraint", "")

        # 2. Exactly zero PostgreSQL executions attempted
        telemetry = res.get("telemetry", {})
        assert telemetry.get("postgres_executor_calls") == 0

        # 3. Zero repair retries attempted
        assert res.get("retry_count", 0) == 0
        assert telemetry.get("repair_count", 0) == 0

        # 4. Zero memory admitted
        assert telemetry.get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"
        assert vector_store.count() == 0
    finally:
        env.close()


def test_live_postgres_regional_revenue_aggregation_repair():
    """Test 8: Autonomous repair of regional revenue aggregation against live PostgreSQL.

    Verifies the complete Test 8 failure-and-repair scenario against live warehouse:
    - User query: Calculate total revenue by region using column named revenue...
    - Initial candidate: Two-table join (fact_sales_performance + dim_geography) using SUM(f.revenue) AS revenue.
    - Read-only AST validation passes (revenue is in aggregate expression, not extracted as output column constraint).
    - Initial candidate reaches PostgreSQL and produces expected undefined-column error ('f.revenue does not exist').
    - Autonomous repair proposes corrected SQL with valid source measure SUM(f.gross_revenue) AS revenue.
    - Repaired query preserves grouping by region and aggregate alias.
    - Repaired query executes against live PostgreSQL, returning regional aggregate rows.
    - Exactly two live PostgreSQL executions (attempt 1 failed, attempt 2 succeeded).
    - Exactly one repair retry (retry_count == 1).
    - Terminal workflow status is STATUS_SUCCESS.
    - Governed operational memory admitted.
    """
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
        user_query = (
            "Calculate total revenue by region using the column named revenue, and group the results by region. "
            "If that column is invalid, use the database error to correct the query and return the regional revenue totals."
        )
        initial_sql = (
            "SELECT d.region, SUM(f.revenue) AS revenue\n"
            "FROM fact_sales_performance AS f\n"
            "JOIN dim_geography AS d ON f.geo_key = d.geo_key\n"
            "GROUP BY d.region;"
        )
        repaired_sql = (
            "SELECT d.region, SUM(f.gross_revenue) AS revenue\n"
            "FROM fact_sales_performance AS f\n"
            "JOIN dim_geography AS d ON f.geo_key = d.geo_key\n"
            "GROUP BY d.region;"
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{initial_sql}\n```",
            extracted_sql=initial_sql,
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response=f"```sql\n{repaired_sql}\n```",
                extracted_sql=repaired_sql,
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 3})

        # 1. Final status is SUCCESS only after corrected query executes
        assert res["status"] == STATUS_SUCCESS
        assert res["execution_result"] is not None
        assert res["execution_result"].is_success is True
        assert res["execution_result"].row_count == 3  # 3 regional rows (APAC, EMEA, North America)

        # 2. Retry accounting
        assert res["retry_count"] == 1
        telemetry = res.get("telemetry", {})
        assert telemetry.get("repair_count") == 1
        assert telemetry.get("generation_attempts") == 2

        # 3. Exactly two live PostgreSQL executions
        assert telemetry.get("postgres_executor_calls") == 2

        # 4. Traces confirm undefined-column initial failure and successful repaired execution
        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 2

        # Attempt 1: First candidate failed with undefined column in DB
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert attempts[0]["exec_error"] is not None
        assert 'column f.revenue does not exist' in attempts[0]["exec_error"]
        assert attempts[0]["is_repair"] is False

        # Attempt 2: Repair candidate executed and succeeded
        assert attempts[1]["is_repair"] is True
        assert attempts[1]["executed_in_db"] is True
        assert attempts[1]["exec_success"] is True
        assert attempts[1]["row_count"] == 3

        # 5. Repair history confirms repair loop was entered with diagnosis and rule
        repair_history = telemetry.get("repair_history", [])
        assert len(repair_history) == 1
        assert repair_history[0]["attempt"] == 1
        assert repair_history[0]["terminal_status"] == STATUS_SUCCESS

        # 6. Governed memory admission
        assert telemetry.get("memory_admission") == "ADMITTED"
        assert telemetry.get("admitted_memory_id") is not None
        assert vector_store.count() == 1
    finally:
        env.close()
