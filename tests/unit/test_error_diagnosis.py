"""
ARMG Phase 4: Deterministic Error Diagnosis Test Suite.

Validates:
1. Undefined column diagnosis (SEMANTIC, identifier extraction, negative constraints, candidate resolution).
2. Undefined relation/table diagnosis (SEMANTIC, table candidate resolution).
3. Grouping error diagnosis (PLANNING, repair rule).
4. Division by zero diagnosis (EXECUTION, NULLIF rule).
5. Syntax error diagnosis (SYNTAX, token extraction).
6. Validation rejection diagnosis (VALIDATION).
7. Permission error diagnosis (PERMISSION).
8. Resource error diagnosis (RESOURCE).
9. Unknown execution error fallback (EXECUTION, no guessing).
10. 50-run determinism verification.
11. Zero schema hallucination verification.
12. Zero LLM / offline verification.
"""

import pytest

from agents.error_diagnosis import DeterministicErrorDiagnoser, DiagnosticResult
from agents.taxonomy import TaxonomyCategory
from environment.observation import ExecutionStatus, RuntimeObservation
@pytest.fixture(scope="module")
def star_schema_catalog():
    """Deterministic in-memory Star Schema catalog for hermetic unit testing."""
    return {
        "tables": {
            "dim_time": {
                "columns": [
                    {"name": "time_key", "type": "integer", "primary_key": True},
                    {"name": "full_date", "type": "date"},
                    {"name": "day_of_week", "type": "varchar"},
                    {"name": "calendar_month", "type": "varchar"},
                    {"name": "calendar_quarter", "type": "varchar"},
                    {"name": "calendar_year", "type": "integer"},
                ]
            },
            "dim_geography": {
                "columns": [
                    {"name": "geo_key", "type": "integer", "primary_key": True},
                    {"name": "region", "type": "varchar"},
                    {"name": "zone", "type": "varchar"},
                    {"name": "market_type", "type": "varchar"},
                ]
            },
            "dim_product": {
                "columns": [
                    {"name": "product_key", "type": "integer", "primary_key": True},
                    {"name": "product_name", "type": "varchar"},
                    {"name": "category", "type": "varchar"},
                    {"name": "sub_category", "type": "varchar"},
                    {"name": "unit_cost", "type": "numeric"},
                ]
            },
            "fact_sales_performance": {
                "columns": [
                    {"name": "fact_key", "type": "integer", "primary_key": True},
                    {"name": "time_key", "type": "integer"},
                    {"name": "geo_key", "type": "integer"},
                    {"name": "product_key", "type": "integer"},
                    {"name": "units_sold", "type": "integer"},
                    {"name": "gross_revenue", "type": "numeric"},
                    {"name": "discount_applied", "type": "numeric"},
                    {"name": "net_profit", "type": "numeric"},
                ]
            },
        }
    }


@pytest.fixture
def diagnoser():
    """Fixture providing DeterministicErrorDiagnoser instance."""
    return DeterministicErrorDiagnoser()


