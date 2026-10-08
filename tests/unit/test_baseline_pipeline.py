"""
ARMG Phase 2: Stateless Baseline Text-to-SQL Pipeline Unit Test Suite.

Validates the complete linear stateless pipeline in hermetic isolation:
A. Schema Introspection & Deterministic Markdown Formatting
B. Deterministic Rule-Based Schema Pruning
C. SQLGlot Execution Guard (multi-statements, DDL/DML, non-SELECT roots)
D. Baseline SQL Generator Mock Unit Tests (payloads, response extraction, failure paths)
E. Pipeline Orchestration Mock Tests (fully isolated from external daemons)

Live database/Ollama tests are isolated in tests/integration/test_baseline_integration.py.
Per Audit 1 Remediation Item REM-P0-04.
"""

from unittest.mock import MagicMock, patch
import pytest
from agents.repair_agent import RepairSQLGenerator
from agents.schema_introspector import SchemaIntrospector, format_catalog_to_markdown
from agents.schema_pruner import SchemaPruner, prune_schema_tables
from agents.sql_generator import SQLGenerator, extract_sql_from_response
from environment.base import ExecutionResult, RuntimeEnvironment
from scripts.run_baseline import BaselinePipeline, BaselineExecutionResult
from validation.execution_validator import ExecutionValidator, validate_sql


