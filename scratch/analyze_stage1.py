import csv
import json
import statistics
from pathlib import Path
from collections import defaultdict

repo_root = Path(r"c:\Users\siddu\Pictures\armg main")
post_csv_path = repo_root / "benchmark" / "benchmark_results.csv"
pre_csv_path = repo_root / "benchmark" / "pre_remediation_results.csv"

def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

post_rows = load_csv(post_csv_path)
pre_rows = load_csv(pre_csv_path)

def analyze_rows(rows, label):
    print(f"=== {label} (Total Rows: {len(rows)}) ===")
    modes = defaultdict(list)
    for r in rows:
        modes[r["mode"]].append(r)
    
    summary = {}
    for mode, m_rows in modes.items():
        total = len(m_rows)
        correct = sum(1 for r in m_rows if int(r["execution_accuracy"]) == 1)
        acc_pct = round((correct / total) * 100, 2)
        
        retries = [int(r["retry_count"]) for r in m_rows]
        mean_retries = round(statistics.mean(retries), 2)
        std_retries = round(statistics.stdev(retries), 2) if len(retries) > 1 else 0.0
        
        latencies = [float(r["latency_ms"]) for r in m_rows]
        mean_lat = round(statistics.mean(latencies), 2)
        std_lat = round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0
        
        tokens = [float(r["total_tokens"]) for r in m_rows if r.get("total_tokens") and r["total_tokens"] != "None"]
        mean_tok = round(statistics.mean(tokens), 2) if tokens else 0.0
        std_tok = round(statistics.stdev(tokens), 2) if len(tokens) > 1 else 0.0
        
        retrievals = [int(r["memory_retrieval_count"]) for r in m_rows if r.get("memory_retrieval_count") and r["memory_retrieval_count"] != "None"]
        total_ret = sum(retrievals)
        queries_with_ret = sum(1 for r in retrievals if r > 0)
        
        admissions = sum(1 for r in m_rows if r.get("memory_admission") in ("ADMITTED", "NAIVE_STORED"))
        reinforcements = sum(1 for r in m_rows if r.get("memory_admission") == "EXISTING_REINFORCED" or (r.get("memory_reinforcement") and r["memory_reinforcement"].startswith("mem-")))
        
        # Category breakdown
        cat_acc = defaultdict(lambda: {"correct": 0, "total": 0})
        for r in m_rows:
            cat_prefix = r["category"].split("—")[0].strip() if "—" in r["category"] else r["category"].split("-")[0].strip()
            cat_acc[cat_prefix]["total"] += 1
            if int(r["execution_accuracy"]) == 1:
                cat_acc[cat_prefix]["correct"] += 1
                
        summary[mode] = {
            "total": total,
            "correct": correct,
            "acc_pct": acc_pct,
            "mean_retries": mean_retries,
            "std_retries": std_retries,
            "mean_lat": mean_lat,
            "std_lat": std_lat,
            "mean_tok": mean_tok,
            "std_tok": std_tok,
            "total_ret": total_ret,
            "queries_with_ret": queries_with_ret,
            "admissions": admissions,
            "reinforcements": reinforcements,
            "cat_acc": dict(cat_acc)
        }
        print(f"Mode: {mode}")
        print(f"  Accuracy: {correct}/{total} ({acc_pct}%)")
        print(f"  Retries: {mean_retries} +/- {std_retries}")
        print(f"  Latency: {mean_lat} +/- {std_lat} ms")
        print(f"  Tokens: {mean_tok} +/- {std_tok}")
        print(f"  Retrieval Count: {total_ret} across {queries_with_ret} queries")
        print(f"  Admissions: {admissions}, Reinforcements: {reinforcements}")
        print(f"  Categories: {dict(cat_acc)}")
        print()
    return summary

print("Analyzing Post-Remediation...")
post_summary = analyze_rows(post_rows, "POST-REMEDIATION")

print("\nAnalyzing Pre-Remediation...")
pre_summary = analyze_rows(pre_rows, "PRE-REMEDIATION")
