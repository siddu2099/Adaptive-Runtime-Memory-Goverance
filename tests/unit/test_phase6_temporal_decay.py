"""
Unit tests for ARMG Phase 6: Temporal Decay Validation.
Hermetic, offline test suite verifying:
- ControlledClock functionality and injection into MemoryGovernanceEngine
- Mathematical accuracy of exponential decay across all target time points (0, 1, 5, 10, 20, 30, 60 days)
- Tolerance assertion: absolute error <= 1e-4 against independent theoretical calculation
- Boundary behavior: zero elapsed time, negative elapsed time clamping, confidence bounds [0, 1]
- Exact transition thresholds (0.80 stable, 0.20 archive) and epsilon neighborhood boundaries
- Idempotence: repeated decay at same epoch produces zero compound double-decay
- Progressive / chained decay equivalence: 0 -> 10 -> 30 vs 0 -> 30
- Full 6-stage lifecycle state progression: NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED
- Archive retention period expiration (30-day purge threshold in apply_decay_sweep)
- Downstream utility and recency dynamic recalculation (no stale cached utility)
- Multiple memory independence (no shared mutable state across instances)
- Reinforcement and decay interaction (reinforce then decay, decay then reinforce)
- FAISS vector store synchronization and retrieval exclusion for ARCHIVED/DELETED states
"""

import math
from datetime import datetime, timezone
from typing import List
import pytest

from agents.taxonomy import TaxonomyCategory
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.governance import MemoryGovernanceEngine, ControlledClock
from memory.vector_store import FAISSMemoryStore
from graph.workflow import ARMGRepairWorkflow


# =====================================================================
# Fixtures & Helpers
# =====================================================================

@pytest.fixture
def sample_knowledge() -> RuntimeKnowledge:
    """Fixture providing standard RuntimeKnowledge."""
    return RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception="column 'rev' does not exist",
        context={"tables_referenced": ["fact_sales_performance"], "broken_column": "rev"},
        root_cause="Column 'rev' is not present in 'fact_sales_performance'.",
        repair_strategy="Replace 'rev' with 'gross_revenue_inr'.",
        negative_constraints=["Do not reference column 'rev'."],
        candidate_replacements=["gross_revenue_inr"],
        confidence=0.50,
    )


@pytest.fixture
def controlled_clock() -> ControlledClock:
    """Fixture providing a fresh ControlledClock initialized at epoch 0."""
    return ControlledClock(
        start_time=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        initial_epoch=0,
    )


@pytest.fixture
def governance_engine(controlled_clock: ControlledClock) -> MemoryGovernanceEngine:
    """Fixture providing MemoryGovernanceEngine injected with controlled clock."""
    return MemoryGovernanceEngine(clock=controlled_clock)


def calc_expected_decay(c_ref: float, lambda_val: float, delta_t: float) -> float:
    """Independent theoretical decay calculation: C(t) = C_ref * exp(-lambda * delta_t)."""
    dt = max(0.0, float(delta_t))
    val = c_ref * math.exp(-lambda_val * dt)
    return max(0.0, min(1.0, round(val, 6)))


def calc_expected_recency(delta_t: float) -> float:
    """Independent theoretical recency calculation: 1 / (1 + delta_t)."""
    dt = max(0.0, float(delta_t))
    return round(1.0 / (1.0 + dt), 6)


# =====================================================================
# Test Suite 1: ControlledClock Mechanics
# =====================================================================

class TestControlledClock:
    """Verification of ControlledClock abstraction and engine integration."""

    def test_clock_initialization_and_advance(self, controlled_clock: ControlledClock):
        assert controlled_clock.current_epoch() == 0
        assert controlled_clock.epoch == 0
        t0 = controlled_clock.now()

        # Advance by 10 days
        new_ep = controlled_clock.advance_days(10)
        assert new_ep == 10
        assert controlled_clock.current_epoch() == 10
        t1 = controlled_clock.now()
        assert (t1 - t0).days == 10

    def test_clock_set_epoch(self, controlled_clock: ControlledClock):
        controlled_clock.set_epoch(45)
        assert controlled_clock.current_epoch() == 45

    def test_engine_clock_fallback_when_none(self):
        engine = MemoryGovernanceEngine(clock=None)
        assert engine.get_current_epoch(None) == 0
        assert engine.get_current_epoch(12) == 12


