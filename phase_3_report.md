# ARMG Phase 3: Benchmark Re-Execution & Statistical Hardening Report

**Project**: Adaptive Runtime Memory Governance (ARMG) for LLM-Based Text-to-SQL Systems  
**Evaluation Phase**: Major Phase 3 (Benchmark Re-Execution & Statistical Hardening)  
**Execution Timestamp**: 2026-10-06T00:35:00+05:30  
**Repository Branch**: `armg-hardening`  
**Git HEAD Commit**: `40d36a3980e5f152a8eadbfa021b833f587d7b3b`  

---

## 1. Executive Summary & Phase 3 Gate Verdict

Major Phase 3 establishes a **clean, fully traceable, multi-seed empirical benchmark dataset** for ARMG using the approved frozen implementation, verified live execution environment, and rigorous descriptive statistical methods. 

All non-negotiable scientific rules, isolation requirements, seed plumbing verification, real FAISS telemetry lineages, and automated consistency checks have been executed and verified programmatically.

### Phase 3 Acceptance Gate Verdict

```text
PHASE 3 — PASS
SAFE TO BEGIN FULL PROJECT FORENSIC AUDIT 3
```

All required acceptance criteria are strictly satisfied with zero P0/P1 defects, zero fabricated data, zero manual entries, and 100% test passing (288/288 passed).

---

## 2. Live Experimental Environment Verification

The execution environment was audited and recorded programmatically to [`benchmark/environment.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/environment.json) via [`scripts/record_environment.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/record_environment.py).

### Environment Audit Matrix

| Component | Target Requirement | Measured / Active Runtime State | Verification Status |
| :--- | :--- | :--- | :---: |
| **Operating System** | Windows 11 64-bit | Windows 11 Build 10.0.26300 (AMD64) | **PASS** |
| **Python Runtime** | Python $\ge 3.11$ | Python 3.13.2 64-bit (`python.exe`) | **PASS** |
| **FAISS Vector Library** | `faiss` / `faiss-cpu` | `faiss-cpu` 1.14.3 | **PASS** |
| **PyTorch** | Standalone C++ wheel | N/A (`faiss-cpu` standalone binary) | **PASS** |
| **SQLGlot** | SQL Parser & Transpiler | 30.12.0 | **PASS** |
| **LangGraph** | Workflow Orchestration | 1.2.5 | **PASS** |
| **psycopg2** | PostgreSQL Driver | 2.9.11 (`dt dec pq3 ext lo64`) | **PASS** |
| **Pydantic** | Schema & Model Validation | 2.12.5 | **PASS** |
| **NumPy** | Numerical Computation | 2.4.1 | **PASS** |
| **PostgreSQL Database** | PostgreSQL Server | PostgreSQL 18.1 on x86_64-windows (msvc-19.44, 64-bit) | **PASS** |
| **PostgreSQL Port & DB** | Port 5432, `armg_db` | Connected, port 5432, db `armg_db` | **PASS** |
| **PostgreSQL Catalog** | 4 Canonical Warehouse Tables | `dim_geography` (6), `dim_product` (8), `dim_time` (365), `fact_sales_performance` (2000) | **PASS** |
| **Ollama Daemon** | Local Daemon on port 11434 | Online (`http://localhost:11434`, v0.32.15) | **PASS** |
| **Generation Model** | `qwen2.5:7b-instruct` | Present, verified via `/api/tags` and inference test | **PASS** |
| **Embedding Model** | `nomic-embed-text` | Present (768-dim), verified via `/api/tags` and embed test | **PASS** |

Environment suite verification executed: `pytest tests/test_env.py` $\to$ **12 passed, 0 failed, 0 skipped** in 21.64s.

---

## 3. Non-Negotiable Scientific Rules Compliance

