"""
ARMG Integration Test Suite: Baseline Pipeline against Live External Services.
Requires live PostgreSQL on localhost:5432 and Ollama on localhost:11434.
Separated from unit tests per Audit 1 Remediation Item REM-P0-04.
"""

import os
import pytest
import requests
from agents.schema_introspector import SchemaIntrospector
from agents.sql_generator import SQLGenerator
from environment.postgres import PostgreSQLEnvironment
from scripts.run_baseline import BaselinePipeline, BaselineExecutionResult

pytestmark = pytest.mark.integration


def is_ollama_online() -> bool:
    """Check if Ollama service is reachable."""
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        res = requests.get(f"{url.rstrip('/')}/api/tags", timeout=2)
        return res.status_code == 200
    except Exception:
        return False


def is_postgres_online() -> bool:
    """Check if PostgreSQL server is reachable."""
    try:
        env = PostgreSQLEnvironment()
        res = env.execute("SELECT 1;")
        env.close()
        return res.is_success
    except Exception:
        return False


# ------------------------------------------------------------------------------
# Live Schema Introspector
# ------------------------------------------------------------------------------
def test_schema_introspector_live():
    """Verify live schema introspector returns all 4 tables with columns and types."""
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    introspector = SchemaIntrospector()
    md = introspector.get_schema_markdown()

    assert "## dim_time" in md
    assert "## dim_geography" in md
    assert "## dim_product" in md
    assert "## fact_sales_performance" in md
    assert "gross_revenue" in md
    assert "net_profit" in md


# ------------------------------------------------------------------------------
# Baseline SQL Generator Communication with Live Ollama
# ------------------------------------------------------------------------------
def test_generator_communication():
    """Verify SQL generator can interact with local Ollama qwen2.5:7b-instruct."""
    if not is_ollama_online():
        pytest.skip("Ollama service is offline or unreachable on localhost:11434")

    generator = SQLGenerator()
    simple_schema = "## dim_geography\n- geo_key: integer (PK)\n- region: varchar"
    res = generator.generate("List all distinct regions.", simple_schema)

    assert len(res.extracted_sql) > 0
    assert "region" in res.extracted_sql.lower()
    assert res.generation_duration_ms > 0.0
    assert res.prompt_tokens is not None or res.completion_tokens is not None


# ------------------------------------------------------------------------------
# End-to-End Baseline Representative Queries
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def pipeline():
    """Module-level baseline pipeline instance."""
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")
    if not is_ollama_online():
        pytest.skip("Ollama service is offline or unreachable on localhost:11434")

    pipe = BaselinePipeline()
    yield pipe
    pipe.env.close()


def test_e2e_query_1_simple_aggregation(pipeline):
    """Query 1: Simple single-metric aggregation over the fact table."""
    q = "What is the total gross revenue?"
    res: BaselineExecutionResult = pipeline.run(q)

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count == 1
    assert len(res.rows) == 1
    total_rev = float(res.rows[0][0])
    assert total_rev > 0.0
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0
    assert res.total_latency_ms > 0.0


def test_e2e_query_2_two_table_join(pipeline):
    """Query 2: Two-table analytical join grouping fact metrics by region."""
    q = "What is the total revenue by region?"
    res: BaselineExecutionResult = pipeline.run(q)

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count >= 1
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0


def test_e2e_query_3_three_table_join(pipeline):
    """Query 3: Three-table analytical join grouping by product category and calendar year."""
    q = "What is the net profit by product category and calendar year?"
    res: BaselineExecutionResult = pipeline.run(q)

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count >= 1
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0