# =====================================================================
# Test Suite 2: Mathematical Decay Validation & Numerical Tolerance
# =====================================================================

class TestMathematicalDecay:
    """Verification of C(t) = C_ref * exp(-lambda * delta_t) across all target time points."""

    @pytest.mark.parametrize("delta_t", [0, 1, 5, 10, 20, 30, 60])
    @pytest.mark.parametrize("c_ref", [0.95, 0.85, 0.80, 0.799, 0.50, 0.25, 0.20, 0.199])
    def test_exponential_decay_all_points_and_confidences(
        self, governance_engine: MemoryGovernanceEngine, delta_t: int, c_ref: float
    ):
        """Verify absolute numerical error <= 1e-4 across all (delta_t, c_ref) pairs."""
        clock = governance_engine.clock
        clock.set_epoch(0)

        mem = RuntimeMemory(
            context={"test": "math"},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=c_ref,
            utility=c_ref * 0.25,
            recency=1.0,
            status=MemoryState.STABLE if c_ref >= 0.80 else MemoryState.ACTIVE,
            simulated_epoch=0,
            confidence_reference=c_ref,
            reference_epoch=0,
        )

        # Advance clock to target delta_t
        clock.set_epoch(delta_t)
        decayed = governance_engine.apply_decay(mem)

        # Independent calculation
        expected_c = calc_expected_decay(c_ref, governance_engine.decay_rate, delta_t)
        abs_err = abs(decayed.confidence - expected_c)

        # Numerical acceptance: error <= 1e-4
        assert abs_err <= 1e-4, (
            f"Numerical error exceeded tolerance at delta_t={delta_t}, c_ref={c_ref}: "
            f"actual={decayed.confidence}, expected={expected_c}, error={abs_err}"
        )

    def test_decay_monotonicity(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence decays strictly monotonically as elapsed time increases."""
        clock = governance_engine.clock
        c_ref = 0.90
        mem = RuntimeMemory(
            context={"test": "monotonic"},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=c_ref,
            confidence_reference=c_ref,
            reference_epoch=0,
            status=MemoryState.STABLE,
        )

        time_points = [0, 1, 5, 10, 20, 30, 60]
        decayed_scores = []
        for t in time_points:
            clock.set_epoch(t)
            d = governance_engine.apply_decay(mem)
            decayed_scores.append(d.confidence)

        for i in range(len(decayed_scores) - 1):
            assert decayed_scores[i] > decayed_scores[i + 1], (
                f"Non-monotonic decay between t={time_points[i]} ({decayed_scores[i]}) "
                f"and t={time_points[i+1]} ({decayed_scores[i+1]})"
            )


# =====================================================================
# Test Suite 3: Boundary Conditions
# =====================================================================

class TestBoundaryConditions:
    """Verification of zero elapsed time, negative time, thresholds and epsilon boundaries."""

    def test_zero_elapsed_time(self, governance_engine: MemoryGovernanceEngine):
        """Verify delta_t = 0 preserves exact reference confidence."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.75,
            confidence_reference=0.75,
            reference_epoch=5,
        )
        governance_engine.clock.set_epoch(5)
        d = governance_engine.apply_decay(mem)
        assert d.confidence == 0.75
        assert d.recency == 1.0

    def test_negative_elapsed_time_clamped_to_zero(self, governance_engine: MemoryGovernanceEngine):
        """Verify negative elapsed time (current_epoch < reference_epoch) clamps delta_t to 0."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.75,
            confidence_reference=0.75,
            reference_epoch=20,
        )
        governance_engine.clock.set_epoch(10)  # 10 < 20 -> delta_t = max(0, -10) = 0
        d = governance_engine.apply_decay(mem)
        assert d.confidence == 0.75
        assert d.recency == 1.0

    def test_exact_stable_threshold_boundary(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence exactly at 0.80 remains STABLE."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.80,
            confidence_reference=0.80,
            reference_epoch=0,
            status=MemoryState.STABLE,
        )
        governance_engine.clock.set_epoch(0)
        d = governance_engine.apply_decay(mem)
        assert d.status == MemoryState.STABLE

    def test_stable_threshold_minus_epsilon(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence at 0.80 - epsilon transitions from STABLE to DECAYING."""
        epsilon = 1e-6
        c_val = 0.80 - epsilon
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=c_val,
            confidence_reference=c_val,
            reference_epoch=0,
            status=MemoryState.STABLE,
        )
        governance_engine.clock.set_epoch(0)
        d = governance_engine.apply_decay(mem)
        assert d.status == MemoryState.DECAYING

    def test_exact_archive_threshold_boundary(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence exactly at 0.20 does NOT archive (threshold is strictly < 0.20)."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.20,
            confidence_reference=0.20,
            reference_epoch=0,
            status=MemoryState.DECAYING,
        )
        governance_engine.clock.set_epoch(0)
        d = governance_engine.apply_decay(mem)
        assert d.status == MemoryState.DECAYING
        assert d.archive_epoch is None

    def test_archive_threshold_minus_epsilon(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence at 0.20 - epsilon transitions to ARCHIVED."""
        epsilon = 1e-6
        c_val = 0.20 - epsilon
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=c_val,
            confidence_reference=c_val,
            reference_epoch=0,
            status=MemoryState.DECAYING,
        )
        governance_engine.clock.set_epoch(10)
        d = governance_engine.apply_decay(mem)
        assert d.status == MemoryState.ARCHIVED
        assert d.archive_epoch == 10

    def test_confidence_clamped_in_unit_interval(self, governance_engine: MemoryGovernanceEngine):
        """Verify confidence is strictly clamped in [0.0, 1.0]."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.01,
            confidence_reference=0.01,
            reference_epoch=0,
        )
        governance_engine.clock.set_epoch(1000)
        d = governance_engine.apply_decay(mem)
        assert 0.0 <= d.confidence <= 1.0


