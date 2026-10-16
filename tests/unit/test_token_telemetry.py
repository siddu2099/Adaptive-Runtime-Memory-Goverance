"""
Unit tests for ARMG Phase 2: Ollama Token Telemetry Accounting.

Verifies:
1. Single attempt accounting (prompt_tokens, completion_tokens, total_tokens, metadata_complete).
2. Multi-attempt repair aggregation (accumulated strictly once per generation attempt).
3. Missing metadata handling (explicit None, no silent zeroing or partial total reporting).
4. Subsequent attempts after missing metadata remain incomplete.
5. Double-counting prevention (nodes do not duplicate counts during graph traversals).
6. Zero token handling (distinct from None/missing).
7. Benchmark record propagation (Mode 4 passes telemetry tokens through to QueryBenchmarkRecord).
"""

from typing import Any, Dict, List, Optional
import pytest

from agents.error_diagnosis import DeterministicErrorDiagnoser
from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from benchmark.modes import (
    QueryBenchmarkRecord,
    create_initial_armg_state,
    execute_mode_4_full_armg,
)
from environment.base import ExecutionResult
from graph.state import (
    ARMGState,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_RUNNING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore


# =============================================================================
# Mock Doubles for Offline Unit Testing
# =============================================================================

class MockEnvironment:
    """Mock database environment for testing workflow without PostgreSQL."""

    def __init__(self, fail_until_attempt: int = 1):
        self.catalog = {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer", "is_pk": True},
                        {"name": "gross_revenue", "type": "numeric", "is_pk": False},
                        {"name": "net_profit", "type": "numeric", "is_pk": False},
                    ]
                },
                "dim_geography": {
                    "columns": [
                        {"name": "geo_key", "type": "integer", "is_pk": True},
                        {"name": "region", "type": "varchar", "is_pk": False},
                    ]
                },
            }
        }
        self.fail_until_attempt = fail_until_attempt
        self.call_count = 0

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, sql: str) -> ExecutionResult:
        self.call_count += 1
        if self.call_count < self.fail_until_attempt:
            return ExecutionResult(
                status="FAILURE",
                query=sql,
                error='column "revenue" does not exist\nLINE 1: SELECT revenue FROM fact_sales_performance;\n               ^',
                execution_time_ms=1.5,
            )
        return ExecutionResult(
            status="SUCCESS",
            query=sql,
            rows=[(1, 1000.0, 200.0)],
            error=None,
            execution_time_ms=1.2,
            row_count=1,
        )


class MockSequenceGenerator:
    """Mock SQL generator that returns a pre-configured sequence of GenerationResults."""

    def __init__(self, sequence: List[GenerationResult]):
        self.sequence = list(sequence)
        self.idx = 0

    def generate(self, question: str, schema_markdown: str) -> GenerationResult:
        res = self.sequence[self.idx]
        self.idx = min(self.idx + 1, len(self.sequence) - 1)
        return res

    def generate_repair(self, repair_prompt: str) -> GenerationResult:
        res = self.sequence[self.idx]
        self.idx = min(self.idx + 1, len(self.sequence) - 1)
        return res


def dummy_embed_fn(text: str) -> Optional[List[float]]:
    """Return deterministic unit vector for unit testing."""
    vec = [0.0] * 768
    vec[0] = 1.0
    return vec


# =============================================================================
# Test Suite 1: Single Attempt Token Accounting
# =============================================================================

