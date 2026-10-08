"""
ARMG Integration Test Suite: Runtime Observation against Live PostgreSQL.
Phase 3 Test Architecture Implementation.

Validates observation layer capturing driver-level exceptions from live PostgreSQL.
Requires live PostgreSQL on localhost:5432.
"""

import pytest
from environment.observation import ExecutionStatus, RuntimeObservation
from environment.observer import RuntimeObserver
from environment.postgres import PostgreSQLEnvironment

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


def test_observation_live_postgres_execution_failure():
    """Live database execution failure observed directly from PostgreSQL adapter."""
    if not is_postgres_online():
        pytest.skip("PostgreSQL database is offline or unreachable on localhost:5432")

    env = PostgreSQLEnvironment()
    try:
        bad_query = "SELECT non_existent_metric FROM fact_sales_performance LIMIT 1;"
        result = env.execute(bad_query)
        assert result.is_success is False

        obs = RuntimeObserver.observe_execution(
            query=bad_query,
            result=result,
            schema_context=["fact_sales_performance"],
        )

        assert obs.status == ExecutionStatus.EXECUTION_FAILURE
        assert obs.is_failure() is True
        assert obs.row_count == 0
        assert obs.raw_error is not None
        assert "does not exist" in obs.raw_error.lower()
        assert obs.normalized_error is not None
        assert "does not exist" in obs.normalized_error.lower()
    finally:
        env.close()
