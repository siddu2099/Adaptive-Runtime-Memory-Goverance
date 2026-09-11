"""
ARMG Phase 2: Stateless Baseline Text-to-SQL Pipeline Test Suite.

Validates the complete linear stateless pipeline:
A. Schema Introspection & Deterministic Markdown Formatting
B. Deterministic Rule-Based Schema Pruning
C. SQLGlot Execution Guard (multi-statements, DDL/DML, non-SELECT roots)
D. Baseline SQL Generator communication with Ollama
E. Three End-to-End Representative Analytical Queries
"""

import pytest
from agents.schema_introspector import SchemaIntrospector, format_catalog_to_markdown
from agents.schema_pruner import SchemaPruner, prune_schema_tables
from agents.sql_generator import SQLGenerator, extract_sql_from_response
from environment.postgres import PostgreSQLEnvironment
from scripts.run_baseline import BaselinePipeline, BaselineExecutionResult
from validation.execution_validator import ExecutionValidator, validate_sql


# ------------------------------------------------------------------------------
# A. Schema Formatting Tests
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


def test_schema_introspector_live():
    """Verify live schema introspector returns all 4 tables with columns and types."""
    introspector = SchemaIntrospector()
    md = introspector.get_schema_markdown()

    assert "## dim_time" in md
    assert "## dim_geography" in md
    assert "## dim_product" in md
    assert "## fact_sales_performance" in md
    assert "gross_revenue" in md
    assert "net_profit" in md


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
# D. Baseline SQL Generator Smoke Test
# ------------------------------------------------------------------------------
def test_generator_communication():
    """Verify SQL generator can interact with local Ollama qwen2.5:7b-instruct."""
    generator = SQLGenerator()
    simple_schema = """## dim_geography\n- geo_key: integer (PK)\n- region: varchar"""
    res = generator.generate("List all distinct regions.", simple_schema)

    assert len(res.extracted_sql) > 0
    assert "region" in res.extracted_sql.lower()
    assert res.generation_duration_ms > 0.0
    # Ollama provides token telemetry
    assert res.prompt_tokens is not None or res.completion_tokens is not None


# ------------------------------------------------------------------------------
# E. End-to-End Baseline Representative Queries
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def pipeline():
    """Module-level baseline pipeline instance."""
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
    # Verify result value is realistic (> 0)
    total_rev = float(res.rows[0][0])
    assert total_rev > 0.0
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0
    assert res.total_latency_ms > 0.0
    print(f"\n[E2E Q1] SQL: {res.extracted_sql} | Result: {total_rev}")


def test_e2e_query_2_two_table_join(pipeline):
    """Query 2: Two-table analytical join grouping fact metrics by region."""
    q = "What is the total revenue by region?"
    res: BaselineExecutionResult = pipeline.run(q)

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count >= 1  # 3 enterprise geographical regions in warehouse
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0
    print(f"\n[E2E Q2] SQL: {res.extracted_sql} | Rows: {res.row_count}")


def test_e2e_query_3_three_table_join(pipeline):
    """Query 3: Three-table analytical join grouping by product category and calendar year."""
    q = "What is the net profit by product category and calendar year?"
    res: BaselineExecutionResult = pipeline.run(q)

    assert res.validation_passed is True
    assert res.execution_status == "SUCCESS"
    assert res.row_count >= 1
    assert res.generation_latency_ms > 0.0
    assert res.execution_latency_ms > 0.0
    print(f"\n[E2E Q3] SQL: {res.extracted_sql} | Rows: {res.row_count}")
