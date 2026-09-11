import csv
from pathlib import Path
from collections import defaultdict

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
seed42_csv = repo_root / "benchmark" / "seed42" / "benchmark_results.csv"
seed123_csv = repo_root / "benchmark" / "seed123" / "benchmark_results.csv"
seed999_csv = repo_root / "benchmark" / "seed999" / "benchmark_results.csv"

def load_rows(path):
    d = defaultdict(dict)
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d[r["mode"]][r["query_id"]] = r
    return d

d42 = load_rows(seed42_csv)
d123 = load_rows(seed123_csv)
d999 = load_rows(seed999_csv)

modes = [
    "Mode 1 (Zero-Shot)",
    "Mode 2 (Stateless Self-Correction)",
    "Mode 3 (Naive Vector RAG)",
    "Mode 4 (Full ARMG)",
    "Mode 5 (ARMG - Negative Constraints)",
    "Mode 6 (ARMG - Temporal Decay)",
]

print("=== CROSS-SEED QUERY-LEVEL VARIANCE (SEEDS 42, 123, 999) ===")
for m in modes:
    print(f"\n--- {m} ---")
    divergences = []
    for qid in [f"Q{i:02d}" for i in range(1, 26)]:
        r42 = d42[m][qid]
        r123 = d123[m][qid]
        r999 = d999[m][qid]
        
        accs = (r42["execution_accuracy"], r123["execution_accuracy"], r999["execution_accuracy"])
        rets = (r42["retry_count"], r123["retry_count"], r999["retry_count"])
        succs = (r42["success"], r123["success"], r999["success"])
        
        if len(set(accs)) > 1 or len(set(rets)) > 1 or len(set(succs)) > 1:
            divergences.append((qid, accs, rets, succs))
            print(f"  {qid}: accs={accs} | retries={rets} | success={succs}")
    if not divergences:
        print("  100% IDENTICAL across all 3 seeds for all 25 queries!")