class TestSingleAttemptTokenAccounting:

    def test_single_attempt_full_metadata(self):
        """Initial attempt with complete token metadata calculates total accurately."""
        env = MockEnvironment(fail_until_attempt=1)
        gen = MockSequenceGenerator([
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=150,
                completion_tokens=42,
                generation_duration_ms=120.0,
            )
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("prompt_tokens") == 150
        assert telemetry.get("completion_tokens") == 42
        assert telemetry.get("total_tokens") == 192
        assert telemetry.get("token_metadata_complete") is True
        assert telemetry.get("generation_attempts") == 1
        assert final_state.get("status") == STATUS_SUCCESS

    def test_single_attempt_missing_prompt_tokens(self):
        """Missing prompt_tokens sets prompt_tokens and total_tokens to None, not 0."""
        env = MockEnvironment(fail_until_attempt=1)
        gen = MockSequenceGenerator([
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=None,
                completion_tokens=42,
                generation_duration_ms=120.0,
            )
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("prompt_tokens") is None
        assert telemetry.get("completion_tokens") == 42
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False
        assert telemetry.get("generation_attempts") == 1

    def test_single_attempt_missing_completion_tokens(self):
        """Missing completion_tokens sets completion_tokens and total_tokens to None."""
        env = MockEnvironment(fail_until_attempt=1)
        gen = MockSequenceGenerator([
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=150,
                completion_tokens=None,
                generation_duration_ms=120.0,
            )
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("prompt_tokens") == 150
        assert telemetry.get("completion_tokens") is None
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False
        assert telemetry.get("generation_attempts") == 1

    def test_single_attempt_all_tokens_missing(self):
        """When both token fields are None, all token counts evaluate to None."""
        env = MockEnvironment(fail_until_attempt=1)
        gen = MockSequenceGenerator([
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=None,
                completion_tokens=None,
                generation_duration_ms=120.0,
            )
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("prompt_tokens") is None
        assert telemetry.get("completion_tokens") is None
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False

    def test_zero_tokens_is_valid_count(self):
        """An integer count of 0 is valid and not treated as missing metadata."""
        env = MockEnvironment(fail_until_attempt=1)
        gen = MockSequenceGenerator([
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=0,
                completion_tokens=25,
                generation_duration_ms=100.0,
            )
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("prompt_tokens") == 0
        assert telemetry.get("completion_tokens") == 25
        assert telemetry.get("total_tokens") == 25
        assert telemetry.get("token_metadata_complete") is True


# =============================================================================
# Test Suite 2: Multi-Attempt Token Aggregation
# =============================================================================

class TestMultiAttemptTokenAggregation:

    def test_two_attempt_repair_aggregation(self):
        """Tokens are aggregated across initial generation and repair attempt."""
        env = MockEnvironment(fail_until_attempt=2)  # Attempt 1 fails, attempt 2 succeeds
        gen = MockSequenceGenerator([
            # Attempt 1 (initial generation - causes column error)
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=110,
                completion_tokens=30,
                generation_duration_ms=100.0,
            ),
            # Attempt 2 (repair attempt - corrected to gross_revenue)
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=160,
                completion_tokens=40,
                generation_duration_ms=150.0,
            ),
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is total gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("generation_attempts") == 2
        assert final_state.get("retry_count") == 1
        assert telemetry.get("prompt_tokens") == 110 + 160  # 270
        assert telemetry.get("completion_tokens") == 30 + 40  # 70
        assert telemetry.get("total_tokens") == 270 + 70  # 340
        assert telemetry.get("token_metadata_complete") is True
        assert final_state.get("status") == STATUS_SUCCESS

    def test_three_attempt_repair_aggregation(self):
        """Tokens accumulate across multiple sequential repair attempts."""
        env = MockEnvironment(fail_until_attempt=3)  # Attempts 1 and 2 fail, attempt 3 succeeds
        gen = MockSequenceGenerator([
            # Attempt 1
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=100,
                completion_tokens=20,
                generation_duration_ms=80.0,
            ),
            # Attempt 2
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=150,
                completion_tokens=30,
                generation_duration_ms=110.0,
            ),
            # Attempt 3
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=200,
                completion_tokens=40,
                generation_duration_ms=140.0,
            ),
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="What is total gross revenue?",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("generation_attempts") == 3
        assert final_state.get("retry_count") == 2
        assert telemetry.get("prompt_tokens") == 100 + 150 + 200  # 450
        assert telemetry.get("completion_tokens") == 20 + 30 + 40  # 90
        assert telemetry.get("total_tokens") == 450 + 90  # 540
        assert telemetry.get("token_metadata_complete") is True
        assert final_state.get("status") == STATUS_SUCCESS


# =============================================================================
# Test Suite 3: Missing Metadata in Multi-Attempt Workflows
# =============================================================================

class TestMissingMetadataInRepairLoop:

    def test_missing_prompt_tokens_in_repair_attempt(self):
        """If a repair attempt lacks prompt_tokens, prompt and total become None."""
        env = MockEnvironment(fail_until_attempt=2)
        gen = MockSequenceGenerator([
            # Attempt 1: Complete metadata
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=100,
                completion_tokens=20,
                generation_duration_ms=80.0,
            ),
            # Attempt 2: Missing prompt_tokens
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=None,
                completion_tokens=35,
                generation_duration_ms=110.0,
            ),
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="Query",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("generation_attempts") == 2
        assert telemetry.get("prompt_tokens") is None
        assert telemetry.get("completion_tokens") == 20 + 35  # 55
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False

    def test_missing_completion_tokens_in_repair_attempt(self):
        """If a repair attempt lacks completion_tokens, completion and total become None."""
        env = MockEnvironment(fail_until_attempt=2)
        gen = MockSequenceGenerator([
            # Attempt 1: Complete metadata
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=100,
                completion_tokens=20,
                generation_duration_ms=80.0,
            ),
            # Attempt 2: Missing completion_tokens
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=130,
                completion_tokens=None,
                generation_duration_ms=110.0,
            ),
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="Query",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("generation_attempts") == 2
        assert telemetry.get("prompt_tokens") == 100 + 130  # 230
        assert telemetry.get("completion_tokens") is None
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False

    def test_subsequent_attempts_after_missing_metadata_remain_incomplete(self):
        """Once metadata is marked incomplete, subsequent attempts do not mask missing count."""
        env = MockEnvironment(fail_until_attempt=3)
        gen = MockSequenceGenerator([
            # Attempt 1: Complete
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=100,
                completion_tokens=20,
                generation_duration_ms=80.0,
            ),
            # Attempt 2: Missing prompt_tokens
            GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
                prompt_tokens=None,
                completion_tokens=25,
                generation_duration_ms=90.0,
            ),
            # Attempt 3: Has prompt_tokens, but total prompt tokens is still unknown
            GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
                prompt_tokens=140,
                completion_tokens=30,
                generation_duration_ms=100.0,
            ),
        ])

        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="Query",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)

        telemetry = final_state.get("telemetry", {})
        assert telemetry.get("generation_attempts") == 3
        # prompt_tokens remains None because attempt 2 was missing
        assert telemetry.get("prompt_tokens") is None
        # completion_tokens had complete metadata across all 3 attempts
        assert telemetry.get("completion_tokens") == 20 + 25 + 30  # 75
        # total_tokens cannot be calculated accurately
        assert telemetry.get("total_tokens") is None
        assert telemetry.get("token_metadata_complete") is False