1. **Rule 1 — Do Not Change the Algorithm**:
   - FAISS metric remains `IndexFlatL2` wrapped in `IndexIDMap2`.
   - Normalization policy remains unit-L2 normalization ($\|v\|_2 = 1.0$) for 768-dim embeddings.
   - Similarity formula remains strictly $S = \frac{1}{1 + d^2}$.
   - Retrieval similarity threshold remains $\tau = 0.50$; admission utility threshold remains $\theta = 0.25$.
   - Governance equations, tier weights, temporal decay rate ($\lambda = 0.05$), LangGraph topology, and AST safety policies were completely frozen and unmodified.
2. **Rule 2 — Never Fabricate or Reconstruct Empirical Results**:
   - Zero numbers in any table, markdown, CSV, or LaTeX artifact are manually typed or synthetic.
   - Every single observation originates from executable benchmark runs.
3. **Rule 3 — Preserve Raw Evidence**:
   - Built canonical hierarchy in [`benchmark/raw/`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/raw) containing 18 mode-seed subdirectories and 75 raw evidence artifacts.

---

## 4. Run Isolation & State Leakage Verification

To guarantee that no memory, index state, runtime context, or telemetry leaks between seeds or modes:
- **Clean Component Instantiation**: Every mode execution creates a fresh `FAISSMemoryStore()`, a fresh `MemoryGovernanceEngine()`, fresh `SQLGenerator` and `RepairSQLGenerator` instances, and a fresh `ARMGRepairWorkflow()` graph.
- **Store Initial State**: For Mode 1 and Mode 2, no memory is used. For Mode 3, 4, 5, 6, memory stores always start with count = 0.
- **Empty-Store Retrieval Semantics**: In Mode 4, queries Q01–Q04 evaluate against an empty store, producing explicit null-candidate telemetry (`candidate_returned_by_faiss = False`, null distance/similarity).
- **Post-Run State Verification**: Terminal memory counts are verified post-execution (Mode 4 plateau at 3 memories; Mode 3 uninhibited growth to 23 memories).

---

## 5. Multi-Seed Execution & Seed Plumbing Verification

### Seed Plumbing Proof

The project uses approved seeds: `42`, `123`, and `999`.

Seed propagation was verified at the code and unit-test level:
```text
Configured Seed (int)
        ↓
SQLGenerator(seed=s) / RepairSQLGenerator(seed=s)
        ↓
options["seed"] = self.seed injected into Ollama payload
        ↓
requests.post(f"{base_url}/api/generate", json={..., "options": {"temperature": 0.0, "seed": seed}})
        ↓
Recorded in QueryBenchmarkRecord.seed and raw run metadata
```

- Verified via unit suite: [`tests/unit/test_seed_plumbing.py`](file:///c:/Users/siddu/Pictures/armg%20main/tests/unit/test_seed_plumbing.py) $\to$ **4 passed**.
- Because `temperature = 0.0`, repeated runs are treated as **reproducibility and stability verification checks across runtime invocations**, not as a high-variance stochastic distribution.

---

## 6. Experimental Modes Definitions

| Mode | Name | Memory Store | FAISS Retrieval | Governance Engine | Strict Negative Constraints | Temporal Decay |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mode 1** | Monolithic Zero-Shot | Disabled | Disabled | Disabled | Disabled | Disabled |
| **Mode 2** | Stateless Self-Correction | Disabled | Disabled | Disabled | Enabled (in prompt) | Disabled |
| **Mode 3** | Naive Vector RAG | Naive Store (all admitted) | Enabled (Top-3, unthresholded) | Disabled | Disabled | Disabled |
| **Mode 4** | Full ARMG Architecture | FAISS IndexFlatL2 | Enabled ($\tau = 0.50$) | Governed ($\theta = 0.25$) | Enabled | Active ($\lambda = 0.05$) |
| **Mode 5** | ARMG - Negative Constraints | FAISS IndexFlatL2 | Enabled ($\tau = 0.50$) | Governed ($\theta = 0.25$) | Disabled | Active ($\lambda = 0.05$) |
| **Mode 6** | ARMG - Temporal Decay | FAISS IndexFlatL2 | Enabled ($\tau = 0.50$) | Governed ($\theta = 0.25$) | Enabled | Disabled ($\lambda = 0.0$) |

---

## 7. Raw Evidence Hierarchy & Preservation

All raw benchmark execution evidence has been structured and preserved in [`benchmark/raw/`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/raw) generated by [`scripts/build_raw_benchmark_hierarchy.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/build_raw_benchmark_hierarchy.py):

```text
benchmark/
    raw/
        seed_42/
            mode_1/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json }
            mode_2/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json }
            mode_3/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json, retrieval_telemetry.csv }
            mode_4/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json, retrieval_telemetry.csv }
            mode_5/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json }
            mode_6/ { per_query_results.csv, execution_log.jsonl, environment.json, run_metadata.json }
        seed_123/
            mode_1/ ... mode_6/
        seed_999/
            mode_1/ ... mode_6/
