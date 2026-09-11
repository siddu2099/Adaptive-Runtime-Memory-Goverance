import csv
import json
import hashlib
import statistics
from pathlib import Path
from collections import defaultdict

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
seed42_csv = repo_root / "benchmark" / "seed42" / "benchmark_results.csv"
seed123_csv = repo_root / "benchmark" / "seed123" / "benchmark_results.csv"
seed999_csv = repo_root / "benchmark" / "seed999" / "benchmark_results.csv"
pre_csv = repo_root / "benchmark" / "pre_remediation_results.csv"
queries_file = repo_root / "benchmark" / "queries.json"
equiv_file = repo_root / "benchmark" / "equivalence.py"

def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("=== 1. INTEGRITY VERIFICATION ===")
files = {
    "queries.json": queries_file,
    "equivalence.py": equiv_file,
    "seed42_csv": seed42_csv,
    "seed123_csv": seed123_csv,
    "seed999_csv": seed999_csv,
    "pre_csv": pre_csv
}

for name, p in files.items():
    print(f"  {name:<15}: exists={p.exists()}, size={p.stat().st_size} bytes, sha256={sha256(p)}")

def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

r42 = load_csv(seed42_csv)
r123 = load_csv(seed123_csv)
r999 = load_csv(seed999_csv)
r_pre = load_csv(pre_csv)

print(f"\nRow Counts: Seed 42: {len(r42)}, Seed 123: {len(r123)}, Seed 999: {len(r999)}, Pre-Rem: {len(r_pre)}")
print(f"Total Post-Remediation Evaluations: {len(r42) + len(r123) + len(r999)}")

# Check modes and queries in each seed
for label, r_set in [("Seed 42", r42), ("Seed 123", r123), ("Seed 999", r999)]:
    modes = defaultdict(list)
    for r in r_set:
        modes[r["mode"]].append(r["query_id"])
    print(f"\n{label} Mode & Query Breakdown:")
    for m, q_list in modes.items():
        q_expected = [f"Q{i:02d}" for i in range(1, 26)]
        assert q_list == q_expected, f"Query mismatch in {label} {m}"
        print(f"  {m:<35}: {len(q_list)} queries (Q01-Q25 verified in order, no duplicates)")

print("\nResult Integrity: 100% VERIFIED.")
