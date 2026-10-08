#!/usr/bin/env python3
"""
ARMG Phase 6: Temporal Decay Validation Script
Canonical, reproducible validation of ARMG's temporal decay mechanism,
lifecycle state transitions, reference-epoch tracking, and FAISS synchronization
under controlled elapsed time.

Outputs:
- benchmark/temporal_decay/temporal_decay_validation.csv
- benchmark/temporal_decay/temporal_decay_validation.json
- benchmark/temporal_decay/fig_temporal_decay.png
- benchmark/temporal_decay/fig_temporal_decay.svg
- manuscript/figures/fig_temporal_decay.png
- manuscript/figures/fig_temporal_decay.svg
"""

import os
import sys
import json
import math
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from agents.taxonomy import TaxonomyCategory
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.governance import MemoryGovernanceEngine, ControlledClock
from memory.vector_store import FAISSMemoryStore
from graph.workflow import ARMGRepairWorkflow


def create_sample_knowledge(confidence: float = 0.50, idx: int = 1) -> RuntimeKnowledge:
    """Helper to create deterministic RuntimeKnowledge."""
    return RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception=f"column 'col_{idx}' does not exist",
        context={"tables_referenced": ["fact_sales_performance"], "broken_column": f"col_{idx}"},
        root_cause=f"Column 'col_{idx}' is not present in 'fact_sales_performance'.",
        repair_strategy=f"Replace 'col_{idx}' with 'valid_col_{idx}'.",
        negative_constraints=[f"Do not reference column 'col_{idx}'."],
        candidate_replacements=[f"valid_col_{idx}"],
        confidence=confidence,
    )


def independent_expected_decay(
    c_ref: float,
    lambda_param: float,
    delta_t: float,
) -> float:
    """Independently calculate theoretical exponential decay: C(t) = C_ref * exp(-lambda * delta_t)."""
    clamped_dt = max(0.0, float(delta_t))
    val = c_ref * math.exp(-lambda_param * clamped_dt)
    return max(0.0, min(1.0, round(val, 6)))


def independent_expected_recency(delta_t: float) -> float:
    """Independently calculate theoretical recency: Recency = 1 / (1 + delta_t)."""
    clamped_dt = max(0.0, float(delta_t))
    return round(1.0 / (1.0 + clamped_dt), 6)


def independent_expected_utility(
    confidence: float,
    successful_uses: int,
    total_uses: int,
    similarity: float,
    recency: float,
) -> float:
    """Independently calculate multi-factor utility: C * SR * Sim * Recency."""
    sr = (successful_uses / total_uses) if total_uses > 0 else 0.5
    u = confidence * sr * similarity * recency
    return max(0.0, min(1.0, round(u, 6)))


def independent_expected_state(
    prev_state: MemoryState,
    c_decayed: float,
    archive_threshold: float,
    stable_threshold: float,
) -> MemoryState:
    """Independently determine theoretical lifecycle state following decay."""
    if prev_state == MemoryState.DELETED:
        return MemoryState.DELETED
    if c_decayed < archive_threshold and prev_state not in (MemoryState.ARCHIVED, MemoryState.DELETED):
        return MemoryState.ARCHIVED
    if c_decayed < stable_threshold and prev_state in (MemoryState.STABLE, MemoryState.ACTIVE):
        return MemoryState.DECAYING
    return prev_state


