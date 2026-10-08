"""
Hermetic Unit Tests for Phase 5 Master Canonical Results Pipeline.
Section 20 & Section 12 Mandatory Verification Suite.

Tests:
1. Valid Input Validation
2. Missing Column Detection
3. Duplicate (Seed, Mode, Query) Combination Detection
4. Missing Query Detection
5. Empty Dataset Detection
6. Invalid Mode Detection
7. Invalid Seed Detection
8. Telemetry Schema Problem Detection
9. Deterministic Pipeline Execution (Hermetic reproducibility)
10. Controlled Source-Perturbation Propagation & Restoration (Section 12)
"""
import copy
import json
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import pytest

from scripts.generate_results import (
    validate_authoritative_inputs,
    compute_all_results_metrics,
    generate_summary_artifacts,
    generate_publication_tables,
    generate_publication_figures,
    generate_results_manifest,
    generate_all_results,
    REPO_ROOT,
    SEEDS,
    MODE_ORDER,
)


@pytest.fixture
def auth_inputs():
    """Paths to authoritative Phase 4 inputs."""
    return {
        "root_csv": REPO_ROOT / "benchmark/benchmark_results.csv",
        "telem_csv": REPO_ROOT / "benchmark/retrieval_telemetry.csv",
        "seed_csvs": [REPO_ROOT / f"benchmark/seed{s}/benchmark_results.csv" for s in SEEDS],
    }


def test_valid_input_validation(auth_inputs):
    """Test that authoritative Phase 4 inputs pass all strict schema invariants."""
    val_info = validate_authoritative_inputs(
        root_benchmark_csv=auth_inputs["root_csv"],
        telemetry_csv=auth_inputs["telem_csv"],
        seed_csv_paths=[str(p) for p in auth_inputs["seed_csvs"]],
    )
    assert val_info["status"] == "VALID"
    assert val_info["total_evaluations"] == 450
    assert val_info["seeds"] == [42, 123, 999]
    assert len(val_info["modes"]) == 6
    assert val_info["telemetry_rows"] == 141
    assert val_info["telemetry_candidates"] == 129


