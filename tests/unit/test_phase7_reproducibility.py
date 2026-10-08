"""
ARMG Phase 7 - Reproducibility, Data Lineage & Statistical Analysis Unit Tests.

Hermetic test suite validating:
- Root vs seed partition exact equivalence
- Paired query-level joins on (seed, query_id)
- Exact aggregate vs query-level reconciliation
- Metric lineage matrix coverage
- Configuration provenance completeness
- Strict statistical unit of analysis segregation (Query-Level N=75 vs Seed-Level N=3)
- Canonical extra-retry detection (5 rows) and mutually exclusive reconciliation (sum = 75)
- Orthogonal boolean annotations (21 divergent, 5 extra retries, 2 overlap)
- Sandboxed perturbation propagation (retry-delta and cross-population isolation)
- Duplicate and missing data detection
- FAISS telemetry lineage consistency
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.analyze_reproducibility import (
    classify_paired_outcome_hierarchical,
    compute_comprehensive_descriptive_stats,
)

ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_DIR = ROOT / "benchmark"
ROOT_CSV = BENCHMARK_DIR / "benchmark_results.csv"
TELEMETRY_CSV = BENCHMARK_DIR / "retrieval_telemetry.csv"
QUERY_LEVEL_CSV = BENCHMARK_DIR / "query_level_mode2_vs_mode4.csv"
LINEAGE_JSON = BENCHMARK_DIR / "metric_lineage.json"
PROVENANCE_JSON = BENCHMARK_DIR / "configuration_provenance.json"


def test_root_seed_exact_equivalence():
    """Verify benchmark_results.csv exactly equals concat(seed42, seed123, seed999)."""
    assert ROOT_CSV.exists(), f"Missing {ROOT_CSV}"
    df_root = pd.read_csv(ROOT_CSV)
    
    seeds = [42, 123, 999]
    seed_dfs = []
    for s in seeds:
        seed_path = BENCHMARK_DIR / f"seed{s}" / "benchmark_results.csv"
        assert seed_path.exists(), f"Missing {seed_path}"
        df_s = pd.read_csv(seed_path)
        assert len(df_s) == 150, f"Expected 150 rows in seed {s}, got {len(df_s)}"
        seed_dfs.append(df_s)
        
    df_concat = pd.concat(seed_dfs, ignore_index=True)
    assert len(df_root) == len(df_concat) == 450
    assert list(df_root.columns) == list(df_concat.columns)
    pd.testing.assert_frame_equal(df_root, df_concat, check_exact=True)


def test_paired_query_level_join_integrity():
    """Verify query_level_mode2_vs_mode4.csv has correct join structure and size."""
    assert QUERY_LEVEL_CSV.exists(), f"Missing {QUERY_LEVEL_CSV}"
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    # 25 queries * 3 seeds = 75 paired rows
    assert len(df_ql) == 75, f"Expected 75 rows, got {len(df_ql)}"
    
    # Check no duplicate (seed, query_id)
    duplicates = df_ql.duplicated(subset=["seed", "query_id"]).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate (seed, query_id) pairs"
    
    # Check all seeds and query IDs are present
    seeds = set(df_ql["seed"].unique())
    assert seeds == {42, 123, 999}
    
    expected_queries = {f"Q{i:02d}" for i in range(1, 26)}
    for s in [42, 123, 999]:
        seed_queries = set(df_ql[df_ql["seed"] == s]["query_id"])
        assert seed_queries == expected_queries, f"Missing queries in seed {s}: {expected_queries - seed_queries}"


def test_query_level_aggregate_reconciliation():
    """Verify query-level metrics sum/average to exact reported aggregate metrics."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    # Mode 2: 72/75 success, 51/75 accuracy
    m2_succ_count = df_ql["mode2_success"].sum()
    m2_acc_count = df_ql["mode2_accuracy"].sum()
    assert m2_succ_count == 72
    assert m2_acc_count == 51
    assert np.isclose(m2_succ_count / 75, 0.9600)
    assert np.isclose(m2_acc_count / 75, 0.6800)
    
    # Mode 4: 72/75 success, 51/75 accuracy
    m4_succ_count = df_ql["mode4_success"].sum()
    m4_acc_count = df_ql["mode4_accuracy"].sum()
    assert m4_succ_count == 72
    assert m4_acc_count == 51
    assert np.isclose(m4_succ_count / 75, 0.9600)
    assert np.isclose(m4_acc_count / 75, 0.6800)
    
    # Check Mode 2 vs Mode 4 means across all 75 queries
    assert np.isclose(df_ql["mode2_retries"].mean(), 21 / 75)  # 0.28
    assert np.isclose(df_ql["mode4_retries"].mean(), 28 / 75)  # 0.3733...
    assert np.isclose(df_ql["mode2_tokens"].mean(), 503.72, atol=1e-2)
    assert np.isclose(df_ql["mode4_tokens"].mean(), 602.8533, atol=1e-2)
    assert np.isclose(df_ql["mode2_latency_ms"].mean(), 6441.56, atol=1e-1)
    assert np.isclose(df_ql["mode4_latency_ms"].mean(), 9000.59, atol=1e-1)


