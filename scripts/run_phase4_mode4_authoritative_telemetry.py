"""
ARMG Phase 4: Mode 4 Live Empirical Telemetry Capture Runner.
Finding P1-01 Remediation Implementation.

Reruns ONLY Mode 4 across seeds 42, 123, and 999 with real live FAISS telemetry logging:
- Real Ollama nomic-embed-text embeddings
- Real FAISS IndexFlatL2 distance & similarity calculation
- Real empty-store null representation
- Direct capture of all evaluated candidates before filtering
- Stores per-seed raw telemetry in benchmark/raw/seed_{seed}/mode_4/retrieval_telemetry.csv
- Generates canonical aggregate benchmark/retrieval_telemetry.csv
- Recomputes multi-seed descriptive statistics
"""

import json
from pathlib import Path
import sys
import time
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.repair_agent import RepairSQLGenerator
from agents.schema_introspector import SchemaIntrospector
from agents.schema_pruner import SchemaPruner
from agents.sql_generator import SQLGenerator
from benchmark.modes import execute_mode_4_full_armg, QueryBenchmarkRecord
from environment.postgres import PostgreSQLEnvironment
from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from memory.telemetry import RetrievalTelemetryLogger
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import ExecutionValidator
from scripts.compute_descriptive_statistics import compute_descriptive_stats
from scripts.verify_phase4_telemetry_provenance import verify_telemetry_provenance

SEEDS = [42, 123, 999]


def run_mode4_telemetry_capture():
    print("=" * 80)
    print("ARMG PHASE 4: MODE 4 LIVE TELEMETRY CAPTURE & PROVENANCE RERUN")
    print("=" * 80)
    t_start = time.perf_counter()

    queries_file = REPO_ROOT / "benchmark" / "queries.json"
    with open(queries_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)
    assert len(dataset) == 25, f"Expected 25 queries, got {len(dataset)}"

    env = PostgreSQLEnvironment()
    introspector = SchemaIntrospector(env)
    pruner = SchemaPruner()
    validator = ExecutionValidator()

    raw_root = REPO_ROOT / "benchmark" / "raw"
    per_seed_telemetry_dfs = []

    for seed in SEEDS:
        print(f"\n>>> Running Mode 4 Live Telemetry for Seed {seed} (25 queries)...")
        seed_start = time.perf_counter()
        run_id = f"authoritative_seed{seed}_mode_4"

        # 1. Fresh FAISS vector store & telemetry logger per seed
        vector_store = FAISSMemoryStore()
        telemetry_logger = RetrievalTelemetryLogger()
        sql_gen = SQLGenerator(seed=seed)
        repair_gen = RepairSQLGenerator(seed=seed)

        wf = ARMGRepairWorkflow(
            environment=env,
            introspector=introspector,
            pruner=pruner,
            sql_generator=sql_gen,
            repair_generator=repair_gen,
            validator=validator,
            vector_store=vector_store,
            embed_fn=default_embed_fn,
            telemetry_logger=telemetry_logger,
        )
        app = wf.build_graph()

        records = []
        for item in dataset:
            rec = execute_mode_4_full_armg(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                workflow_app=app,
                max_retries=3,
            )
            records.append(rec)
            telemetry_logger.update_store_size_after_query(
                query_id=item["query_id"],
                mode="Mode 4 (Full ARMG)",
                store_size_after=vector_store.count(),
            )
            print(
                f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} "
                f"ret={rec.memory_retrieval_count} adm={rec.memory_admission} reinf={rec.memory_reinforcement} "
                f"store={vector_store.count()} lat={rec.latency_ms:.1f}ms",
                flush=True,
            )

        seed_elapsed = time.perf_counter() - seed_start
        print(f"  [Seed {seed}] Mode 4 Completed in {seed_elapsed:.1f}s | Final Store Size: {vector_store.count()}")

        # 2. Write per-seed raw telemetry CSV
        mode_dir = raw_root / f"seed_{seed}" / "mode_4"
        mode_dir.mkdir(parents=True, exist_ok=True)
        raw_telem_csv = mode_dir / "retrieval_telemetry.csv"
        telemetry_logger.write_csv(raw_telem_csv)
        print(f"  -> Written raw telemetry: {raw_telem_csv} ({len(telemetry_logger.retrieval_records)} records)")

        df_seed_telem = pd.read_csv(raw_telem_csv)
        per_seed_telemetry_dfs.append(df_seed_telem)

        # 3. Update per-query results CSV in raw directory
        new_mode_df = pd.DataFrame([r.to_dict() for r in records])
        new_mode_df.to_csv(mode_dir / "per_query_results.csv", index=False)

        # Update execution_log.jsonl
        log_jsonl = mode_dir / "execution_log.jsonl"
        with open(log_jsonl, "w", encoding="utf-8") as f_log:
            for r in records:
                d = r.to_dict()
                d["success"] = bool(d["success"])
                d["execution_accuracy"] = int(d["execution_accuracy"])
                f_log.write(json.dumps(d) + "\n")

        # 4. Update Mode 4 in seed{seed}/benchmark_results.csv
        seed_csv_path = REPO_ROOT / "benchmark" / f"seed{seed}" / "benchmark_results.csv"
        seed_df = pd.read_csv(seed_csv_path)
        # Replace mode_4 rows
        m4_mask = seed_df["mode"].str.contains("Mode 4")
        non_m4_df = seed_df[~m4_mask]
        updated_seed_df = pd.concat([non_m4_df, new_mode_df], ignore_index=True)
        # Sort by mode and query_id to keep consistent order
        updated_seed_df.to_csv(seed_csv_path, index=False)

    # 5. Build Canonical Aggregate Retrieval Telemetry CSV
    print("\n[Step 5] Building Canonical Aggregate Retrieval Telemetry CSV...")
    canonical_df = pd.concat(per_seed_telemetry_dfs, ignore_index=True)
    canonical_telem_path = REPO_ROOT / "benchmark" / "retrieval_telemetry.csv"
    canonical_df.to_csv(canonical_telem_path, index=False)
    print(f"  -> Written canonical telemetry: {canonical_telem_path} ({len(canonical_df)} records across 3 seeds)")

    # 6. Rebuild benchmark/benchmark_results.csv (450 rows)
    all_seed_dfs = []
    for s in SEEDS:
        all_seed_dfs.append(pd.read_csv(REPO_ROOT / "benchmark" / f"seed{s}" / "benchmark_results.csv"))
    combined_all = pd.concat(all_seed_dfs, ignore_index=True)
    assert len(combined_all) == 450, f"Expected 450 total rows, got {len(combined_all)}"
    combined_all.to_csv(REPO_ROOT / "benchmark" / "benchmark_results.csv", index=False)
    print("  -> Updated benchmark/benchmark_results.csv with 450 authoritative records.")

    # 7. Recompute Multi-Seed Descriptive Statistics
    print("\n[Step 7] Recomputing Descriptive Multi-Seed Statistics...")
    compute_descriptive_stats()

    # 8. Run Telemetry Provenance Verification
    print("\n[Step 8] Running Telemetry Provenance Audit...")
    verify_telemetry_provenance()

    env.close()
    total_elapsed = time.perf_counter() - t_start
    print("\n" + "=" * 80)
    print(f"MODE 4 TELEMETRY REMEDIATION COMPLETE IN {total_elapsed:.1f}s ({total_elapsed/60:.2f} min)")
    print("=" * 80)


if __name__ == "__main__":
    run_mode4_telemetry_capture()
