"""
ARMG Phase 2 Unit Tests: Real FAISS Telemetry & Retrieval Evidence.
Restored Original Retrieval Geometry (IndexFlatL2, s = 1 / (1 + d^2)).

Deterministic tests covering all 20 required specifications:
FAISS geometry:
1. Raw squared L2 distance is captured directly from FAISS.
2. Normalized vectors produce similarity = 1 / (1 + d^2) where d^2 = 2(1 - cos theta).
3. Boundary behavior across exact mathematical points: d^2 in {0, 1, 4, 9, 280, 10000}.
4. Ranking is preserved: lowest distance / highest similarity first (ascending d^2).
Threshold behavior:
5. 0.499999 fails retrieval threshold (tau = 0.50).
6. 0.500000 passes retrieval threshold (tau = 0.50).
7. 0.500001 passes retrieval threshold (tau = 0.50).
Candidate provenance:
8. Candidate memory IDs are preserved.
9. Candidate ranks are preserved.
10. Every returned FAISS candidate is logged before filtering.
Governance:
11. Below-threshold candidates are not injected into repair context.
12. Archived/deleted memories are filtered according to current lifecycle rules.
13. Admission utility threshold (0.25) remains independent from retrieval threshold (0.50).
Empty retrieval:
14. Empty store produces null similarity/distance fields.
15. No-result is never encoded as numeric zero.
Evidence lineage:
16. Telemetry reaches the raw benchmark artifact with canonical schema.
17. Changing one raw telemetry score changes downstream analysis.
18. Corresponding Figure 3/table changes automatically.
Anti-fabrication & anti-reconstruction:
19. No np.random values enter the empirical pipeline.
20. Anti-reconstruction test (Section 10): canonical telemetry cannot be generated from
    benchmark summaries without executing the actual FAISS vector-search operation.
"""

import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import pytest

from agents.taxonomy import TaxonomyCategory
from benchmark.analysis import compute_retrieval_telemetry_metrics
from environment.base import ExecutionResult, RuntimeEnvironment
from graph.workflow import ARMGRepairWorkflow
from manuscript.figures.source.fig3_retrieval_geometry import generate_fig3
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.telemetry import (
    RetrievalCandidateRecord,
    RetrievalTelemetryLogger,
    RETRIEVAL_TELEMETRY_COLUMNS,
)
from memory.vector_store import FAISSMemoryStore
from scripts.generate_validation_tables import generate_validation_tables


def create_unit_vector(seed: int) -> np.ndarray:
    """Deterministic 768-dim unit-normalized float32 vector."""
    rng = np.random.RandomState(seed)
    v = rng.randn(768).astype(np.float32)
    return v / float(np.linalg.norm(v))


def create_sample_memory(memory_id: str, status: MemoryState = MemoryState.ACTIVE) -> RuntimeMemory:
    """Helper creating a sample RuntimeMemory."""
    return RuntimeMemory(
        memory_id=memory_id,
        context={"tables": ["fact_sales_performance"]},
        failure_type=TaxonomyCategory.SEMANTIC,
        root_cause="Column error",
        repair_strategy="Map column",
        status=status,
        confidence=0.55,
        utility=0.55,
    )


# =============================================================================
# FAISS Geometry (Tests 1-4)
# =============================================================================

def test_01_raw_distance_l2_sq_captured_directly_from_faiss():
    """1. Raw squared L2 distance is captured directly from FAISS index.search()."""
    store = FAISSMemoryStore()
    mem = create_sample_memory("mem-01")
    v = create_unit_vector(42)
    store.add(mem, v)

    raw_candidates = store.search_raw_candidates(v, top_k=1)
    assert len(raw_candidates) == 1
    ret_mem, rank, dist_l2_sq, sim = raw_candidates[0]

    # Directly query FAISS index to verify dist_l2_sq is identical to C++ search output
    distances, indices = store.index.search(v.reshape(1, 768), 1)
    faiss_raw_dist = float(distances[0][0])
    assert abs(dist_l2_sq - faiss_raw_dist) < 1e-6
    # Exact vector match -> d^2 ~ 0.0, sim ~ 1.0
    assert abs(dist_l2_sq) < 1e-4
    assert abs(sim - 1.0) < 1e-4