def test_diagnosis_undefined_column(diagnoser, star_schema_catalog):
    """Test 1: Undefined column error diagnosis."""
    obs = RuntimeObservation(
        query="SELECT region, SUM(revenue) FROM fact_sales_performance GROUP BY region;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='psycopg2.errors.UndefinedColumn: column "revenue" does not exist\nLINE 1: SELECT region, SUM(revenue) FROM ...',
        normalized_error='psycopg2.errors.UndefinedColumn: column "revenue" does not exist\nLINE 1: SELECT region, SUM(revenue) FROM ...',
        execution_time_ms=2.1,
        row_count=0,
        schema_context=["fact_sales_performance", "dim_geography"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.SEMANTIC
    assert diag.broken_identifier == "revenue"
    assert diag.negative_constraints == ["revenue"]
    assert "Referenced column 'revenue' does not exist" in diag.root_cause
    assert "schema-valid candidate" in diag.repair_rule.lower()

    # Verify candidates include key financial metrics gross_revenue and net_profit
    assert "gross_revenue" in diag.candidate_replacements
    assert "net_profit" in diag.candidate_replacements
    # gross_revenue must rank ahead due to exact substring match
    assert diag.candidate_replacements.index("gross_revenue") < diag.candidate_replacements.index("net_profit")


def test_diagnosis_undefined_relation(diagnoser, star_schema_catalog):
    """Test 2: Undefined relation error diagnosis."""
    obs = RuntimeObservation(
        query="SELECT * FROM sales;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='psycopg2.errors.UndefinedTable: relation "sales" does not exist',
        normalized_error='psycopg2.errors.UndefinedTable: relation "sales" does not exist',
        execution_time_ms=1.5,
        row_count=0,
        schema_context=["sales"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.SEMANTIC
    assert diag.broken_identifier == "sales"
    assert diag.negative_constraints == ["sales"]
    assert "fact_sales_performance" in diag.candidate_replacements
    # fact_sales_performance contains 'sales' so it should be the top candidate
    assert diag.candidate_replacements[0] == "fact_sales_performance"


def test_diagnosis_grouping_error(diagnoser, star_schema_catalog):
    """Test 3: Grouping requirement error diagnosis."""
    obs = RuntimeObservation(
        query="SELECT region, gross_revenue FROM fact_sales_performance f JOIN dim_geography dg ON f.geo_key = dg.geo_key;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='psycopg2.errors.GroupingError: column "dg.region" must appear in the GROUP BY clause or be used in an aggregate function',
        normalized_error='psycopg2.errors.GroupingError: column "dg.region" must appear in the GROUP BY clause or be used in an aggregate function',
        execution_time_ms=2.0,
        row_count=0,
        schema_context=["fact_sales_performance", "dim_geography"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.PLANNING
    assert diag.broken_identifier == "dg.region"
    assert "GROUP BY" in diag.repair_rule


def test_diagnosis_division_by_zero(diagnoser, star_schema_catalog):
    """Test 4: Division by zero runtime execution error diagnosis."""
    obs = RuntimeObservation(
        query="SELECT gross_revenue / 0 FROM fact_sales_performance LIMIT 1;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="psycopg2.errors.DivisionByZero: division by zero",
        normalized_error="psycopg2.errors.DivisionByZero: division by zero",
        execution_time_ms=1.1,
        row_count=0,
        schema_context=["fact_sales_performance"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.EXECUTION
    assert "division by zero" in diag.root_cause.lower()
    assert "nullif" in diag.repair_rule.lower()


def test_diagnosis_syntax_error(diagnoser, star_schema_catalog):
    """Test 5: Syntax error diagnosis with parser token extraction."""
    obs = RuntimeObservation(
        query="SELEC region FRM dim_geography;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='psycopg2.errors.SyntaxError: syntax error at or near "FRM"',
        normalized_error='psycopg2.errors.SyntaxError: syntax error at or near "FRM"',
        execution_time_ms=0.8,
        row_count=0,
        schema_context=["dim_geography"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.SYNTAX
    assert diag.broken_identifier == "FRM"
    assert diag.negative_constraints == ["FRM"]
    assert "syntax near the reported parser location" in diag.repair_rule.lower()


def test_diagnosis_validation_failure(diagnoser, star_schema_catalog):
    """Test 6: Pre-execution AST guardrail rejection diagnosis."""
    obs = RuntimeObservation(
        query="DROP TABLE dim_product;",
        status=ExecutionStatus.VALIDATION_FAILURE,
        raw_error="Destructive mutation 'Drop' is strictly rejected.",
        normalized_error="Destructive mutation 'Drop' is strictly rejected.",
        execution_time_ms=0.0,
        row_count=0,
        schema_context=["dim_product"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.VALIDATION
    assert "guardrail validation rejected" in diag.root_cause.lower()
    assert "read-only select" in diag.repair_rule.lower()


def test_diagnosis_permission_error(diagnoser, star_schema_catalog):
    """Test 7: Permission/authorization error diagnosis."""
    obs = RuntimeObservation(
        query="ALTER TABLE dim_product SET SCHEMA archive;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="psycopg2.errors.InsufficientPrivilege: permission denied for table dim_product",
        normalized_error="psycopg2.errors.InsufficientPrivilege: permission denied for table dim_product",
        execution_time_ms=1.2,
        row_count=0,
        schema_context=["dim_product"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.PERMISSION
    assert "privileges or read-only" in diag.root_cause.lower()
    assert "permitted by the configured database authorization" in diag.repair_rule.lower()


def test_diagnosis_resource_error(diagnoser, star_schema_catalog):
    """Test 8: Resource exhaustion or timeout error diagnosis."""
    obs = RuntimeObservation(
        query="SELECT * FROM fact_sales_performance CROSS JOIN dim_time;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="psycopg2.errors.QueryCanceled: canceling statement due to statement timeout",
        normalized_error="psycopg2.errors.QueryCanceled: canceling statement due to statement timeout",
        execution_time_ms=30000.0,
        row_count=0,
        schema_context=["fact_sales_performance", "dim_time"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.RESOURCE
    assert "timeout" in diag.root_cause.lower() or "resource" in diag.root_cause.lower()
    assert "resource limitation" in diag.repair_rule.lower()


def test_diagnosis_unknown_execution_error_fallback(diagnoser, star_schema_catalog):
    """Test 9: Unclassified execution error uses documented deterministic fallback."""
    obs = RuntimeObservation(
        query="SELECT 1;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="psycopg2.OperationalError: unexpected internal worker termination",
        normalized_error="psycopg2.OperationalError: unexpected internal worker termination",
        execution_time_ms=5.0,
        row_count=0,
        schema_context=["dim_time"],
    )

    diag: DiagnosticResult = diagnoser.diagnose(obs, star_schema_catalog)

    assert diag.taxonomy_category == TaxonomyCategory.EXECUTION
    assert diag.broken_identifier is None
    assert "not matched by a specialized deterministic rule" in diag.root_cause.lower()


def test_diagnosis_determinism_50_runs(diagnoser, star_schema_catalog):
    """Test 10: Run diagnosis 50 times with identical input; verify identical output."""
    obs = RuntimeObservation(
        query="SELECT region, SUM(revenue) FROM fact_sales_performance GROUP BY region;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='psycopg2.errors.UndefinedColumn: column "revenue" does not exist',
        normalized_error='psycopg2.errors.UndefinedColumn: column "revenue" does not exist',
        execution_time_ms=2.0,
        row_count=0,
        schema_context=["fact_sales_performance", "dim_geography"],
    )

    baseline_dict = diagnoser.diagnose(obs, star_schema_catalog).to_dict()

    for i in range(50):
        run_dict = diagnoser.diagnose(obs, star_schema_catalog).to_dict()
        assert run_dict == baseline_dict, f"Non-deterministic diagnosis detected at iteration {i}"


def test_no_schema_hallucination(diagnoser, star_schema_catalog):
    """Test 11: All generated candidates must strictly exist in the supplied schema catalog."""
    obs = RuntimeObservation(
        query="SELECT non_existent_token FROM fact_sales_performance;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "non_existent_token" does not exist',
        normalized_error='column "non_existent_token" does not exist',
        execution_time_ms=1.0,
        row_count=0,
        schema_context=["fact_sales_performance", "dim_time", "dim_product", "dim_geography"],
    )

    diag = diagnoser.diagnose(obs, star_schema_catalog)

    # Collect every valid column across the catalog
    all_valid_columns = set()
    for tbl in star_schema_catalog["tables"].values():
        for col in tbl.get("columns", []):
            all_valid_columns.add(col["name"])

    for cand in diag.candidate_replacements:
        assert cand in all_valid_columns, f"Hallucinated candidate detected: '{cand}'"


def test_zero_llm_dependency(diagnoser, star_schema_catalog):
    """Test 12: Diagnosis executes purely in-process with zero network or LLM dependencies."""
    # Ensure error_diagnosis module does not import requests, ollama, or langchain
    import agents.error_diagnosis as diag_mod

    disallowed = ["requests", "ollama", "langchain", "langgraph", "faiss"]
    for mod_name in disallowed:
        assert mod_name not in diag_mod.__dict__, f"Forbidden dependency '{mod_name}' found in error_diagnosis"

    # Execution requires only observation and catalog
    obs = RuntimeObservation(
        query="SELECT region, SUM(revenue) FROM fact_sales_performance;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "revenue" does not exist',
        schema_context=["fact_sales_performance"],
    )
    result = diagnoser.diagnose(obs, star_schema_catalog)
    assert result.taxonomy_category == TaxonomyCategory.SEMANTIC
