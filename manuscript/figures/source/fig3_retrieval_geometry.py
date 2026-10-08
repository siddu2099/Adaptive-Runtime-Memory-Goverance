"""
Figure 3: Empirical Post-Remediation Retrieval Telemetry with Derived Pre-Remediation Baseline.
Phase 2 Canonical Implementation.

Enforces:
- Post-remediation values derived directly from raw recorded FAISS telemetry:
  benchmark/retrieval_telemetry.csv -> Figure 3 (PNG/SVG)
- Explicit derived / non-empirical historical baseline for pre-remediation (S ~ 0.0035 from unnormalized norms)
- Strict empty-store null handling
"""

import os
from pathlib import Path
from typing import List, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_fig3(
    telemetry_path: str = "benchmark/retrieval_telemetry.csv",
    output_png: str = "manuscript/figures/png/fig3_retrieval_geometry.png",
    output_svg: str = "manuscript/figures/svg/fig3_retrieval_geometry.svg",
) -> None:
    """Generate camera-ready Figure 3: Empirical Post-Remediation Retrieval Telemetry with Derived Pre-Remediation Baseline."""
    p = Path(telemetry_path)
    if not p.exists():
        raise FileNotFoundError(
            f"Canonical FAISS retrieval telemetry not found at '{telemetry_path}'. "
            "Real empirical evidence is required; synthetic fallback is strictly prohibited per Phase 2 Section 9."
        )

    df = pd.read_csv(p)
    if df.empty:
        raise ValueError(f"Telemetry dataset at '{telemetry_path}' is empty. Empirical evidence required.")

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    os.makedirs(os.path.dirname(output_svg), exist_ok=True)

    # Filter Post-Remediation Mode 4
    post_m4 = df[df["mode"] == "Mode 4 (Full ARMG)"].copy()
    if post_m4.empty:
        # Fallback to any Mode 4 naming if present
        post_m4 = df[df["mode"].str.contains("Mode 4", na=False)].copy()

    if post_m4.empty:
        raise ValueError("No Mode 4 retrieval telemetry found in dataset.")

    # Determine ordered unique queries
    queries = sorted(post_m4["query_id"].unique())
    x = np.arange(len(queries))

    # Aggregate top observed cosine similarity and retrieval count per query
    post_sim = list()
    post_retrievals = list()
    has_candidate_post = list()

    for qid in queries:
        q_rows = post_m4[post_m4["query_id"] == qid]
        ret_cnt = int(q_rows["retrieval_count"].iloc[0])
        post_retrievals.append(ret_cnt)

        # Candidates actually returned by FAISS
        faiss_cands = q_rows[q_rows["candidate_returned_by_faiss"] == True]
        if not faiss_cands.empty and faiss_cands["similarity"].notna().any():
            top_score = float(faiss_cands["similarity"].max())
            post_sim.append(top_score)
            has_candidate_post.append(True)
        else:
            # Empty store or no FAISS candidate
            post_sim.append(np.nan)
            has_candidate_post.append(False)

    post_sim = np.array(post_sim)
    post_retrievals = np.array(post_retrievals)

    # Check for pre-remediation telemetry in same dataset
    pre_df = df[df["mode"].str.contains("Pre-Remediation", na=False)].copy()
    has_empirical_pre = not pre_df.empty

    pre_sim = []
    if has_empirical_pre:
        for qid in queries:
            q_rows = pre_df[pre_df["query_id"] == qid]
            if not q_rows.empty:
                faiss_cands = q_rows[q_rows["candidate_returned_by_faiss"] == True]
                if not faiss_cands.empty and faiss_cands["similarity"].notna().any():
                    pre_sim.append(float(faiss_cands["similarity"].max()))
                else:
                    pre_sim.append(np.nan)
            else:
                pre_sim.append(np.nan)
    else:
        # If pre-remediation is not in telemetry, use historical mathematically derived baseline ~0.0035
        # (calculated from unnormalized nomic-embed norms ||v|| ~ 19.8, d^2 ~ 280, S = 1/(1+d^2) ~ 0.0035)
        pre_sim = [0.0035] * len(queries)

    pre_sim = np.array(pre_sim)

    # Dynamic metric computations
    total_retrievals = int(np.sum(post_retrievals))
    distinct_retrieval_queries = int(np.sum(post_retrievals > 0))
    coverage_pct = (distinct_retrieval_queries / len(queries)) * 100.0 if len(queries) > 0 else 0.0

    valid_post_sims = post_sim[~np.isnan(post_sim)]
    mean_post_sim = float(np.mean(valid_post_sims)) if len(valid_post_sims) > 0 else 0.0

    tau = 0.50

    # Plotting setup
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300, sharey=True)
    plt.rcParams["font.sans-serif"] = "Arial"
    plt.rcParams["axes.edgecolor"] = "#333333"
    plt.rcParams["axes.linewidth"] = 0.8

    # -------------------------------------------------------------------------
    # Panel 1: Pre-Remediation (Unnormalized Embeddings - Derived Baseline)
    # -------------------------------------------------------------------------
    valid_pre_mask = ~np.isnan(pre_sim)
    if np.any(valid_pre_mask):
        ax1.scatter(
            x[valid_pre_mask],
            pre_sim[valid_pre_mask],
            color="#7f8c8d",
            s=45,
            zorder=3,
            label="Derived Similarity S = 1/(1+d^2)",
        )

    ax1.axhline(tau, color="#c0392b", linestyle="--", linewidth=1.5, label=f"Retrieval Threshold (tau = {tau})")
    ax1.fill_between([-1, 26], 0, tau, color="#f8d7da", alpha=0.3, label="Sub-Threshold Zone (No Retrieval)")
    ax1.set_title(
        "Pre-Remediation: Unnormalized Embeddings (Derived Baseline)\n(||v|| ~ 19.8, d^2 ~ 280, S = 1/(1+d^2) ~ 0.0035, Non-Empirical)",
        fontsize=9.5,
        fontweight="bold",
        pad=10,
    )
    ax1.set_xlabel("Benchmark Query ID", fontsize=9, fontweight="bold")
    ax1.set_ylabel(r"FAISS Similarity Score $S = \frac{1}{1 + d^2}$", fontsize=9, fontweight="bold")
    ax1.set_xticks(x[::2])
    ax1.set_xticklabels(queries[::2], fontsize=8)
    ax1.set_xlim(-0.8, len(queries) - 0.2)
    ax1.set_ylim(-0.02, 1.02)
    ax1.grid(axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax1.text(
        len(queries) / 2.0,
        0.15,
        "Mean Similarity S ~ 0.0035 << 0.50\nTotal Retrievals = 0 / 25 (0.0% Coverage)",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#721c24",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#f5c6cb"),
    )

    # -------------------------------------------------------------------------
    # Panel 2: Post-Remediation (Unit-L2 Normalized Embeddings)
    # -------------------------------------------------------------------------
    colors = ["#27ae60" if r > 0 else "#7f8c8d" for r in post_retrievals]

    # Plot actual observed candidate scores
    for idx, (sim_val, has_cand, col) in enumerate(zip(post_sim, has_candidate_post, colors)):
        if has_cand and not np.isnan(sim_val):
            ax2.scatter(
                idx,
                sim_val,
                color=col,
                s=55,
                zorder=3,
                edgecolors="#1e8449" if col == "#27ae60" else "#555555",
                linewidths=0.6,
            )
        else:
            # Empty store / No candidate returned: distinct null marker at bottom with label
            ax2.scatter(
                idx,
                0.01,
                marker="x",
                color="#999999",
                s=35,
                zorder=3,
                linewidths=1.0,
            )

    ax2.axhline(tau, color="#c0392b", linestyle="--", linewidth=1.5, label=f"Retrieval Threshold (tau = {tau})")
    ax2.fill_between([-1, 26], tau, 1.02, color="#d4edda", alpha=0.3, label="Active Retrieval Zone (S >= tau)")
    ax2.set_title(
        f"Post-Remediation: Unit-L2 Normalized Embeddings\n(||v|| = 1.0, {total_retrievals} Retrievals Restored Across {distinct_retrieval_queries} Queries)",
        fontsize=9.5,
        fontweight="bold",
        pad=10,
    )
    ax2.set_xlabel("Benchmark Query ID", fontsize=9, fontweight="bold")
    ax2.set_xticks(x[::2])
    ax2.set_xticklabels(queries[::2], fontsize=8)
    ax2.set_xlim(-0.8, len(queries) - 0.2)
    ax2.grid(axis="y", linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=8, framealpha=0.9)

    # Dynamic annotation box
    if total_retrievals > 0:
        annot_x = min(17, len(queries) - 1)
        annot_y = post_sim[annot_x] if not np.isnan(post_sim[annot_x]) else 0.70
        ax2.annotate(
            f"{total_retrievals} Total Retrievals\nacross {distinct_retrieval_queries} Queries ({coverage_pct:.1f}%)\nMean Observed S = {mean_post_sim:.4f}",
            xy=(annot_x, annot_y),
            xytext=(max(0, annot_x - 5), 0.88),
            arrowprops=dict(arrowstyle="->", lw=1.2, color="#155724"),
            fontsize=8.5,
            fontweight="bold",
            color="#155724",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffffff", edgecolor="#c3e6cb"),
        )

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.savefig(output_svg, format="svg", bbox_inches="tight")
    plt.close()
    print(f"Figure 3 generated successfully from real FAISS telemetry: {output_png} and {output_svg}")


if __name__ == "__main__":
    generate_fig3()