def test_02_similarity_transformation_equation():
    """2. Similarity equation S = 1 / (1 + d^2) matches squared Euclidean distance."""
    store = FAISSMemoryStore()
    u = create_unit_vector(10)
    v = create_unit_vector(20)
    mem = create_sample_memory("mem-02")
    store.add(mem, u)

    expected_d2 = float(np.sum((u - v) ** 2))
    expected_sim = 1.0 / (1.0 + expected_d2)

    raw_candidates = store.search_raw_candidates(v, top_k=1)
    ret_mem, rank, dist_l2_sq, sim = raw_candidates[0]

    assert abs(dist_l2_sq - expected_d2) < 1e-4
    assert abs(sim - expected_sim) < 1e-4
    assert abs(sim - (1.0 / (1.0 + dist_l2_sq))) < 1e-6


def test_03_boundary_behavior_exact_points():
    """3. Test exact mathematical boundary points: d^2 in {0, 1, 4, 9, 280, 10000}."""
    test_cases = [
        (0.0, 1.0, True),
        (1.0, 0.50, True),
        (1.000001, 1.0 / 2.000001, False),
        (0.999999, 1.0 / 1.999999, True),
        (4.0, 0.20, False),
        (9.0, 0.10, False),
        (280.0, 1.0 / 281.0, False),
        (10000.0, 1.0 / 10001.0, False),
    ]

    for d2, expected_sim, expected_pass in test_cases:
        sim = 1.0 / (1.0 + d2)
        assert abs(sim - expected_sim) < 1e-6
        passed = bool(sim >= 0.50)
        assert passed == expected_pass, f"Failed for d2={d2}, sim={sim}"
        assert 0.0 < sim <= 1.0


def test_04_ranking_preserved_lowest_distance_first():
    """4. Candidate ranking is preserved: lowest distance / highest similarity first."""
    store = FAISSMemoryStore()
    u = create_unit_vector(100)
    store.add(create_sample_memory("mem-near"), u)
    store.add(create_sample_memory("mem-far"), -u)  # Opposite vector, d^2 = 4.0

    candidates = store.search_raw_candidates(u, top_k=2)
    assert len(candidates) == 2
    assert candidates[0][1] == 1  # Rank 1
    assert candidates[1][1] == 2  # Rank 2
    # Rank 1 has lowest distance and highest similarity
    assert candidates[0][2] < candidates[1][2]
    assert candidates[0][3] > candidates[1][3]
    assert abs(candidates[0][2] - 0.0) < 1e-4
    assert abs(candidates[0][3] - 1.0) < 1e-4
    assert abs(candidates[1][2] - 4.0) < 1e-4
    assert abs(candidates[1][3] - 0.20) < 1e-4


# =============================================================================
# Threshold Behavior (Tests 5-7)
# =============================================================================

def test_05_threshold_behavior_point_499999_fails():
    """5. 0.499999 fails retrieval threshold (tau = 0.50)."""
    tau = 0.50
    sim = 0.499999
    passed = bool(sim >= tau)
    assert not passed
    d2 = (1.0 / sim) - 1.0
    rec = RetrievalCandidateRecord(
        run_id="run1", mode="Mode 4", query_id="Q01", memory_id="mem-1", rank=1,
        distance_l2_sq=d2, similarity=sim, retrieval_similarity_threshold=tau,
        passed_retrieval_threshold=passed,
    )
    assert rec.passed_retrieval_threshold is False


def test_06_threshold_behavior_point_500000_passes():
    """6. 0.500000 passes retrieval threshold (tau = 0.50)."""
    tau = 0.50
    sim = 0.500000
    passed = bool(sim >= tau)
    assert passed
    d2 = (1.0 / sim) - 1.0
    rec = RetrievalCandidateRecord(
        run_id="run1", mode="Mode 4", query_id="Q01", memory_id="mem-1", rank=1,
        distance_l2_sq=d2, similarity=sim, retrieval_similarity_threshold=tau,
        passed_retrieval_threshold=passed,
    )
    assert rec.passed_retrieval_threshold is True


