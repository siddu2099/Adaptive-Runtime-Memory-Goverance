"""
Hermetic Unit Tests for RuntimeEnvironment Protocol & ExecutionResult Contract.
Phase 3 Test Architecture Implementation.

Verifies:
1. RuntimeEnvironment Protocol conformance with test double.
2. ExecutionResult model properties (status, query, error, rows, row_count, execution_time_ms).
3. Zero network, zero database execution.
"""

from typing import Any, Dict, List
import pytest
from environment.base import ExecutionResult, RuntimeEnvironment


class InMemTestEnvironment(RuntimeEnvironment):
    """Hermetic test double conforming to RuntimeEnvironment protocol."""

    def __init__(self):
        self.executed_queries: List[str] = []

    def execute(self, sql: str) -> ExecutionResult:
        self.executed_queries.append(sql)
        return ExecutionResult(
            status="SUCCESS",
            query=sql,
            rows=[(1, "Test")],
            row_count=1,
            execution_time_ms=0.5,
        )

    def inspect(self) -> Dict[str, Any]:
        return {
            "tables": {
                "mock_table": {
                    "columns": [{"name": "id", "type": "integer", "primary_key": True}]
                }
            }
        }


def test_runtime_environment_protocol_conformance():
    """Verify test double conforms to RuntimeEnvironment protocol."""
    env = InMemTestEnvironment()
    assert isinstance(env, RuntimeEnvironment)


def test_execution_result_properties():
    """Verify ExecutionResult property access and helper flags."""
    res_success = ExecutionResult(
        status="SUCCESS",
        query="SELECT 1;",
        rows=[(1,)],
        row_count=1,
        execution_time_ms=1.2,
    )
    assert res_success.is_success is True
    assert res_success.error is None
    assert res_success.row_count == 1
    assert len(res_success.rows) == 1

    res_fail = ExecutionResult(
        status="FAILURE",
        query="SELECT bad;",
        error="column bad does not exist",
        execution_time_ms=0.8,
    )
    assert res_fail.is_success is False
    assert res_fail.error == "column bad does not exist"
    assert res_fail.row_count == 0


def test_in_mem_inspect_structure():
    """Verify inspect() returns expected dictionary catalog format."""
    env = InMemTestEnvironment()
    catalog = env.inspect()
    assert "tables" in catalog
    assert "mock_table" in catalog["tables"]
