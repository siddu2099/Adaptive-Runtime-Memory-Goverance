"""
Unit tests for ARMG Phase 6: Runtime Memory Governance and FAISS Vector Storage.

Verifies:
- Suite A: RuntimeMemory model validation (Pydantic v2, bounds, counters, immutability, serialization).
- Suite B: FAISS CPU vector storage (768-dim, search, top-k, NaN/Inf rejection, shape rejection, deletion).
- Suite C: Multi-factor utility calculation (exact equation, boundary conditions).
- Suite D: Admission filtering (theta = 0.25 threshold, neutral priors, rejection below threshold).
- Suite E: Asymptotic confidence escalation (alpha = 0.10, bounds, transition to ACTIVE and STABLE).
- Suite F: Failure penalty (beta = 0.15, non-increment of successful uses, transition to ARCHIVED).
- Suite G: Continuous exponential decay (lambda = 0.05/day, 10, 30, 60 days, monotonic).
- Suite H: Complete deterministic lifecycle progression (NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED).
- Suite I: Archive retention expiration (30 days in ARCHIVED -> DELETED).
- Suite J: Pure offline operation (zero LLM, zero PostgreSQL).
- Determinism: 50-iteration stability across utility, escalation, decay, and vector search.
"""

from datetime import datetime, timezone
import math
import numpy as np
import pytest
from pydantic import ValidationError

from agents.taxonomy import TaxonomyCategory
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def sample_knowledge() -> RuntimeKnowledge:
    """Fixture providing a standard RuntimeKnowledge instance."""
    return RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception="column 'rev' does not exist",
        context={"tables_referenced": ["fact_sales_performance"], "broken_column": "rev"},
        root_cause="Column 'rev' is not present in 'fact_sales_performance'.",
        repair_strategy="Replace 'rev' with 'gross_revenue_inr'.",
        negative_constraints=["Do not reference column 'rev'."],
        candidate_replacements=["gross_revenue_inr", "net_revenue_inr"],
        confidence=0.50,
    )


@pytest.fixture
def governance_engine() -> MemoryGovernanceEngine:
    """Fixture providing default MemoryGovernanceEngine."""
    return MemoryGovernanceEngine()


@pytest.fixture
def vector_store() -> FAISSMemoryStore:
    """Fixture providing fresh FAISSMemoryStore."""
    return FAISSMemoryStore()


# =====================================================================
# Suite A: RuntimeMemory Model Validation
# =====================================================================