def test_paired_differences_definition_and_sign_convention():
    """Verify delta calculations follow Mode4 - Mode2 convention strictly."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    for _, row in df_ql.iterrows():
        # Delta definition: Mode4 - Mode2
        assert row["delta_success"] == int(row["mode4_success"]) - int(row["mode2_success"])
        assert row["delta_accuracy"] == int(row["mode4_accuracy"]) - int(row["mode2_accuracy"])
        assert row["delta_retries"] == int(row["mode4_retries"]) - int(row["mode2_retries"])
        assert np.isclose(row["delta_tokens"], row["mode4_tokens"] - row["mode2_tokens"], atol=1e-2)
        assert np.isclose(row["delta_latency_ms"], row["mode4_latency_ms"] - row["mode2_latency_ms"], atol=0.05)


def test_failure_query_and_semantic_divergence_consistency():
    """Verify Q11 fails across all seeds and Q05, Q14, Q15, Q17, Q18, Q19, Q25 diverge."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    # Q11 execution failure
    q11 = df_ql[df_ql["query_id"] == "Q11"]
    assert len(q11) == 3
    assert (q11["mode2_success"] == False).all()
    assert (q11["mode4_success"] == False).all()
    
    # Semantic divergence: success=True, accuracy=0
    # Exactly 7 queries across all 3 seeds: Q05, Q14, Q15, Q17, Q18, Q19, Q25 (21 total rows)
    divergent_queries = {"Q05", "Q14", "Q15", "Q17", "Q18", "Q19", "Q25"}
    for qid in divergent_queries:
        rows = df_ql[df_ql["query_id"] == qid]
        assert len(rows) == 3
        assert (rows["mode4_success"] == True).all()
        assert (rows["mode4_accuracy"] == False).all()
        assert (rows["mode2_success"] == True).all()
        assert (rows["mode2_accuracy"] == False).all()


def test_extra_retry_canonical_derivation_and_identities():
    """Verify exactly 5 rows have positive retry-deltas derived from canonical CSV."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    pos_retries = df_ql[df_ql["delta_retries"] > 0]
    
    # Exactly 5 rows
    assert len(pos_retries) == 5
    
    # Exact identities
    q08_cases = pos_retries[pos_retries["query_id"] == "Q08"]
    assert len(q08_cases) == 3
    assert set(q08_cases["seed"]) == {42, 123, 999}
    assert (q08_cases["delta_retries"] == 1).all()
    
    q19_cases = pos_retries[pos_retries["query_id"] == "Q19"]
    assert len(q19_cases) == 2
    assert set(q19_cases["seed"]) == {123, 999}
    assert (q19_cases["delta_retries"] == 2).all()
    
    # Remaining 70 rows are zero delta, 0 rows negative
    assert (df_ql["delta_retries"] == 0).sum() == 70
    assert (df_ql["delta_retries"] < 0).sum() == 0


def test_classification_mutually_exclusive_reconciliation():
    """Verify mutually exclusive classification counts sum exactly to 75 rows (100%)."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    vc = df_ql["outcome_classification"].value_counts()
    
    assert vc.sum() == 75
    expected_distribution = {
        "Outcome & Token Parity": 42,
        "Semantic Divergence": 19,
        "Parity with Token Overhead": 6,
        "Mode 4 Extra Retries": 5,
        "Execution Failure": 3,
    }
    for cat, expected_count in expected_distribution.items():
        assert vc.get(cat, 0) == expected_count, f"Mismatch in category {cat}: {vc.get(cat, 0)} != {expected_count}"


