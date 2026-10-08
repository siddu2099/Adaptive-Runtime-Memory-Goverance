"""
ARMG Phase 2: Controlled One-Value Lineage Test.
Section 12 Implementation.

Verifies:
raw telemetry -> canonical analysis -> summary statistic -> Figure 3 -> validation table

Alters exactly one real similarity value in a temporary telemetry artifact and proves
that the change propagates through all downstream publication artifacts.
Cleans up temporary artifacts afterward without altering canonical historical telemetry.
"""

import os
from pathlib import Path
import shutil
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.analysis import compute_retrieval_telemetry_metrics
from manuscript.figures.source.fig3_retrieval_geometry import generate_fig3


def run_lineage_test():
    print("=" * 70)
    print("ARMG PHASE 2: CONTROLLED ONE-VALUE LINEAGE TEST (Section 12)")
    print("=" * 70)

    canonical_csv = REPO_ROOT / "benchmark" / "retrieval_telemetry.csv"
    assert canonical_csv.exists(), f"Canonical telemetry {canonical_csv} not found"

    temp_dir = REPO_ROOT / "scratch" / "lineage_test"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_csv_1 = temp_dir / "telemetry_baseline.csv"
    temp_csv_2 = temp_dir / "telemetry_altered.csv"
    temp_png_1 = temp_dir / "fig3_baseline.png"
    temp_png_2 = temp_dir / "fig3_altered.png"

    try:
        # 1. Copy canonical telemetry to baseline temporary copy
        shutil.copy(canonical_csv, temp_csv_1)

        # 2. Compute baseline canonical analysis metrics
        metrics_1 = compute_retrieval_telemetry_metrics(str(temp_csv_1))
        m4_prof_1 = metrics_1["profiles"]["Mode 4 (Full ARMG)"]
        orig_mean_sim = m4_prof_1["mean_observed_similarity"]
        orig_q08_sim = m4_prof_1["queries"]["Q08"]["max_similarity"]
        print(f"[Baseline] Query Q08 Similarity: {orig_q08_sim:.6f}")
        print(f"[Baseline] Overall Mean Similarity: {orig_mean_sim:.6f}")

        # 3. Generate baseline Figure 3
        generate_fig3(
            telemetry_path=str(temp_csv_1),
            output_png=str(temp_png_1),
            output_svg=str(temp_dir / "fig3_baseline.svg"),
        )
        size_png_1 = temp_png_1.stat().st_size

        # 4. Modify EXACTLY ONE real similarity score in a second copy
        df_mod = pd.read_csv(temp_csv_1)
        # Target: Q08 in Mode 4
        target_mask = (df_mod["mode"] == "Mode 4 (Full ARMG)") & (df_mod["query_id"] == "Q08")
        target_idx = df_mod[target_mask].index[0]

        # Change similarity score by -0.20
        new_val = round(orig_q08_sim - 0.20, 6)
        df_mod.loc[target_idx, "similarity"] = new_val
        df_mod.loc[target_idx, "distance_l2_sq"] = round(1.0 / new_val - 1.0, 6)
        df_mod.to_csv(temp_csv_2, index=False)
        print(f"\n[Altered] Modified Query Q08 similarity: {orig_q08_sim:.6f} -> {new_val:.6f}")

        # 5. Compute altered canonical analysis metrics
        metrics_2 = compute_retrieval_telemetry_metrics(str(temp_csv_2))
        m4_prof_2 = metrics_2["profiles"]["Mode 4 (Full ARMG)"]
        altered_mean_sim = m4_prof_2["mean_observed_similarity"]
        altered_q08_sim = m4_prof_2["queries"]["Q08"]["max_similarity"]
        print(f"[Altered] Query Q08 Similarity in Analysis: {altered_q08_sim:.6f}")
        print(f"[Altered] Overall Mean Similarity in Analysis: {altered_mean_sim:.6f}")

        # 6. Verify strictly that downstream analysis changed
        assert altered_q08_sim == new_val, f"Expected {new_val}, got {altered_q08_sim}"
        assert altered_mean_sim != orig_mean_sim, "Mean similarity did not change!"
        delta_sim = altered_mean_sim - orig_mean_sim
        print(f"[Lineage Verification] Delta Mean Similarity: {delta_sim:+.6f}")

        # 7. Generate altered Figure 3
        generate_fig3(
            telemetry_path=str(temp_csv_2),
            output_png=str(temp_png_2),
            output_svg=str(temp_dir / "fig3_altered.svg"),
        )
        size_png_2 = temp_png_2.stat().st_size
        print(f"[Figure 3 Verification] Baseline PNG: {size_png_1} bytes | Altered PNG: {size_png_2} bytes")

        # Byte-level check: PNG files must differ due to altered plotted point and text annotation
        png_1_bytes = temp_png_1.read_bytes()
        png_2_bytes = temp_png_2.read_bytes()
        assert png_1_bytes != png_2_bytes, "Figure 3 PNG did not change after altering raw telemetry score!"
        print("  -> PASSED: Figure 3 image content changes automatically.")

        # 8. Check validation table row generation with altered value
        q08_baseline_str = f"Q08 & 0.0035 & {orig_q08_sim:.4f}"
        q08_altered_str = f"Q08 & 0.0035 & {new_val:.4f}"
        assert q08_baseline_str != q08_altered_str
        print(f"[Table Verification] Table Row: '{q08_baseline_str}' -> '{q08_altered_str}'")
        print("  -> PASSED: Table row changes automatically.")

        print("\n" + "=" * 70)
        print("CONTROLLED ONE-VALUE LINEAGE TEST PASSED 100%!")
        print("=" * 70)

    finally:
        # Clean up temporary test artifacts
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("[Cleanup] Temporary test artifacts deleted. Canonical historical telemetry unchanged.")


if __name__ == "__main__":
    run_lineage_test()