# =====================================================================
# Test Suite 4: Idempotence & Progressive Chained Decay
# =====================================================================

class TestIdempotenceAndChainedDecay:
    """Verification of double-decay prevention and progressive chain equivalence."""

    def test_idempotence_at_same_epoch(self, governance_engine: MemoryGovernanceEngine):
        """Verify repeatedly applying decay at the same epoch does NOT double-decay."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.70,
            confidence_reference=0.70,
            reference_epoch=0,
            status=MemoryState.ACTIVE,
        )
        governance_engine.clock.set_epoch(10)

        d1 = governance_engine.apply_decay(mem)
        d2 = governance_engine.apply_decay(d1)
        d3 = governance_engine.apply_decay(d2)

        assert d1.confidence == d2.confidence == d3.confidence
        assert d1.utility == d2.utility == d3.utility
        assert d1.recency == d2.recency == d3.recency

    def test_progressive_chained_decay_equivalence(self, governance_engine: MemoryGovernanceEngine):
        """Verify 0 -> 10 -> 30 yields identical result to direct 0 -> 30."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.85,
            confidence_reference=0.85,
            reference_epoch=0,
            status=MemoryState.STABLE,
        )
        # Stepwise: 0 -> 10 -> 30
        governance_engine.clock.set_epoch(10)
        m_step10 = governance_engine.apply_decay(mem)
        governance_engine.clock.set_epoch(30)
        m_step30 = governance_engine.apply_decay(m_step10)

        # Direct: 0 -> 30
        governance_engine.clock.set_epoch(30)
        m_direct30 = governance_engine.apply_decay(mem)

        assert m_step30.confidence == m_direct30.confidence
        assert m_step30.recency == m_direct30.recency
        assert m_step30.utility == m_direct30.utility
        assert m_step30.status == m_direct30.status