```

Total: **18 mode directories, 75 raw evidence files, 450 query evaluations**.

---

## 8. Live FAISS Retrieval Telemetry & Geometry

For Mode 4, FAISS retrieval telemetry is captured directly from the execution path in [`memory/telemetry.py`](file:///c:/Users/siddu/Pictures/armg%20main/memory/telemetry.py):

$$\text{Query Vector } \mathbf{q} \in \mathbb{R}^{768}, \quad \|\mathbf{q}\|_2 = 1.0$$
$$d^2 = \|\mathbf{q} - \mathbf{v}\|_2^2 \in [0, 4]$$
$$S = \frac{1}{1 + d^2} \in [0.20, 1.0]$$

Every candidate returned by `faiss.IndexFlatL2.search()` is recorded prior to threshold or lifecycle filtering.

---

## 9. Telemetry Coverage Audit

Executed via [`scripts/audit_telemetry_coverage.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/audit_telemetry_coverage.py).

### Telemetry Entity Disambiguation

| Metric / Entity | Value | Exact Definition |
| :--- | :---: | :--- |
| **Total Telemetry Rows** | **47** | Total individual lines in `benchmark/retrieval_telemetry.csv`. |
| **Unique Benchmark Queries** | **25** | Total queries in corpus (Q01 to Q25). |
| **Empty-Store Queries** | **4** | Q01–Q04: Store size = 0; FAISS search skipped; explicit null logged. |
| **FAISS Candidates Evaluated** | **43** | Total candidate neighbors returned by FAISS search across Q05–Q25. |
| **Accepted Candidate Memories** | **16** | Candidates satisfying $S \ge \tau = 0.50$ ($d^2 \le 1.0$). |
| **Distinct Retrieval Queries** | **12** | Distinct queries where $\ge 1$ candidate was admitted for prompt injection. |
| **Retrieval Query Coverage** | **48.0%** | $\frac{12 \text{ queries}}{25 \text{ queries}} = 48.0\%$. |

Queries with active retrieval: `['Q08', 'Q10', 'Q16', 'Q17', 'Q18', 'Q19', 'Q20', 'Q21', 'Q22', 'Q23', 'Q24', 'Q25']`.

---

## 10. Multi-Seed Descriptive Statistical Analysis