def test_missing_column_raises(auth_inputs, tmp_path):
    """Test that missing required columns in benchmark CSV raises ValueError."""
    bad_csv = tmp_path / "bad_bench.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    df = df.drop(columns=["latency_ms"])
    df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_duplicate_query_raises(auth_inputs, tmp_path):
    """Test that duplicate (seed, mode, query_id) combinations raise ValueError."""
    bad_csv = tmp_path / "dup_bench.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    # Duplicate first row
    dup_df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    dup_df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="rows; expected exactly 450"):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_duplicate_combination_within_450_raises(auth_inputs, tmp_path):
    """Test that duplicate combination within 450 rows is detected."""
    bad_csv = tmp_path / "dup_within_450.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    # Replace row 1 with row 0's combination
    df.loc[1, "query_id"] = df.loc[0, "query_id"]
    df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="Duplicate"):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_missing_query_raises(auth_inputs, tmp_path):
    """Test that missing a required query in a mode raises ValueError."""
    bad_csv = tmp_path / "missing_query.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    # Replace Q25 with Q01 in one row, keeping count 450
    mask = (df["seed"] == 42) & (df["mode"].str.startswith("Mode 1")) & (df["query_id"] == "Q25")
    df.loc[mask, "query_id"] = "Q01"
    df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_empty_dataset_raises(auth_inputs, tmp_path):
    """Test that empty benchmark CSV raises ValueError."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("run_id,mode,seed\n", encoding="utf-8")

    with pytest.raises(ValueError):
        validate_authoritative_inputs(
            root_benchmark_csv=empty_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_invalid_mode_raises(auth_inputs, tmp_path):
    """Test that unexpected mode names raise ValueError."""
    bad_csv = tmp_path / "bad_mode.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    df.loc[df["mode"].str.startswith("Mode 1"), "mode"] = "Mode 99 (Invalid Mode)"
    df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="Missing expected mode"):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_invalid_seed_raises(auth_inputs, tmp_path):
    """Test that unexpected seeds raise ValueError."""
    bad_csv = tmp_path / "bad_seed.csv"
    df = pd.read_csv(auth_inputs["root_csv"])
    df.loc[df["seed"] == 42, "seed"] = 777
    df.to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="Expected seeds"):
        validate_authoritative_inputs(
            root_benchmark_csv=bad_csv,
            telemetry_csv=auth_inputs["telem_csv"],
        )


def test_telemetry_schema_problem_raises(auth_inputs, tmp_path):
    """Test that missing required telemetry columns raise ValueError."""
    bad_telem = tmp_path / "bad_telem.csv"
    df = pd.read_csv(auth_inputs["telem_csv"])
    df = df.drop(columns=["similarity"])
    df.to_csv(bad_telem, index=False)

    with pytest.raises(ValueError, match="Telemetry missing required columns"):
        validate_authoritative_inputs(
            root_benchmark_csv=auth_inputs["root_csv"],
            telemetry_csv=bad_telem,
        )


def test_deterministic_output(auth_inputs):
    """Test that pipeline execution is 100% deterministic given identical inputs."""
    r1 = compute_all_results_metrics(
        seed_csv_paths=[str(p) for p in auth_inputs["seed_csvs"]],
        telemetry_path=str(auth_inputs["telem_csv"]),
    )
    r2 = compute_all_results_metrics(
        seed_csv_paths=[str(p) for p in auth_inputs["seed_csvs"]],
        telemetry_path=str(auth_inputs["telem_csv"]),
    )

    pd.testing.assert_frame_equal(r1["metrics_df"], r2["metrics_df"])
    assert r1["tradeoff"] == r2["tradeoff"]
    assert json.dumps(r1["stats_dict"], sort_keys=True) == json.dumps(r2["stats_dict"], sort_keys=True)


def test_source_perturbation_propagation(auth_inputs, tmp_path):
    """
    Section 12 Mandatory Verification: Controlled Source-Perturbation Test.
    1. Copy authoritative benchmark data into a temporary sandbox.
    2. Change exactly one controlled source value in the sandbox:
       Perturb Mode 1 Query Q01 in seed 42 from success=True, acc=True to success=False, acc=False.
    3. Run canonical results generator targeting the sandbox.
    4. Verify that downstream metrics, tables, and summaries change accordingly.
    5. Restore original data.
    6. Regenerate from unperturbed evidence.
    7. Verify outputs return to authoritative values.
    """
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    summary_dir = sandbox_dir / "summaries"
    table_dir = sandbox_dir / "tables"
    fig_dir = sandbox_dir / "figures"
    manifest_file = sandbox_dir / "results_manifest.json"

    # Step 1: Copy authoritative CSVs to sandbox
    seed_files = []
    for s in SEEDS:
        s_dir = sandbox_dir / f"seed{s}"
        s_dir.mkdir()
        dst = s_dir / "benchmark_results.csv"
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], dst)
        seed_files.append(dst)

    root_dst = sandbox_dir / "benchmark_results.csv"
    shutil.copy(auth_inputs["root_csv"], root_dst)
    telem_dst = sandbox_dir / "retrieval_telemetry.csv"
    shutil.copy(auth_inputs["telem_csv"], telem_dst)

    # Check baseline unperturbed Mode 1 metrics
    base_res = compute_all_results_metrics(
        seed_csv_paths=[str(p) for p in seed_files],
        telemetry_path=str(telem_dst),
    )
    m1_base = base_res["metrics_df"][base_res["metrics_df"]["mode"].str.startswith("Mode 1")].iloc[0]
    assert m1_base["exec_succ"] == 80.00
    assert m1_base["exec_acc"] == 60.00

    # Step 2: Perturb exactly ONE row (seed 42, Mode 1, Q01)
    df42 = pd.read_csv(seed_files[0])
    target_idx = df42[(df42["mode"].str.startswith("Mode 1")) & (df42["query_id"] == "Q01")].index[0]
    assert df42.loc[target_idx, "success"] == True
    assert df42.loc[target_idx, "execution_accuracy"] == 1

    # Deliberate reversible change: flip success to False and acc to 0
    df42.loc[target_idx, "success"] = False
    df42.loc[target_idx, "execution_accuracy"] = 0
    df42.to_csv(seed_files[0], index=False)

    # Reassemble root CSV in sandbox
    dfs_perturbed = [pd.read_csv(p) for p in seed_files]
    root_perturbed = pd.concat(dfs_perturbed, ignore_index=True)
    root_perturbed.to_csv(root_dst, index=False)

    # Step 3: Run canonical results generator on perturbed sandbox
    pert_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )

    # Step 4: Verify downstream changes propagate mathematically
    # Mode 1 had 60 successes out of 75 evals (80.00%). Now it has 59 out of 75 (78.67%).
    # Acc was 45/75 (60.00%). Now it is 44/75 (58.67%).
    m1_pert = pert_res["metrics"]["metrics_df"][pert_res["metrics"]["metrics_df"]["mode"].str.startswith("Mode 1")].iloc[0]
    assert round(m1_pert["exec_succ"], 2) == 78.67
    assert round(m1_pert["exec_acc"], 2) == 58.67

    # Verify summary JSON changed
    with open(summary_dir / "statistical_summary.json", "r") as f:
        sum_json = json.load(f)
    m1_stat = sum_json["Mode 1 (Zero-Shot)"]
    assert m1_stat["execution_success"]["numerator"] == 59
    assert m1_stat["relational_accuracy"]["numerator"] == 44

    # Verify table changed
    with open(table_dir / "table_fig4_validation.tex", "r") as f:
        t_b_content = f.read()
    assert "59 / 75" in t_b_content
    assert "44 / 75" in t_b_content
    assert "78.67" in t_b_content

    # Step 5: Restore original authoritative data in sandbox
    shutil.copy(auth_inputs["seed_csvs"][0], seed_files[0])
    shutil.copy(auth_inputs["root_csv"], root_dst)

    # Step 6: Regenerate from restored evidence
    restored_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )

    # Step 7: Verify outputs return to authoritative values
    m1_restored = restored_res["metrics"]["metrics_df"][restored_res["metrics"]["metrics_df"]["mode"].str.startswith("Mode 1")].iloc[0]
    assert m1_restored["exec_succ"] == 80.00
    assert m1_restored["exec_acc"] == 60.00

    with open(summary_dir / "statistical_summary.json", "r") as f:
        sum_restored = json.load(f)
    assert sum_restored["Mode 1 (Zero-Shot)"]["execution_success"]["numerator"] == 60
    assert sum_restored["Mode 1 (Zero-Shot)"]["relational_accuracy"]["numerator"] == 45

    with open(table_dir / "table_fig4_validation.tex", "r") as f:
        t_b_restored = f.read()
    assert "60 / 75" in t_b_restored
    assert "45 / 75" in t_b_restored
    assert "80.00" in t_b_restored


def test_perturbation_fig3_telemetry(auth_inputs, tmp_path):
    """
    Focused perturbation test for Figure 3 and Table A (Retrieval Telemetry).
    1. Copy inputs to isolated sandbox.
    2. Perturb Q05 telemetry in seed 42 to similarity=0.8500 (passing threshold 0.50).
    3. Generate all results in sandbox.
    4. Verify Figure 3 and Table A reflect the delta ($17$ retrieval events, $13$ distinct queries, Q05 Yes (1)).
    5. Restore original telemetry.
    6. Regenerate and verify exact baseline restoration ($16$ events, $12$ distinct queries, Q05 No (0)).
    """
    sandbox_dir = tmp_path / "sandbox_fig3"
    sandbox_dir.mkdir()
    summary_dir = sandbox_dir / "summaries"
    table_dir = sandbox_dir / "tables"
    fig_dir = sandbox_dir / "figures"
    manifest_file = sandbox_dir / "results_manifest.json"

    seed_files = []
    for s in SEEDS:
        s_dir = sandbox_dir / f"seed{s}"
        s_dir.mkdir()
        dst = s_dir / "benchmark_results.csv"
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], dst)
        seed_files.append(dst)

    root_dst = sandbox_dir / "benchmark_results.csv"
    shutil.copy(auth_inputs["root_csv"], root_dst)
    telem_dst = sandbox_dir / "retrieval_telemetry.csv"
    shutil.copy(auth_inputs["telem_csv"], telem_dst)

    # Baseline verification
    base_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig3_validation.tex", "r") as f:
        t_a_base = f.read()
    assert "$16$ retrieval events" in t_a_base
    assert "$12$ of 25 ($48.0\\%$)" in t_a_base
    assert "Q05 & 0.0035 & 0.4917 & No (0) & No (0)" in t_a_base

    # Perturb: Modify Q05 telemetry in seed 42
    telem_df = pd.read_csv(telem_dst)
    mask = (telem_df["run_id"].str.contains("seed42")) & (telem_df["query_id"] == "Q05")
    q05_idx = telem_df[mask].index[0]
    telem_df.loc[q05_idx, "similarity"] = 0.8500
    telem_df.loc[q05_idx, "distance_l2_sq"] = 1.0 / 0.8500 - 1.0
    telem_df.loc[q05_idx, "passed_retrieval_threshold"] = True
    telem_df.loc[q05_idx, "retrieval_count"] = 1
    telem_df.loc[q05_idx, "accepted_memory_count"] = 1
    telem_df.to_csv(telem_dst, index=False)

    # Regenerate perturbed
    pert_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig3_validation.tex", "r") as f:
        t_a_pert = f.read()
    assert "$17$ retrieval events" in t_a_pert
    assert "$13$ of 25 ($52.0\\%$)" in t_a_pert
    assert "Q05 & 0.0035 & 0.8500 & No (0) & Yes (1)" in t_a_pert

    # Restore
    shutil.copy(auth_inputs["telem_csv"], telem_dst)
    rest_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig3_validation.tex", "r") as f:
        t_a_rest = f.read()
    assert "$16$ retrieval events" in t_a_rest
    assert "$12$ of 25 ($48.0\\%$)" in t_a_rest
    assert "Q05 & 0.0035 & 0.4917 & No (0) & No (0)" in t_a_rest


def test_perturbation_fig5_tradeoff(auth_inputs, tmp_path):
    """
    Focused perturbation test for Figure 5 and Table C / Table VIII (Trade-Off Profile).
    1. Copy inputs to isolated sandbox.
    2. Perturb Mode 4 Query Q01 in seed 42 retry_count from 0 to 3.
    3. Generate all results in sandbox.
    4. Verify Mode 4 retries increases (from 0.37 to 0.41) and trade-off delta changes (+33.33% to +47.62%).
    5. Restore original benchmark CSV.
    6. Regenerate and verify exact baseline restoration (retries returns to 0.37, delta to +33.33%).
    """
    sandbox_dir = tmp_path / "sandbox_fig5"
    sandbox_dir.mkdir()
    summary_dir = sandbox_dir / "summaries"
    table_dir = sandbox_dir / "tables"
    fig_dir = sandbox_dir / "figures"
    manifest_file = sandbox_dir / "results_manifest.json"

    seed_files = []
    for s in SEEDS:
        s_dir = sandbox_dir / f"seed{s}"
        s_dir.mkdir()
        dst = s_dir / "benchmark_results.csv"
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], dst)
        seed_files.append(dst)

    root_dst = sandbox_dir / "benchmark_results.csv"
    shutil.copy(auth_inputs["root_csv"], root_dst)
    telem_dst = sandbox_dir / "retrieval_telemetry.csv"
    shutil.copy(auth_inputs["telem_csv"], telem_dst)

    # Baseline check
    base_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig5_validation.tex", "r") as f:
        t_c_base = f.read()
    assert "0.37" in t_c_base
    assert "+33.33\\%" in t_c_base

    # Perturb seed 42 Mode 4 Q01 retries from 0 to 3
    df42 = pd.read_csv(seed_files[0])
    target_idx = df42[(df42["mode"].str.startswith("Mode 4")) & (df42["query_id"] == "Q01")].index[0]
    assert df42.loc[target_idx, "retry_count"] == 0
    df42.loc[target_idx, "retry_count"] = 3
    df42.to_csv(seed_files[0], index=False)

    # Reassemble root
    dfs_perturbed = [pd.read_csv(p) for p in seed_files]
    pd.concat(dfs_perturbed, ignore_index=True).to_csv(root_dst, index=False)

    # Regenerate perturbed
    pert_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig5_validation.tex", "r") as f:
        t_c_pert = f.read()
    assert "0.41" in t_c_pert
    assert "+47.62" in t_c_pert

    with open(table_dir / "table8_tradeoff.tex", "r") as f:
        t8_pert = f.read()
    assert "0.41" in t8_pert
    assert "+47.62" in t8_pert

    # Restore
    shutil.copy(auth_inputs["seed_csvs"][0], seed_files[0])
    shutil.copy(auth_inputs["root_csv"], root_dst)

    rest_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig5_validation.tex", "r") as f:
        t_c_rest = f.read()
    assert "0.37" in t_c_rest
    assert "+33.33\\%" in t_c_rest


def test_perturbation_fig6_memory_growth(auth_inputs, tmp_path):
    """
    Focused perturbation test for Figure 6 and Table D (Memory Store Growth).
    1. Copy inputs to isolated sandbox.
    2. Perturb Mode 4 Query Q07 admission from None to ADMITTED in seed 42.
    3. Generate all results in sandbox.
    4. Verify Table D and Figure 6 reflect the delta (final plateau 4 instead of 3, Q07 ADMITTED).
    5. Restore original benchmark CSV.
    6. Regenerate and verify exact baseline restoration (final plateau returns to 3).
    """
    sandbox_dir = tmp_path / "sandbox_fig6"
    sandbox_dir.mkdir()
    summary_dir = sandbox_dir / "summaries"
    table_dir = sandbox_dir / "tables"
    fig_dir = sandbox_dir / "figures"
    manifest_file = sandbox_dir / "results_manifest.json"

    seed_files = []
    for s in SEEDS:
        s_dir = sandbox_dir / f"seed{s}"
        s_dir.mkdir()
        dst = s_dir / "benchmark_results.csv"
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], dst)
        seed_files.append(dst)

    root_dst = sandbox_dir / "benchmark_results.csv"
    shutil.copy(auth_inputs["root_csv"], root_dst)
    telem_dst = sandbox_dir / "retrieval_telemetry.csv"
    shutil.copy(auth_inputs["telem_csv"], telem_dst)

    # Baseline check
    base_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig6_validation.tex", "r") as f:
        t_d_base = f.read()
    assert "invariant at exactly 3 from Q15 to Q25" in t_d_base
    assert "Q04 (Store=1), Q13 (Store=2), Q15 (Store=3)" in t_d_base

    # Perturb seed 42 Mode 4 Q07 to ADMITTED
    df42 = pd.read_csv(seed_files[0])
    target_idx = df42[(df42["mode"].str.startswith("Mode 4")) & (df42["query_id"] == "Q07")].index[0]
    df42.loc[target_idx, "memory_admission"] = "ADMITTED"
    df42.to_csv(seed_files[0], index=False)

    # Reassemble root
    dfs_perturbed = [pd.read_csv(p) for p in seed_files]
    pd.concat(dfs_perturbed, ignore_index=True).to_csv(root_dst, index=False)

    # Regenerate perturbed
    pert_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig6_validation.tex", "r") as f:
        t_d_pert = f.read()
    assert "invariant at exactly 4 from Q15 to Q25" in t_d_pert
    assert "Q07 (Store=2)" in t_d_pert
    assert "Q15 (Store=4)" in t_d_pert

    # Restore
    shutil.copy(auth_inputs["seed_csvs"][0], seed_files[0])
    shutil.copy(auth_inputs["root_csv"], root_dst)

    rest_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table_fig6_validation.tex", "r") as f:
        t_d_rest = f.read()
    assert "invariant at exactly 3 from Q15 to Q25" in t_d_rest
    assert "Q04 (Store=1), Q13 (Store=2), Q15 (Store=3)" in t_d_rest


def test_perturbation_table9_divergence(auth_inputs, tmp_path):
    """
    Focused perturbation test for Table IX (Forensic Failure Diagnostics).
    1. Copy inputs to isolated sandbox.
    2. Perturb Mode 4 Query Q05 execution_accuracy from 0 to 1 across all seeds.
    3. Generate all results in sandbox.
    4. Verify Table IX drops from 7 divergent queries to 6 (Q05 removed, caption updated to Six).
    5. Restore original benchmark CSVs.
    6. Regenerate and verify exact baseline restoration (7 divergent queries restored, caption Seven).
    """
    sandbox_dir = tmp_path / "sandbox_table9"
    sandbox_dir.mkdir()
    summary_dir = sandbox_dir / "summaries"
    table_dir = sandbox_dir / "tables"
    fig_dir = sandbox_dir / "figures"
    manifest_file = sandbox_dir / "results_manifest.json"

    seed_files = []
    for s in SEEDS:
        s_dir = sandbox_dir / f"seed{s}"
        s_dir.mkdir()
        dst = s_dir / "benchmark_results.csv"
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], dst)
        seed_files.append(dst)

    root_dst = sandbox_dir / "benchmark_results.csv"
    shutil.copy(auth_inputs["root_csv"], root_dst)
    telem_dst = sandbox_dir / "retrieval_telemetry.csv"
    shutil.copy(auth_inputs["telem_csv"], telem_dst)

    # Baseline check
    base_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table9_failures.tex", "r") as f:
        t9_base = f.read()
    assert "Seven Divergent Semantic Queries" in t9_base
    assert "Q05 & A & Success & False" in t9_base

    # Perturb Q05 in all seeds to execution_accuracy = 1
    for sf in seed_files:
        df_s = pd.read_csv(sf)
        mask = (df_s["mode"].str.startswith("Mode 4")) & (df_s["query_id"] == "Q05")
        df_s.loc[mask, "execution_accuracy"] = 1
        df_s.to_csv(sf, index=False)

    # Reassemble root
    dfs_perturbed = [pd.read_csv(p) for p in seed_files]
    pd.concat(dfs_perturbed, ignore_index=True).to_csv(root_dst, index=False)

    # Regenerate perturbed
    pert_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table9_failures.tex", "r") as f:
        t9_pert = f.read()
    assert "Six Divergent Semantic Queries" in t9_pert
    assert "Q05" not in t9_pert
    assert "Q14" in t9_pert

    # Restore
    for s, sf in zip(SEEDS, seed_files):
        shutil.copy(auth_inputs["seed_csvs"][SEEDS.index(s)], sf)
    shutil.copy(auth_inputs["root_csv"], root_dst)

    rest_res = generate_all_results(
        root_benchmark_csv=root_dst,
        telemetry_csv=telem_dst,
        seed_csv_paths=[str(p) for p in seed_files],
        output_summary_dir=summary_dir,
        output_table_dir=table_dir,
        output_png_dir=fig_dir / "png",
        output_svg_dir=fig_dir / "svg",
        manifest_path=manifest_file,
    )
    with open(table_dir / "table9_failures.tex", "r") as f:
        t9_rest = f.read()
    assert "Seven Divergent Semantic Queries" in t9_rest
    assert "Q05 & A & Success & False" in t9_rest

