"""
ARMG Phase 4: Benchmark Raw-Data Integrity and Smoke-Test Exclusion Verification.
Remediation Verification Suite.
"""

import json
from pathlib import Path
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SEEDS = [42, 123, 999]
MODES = ["mode_1", "mode_2", "mode_3", "mode_4", "mode_5", "mode_6"]
SMOKE_RUN_ID = "run_mode_1_1791274481"


def verify_phase4_data_integrity():
    print("=" * 80)
    print("ARMG PHASE 4: DATA INTEGRITY & SMOKE-TEST EXCLUSION VERIFICATION")
    print("=" * 80)

    # 1. Check Root benchmark_results.csv
    root_csv = REPO_ROOT / "benchmark" / "benchmark_results.csv"
    assert root_csv.exists(), f"Missing {root_csv}"
    root_df = pd.read_csv(root_csv)
    assert len(root_df) == 450, f"Expected 450 rows in root CSV, got {len(root_df)}"
    assert not (root_df["run_id"] == SMOKE_RUN_ID).any(), "Smoke test found in root benchmark_results.csv!"
    print("  [PASS] Root benchmark_results.csv has 450 rows, 0 smoke records.")

    # 2. Check Seed CSVs
    for s in SEEDS:
        seed_csv = REPO_ROOT / "benchmark" / f"seed{s}" / "benchmark_results.csv"
        assert seed_csv.exists(), f"Missing {seed_csv}"
        df_s = pd.read_csv(seed_csv)
        assert len(df_s) == 150, f"Expected 150 rows in seed {s} CSV, got {len(df_s)}"
        assert not (df_s["run_id"] == SMOKE_RUN_ID).any(), f"Smoke test found in seed {s} CSV!"
        print(f"  [PASS] Seed {s} benchmark_results.csv has 150 rows, 0 smoke records.")

    # 3. Check Raw Hierarchy
    raw_root = REPO_ROOT / "benchmark" / "raw"
    total_raw_rows = 0
    for s in SEEDS:
        for m in MODES:
            p = raw_root / f"seed_{s}" / m / "per_query_results.csv"
            assert p.exists(), f"Missing {p}"
            df_raw = pd.read_csv(p)
            assert len(df_raw) == 25, f"Expected 25 rows in {p}, got {len(df_raw)}"
            assert not (df_raw["run_id"] == SMOKE_RUN_ID).any(), f"Smoke test found in {p}!"
            total_raw_rows += len(df_raw)

    assert total_raw_rows == 450, f"Expected 450 total raw rows, got {total_raw_rows}"
    print(f"  [PASS] Raw hierarchy across all 18 mode directories has 450 rows, 0 smoke records.")

    # 4. Check Statistical Summary
    stat_json = REPO_ROOT / "benchmark" / "statistical_summary.json"
    assert stat_json.exists()
    with open(stat_json, "r", encoding="utf-8") as f:
        stat_data = json.load(f)
    for m_name, d in stat_data.items():
        assert d["sample_size_seeds"] == 3
        assert d["total_queries_evaluated"] == 75
        assert d["execution_success"]["denominator"] == 75
        assert d["relational_accuracy"]["denominator"] == 75
    print("  [PASS] Multi-seed statistical summary has 75 evaluations per mode (450 total).")

    # 5. Check Telemetry Coverage
    telem_csv = REPO_ROOT / "benchmark" / "retrieval_telemetry.csv"
    assert telem_csv.exists()
    telem_df = pd.read_csv(telem_csv)
    assert len(telem_df) == 141, f"Expected 141 rows (47 x 3), got {len(telem_df)}"
    assert not (telem_df["run_id"] == SMOKE_RUN_ID).any()
    print("  [PASS] Canonical retrieval telemetry has 141 rows across 3 seeds (47 each).")

    print("\nALL DATA INTEGRITY AND SMOKE-TEST EXCLUSION CHECKS PASSED.")
    return True


if __name__ == "__main__":
    verify_phase4_data_integrity()