def test_outcome_token_parity_does_not_imply_identical_latency():
    """Regression test: verify rows classified as 'Outcome & Token Parity' have identical
    success, accuracy, retries, tokens <= 0, but can have non-zero (different) latency.
    Proves that latency is treated orthogonally and not required to be identical.
    Also validates that the total mutually exclusive classification count remains exactly 75/75.
    """
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    # Check total mutually exclusive classifications count
    vc = df_ql["outcome_classification"].value_counts()
    assert vc.sum() == 75, f"Expected 75 total classifications, got {vc.sum()}"
    
    parity_rows = df_ql[df_ql["outcome_classification"] == "Outcome & Token Parity"]
    assert len(parity_rows) == 42
    
    # 1. Verify underlying outcome and token predicates hold for all parity rows:
    assert (parity_rows["mode2_success"] == parity_rows["mode4_success"]).all()
    assert (parity_rows["mode2_accuracy"] == parity_rows["mode4_accuracy"]).all()
    assert (parity_rows["delta_retries"] == 0).all()
    assert (parity_rows["delta_tokens"] <= 0).all()
    
    # 2. Verify latency is NOT identical (different latency) across these parity rows
    # Mode 4 incurs memory retrieval / governance runtime overhead
    assert (parity_rows["delta_latency_ms"] != 0).any()
    # In fact, mode 4 latency overhead is positive for the vast majority:
    assert (parity_rows["delta_latency_ms"] > 0).sum() > 0
    
    # 3. Direct function test with synthetic row having different latency
    synth_label = classify_paired_outcome_hierarchical(
        s_m2=True,
        s_m4=True,
        a_m2=True,
        a_m4=True,
        delta_ret=0,
        delta_tok=0.0,
        delta_lat=2150.5,  # strictly non-zero latency delta
        is_divergent=False,
    )
    assert synth_label == "Outcome & Token Parity"
    assert synth_label != "Strict Identical"


def test_orthogonal_boolean_annotations_consistency():
    """Verify independent overlapping annotations match underlying data."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    assert df_ql["is_execution_failure"].sum() == 3
    assert df_ql["has_positive_retry_delta"].sum() == 5
    assert df_ql["divergent_semantic_query"].sum() == 21
    assert df_ql["has_token_overhead"].sum() == 20
    assert df_ql["overlap_divergent_and_extra_retries"].sum() == 2
    
    # Mathematical reconciliation:
    # 21 divergent = 19 (classified as Semantic Divergence) + 2 (classified as Extra Retries)
    mut_divergent = (df_ql["outcome_classification"] == "Semantic Divergence").sum()
    overlap = df_ql["overlap_divergent_and_extra_retries"].sum()
    assert mut_divergent + overlap == df_ql["divergent_semantic_query"].sum() == 21


def test_statistical_populations_strict_segregation():
    """Verify query-level (N=75) and seed-level (N=3) statistics are strictly segregated."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    df_root = pd.read_csv(ROOT_CSV)
    
    stats = compute_comprehensive_descriptive_stats(df_ql, df_root)
    assert "query_level_population" in stats
    assert "seed_level_population" in stats
    
    ql = stats["query_level_population"]
    sl = stats["seed_level_population"]
    
    # Population sizes
    assert ql["sample_size_evaluations"] == 75
    assert sl["sample_size_seeds"] == 3
    
    # Mode 4 Latency dispersion comparison:
    # Query-level std across 75 evaluations is high (~4954 ms)
    # Seed-level std across 3 run averages is ~184.33 ms
    ql_m4_lat_std = ql["Mode 4 (Full ARMG)"]["latency_ms"]["std_sample_ddof1"]
    sl_m4_lat_std = sl["Mode 4 (Full ARMG)"]["latency_ms"]["std_sample_ddof1"]
    assert np.isclose(ql_m4_lat_std, 4954.47, atol=1e-1)
    assert np.isclose(sl_m4_lat_std, 184.33, atol=1e-1)
    
    # Retry dispersion comparison:
    ql_m4_ret_std = ql["Mode 4 (Full ARMG)"]["retries"]["std_sample_ddof1"]
    sl_m4_ret_std = sl["Mode 4 (Full ARMG)"]["retries"]["std_sample_ddof1"]
    assert np.isclose(ql_m4_ret_std, 0.7310, atol=1e-2)
    assert np.isclose(sl_m4_ret_std, 0.0462, atol=1e-2)


