import csv
import statistics
from pathlib import Path
from collections import defaultdict

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
seed42_csv = repo_root / "benchmark" / "seed42" / "benchmark_results.csv"
seed123_csv = repo_root / "benchmark" / "seed123" / "benchmark_results.csv"
seed999_csv = repo_root / "benchmark" / "seed999" / "benchmark_results.csv"
pre_csv = repo_root / "benchmark" / "pre_remediation_results.csv"

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

# 1. Mode 4 vs Mode 2 Detailed Calculations
def get_mode_data(rows, mode_name):
    return {r["query_id"]: r for r in rows if r["mode"] == mode_name}

m2_42 = get_mode_data(r42, "Mode 2 (Stateless Self-Correction)")
m4_42 = get_mode_data(r42, "Mode 4 (Full ARMG)")

m2_123 = get_mode_data(r123, "Mode 2 (Stateless Self-Correction)")
m4_123 = get_mode_data(r123, "Mode 4 (Full ARMG)")

m2_999 = get_mode_data(r999, "Mode 2 (Stateless Self-Correction)")
m4_999 = get_mode_data(r999, "Mode 4 (Full ARMG)")

print("=== TABLE B: MODE 4 VS MODE 2 QUERY COMPARISON (SEED 42 / 123 / 999) ===")
print(f"{'QID':<5} | {'M2 Out (Acc,Succ,Ret)':<22} | {'M4 Out (Acc,Succ,Ret)':<22} | {'PG Diff':<8} | {'Sem Diff':<8} | {'Ret Diff (M2-M4)':<16}")
print("-" * 90)

improved = []
worsened = []
unchanged = []
pg_diff_queries = []
sem_diff_queries = []
ret_diff_queries = []

for qid in sorted(m2_42.keys()):
    # across seeds
    m2_s = [int(m2_42[qid]["retry_count"]), int(m2_123[qid]["retry_count"]), int(m2_999[qid]["retry_count"])]
    m4_s = [int(m4_42[qid]["retry_count"]), int(m4_123[qid]["retry_count"]), int(m4_999[qid]["retry_count"])]
    
    m2_acc = int(m2_42[qid]["execution_accuracy"])
    m4_acc = int(m4_42[qid]["execution_accuracy"])
    
    m2_pg = m2_42[qid]["success"] == "True"
    m4_pg = m4_42[qid]["success"] == "True"
    
    pg_diff = "M4 +1" if (m4_pg and not m2_pg) else ("M2 +1" if (m2_pg and not m4_pg) else "Same")
    sem_diff = "M4 +1" if (m4_acc > m2_acc) else ("M2 +1" if (m2_acc > m4_acc) else "Same")
    
    avg_m2_ret = statistics.mean(m2_s)
    avg_m4_ret = statistics.mean(m4_s)
    ret_diff = round(avg_m2_ret - avg_m4_ret, 2)
    
    out_m2 = f"acc={m2_acc}, s={1 if m2_pg else 0}, r={avg_m2_ret}"
    out_m4 = f"acc={m4_acc}, s={1 if m4_pg else 0}, r={avg_m4_ret}"
    
    print(f"{qid:<5} | {out_m2:<22} | {out_m4:<22} | {pg_diff:<8} | {sem_diff:<8} | {ret_diff:<16}")
    
    if avg_m4_ret < avg_m2_ret or (m4_pg and not m2_pg) or (m4_acc > m2_acc):
        improved.append(qid)
    elif avg_m4_ret > avg_m2_ret or (m2_pg and not m4_pg) or (m2_acc > m4_acc):
        worsened.append(qid)
    else:
        unchanged.append(qid)
        
    if pg_diff != "Same":
        pg_diff_queries.append(qid)
    if sem_diff != "Same":
        sem_diff_queries.append(qid)
    if ret_diff != 0:
        ret_diff_queries.append((qid, ret_diff))

print(f"\nImproved Queries ({len(improved)}): {improved}")
print(f"Worsened Queries ({len(worsened)}): {worsened}")
print(f"Unchanged Queries ({len(unchanged)}): {unchanged}")
print(f"PG Success Diff Queries: {pg_diff_queries}")
print(f"Semantic Diff Queries: {sem_diff_queries}")
print(f"Retry Diff Queries: {ret_diff_queries}")

# 2. Effect Size Calculation
m2_ret_seeds = [0.44, 0.44, 0.40]
m4_ret_seeds = [0.28, 0.28, 0.28]

mean_m2_ret = statistics.mean(m2_ret_seeds)
mean_m4_ret = statistics.mean(m4_ret_seeds)

abs_red = mean_m2_ret - mean_m4_ret
rel_red = (abs_red / mean_m2_ret) * 100.0

print(f"\nRetry Reduction:")
print(f"  Mode 2 Mean Retries: {round(mean_m2_ret, 4)}")
print(f"  Mode 4 Mean Retries: {round(mean_m4_ret, 4)}")
print(f"  Absolute Reduction: {round(abs_red, 4)} retries/query")
print(f"  Relative Reduction: {round(rel_red, 2)}%")

# Per-seed reductions
for s_name, m2_v, m4_v in zip(["Seed 42", "Seed 123", "Seed 999"], m2_ret_seeds, m4_ret_seeds):
    d_abs = m2_v - m4_v
    d_rel = (d_abs / m2_v) * 100.0
    print(f"  {s_name}: M2={m2_v}, M4={m4_v} -> Abs Red={round(d_abs, 4)}, Rel Red={round(d_rel, 2)}%")

# 3. Latency & Token trade-off
m2_lat_seeds = [7360.37, 7187.05, 6901.61]
m4_lat_seeds = [8618.89, 8629.83, 8445.94]

mean_m2_lat = statistics.mean(m2_lat_seeds)
mean_m4_lat = statistics.mean(m4_lat_seeds)
lat_diff = mean_m4_lat - mean_m2_lat
lat_rel = (lat_diff / mean_m2_lat) * 100.0

m2_tok_seeds = [580.04, 580.04, 558.08]
m4_tok_seeds = [542.36, 542.40, 542.36]

mean_m2_tok = statistics.mean(m2_tok_seeds)
mean_m4_tok = statistics.mean(m4_tok_seeds)
tok_diff = mean_m2_tok - mean_m4_tok
tok_rel = (tok_diff / mean_m2_tok) * 100.0

print(f"\nLatency & Token Trade-off:")
print(f"  Mode 2 Latency: {round(mean_m2_lat, 2)} ms, Mode 4 Latency: {round(mean_m4_lat, 2)} ms")
print(f"  Latency Overhead in Mode 4: +{round(lat_diff, 2)} ms (+{round(lat_rel, 2)}%)")
print(f"  Mode 2 Tokens: {round(mean_m2_tok, 2)}, Mode 4 Tokens: {round(mean_m4_tok, 2)}")
print(f"  Token Savings in Mode 4: -{round(tok_diff, 2)} tokens (-{round(tok_rel, 2)}%)")

# 4. Memory Transfer Metrics
# Denominators:
# Total queries = 25
# Retrieval-bearing queries = 12
# Total retrieval events = 16
# Applied retrieved cases = ?
# Let's inspect applied cases:
# In initial generation: retrieved memories were formatted into the prompt context for all 12 queries.
# In repair: explicit applied_memory_id set on Q17.
# Reinforcement on Q17.
# Successful repair on Q17.
