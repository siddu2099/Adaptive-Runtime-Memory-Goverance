"""
ARMG Phase 1: PostgreSQL Environment Adapter Verification Suite.

Validates the PostgreSQLEnvironment adapter against the live Star Schema warehouse:
- RuntimeEnvironment Protocol conformance
- Direct zero-token catalog inspection (tables, columns, types, primary keys)
- Valid analytical query execution with timing and row capture
- Programmatic error capture on:
    * UndefinedColumn
    * UndefinedTable
    * GroupingError (missing GROUP BY clause)
    * Division by zero runtime error
    * Syntax error
- Pre-execution validation via SQLGlot
- Connection lifecycle management and zero resource leakage
"""

import pytest
from environment.base import ExecutionResult, RuntimeEnvironment
from environment.postgres import PostgreSQLEnvironment


@pytest.fixture
def env():
    """Fixture providing a managed PostgreSQLEnvironment instance."""
    adapter = PostgreSQLEnvironment()
    yield adapter
    adapter.close()


def test_protocol_conformance(env):
    """Verify PostgreSQLEnvironment structurally conforms to RuntimeEnvironment protocol."""
    assert isinstance(env, RuntimeEnvironment)


def test_catalog_inspection(env):
    """Verify inspect() accurately captures all 4 Star Schema tables and schema metadata."""
    catalog = env.inspect()
    assert "tables" in catalog
    tables = catalog["tables"]

    # All 4 Star Schema tables must be present
    expected_tables = ["dim_time", "dim_geography", "dim_product", "fact_sales_performance"]
    for tbl in expected_tables:
        assert tbl in tables, f"Expected table '{tbl}' not found in inspected catalog."

    # Verify dim_time columns
    time_cols = {c["name"] for c in tables["dim_time"]["columns"]}
    assert {"time_key", "full_date", "day_of_week", "calendar_month", "calendar_quarter", "calendar_year"}.issubset(time_cols)

    # Verify dim_geography columns
    geo_cols = {c["name"] for c in tables["dim_geography"]["columns"]}
    assert {"geo_key", "region", "zone", "market_type"}.issubset(geo_cols)

    # Verify dim_product columns
    prod_cols = {c["name"] for c in tables["dim_product"]["columns"]}
    assert {"product_key", "product_name", "category", "sub_category", "unit_cost"}.issubset(prod_cols)

    # Verify fact_sales_performance columns
    fact_cols = {c["name"] for c in tables["fact_sales_performance"]["columns"]}
    assert {"fact_key", "time_key", "geo_key", "product_key", "units_sold", "gross_revenue", "discount_applied", "net_profit"}.issubset(fact_cols)

    # Verify primary keys
    for c in tables["fact_sales_performance"]["columns"]:
        if c["name"] == "fact_key":
            assert c["primary_key"] is True


def test_valid_analytical_query(env):
    """Verify execution of a multi-table analytical aggregation with timing and result rows."""
    query = """
    SELECT 
        dg.region,
        COUNT(f.fact_key) AS total_orders,
        SUM(f.units_sold) AS total_units,
        ROUND(SUM(f.gross_revenue), 2) AS total_gross_revenue,
        ROUND(SUM(f.net_profit), 2) AS total_net_profit
    FROM fact_sales_performance f
    JOIN dim_geography dg ON f.geo_key = dg.geo_key
    GROUP BY dg.region
    ORDER BY total_gross_revenue DESC;
    """
    result: ExecutionResult = env.execute(query)

    assert result.status == "SUCCESS"
    assert result.is_success is True
    assert result.error is None
    assert result.row_count > 0
    assert len(result.rows) == result.row_count
    assert result.execution_time_ms > 0.0

    # Ensure aggregate values are non-trivial
    first_row = result.rows[0]
    assert len(first_row) == 5
    assert first_row[1] > 0  # total_orders > 0


def test_error_capture_undefined_column(env):
    """Verify programmatic capture and observation of UndefinedColumn error."""
    # Intentional hallucination of non-existent column 'revenue'
    bad_query = """
    SELECT dg.region, SUM(f.revenue) AS total_revenue
    FROM fact_sales_performance f
    JOIN dim_geography dg ON f.geo_key = dg.geo_key
    GROUP BY dg.region;
    """
    result: ExecutionResult = env.execute(bad_query)

    assert result.status == "FAILURE"
    assert result.is_success is False
    assert result.rows == []
    assert result.row_count == 0
    assert result.error is not None
    assert "does not exist" in result.error.lower()

    # Verify observation normalization
    obs = env.observe(result.error)
    assert obs["error_class"] == "UndefinedColumn"
    assert "does not exist" in obs["error_message"].lower()


def test_error_capture_undefined_table(env):
    """Verify programmatic capture and observation of UndefinedTable error."""
    bad_query = "SELECT * FROM non_existent_enterprise_table LIMIT 10;"
    result: ExecutionResult = env.execute(bad_query)

    assert result.status == "FAILURE"
    assert result.is_success is False
    assert result.error is not None
    assert "does not exist" in result.error.lower()

    obs = env.observe(result.error)
    assert obs["error_class"] == "UndefinedTable"


def test_error_capture_grouping_error(env):
    """Verify programmatic capture and observation of GroupingError (missing GROUP BY)."""
    bad_query = """
    SELECT dg.region, f.gross_revenue
    FROM fact_sales_performance f
    JOIN dim_geography dg ON f.geo_key = dg.geo_key
    GROUP BY dg.region;
    """
    result: ExecutionResult = env.execute(bad_query)

    assert result.status == "FAILURE"
    assert result.is_success is False
    assert result.error is not None
    assert "must appear in the group by clause" in result.error.lower()

    obs = env.observe(result.error)
    assert obs["error_class"] == "GroupingError"


def test_error_capture_division_by_zero(env):
    """Verify programmatic capture and observation of runtime numerical division by zero."""
    bad_query = "SELECT gross_revenue / 0 FROM fact_sales_performance LIMIT 1;"
    result: ExecutionResult = env.execute(bad_query)

    assert result.status == "FAILURE"
    assert result.is_success is False
    assert result.error is not None
    assert "division by zero" in result.error.lower()

    obs = env.observe(result.error)
    assert obs["error_class"] == "DivisionByZero"


def test_error_capture_syntax_error(env):
    """Verify programmatic capture and observation of raw SQL syntax error."""
    bad_query = "SELEC region, zone FRM dim_geography;"
    result: ExecutionResult = env.execute(bad_query)

    assert result.status == "FAILURE"
    assert result.is_success is False
    assert result.error is not None
    assert "syntax error" in result.error.lower()

    obs = env.observe(result.error)
    assert obs["error_class"] == "SyntaxError"


def test_pre_execution_validation(env):
    """Verify static SQLGlot validation correctly parses valid SQL and flags invalid SQL."""
    valid_sql = "SELECT region, zone FROM dim_geography;"
    is_valid, err = env.validate(valid_sql)
    assert is_valid is True
    assert err is None

    empty_sql = "   "
    is_valid, err = env.validate(empty_sql)
    assert is_valid is False
    assert "empty" in err.lower()

    malformed_sql = "SELECT FROM WHERE;"
    is_valid, err = env.validate(malformed_sql)
    assert is_valid is False
    assert err is not None


def test_connection_cleanup_and_lifecycle():
    """Verify connection is cleanly closed and does not leak resources."""
    with PostgreSQLEnvironment() as scoped_env:
        res = scoped_env.execute("SELECT 1;")
        assert res.is_success is True

    # After exit, connection must be closed
    assert scoped_env._connection is None or scoped_env._connection.closed
