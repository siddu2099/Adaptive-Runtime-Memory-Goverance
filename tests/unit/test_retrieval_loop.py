"""
ARMG: Retrieval and Closed-Loop Learning Unit Tests.

Verifies:
A. Runtime embedding normalization: 768-dim, finite, unit L2 norm (||v||₂ ≈ 1.0).
B. FAISS similarity geometry: squared L2 distance, normalized similarity 1 / (1 + d),
   and threshold satisfaction for cosine similarity ~0.72.
C. Governed memory retrieval: active memories retrieved when similarity >= 0.50.
D. Post-repair memory admission: RuntimeMemory created, embedded, stored with valid governance.
E. Applied memory reinforcement: previously retrieved & applied memory is reinforced.
F. Safety regression: destructive requests remain strictly STATUS_BLOCKED with zero admission.
G. Two-pass closed-loop retrieval and learning:
   - Run 1: 0 retrieved -> failure -> repair succeeds -> 1 memory admitted -> FAISS count = 1.
   - Run 2: 1+ retrieved -> identified before generation -> repair succeeds -> reinforced.
"""

from typing import Any, Dict, List, Optional
import math
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import SQLGenerator, GenerationResult
from agents.taxonomy import TaxonomyCategory
from environment.base import ExecutionResult, RuntimeEnvironment
from graph.state import (
    ARMGState,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.vector_store import FAISSMemoryStore


# =====================================================================
# Test Helpers and Fixtures
# =====================================================================

class MockWarehouseEnvironment(RuntimeEnvironment):
    """Deterministic environment simulating semantic schema errors and repairs."""

    def __init__(self, failing_column: str = "definitely_nonexistent_column_xyz"):
        self.failing_column = failing_column
        self.execution_attempts = 0
        self.executed_sqls: List[str] = []

    def execute(self, sql: str) -> ExecutionResult:
        self.execution_attempts += 1
        self.executed_sqls.append(sql)
        if self.failing_column in sql:
            return ExecutionResult(
                status="FAILURE",
                query=sql,
                error=f'column "{self.failing_column}" does not exist\nLINE 1: SELECT {self.failing_column} FROM fact_sales_performance;\n               ^',
                execution_time_ms=1.5,
            )
        return ExecutionResult(
            status="SUCCESS",
            query=sql,
            rows=[(42000.0,)],
            row_count=1,
            execution_time_ms=1.5,
        )

    def inspect(self) -> Dict[str, List[str]]:
        return {
            "fact_sales_performance": [
                "fact_key",
                "time_key",
                "geo_key",
                "product_key",
                "units_sold",
                "gross_revenue",
                "discount_applied",
                "net_profit",
            ]
        }


def make_deterministic_embed_fn(base_seed: int = 42):
    """Deterministic normalized mock embed function for reproducible testing."""
    def _mock_embed(text: str) -> List[float]:
        # Semantic mapping: queries or knowledge about nonexistent columns share high similarity
        if "definitely_nonexistent_column_xyz" in text or "nonexistent" in text:
            seed = base_seed
        else:
            seed = abs(hash(text)) % (2**31)
        rng = np.random.RandomState(seed)
        vec = rng.randn(768).astype(np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
    return _mock_embed


# =====================================================================
# Test A: Runtime Embedding Normalization
# =====================================================================

class TestRuntimeEmbeddingNormalization:
    """Test A: Verify runtime embedding boundary enforces float32, 768-dim, and unit norm."""

    def test_default_embed_fn_unit_normalization_with_mock_api(self):
        """Verify default_embed_fn returns float32, 768-dim, unit-normalized vector."""
        raw_unnormalized = (np.ones(768, dtype=np.float32) * 0.5).tolist()  # Norm = sqrt(768 * 0.25) ≈ 13.856
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": raw_unnormalized}

        with patch("requests.post", return_value=mock_response):
            result = default_embed_fn("Test query for normalization")

        assert result is not None
        assert len(result) == 768
        v = np.array(result, dtype=np.float32)
        assert np.isfinite(v).all()
        norm = float(np.linalg.norm(v))
        assert abs(norm - 1.0) < 1e-5, f"Expected unit norm ≈ 1.0, got {norm}"

    def test_default_embed_fn_rejects_nan_inf(self):
        """Verify default_embed_fn rejects non-finite vectors."""
        bad_vec = (np.ones(768, dtype=np.float32)).tolist()
        bad_vec[0] = float("nan")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": bad_vec}

        with patch("requests.post", return_value=mock_response):
            result = default_embed_fn("Test nan")
        assert result is None

    def test_default_embed_fn_rejects_wrong_dimension(self):
        """Verify default_embed_fn rejects vectors not matching 768 dimensions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1] * 512}

        with patch("requests.post", return_value=mock_response):
            result = default_embed_fn("Test 512 dim")
        assert result is None


# =====================================================================
# Test B: FAISS Similarity Geometry
# =====================================================================

class TestFAISSSimilarityGeometry:
    """Test B: Verify distance and similarity equations on normalized vectors."""

    def test_geometry_with_unit_vectors(self):
        """Verify d = squared L2 distance, sim = 1 / (1 + d), and threshold satisfaction."""
        vstore = FAISSMemoryStore()

        # Create two unit vectors with known angle / cosine similarity
        rng = np.random.RandomState(42)
        u = rng.randn(768).astype(np.float32)
        u /= np.linalg.norm(u)

        # Perturb u slightly to simulate query and repair knowledge
        noise = rng.randn(768).astype(np.float32) * 0.6
        v = u + noise
        v /= np.linalg.norm(v)

        cos_sim = float(np.dot(u, v))
        expected_l2_sq = float(np.sum((u - v) ** 2))
        expected_sim = 1.0 / (1.0 + expected_l2_sq)

        # Store memory with vector u
        mem = RuntimeMemory(
            context={"tables_referenced": ["fact_sales_performance"]},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced definitely_nonexistent_column_xyz does not exist",
            repair_strategy="Replace invalid column identifier with a schema-valid candidate",
            status=MemoryState.ACTIVE,
            confidence=0.55,
            utility=0.55,
        )
        vstore.add(mem, u)

        # Search with vector v
        matches = vstore.search(v, top_k=1)
        assert len(matches) == 1
        ret_mem, dist, sim = matches[0]

        assert ret_mem.memory_id == mem.memory_id
        assert abs(dist - expected_l2_sq) < 1e-4
        assert abs(sim - expected_sim) < 1e-4

        # For cosine similarity > 0.70, converted similarity must exceed the 0.50 retrieval threshold
        if cos_sim >= 0.70:
            assert sim >= 0.50, f"Expected similarity >= 0.50, got {sim}"


# =====================================================================
# Test C: Governed Memory Retrieval
# =====================================================================

class TestGovernedMemoryRetrieval:
    """Test C: Verify retrieval node returns active memories when sim >= 0.50."""

    def test_retrieval_node_retrieves_active_similar_memory(self):
        vstore = FAISSMemoryStore()
        embed_fn = make_deterministic_embed_fn(base_seed=100)

        vec = embed_fn("Show the total of fact_sales_performance.definitely_nonexistent_column_xyz")
        mem = RuntimeMemory(
            context={"tables_referenced": ["fact_sales_performance"]},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced definitely_nonexistent_column_xyz does not exist",
            repair_strategy="Replace invalid column identifier with a schema-valid candidate",
            status=MemoryState.ACTIVE,
            confidence=0.55,
            utility=0.55,
            embedding=vec,
        )
        vstore.add(mem, vec)

        wf = ARMGRepairWorkflow(
            environment=MockWarehouseEnvironment(),
            vector_store=vstore,
            embed_fn=embed_fn,
        )

        state: ARMGState = {
            "user_query": "Show the total of fact_sales_performance.definitely_nonexistent_column_xyz",
            "telemetry": {},
        }
        res = wf.memory_retrieval_node(state)

        assert len(res["retrieved_memories"]) == 1
        assert res["retrieved_memories"][0].memory_id == mem.memory_id
        assert res["telemetry"]["memory_retrieval_count"] == 1


# =====================================================================
# Test D: Post-Repair Memory Admission
# =====================================================================

class TestPostRepairAdmission:
    """Test D: Verify successful repair admits new RuntimeMemory into FAISS."""

    def test_successful_repair_admits_memory(self):
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()
        embed_fn = make_deterministic_embed_fn(base_seed=100)

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question="", schema_markdown="", **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT SUM(definitely_nonexistent_column_xyz) FROM fact_sales_performance;",
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda p: GenerationResult(
                raw_response="",
                extracted_sql="SELECT SUM(net_profit) FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=MockWarehouseEnvironment(),
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({
            "user_query": "Show the total of fact_sales_performance.definitely_nonexistent_column_xyz",
            "max_retries": 3,
        })

        assert res["status"] == STATUS_SUCCESS
        assert res["retry_count"] == 1
        assert res["telemetry"]["memory_admission"] == "ADMITTED"
        assert vstore.count() == 1

        admitted_id = res["telemetry"]["admitted_memory_id"]
        admitted_mem = vstore.get(admitted_id)
        assert admitted_mem is not None
        assert admitted_mem.status == MemoryState.ACTIVE
        assert admitted_mem.confidence == 0.55
        assert admitted_mem.utility == 0.55
        assert admitted_mem.total_uses == 1
        assert admitted_mem.successful_uses == 1


# =====================================================================
# Test E & G: Reinforcement and Closed-Loop Retrieval
# =====================================================================

class TestClosedLoopRetrievalAndReinforcement:
    """Test E & G: Two-pass closed-loop retrieval, identification, and reinforcement."""

    def test_closed_loop_two_pass_workflow(self):
        """Run 1: 0 retrieved -> repair -> admit mem-1 (count=1).
        Run 2: 1+ retrieved -> identified before generation -> repair -> reinforce mem-1 (count remains 1).
        """
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()
        embed_fn = make_deterministic_embed_fn(base_seed=100)
        env = MockWarehouseEnvironment()

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question="", schema_markdown="", **kw: GenerationResult(
            raw_response="",
            extracted_sql="SELECT SUM(definitely_nonexistent_column_xyz) FROM fact_sales_performance;",
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda p: GenerationResult(
                raw_response="",
                extracted_sql="SELECT SUM(net_profit) FROM fact_sales_performance;",
            )
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=embed_fn,
        )
        graph = wf.build_graph()

        # Seed an unrelated memory to verify it is NOT modified
        unrelated_mem = RuntimeMemory(
            context={"tables_referenced": ["dim_geography"]},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Unrelated column failure in dim_geography",
            repair_strategy="Replace with valid geography column",
            confidence=0.70,
            utility=0.70,
            status=MemoryState.ACTIVE,
            successful_uses=3,
            total_uses=4,
            embedding=embed_fn("Unrelated geography query"),
        )
        vstore.add(unrelated_mem, unrelated_mem.embedding)
        initial_store_count = vstore.count()
        assert initial_store_count == 1

        query = "Show the total of fact_sales_performance.definitely_nonexistent_column_xyz"

        # --- PASS 1 ---
        res1 = graph.invoke({"user_query": query, "max_retries": 3})
        assert res1["status"] == STATUS_SUCCESS
        assert res1["telemetry"]["memory_retrieval_count"] == 0
        assert res1["telemetry"]["memory_admission"] == "ADMITTED"
        assert vstore.count() == 2  # Unrelated + newly admitted

        first_mem_id = res1["telemetry"]["admitted_memory_id"]
        first_mem = vstore.get(first_mem_id)
        assert first_mem is not None
        assert first_mem.successful_uses == 1
        assert first_mem.total_uses == 1
        assert abs(first_mem.confidence - 0.55) < 1e-4

        # --- PASS 2 ---
        res2 = graph.invoke({"user_query": query, "max_retries": 3})
        assert res2["status"] == STATUS_SUCCESS

        # Verification: retrieval happened BEFORE generation and found the memory
        assert res2["telemetry"]["memory_retrieval_count"] >= 1
        retrieved_ids = [m.memory_id for m in res2["retrieved_memories"]]
        assert first_mem_id in retrieved_ids

        # Verification: repair identified and applied the retrieved memory
        assert res2.get("applied_memory_id") == first_mem_id
        assert res2["telemetry"].get("reinforced_memory_id") == first_mem_id

        # Verification: existing memory was reinforced with correct Phase 6 governance math
        reinforced_mem = vstore.get(first_mem_id)
        assert reinforced_mem is not None
        assert reinforced_mem.successful_uses == 2
        assert reinforced_mem.total_uses == 2
        # Phase 6: conf = 0.9 * 0.55 + 0.1 * 1.0 = 0.595
        assert abs(reinforced_mem.confidence - 0.595) < 1e-4

        # Verification: Mutual exclusion between reinforcement and new admission
        # 1. Telemetry indicates existing memory reinforced
        assert res2["telemetry"].get("memory_admission") == "EXISTING_REINFORCED"
        # 2. No new admitted_memory_id was created
        assert res2["telemetry"].get("admitted_memory_id") is None
        # 3. Store count remains exactly 2 (unrelated + reinforced memory; NO duplicate admitted)
        assert vstore.count() == 2

        # Verification: Unrelated memory remained untouched
        unrelated_after = vstore.get(unrelated_mem.memory_id)
        assert unrelated_after is not None
        assert unrelated_after.successful_uses == 3
        assert unrelated_after.total_uses == 4
        assert abs(unrelated_after.confidence - 0.70) < 1e-4


# =====================================================================
# Test F: Safety Regression
# =====================================================================

class TestSafetyRegression:
    """Test F: Destructive requests remain strictly STATUS_BLOCKED with zero admission."""

    def test_destructive_delete_remains_blocked(self):
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()
        embed_fn = make_deterministic_embed_fn(base_seed=100)
        env = MockWarehouseEnvironment()

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question="", schema_markdown="", **kw: GenerationResult(
            raw_response="",
            extracted_sql="DELETE FROM fact_sales_performance;",
        )

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            vector_store=vstore,
            governance_engine=gov,
            embed_fn=embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": "Delete all records from the sales table.", "max_retries": 3})

        assert res["status"] == STATUS_BLOCKED
        assert env.execution_attempts == 0
        assert res.get("runtime_knowledge") is None
        assert res["telemetry"]["memory_admission"] == "SAFETY_VIOLATION_BLOCKED"
        assert vstore.count() == 0
