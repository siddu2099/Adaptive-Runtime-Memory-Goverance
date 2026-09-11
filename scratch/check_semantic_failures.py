import csv
from pathlib import Path

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
seed42_csv = repo_root / "benchmark" / "seed42" / "benchmark_results.csv"

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["mode"] == "Mode 4 (Full ARMG)"]

rows = load_csv(seed42_csv)

divergent = [r for r in rows if r["success"] == "True" and r["execution_accuracy"] == "0"]

print("=== TABLE D: SEMANTIC FAILURE ANALYSIS (7 DIVERGENT QUERIES) ===")
for r in divergent:
    qid = r["query_id"]
    cat = r["category"].split("—")[0].strip() if "—" in r["category"] else r["category"].split("-")[0].strip()
    print(f"\n[{qid}] ({cat}) Question: {r['question']}")
    print(f"  Gold SQL: {r['gold_sql']}")
    print(f"  Gen SQL:  {r['final_sql'].replace(chr(10), ' ')}")