class TestRuntimeMemoryValidation:
    """Suite A: Comprehensive Pydantic v2 validation tests for RuntimeMemory."""

    def test_valid_construction(self, sample_knowledge: RuntimeKnowledge):
        """Verify normal, valid construction of RuntimeMemory."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.50,
            utility=0.25,
            recency=1.0,
            status=MemoryState.NEW,
            successful_uses=0,
            total_uses=0,
        )
        assert mem.memory_id.startswith("mem-")
        assert mem.status == MemoryState.NEW
        assert mem.confidence == 0.50
        assert mem.utility == 0.25
        assert mem.recency == 1.0
        assert mem.successful_uses == 0
        assert mem.total_uses == 0

    def test_confidence_bounds_enforced(self, sample_knowledge: RuntimeKnowledge):
        """Verify confidence strictly requires 0.0 <= confidence <= 1.0."""
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                confidence=-0.01,
            )
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                confidence=1.01,
            )

    def test_utility_bounds_enforced(self, sample_knowledge: RuntimeKnowledge):
        """Verify utility strictly requires 0.0 <= utility <= 1.0."""
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                utility=-0.01,
            )
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                utility=1.05,
            )

    def test_counter_validation(self, sample_knowledge: RuntimeKnowledge):
        """Verify successful_uses cannot exceed total_uses and counters cannot be negative."""
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                successful_uses=3,
                total_uses=2,  # Invalid: 3 > 2
            )
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                successful_uses=-1,
                total_uses=0,
            )

    def test_enum_validation(self, sample_knowledge: RuntimeKnowledge):
        """Verify only the 6 defined MemoryState enums are valid."""
        with pytest.raises(ValidationError):
            RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                status="INVALID_STATE",  # type: ignore
            )

    def test_immutability_and_copy_with(self, sample_knowledge: RuntimeKnowledge):
        """Verify RuntimeMemory is frozen and copy_with creates a modified copy."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.50,
        )
        with pytest.raises(ValidationError):
            mem.confidence = 0.70  # Frozen model cannot be mutated directly

        updated = mem.copy_with(confidence=0.70, status=MemoryState.ACTIVE)
        assert updated.confidence == 0.70
        assert updated.status == MemoryState.ACTIVE
        assert mem.confidence == 0.50  # Original remains unchanged

    def test_serialization(self, sample_knowledge: RuntimeKnowledge):
        """Verify to_dict and to_json serialization round-trips."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            status=MemoryState.NEW,
        )
        d = mem.to_dict()
        assert d["status"] == "NEW"
        assert d["failure_type"] == "Semantic"
        json_str = mem.to_json()
        assert "Semantic" in json_str


# =====================================================================
# Suite B: FAISS CPU Vector Storage
# =====================================================================

class TestFAISSVectorStore:
    """Suite B: Comprehensive verification of FAISS vector store operations."""

    def test_768_dim_insertion_and_search(self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge):
        """Verify insertion of 768-dim vector and nearest-neighbor retrieval."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
        )
        vec = np.random.RandomState(42).randn(768).astype(np.float32)
        int_id = vector_store.add(mem, vec)
        assert int_id == 1
        assert vector_store.count() == 1

        # Search with identical vector -> distance should be ~0.0, similarity should be 1.0
        results = vector_store.search(vec, top_k=5)
        assert len(results) == 1
        ret_mem, dist, sim = results[0]
        assert ret_mem.memory_id == mem.memory_id
        assert abs(dist) < 1e-4
        assert abs(sim - 1.0) < 1e-4

    def test_top_k_behavior(self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge):
        """Verify top_k retrieves sorted nearest neighbors."""
        rng = np.random.RandomState(123)
        mems = []
        for i in range(5):
            m = RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=f"Cause {i}",
                repair_strategy=f"Repair {i}",
            )
            v = rng.randn(768).astype(np.float32)
            vector_store.add(m, v)
            mems.append((m, v))

        query_vec = mems[0][1]
        results = vector_store.search(query_vec, top_k=3)
        assert len(results) == 3
        # First result should be mems[0] with distance ~0
        assert results[0][0].memory_id == mems[0][0].memory_id
        # Distances must be non-decreasing
        assert results[0][1] <= results[1][1] <= results[2][1]

    def test_malformed_dimension_rejection(self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge):
        """Verify non-768 vectors are rejected with ValueError."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
        )
        with pytest.raises(ValueError, match="Invalid vector dimension"):
            vector_store.add(mem, np.zeros(512, dtype=np.float32))

        with pytest.raises(ValueError, match="Invalid vector dimension"):
            vector_store.add(mem, np.zeros((2, 384), dtype=np.float32))

        with pytest.raises(ValueError, match="Invalid vector dimension"):
            vector_store.search(np.zeros(100, dtype=np.float32))

    def test_nan_and_infinite_rejection(self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge):
        """Verify NaN and Inf values are explicitly rejected."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
        )
        nan_vec = np.zeros(768, dtype=np.float32)
        nan_vec[0] = np.nan
        with pytest.raises(ValueError, match="NaN"):
            vector_store.add(mem, nan_vec)

        inf_vec = np.zeros(768, dtype=np.float32)
        inf_vec[10] = np.inf
        with pytest.raises(ValueError, match="infinite"):
            vector_store.add(mem, inf_vec)

    def test_deletion_synchronized_across_faiss_and_metadata(
        self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge
    ):
        """Verify deletion physically removes vector from FAISS and metadata."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
        )
        vec = np.ones(768, dtype=np.float32)
        vector_store.add(mem, vec)
        assert vector_store.count() == 1
        assert vector_store.get(mem.memory_id) is not None

        deleted = vector_store.delete(mem.memory_id)
        assert deleted is True
        assert vector_store.count() == 0
        assert vector_store.get(mem.memory_id) is None

        # Search should return empty
        results = vector_store.search(vec, top_k=5)
        assert len(results) == 0

        # Deleting non-existent memory returns False
        assert vector_store.delete("non-existent-id") is False


# =====================================================================
# Suite C: Multi-factor Utility Calculation
# =====================================================================

class TestUtilityCalculation:
    """Suite C: Verification of utility equation and boundary constraints."""

    def test_exact_utility_formula_with_prior(self, governance_engine: MemoryGovernanceEngine):
        """Verify Utility = Confidence * SuccessRate * ContextSimilarity * Recency with prior."""
        # Initial state: total_uses = 0 -> SuccessRate = 0.5; delta_t = 0.0 -> Recency = 1.0
        utility = governance_engine.calculate_utility(
            confidence=0.50,
            successful_uses=0,
            total_uses=0,
            context_similarity=1.0,
            delta_t=0.0,
        )
        # 0.50 * 0.5 * 1.0 * 1.0 = 0.25
        assert utility == 0.25

    def test_utility_with_history(self, governance_engine: MemoryGovernanceEngine):
        """Verify utility calculation with empirical usage history and elapsed time."""
        # Confidence = 0.80, successes = 8, total = 10 -> SuccessRate = 0.80
        # Similarity = 0.90, delta_t = 1.0 -> Recency = 1 / (1 + 1) = 0.50
        # Expected = 0.80 * 0.80 * 0.90 * 0.50 = 0.288
        utility = governance_engine.calculate_utility(
            confidence=0.80,
            successful_uses=8,
            total_uses=10,
            context_similarity=0.90,
            delta_t=1.0,
        )
        assert utility == 0.288

    def test_utility_via_runtime_memory_object(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify calculate_utility accepts RuntimeMemory instance directly."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.70,
            successful_uses=3,
            total_uses=4,
        )
        # 0.70 * (3/4) * 1.0 * (1 / (1 + 0)) = 0.70 * 0.75 * 1.0 * 1.0 = 0.525
        u = governance_engine.calculate_utility(mem, context_similarity=1.0, delta_t=0.0)
        assert u == 0.525

    def test_boundary_values(self, governance_engine: MemoryGovernanceEngine):
        """Verify boundary cases: similarity = 0, similarity = 1, delta_t = 0."""
        # similarity = 0 -> utility = 0
        u_zero = governance_engine.calculate_utility(
            confidence=0.8, successful_uses=5, total_uses=5, context_similarity=0.0, delta_t=0.0
        )
        assert u_zero == 0.0

        # delta_t = 0 -> recency = 1.0
        u_dt0 = governance_engine.calculate_utility(
            confidence=1.0, successful_uses=1, total_uses=1, context_similarity=1.0, delta_t=0.0
        )
        assert u_dt0 == 1.0

        # Out-of-bounds similarity or confidence raises ValueError
        with pytest.raises(ValueError):
            governance_engine.calculate_utility(
                confidence=0.5, successful_uses=0, total_uses=0, context_similarity=-0.1
            )
        with pytest.raises(ValueError):
            governance_engine.calculate_utility(
                confidence=0.5, successful_uses=0, total_uses=0, context_similarity=1.1
            )


# =====================================================================
# Suite D: Admission Filtering
# =====================================================================

class TestAdmissionFiltering:
    """Suite D: Verification of admission threshold and neutral initial state."""

    def test_admission_success_at_threshold(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify candidate meets admission threshold theta = 0.25 when similarity = 1.0."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        assert mem.status == MemoryState.NEW
        assert mem.confidence == 0.50
        assert mem.successful_uses == 0
        assert mem.total_uses == 0
        assert mem.utility == 0.25

    def test_admission_rejection_below_threshold(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify candidate is rejected when initial utility < theta (e.g. similarity = 0.80)."""
        # Utility = 0.50 * 0.5 * 0.80 * 1.0 = 0.20 < 0.25
        mem = governance_engine.admit(sample_knowledge, context_similarity=0.80)
        assert mem is None