# =====================================================================
# Test Suite 5: Full Lifecycle Transitions & Purge Expiration
# =====================================================================

class TestLifecycleTransitionsAndPurge:
    """Verification of complete 6-stage lifecycle and 30-day archive retention purge."""

    def test_complete_six_stage_lifecycle(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify: NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED."""
        clock = governance_engine.clock
        clock.set_epoch(0)

        # 1. NEW upon admission
        m_new = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        assert m_new is not None
        assert m_new.status == MemoryState.NEW

        # 2. ACTIVE upon first successful retrieval
        clock.advance_days(1)
        m_active = governance_engine.record_success(m_new)
        assert m_active.status == MemoryState.ACTIVE

        # 3. STABLE upon reaching confidence >= 0.80
        curr = m_active
        for day in range(2, 10):
            clock.advance_days(1)
            curr = governance_engine.record_success(curr)
        assert curr.status == MemoryState.STABLE
        assert curr.confidence >= 0.80
        m_stable = curr
        stable_ref_ep = m_stable.reference_epoch

        # 4. DECAYING upon dropping below 0.80 due to elapsed time
        clock.set_epoch(stable_ref_ep + 15)
        m_decaying = governance_engine.apply_decay(m_stable)
        assert m_decaying.status == MemoryState.DECAYING
        assert 0.20 <= m_decaying.confidence < 0.80

        # 5. ARCHIVED upon dropping below 0.20 due to continued elapsed time
        clock.set_epoch(stable_ref_ep + 35)
        m_archived = governance_engine.apply_decay(m_decaying)
        assert m_archived.status == MemoryState.ARCHIVED
        assert m_archived.archive_epoch == stable_ref_ep + 35

        # 6. Retention check: Day 29 still ARCHIVED, Day 30+ DELETED
        arch_ep = m_archived.archive_epoch
        clock.set_epoch(arch_ep + 29)
        sweep_29 = governance_engine.apply_decay_sweep([m_archived])
        assert sweep_29[0].status == MemoryState.ARCHIVED

        clock.set_epoch(arch_ep + 30)
        sweep_30 = governance_engine.apply_decay_sweep([m_archived])
        assert sweep_30[0].status == MemoryState.DELETED

    def test_terminal_deleted_state_ignores_decay(self, governance_engine: MemoryGovernanceEngine):
        """Verify memories in DELETED state remain unaffected by further decay calls."""
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=0.05,
            confidence_reference=0.05,
            reference_epoch=0,
            status=MemoryState.DELETED,
        )
        governance_engine.clock.set_epoch(50)
        d = governance_engine.apply_decay(mem)
        assert d.status == MemoryState.DELETED
        assert d.confidence == 0.05


# =====================================================================
# Test Suite 6: Utility & Recency Dynamic Recalculation
# =====================================================================

class TestUtilityAndRecencyRecalculation:
    """Verify decay dynamically recalculates recency and utility without stale cache."""

    def test_utility_and_recency_attenuation(self, governance_engine: MemoryGovernanceEngine):
        c_init = 0.60
        mem = RuntimeMemory(
            context={},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause",
            repair_strategy="strategy",
            confidence=c_init,
            confidence_reference=c_init,
            reference_epoch=0,
            successful_uses=2,
            total_uses=4,  # SR = 0.5
            status=MemoryState.ACTIVE,
        )
        governance_engine.clock.set_epoch(10)
        d = governance_engine.apply_decay(mem)

        expected_c = calc_expected_decay(c_init, governance_engine.decay_rate, 10)
        expected_rec = calc_expected_recency(10)  # 1 / 11 = 0.090909
        expected_u = round(expected_c * 0.5 * 1.0 * expected_rec, 6)

        assert abs(d.confidence - expected_c) <= 1e-4
        assert abs(d.recency - expected_rec) <= 1e-4
        assert abs(d.utility - expected_u) <= 1e-4


# =====================================================================
# Test Suite 7: Multi-Memory Independence & Non-Interference
# =====================================================================

class TestMultiMemoryIndependence:
    """Verify multiple concurrent memories decay independently without shared mutable state."""

    def test_independent_memories_different_epochs(self, governance_engine: MemoryGovernanceEngine):
        clock = governance_engine.clock
        clock.set_epoch(0)

        # Mem 1 admitted at epoch 0
        mem1 = RuntimeMemory(
            context={"id": 1},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause1",
            repair_strategy="strategy1",
            confidence=0.80,
            confidence_reference=0.80,
            reference_epoch=0,
            status=MemoryState.STABLE,
        )

        # Mem 2 admitted at epoch 10
        mem2 = RuntimeMemory(
            context={"id": 2},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="cause2",
            repair_strategy="strategy2",
            confidence=0.80,
            confidence_reference=0.80,
            reference_epoch=10,
            status=MemoryState.STABLE,
        )

        # Evaluate at epoch 20
        clock.set_epoch(20)
        decayed_batch = governance_engine.apply_decay_sweep([mem1, mem2])

        d1 = decayed_batch[0]
        d2 = decayed_batch[1]

        # mem1 elapsed = 20 days: C = 0.80 * exp(-1.0) = 0.294304
        exp_c1 = calc_expected_decay(0.80, governance_engine.decay_rate, 20)
        # mem2 elapsed = 10 days: C = 0.80 * exp(-0.5) = 0.485225
        exp_c2 = calc_expected_decay(0.80, governance_engine.decay_rate, 10)

        assert abs(d1.confidence - exp_c1) <= 1e-4
        assert abs(d2.confidence - exp_c2) <= 1e-4
        assert d1.confidence < d2.confidence


# =====================================================================
# Test Suite 8: Reinforcement & Decay Interplay
# =====================================================================

class TestReinforcementDecayInterplay:
    """Verify reference epoch tracking and confidence reset during reinforcement."""

    def test_reinforcement_after_decay_resets_reference(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        clock = governance_engine.clock
        clock.set_epoch(0)

        # Admit and escalate at epoch 0
        m0 = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        m0 = governance_engine.record_success(m0)
        assert m0.reference_epoch == 0
        c0 = m0.confidence

        # Decay to epoch 10
        clock.set_epoch(10)
        m10 = governance_engine.apply_decay(m0)
        assert m10.confidence < c0
        assert m10.reference_epoch == 0  # reference epoch preserved during decay

        # Reinforce at epoch 10
        m10_reinf = governance_engine.record_success(m10)
        assert m10_reinf.reference_epoch == 10  # reference epoch resets upon reinforcement
        assert m10_reinf.confidence_reference == m10_reinf.confidence
        assert m10_reinf.confidence > m10.confidence

        # Further decay to epoch 25 (delta_t = 15 from epoch 10)
        clock.set_epoch(25)
        m25 = governance_engine.apply_decay(m10_reinf)
        exp_c25 = calc_expected_decay(m10_reinf.confidence_reference, governance_engine.decay_rate, 15)
        assert abs(m25.confidence - exp_c25) <= 1e-4


# =====================================================================
# Test Suite 9: FAISS Store Synchronization & Retrieval Filtering
# =====================================================================

class TestFAISSSynchronizationAndRetrieval:
    """Verify FAISS vector store metadata synchronization and lifecycle retrieval exclusion."""

    def test_faiss_metadata_update_and_exclusion(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        clock = governance_engine.clock
        clock.set_epoch(0)

        store = FAISSMemoryStore()
        v_dummy = [1.0] + [0.0] * 767

        # Add active memory
        mem = governance_engine.admit(sample_knowledge, context_similarity=1.0)
        mem = governance_engine.record_success(mem)
        store.add(mem, v_dummy)
        assert store.count() == 1

        # Search retrieves active memory
        raw_res = store.search_raw_candidates(v_dummy, top_k=5)
        assert len(raw_res) == 1
        assert raw_res[0][0].status == MemoryState.ACTIVE

        # Decay memory to ARCHIVED
        clock.set_epoch(50)
        mem_arch = governance_engine.apply_decay(mem)
        assert mem_arch.status == MemoryState.ARCHIVED

        # Synchronize metadata into FAISS store
        sync_ok = store.update_memory(mem_arch)
        assert sync_ok is True
        assert store.get(mem.memory_id).status == MemoryState.ARCHIVED

        # Workflow retrieval node must exclude ARCHIVED memory
        wf = ARMGRepairWorkflow(
            environment=None,
            vector_store=store,
            embed_fn=lambda _: v_dummy,
        )
        res = wf.memory_retrieval_node({"user_query": "rev query", "telemetry": {}})
        assert len(res["retrieved_memories"]) == 0

        # Purge to DELETED
        clock.set_epoch(50 + 35)
        sweep = governance_engine.apply_decay_sweep([mem_arch])
        mem_del = sweep[0]
        assert mem_del.status == MemoryState.DELETED

        store.update_memory(mem_del)
        assert store.get(mem.memory_id).status == MemoryState.DELETED

        # FAISS search filters out DELETED
        faiss_matches = store.search(v_dummy, top_k=5)
        assert len(faiss_matches) == 0

        # Physical deletion from FAISS
        phys_del = store.delete(mem.memory_id)
        assert phys_del is True
        assert store.count() == 0
        assert store.get(mem.memory_id) is None


# =====================================================================
# Test Suite 10: Lifecycle Immutability & Resurrection Prevention
# =====================================================================

class TestLifecycleImmutabilityAndResurrectionPrevention:
    """Forensic verification that ARCHIVED/DELETED states cannot be illegally resurrected or reverted."""

    def test_record_success_on_archived_memory_never_resurrects(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify an ARCHIVED memory cannot be resurrected to ACTIVE or STABLE by record_success."""
        mem_arch = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.79,
            confidence_reference=0.79,
            reference_epoch=0,
            archive_epoch=5,
            status=MemoryState.ARCHIVED,
        )
        # Confidence escalates past 0.80: 0.79 + 0.1*(1 - 0.79) = 0.811
        updated = governance_engine.record_success(mem_arch)
        assert updated.confidence >= 0.80
        # Status MUST NOT become STABLE; ARCHIVED state must be preserved
        assert updated.status == MemoryState.ARCHIVED

    def test_record_success_on_deleted_memory_preserves_terminality(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify a DELETED memory is strictly terminal and ignored by record_success."""
        mem_del = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.05,
            confidence_reference=0.05,
            reference_epoch=0,
            status=MemoryState.DELETED,
        )
        updated = governance_engine.record_success(mem_del)
        assert updated.status == MemoryState.DELETED
        assert updated.confidence == 0.05

    def test_record_failure_on_deleted_memory_never_reverts_to_archived(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify a DELETED memory does not revert to ARCHIVED when penalized."""
        mem_del = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.10,
            confidence_reference=0.10,
            reference_epoch=0,
            status=MemoryState.DELETED,
        )
        updated = governance_engine.record_failure(mem_del)
        assert updated.status == MemoryState.DELETED

    def test_record_failure_on_archived_memory_preserves_original_archive_epoch(
        self, governance_engine: MemoryGovernanceEngine, sample_knowledge: RuntimeKnowledge
    ):
        """Verify penalizing an already-ARCHIVED memory preserves original archive_epoch countdown."""
        mem_arch = RuntimeMemory(
            context=dict(sample_knowledge.context),
            failure_type=sample_knowledge.failure_type,
            root_cause=sample_knowledge.root_cause,
            repair_strategy=sample_knowledge.repair_strategy,
            confidence=0.15,
            confidence_reference=0.15,
            reference_epoch=0,
            archive_epoch=10,
            status=MemoryState.ARCHIVED,
        )
        governance_engine.clock.set_epoch(25)
        updated = governance_engine.record_failure(mem_arch)
        assert updated.status == MemoryState.ARCHIVED
        assert updated.archive_epoch == 10  # Preserved, not overwritten to 25

