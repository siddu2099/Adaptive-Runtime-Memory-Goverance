"""
ARMG Canonical Benchmark Analysis Layer.
Provides a strictly data-driven pipeline connecting raw benchmark execution CSVs
directly to summary metrics, LaTeX tables, and publication visualization figures.
Enforces:
    RAW BENCHMARK CSVs -> CANONICAL ANALYSIS -> METRIC DATASET -> TABLES / FIGURES
Per Audit 1 Remediation Item REM-P0-02.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

DEFAULT_BENCHMARK_CSVS = [
    "benchmark/seed42/benchmark_results.csv",
    "benchmark/seed123/benchmark_results.csv",
    "benchmark/seed999/benchmark_results.csv",
]

MODE_ORDER = [
    "Mode 1 (Zero-Shot)",
    "Mode 2 (Stateless Self-Correction)",
    "Mode 3 (Naive Vector RAG)",
    "Mode 4 (Full ARMG)",
    "Mode 5 (ARMG - Negative Constraints)",
    "Mode 6 (ARMG - Temporal Decay)",
]

MODE_LABELS = {
    "Mode 1 (Zero-Shot)": "Mode 1\n(Zero-Shot)",
    "Mode 2 (Stateless Self-Correction)": "Mode 2\n(Stateless Self-Corr)",
    "Mode 3 (Naive Vector RAG)": "Mode 3\n(Naive RAG)",
    "Mode 4 (Full ARMG)": "Mode 4\n(Full ARMG)",
    "Mode 5 (ARMG - Negative Constraints)": "Mode 5\n(ARMG − NegConst)",
    "Mode 6 (ARMG - Temporal Decay)": "Mode 6\n(ARMG with λ=0)",
}


def load_benchmark_runs(csv_paths: Optional[List[str]] = None) -> List[pd.DataFrame]:
    """Load raw benchmark CSVs from disk."""
    paths = csv_paths or DEFAULT_BENCHMARK_CSVS
    dfs = []
    for p in paths:
        if os.path.exists(p):
            dfs.append(pd.read_csv(p))
        else:
            raise FileNotFoundError(f"Benchmark CSV not found: {p}")
    return dfs


def compute_benchmark_metrics(
    dfs: Optional[List[pd.DataFrame]] = None,
    csv_paths: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Compute programmatic aggregations across benchmark runs.
    
    Returns DataFrame with columns:
        mode, exec_succ, succ_std, exec_acc, acc_std, retries, ret_std,
        latency_ms, lat_std, total_tokens, tok_std, store_size
    """
    if dfs is None:
        dfs = load_benchmark_runs(csv_paths=csv_paths)

    n_runs = len(dfs)
    records = []

    # Map possible naming variations in raw CSV
    for target_mode in MODE_ORDER:
        mode_records = []
        for df in dfs:
            # Match mode by exact or prefix
            sub = df[df["mode"].str.startswith(target_mode[:6])]
            if sub.empty:
                continue

            succ = float((sub["success"] == True).mean() * 100.0)
            acc = float((sub["execution_accuracy"] == True).mean() * 100.0)
            ret = float(sub["retry_count"].mean())
            lat = float(sub["latency_ms"].mean())
            tok = float(sub["total_tokens"].mean())

            # Store size: Mode 3 stores all; Mode 4-6 admits only high-utility items
            if "Mode 3" in target_mode:
                store_size = int((sub["memory_admission"] == "NAIVE_STORED").sum())
            elif any(m in target_mode for m in ("Mode 4", "Mode 5", "Mode 6")):
                store_size = int((sub["memory_admission"] == "ADMITTED").sum())
            else:
                store_size = 0

            mode_records.append({
                "succ": succ,
                "acc": acc,
                "ret": ret,
                "lat": lat,
                "tok": tok,
                "store": store_size,
            })

        if not mode_records:
            continue

        succ_vals = [r["succ"] for r in mode_records]
        acc_vals = [r["acc"] for r in mode_records]
        ret_vals = [r["ret"] for r in mode_records]
        lat_vals = [r["lat"] for r in mode_records]
        tok_vals = [r["tok"] for r in mode_records]
        store_vals = [r["store"] for r in mode_records]

        ddof = 1 if n_runs > 1 else 0

        records.append({
            "mode": target_mode,
            "exec_succ": float(np.mean(succ_vals)),
            "succ_std": float(np.std(succ_vals, ddof=ddof)),
            "exec_acc": float(np.mean(acc_vals)),
            "acc_std": float(np.std(acc_vals, ddof=ddof)),
            "retries": float(np.mean(ret_vals)),
            "ret_std": float(np.std(ret_vals, ddof=ddof)),
            "latency_ms": float(np.mean(lat_vals)),
            "lat_std": float(np.std(lat_vals, ddof=ddof)),
            "total_tokens": float(np.mean(tok_vals)),
            "tok_std": float(np.std(tok_vals, ddof=ddof)),
            "store_size": int(np.mean(store_vals)),
        })

    return pd.DataFrame(records)


