"""
ARMG Phase 3: Telemetry Coverage and Lineage Audit.
Section 9 Audit Implementation.

Explicitly analyzes the distinction between:
- Telemetry Rows (47 total logged records)
- Empty-Store Query Evaluations (4 queries: Q01-Q04)
- FAISS Candidates Evaluated (43 candidate rows)
- Accepted Retrieval Candidates (16 memories passing tau >= 0.50)
- Distinct Queries with Retrievals (12 queries: 48.0% query coverage)
"""

import json
from pathlib import Path
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def audit_telemetry_coverage(telemetry_csv: str = "benchmark/retrieval_telemetry.csv") -> dict:
    csv_path = REPO_ROOT / telemetry_csv
    assert csv_path.exists(), f"Telemetry CSV not found: {csv_path}"

    df = pd.read_csv(csv_path)

    total_rows = len(df)
    unique_queries = df["query_id"].nunique()
    empty_store_rows = df[df["candidate_returned_by_faiss"] == False]
    candidate_rows = df[df["candidate_returned_by_faiss"] == True]

    passed_candidates = candidate_rows[candidate_rows["passed_retrieval_threshold"] == True]
    queries_with_retrieval = passed_candidates["query_id"].unique()

    audit_summary = {
        "total_telemetry_rows": int(total_rows),
        "unique_benchmark_queries": int(unique_queries),
        "empty_store_query_rows": int(len(empty_store_rows)),
        "faiss_candidates_evaluated": int(len(candidate_rows)),
        "accepted_retrieval_candidates": int(len(passed_candidates)),
        "queries_with_active_retrieval": int(len(queries_with_retrieval)),
        "queries_with_active_retrieval_list": sorted(list(queries_with_retrieval)),
        "query_retrieval_coverage_pct": round((len(queries_with_retrieval) / unique_queries) * 100.0, 2),
    }

    print("=" * 70)
    print("ARMG PHASE 3: TELEMETRY COVERAGE AUDIT (Section 9)")
    print("=" * 70)
    print(f"Total Telemetry Rows:              {audit_summary['total_telemetry_rows']}")
    print(f"Unique Benchmark Queries:          {audit_summary['unique_benchmark_queries']}")
    print(f"Empty-Store Query Evaluations:     {audit_summary['empty_store_query_rows']} (Q01-Q04)")
    print(f"FAISS Candidates Evaluated:        {audit_summary['faiss_candidates_evaluated']}")
    print(f"Accepted Retrieval Candidates:     {audit_summary['accepted_retrieval_candidates']} (S >= tau=0.50)")
    print(f"Queries with Active Retrieval:     {audit_summary['queries_with_active_retrieval']} / {unique_queries} ({audit_summary['query_retrieval_coverage_pct']}%)")
    print(f"Queries List:                      {audit_summary['queries_with_active_retrieval_list']}")

    # Integrity assertions
    assert audit_summary["total_telemetry_rows"] == 47, f"Expected 47 rows, got {audit_summary['total_telemetry_rows']}"
    assert audit_summary["unique_benchmark_queries"] == 25, f"Expected 25 queries, got {audit_summary['unique_benchmark_queries']}"
    assert audit_summary["accepted_retrieval_candidates"] == 16, f"Expected 16 accepted candidates, got {audit_summary['accepted_retrieval_candidates']}"
    assert audit_summary["queries_with_active_retrieval"] == 12, f"Expected 12 queries, got {audit_summary['queries_with_active_retrieval']}"
    assert audit_summary["query_retrieval_coverage_pct"] == 48.0, f"Expected 48.0%, got {audit_summary['query_retrieval_coverage_pct']}"

    print("\nAUDIT VERDICT: PASSED - All counts and coverage strictly reconciled.")
    return audit_summary


if __name__ == "__main__":
    audit_telemetry_coverage()
