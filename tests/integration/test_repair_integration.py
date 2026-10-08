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
from graph.state import STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow
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
    """Integration test with live PostgreSQL warehouse instance."""
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

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            embed_fn=deterministic_mock_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Show total sales revenue", "max_retries": 3})
        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 1
        assert res["execution_result"] is not None
        assert res["execution_result"].is_success is True
    finally:
        env.close()
