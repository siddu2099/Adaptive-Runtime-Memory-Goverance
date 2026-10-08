"""
Superseded in Phase 5: Delegated to canonical master generator.
Authoritative Canonical Generator: scripts/generate_results.py

This wrapper ensures backwards compatibility for existing invocations while
guaranteeing that exactly ONE calculation path generates all LaTeX tables.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_results import (
    compute_all_results_metrics,
    generate_publication_tables,
)

def generate_tables():
    print("[SUPERSEDED GENERATOR] Delegating table generation to canonical pipeline: scripts/generate_results.py")
    results = compute_all_results_metrics()
    generated = generate_publication_tables(results, output_dir=REPO_ROOT / "manuscript/tables")
    print(f"Canonical pipeline generated {len(generated)} tables successfully.")
    return generated

if __name__ == '__main__':
    generate_tables()