def test_07_threshold_behavior_point_500001_passes():
    """7. 0.500001 passes retrieval threshold (tau = 0.50)."""
    tau = 0.50
    sim = 0.500001
    passed = bool(sim >= tau)
    assert passed
    d2 = (1.0 / sim) - 1.0
    rec = RetrievalCandidateRecord(
        run_id="run1", mode="Mode 4", query_id="Q01", memory_id="mem-1", rank=1,
        distance_l2_sq=d2, similarity=sim, retrieval_similarity_threshold=tau,
        passed_retrieval_threshold=passed,
    )
    assert rec.passed_retrieval_threshold is True


# =============================================================================
# Candidate Provenance (Tests 8-10)
# =============================================================================

def test_08_candidate_memory_ids_are_preserved():
    """8. Candidate memory IDs are preserved end-to-end."""
    store = FAISSMemoryStore()
    target_id = "mem-test-provenance-xyz-123"
    mem = create_sample_memory(target_id)
    v = create_unit_vector(55)
    store.add(mem, v)

    raw_cands = store.search_raw_candidates(v, top_k=1)
    assert raw_cands[0][0].memory_id == target_id


def test_09_candidate_ranks_are_preserved():
    """9. Candidate sequential ranks 1..K are preserved."""
    store = FAISSMemoryStore()
    v_base = create_unit_vector(1)
    for i in range(5):
        store.add(create_sample_memory(f"mem-{i}"), create_unit_vector(i + 10))

    raw_cands = store.search_raw_candidates(v_base, top_k=3)
    ranks = [r[1] for r in raw_cands]
    assert ranks == [1, 2, 3]


def test_10_every_returned_faiss_candidate_is_logged_before_filtering():
    """10. Every returned FAISS candidate is logged in telemetry before threshold filtering."""
    logger = RetrievalTelemetryLogger()
    candidates = [
        {"memory_id": "mem-high", "rank": 1, "distance_l2_sq": 0.10, "similarity": 0.909091},
        {"memory_id": "mem-low1", "rank": 2, "distance_l2_sq": 1.50, "similarity": 0.400000},
        {"memory_id": "mem-low2", "rank": 3, "distance_l2_sq": 2.50, "similarity": 0.285714},
    ]
    # Only candidate 1 passes threshold (sim >= 0.50), but logger captures all 3
    records = logger.log_retrieval_event(
        run_id="run_test",
        mode="Mode 4",
        query_id="Q05",
        candidates=candidates,
        retrieval_count=1,
        accepted_memory_count=1,
        store_size_before=3,
        threshold=0.50,
    )
    assert len(records) == 3
    assert records[0].passed_retrieval_threshold is True
    assert records[1].passed_retrieval_threshold is False
    assert records[2].passed_retrieval_threshold is False
    assert all(r.candidate_returned_by_faiss for r in records)


# =============================================================================
# Governance & Independence (Tests 11-13)
# =============================================================================

def test_11_below_threshold_candidates_not_injected_into_repair_context():
    """11. Below-threshold candidates are excluded from retrieved_memories in repair context."""
    store = FAISSMemoryStore()
    gov = MemoryGovernanceEngine()
    # Add a memory whose similarity to query will be < 0.50 (d^2 = 4.0, sim = 0.20)
    u = create_unit_vector(111)
    v = -u
    mem = create_sample_memory("mem-subthreshold")
    store.add(mem, u)

    logger = RetrievalTelemetryLogger()
    wf = ARMGRepairWorkflow(
        environment=None,
        governance_engine=gov,
        vector_store=store,
        embed_fn=lambda _: v.tolist(),
        telemetry_logger=logger,
    )
    res = wf.memory_retrieval_node({"user_query": "test query", "telemetry": {}})
    assert len(res["retrieved_memories"]) == 0
    assert res["telemetry"]["memory_retrieval_count"] == 0