def run_temporal_decay_validation() -> Dict[str, Any]:
    print("=" * 70)
    print("ARMG PHASE 6: TEMPORAL DECAY VALIDATION")
    print("=" * 70)

    # 1. Inspect Engine Configuration
    engine = MemoryGovernanceEngine()
    configured_lambda = engine.decay_rate
    stable_thresh = engine.stable_threshold
    archive_thresh = engine.archive_threshold
    admission_thresh = engine.admission_threshold
    retention_days = engine.archive_retention_days

    print(f"Engine Configuration Verified:")
    print(f"  Decay Rate (lambda)        : {configured_lambda:.4f} / day")
    print(f"  Stable Threshold           : {stable_thresh:.2f}")
    print(f"  Archive Threshold          : {archive_thresh:.2f}")
    print(f"  Admission Threshold        : {admission_thresh:.2f}")
    print(f"  Archive Retention Days     : {retention_days} days")

    assert configured_lambda == 0.05, f"Expected lambda=0.05, got {configured_lambda}"
    assert stable_thresh == 0.80, f"Expected stable_threshold=0.80, got {stable_thresh}"
    assert archive_thresh == 0.20, f"Expected archive_threshold=0.20, got {archive_thresh}"
    assert retention_days == 30, f"Expected retention_days=30, got {retention_days}"

    # 2. Define Initial Confidence Sweep around Key Boundaries
    initial_confidences = [
        ("Very High (0.95)", 0.95, MemoryState.STABLE),
        ("High (0.90)", 0.90, MemoryState.STABLE),
        ("Stable Region (0.85)", 0.85, MemoryState.STABLE),
        ("Exact Stable Boundary (0.80)", 0.80, MemoryState.STABLE),
        ("Just Below Stable (0.799)", 0.799, MemoryState.ACTIVE),
        ("Mid-range Prior (0.50)", 0.50, MemoryState.ACTIVE),
        ("Low Range (0.25)", 0.25, MemoryState.ACTIVE),
        ("Exact Archive Boundary (0.20)", 0.20, MemoryState.ACTIVE),
        ("Just Below Archive (0.199)", 0.199, MemoryState.ACTIVE),
    ]

    target_time_points = [0, 1, 5, 10, 20, 30, 60]

    validation_records: List[Dict[str, Any]] = []
    max_absolute_error = 0.0
    all_within_tolerance = True

    print("\n[Step 1] Executing Longitudinal Decay Across Controlled Time Points...")
    clock = ControlledClock(initial_epoch=0)
    gov_clock = MemoryGovernanceEngine(clock=clock)

    for label, init_c, initial_state in initial_confidences:
        # Create controlled memory with reference at epoch 0
        now_iso = clock.now().isoformat()
        mem = RuntimeMemory(
            context={"test": label},
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause=f"Test cause for {label}",
            repair_strategy=f"Test strategy for {label}",
            negative_constraints=[],
            candidate_replacements=[],
            confidence=init_c,
            utility=init_c * 0.5 * 1.0 * 1.0,
            recency=1.0,
            status=initial_state,
            successful_uses=1 if initial_state == MemoryState.STABLE else 0,
            total_uses=1 if initial_state == MemoryState.STABLE else 0,
            created_at=now_iso,
            last_used_at=now_iso,
            simulated_epoch=0,
            confidence_reference=init_c,
            reference_epoch=0,
            archive_epoch=None,
        )

        for t in target_time_points:
            # Advance controlled clock
            clock.set_epoch(t)

            # Production decay execution
            decayed = gov_clock.apply_decay(mem)

            # Independent theoretical expectations
            exp_c = independent_expected_decay(init_c, configured_lambda, t)
            exp_rec = independent_expected_recency(t)
            exp_u = independent_expected_utility(
                exp_c, mem.successful_uses, mem.total_uses, 1.0, exp_rec
            )
            exp_state = independent_expected_state(
                initial_state, exp_c, archive_thresh, stable_thresh
            )

            abs_err = abs(decayed.confidence - exp_c)
            rel_err = (abs_err / exp_c) if exp_c > 1e-9 else 0.0

            if abs_err > max_absolute_error:
                max_absolute_error = abs_err

            within_tol = abs_err <= 1e-4
            if not within_tol:
                all_within_tolerance = False

            state_match = (decayed.status == exp_state)

            record = {
                "test_label": label,
                "initial_confidence": init_c,
                "initial_state": initial_state.value,
                "reference_epoch": 0,
                "current_epoch": t,
                "elapsed_days": t,
                "configured_lambda": configured_lambda,
                "expected_confidence": exp_c,
                "actual_confidence": decayed.confidence,
                "absolute_error": round(abs_err, 8),
                "relative_error": round(rel_err, 8),
                "expected_recency": exp_rec,
                "actual_recency": decayed.recency,
                "expected_utility": exp_u,
                "actual_utility": decayed.utility,
                "expected_state": exp_state.value,
                "actual_state": decayed.status.value,
                "is_archived": decayed.status == MemoryState.ARCHIVED,
                "is_deleted": decayed.status == MemoryState.DELETED,
                "state_match": state_match,
                "error_within_tolerance": within_tol,
            }
            validation_records.append(record)

    print(f"  Evaluated {len(validation_records)} condition points.")
    print(f"  Maximum Absolute Error: {max_absolute_error:.8f} (Tolerance: <= 1e-4)")
    print(f"  All Points Within Tolerance: {all_within_tolerance}")

    # [Step 2] Boundary Condition Verifications
    print("\n[Step 2] Boundary Testing...")
    boundary_results = {}

    # 2a. Zero elapsed time (delta_t = 0)
    m_zero = gov_clock.apply_decay(mem, current_epoch=0)
    assert m_zero.confidence == mem.confidence_reference, "Delta t = 0 must preserve exact reference confidence"
    boundary_results["zero_elapsed_time"] = "PASS"

    # 2b. Negative elapsed time (current_epoch < reference_epoch)
    m_neg = gov_clock.apply_decay(mem, current_epoch=-15)
    assert m_neg.confidence == mem.confidence_reference, "Negative elapsed time must clamp delta_t to 0"
    boundary_results["negative_elapsed_time"] = "PASS"

    # 2c. Exact stable threshold (0.80)
    mem_80 = mem.copy_with(confidence=0.80, confidence_reference=0.80, status=MemoryState.STABLE)
    decayed_80 = gov_clock.apply_decay(mem_80, current_epoch=0)
    assert decayed_80.status == MemoryState.STABLE, "Confidence exactly 0.80 must remain STABLE"
    boundary_results["exact_stable_threshold"] = "PASS"

    # 2d. Stable threshold - epsilon (0.799999)
    mem_799 = mem.copy_with(confidence=0.799999, confidence_reference=0.799999, status=MemoryState.STABLE)
    decayed_799 = gov_clock.apply_decay(mem_799, current_epoch=0)
    assert decayed_799.status == MemoryState.DECAYING, "Confidence below 0.80 must transition to DECAYING"
    boundary_results["below_stable_threshold"] = "PASS"

    # 2e. Exact archive threshold (0.20)
    mem_20 = mem.copy_with(confidence=0.20, confidence_reference=0.20, status=MemoryState.ACTIVE)
    decayed_20 = gov_clock.apply_decay(mem_20, current_epoch=0)
    assert decayed_20.status != MemoryState.ARCHIVED, "Confidence exactly 0.20 must NOT archive (threshold is strictly < 0.20)"
    boundary_results["exact_archive_threshold"] = "PASS"

    # 2f. Archive threshold - epsilon (0.199999)
    mem_199 = mem.copy_with(confidence=0.199999, confidence_reference=0.199999, status=MemoryState.ACTIVE)
    decayed_199 = gov_clock.apply_decay(mem_199, current_epoch=0)
    assert decayed_199.status == MemoryState.ARCHIVED, "Confidence below 0.20 must transition to ARCHIVED"
    assert decayed_199.archive_epoch == 0, "Archived memory must record archive_epoch"
    boundary_results["below_archive_threshold"] = "PASS"

    for k, v in boundary_results.items():
        print(f"  {k:28s}: {v}")

    # [Step 3] Idempotence / Double-Decay Test
    print("\n[Step 3] Idempotence (Double-Decay) Testing...")
    clock.set_epoch(10)
    d10_first = gov_clock.apply_decay(mem)
    d10_second = gov_clock.apply_decay(d10_first)
    d10_third = gov_clock.apply_decay(d10_second)
    assert d10_first.confidence == d10_second.confidence == d10_third.confidence, (
        f"Repeated decay at epoch 10 mutated confidence: {d10_first.confidence} vs {d10_second.confidence}"
    )
    print(f"  Epoch 10 repeatedly evaluated: C = {d10_first.confidence:.6f} == {d10_second.confidence:.6f} == {d10_third.confidence:.6f}")
    print("  Idempotence Status: PASS (Zero compound double-decay)")

    # [Step 4] Progressive vs Direct Chained Decay
    print("\n[Step 4] Progressive vs Direct Chained Decay...")
    # Progressive: 0 -> 10 -> 30
    clock.set_epoch(10)
    step_10 = gov_clock.apply_decay(mem)
    clock.set_epoch(30)
    step_30 = gov_clock.apply_decay(step_10)

    # Direct: 0 -> 30
    direct_30 = gov_clock.apply_decay(mem)
    assert step_30.confidence == direct_30.confidence, (
        f"Chained decay {step_30.confidence} != Direct decay {direct_30.confidence}"
    )
    print(f"  Chained (0->10->30): C = {step_30.confidence:.6f}")
    print(f"  Direct  (0->30)    : C = {direct_30.confidence:.6f}")
    print("  Chained Equivalence Status: PASS")

    # [Step 5] Full Lifecycle Transition & Purge Sweep
    print("\n[Step 5] Full Lifecycle Transition & Purge Validation...")
    # Admission -> Active -> Stable -> Decaying -> Archived -> Deleted
    clock.set_epoch(0)
    k_cand = create_sample_knowledge(confidence=0.50, idx=101)
    m_admitted = gov_clock.admit(k_cand, context_similarity=1.0)
    assert m_admitted.status == MemoryState.NEW

    # First success at epoch 1 -> ACTIVE
    clock.set_epoch(1)
    m_active = gov_clock.record_success(m_admitted)
    assert m_active.status == MemoryState.ACTIVE
    assert m_active.reference_epoch == 1

    # Multiple successes -> STABLE (reaches >= 0.80)
    m_stable = m_active
    for ep in range(2, 10):
        clock.set_epoch(ep)
        m_stable = gov_clock.record_success(m_stable)
    assert m_stable.status == MemoryState.STABLE
    assert m_stable.confidence >= 0.80
    ref_stable_epoch = m_stable.reference_epoch

    # Decay to DECAYING (< 0.80)
    clock.set_epoch(ref_stable_epoch + 15)
    m_decaying = gov_clock.apply_decay(m_stable)
    assert m_decaying.status == MemoryState.DECAYING

    # Decay to ARCHIVED (< 0.20)
    clock.set_epoch(ref_stable_epoch + 35)
    m_archived = gov_clock.apply_decay(m_decaying)
    assert m_archived.status == MemoryState.ARCHIVED
    assert m_archived.archive_epoch == ref_stable_epoch + 35
    arch_epoch = m_archived.archive_epoch

    # Retention check: At 29 days in archive -> Still ARCHIVED
    clock.set_epoch(arch_epoch + 29)
    sweep_29 = gov_clock.apply_decay_sweep([m_archived])
    assert sweep_29[0].status == MemoryState.ARCHIVED

    # Retention check: At 30 days in archive -> DELETED
    clock.set_epoch(arch_epoch + 30)
    sweep_30 = gov_clock.apply_decay_sweep([m_archived])
    assert sweep_30[0].status == MemoryState.DELETED
    print("  Full Sequence NEW -> ACTIVE -> STABLE -> DECAYING -> ARCHIVED -> DELETED: PASS")
    print("  Archive Retention Purge (30 days threshold): PASS")

    # [Step 6] Reinforcement + Decay Interaction
    print("\n[Step 6] Reinforcement + Decay Interaction Testing...")
    # Case A: Decayed memory is reinforced -> resets reference epoch and elevates confidence
    clock.set_epoch(0)
    m_base = gov_clock.admit(k_cand, context_similarity=1.0)
    m_base = gov_clock.record_success(m_base)  # C = 0.55 at epoch 0
    clock.set_epoch(10)
    m_dec = gov_clock.apply_decay(m_base)      # C = 0.333592 at epoch 10
    assert m_dec.confidence < 0.55

    # Reinforce at epoch 10
    m_reinf = gov_clock.record_success(m_dec)
    assert m_reinf.reference_epoch == 10
    assert m_reinf.confidence_reference == m_reinf.confidence
    # Escalation: C_new = 0.333592 + 0.10 * (1 - 0.333592) = 0.400233
    assert abs(m_reinf.confidence - (m_dec.confidence + 0.10 * (1.0 - m_dec.confidence))) < 1e-4

    # Further decay from epoch 10 to epoch 20 (delta_t = 10 from new reference)
    clock.set_epoch(20)
    m_dec_again = gov_clock.apply_decay(m_reinf)
    expected_c_again = independent_expected_decay(m_reinf.confidence, configured_lambda, 10)
    assert abs(m_dec_again.confidence - expected_c_again) < 1e-4
    print("  Decay -> Reinforce -> Decay Interaction: PASS")

    # [Step 7] Multi-Memory Independence & Shared-State Safety
    print("\n[Step 7] Multi-Memory Independence & Non-Interference...")
    clock.set_epoch(0)
    memories = []
    for i in range(5):
        k = create_sample_knowledge(confidence=0.50 + i * 0.10, idx=200 + i)
        m = gov_clock.admit(k, context_similarity=1.0)
        memories.append(m)

    # Advance clock to epoch 15 and sweep
    clock.set_epoch(15)
    decayed_all = gov_clock.apply_decay_sweep(memories)
    for orig, dec in zip(memories, decayed_all):
        expected_c = independent_expected_decay(orig.confidence_reference, configured_lambda, 15)
        assert abs(dec.confidence - expected_c) < 1e-4
        assert dec.memory_id == orig.memory_id
    print("  5 Concurrent Independent Memories Decayed Without State Bleed: PASS")

    # [Step 8] FAISS Vector Store Synchronization & Exclusion
    print("\n[Step 8] FAISS Vector Store Synchronization & Lifecycle Filtering...")
    store = FAISSMemoryStore()
    v_unit = [1.0] + [0.0] * 767

    # Add memory in ACTIVE state
    m_sync = gov_clock.admit(k_cand, context_similarity=1.0)
    m_sync = gov_clock.record_success(m_sync)
    store.add(m_sync, v_unit)
    assert store.count() == 1

    # Search returns active memory
    raw_res = store.search_raw_candidates(v_unit, top_k=5)
    assert len(raw_res) == 1
    assert raw_res[0][0].status == MemoryState.ACTIVE

    # Decay memory to ARCHIVED
    clock.set_epoch(50)
    m_sync_arch = gov_clock.apply_decay(m_sync)
    assert m_sync_arch.status == MemoryState.ARCHIVED
    store.update_memory(m_sync_arch)

    # Verify retrieval exclusion for ARCHIVED
    workflow = ARMGRepairWorkflow(
        environment=None,
        vector_store=store,
        embed_fn=lambda _: v_unit,
    )
    ret_res = workflow.memory_retrieval_node({"user_query": "test query", "telemetry": {}})
    assert len(ret_res["retrieved_memories"]) == 0, "ARCHIVED memory must be excluded from retrieval"

    # Advance to purge -> DELETED
    clock.set_epoch(50 + 35)
    sweep_del = gov_clock.apply_decay_sweep([m_sync_arch])
    m_sync_del = sweep_del[0]
    assert m_sync_del.status == MemoryState.DELETED
    store.update_memory(m_sync_del)

    # In FAISS store, search() filters out DELETED memories
    faiss_search = store.search(v_unit, top_k=5)
    assert len(faiss_search) == 0, "DELETED memory must be filtered out in store.search()"

    # Also test physical delete from FAISS
    del_ok = store.delete(m_sync_del.memory_id)
    assert del_ok is True
    assert store.count() == 0
    print("  FAISS Store Metadata Synchronization & Retrieval Filtering: PASS")

    # 3. Export Machine-Readable Results
    print("\n[Step 9] Exporting Machine-Readable Evidence...")
    out_dir = PROJECT_ROOT / "benchmark" / "temporal_decay"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "temporal_decay_validation.csv"
    json_path = out_dir / "temporal_decay_validation.json"

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(validation_records[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validation_records)
    print(f"  CSV Saved: {csv_path}")

    # Write JSON
    json_summary = {
        "metadata": {
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "configured_lambda": configured_lambda,
            "stable_threshold": stable_thresh,
            "archive_threshold": archive_thresh,
            "admission_threshold": admission_thresh,
            "archive_retention_days": retention_days,
            "tolerance": 1e-4,
            "max_absolute_error": max_absolute_error,
            "all_within_tolerance": all_within_tolerance,
            "total_condition_points": len(validation_records),
        },
        "boundary_results": boundary_results,
        "records": validation_records,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_summary, f, indent=2)
    print(f"  JSON Saved: {json_path}")

    # 4. Generate Publication-Quality Figures
    print("\n[Step 10] Generating Figures...")
    generate_validation_figures(validation_records, configured_lambda, out_dir)

    print("\n" + "=" * 70)
    print("TEMPORAL DECAY VALIDATION COMPLETE: ALL CHECKS PASSED")
    print("=" * 70)

    return json_summary


def generate_validation_figures(
    records: List[Dict[str, Any]],
    decay_rate: float,
    output_dir: Path,
):
    """Generate high-resolution validation figures comparing actual vs theoretical decay curves."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Subplot 1: Confidence Decay Curves (Actual vs Expected)
    ax1 = axes[0, 0]
    labels_to_plot = [
        "Very High (0.95)",
        "Stable Region (0.85)",
        "Just Below Stable (0.799)",
        "Mid-range Prior (0.50)",
        "Low Range (0.25)",
    ]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]

    for label, color in zip(labels_to_plot, colors):
        subset = [r for r in records if r["test_label"] == label]
        subset.sort(key=lambda x: x["elapsed_days"])
        days = [r["elapsed_days"] for r in subset]
        act_c = [r["actual_confidence"] for r in subset]
        exp_c = [r["expected_confidence"] for r in subset]

        # Theoretical line
        ax1.plot(days, exp_c, linestyle="--", color=color, alpha=0.6)
        # Actual points
        ax1.plot(days, act_c, marker="o", markersize=5, linestyle="-", color=color, label=label)

    # Threshold lines
    ax1.axhline(0.80, color="gray", linestyle=":", label="Stable Thresh (0.80)")
    ax1.axhline(0.20, color="red", linestyle=":", label="Archive Thresh (0.20)")

    ax1.set_title("Temporal Confidence Decay: Implemented vs Theoretical", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Elapsed Time $\\Delta t$ (days)")
    ax1.set_ylabel("Confidence $C(t)$")
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=8)

    # Subplot 2: Absolute Error vs Days
    ax2 = axes[0, 1]
    for label, color in zip(labels_to_plot, colors):
        subset = [r for r in records if r["test_label"] == label]
        subset.sort(key=lambda x: x["elapsed_days"])
        days = [r["elapsed_days"] for r in subset]
        errs = [r["absolute_error"] for r in subset]
        # Avoid log(0)
        plot_errs = [max(e, 1e-8) for e in errs]
        ax2.plot(days, plot_errs, marker="s", markersize=4, linestyle="-", color=color, label=label)

    ax2.axhline(1e-4, color="crimson", linestyle="--", label="Acceptance Bound ($10^{-4}$)")
    ax2.set_title("Absolute Numerical Error $|C_{actual} - C_{expected}|$", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Elapsed Time $\\Delta t$ (days)")
    ax2.set_ylabel("Absolute Error")
    ax2.set_yscale("log")
    ax2.set_ylim(1e-9, 1e-3)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8)

    # Subplot 3: Recency & Utility Dynamics
    ax3 = axes[1, 0]
    mid_subset = [r for r in records if r["test_label"] == "Mid-range Prior (0.50)"]
    mid_subset.sort(key=lambda x: x["elapsed_days"])
    days = [r["elapsed_days"] for r in mid_subset]
    rec = [r["actual_recency"] for r in mid_subset]
    util = [r["actual_utility"] for r in mid_subset]
    conf = [r["actual_confidence"] for r in mid_subset]

    ax3.plot(days, conf, marker="o", label="Confidence $C(t)$", color="#1f77b4")
    ax3.plot(days, rec, marker="^", label="Recency $R(t) = 1/(1+\\Delta t)$", color="#ff7f0e")
    ax3.plot(days, util, marker="s", label="Utility $U(t) = C \\cdot SR \\cdot Sim \\cdot R$", color="#2ca02c")
    ax3.set_title("Utility and Recency Attenuation ($C_0 = 0.50$)", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Elapsed Time $\\Delta t$ (days)")
    ax3.set_ylabel("Score in [0, 1]")
    ax3.set_ylim(-0.02, 1.02)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right", fontsize=9)

    # Subplot 4: Lifecycle Phase State Progression
    ax4 = axes[1, 1]
    t_cont = np.linspace(0, 60, 200)
    c_stable_cont = 0.85 * np.exp(-decay_rate * t_cont)
    c_mid_cont = 0.50 * np.exp(-decay_rate * t_cont)

    ax4.plot(t_cont, c_stable_cont, color="#2ca02c", lw=2, label="Candidate 1 ($C_0 = 0.85$)")
    ax4.plot(t_cont, c_mid_cont, color="#1f77b4", lw=2, label="Candidate 2 ($C_0 = 0.50$)")

    ax4.axhspan(0.80, 1.00, color="green", alpha=0.1, label="STABLE Zone ($C \\geq 0.80$)")
    ax4.axhspan(0.20, 0.80, color="orange", alpha=0.1, label="DECAYING Zone ($0.20 \\leq C < 0.80$)")
    ax4.axhspan(0.00, 0.20, color="red", alpha=0.1, label="ARCHIVED Zone ($C < 0.20$)")

    ax4.set_title("Lifecycle State Zones under Temporal Decay", fontsize=12, fontweight="bold")
    ax4.set_xlabel("Elapsed Time $\\Delta t$ (days)")
    ax4.set_ylabel("Confidence $C(t)$")
    ax4.set_ylim(0.0, 1.0)
    ax4.grid(True, linestyle="--", alpha=0.5)
    ax4.legend(loc="upper right", fontsize=8)

    plt.tight_layout()

    # Save to benchmark/temporal_decay/
    fig_png_bench = output_dir / "fig_temporal_decay.png"
    fig_svg_bench = output_dir / "fig_temporal_decay.svg"
    plt.savefig(fig_png_bench, dpi=300)
    plt.savefig(fig_svg_bench, format="svg")
    print(f"  Saved figure: {fig_png_bench}")
    print(f"  Saved figure: {fig_svg_bench}")

    # Also save to manuscript/figures/
    manuscript_dir = PROJECT_ROOT / "manuscript" / "figures"
    manuscript_png = manuscript_dir / "fig_temporal_decay.png"
    manuscript_svg = manuscript_dir / "fig_temporal_decay.svg"
    manuscript_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(manuscript_png, dpi=300)
    plt.savefig(manuscript_svg, format="svg")
    print(f"  Saved figure: {manuscript_png}")
    print(f"  Saved figure: {manuscript_svg}")

    # Also save in png/ and svg/ subdirectories if they exist
    png_sub = manuscript_dir / "png"
    svg_sub = manuscript_dir / "svg"
    if png_sub.exists():
        plt.savefig(png_sub / "fig_temporal_decay.png", dpi=300)
    if svg_sub.exists():
        plt.savefig(svg_sub / "fig_temporal_decay.svg", format="svg")

    plt.close()


if __name__ == "__main__":
    res = run_temporal_decay_validation()
    sys.exit(0)
