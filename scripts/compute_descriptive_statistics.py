"""
Superseded in Phase 5: Delegated to canonical master generator.
Authoritative Canonical Generator: scripts/generate_results.py

This wrapper ensures backwards compatibility for existing invocations while
guaranteeing that exactly ONE calculation path generates statistical summaries.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_results import (
    compute_all_results_metrics,
    generate_summary_artifacts,
)

def compute_descriptive_stats():
    print("[SUPERSEDED GENERATOR] Delegating descriptive statistics to canonical pipeline: scripts/generate_results.py")
    results = compute_all_results_metrics()
    generated = generate_summary_artifacts(results)
    print(f"Canonical pipeline generated {len(generated)} statistical summary artifacts successfully.")
    return results["stats_dict"]

if __name__ == '__main__':
    compute_descriptive_stats()