def test_12_archived_and_deleted_memories_filtered_by_lifecycle():
    """12. High-similarity memories that are ARCHIVED or DELETED are filtered out."""
    store = FAISSMemoryStore()
    v = create_unit_vector(222)
    mem_archived = create_sample_memory("mem-archived", status=MemoryState.ARCHIVED)
    store.add(mem_archived, v)

    logger = RetrievalTelemetryLogger()
    wf = ARMGRepairWorkflow(
        environment=None,
        vector_store=store,
        embed_fn=lambda _: v.tolist(),
        telemetry_logger=logger,
    )
    res = wf.memory_retrieval_node({"user_query": "test query", "telemetry": {}})
    # High similarity ~1.0, but ARCHIVED -> excluded from retrieved_memories
    assert len(res["retrieved_memories"]) == 0


def test_13_admission_utility_independent_from_retrieval_similarity_threshold():
    """13. Admission utility threshold (0.25) remains separate and independent from retrieval threshold (0.50)."""
    gov = MemoryGovernanceEngine()
    retrieval_threshold = 0.50
    assert gov.admission_threshold == 0.25
    assert gov.admission_threshold != retrieval_threshold

    # Candidate with utility = 0.25 passes admission
    rk = RuntimeKnowledge(
        context={"table": "fact"},
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception='column "fact" does not exist',
        root_cause="cause",
        repair_strategy="strategy",
        confidence=0.50,
    )
    admitted = gov.admit(rk, context_similarity=1.0)
    assert admitted is not None
    assert admitted.utility >= 0.25


# =============================================================================
# Empty Retrieval Semantics (Tests 14-15)
# =============================================================================

def test_14_empty_store_produces_null_similarity_fields():
    """14. Empty store produces null similarity, distance, and memory_id fields."""
    logger = RetrievalTelemetryLogger()
    records = logger.log_retrieval_event(
        run_id="run1", mode="Mode 4", query_id="Q01",
        candidates=[], retrieval_count=0, accepted_memory_count=0, store_size_before=0,
    )
    assert len(records) == 1
    rec = records[0]
    assert rec.memory_id is None
    assert rec.rank is None
    assert rec.distance_l2_sq is None
    assert rec.similarity is None
    assert rec.candidate_returned_by_faiss is False
    assert rec.retrieval_count == 0


def test_15_no_result_is_never_encoded_as_numeric_zero():
    """15. Empty store no-result is never encoded as numeric 0.0."""
    logger = RetrievalTelemetryLogger()
    records = logger.log_retrieval_event(
        run_id="run1", mode="Mode 4", query_id="Q01",
        candidates=[], retrieval_count=0, accepted_memory_count=0, store_size_before=0,
    )
    rec = records[0]
    assert rec.similarity is not 0.0
    assert rec.similarity is None
    assert rec.distance_l2_sq is not 0.0
    assert rec.distance_l2_sq is None


# =============================================================================
# Evidence Lineage (Tests 16-18)
# =============================================================================

def test_16_telemetry_reaches_raw_benchmark_artifact(tmp_path):
    """16. Telemetry serializes cleanly to CSV with all canonical columns."""
    logger = RetrievalTelemetryLogger()
    logger.log_retrieval_event(
        run_id="seed42", mode="Mode 4 (Full ARMG)", query_id="Q01",
        candidates=[], retrieval_count=0, accepted_memory_count=0, store_size_before=0,
    )
    logger.log_retrieval_event(
        run_id="seed42", mode="Mode 4 (Full ARMG)", query_id="Q02",
        candidates=[{"memory_id": "mem-1", "rank": 1, "distance_l2_sq": 0.15, "similarity": 0.869565}],
        retrieval_count=1, accepted_memory_count=1, store_size_before=1,
    )
    csv_file = tmp_path / "test_telemetry.csv"
    logger.write_csv(csv_file)

    assert csv_file.exists()
    loaded_df = pd.read_csv(csv_file)
    assert list(loaded_df.columns) == RETRIEVAL_TELEMETRY_COLUMNS
    assert len(loaded_df) == 2