# ------------------------------------------------------------------------------
# A. Schema Formatting & Introspection Tests
# ------------------------------------------------------------------------------
def test_schema_formatting_deterministic():
    """Verify schema formatting contains all tables, columns, types, and is deterministic."""
    sample_catalog = {
        "tables": {
            "dim_product": {
                "columns": [
                    {"name": "product_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                    {"name": "product_name", "type": "character varying", "primary_key": False, "ordinal_position": 2},
                ]
            },
            "dim_time": {
                "columns": [
                    {"name": "time_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                    {"name": "full_date", "type": "date", "primary_key": False, "ordinal_position": 2},
                ]
            }
        }
    }

    md1 = format_catalog_to_markdown(sample_catalog)
    md2 = format_catalog_to_markdown(sample_catalog)

    # Determinism: two successive calls must produce identical strings
    assert md1 == md2

    # Verify content
    assert "## dim_product" in md1
    assert "## dim_time" in md1
    assert "- product_key: integer (PK)" in md1
    assert "- product_name: character varying" in md1
    assert "- time_key: integer (PK)" in md1
    assert "- full_date: date" in md1

    # Verify alphabetical order: dim_product must precede dim_time
    assert md1.index("## dim_product") < md1.index("## dim_time")


def test_schema_introspector_with_mock_env():
    """Verify SchemaIntrospector extracts and formats markdown from environment inspect()."""
    mock_env = MagicMock(spec=RuntimeEnvironment)
    mock_env.inspect.return_value = {
        "tables": {
            "dim_geography": {
                "columns": [
                    {"name": "geo_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                    {"name": "region", "type": "character varying", "primary_key": False, "ordinal_position": 2},
                ]
            },
            "fact_sales_performance": {
                "columns": [
                    {"name": "fact_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                    {"name": "gross_revenue", "type": "numeric", "primary_key": False, "ordinal_position": 2},
                ]
            }
        }
    }

    introspector = SchemaIntrospector(env=mock_env)
    md = introspector.get_schema_markdown()

    assert "## dim_geography" in md
    assert "## fact_sales_performance" in md
    assert "geo_key" in md
    assert "gross_revenue" in md


# ------------------------------------------------------------------------------
# B. Deterministic Pruning Tests
# ------------------------------------------------------------------------------
def test_pruning_geography_query():
    """Query with region/location keywords should select dim_geography and fact table."""
    tables = prune_schema_tables("What is the total revenue by region?")
    assert tables == ["dim_geography", "fact_sales_performance"]


def test_pruning_product_and_time_query():
    """Query with product category and year keywords should select dim_product, dim_time, and fact."""
    tables = prune_schema_tables("What is the net profit by product category and calendar year?")
    assert tables == ["dim_product", "dim_time", "fact_sales_performance"]


def test_pruning_ambiguous_query():
    """Ambiguous query with no specific dimension keywords falls back to all 4 tables."""
    tables = prune_schema_tables("Show me all general analytical key performance indicators.")
    assert tables == ["dim_geography", "dim_product", "dim_time", "fact_sales_performance"]


def test_pruning_simple_aggregation():
    """Query with no dimension keywords falls back to all 4 tables for complete context."""
    tables = prune_schema_tables("What is the total gross revenue?")
    assert tables == ["dim_geography", "dim_product", "dim_time", "fact_sales_performance"]


# ------------------------------------------------------------------------------
# C. SQL Validator Tests
# ------------------------------------------------------------------------------
def test_validator_accepts_valid_select():
    """Validator must accept standard read-only analytical SELECT."""
    sql = """
    SELECT dg.region, SUM(f.gross_revenue) AS rev
    FROM fact_sales_performance f
    JOIN dim_geography dg ON f.geo_key = dg.geo_key
    GROUP BY dg.region;
    """
    is_valid, err = validate_sql(sql)
    assert is_valid is True
    assert err is None


@pytest.mark.parametrize("bad_sql,reason_keyword", [
    ("DROP TABLE dim_product;", "Drop"),
    ("DELETE FROM fact_sales_performance WHERE fact_key = 1;", "Delete"),
    ("UPDATE dim_product SET unit_cost = 0;", "Update"),
    ("INSERT INTO dim_product (product_key) VALUES (99);", "Insert"),
    ("ALTER TABLE dim_product ADD COLUMN test_col int;", "Alter"),
    ("TRUNCATE TABLE fact_sales_performance;", "Truncate"),
    ("SELECT 1; SELECT 2;", "Multiple statements"),
    ("CREATE TABLE test_tbl (id int);", "Create"),
    ("SHOW TABLES;", "Command"),
])
def test_validator_rejects_forbidden_statements(bad_sql, reason_keyword):
    """Validator must reject multi-statements, DDL/DML mutations, and non-SELECT roots."""
    is_valid, err = validate_sql(bad_sql)
    assert is_valid is False
    assert err is not None
    assert reason_keyword.lower() in err.lower()


# ------------------------------------------------------------------------------
# D. Mocked SQL Generator Unit Tests (Isolated from Ollama)
# ------------------------------------------------------------------------------
def test_generator_mock_success_response():
    """Verify SQLGenerator correctly parses successful LLM response with metrics."""
    generator = SQLGenerator(seed=42)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT region, SUM(gross_revenue) FROM fact_sales_performance GROUP BY region;\n```",
            "prompt_eval_count": 45,
            "eval_count": 22,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = generator.generate("Total revenue by region", "## dim_geography\n## fact_sales_performance")

        assert "SELECT region" in res.extracted_sql
        assert res.prompt_tokens == 45
        assert res.completion_tokens == 22
        assert res.generation_duration_ms >= 0.0


def test_generator_mock_network_failure():
    """Verify SQLGenerator handles network exceptions gracefully without raising."""
    generator = SQLGenerator()

    with patch("requests.post", side_effect=Exception("Connection refused")):
        res = generator.generate("Question", "Schema")

        assert res.raw_response == ""
        assert res.extracted_sql == ""
        assert res.prompt_tokens is None
        assert res.completion_tokens is None
        assert res.generation_duration_ms >= 0.0


def test_repair_generator_mock_success():
    """Verify RepairSQLGenerator correctly parses repair LLM response."""
    repair_gen = RepairSQLGenerator(seed=123)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT product_name FROM dim_product;\n```",
            "prompt_eval_count": 60,
            "eval_count": 15,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = repair_gen.generate_repair("[STRICT REPAIR CONSTRAINTS]\nUse product_name")

        assert res.extracted_sql == "SELECT product_name FROM dim_product;"
        assert res.prompt_tokens == 60
        assert res.completion_tokens == 15


# ------------------------------------------------------------------------------
# E. Baseline Pipeline Mock Orchestration Unit Test
# ------------------------------------------------------------------------------
def test_baseline_pipeline_mock_run():
    """Verify complete BaselinePipeline orchestration with injected mock components."""
    mock_env = MagicMock(spec=RuntimeEnvironment)
    mock_env.inspect.return_value = {
        "tables": {
            "dim_geography": {
                "columns": [{"name": "geo_key", "type": "int", "primary_key": True, "ordinal_position": 1}]
            },
            "fact_sales_performance": {
                "columns": [{"name": "gross_revenue", "type": "numeric", "primary_key": False, "ordinal_position": 1}]
            }
        }
    }
    mock_env.execute.return_value = ExecutionResult(
        status="SUCCESS",
        query="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
        rows=[(50000.0,)],
        row_count=1,
        execution_time_ms=12.5,
    )

    mock_gen = MagicMock(spec=SQLGenerator)
    mock_gen.generate.return_value = MagicMock(
        extracted_sql="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
        prompt_tokens=30,
        completion_tokens=10,
        generation_duration_ms=45.0,
    )

    pipeline = BaselinePipeline(env=mock_env, generator=mock_gen)
    res = pipeline.run("What is total revenue?")

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count == 1
    assert res.rows == [(50000.0,)]
    assert res.total_latency_ms >= 0.0