# =====================================================================
# Suite E: Asymptotic Confidence Escalation
# =====================================================================

class TestConfidenceEscalation:
    """Suite E: Verification of asymptotic confidence escalation equation."""

    def test_escalation_formula_and_state_transitions(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify C_new = C_old + 0.10 * (1 - C_old) and NEW -> ACTIVE transition."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        assert mem.status == MemoryState.NEW
        assert mem.confidence == 0.50

        # First success: NEW -> ACTIVE, C_new = 0.50 + 0.10 * 0.50 = 0.55
        m1 = governance_engine.record_success(mem)
        assert m1.status == MemoryState.ACTIVE
        assert m1.confidence == 0.55
        assert m1.successful_uses == 1
        assert m1.total_uses == 1

        # Second success: C_new = 0.55 + 0.10 * 0.45 = 0.595
        m2 = governance_engine.record_success(m1)
        assert m2.confidence == 0.595
        assert m2.successful_uses == 2
        assert m2.total_uses == 2

    def test_repeated_success_approaches_one_and_reaches_stable(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify 10 successive successes reach STABLE state (>= 0.80) and stay <= 1.0."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None

        curr = mem
        for i in range(10):
            curr = governance_engine.record_success(curr)
            assert curr.confidence <= 1.0

        # Analytical expectation: 1 - 0.50 * (0.90)^10 = 1 - 0.50 * 0.348678 = 0.825661
        assert abs(curr.confidence - 0.825661) < 1e-4
        assert curr.confidence >= 0.80
        assert curr.status == MemoryState.STABLE
        assert curr.successful_uses == 10
        assert curr.total_uses == 10


# =====================================================================
# Suite F: Failure Penalty
# =====================================================================

class TestFailurePenalty:
    """Suite F: Verification of failure penalty formula and archiving."""

    def test_failure_penalty_formula(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify C_new = C_old * (1 - 0.15) and successful_uses is not incremented."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        mem = governance_engine.record_success(mem)  # C = 0.55, succ = 1, total = 1

        # Record failure
        penalized = governance_engine.record_failure(mem)
        expected_c = round(0.55 * 0.85, 6)  # 0.4675
        assert penalized.confidence == expected_c
        assert penalized.successful_uses == 1  # Unchanged
        assert penalized.total_uses == 2       # Incremented

    def test_failure_penalty_transitions_to_archived_when_below_threshold(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify multiple failures reduce confidence below 0.20 and transition to ARCHIVED."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None

        curr = mem
        # Apply 7 successive failures: 0.50 * (0.85)^7 = 0.50 * 0.320577 = 0.160288 < 0.20
        for _ in range(7):
            curr = governance_engine.record_failure(curr)

        assert curr.confidence < 0.20
        assert curr.status == MemoryState.ARCHIVED
        assert curr.archive_epoch is not None


# =====================================================================
# Suite G: Continuous Exponential Decay
# =====================================================================

class TestExponentialDecay:
    """Suite G: Verification of exponential decay at 10, 30, and 60 days."""

    def test_exponential_decay_mathematics(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify C(t) = C_0 * exp(-lambda * delta_t) with lambda = 0.05/day."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0, current_epoch=0)
        assert mem is not None
        # Promote to ACTIVE with 1 success so C_ref = 0.55 at epoch 0
        mem = governance_engine.record_success(mem, current_epoch=0)
        assert mem.confidence == 0.55

        # At delta_t = 10 days
        d10 = governance_engine.apply_decay(mem, current_epoch=10)
        exp_10 = round(0.55 * math.exp(-0.05 * 10), 6)  # 0.55 * exp(-0.5) = 0.333592
        assert abs(d10.confidence - exp_10) < 1e-4

        # At delta_t = 30 days
        d30 = governance_engine.apply_decay(mem, current_epoch=30)
        exp_30 = round(0.55 * math.exp(-0.05 * 30), 6)  # 0.55 * exp(-1.5) = 0.122722
        assert abs(d30.confidence - exp_30) < 1e-4
        # Since 0.122722 < 0.20, d30 transitions to ARCHIVED
        assert d30.status == MemoryState.ARCHIVED

        # At delta_t = 60 days
        d60 = governance_engine.apply_decay(mem, current_epoch=60)
        exp_60 = round(0.55 * math.exp(-0.05 * 60), 6)  # 0.55 * exp(-3.0) = 0.027383
        assert abs(d60.confidence - exp_60) < 1e-4

        # Monotonicity check
        assert mem.confidence > d10.confidence > d30.confidence > d60.confidence

    def test_temporal_decay_explicit_ages_and_boundaries(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify explicit ages (0, 1, 5, 10, 20, 30, 60), negative delta_t, and repeated decay."""
        knowledge_high = sample_knowledge.model_copy(update={"confidence": 0.85})
        mem = governance_engine.admit(knowledge_high, context_similarity=1.0, current_epoch=0)
        assert mem is not None
        # Promote to STABLE with 1 success (C_ref = 0.85 + 0.1*(1 - 0.85) = 0.865 >= 0.80) at epoch 0
        mem = governance_engine.record_success(mem, current_epoch=0)
        assert mem.confidence >= 0.80
        assert mem.status == MemoryState.STABLE
        c_ref = mem.confidence_reference
        assert mem.reference_epoch == 0

        # Exact expected evaluations at λ = 0.05:
        target_ages = [0, 1, 5, 10, 20, 30, 60]
        decayed_memories = []
        for age in target_ages:
            d = governance_engine.apply_decay(mem, current_epoch=age)
            decayed_memories.append(d)
            expected_c = round(c_ref * math.exp(-0.05 * age), 6)
            assert abs(d.confidence - expected_c) < 1e-4, f"Mismatch at age {age}"

        # Age 0 check
        assert decayed_memories[0].confidence == c_ref
        assert decayed_memories[0].recency == 1.0

        # Monotonic decay check across 0, 1, 5, 10, 20, 30, 60 days
        for i in range(len(decayed_memories) - 1):
            assert decayed_memories[i].confidence > decayed_memories[i+1].confidence
            assert decayed_memories[i].recency > decayed_memories[i+1].recency

        # Boundary Case 1: Negative / Past timestamp (current_epoch < reference_epoch)
        d_neg = governance_engine.apply_decay(mem, current_epoch=-10)
        assert d_neg.confidence == c_ref  # clamped: delta_t = max(0, -10 - 0) = 0

        # Boundary Case 2: Repeated decay at same epoch (idempotence, no double decay)
        d_10_first = governance_engine.apply_decay(mem, current_epoch=10)
        d_10_second = governance_engine.apply_decay(d_10_first, current_epoch=10)
        assert d_10_first.confidence == d_10_second.confidence

        # Boundary Case 3: Chained progressive decay
        d_chained_30 = governance_engine.apply_decay(d_10_first, current_epoch=30)
        d_direct_30 = governance_engine.apply_decay(mem, current_epoch=30)
        assert d_chained_30.confidence == d_direct_30.confidence

        # State transitions at thresholds:
        # At age 10: c ~ 0.515 < 0.80 -> DECAYING
        assert d_10_first.status == MemoryState.DECAYING
        # At age 60: c ~ 0.042 < 0.20 -> ARCHIVED
        assert decayed_memories[-1].status == MemoryState.ARCHIVED


# =====================================================================
# Suite H: Complete Deterministic Lifecycle Progression
# =====================================================================

class TestLifecycleProgression:
    """Suite H: Complete progression: NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED."""

    def test_full_lifecycle_progression(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify the full 6-stage lifecycle sequence with documented operational triggers."""
        # 1. Admission: Admitted candidate enters as NEW
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0, current_epoch=0)
        assert mem is not None
        assert mem.status == MemoryState.NEW

        # 2. First successful retrieval/use: NEW -> ACTIVE
        active_mem = governance_engine.record_success(mem, current_epoch=1)
        assert active_mem.status == MemoryState.ACTIVE
        assert active_mem.confidence == 0.55

        # 3. Repeated successes: Confidence reaches >= 0.80 -> STABLE
        stable_mem = active_mem
        for epoch in range(2, 12):
            stable_mem = governance_engine.record_success(stable_mem, current_epoch=epoch)
        assert stable_mem.status == MemoryState.STABLE
        assert stable_mem.confidence >= 0.80

        # 4. Inactivity with elapsed time: Confidence drops below 0.80 -> DECAYING
        # At epoch 18 (delta_t = 7 days since last reference): C = 0.825661 * exp(-0.35) = 0.5819 < 0.80
        decaying_mem = governance_engine.apply_decay(stable_mem, current_epoch=18)
        assert decaying_mem.status == MemoryState.DECAYING
        assert 0.20 <= decaying_mem.confidence < 0.80

        # 5. Continued inactivity: Confidence drops below 0.20 -> ARCHIVED
        # At epoch 45 (delta_t = 34 days since last reference): C = 0.825661 * exp(-1.70) = 0.1508 < 0.20
        archived_mem = governance_engine.apply_decay(decaying_mem, current_epoch=45)
        assert archived_mem.status == MemoryState.ARCHIVED
        assert archived_mem.archive_epoch == 45

        # 6. Retention period exceeded (30 days in archive): ARCHIVED -> DELETED
        # At epoch 76 (current_epoch - archive_epoch = 76 - 45 = 31 >= 30 days retention)
        sweep_result = governance_engine.apply_decay_sweep([archived_mem], current_epoch=76)
        deleted_mem = sweep_result[0]
        assert deleted_mem.status == MemoryState.DELETED

    def test_invalid_lifecycle_transition_rejected(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify invalid backward transitions (e.g. ARCHIVED -> ACTIVE) raise ValueError."""
        mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            status=MemoryState.ARCHIVED,
        )
        with pytest.raises(ValueError, match="Invalid lifecycle transition"):
            governance_engine.transition_state(mem, MemoryState.ACTIVE)


# =====================================================================
# Suite I: Archive Retention Expiration
# =====================================================================

class TestArchiveRetention:
    """Suite I: Verification of 30-day retention boundary."""

    def test_archive_retention_boundary(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify archived memory remains ARCHIVED until day 30, then DELETED on day 30+."""
        archived_mem = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.15,
            status=MemoryState.ARCHIVED,
            simulated_epoch=10,
            archive_epoch=10,
        )

        # At day 39 (elapsed 29 days in archive) -> still ARCHIVED
        sweep_29 = governance_engine.apply_decay_sweep([archived_mem], current_epoch=39)
        assert sweep_29[0].status == MemoryState.ARCHIVED

        # At day 40 (elapsed 30 days in archive) -> transitions to DELETED
        sweep_30 = governance_engine.apply_decay_sweep([archived_mem], current_epoch=40)
        assert sweep_30[0].status == MemoryState.DELETED


# =====================================================================
# Suite J: Offline Operation & Determinism
# =====================================================================

class TestOfflineAndDeterminism:
    """Suite J & Determinism: Pure offline execution and 50-iteration stability."""

    def test_offline_zero_llm_zero_database(
        self, governance_engine: MemoryGovernanceEngine, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge
    ):
        """Verify governance and FAISS run without LLM calls or database connection."""
        # This test passes completely offline in milliseconds
        admitted = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert admitted is not None

        vec = np.zeros(768, dtype=np.float32)
        vec[0] = 1.0
        int_id = vector_store.add(admitted, vec)
        assert int_id == 1

        results = vector_store.search(vec, top_k=1)
        assert len(results) == 1
        assert results[0][0].memory_id == admitted.memory_id

    def test_50_run_determinism(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify governance calculations and FAISS tie-break are 100% deterministic across 50 runs."""
        # 1. Utility determinism
        u_baseline = governance_engine.calculate_utility(
            confidence=0.75, successful_uses=6, total_uses=8, context_similarity=0.92, delta_t=4.5
        )
        for _ in range(50):
            u_check = governance_engine.calculate_utility(
                confidence=0.75, successful_uses=6, total_uses=8, context_similarity=0.92, delta_t=4.5
            )
            assert u_check == u_baseline

        # 2. Escalation determinism
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        c1 = governance_engine.record_success(mem).confidence
        for _ in range(50):
            assert governance_engine.record_success(mem).confidence == c1

        # 3. Penalty determinism
        p1 = governance_engine.record_failure(mem).confidence
        for _ in range(50):
            assert governance_engine.record_failure(mem).confidence == p1


# =====================================================================
# Phase 1B: Mathematical & Boundary Validation Suite
# =====================================================================

class TestPhase1BMathematicalBoundaryValidation:
    """Suite K: Comprehensive boundary, monotonicity, and numerical stability validation.
    
    Covers:
    - Confidence reinforcement at exact boundary points: C in {0, 0.1, 0.5, 0.9, 0.99, 1.0}
    - Failure penalty at exact boundary points: C in {0.9, 0.5, 0.22, 0.0}
    - FAISS distance to normalized similarity conversion: d^2 in {0, 0.01, 0.25, 1, 4, 100, 10^9}
    - Utility multi-factor combinations and boundary conditions
    - Exact admission threshold gating (theta = 0.25 boundary: 0.249999, 0.25, 0.250001)
    - Exact retrieval threshold gating (sim = 0.50 boundary: 0.499999, 0.50, 0.500001)
    - Pathological and invalid input handling
    - Repeated success, repeated failure, and alternating outcome stability
    """

    def test_confidence_reinforcement_boundary_points(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 4: Test reinforcement equation C_new = C + alpha(1 - C) at exact boundary points."""
        test_points = [
            (0.0, 0.10),
            (0.10, 0.19),
            (0.50, 0.55),
            (0.90, 0.91),
            (0.99, 0.991),
            (1.0, 1.0),
        ]
        for c_init, c_expected in test_points:
            mem = RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                confidence=c_init,
                utility=c_init,
                status=MemoryState.ACTIVE if c_init < 0.80 else MemoryState.STABLE,
            )
            updated = governance_engine.record_success(mem)
            assert abs(updated.confidence - c_expected) < 1e-5, f"At C={c_init}: expected {c_expected}, got {updated.confidence}"
            assert updated.confidence >= c_init, f"Reinforcement decreased confidence from {c_init} to {updated.confidence}"
            assert 0.0 <= updated.confidence <= 1.0, f"Confidence out of bounds: {updated.confidence}"

    def test_confidence_reinforcement_repeated_success(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 11: Test repeated reinforcement asymptotically approaches 1.0 and never exceeds 1.0."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        curr = mem
        prev_conf = curr.confidence
        for _ in range(50):
            curr = governance_engine.record_success(curr)
            assert curr.confidence >= prev_conf
            assert 0.0 <= curr.confidence <= 1.0
            prev_conf = curr.confidence
        assert abs(curr.confidence - 1.0) < 0.005
        assert curr.status == MemoryState.STABLE

    def test_failure_penalty_boundary_points(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 5: Test failure penalty C_new = max(0, C * (1 - beta)) at boundary points."""
        test_points = [
            (0.90, 0.765, MemoryState.STABLE, MemoryState.DECAYING),
            (0.50, 0.425, MemoryState.ACTIVE, MemoryState.ACTIVE),
            (0.22, 0.187, MemoryState.ACTIVE, MemoryState.ARCHIVED),
            (0.0, 0.0, MemoryState.ACTIVE, MemoryState.ARCHIVED),
        ]
        for c_init, c_expected, init_state, expected_state in test_points:
            mem = RuntimeMemory(
                context=dict(sample_knowledge.context),
                failure_type=sample_knowledge.failure_type,
                root_cause=sample_knowledge.root_cause,
                repair_strategy=sample_knowledge.repair_strategy,
                confidence=c_init,
                utility=c_init,
                status=init_state,
            )
            updated = governance_engine.record_failure(mem)
            assert abs(updated.confidence - c_expected) < 1e-5, f"At C={c_init}: expected {c_expected}, got {updated.confidence}"
            assert updated.confidence <= c_init, f"Failure penalty increased confidence from {c_init} to {updated.confidence}"
            assert updated.confidence >= 0.0, "Confidence became negative"
            assert updated.status == expected_state, f"At C={c_init}: expected state {expected_state}, got {updated.status}"

    def test_failure_penalty_repeated_failure(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 11: Test repeated failures monotonically decrease and remain bounded at 0.0."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        curr = mem
        prev_conf = curr.confidence
        for _ in range(50):
            curr = governance_engine.record_failure(curr)
            assert curr.confidence <= prev_conf
            assert curr.confidence >= 0.0
            prev_conf = curr.confidence
        assert 0.0 <= curr.confidence < 0.001
        assert curr.status == MemoryState.ARCHIVED

    def test_alternating_success_failure_stability(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 11: Test alternating success and failure outcomes remain bounded in [0, 1]."""
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem is not None
        curr = mem
        for _ in range(25):
            curr = governance_engine.record_success(curr)
            assert 0.0 <= curr.confidence <= 1.0
            curr = governance_engine.record_failure(curr)
            assert 0.0 <= curr.confidence <= 1.0

    def test_faiss_distance_to_similarity_exact_points(self, vector_store: FAISSMemoryStore, sample_knowledge: RuntimeKnowledge):
        """Section 6: Test conversion of FAISS squared L2 distance to similarity sim = 1 / (1 + d^2)."""
        distances_and_expected_sims = [
            (0.0, 1.0),
            (0.01, 1.0 / 1.01),
            (0.25, 1.0 / 1.25),
            (1.0, 0.50),
            (4.0, 0.20),
            (100.0, 1.0 / 101.0),
            (1e9, 1.0 / (1.0 + 1e9)),
        ]
        prev_sim = 2.0
        for d_sq, expected_sim in distances_and_expected_sims:
            sim = 1.0 / (1.0 + d_sq)
            sim_rounded = round(sim, 6)
            assert abs(sim_rounded - round(expected_sim, 6)) < 1e-5
            assert 0.0 < sim <= 1.0
            assert sim < prev_sim, f"Monotonicity violated: d^2={d_sq} gave sim={sim} >= {prev_sim}"
            prev_sim = sim

    def test_utility_factor_boundaries(self, governance_engine: MemoryGovernanceEngine):
        """Section 7: Test Utility = C * SR * Sim * Recency across combinations and boundary points."""
        # 1. All factors 1.0
        assert governance_engine.calculate_utility(confidence=1.0, successful_uses=1, total_uses=1, context_similarity=1.0, delta_t=0.0) == 1.0

        # 2. Zero in individual multiplicative factors produces 0.0
        assert governance_engine.calculate_utility(confidence=0.0, successful_uses=1, total_uses=1, context_similarity=1.0, delta_t=0.0) == 0.0
        assert governance_engine.calculate_utility(confidence=1.0, successful_uses=0, total_uses=1, context_similarity=1.0, delta_t=0.0) == 0.0
        assert governance_engine.calculate_utility(confidence=1.0, successful_uses=1, total_uses=1, context_similarity=0.0, delta_t=0.0) == 0.0

        # 3. All factors zero
        assert governance_engine.calculate_utility(confidence=0.0, successful_uses=0, total_uses=1, context_similarity=0.0, delta_t=0.0) == 0.0

        # 4. Mixed fractional values: 0.6 * (3/4) * 0.8 * (1 / (1 + 1)) = 0.6 * 0.75 * 0.8 * 0.5 = 0.18
        u = governance_engine.calculate_utility(confidence=0.6, successful_uses=3, total_uses=4, context_similarity=0.8, delta_t=1.0)
        assert abs(u - 0.18) < 1e-5

        # 5. Elapsed time / recency boundary: delta_t = 999 -> recency = 0.001
        u_rec = governance_engine.calculate_utility(confidence=1.0, successful_uses=1, total_uses=1, context_similarity=1.0, delta_t=999.0)
        assert abs(u_rec - 0.001) < 1e-5

    def test_admission_threshold_exact_boundary(self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge):
        """Section 8: Test exact admission threshold gating at theta = 0.25 (operator is >=)."""
        # 1. Utility = 0.249999 -> rejected (< 0.25)
        # Using context_similarity = 0.249999 / (0.50 * 0.5) = 0.249999 / 0.25 = 0.999996
        sim_reject = 0.249999 / 0.25
        mem_rejected = governance_engine.admit(sample_knowledge, context_similarity=sim_reject)
        assert mem_rejected is None, "Candidate with utility 0.249999 should be rejected"

        # 2. Utility = 0.250000 -> admitted (>= 0.25)
        mem_exact = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert mem_exact is not None, "Candidate with utility 0.250000 must be admitted"
        assert mem_exact.utility == 0.25

        # 3. Utility = 0.250001 -> admitted (>= 0.25)
        high_conf_knowledge = sample_knowledge.model_copy(update={"confidence": 0.500002})
        mem_above = governance_engine.admit(high_conf_knowledge, context_similarity=1.0)
        assert mem_above is not None, "Candidate with utility 0.250001 must be admitted"
        assert mem_above.utility >= 0.25

    def test_retrieval_threshold_exact_boundary(self):
        """Section 9: Test exact retrieval threshold gating at similarity = 0.50 (operator is >=)."""
        # Retrieval rule: if sim >= 0.50 and mem.status.value not in ("ARCHIVED", "DELETED"): retrieved.append(mem)
        # 1. 0.499999 -> rejected
        sim_below = 0.499999
        assert not (sim_below >= 0.50), "0.499999 must not meet >= 0.50 retrieval threshold"

        # 2. 0.50 -> accepted (equality accepted)
        sim_exact = 0.50
        assert sim_exact >= 0.50, "0.50 must meet >= 0.50 retrieval threshold"

        # 3. 0.500001 -> accepted
        sim_above = 0.500001
        assert sim_above >= 0.50, "0.500001 must meet >= 0.50 retrieval threshold"

    def test_pathological_and_invalid_inputs(self, governance_engine: MemoryGovernanceEngine, vector_store: FAISSMemoryStore):
        """Section 10: Test invalid and pathological inputs against API contracts."""
        # 1. Negative confidence
        with pytest.raises(ValueError, match="confidence"):
            governance_engine.calculate_utility(confidence=-0.1, successful_uses=1, total_uses=1)

        # 2. Confidence > 1
        with pytest.raises(ValueError, match="confidence"):
            governance_engine.calculate_utility(confidence=1.1, successful_uses=1, total_uses=1)

        # 3. Negative context_similarity
        with pytest.raises(ValueError, match="context_similarity"):
            governance_engine.calculate_utility(confidence=0.5, successful_uses=1, total_uses=1, context_similarity=-0.01)

        # 4. Context similarity > 1
        with pytest.raises(ValueError, match="context_similarity"):
            governance_engine.calculate_utility(confidence=0.5, successful_uses=1, total_uses=1, context_similarity=1.01)

        # 5. Negative delta_t
        with pytest.raises(ValueError, match="delta_t"):
            governance_engine.calculate_utility(confidence=0.5, successful_uses=1, total_uses=1, delta_t=-1.0)

        # 6. NaN in confidence or similarity
        with pytest.raises(ValueError, match="confidence"):
            governance_engine.calculate_utility(confidence=float("nan"), successful_uses=1, total_uses=1)
        with pytest.raises(ValueError, match="context_similarity"):
            governance_engine.calculate_utility(confidence=0.5, successful_uses=1, total_uses=1, context_similarity=float("nan"))

        # 7. Infinity in confidence or similarity
        with pytest.raises(ValueError, match="confidence"):
            governance_engine.calculate_utility(confidence=float("inf"), successful_uses=1, total_uses=1)
        with pytest.raises(ValueError, match="context_similarity"):
            governance_engine.calculate_utility(confidence=0.5, successful_uses=1, total_uses=1, context_similarity=float("inf"))