Executed via [`scripts/compute_descriptive_statistics.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/compute_descriptive_statistics.py), serialized to [`benchmark/statistical_summary.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/statistical_summary.json) and [`benchmark/statistical_summary.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/statistical_summary.csv).

Sample size $n = 3$ runs; $N = 75$ total query evaluations per mode ($450$ total evaluations across the benchmark). Standard deviations are computed as sample standard deviations with Bessel's correction ($\text{ddof} = 1$).

### Multi-Seed Comprehensive Descriptive Statistics Table

| Mode | PG Success (Num / Den) | PG Success Mean $\pm$ Std | Relational Acc (Num / Den) | Relational Acc Mean $\pm$ Std | Mean Retries $\pm$ Std | Mean Latency (ms) $\pm$ Std | Mean Tokens $\pm$ Std | Final Store Size |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mode 1 (Zero-Shot)** | 57 / 75 | $76.00\% \pm 0.00\%$ | 43 / 75 | $57.33\% \pm 2.31\%$ | $0.00 \pm 0.00$ | $5,087.73 \pm 210.33$ | $378.00 \pm 0.00$ | 0 |
| **Mode 2 (Stateless Self-Corr)** | 69 / 75 | $92.00\% \pm 0.00\%$ | 51 / 75 | $68.00\% \pm 0.00\%$ | $0.43 \pm 0.02$ | $7,149.68 \pm 231.65$ | $572.72 \pm 0.00$ | 0 |
| **Mode 3 (Naive Vector RAG)** | 69 / 75 | $92.00\% \pm 0.00\%$ | 51 / 75 | $68.00\% \pm 0.00\%$ | $0.00 \pm 0.00$ | $6,844.01 \pm 56.89$ | $655.48 \pm 0.00$ | 23 |
| **Mode 4 (Full ARMG)** | 72 / 75 | $96.00\% \pm 0.00\%$ | 51 / 75 | $68.00\% \pm 0.00\%$ | $0.28 \pm 0.00$ | $8,564.89 \pm 103.15$ | $542.37 \pm 0.00$ | 3 |
| **Mode 5 (ARMG − NegConst)** | 72 / 75 | $96.00\% \pm 0.00\%$ | 51 / 75 | $68.00\% \pm 0.00\%$ | $0.36 \pm 0.00$ | $8,941.29 \pm 108.68$ | $560.12 \pm 0.00$ | 3 |
| **Mode 6 (ARMG with $\lambda=0$)** | 71 / 75 | $94.67\% \pm 2.31\%$ | 51 / 75 | $68.00\% \pm 0.00\%$ | $0.37 \pm 0.02$ | $9,036.96 \pm 178.55$ | $568.44 \pm 0.00$ | 3 |

### Per-Seed Results Breakdown

- **Seed 42**:
  - Mode 1: 19/25 succ (76.0%), 14/25 acc (56.0%)
  - Mode 2: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 3: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 4: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 5: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 6: 23/25 succ (92.0%), 17/25 acc (68.0%)
- **Seed 123**:
  - Mode 1: 19/25 succ (76.0%), 14/25 acc (56.0%)
  - Mode 2: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 3: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 4: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 5: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 6: 24/25 succ (96.0%), 17/25 acc (68.0%)
- **Seed 999**:
  - Mode 1: 19/25 succ (76.0%), 15/25 acc (60.0%)
  - Mode 2: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 3: 23/25 succ (92.0%), 17/25 acc (68.0%)
  - Mode 4: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 5: 24/25 succ (96.0%), 17/25 acc (68.0%)
  - Mode 6: 24/25 succ (96.0%), 17/25 acc (68.0%)

---

## 11. Metric Lineage & Automated Perturbation Proof

Verified via [`scripts/test_benchmark_lineage.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/test_benchmark_lineage.py).

### Automated Perturbation Test Mechanics

1. Seed CSVs were copied to a temporary isolated sandbox (`scratch/benchmark_lineage_test/`).
2. Downstream aggregations and LaTeX table strings were computed.
3. In Seed 42, Mode 4, Q01, exactly one record was perturbed:
   - `latency_ms`: $3280.707 \to 8280.707$ ($+5000.0$ ms)
   - `success`: $\text{True} \to \text{False}$
   - `execution_accuracy`: $1 \to 0$
4. Downstream metrics recomputed:
   - `exec_acc`: $68.00\% \to 66.67\%$ ($\Delta = -1.33\%$, matching theoretical $\frac{-4.0\%}{3}$)
   - `exec_succ`: $96.00\% \to 94.67\%$ ($\Delta = -1.33\%$, matching theoretical $\frac{-4.0\%}{3}$)
   - `latency_ms`: $8564.89 \to 8631.55$ ms ($\Delta = +66.67$ ms, matching theoretical $\frac{5000 / 25}{3}$)
   - Generated LaTeX table strings changed dynamically to reflect perturbed numbers.
