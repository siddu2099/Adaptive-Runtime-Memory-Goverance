"""
ARMG Phase 6: Runtime Memory Governance Engine.

Implements the mathematical control system for governing operational knowledge persistence:
- Multi-factor utility calculation: Utility = Confidence * SuccessRate * ContextSimilarity * Recency.
- Admission filtering: Candidate admitted if Utility >= theta (0.25).
- Asymptotic confidence escalation on success: C_new = C_old + alpha * (1 - C_old).
- Penalty reduction on failure: C_new = max(0, C_old * (1 - beta)).
- Continuous exponential decay: C(t) = C_0 * exp(-lambda * delta_t).
- Six-stage lifecycle machine: NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED.
- Deterministic simulated-time / epoch support.

Zero-LLM, zero-database, pure mathematical execution.
"""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional

from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory


class ControlledClock:
    """Injectable deterministic clock for temporal lifecycle validation (Phase 6)."""

    def __init__(
        self,
        start_time: Optional[datetime] = None,
        initial_epoch: int = 0,
    ) -> None:
        self._current_time = start_time or datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self._epoch = initial_epoch

    def now(self) -> datetime:
        """Return the current simulated datetime."""
        return self._current_time

    @property
    def epoch(self) -> int:
        """Return the current simulated epoch."""
        return self._epoch

    def current_epoch(self) -> int:
        """Return the current simulated epoch."""
        return self._epoch

    def advance_days(self, days: int) -> int:
        """Advance time by a specified number of calendar days / epochs."""
        from datetime import timedelta
        self._epoch += days
        self._current_time += timedelta(days=days)
        return self._epoch

    def set_epoch(self, epoch: int) -> int:
        """Set epoch directly, adjusting simulated wall-clock time accordingly."""
        from datetime import timedelta
        diff = epoch - self._epoch
        self._epoch = epoch
        self._current_time += timedelta(days=diff)
        return self._epoch