def test_perturbation_retry_classification_dynamic_propagation():
    """Perturbation test 1: Modify in-memory retry value and verify automatic propagation."""
    df_ql = pd.read_csv(QUERY_LEVEL_CSV).copy()
    
    # Original Extra Retries count is 5
    init_extra_count = (df_ql["delta_retries"] > 0).sum()
    assert init_extra_count == 5
    
    # Modify Q01 Seed 42: set mode4_retries to 1 (mode2 is 0)
    target_idx = df_ql[(df_ql["seed"] == 42) & (df_ql["query_id"] == "Q01")].index[0]
    df_ql.at[target_idx, "mode4_retries"] = 1
    df_ql.at[target_idx, "delta_retries"] = 1
    
    # Reclassify using canonical function
    row = df_ql.loc[target_idx]
    new_class = classify_paired_outcome_hierarchical(
        s_m2=bool(row["mode2_success"]),
        s_m4=bool(row["mode4_success"]),
        a_m2=bool(row["mode2_accuracy"]),
        a_m4=bool(row["mode4_accuracy"]),
        delta_ret=int(row["delta_retries"]),
        delta_tok=float(row["delta_tokens"]),
        delta_lat=float(row["delta_latency_ms"]),
        is_divergent=bool(row["divergent_semantic_query"]),
    )
    df_ql.at[target_idx, "outcome_classification"] = new_class
    
    # Verification: Extra retries count increases to 6 automatically
    assert (df_ql["delta_retries"] > 0).sum() == 6
    assert (df_ql["outcome_classification"] == "Mode 4 Extra Retries").sum() == 6
    assert (df_ql["outcome_classification"] == "Outcome & Token Parity").sum() == 41
    
    # Verify disk files remain untouched
    disk_df = pd.read_csv(QUERY_LEVEL_CSV)
    assert (disk_df["delta_retries"] > 0).sum() == 5
    assert (disk_df["outcome_classification"] == "Mode 4 Extra Retries").sum() == 5
    assert (disk_df["outcome_classification"] == "Outcome & Token Parity").sum() == 42


def test_perturbation_query_level_vs_seed_level_segregation():
    """Perturbation test 2: Modify query metric in-memory; verify no cross-population contamination."""
    df_root = pd.read_csv(ROOT_CSV).copy()
    
    # Find Seed 42 Mode 4 Q01
    idx = df_root[
        (df_root["seed"] == 42) &
        (df_root["mode"] == "Mode 4 (Full ARMG)") &
        (df_root["query_id"] == "Q01")
    ].index[0]
    
    orig_tokens = df_root.at[idx, "total_tokens"]
    df_root.at[idx, "total_tokens"] = orig_tokens + 1000.0
    
    # Compute seed-level aggregate means
    sub = df_root[df_root["mode"] == "Mode 4 (Full ARMG)"]
    seed_means = sub.groupby("seed")["total_tokens"].mean().to_dict()
    
    # Seed 42 mean increases by exactly 1000 / 25 = 40.0 tokens
    # Seed 123 and Seed 999 remain identical to baseline
    assert np.isclose(seed_means[42], 569.96 + 40.0, atol=1e-2)
    assert np.isclose(seed_means[123], 619.36, atol=1e-2)
    assert np.isclose(seed_means[999], 619.24, atol=1e-2)
    
    # Confirm disk file is 100% untouched
    disk_root = pd.read_csv(ROOT_CSV)
    assert disk_root.at[idx, "total_tokens"] == orig_tokens


def test_metric_lineage_matrix_structure():
    """Verify metric_lineage.json contains complete valid lineage definitions."""
    assert LINEAGE_JSON.exists(), f"Missing {LINEAGE_JSON}"
    with open(LINEAGE_JSON, "r", encoding="utf-8") as f:
        lineage = json.load(f)
        
    assert "metrics" in lineage
    metrics_list = lineage["metrics"]
    assert len(metrics_list) >= 8
    
    metric_names = [m["metric_name"] for m in metrics_list]
    expected_substrings = [
        "ExecSucc",
        "ExecAcc",
        "Retry",
        "Tokens",
        "Latency",
        "Memory Store Size",
        "FAISS Retrieval",
        "Divergent",
    ]
    for sub in expected_substrings:
        assert any(sub in name for name in metric_names), f"Missing metric containing '{sub}'"
        
    for m in metrics_list:
        assert "raw_source" in m
        assert "analysis_function" in m
        assert "transformation_formula" in m
        assert "primary_outputs" in m