# =============================================================================
# Test Suite 4: Double-Counting Prevention
# =============================================================================

class TestDoubleCountingPrevention:

    def test_tokens_accumulated_strictly_once_per_generation_attempt(self):
        """Tokens are never accumulated multiple times across intermediate graph nodes."""
        env = MockEnvironment(fail_until_attempt=2)
        attempt1 = GenerationResult(
            raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT revenue FROM fact_sales_performance;",
            prompt_tokens=105,
            completion_tokens=25,
            generation_duration_ms=90.0,
        )
        attempt2 = GenerationResult(
            raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
            extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            prompt_tokens=155,
            completion_tokens=35,
            generation_duration_ms=120.0,
        )

        gen = MockSequenceGenerator([attempt1, attempt2])
        workflow = ARMGRepairWorkflow(
            environment=env,
            sql_generator=gen,
            repair_generator=gen,
            embed_fn=dummy_embed_fn,
        )
        app = workflow.build_graph()

        initial_state = create_initial_armg_state(
            user_query="Query",
            max_retries=3,
        )
        final_state = app.invoke(initial_state)
        telemetry = final_state.get("telemetry", {})

        # Expected counts are EXACTLY the sum of attempt1 and attempt2 (1:1, no extra additions)
        expected_prompt = attempt1.prompt_tokens + attempt2.prompt_tokens
        expected_comp = attempt1.completion_tokens + attempt2.completion_tokens
        expected_total = expected_prompt + expected_comp

        assert telemetry.get("prompt_tokens") == expected_prompt
        assert telemetry.get("completion_tokens") == expected_comp
        assert telemetry.get("total_tokens") == expected_total
        assert telemetry.get("generation_attempts") == 2


