"""
ARMG Phase 9: Empirical Evaluation Runner.

Executes the formal empirical evaluation across six experimental configurations:
- Mode 1: Monolithic Zero-Shot Baseline
- Mode 2: Stateless Self-Correction Baseline
- Mode 3: Naive Vector RAG Baseline
- Mode 4: Full ARMG Architecture
- Mode 5: ARMG - Negative Constraints (Ablation)
- Mode 6: ARMG - Temporal Decay (Ablation with lambda=0)

Usage:
  python scripts/eval_runner.py --verify-gold
  python scripts/eval_runner.py --limit 2
  python scripts/eval_runner.py --mode all --output benchmark/benchmark_results.csv
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.repair_agent import RepairSQLGenerator
from agents.schema_introspector import SchemaIntrospector
from agents.schema_pruner import SchemaPruner
from agents.sql_generator import SQLGenerator
from benchmark.equivalence import check_relational_equivalence
from benchmark.modes import (
    AblationNoNegConstraintsWorkflow,
    NaiveVectorStore,
    QueryBenchmarkRecord,
    execute_mode_1_zero_shot,
    execute_mode_2_self_correction,
    execute_mode_3_naive_rag,
    execute_mode_4_full_armg,
    execute_mode_5_armg_no_neg_constraints,
    execute_mode_6_armg_no_decay,
)
from environment.postgres import PostgreSQLEnvironment
from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import ExecutionValidator

QUERIES_FILE = REPO_ROOT / "benchmark" / "queries.json"
DEFAULT_OUTPUT_CSV = REPO_ROOT / "benchmark" / "benchmark_results.csv"


def load_and_validate_dataset(filepath: Path = QUERIES_FILE) -> List[Dict[str, Any]]:
    """Load benchmark queries and strictly validate distribution and fields."""
    if not filepath.exists():
        raise FileNotFoundError(f"Benchmark queries file not found at {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if len(data) != 25:
        raise ValueError(f"Expected exactly 25 benchmark queries, found {len(data)}")

    expected_ids = [f"Q{i:02d}" for i in range(1, 26)]
    actual_ids = [item.get("query_id") for item in data]
    if actual_ids != expected_ids:
        raise ValueError(f"Query IDs mismatch. Expected {expected_ids}, got {actual_ids}")

    # Check category distribution
    cat_counts: Dict[str, int] = {}
    for item in data:
        cat = item.get("category", "")
        cat_prefix = cat.split("—")[0].strip() if "—" in cat else cat.split("-")[0].strip()
        cat_counts[cat_prefix] = cat_counts.get(cat_prefix, 0) + 1

    expected_distribution = {
        "Category A": 5,
        "Category B": 8,
        "Category C": 6,
        "Category D": 6,
    }

    for cat_prefix, exp_count in expected_distribution.items():
        actual = cat_counts.get(cat_prefix, 0)
        if actual != exp_count:
            raise ValueError(
                f"Category distribution mismatch for {cat_prefix}: expected {exp_count}, got {actual}"
            )

    return data


def verify_gold_queries(
    dataset: List[Dict[str, Any]],
    env: Optional[PostgreSQLEnvironment] = None,
) -> Tuple[bool, List[str]]:
    """Gate A: Execute every gold SQL against PostgreSQL and verify successful execution."""
    env = env or PostgreSQLEnvironment()
    failed_reports = []

    for item in dataset:
        qid = item["query_id"]
        gold_sql = item["gold_sql"]
        res = env.execute(gold_sql)
        if not res.is_success:
            failed_reports.append(f"Query {qid} failed execution: {res.error}")

    return len(failed_reports) == 0, failed_reports


def run_mode_experiment(
    mode_name: str,
    dataset: List[Dict[str, Any]],
    env: PostgreSQLEnvironment,
    seed: int = 42,
    run_id: Optional[str] = None,
) -> List[QueryBenchmarkRecord]:
    """Execute an independent, clean experimental run for a specific mode."""
    run_id = run_id or f"run_{mode_name.lower().replace(' ', '_').replace('-', '_')}_{int(time.time())}"
    records: List[QueryBenchmarkRecord] = []

    # Initialize independent components per mode
    introspector = SchemaIntrospector(env)
    pruner = SchemaPruner()
    validator = ExecutionValidator()
    generator = SQLGenerator()
    repair_generator = RepairSQLGenerator()

    if mode_name == "mode_1":
        for item in dataset:
            rec = execute_mode_1_zero_shot(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                generator=generator,
                introspector=introspector,
                pruner=pruner,
                validator=validator,
            )
            records.append(rec)
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} lat={rec.latency_ms}ms", flush=True)

    elif mode_name == "mode_2":
        for item in dataset:
            rec = execute_mode_2_self_correction(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                generator=generator,
                repair_generator=repair_generator,
                introspector=introspector,
                pruner=pruner,
                validator=validator,
                max_retries=3,
            )
            records.append(rec)
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} lat={rec.latency_ms}ms", flush=True)

    elif mode_name == "mode_3":
        # Fresh naive vector store
        naive_store = NaiveVectorStore(dimension=768)
        for item in dataset:
            rec = execute_mode_3_naive_rag(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                naive_store=naive_store,
                embed_fn=default_embed_fn,
                generator=generator,
                introspector=introspector,
                pruner=pruner,
                validator=validator,
            )
            records.append(rec)
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} ret={rec.memory_retrieval_count} adm={rec.memory_admission} store={naive_store.count()} lat={rec.latency_ms}ms", flush=True)

    elif mode_name == "mode_4":
        # Fresh FAISS memory store and ARMG workflow
        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            introspector=introspector,
            pruner=pruner,
            sql_generator=generator,
            repair_generator=repair_generator,
            validator=validator,
            vector_store=vector_store,
            embed_fn=default_embed_fn,
        )
        app = wf.build_graph()
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
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} ret={rec.memory_retrieval_count} adm={rec.memory_admission} reinf={rec.memory_reinforcement} store={vector_store.count()} lat={rec.latency_ms}ms", flush=True)
        print(f"    >>> Mode 4 Final Store Count: {vector_store.count()}", flush=True)

    elif mode_name == "mode_5":
        # Fresh FAISS memory store and AblationNoNegConstraintsWorkflow
        vector_store = FAISSMemoryStore()
        wf = AblationNoNegConstraintsWorkflow(
            environment=env,
            introspector=introspector,
            pruner=pruner,
            sql_generator=generator,
            repair_generator=repair_generator,
            validator=validator,
            vector_store=vector_store,
            embed_fn=default_embed_fn,
        )
        app = wf.build_graph()
        for item in dataset:
            rec = execute_mode_5_armg_no_neg_constraints(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                workflow_app=app,
                max_retries=3,
            )
            records.append(rec)
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} ret={rec.memory_retrieval_count} adm={rec.memory_admission} reinf={rec.memory_reinforcement} store={vector_store.count()} lat={rec.latency_ms}ms", flush=True)
        print(f"    >>> Mode 5 Final Store Count: {vector_store.count()}", flush=True)

    elif mode_name == "mode_6":
        # Fresh FAISS memory store with lambda=0 (no temporal decay)
        vector_store = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine(decay_rate=0.0)
        wf = ARMGRepairWorkflow(
            environment=env,
            introspector=introspector,
            pruner=pruner,
            sql_generator=generator,
            repair_generator=repair_generator,
            validator=validator,
            governance_engine=gov_engine,
            vector_store=vector_store,
            embed_fn=default_embed_fn,
        )
        app = wf.build_graph()
        for item in dataset:
            rec = execute_mode_6_armg_no_decay(
                query_item=item,
                env=env,
                run_id=run_id,
                seed=seed,
                workflow_app=app,
                max_retries=3,
            )
            records.append(rec)
            print(f"    [{item['query_id']}] acc={rec.execution_accuracy} retries={rec.retry_count} ret={rec.memory_retrieval_count} adm={rec.memory_admission} reinf={rec.memory_reinforcement} store={vector_store.count()} lat={rec.latency_ms}ms", flush=True)
        print(f"    >>> Mode 6 Final Store Count: {vector_store.count()}", flush=True)

    else:
        raise ValueError(f"Unknown mode: {mode_name}")

    return records


def compute_aggregate_metrics(records: List[QueryBenchmarkRecord]) -> Dict[str, Any]:
    """Compute summary metrics and standard deviations for a set of query records."""
    if not records:
        return {}

    total_queries = len(records)
    correct_queries = sum(r.execution_accuracy for r in records)
    exec_acc_pct = round((correct_queries / total_queries) * 100.0, 2)

    retries = [r.retry_count for r in records]
    latencies = [r.latency_ms for r in records]
    tokens = [r.total_tokens for r in records if r.total_tokens is not None]

    mean_retries = round(statistics.mean(retries), 2)
    std_retries = round(statistics.stdev(retries), 2) if len(retries) > 1 else 0.0

    mean_latency = round(statistics.mean(latencies), 2)
    std_latency = round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0

    mean_tokens = round(statistics.mean(tokens), 2) if tokens else None
    std_tokens = round(statistics.stdev(tokens), 2) if len(tokens) > 1 else (0.0 if tokens else None)

    # Category breakdown
    cat_breakdown: Dict[str, Dict[str, int]] = {}
    for r in records:
        cat_prefix = r.category.split("—")[0].strip() if "—" in r.category else r.category.split("-")[0].strip()
        if cat_prefix not in cat_breakdown:
            cat_breakdown[cat_prefix] = {"total": 0, "correct": 0}
        cat_breakdown[cat_prefix]["total"] += 1
        cat_breakdown[cat_prefix]["correct"] += r.execution_accuracy

    cat_acc = {}
    for cat_prefix, stats in cat_breakdown.items():
        cat_acc[cat_prefix] = f"{stats['correct']}/{stats['total']} ({round((stats['correct'] / stats['total']) * 100.0, 1)}%)"

    return {
        "mode": records[0].mode,
        "total_queries": total_queries,
        "correct_queries": correct_queries,
        "exec_acc_pct": exec_acc_pct,
        "mean_retries": mean_retries,
        "std_retries": std_retries,
        "mean_latency_ms": mean_latency,
        "std_latency_ms": std_latency,
        "mean_tokens": mean_tokens,
        "std_tokens": std_tokens,
        "category_accuracy": cat_acc,
    }


def export_results_to_csv(records: List[QueryBenchmarkRecord], output_path: Path) -> None:
    """Save all query records to a machine-readable CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return

    fieldnames = [
        "run_id",
        "mode",
        "seed",
        "query_id",
        "category",
        "question",
        "success",
        "execution_accuracy",
        "retry_count",
        "generation_attempts",
        "latency_ms",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "validation_failures",
        "execution_failures",
        "memory_retrieval_count",
        "memory_admission",
        "memory_reinforcement",
        "error_category",
        "failure_reason",
        "final_sql",
        "gold_sql",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())