class MemoryGovernanceEngine:
    """Mathematical governance and lifecycle management engine for RuntimeMemory."""

    def __init__(
        self,
        admission_threshold: float = 0.25,
        stable_threshold: float = 0.80,
        archive_threshold: float = 0.20,
        escalation_rate: float = 0.10,
        penalty_rate: float = 0.15,
        decay_rate: float = 0.05,
        archive_retention_days: int = 30,
        clock: Optional[Any] = None,
    ):
        self.admission_threshold = admission_threshold
        self.stable_threshold = stable_threshold
        self.archive_threshold = archive_threshold
        self.escalation_rate = escalation_rate
        self.penalty_rate = penalty_rate
        self.decay_rate = decay_rate
        self.archive_retention_days = archive_retention_days
        self.clock = clock

    def get_current_epoch(self, explicit_epoch: Optional[int] = None) -> int:
        """Determine current epoch from explicit argument or injected clock."""
        if explicit_epoch is not None:
            return explicit_epoch
        if self.clock is not None:
            if hasattr(self.clock, "current_epoch"):
                return self.clock.current_epoch()
            if hasattr(self.clock, "epoch"):
                return self.clock.epoch
        return 0

    def get_now_iso(self) -> str:
        """Determine current ISO timestamp from injected clock or system UTC."""
        if self.clock is not None and hasattr(self.clock, "now"):
            dt = self.clock.now()
            if hasattr(dt, "isoformat"):
                return dt.isoformat()
        return datetime.now(timezone.utc).isoformat()

    def calculate_utility(
        self,
        memory: Optional[RuntimeMemory] = None,
        context_similarity: float = 1.0,
        delta_t: float = 0.0,
        *,
        confidence: Optional[float] = None,
        successful_uses: Optional[int] = None,
        total_uses: Optional[int] = None,
    ) -> float:
        """Calculate operational utility using the multi-factor heuristic (Section 12.4).
        
        Utility = Confidence * SuccessRate * ContextSimilarity * Recency
        
        Where:
            SuccessRate = successful_uses / total_uses (0.5 if total_uses == 0)
            Recency = 1.0 / (1.0 + delta_t)
            
        Args:
            memory: Optional RuntimeMemory instance to extract confidence, uses from.
            context_similarity: Semantic similarity between query and memory in [0.0, 1.0].
            delta_t: Elapsed time (in days or arbitrary time units) >= 0.0.
            confidence: Explicit confidence score if memory is not provided.
            successful_uses: Explicit successful_uses if memory is not provided.
            total_uses: Explicit total_uses if memory is not provided.
            
        Returns:
            Calculated utility in [0.0, 1.0].
        """
        if memory is not None:
            c = memory.confidence
            s_uses = memory.successful_uses
            t_uses = memory.total_uses
        else:
            c = confidence if confidence is not None else 0.5
            s_uses = successful_uses if successful_uses is not None else 0
            t_uses = total_uses if total_uses is not None else 0

        if not (0.0 <= context_similarity <= 1.0):
            raise ValueError(f"context_similarity must be between 0.0 and 1.0, got {context_similarity}")
        if not (0.0 <= c <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {c}")
        if delta_t < 0.0:
            raise ValueError(f"delta_t must be non-negative, got {delta_t}")

        # Success rate calculation
        if t_uses > 0:
            success_rate = s_uses / t_uses
        else:
            success_rate = 0.5  # Neutral initial prior

        # Recency calculation
        recency = 1.0 / (1.0 + delta_t)

        utility = c * success_rate * context_similarity * recency
        return max(0.0, min(1.0, round(utility, 6)))

    def transition_state(
        self,
        memory: RuntimeMemory,
        target_state: MemoryState,
    ) -> RuntimeMemory:
        """Explicitly transition memory lifecycle state with deterministic validation.
        
        Valid transitions:
            NEW -> ACTIVE, ARCHIVED, DELETED
            ACTIVE -> STABLE, DECAYING, ARCHIVED, DELETED
            STABLE -> DECAYING, ARCHIVED, DELETED
            DECAYING -> ACTIVE, STABLE, ARCHIVED, DELETED
            ARCHIVED -> DELETED
            DELETED -> (Terminal, no transitions allowed)
        """
        valid_transitions = {
            MemoryState.NEW: {MemoryState.ACTIVE, MemoryState.ARCHIVED, MemoryState.DELETED},
            MemoryState.ACTIVE: {MemoryState.STABLE, MemoryState.DECAYING, MemoryState.ARCHIVED, MemoryState.DELETED},
            MemoryState.STABLE: {MemoryState.DECAYING, MemoryState.ARCHIVED, MemoryState.DELETED},
            MemoryState.DECAYING: {MemoryState.ACTIVE, MemoryState.STABLE, MemoryState.ARCHIVED, MemoryState.DELETED},
            MemoryState.ARCHIVED: {MemoryState.DELETED},
            MemoryState.DELETED: set(),
        }

        if target_state == memory.status:
            return memory

        allowed = valid_transitions.get(memory.status, set())
        if target_state not in allowed:
            raise ValueError(
                f"Invalid lifecycle transition: cannot transition from {memory.status.value} to {target_state.value}"
            )

        return memory.copy_with(status=target_state)

    def admit(
        self,
        knowledge: RuntimeKnowledge,
        embedding: Optional[List[float]] = None,
        context_similarity: float = 1.0,
        current_epoch: Optional[int] = None,
    ) -> Optional[RuntimeMemory]:
        """Evaluate candidate knowledge against admission threshold for memory entry.
        
        Admission evaluates whether knowledge qualifies for persistent memory.
        It does NOT imply verified repair success.
        
        Initial candidate prior:
            confidence = 0.50
            successful_uses = 0, total_uses = 0 -> SuccessRate = 0.5
            delta_t = 0.0 -> Recency = 1.0
            initial_utility = 0.50 * 0.5 * context_similarity * 1.0 = 0.25 * context_similarity
            
        Returns:
            RuntimeMemory in NEW state if Utility >= admission_threshold, else None.
        """
        initial_utility = self.calculate_utility(
            confidence=knowledge.confidence,
            successful_uses=0,
            total_uses=0,
            context_similarity=context_similarity,
            delta_t=0.0,
        )

        if initial_utility < self.admission_threshold:
            return None

        epoch = self.get_current_epoch(current_epoch)
        now_iso = self.get_now_iso()
        return RuntimeMemory(
            context=dict(knowledge.context),
            failure_type=knowledge.failure_type,
            root_cause=knowledge.root_cause,
            repair_strategy=knowledge.repair_strategy,
            negative_constraints=list(knowledge.negative_constraints),
            candidate_replacements=list(knowledge.candidate_replacements),
            confidence=knowledge.confidence,
            utility=initial_utility,
            recency=1.0,
            embedding=list(embedding) if embedding is not None else None,
            status=MemoryState.NEW,
            successful_uses=0,
            total_uses=0,
            created_at=now_iso,
            last_used_at=now_iso,
            simulated_epoch=epoch,
            confidence_reference=knowledge.confidence,
            reference_epoch=epoch,
            archive_epoch=None,
        )

    def record_success(
        self,
        memory: RuntimeMemory,
        current_epoch: Optional[int] = None,
    ) -> RuntimeMemory:
        """Asymptotically escalate confidence upon successful query execution using memory.
        
        Equation: C_new = C_old + alpha * (1.0 - C_old)
        
        State transitions:
            NEW -> ACTIVE
            confidence >= 0.80 -> STABLE
        """
        if memory.status == MemoryState.DELETED:
            return memory

        epoch = self.get_current_epoch(current_epoch) if current_epoch is not None else (
            self.clock.current_epoch() if self.clock is not None else memory.simulated_epoch
        )
        new_succ = memory.successful_uses + 1
        new_total = memory.total_uses + 1

        c_old = memory.confidence
        c_new = c_old + self.escalation_rate * (1.0 - c_old)
        c_new = max(0.0, min(1.0, round(c_new, 6)))

        # Lifecycle state transition (ARCHIVED cannot be resurrected; DELETED is terminal)
        if memory.status in (MemoryState.ARCHIVED, MemoryState.DELETED):
            new_status = memory.status
        elif c_new >= self.stable_threshold:
            new_status = MemoryState.STABLE
        elif memory.status in (MemoryState.NEW, MemoryState.DECAYING):
            new_status = MemoryState.ACTIVE
        else:
            new_status = memory.status

        # Re-compute utility
        new_utility = self.calculate_utility(
            confidence=c_new,
            successful_uses=new_succ,
            total_uses=new_total,
            context_similarity=1.0,
            delta_t=0.0,
        )

        now_iso = self.get_now_iso()
        return memory.copy_with(
            confidence=c_new,
            utility=new_utility,
            recency=1.0,
            successful_uses=new_succ,
            total_uses=new_total,
            status=new_status,
            last_used_at=now_iso,
            simulated_epoch=epoch,
            confidence_reference=c_new,
            reference_epoch=epoch,
        )

    def record_failure(
        self,
        memory: RuntimeMemory,
        current_epoch: Optional[int] = None,
    ) -> RuntimeMemory:
        """Penalize confidence upon failed repair application using memory.
        
        Equation: C_new = max(0.0, C_old * (1.0 - beta))
        
        State transitions:
            C_new < 0.20 -> ARCHIVED
            STABLE and C_new < 0.80 -> DECAYING
        """
        if memory.status == MemoryState.DELETED:
            return memory

        epoch = self.get_current_epoch(current_epoch) if current_epoch is not None else (
            self.clock.current_epoch() if self.clock is not None else memory.simulated_epoch
        )
        new_total = memory.total_uses + 1
        # successful_uses is NOT incremented on failure

        c_old = memory.confidence
        c_new = max(0.0, round(c_old * (1.0 - self.penalty_rate), 6))

        archive_epoch = memory.archive_epoch
        if memory.status in (MemoryState.ARCHIVED, MemoryState.DELETED):
            new_status = memory.status
        elif c_new < self.archive_threshold:
            new_status = MemoryState.ARCHIVED
            archive_epoch = epoch
        elif memory.status == MemoryState.STABLE and c_new < self.stable_threshold:
            new_status = MemoryState.DECAYING
        else:
            new_status = memory.status

        new_utility = self.calculate_utility(
            confidence=c_new,
            successful_uses=memory.successful_uses,
            total_uses=new_total,
            context_similarity=1.0,
            delta_t=0.0,
        )

        now_iso = self.get_now_iso()
        return memory.copy_with(
            confidence=c_new,
            utility=new_utility,
            total_uses=new_total,
            status=new_status,
            last_used_at=now_iso,
            simulated_epoch=epoch,
            confidence_reference=c_new,
            reference_epoch=epoch,
            archive_epoch=archive_epoch,
        )

    def apply_decay(
        self,
        memory: RuntimeMemory,
        current_epoch: Optional[int] = None,
    ) -> RuntimeMemory:
        """Apply continuous exponential decay based on elapsed calendar days/epochs.
        
        Equation: C(t) = C_reference * exp(-lambda * delta_t)
        
        Uses tracked reference confidence and reference epoch to avoid compound double-decay.
        """
        if memory.status == MemoryState.DELETED:
            return memory

        epoch = self.get_current_epoch(current_epoch)
        delta_t = max(0, epoch - memory.reference_epoch)
        c_ref = memory.confidence_reference
        c_decayed = c_ref * math.exp(-self.decay_rate * delta_t)
        c_decayed = max(0.0, min(1.0, round(c_decayed, 6)))

        archive_epoch = memory.archive_epoch
        if c_decayed < self.archive_threshold and memory.status not in (MemoryState.ARCHIVED, MemoryState.DELETED):
            new_status = MemoryState.ARCHIVED
            archive_epoch = epoch
        elif c_decayed < self.stable_threshold and memory.status in (MemoryState.STABLE, MemoryState.ACTIVE):
            new_status = MemoryState.DECAYING
        else:
            new_status = memory.status

        new_utility = self.calculate_utility(
            confidence=c_decayed,
            successful_uses=memory.successful_uses,
            total_uses=memory.total_uses,
            context_similarity=1.0,
            delta_t=float(delta_t),
        )

        recency = 1.0 / (1.0 + float(delta_t))

        return memory.copy_with(
            confidence=c_decayed,
            utility=new_utility,
            recency=round(recency, 6),
            status=new_status,
            simulated_epoch=epoch,
            archive_epoch=archive_epoch,
        )

    def apply_decay_sweep(
        self,
        memories: List[RuntimeMemory],
        current_epoch: Optional[int] = None,
    ) -> List[RuntimeMemory]:
        """Sweep all memories for simulated time: apply decay and purge expired archives.
        
        If status == ARCHIVED and (current_epoch - archive_epoch) >= archive_retention_days:
            transitions to DELETED.
        """
        epoch = self.get_current_epoch(current_epoch)
        updated_list: List[RuntimeMemory] = []
        for mem in memories:
            decayed_mem = self.apply_decay(mem, epoch)
            if decayed_mem.status == MemoryState.ARCHIVED:
                arch_epoch = decayed_mem.archive_epoch or decayed_mem.simulated_epoch
                if (epoch - arch_epoch) >= self.archive_retention_days:
                    decayed_mem = decayed_mem.copy_with(
                        status=MemoryState.DELETED,
                        simulated_epoch=epoch,
                    )
            updated_list.append(decayed_mem)
        return updated_list