def test_configuration_provenance_completeness():
    """Verify configuration_provenance.json has all required parameters."""
    assert PROVENANCE_JSON.exists(), f"Missing {PROVENANCE_JSON}"
    with open(PROVENANCE_JSON, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    assert config["metadata"]["git_commit"] == "40d36a3980e5f152a8eadbfa021b833f587d7b3b"
    assert "3.13" in config["system_environment"]["python_version"] or "3.10" in config["system_environment"]["python_version"]
    assert "PostgreSQL 18.1" in config["database_engine"]["version"]
    assert config["neural_inference_stack"]["generation_model"] == "qwen2.5:7b-instruct"
    assert config["neural_inference_stack"]["embedding_model"] == "nomic-embed-text"
    assert config["neural_inference_stack"]["generation_temperature"] == 0.0
    assert config["neural_inference_stack"]["embedding_dimension"] == 768
    
    gov = config["armg_governance_configuration"]
    assert gov["admission_threshold_theta"] == 0.25
    assert gov["retrieval_similarity_threshold_tau"] == 0.50
    assert gov["max_repair_retries"] == 3
    assert gov["temporal_decay_rate_lambda"] == 0.05
    
    exp = config["experimental_design"]
    assert exp["benchmark_seeds"] == [42, 123, 999]
    assert exp["unique_queries_count"] == 25
    assert exp["total_evaluations"] == 450


def test_faiss_telemetry_lineage():
    """Verify retrieval telemetry line count, candidates, and threshold filtering."""
    assert TELEMETRY_CSV.exists(), f"Missing {TELEMETRY_CSV}"
    df_tel = pd.read_csv(TELEMETRY_CSV)
    
    # Total rows: 141 (47 per seed)
    assert len(df_tel) == 141
    for s in [42, 123, 999]:
        seed_subset = df_tel[df_tel["run_id"].str.contains(f"seed{s}")]
        assert len(seed_subset) == 47
        # 16 candidate rows per seed meet similarity threshold >= 0.50
        assert len(seed_subset[seed_subset["similarity"] >= 0.50]) == 16
        
    # Candidates with valid distance/similarity
    valid_cands = df_tel.dropna(subset=["distance_l2_sq", "similarity"])
    assert len(valid_cands) == 129
    
    # Across all 3 seeds: 16 * 3 = 48 candidates meet similarity >= 0.50
    retrievals = valid_cands[valid_cands["similarity"] >= 0.50]
    assert len(retrievals) == 48


def test_examiner_summary_query_level_and_pair_level_consistency():
    """Verify examiner-summary query-level and pair-level counts derived directly from canonical CSV.
    
    Verifies:
    - Outcome & Token Parity distinct query count = 14
    - Semantic Divergence distinct query count = 7
    - Execution Failure distinct query count = 1
    - Positive retry-delta distinct query count = 2
    - Positive retry-delta pair count = 5
    - Overlap of semantic divergence and positive retry delta = 2 pairs
    """
    assert QUERY_LEVEL_CSV.exists(), f"Missing {QUERY_LEVEL_CSV}"
    df_ql = pd.read_csv(QUERY_LEVEL_CSV)
    
    # 1. Distinct queries under Outcome & Token Parity (hierarchical classification)
    parity_pairs = df_ql[df_ql["outcome_classification"] == "Outcome & Token Parity"]
    parity_queries = parity_pairs["query_id"].unique()
    assert len(parity_queries) == 14
    # All 14 queries appear across all 3 seeds (14 * 3 = 42 pairs)
    assert len(parity_pairs) == 42
    
    # 2. Distinct queries under Semantic Divergence (success=True, accuracy=False)
    divergent_pairs = df_ql[df_ql["divergent_semantic_query"] == True]
    divergent_queries = divergent_pairs["query_id"].unique()
    assert len(divergent_queries) == 7
    # Across all 3 seeds: 7 * 3 = 21 pairs
    assert len(divergent_pairs) == 21
    
    # 3. Distinct queries under Execution Failure (success=False in both modes)
    exec_fail_pairs = df_ql[df_ql["is_execution_failure"] == True]
    exec_fail_queries = exec_fail_pairs["query_id"].unique()
    assert len(exec_fail_queries) == 1
    assert exec_fail_queries[0] == "Q11"
    # Across all 3 seeds: 1 * 3 = 3 pairs
    assert len(exec_fail_pairs) == 3
    
    # 4. Positive retry-delta queries and pairs
    pos_retry_pairs = df_ql[df_ql["has_positive_retry_delta"] == True]
    pos_retry_queries = set(pos_retry_pairs["query_id"].unique())
    assert len(pos_retry_queries) == 2
    assert pos_retry_queries == {"Q08", "Q19"}
    # Pair count: Q08 has 3 pairs (seeds 42, 123, 999) + Q19 has 2 pairs (seeds 123, 999) = 5 pairs
    assert len(pos_retry_pairs) == 5
    
    # 5. Overlap between Semantic Divergence and Positive Retry Delta:
    # Q19 in seeds 123 and 999 is simultaneously divergent and has positive retry delta
    overlap_pairs = df_ql[
        (df_ql["divergent_semantic_query"] == True) & (df_ql["has_positive_retry_delta"] == True)
    ]
    assert len(overlap_pairs) == 2
    assert set(overlap_pairs["query_id"]) == {"Q19"}
    assert set(overlap_pairs["seed"]) == {123, 999}