def format_ieee_markdown_table(mode_metrics: List[Dict[str, Any]]) -> str:
    """Format aggregate results into an IEEE publication-style Markdown table."""
    lines = [
        "| Mode | ExecAcc (%) | Mean Retries (+/- std) | Mean Latency ms (+/- std) | Mean Tokens (+/- std) |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for m in mode_metrics:
        mode_label = m["mode"]
        acc_str = f"{m['exec_acc_pct']}% ({m['correct_queries']}/{m['total_queries']})"
        retry_str = f"{m['mean_retries']} +/- {m['std_retries']}"
        lat_str = f"{m['mean_latency_ms']} +/- {m['std_latency_ms']}"
        tok_str = f"{m['mean_tokens']} +/- {m['std_tokens']}" if m["mean_tokens"] is not None else "N/A"
        lines.append(f"| {mode_label} | {acc_str} | {retry_str} | {lat_str} | {tok_str} |")

    return "\n".join(lines)


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="ARMG Phase 9 Empirical Evaluation Runner")
    parser.add_argument("--verify-gold", action="store_true", help="Execute Gate A gold verification only")
    parser.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["mode_1", "mode_2", "mode_3", "mode_4", "mode_5", "mode_6", "all"],
        help="Evaluation mode to execute",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of queries (for smoke testing)")
    parser.add_argument("--seed", type=int, default=42, help="Random/database seed")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV, help="Output CSV path")

    args = parser.parse_args()

    print("=" * 80)
    print("ARMG PHASE 9: IEEE EMPIRICAL EVALUATION HARNESS")
    print("=" * 80)

    # 1. Load and validate dataset
    dataset = load_and_validate_dataset()
    print(f"Dataset successfully validated: {len(dataset)} queries loaded.")

    env = PostgreSQLEnvironment()

    # 2. Gate A: Gold SQL verification
    if args.verify_gold or args.mode == "all":
        print("\n--- Gate A: Gold SQL PostgreSQL Verification ---")
        passed, errors = verify_gold_queries(dataset, env)
        if not passed:
            print("GATE A FAILED:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        print("GATE A PASSED: All 25 gold queries executed successfully against PostgreSQL warehouse.")

        if args.verify_gold:
            print("\nGold verification complete. Exiting as requested.")
            return

    # Slice dataset if --limit provided
    eval_dataset = dataset[:args.limit] if args.limit is not None else dataset
    print(f"\nEvaluating {len(eval_dataset)} queries per mode.")

    modes_to_run = (
        ["mode_1", "mode_2", "mode_3", "mode_4", "mode_5", "mode_6"]
        if args.mode == "all"
        else [args.mode]
    )

    all_records: List[QueryBenchmarkRecord] = []
    all_metrics: List[Dict[str, Any]] = []

    for mode_key in modes_to_run:
        print(f"\n>>> Running Experiment: {mode_key.upper()} ({len(eval_dataset)} queries) ...")
        t0 = time.perf_counter()
        records = run_mode_experiment(
            mode_name=mode_key,
            dataset=eval_dataset,
            env=env,
            seed=args.seed,
        )
        elapsed = time.perf_counter() - t0
        metrics = compute_aggregate_metrics(records)

        all_records.extend(records)
        all_metrics.append(metrics)

        print(f"    Completed in {round(elapsed, 2)}s | ExecAcc: {metrics['exec_acc_pct']}% | Mean Retries: {metrics['mean_retries']}")

    # Export CSV
    export_results_to_csv(all_records, args.output)
    print(f"\nPer-query records exported to: {args.output.resolve()}")

    # Display IEEE Table
    ieee_table = format_ieee_markdown_table(all_metrics)
    print("\n" + "=" * 80)
    print("IEEE COMPARATIVE RESULTS TABLE")
    print("=" * 80)
    print(ieee_table)

    # Display Category Breakdown
    print("\n" + "=" * 80)
    print("CATEGORY-WISE ACCURACY BREAKDOWN")
    print("=" * 80)
    cat_lines = []
    for m in all_metrics:
        print(f"\n{m['mode']}:")
        cat_lines.append(f"\n### {m['mode']}")
        for cat, acc in m.get("category_accuracy", {}).items():
            print(f"  - {cat}: {acc}")
            cat_lines.append(f"- **{cat}**: {acc}")

    # Export markdown summary file
    summary_path = args.output.parent / "benchmark_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# ARMG Phase 9: IEEE Benchmark Results\n\n")
        f.write("## Comparative Results Table\n\n")
        f.write(ieee_table + "\n\n")
        f.write("## Category-Wise Accuracy Breakdown\n")
        f.write("\n".join(cat_lines) + "\n")
    print(f"\nSummary report written to: {summary_path.resolve()}")



if __name__ == "__main__":
    main()
