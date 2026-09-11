import csv
from pathlib import Path

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
post_csv_path = repo_root / "benchmark" / "benchmark_results.csv"
pre_csv_path = repo_root / "benchmark" / "pre_remediation_results.csv"

def get_query(path, mode_name, qid):
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["mode"] == mode_name and r["query_id"] == qid:
                return r
    return None

print("=== Q19 INVESTIGATION (MODE 4) ===")
pre_q19 = get_query(pre_csv_path, "Mode 4 (Full ARMG)", "Q19")
post_q19 = get_query(post_csv_path, "Mode 4 (Full ARMG)", "Q19")

print(f"PRE-REMEDIATION Q19:")
print(f"  success: {pre_q19['success']}, exec_acc: {pre_q19['execution_accuracy']}, retries: {pre_q19['retry_count']}")
print(f"  val_failures: {pre_q19['validation_failures']}, exec_failures: {pre_q19['execution_failures']}")
print(f"  error_cat: {pre_q19['error_category']}, fail_reason: {pre_q19['failure_reason']}")
print(f"  final_sql:\n{pre_q19['final_sql']}")
print()
print(f"POST-REMEDIATION Q19:")
print(f"  success: {post_q19['success']}, exec_acc: {post_q19['execution_accuracy']}, retries: {post_q19['retry_count']}")
print(f"  val_failures: {post_q19['validation_failures']}, exec_failures: {post_q19['execution_failures']}")
print(f"  error_cat: {post_q19['error_category']}, fail_reason: {post_q19['failure_reason']}")
print(f"  final_sql:\n{post_q19['final_sql']}")
print(f"  gold_sql:\n{post_q19['gold_sql']}")

print("\n=== Q17 INVESTIGATION (MODE 4) ===")
pre_q17 = get_query(pre_csv_path, "Mode 4 (Full ARMG)", "Q17")
post_q17 = get_query(post_csv_path, "Mode 4 (Full ARMG)", "Q17")
print(f"PRE Q17: retries={pre_q17['retry_count']} ret={pre_q17['memory_retrieval_count']} adm={pre_q17['memory_admission']}")
print(f"POST Q17: retries={post_q17['retry_count']} ret={post_q17['memory_retrieval_count']} adm={post_q17['memory_admission']} reinf={post_q17['memory_reinforcement']}")
print(f"POST Q17 final_sql:\n{post_q17['final_sql']}")
print(f"POST Q17 gold_sql:\n{post_q17['gold_sql']}")
