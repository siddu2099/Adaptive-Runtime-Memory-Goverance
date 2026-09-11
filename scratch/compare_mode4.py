import csv
from pathlib import Path

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
post_csv_path = repo_root / "benchmark" / "benchmark_results.csv"
pre_csv_path = repo_root / "benchmark" / "pre_remediation_results.csv"

def load_mode(path, mode_name):
    records = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["mode"] == mode_name:
                records[r["query_id"]] = r
    return records

post_m4 = load_mode(post_csv_path, "Mode 4 (Full ARMG)")
pre_m4 = load_mode(pre_csv_path, "Mode 4 (Full ARMG)")

print(f"{'QID':<5} | {'Pre Acc':<7} {'Post Acc':<8} | {'Pre Retr':<8} {'Post Retr':<9} | {'Pre Ret':<7} {'Post Ret':<8} | {'Post Adm':<22} | {'Post Reinf':<15}")
print("-" * 95)
for qid in sorted(post_m4.keys()):
    pre = pre_m4[qid]
    post = post_m4[qid]
    print(f"{qid:<5} | {pre['execution_accuracy']:<7} {post['execution_accuracy']:<8} | {pre['retry_count']:<8} {post['retry_count']:<9} | {pre['memory_retrieval_count']:<7} {post['memory_retrieval_count']:<8} | {str(post['memory_admission']):<22} | {str(post['memory_reinforcement']):<15}")