# =============================================================================
# Test Suite 5: Benchmark Mode 4 Record Propagation
# =============================================================================

class TestBenchmarkRecordTokenPropagation:

    def test_mode4_benchmark_record_preserves_tokens(self):
        """execute_mode_4_full_armg correctly sets prompt, completion, and total tokens."""
        class MockWorkflowApp:
            def invoke(self, state: ARMGState) -> Dict[str, Any]:
                return {
                    "status": STATUS_SUCCESS,
                    "validation_passed": True,
                    "execution_result": ExecutionResult(
                        status="SUCCESS",
                        query="SELECT gross_revenue FROM fact_sales_performance;",
                        rows=[(1, 1000.0, 200.0)],
                        error=None,
                        execution_time_ms=1.2,
                        row_count=1,
                    ),
                    "generated_sql": "SELECT gross_revenue FROM fact_sales_performance;",
                    "retry_count": 1,
                    "telemetry": {
                        "prompt_tokens": 270,
                        "completion_tokens": 70,
                        "total_tokens": 340,
                        "generation_attempts": 2,
                    },
                }

        class MockEnvForBenchmark:
            def execute(self, sql: str) -> ExecutionResult:
                return ExecutionResult(
                    status="SUCCESS",
                    query=sql,
                    rows=[(1, 1000.0, 200.0)],
                    error=None,
                    execution_time_ms=1.0,
                    row_count=1,
                )

        query_item = {
            "query_id": "Q01",
            "category": "Category A",
            "question": "What is gross revenue?",
            "gold_sql": "SELECT gross_revenue FROM fact_sales_performance;",
        }

        record = execute_mode_4_full_armg(
            query_item=query_item,
            env=MockEnvForBenchmark(),
            run_id="test_run",
            seed=42,
            workflow_app=MockWorkflowApp(),
        )

        assert record.prompt_tokens == 270
        assert record.completion_tokens == 70
        assert record.total_tokens == 340
        assert record.retry_count == 1
        assert record.generation_attempts == 2

    def test_mode4_benchmark_record_carries_none_when_metadata_missing(self):
        """execute_mode_4_full_armg preserves None when telemetry indicates incomplete data."""
        class MockWorkflowApp:
            def invoke(self, state: ARMGState) -> Dict[str, Any]:
                return {
                    "status": STATUS_SUCCESS,
                    "validation_passed": True,
                    "execution_result": ExecutionResult(
                        status="SUCCESS",
                        query="SELECT gross_revenue FROM fact_sales_performance;",
                        rows=[(1, 1000.0, 200.0)],
                        error=None,
                        execution_time_ms=1.2,
                        row_count=1,
                    ),
                    "generated_sql": "SELECT gross_revenue FROM fact_sales_performance;",
                    "retry_count": 0,
                    "telemetry": {
                        "prompt_tokens": None,
                        "completion_tokens": 40,
                        "total_tokens": None,
                        "generation_attempts": 1,
                    },
                }

        class MockEnvForBenchmark:
            def execute(self, sql: str) -> ExecutionResult:
                return ExecutionResult(
                    status="SUCCESS",
                    query=sql,
                    rows=[(1, 1000.0, 200.0)],
                    error=None,
                    execution_time_ms=1.0,
                    row_count=1,
                )

        query_item = {
            "query_id": "Q01",
            "category": "Category A",
            "question": "What is gross revenue?",
            "gold_sql": "SELECT gross_revenue FROM fact_sales_performance;",
        }

        record = execute_mode_4_full_armg(
            query_item=query_item,
            env=MockEnvForBenchmark(),
            run_id="test_run",
            seed=42,
            workflow_app=MockWorkflowApp(),
        )

        assert record.prompt_tokens is None
        assert record.completion_tokens == 40
        assert record.total_tokens is None
