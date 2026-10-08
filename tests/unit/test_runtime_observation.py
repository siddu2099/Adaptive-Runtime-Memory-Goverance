"""
ARMG Phase 3: Runtime Observation Layer Test Suite.

Validates:
1. Successful execution observation.
2. Database execution failure observation (both synthetic and live PostgreSQL driver).
3. Validation failure observation.
4. Observation immutability (frozen Pydantic model).
5. Serialization via to_dict().
6. Conservative error normalization (preserves diagnostic content, does NOT classify).
"""

from datetime import datetime
import pytest
from pydantic import ValidationError

from environment.base import ExecutionResult
from environment.observation import ExecutionStatus, RuntimeObservation
from environment.observer import RuntimeObserver, normalize_error_string


def test_observation_successful_execution():
    """Test 1: Verify observation of successful query execution."""
    result = ExecutionResult(
        status="SUCCESS",
        query="SELECT COUNT(*) FROM fact_sales_performance;",
        rows=[(2000,)],
        error=None,
        execution_time_ms=3.45,
        row_count=1,
    )
    schema_context = ["fact_sales_performance"]

    obs = RuntimeObserver.observe_execution(
        query=result.query,
        result=result,
        schema_context=schema_context,
    )

    assert obs.status == ExecutionStatus.SUCCESS
    assert obs.is_failure() is False
    assert obs.query == result.query
    assert obs.row_count == 1
    assert obs.execution_time_ms == 3.45
    assert obs.raw_error is None
    assert obs.normalized_error is None
    assert obs.schema_context == ["fact_sales_performance"]
    assert len(obs.observation_id) > 0
    # Verify ISO 8601 with timezone
    parsed_dt = datetime.fromisoformat(obs.timestamp)
    assert parsed_dt.tzinfo is not None


def test_observation_database_execution_failure():
    """Test 2: Verify observation of database execution failure preserves error without diagnosis."""
    raw_error_text = (
        'psycopg2.errors.UndefinedColumn: column "revenue" does not exist\n'
        'LINE 1: SELECT region, SUM(revenue) FROM fact_sales_performance\n'
        '                           ^\n'
        'HINT: Perhaps you meant to reference the column "f.gross_revenue".'
    )
    result = ExecutionResult(
        status="FAILURE",
        query="SELECT region, SUM(revenue) FROM fact_sales_performance;",
        rows=[],
        error=raw_error_text,
        execution_time_ms=4.12,
        row_count=0,
    )
    schema_context = ["fact_sales_performance", "dim_geography"]

    obs = RuntimeObserver.observe_execution(
        query=result.query,
        result=result,
        schema_context=schema_context,
    )

    assert obs.status == ExecutionStatus.EXECUTION_FAILURE
    assert obs.is_failure() is True
    assert obs.row_count == 0
    assert obs.execution_time_ms == 4.12
    assert obs.raw_error == raw_error_text
    assert obs.normalized_error is not None
    assert 'column "revenue" does not exist' in obs.normalized_error
    assert "HINT:" in obs.normalized_error
    assert "LINE 1:" in obs.normalized_error

    # CRITICAL PHASE 3 BOUNDARY: Observer must NOT produce diagnosis or repair objects
    assert not hasattr(obs, "failure_type")
    assert not hasattr(obs, "root_cause")
    assert not hasattr(obs, "candidate_replacements")
    assert not hasattr(obs, "repair_strategy")


def test_observation_validation_failure():
    """Test 3: Verify observation of pre-execution AST validation rejection."""
    rejected_query = "DROP TABLE dim_product;"
    val_error = "Destructive mutation 'Drop' is strictly rejected."
    schema_context = ["dim_product"]

    obs = RuntimeObserver.observe_validation_failure(
        query=rejected_query,
        validation_error=val_error,
        schema_context=schema_context,
    )

    assert obs.status == ExecutionStatus.VALIDATION_FAILURE
    assert obs.is_failure() is True
    assert obs.query == rejected_query
    assert obs.row_count == 0
    assert obs.execution_time_ms == 0.0
    assert obs.raw_error == val_error
    assert obs.normalized_error == val_error
    assert obs.schema_context == ["dim_product"]


def test_observation_immutability():
    """Test 4: Verify RuntimeObservation is strictly immutable and cannot be modified."""
    obs = RuntimeObservation(
        query="SELECT 1;",
        status=ExecutionStatus.SUCCESS,
        execution_time_ms=1.0,
        row_count=1,
    )

    with pytest.raises(ValidationError):
        # In Pydantic v2 with frozen=True, attribute assignment raises ValidationError
        obs.query = "SELECT 2;"  # type: ignore

    with pytest.raises(ValidationError):
        obs.status = ExecutionStatus.EXECUTION_FAILURE  # type: ignore

    with pytest.raises(ValidationError):
        obs.row_count = 999  # type: ignore


def test_observation_serialization():
    """Test 5: Verify to_dict() outputs clean JSON-serializable structure with all fields."""
    obs = RuntimeObservation(
        query="SELECT region FROM dim_geography;",
        status=ExecutionStatus.SUCCESS,
        raw_error=None,
        normalized_error=None,
        execution_time_ms=2.5,
        row_count=6,
        schema_context=["dim_geography"],
    )

    data = obs.to_dict()

    expected_keys = {
        "observation_id",
        "query",
        "status",
        "raw_error",
        "normalized_error",
        "execution_time_ms",
        "row_count",
        "schema_context",
        "timestamp",
    }
    assert set(data.keys()) == expected_keys
    assert data["status"] == "SUCCESS"
    assert isinstance(data["status"], str)
    assert data["row_count"] == 6
    assert data["schema_context"] == ["dim_geography"]


def test_conservative_normalization():
    """Test 6: Verify normalization cleans formatting while strictly preserving diagnostic details."""
    messy_error = (
        "\r\n\r\n  psycopg2.errors.UndefinedTable: relation \"sales_dw\" does not exist   \r\n"
        "LINE 1: SELECT * FROM sales_dw;    \r\n\r\n\r\n"
        "                      ^   \r\n"
    )
    cleaned = normalize_error_string(messy_error)

    assert cleaned is not None
    # Verifies carriage returns stripped
    assert "\r" not in cleaned
    # Verifies key diagnostic text preserved
    assert 'relation "sales_dw" does not exist' in cleaned
    assert "LINE 1: SELECT * FROM sales_dw;" in cleaned
    assert "^" in cleaned
    # Verifies outer padding stripped
    assert not cleaned.startswith("\n")
    assert not cleaned.endswith(" ")
    # None handling
    assert normalize_error_string(None) is None
