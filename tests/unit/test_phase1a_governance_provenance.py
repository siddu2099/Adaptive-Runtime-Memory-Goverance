"""
ARMG Phase 1A Regression Tests: Memory Governance State & Provenance Correctness.

Verifies the fundamental invariant:
    Reinforcement(memory_X) is permitted only when memory_X is the memory
    associated with the repair action that actually produced the terminal successful result.

Tests:
    Test A — Successful reuse: Memory applied on successful repair is reinforced.
    Test B — Same failure category across retries: Memory remains active and is reinforced on success.
    Test C — Different failure category (CRITICAL REGRESSION): Stale memory from a prior failed attempt
             is NOT reinforced when a later retry succeeds under a different diagnosis.
    Test D — No memory involved: Successful repair without memory admits novel knowledge without reinforcing.
    Test E — Terminal failure: Failed retries do not trigger false success reinforcement.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pytest

from agents.error_diagnosis import DeterministicErrorDiagnoser, DiagnosticResult
from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from agents.taxonomy import TaxonomyCategory
from environment.base import ExecutionResult, RuntimeEnvironment
from graph.state import STATUS_FAILED, STATUS_RETRYING, STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeMemory
from memory.vector_store import FAISSMemoryStore


class ScriptedWarehouseEnvironment(RuntimeEnvironment):
    """Deterministic environment that returns a predetermined sequence of ExecutionResults."""

    def __init__(self, execution_responses: List[ExecutionResult]):
        self.execution_responses = execution_responses
        self.execution_attempts = 0
        self.executed_sqls: List[str] = []

    def execute(self, sql: str) -> ExecutionResult:
        self.executed_sqls.append(sql)
        if self.execution_attempts < len(self.execution_responses):
            res = self.execution_responses[self.execution_attempts]
        else:
            res = self.execution_responses[-1]
        self.execution_attempts += 1
        return res

    def inspect(self) -> Dict[str, Any]:
        return {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer"},
                        {"name": "geo_key", "type": "integer"},
                        {"name": "gross_revenue", "type": "numeric"},
                        {"name": "net_profit", "type": "numeric"},
                    ]
                }
            }
        }


def make_test_memory(
    memory_id: str,
    root_cause: str,
    repair_strategy: str,
    category: TaxonomyCategory = TaxonomyCategory.SEMANTIC,
    confidence: float = 0.50,
    embedding: Optional[List[float]] = None,
) -> RuntimeMemory:
    """Helper to construct deterministic RuntimeMemory instances."""
    if embedding is None:
        rng = np.random.RandomState(42)
        v = rng.randn(768).astype(np.float32)
        v /= np.linalg.norm(v)
        embedding = v.tolist()

    return RuntimeMemory(
        memory_id=memory_id,
        context={"tables_referenced": ["fact_sales_performance"]},
        failure_type=category,
        root_cause=root_cause,
        repair_strategy=repair_strategy,
        confidence=confidence,
        utility=confidence,
        status=MemoryState.ACTIVE,
        successful_uses=0,
        total_uses=0,
        embedding=embedding,
    )


class TestMemoryGovernanceProvenance:
    """Suite of 5 required test scenarios verifying retry-level repair provenance."""

    def test_scenario_a_successful_reuse(self):
        """Test A: Existing memory retrieved -> applied in Repair 1 -> succeeds -> reinforced."""
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        mem_a = make_test_memory(
            memory_id="mem-sem-001",
            category=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced column 'bad_col_a' does not exist in the active schema.",
            repair_strategy="Replace the invalid column identifier with a schema-valid candidate.",
        )
        vstore.add(mem_a, mem_a.embedding)

        # Attempt 0: fails with undefined column 'bad_col_a'
        # Attempt 1: succeeds
        env = ScriptedWarehouseEnvironment([
            ExecutionResult(
                status="FAILURE",
                query="SELECT bad_col_a FROM fact_sales_performance;",
                error='column "bad_col_a" does not exist\nLINE 1: SELECT bad_col_a FROM fact_sales_performance;',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="SUCCESS",
                query="SELECT net_profit FROM fact_sales_performance;",
                rows=[(100.0,)],
                row_count=1,
                execution_time_ms=1.0,
            ),
        ])

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT bad_col_a FROM fact_sales_performance;",
        )
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="",
                extracted_sql="SELECT net_profit FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=lambda text: mem_a.embedding,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Calculate net profit", "max_retries": 3})

        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 1
        assert res["telemetry"]["memory_admission"] == "EXISTING_REINFORCED"
        assert res["telemetry"]["reinforced_memory_id"] == mem_a.memory_id

        mem_a_after = vstore.get(mem_a.memory_id)
        assert mem_a_after.successful_uses == 1
        assert mem_a_after.confidence > 0.50

    def test_scenario_b_same_failure_category_across_retries(self):
        """Test B: Memory A applied in Retry 1 (fails) -> Retry 2 has same diagnosis -> succeeds -> reinforced."""
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        mem_a = make_test_memory(
            memory_id="mem-sem-002",
            category=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced column 'bad_col_a' does not exist in the active schema.",
            repair_strategy="Replace the invalid column identifier with a schema-valid candidate.",
        )
        vstore.add(mem_a, mem_a.embedding)

        # Attempt 0: fails with bad_col_a
        # Attempt 1: repair 1 also fails with bad_col_a (same diagnosis)
        # Attempt 2: repair 2 succeeds
        env = ScriptedWarehouseEnvironment([
            ExecutionResult(
                status="FAILURE",
                query="SELECT bad_col_a FROM fact_sales_performance;",
                error='column "bad_col_a" does not exist\nLINE 1: SELECT bad_col_a FROM fact_sales_performance;',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="FAILURE",
                query="SELECT bad_col_a FROM fact_sales_performance;",
                error='column "bad_col_a" does not exist\nLINE 1: SELECT bad_col_a FROM fact_sales_performance;',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="SUCCESS",
                query="SELECT net_profit FROM fact_sales_performance;",
                rows=[(100.0,)],
                row_count=1,
                execution_time_ms=1.0,
            ),
        ])

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT bad_col_a FROM fact_sales_performance;",
        )

        repair_attempt = [0]
        def repair_fn(prompt):
            repair_attempt[0] += 1
            if repair_attempt[0] == 1:
                return GenerationResult(raw_response="", extracted_sql="SELECT bad_col_a FROM fact_sales_performance;")
            return GenerationResult(raw_response="", extracted_sql="SELECT net_profit FROM fact_sales_performance;")

        mock_repair = RepairSQLGenerator(generator_fn=repair_fn)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=lambda text: mem_a.embedding,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Calculate net profit", "max_retries": 3})

        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 2
        # Memory A is still the active repair rule for Attempt 2, so it may be reinforced
        assert res["telemetry"]["memory_admission"] == "EXISTING_REINFORCED"
        assert res["telemetry"]["reinforced_memory_id"] == mem_a.memory_id
        mem_a_after = vstore.get(mem_a.memory_id)
        assert mem_a_after.successful_uses == 1

    def test_scenario_c_different_failure_category_stale_memory_not_reinforced(self):
        """Test C (CRITICAL REGRESSION):
        Memory A applied in Retry 1 (Semantic / bad_col_a).
        Retry 1 fails.
        Retry 2 encounters a completely different failure category (Planning / GROUP BY).
        Memory A is NOT applicable to Retry 2.
        Retry 2 succeeds.
        INVARIANT: Memory A must NOT be reinforced merely because applied_memory_id carried over!
        """
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        mem_a = make_test_memory(
            memory_id="mem-sem-stale",
            category=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced column 'bad_col_a' does not exist in the active schema.",
            repair_strategy="Replace the invalid column identifier with a schema-valid candidate.",
            confidence=0.50,
        )
        vstore.add(mem_a, mem_a.embedding)

        # Attempt 0: fails with undefined column (Semantic)
        # Attempt 1: fails with GROUP BY missing error (Planning)
        # Attempt 2: succeeds with valid grouped query
        env = ScriptedWarehouseEnvironment([
            ExecutionResult(
                status="FAILURE",
                query="SELECT bad_col_a FROM fact_sales_performance;",
                error='column "bad_col_a" does not exist\nLINE 1: SELECT bad_col_a FROM fact_sales_performance;',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="FAILURE",
                query="SELECT geo_key, SUM(net_profit) FROM fact_sales_performance;",
                error='column "fact_sales_performance.geo_key" must appear in the GROUP BY clause or be used in an aggregate function',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="SUCCESS",
                query="SELECT geo_key, SUM(net_profit) FROM fact_sales_performance GROUP BY geo_key;",
                rows=[(1, 100.0)],
                row_count=1,
                execution_time_ms=1.0,
            ),
        ])

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT bad_col_a FROM fact_sales_performance;",
        )

        repair_attempt = [0]
        def repair_fn(prompt):
            repair_attempt[0] += 1
            if repair_attempt[0] == 1:
                return GenerationResult(
                    raw_response="",
                    extracted_sql="SELECT geo_key, SUM(net_profit) FROM fact_sales_performance;",
                )
            return GenerationResult(
                raw_response="",
                extracted_sql="SELECT geo_key, SUM(net_profit) FROM fact_sales_performance GROUP BY geo_key;",
            )

        mock_repair = RepairSQLGenerator(generator_fn=repair_fn)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=lambda text: mem_a.embedding,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Calculate net profit by geo", "max_retries": 3})

        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 2

        # CRITICAL INVARIANT: Memory A was NOT the active repair rule for Attempt 2!
        # Memory A must NOT be reinforced!
        mem_a_after = vstore.get(mem_a.memory_id)
        assert mem_a_after.successful_uses == 0, (
            f"STALE REINFORCEMENT DEFECT: Memory {mem_a.memory_id} was reinforced "
            f"(successful_uses={mem_a_after.successful_uses}) even though Attempt 2 succeeded under a different failure category!"
        )
        assert mem_a_after.confidence == 0.50, (
            f"Memory confidence escalated to {mem_a_after.confidence} without causal success!"
        )
        assert res["telemetry"].get("reinforced_memory_id") != mem_a.memory_id
        # Instead, novel knowledge from Attempt 2 may be admitted
        assert res["telemetry"].get("memory_admission") == "ADMITTED"

    def test_scenario_d_no_memory_involved(self):
        """Test D: No retrieved memory -> repair succeeds -> novel knowledge admitted without reinforcement."""
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        env = ScriptedWarehouseEnvironment([
            ExecutionResult(
                status="FAILURE",
                query="SELECT bad_col_xyz FROM fact_sales_performance;",
                error='column "bad_col_xyz" does not exist\nLINE 1: SELECT bad_col_xyz FROM fact_sales_performance;',
                execution_time_ms=1.0,
            ),
            ExecutionResult(
                status="SUCCESS",
                query="SELECT net_profit FROM fact_sales_performance;",
                rows=[(100.0,)],
                row_count=1,
                execution_time_ms=1.0,
            ),
        ])

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT bad_col_xyz FROM fact_sales_performance;",
        )
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="",
                extracted_sql="SELECT net_profit FROM fact_sales_performance;",
            )
        )

        rng = np.random.RandomState(999)
        dummy_vec = rng.randn(768).astype(np.float32)
        dummy_vec /= np.linalg.norm(dummy_vec)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=lambda text: dummy_vec.tolist(),
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Calculate net profit", "max_retries": 3})

        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 1
        assert res["telemetry"].get("reinforced_memory_id") is None
        assert res["telemetry"]["memory_admission"] == "ADMITTED"
        assert vstore.count() == 1

    def test_scenario_e_terminal_failure(self):
        """Test E: Memory applied on Attempt 1 -> all retries fail -> terminal failure -> no false reinforcement."""
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        mem_a = make_test_memory(
            memory_id="mem-sem-fail",
            category=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced column 'bad_col_a' does not exist in the active schema.",
            repair_strategy="Replace the invalid column identifier with a schema-valid candidate.",
            confidence=0.50,
        )
        vstore.add(mem_a, mem_a.embedding)

        # All attempts fail
        fail_res = ExecutionResult(
            status="FAILURE",
            query="SELECT bad_col_a FROM fact_sales_performance;",
            error='column "bad_col_a" does not exist\nLINE 1: SELECT bad_col_a FROM fact_sales_performance;',
            execution_time_ms=1.0,
        )
        env = ScriptedWarehouseEnvironment([fail_res, fail_res, fail_res, fail_res])

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT bad_col_a FROM fact_sales_performance;",
        )
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="",
                extracted_sql="SELECT bad_col_a FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=lambda text: mem_a.embedding,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Calculate net profit", "max_retries": 3})

        assert res["status"] == STATUS_FAILED
        assert res["retry_count"] == 3
        # No success reinforcement occurred
        mem_a_after = vstore.get(mem_a.memory_id)
        assert mem_a_after.successful_uses == 0
        assert res["telemetry"].get("reinforced_memory_id") is None
        assert res["telemetry"]["memory_admission"] == "TERMINAL_FAILURE_NOT_ADMITTED"
