import csv
from pathlib import Path

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
seed42_csv = repo_root / "benchmark" / "seed42" / "benchmark_results.csv"
seed123_csv = repo_root / "benchmark" / "seed123" / "benchmark_results.csv"
seed999_csv = repo_root / "benchmark" / "seed999" / "benchmark_results.csv"

def load_mode4(path):
    recs = {}
    with open(path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["mode"] == "Mode 4 (Full ARMG)":
                recs[r["query_id"]] = r
    return recs

m4_42 = load_mode4(seed42_csv)
m4_123 = load_mode4(seed123_csv)
m4_999 = load_mode4(seed999_csv)

print("=== MODE 4 QUERY-LEVEL MEMORY TRANSFER TABLE (SEED 42 / 123 / 999) ===")
print(f"{'QID':<5} | {'Retrieved?':<10} | {'RetCount':<8} | {'Applied?':<8} | {'Repair Occurred?':<16} | {'Repair Succ?':<12} | {'Reinforced?':<12} | {'ExecAcc':<7} | {'PG Succ':<7}")
print("-" * 105)

for qid in sorted(m4_42.keys()):
    r42 = m4_42[qid]
    r123 = m4_123[qid]
    r999 = m4_999[qid]
    
    ret_count = int(r42["memory_retrieval_count"])
    retrieved = "Yes" if ret_count > 0 else "No"
    
    # In ARMG workflow:
    # Retrieved memories are injected into state['retrieved_memories'].
    # When repair occurs:
    # - if repair succeeds using an existing memory: applied_memory_id is set and reinforced!
    # - if repair occurs with retries > 0:
    retries = int(r42["retry_count"])
    repair_occurred = "Yes" if retries > 0 else "No"
    repair_succ = "Yes" if (retries > 0 and r42["success"] == "True") else ("No" if retries > 0 else "N/A")
    
    reinforced = r42.get("memory_reinforcement") or "No"
    if reinforced != "No":
        applied = "Yes (mem)"
    elif ret_count > 0:
        applied = "Injected"
    else:
        applied = "No"
        
    acc = r42["execution_accuracy"]
    pg_s = r42["success"]
    
    print(f"{qid:<5} | {retrieved:<10} | {ret_count:<8} | {applied:<8} | {repair_occurred:<16} | {repair_succ:<12} | {reinforced:<12} | {acc:<7} | {pg_s:<7}")