5. Canonical benchmark files remained 100% untouched.

**Verdict: PASS**. Direct mathematical lineage is proven end-to-end.

---

## 12. Research Claim Audit

| Result / Claim | Classification | Justification & Provenance |
| :--- | :---: | :--- |
| **Figure 3 Post-Remediation Telemetry** | **EMPIRICAL** | Captured directly from live FAISS `IndexFlatL2.search()` with normalized embeddings. |
| **Figure 3 Pre-Remediation Baseline ($S \approx 0.0035$)** | **DERIVED / NON-EMPIRICAL** | Derived mathematically from unnormalized vector norm ($\|v\| \approx 19.8$, $d^2 \approx 280$). Clearly footnoted. |
| **Figure 4 Mode 1–6 Success & Accuracy** | **EMPIRICAL** | Computed programmatically from 450 live PostgreSQL executions across seeds 42, 123, 999. |
| **Figure 5 Trade-Off Profile Deltas** | **EMPIRICAL** | Derived from raw benchmark measurements comparing Mode 4 against Mode 2. |
| **Figure 6 Memory Store Trajectories** | **EMPIRICAL** | Derived from live memory admission decisions during sequential query execution. |
| **Pre-Remediation Synthetic Retrieval Data** | **QUARANTINED** | Isolated and quarantined from publication artifacts. |

---

## 13. Temporal Decay & Elapsed Execution

- The primary benchmark executes queries over elapsed real time (~25 queries over ~3–5 minutes per mode).
- Memory half-life decay ($\lambda = 0.05$ per epoch) is epoch-based. Within the 25-query span, admitted memories remain active and do not degrade prematurely.
- In compliance with Section 16, **zero artificial time increments or synthetic epochs were injected into the primary benchmark**.
- The primary benchmark honestly reflects that temporal decay remains unexercised over short single-session workloads. Mode 6 ($\lambda = 0$) serves as the controlled ablation.

---

## 14. Fresh Test Suite Reconciled Execution Counts

Executed fresh: `pytest -q` on Python 3.13.2 Windows 11.

```text
================================ test session starts ================================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\siddu\Pictures\armg main
plugins: anyio-4.8.0, langsmith-0.8.16, asyncio-1.4.0
collected 288 items

288 passed, 2 warnings in 58.78s
```

### Breakdown by Suite

- `tests/unit/`: **271 passed** (including new `test_phase3_benchmark_reproducibility.py` and `test_seed_plumbing.py`)
- `tests/integration/`: **5 passed** (all live PostgreSQL integration tests)
- `tests/test_env.py`: **12 passed** (all environment, Ollama, and database connectivity tests)
- **Total**: **288 passed, 0 failed, 0 skipped**.

---

## 15. Automated Consistency Checks

Executed via [`scripts/verify_phase3_consistency.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/verify_phase3_consistency.py):

1. **Dataset Integrity**: 450 total query evaluations across 3 seeds and 6 modes audited. Zero duplicate run IDs, zero missing queries, zero malformed rows.
2. **Telemetry Integrity**: All 47 telemetry rows obey $S = \frac{1}{1 + d^2}$, valid ranks, monotonic store growth, and null empty-store semantics.
3. **Statistical Integrity**: All summary metrics strictly match raw CSV aggregations with Bessel's correction.
4. **Publication Integrity**: All 5 LaTeX validation tables match raw analytical metrics with zero discrepancies.

---

## 16. Final Phase 3 Gate Decision

All 14 requirements of the Phase 3 Primary Objective and Acceptance Gate have been strictly verified.

```text
PHASE 3 — PASS
SAFE TO BEGIN FULL PROJECT FORENSIC AUDIT 3
```