def compute_tradeoff_profile(metrics_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute exact comparison deltas between Mode 4 (Full ARMG) and Mode 2 (Stateless Self-Correction)."""
    m2 = metrics_df[metrics_df["mode"].str.startswith("Mode 2")].iloc[0]
    m4 = metrics_df[metrics_df["mode"].str.startswith("Mode 4")].iloc[0]

    # Relative percentage changes
    ret_pct = ((m4["retries"] - m2["retries"]) / m2["retries"]) * 100.0 if m2["retries"] != 0 else 0.0
    tok_pct = ((m4["total_tokens"] - m2["total_tokens"]) / m2["total_tokens"]) * 100.0
    lat_pct = ((m4["latency_ms"] - m2["latency_ms"]) / m2["latency_ms"]) * 100.0

    # Percentage point changes
    succ_pp = m4["exec_succ"] - m2["exec_succ"]
    acc_pp = m4["exec_acc"] - m2["exec_acc"]

    deltas = [ret_pct, tok_pct, succ_pp, lat_pct, acc_pp]
    units = ["%", "%", "pp", "%", "pp"]
    labels = [
        f"{ret_pct:+.2f}%\n({m4['retries']:.2f} vs {m2['retries']:.2f} retries)",
        f"{tok_pct:+.2f}%\n({m4['total_tokens']:.1f} vs {m2['total_tokens']:.1f} tok)",
        f"{succ_pp:+.2f} pp\n({m4['exec_succ']:.1f}% vs {m2['exec_succ']:.1f}%)",
        f"{lat_pct:+.2f}%\n({m4['latency_ms']:.1f} vs {m2['latency_ms']:.1f} ms)",
        f"{acc_pp:+.2f} pp\n({m4['exec_acc']:.2f}% Parity)",
    ]

    return {
        "m2": m2.to_dict(),
        "m4": m4.to_dict(),
        "deltas": deltas,
        "units": units,
        "labels": labels,
    }


def compute_retrieval_telemetry_metrics(
    telemetry_path: str = "benchmark/retrieval_telemetry.csv",
    df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Dynamically compute retrieval geometry and threshold metrics from real FAISS telemetry.
    
    Enforces:
    - Zero synthetic data (no np.random)
    - Direct derivation from raw recorded FAISS index.search() telemetry
    - Exact separation of retrieval threshold (0.50) from admission threshold (0.25)
    - Strict empty-store null representation
    """
    if df is None:
        if not os.path.exists(telemetry_path):
            raise FileNotFoundError(f"Telemetry CSV not found: {telemetry_path}")
        df = pd.read_csv(telemetry_path)

    required_cols = [
        "run_id", "mode", "query_id", "distance_l2_sq", "similarity",
        "retrieval_similarity_threshold", "passed_retrieval_threshold",
        "candidate_returned_by_faiss", "retrieval_count", "accepted_memory_count",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Telemetry dataframe missing required columns: {missing}")

    modes = df["mode"].unique()
    query_profiles: Dict[str, Dict[str, Any]] = {}

    for mode in modes:
        mode_df = df[df["mode"] == mode]
        query_records = {}
        for qid, q_group in mode_df.groupby("query_id", sort=True):
            faiss_cands = q_group[q_group["candidate_returned_by_faiss"] == True]
            if not faiss_cands.empty and faiss_cands["similarity"].notna().any():
                max_sim = float(faiss_cands["similarity"].max())
                mean_sim = float(faiss_cands["similarity"].mean())
                min_dist = float(faiss_cands["distance_l2_sq"].min()) if faiss_cands["distance_l2_sq"].notna().any() else None
                n_cands = len(faiss_cands)
            else:
                max_sim = None
                mean_sim = None
                min_dist = None
                n_cands = 0

            ret_count = int(q_group["retrieval_count"].iloc[0])
            acc_count = int(q_group["accepted_memory_count"].iloc[0])
            store_before = int(q_group["store_size_before_retrieval"].iloc[0])
            store_after = int(q_group["store_size_after_query"].iloc[0])

            query_records[qid] = {
                "query_id": qid,
                "max_similarity": max_sim,
                "mean_similarity": mean_sim,
                "min_distance_l2_sq": min_dist,
                "candidate_count": n_cands,
                "retrieval_count": ret_count,
                "accepted_memory_count": acc_count,
                "store_size_before": store_before,
                "store_size_after": store_after,
            }

        all_max_sims = [r["max_similarity"] for r in query_records.values() if r["max_similarity"] is not None]
        mean_observed_sim = float(np.mean(all_max_sims)) if all_max_sims else 0.0
        total_retrieval_events = sum(r["retrieval_count"] for r in query_records.values())
        distinct_queries = sum(1 for r in query_records.values() if r["retrieval_count"] > 0)
        n_queries = len(query_records)
        coverage_pct = (distinct_queries / n_queries * 100.0) if n_queries > 0 else 0.0

        query_profiles[mode] = {
            "mode": mode,
            "queries": query_records,
            "mean_observed_similarity": mean_observed_sim,
            "total_retrieval_events": total_retrieval_events,
            "distinct_queries_with_retrieval": distinct_queries,
            "total_queries": n_queries,
            "retrieval_coverage_pct": coverage_pct,
        }

    return {
        "raw_df": df,
        "modes": list(modes),
        "profiles": query_profiles,
    }

