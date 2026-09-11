import csv
import math
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

rows_42 = load_csv(seed42_csv)
rows_123 = load_csv(seed123_csv)
rows_999 = load_csv(seed999_csv)
rows_pre = load_csv(pre_csv)

def get_mode_stats(rows):
    by_mode = defaultdict(list)
    for r in rows:
        by_mode[r["mode"]].append(r)
        
    stats = {}
    for mode, m_rows in by_mode.items():
        total = len(m_rows)
        correct = sum(1 for r in m_rows if int(r["execution_accuracy"]) == 1)
        acc_pct = (correct / total) * 100.0
        
        pg_success = sum(1 for r in m_rows if r["success"] == "True")
        pg_success_pct = (pg_success / total) * 100.0
        
        retries = [int(r["retry_count"]) for r in m_rows]
        mean_retries = statistics.mean(retries)
        std_retries = statistics.stdev(retries) if len(retries) > 1 else 0.0
        
        latencies = [float(r["latency_ms"]) for r in m_rows]
        mean_lat = statistics.mean(latencies)
        std_lat = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        
        tokens = [float(r["total_tokens"]) for r in m_rows if r.get("total_tokens") and r["total_tokens"] != "None"]
        mean_tok = statistics.mean(tokens) if tokens else 0.0
        std_tok = statistics.stdev(tokens) if len(tokens) > 1 else 0.0
        
        retrievals = [int(r["memory_retrieval_count"]) for r in m_rows if r.get("memory_retrieval_count") and r["memory_retrieval_count"] != "None"]
        total_ret = sum(retrievals)
        queries_with_ret = sum(1 for r in retrievals if r > 0)
        
        admissions = sum(1 for r in m_rows if r.get("memory_admission") in ("ADMITTED", "NAIVE_STORED"))
        reinforcements = sum(1 for r in m_rows if r.get("memory_admission") == "EXISTING_REINFORCED" or (r.get("memory_reinforcement") and r["memory_reinforcement"].startswith("mem-")))
        
        if "Mode 1" in mode or "Mode 2" in mode:
            final_store = 0
        elif "Mode 3" in mode:
            final_store = admissions
        else:
            final_store = 3
            
        stats[mode] = {
            "mode": mode,
            "total": total,
            "correct": correct,
            "acc_pct": round(acc_pct, 2),
            "pg_success": pg_success,
            "pg_success_pct": round(pg_success_pct, 2),
            "mean_retries": round(mean_retries, 2),
            "std_retries": round(std_retries, 2),
            "mean_lat": round(mean_lat, 2),
            "std_lat": round(std_lat, 2),
            "mean_tok": round(mean_tok, 2),
            "std_tok": round(std_tok, 2),
            "total_ret": total_ret,
            "queries_with_ret": queries_with_ret,
            "admissions": admissions,
            "reinforcements": reinforcements,
            "final_store": final_store,
        }
    return stats

stats_42 = get_mode_stats(rows_42)
stats_123 = get_mode_stats(rows_123)
stats_999 = get_mode_stats(rows_999)
stats_pre = get_mode_stats(rows_pre)

print("=== SEED 123 STATS ===")
for m, s in stats_123.items():
    print(m, s)

print("\n=== SEED 999 STATS ===")
for m, s in stats_999.items():
    print(m, s)

# 3-Seed Aggregation
modes_ordered = [
    "Mode 1 (Zero-Shot)",
    "Mode 2 (Stateless Self-Correction)",
    "Mode 3 (Naive Vector RAG)",
    "Mode 4 (Full ARMG)",
    "Mode 5 (ARMG - Negative Constraints)",
    "Mode 6 (ARMG - Temporal Decay)",
]

print("\n=== 3-SEED AGGREGATE SUMMARY ===")
agg = {}
for m in modes_ordered:
    s42 = stats_42[m]
    s123 = stats_123[m]
    s999 = stats_999[m]
    
    accs = [s42["acc_pct"], s123["acc_pct"], s999["acc_pct"]]
    pg_succs = [s42["pg_success_pct"], s123["pg_success_pct"], s999["pg_success_pct"]]
    rets = [s42["mean_retries"], s123["mean_retries"], s999["mean_retries"]]
    lats = [s42["mean_lat"], s123["mean_lat"], s999["mean_lat"]]
    toks = [s42["mean_tok"], s123["mean_tok"], s999["mean_tok"]]
    
    mean_acc = round(statistics.mean(accs), 2)
    sd_acc = round(statistics.stdev(accs), 2)
    
    mean_pg = round(statistics.mean(pg_succs), 2)
    sd_pg = round(statistics.stdev(pg_succs), 2)
    
    mean_ret = round(statistics.mean(rets), 2)
    sd_ret = round(statistics.stdev(rets), 2)
    
    mean_lat = round(statistics.mean(lats), 2)
    sd_lat = round(statistics.stdev(lats), 2)
    
    mean_tok = round(statistics.mean(toks), 2)
    sd_tok = round(statistics.stdev(toks), 2)
    
    agg[m] = {
        "acc_mean_sd": f"{mean_acc}% ± {sd_acc}%",
        "pg_mean_sd": f"{mean_pg}% ± {sd_pg}%",
        "ret_mean_sd": f"{mean_ret} ± {sd_ret}",
        "lat_mean_sd": f"{mean_lat} ± {sd_lat} ms",
        "tok_mean_sd": f"{mean_tok} ± {sd_tok}",
        "raw": {
            "accs": accs,
            "rets": rets,
            "lats": lats,
            "toks": toks,
        }
    }
    print(f"{m}:")
    print(f"  ExecAcc: {mean_acc}% ± {sd_acc}% (raw: {accs})")
    print(f"  PG Success: {mean_pg}% ± {sd_pg}% (raw: {pg_succs})")
    print(f"  Retries: {mean_ret} ± {sd_ret} (raw: {rets})")
    print(f"  Latency: {mean_lat} ± {sd_lat} ms (raw: {lats})")
    print(f"  Tokens: {mean_tok} ± {sd_tok} (raw: {toks})")