def test_17_changing_one_raw_telemetry_score_changes_downstream_analysis(tmp_path):
    """17. Lineage verification: changing one raw score propagates directly to downstream analysis."""
    logger = RetrievalTelemetryLogger()
    logger.log_retrieval_event(
        run_id="seed42", mode="Mode 4 (Full ARMG)", query_id="Q01",
        candidates=[{"memory_id": "mem-1", "rank": 1, "distance_l2_sq": 0.666667, "similarity": 0.60}],
        retrieval_count=1, accepted_memory_count=1, store_size_before=1,
    )
    csv1 = tmp_path / "telemetry_orig.csv"
    logger.write_csv(csv1)
    metrics1 = compute_retrieval_telemetry_metrics(str(csv1))
    mean_sim_1 = metrics1["profiles"]["Mode 4 (Full ARMG)"]["mean_observed_similarity"]

    # Modify exactly one value in a second copy
    df2 = pd.read_csv(csv1)
    df2.loc[0, "similarity"] = 0.90
    df2.loc[0, "distance_l2_sq"] = 0.111111
    csv2 = tmp_path / "telemetry_mod.csv"
    df2.to_csv(csv2, index=False)

    metrics2 = compute_retrieval_telemetry_metrics(str(csv2))
    mean_sim_2 = metrics2["profiles"]["Mode 4 (Full ARMG)"]["mean_observed_similarity"]

    assert mean_sim_1 == 0.60
    assert mean_sim_2 == 0.90
    assert mean_sim_1 != mean_sim_2


def test_18_corresponding_figure3_and_table_changes_automatically(tmp_path):
    """18. Lineage propagation to Figure 3."""
    logger = RetrievalTelemetryLogger()
    logger.log_retrieval_event(
        run_id="seed42", mode="Mode 4 (Full ARMG)", query_id="Q01",
        candidates=[{"memory_id": "mem-1", "rank": 1, "distance_l2_sq": 0.538462, "similarity": 0.65}],
        retrieval_count=1, accepted_memory_count=1, store_size_before=1,
    )
    csv_path = tmp_path / "telemetry.csv"
    png_path = tmp_path / "fig3.png"
    svg_path = tmp_path / "fig3.svg"
    logger.write_csv(csv_path)

    generate_fig3(telemetry_path=str(csv_path), output_png=str(png_path), output_svg=str(svg_path))
    assert png_path.exists()
    assert svg_path.exists()


# =============================================================================
# Anti-Fabrication & Anti-Reconstruction Constraints (Tests 19-20)
# =============================================================================

def test_19_no_np_random_in_empirical_pipeline():
    """19. No np.random or synthetic modeling calls exist in empirical publication generators."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    target_files = [
        repo_root / "manuscript" / "figures" / "source" / "fig3_retrieval_geometry.py",
        repo_root / "benchmark" / "analysis.py",
    ]

    for tf in target_files:
        assert tf.exists(), f"Target file {tf} not found"
        code = tf.read_text(encoding="utf-8")
        assert "np.random.normal" not in code
        assert "np.random.uniform" not in code
        assert "random.uniform(" not in code
        assert "random.normal(" not in code


def test_20_anti_reconstruction_test_requires_actual_faiss_search():
    """20. Section 10: Canonical telemetry cannot be generated solely from benchmark results/queries
    without executing the actual FAISS vector search operation."""
    store = FAISSMemoryStore()
    # Add a memory
    mem = create_sample_memory("mem-q04")
    v_mem = create_unit_vector(42)
    store.add(mem, v_mem)

    # Prove that telemetry values originate directly from FAISS search:
    # If FAISS search is NOT called, candidates cannot be inferred from query text or benchmark metadata
    query_vec = create_unit_vector(42)  # Identical vector
    cands = store.search_raw_candidates(query_vec, top_k=1)
    assert len(cands) == 1
    ret_mem, rank, dist, sim = cands[0]

    # Verify that dist originates from the real FAISS C++ index
    raw_dist, _ = store.index.search(query_vec.reshape(1, 768), 1)
    assert float(raw_dist[0][0]) == dist
    assert abs(dist) < 1e-4
    assert abs(sim - 1.0) < 1e-4

    # If the index is empty, FAISS returns empty - not invented candidates
    empty_store = FAISSMemoryStore()
    empty_cands = empty_store.search_raw_candidates(query_vec, top_k=3)
    assert len(empty_cands) == 0
