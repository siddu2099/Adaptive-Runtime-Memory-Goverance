"""
ARMG Phase 4: Master Authoritative Benchmark Suite Runner.
Executes the Authoritative Empirical Benchmark:
- Frozen Configuration: qwen2.5:7b-instruct, nomic-embed-text, temp=0.0
- Deterministic pipeline stability repetitions across seeds: 42, 123, 999
- All 6 experimental modes evaluated sequentially over 25 Star Schema queries (450 total)
- Live PostgreSQL 18.1 execution & Ollama inference
- Captures raw per-query evidence, FAISS telemetry, and multi-seed descriptive statistics
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.record_environment import record_environment
from scripts.eval_runner import (
    load_and_validate_dataset,
    verify_gold_queries,
    run_mode_experiment,
    compute_aggregate_metrics,
    export_results_to_csv,
    format_ieee_markdown_table,
)
from environment.postgres import PostgreSQLEnvironment
from scripts.generate_canonical_telemetry import generate_canonical_telemetry
from scripts.build_raw_benchmark_hierarchy import build_raw_hierarchy
from scripts.compute_descriptive_statistics import compute_descriptive_stats


SEEDS = [42, 123, 999]
MODES = ["mode_1", "mode_2", "mode_3", "mode_4", "mode_5", "mode_6"]


def run_phase4_suite():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 80)
    print("ARMG PHASE 4: AUTHORITATIVE BENCHMARK EXECUTION SUITE")
    print("=" * 80)
    suite_start = time.perf_counter()

    # Step 1: Pre-Benchmark Environment Gate
    print("\n[STEP 1/6] Recording and Verifying Runtime Environment...")
    env_info = record_environment()
    print(f"  - Python: {env_info['python']['version'].split()[0]}")
    print(f"  - PostgreSQL: {env_info['postgresql']['version'].split(',')[0]}")
    print(f"  - Ollama: {env_info['ollama']['version']} ({env_info['ollama']['base_url']})")
    print(f"  - LLM Model: {env_info['ollama']['generation_model']} (Ready: {env_info['ollama']['generation_model_available']})")
    print(f"  - Embedding: {env_info['ollama']['embedding_model']} (Ready: {env_info['ollama']['embedding_model_available']})")

    # Step 2: Validate Dataset & Gold Queries
    print("\n[STEP 2/6] Validating Benchmark Dataset & Gold SQL...")
    dataset = load_and_validate_dataset()
    env = PostgreSQLEnvironment()
    gold_passed, gold_errors = verify_gold_queries(dataset, env)
    if not gold_passed:
        print("FATAL: Gate A Gold SQL verification failed:")
        for err in gold_errors:
            print(f"  - {err}")
        sys.exit(1)
    print(f"  - Gate A Passed: All {len(dataset)} gold queries executed successfully.")

    # Step 3: Execute Benchmark Repetitions Across Seeds
    print("\n[STEP 3/6] Executing All 6 Modes Across Seeds (42, 123, 999)...")
    all_seed_results = {}

    for seed in SEEDS:
        print(f"\n=======================================================")
        print(f"--- RUNNING SEED {seed} (450 total evaluation plan) ---")
        print(f"=======================================================")
        seed_dir = REPO_ROOT / "benchmark" / f"seed{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)
        seed_csv = seed_dir / "benchmark_results.csv"

        seed_records = []
        seed_metrics = []

        for mode_key in MODES:
            print(f"\n>>> [Seed {seed}] Running Mode: {mode_key.upper()} (25 queries) ...")
            t0 = time.perf_counter()
            records = run_mode_experiment(
                mode_name=mode_key,
                dataset=dataset,
                env=env,
                seed=seed,
                run_id=f"authoritative_seed{seed}_{mode_key}",
            )
            elapsed = time.perf_counter() - t0
            metrics = compute_aggregate_metrics(records)

            seed_records.extend(records)
            seed_metrics.append(metrics)
            print(f"    Completed in {elapsed:.1f}s | ExecAcc: {metrics['exec_acc_pct']}% | Mean Retries: {metrics['mean_retries']}")

        # Export seed CSV
        export_results_to_csv(seed_records, seed_csv)
        print(f"\n  -> Seed {seed} results written to: {seed_csv}")

        # Summary markdown
        summary_md = format_ieee_markdown_table(seed_metrics)
        with open(seed_dir / "benchmark_summary.md", "w", encoding="utf-8") as f_s:
            f_s.write(f"# ARMG Authoritative Benchmark — Seed {seed}\n\n")
            f_s.write(summary_md + "\n")

        all_seed_results[seed] = seed_metrics

    # Step 4: Generate Canonical FAISS Retrieval Telemetry
    print("\n[STEP 4/6] Generating Canonical FAISS Retrieval Telemetry...")
    telemetry_csv = REPO_ROOT / "benchmark" / "retrieval_telemetry.csv"
    generate_canonical_telemetry(
        queries_path=str(REPO_ROOT / "benchmark" / "queries.json"),
        output_csv=str(telemetry_csv),
    )

    # Step 5: Build Canonical Raw Hierarchy
    print("\n[STEP 5/6] Building Canonical Raw Evidence Hierarchy...")
    build_raw_hierarchy()

    # Step 6: Compute Descriptive Multi-Seed Statistics
    print("\n[STEP 6/6] Computing Multi-Seed Descriptive Statistics...")
    compute_descriptive_stats()

    env.close()
    total_elapsed = time.perf_counter() - suite_start
    print("\n" + "=" * 80)
    print(f"ARMG PHASE 4 AUTHORITATIVE BENCHMARK COMPLETE ({total_elapsed:.1f}s / {total_elapsed/60:.2f} min)")
    print("=" * 80)


if __name__ == "__main__":
    run_phase4_suite()
