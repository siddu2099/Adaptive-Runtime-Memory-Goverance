import csv
from pathlib import Path
from collections import defaultdict

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
post_csv_path = repo_root / "benchmark" / "benchmark_results.csv"
pre_csv_path = repo_root / "benchmark" / "pre_remediation_results.csv"

def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

post_rows = load_csv(post_csv_path)
pre_rows = load_csv(pre_csv_path)

print("=== EXECUTION SUCCESS vs RELATIONAL EQUIVALENCE (POST-REMEDIATION) ===")
modes = defaultdict(list)
for r in post_rows:
    modes[r["mode"]].append(r)

for mode, r_list in modes.items():
    success_count = sum(1 for r in r_list if r["success"] == "True")
    exec_acc_count = sum(1 for r in r_list if r["execution_accuracy"] == "1")
    executable_non_equiv = sum(1 for r in r_list if r["success"] == "True" and r["execution_accuracy"] == "0")
    print(f"{mode}:")
    print(f"  PostgreSQL Success (is_success=True): {success_count}/25 ({round(success_count/25*100, 1)}%)")
    print(f"  Semantic Accuracy (exec_acc=1):        {exec_acc_count}/25 ({round(exec_acc_count/25*100, 1)}%)")
    print(f"  Executable but Non-Equivalent:        {executable_non_equiv}/25")

print("\n=== MEMORY RETRIEVAL DETAILS (MODE 4, 5, 6 POST-REMEDIATION) ===")
for m_key in ["Mode 4 (Full ARMG)", "Mode 5 (ARMG - Negative Constraints)", "Mode 6 (ARMG - Temporal Decay)"]:
    m_records = modes[m_key]
    print(f"\n--- {m_key} ---")
    for r in m_records:
        ret_count = int(r["memory_retrieval_count"])
        adm = r["memory_admission"]
        reinf = r["memory_reinforcement"]
        if ret_count > 0 or adm or reinf:
            print(f"  {r['query_id']}: ret_count={ret_count} | adm={adm} | reinf={reinf} | retries={r['retry_count']} | acc={r['execution_accuracy']} | succ={r['success']}")

print("\n=== Q01-Q25 ACCURACY MATRIX ACROSS ALL 6 MODES (POST) ===")
q_matrix = defaultdict(dict)
for r in post_rows:
    m_short = r["mode"].split("(")[0].strip().replace("Mode ", "M")
    q_matrix[r["query_id"]][m_short] = f"{r['execution_accuracy']}(s={1 if r['success']=='True' else 0},r={r['retry_count']})"

print(f"{'QID':<5} | {'M1':<12} | {'M2':<12} | {'M3':<12} | {'M4':<12} | {'M5':<12} | {'M6':<12}")
print("-" * 85)
for qid in sorted(q_matrix.keys()):
    row = q_matrix[qid]
    print(f"{qid:<5} | {row.get('M1',''):<12} | {row.get('M2',''):<12} | {row.get('M3',''):<12} | {row.get('M4',''):<12} | {row.get('M5',''):<12} | {row.get('M6',''):<12}")
