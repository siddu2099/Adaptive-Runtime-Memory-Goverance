# ARMG — PHASE 4 ACCEPTANCE REPORT
## AUTHORITATIVE BENCHMARK RERUN & EMPIRICAL EVIDENCE

**Execution Date:** 2026-10-06  
**Auditor / Agent:** Antigravity Advanced Agentic Coding Assistant (DeepMind)  
**Repository:** `siddu2099/Adaptive-Runtime-Memory-Goverance`  
**Branch:** `armg-hardening`  
**Phase:** **PHASE 4 — AUTHORITATIVE BENCHMARK**  
**Authoritative Road-Map Alignment:** Fully fulfills Phase 4 Authoritative Benchmark Execution. Prior preliminary benchmark runs archived in `benchmark/historical_preliminary/`.

---

## EXECUTIVE SUMMARY

Phase 4 executes the complete, authoritative empirical benchmark across all 6 experimental modes and 3 stability repetitions (seeds 42, 123, 999) under the frozen, hardened ARMG implementation and verified test architecture.

All **450 total query evaluations** ($3\text{ seeds} \times 6\text{ modes} \times 25\text{ queries}$) were executed live against the PostgreSQL 18.1 Star Schema data warehouse (`armg_db`) and local Ollama (`qwen2.5:7b-instruct`, `nomic-embed-text`) at `temperature = 0.0`. 

Prior to execution, all historical/preliminary benchmark artifacts were safely archived in `benchmark/historical_preliminary/`. The authoritative dataset was generated strictly programmatically without manual edits, synthetic scores, or algorithmic tuning.

---

## 1. PRE-BENCHMARK ENVIRONMENT GATE

All pre-benchmark environment prerequisites were verified live from the active machine and recorded to [`benchmark/environment.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/environment.json):

| Parameter | Recorded Runtime Value | Status |
|---|---|---|
| **Git Commit Hash** | `40d36a3980e5f152a8eadbfa021b833f587d7b3b` | Verified |
| **Operating System** | Windows 11 AMD64 (Build 10.0.26300) | Verified |
| **Python Runtime** | `3.13.2 (tags/v3.13.2:4f8bb39)` | Verified |
| **PostgreSQL Server** | `PostgreSQL 18.1 on x86_64-windows, compiled by msvc-19.44.35221, 64-bit` | Verified |
| **Ollama Server** | `v0.32.15` running on `http://localhost:11434` | Verified |
| **LLM Model** | `qwen2.5:7b-instruct` | Verified & Loaded |
| **Embedding Model** | `nomic-embed-text` | Verified & Loaded |
| **FAISS Library** | `faiss-cpu 1.14.3` (standalone CPU build) | Verified |
| **LangGraph Library** | `1.2.5` | Verified |
| **SQLGlot Library** | `30.12.0` | Verified |
| **psycopg2 Library** | `2.9.11` | Verified |
| **pydantic Library** | `2.12.5` | Verified |
| **numpy Library** | `2.4.1` | Verified |
| **pytest Library** | `9.1.1` | Verified |
| **Database Warehouse** | `armg_db` on port 5432 with 4 tables: `dim_geography` (6 rows), `dim_product` (8 rows), `dim_time` (365 rows), `fact_sales_performance` (2,000 rows) | Seed Verified |
| **Gate A: Gold Queries** | 25 of 25 gold SQL queries executed successfully on live PostgreSQL | 100% Passed |

---

## 2. FROZEN EXPERIMENTAL CONFIGURATION

The experimental parameters were strictly frozen prior to execution without modification:

- **Generation Temperature:** $0.0$ (deterministic pipeline stability)
- **Primary LLM:** `qwen2.5:7b-instruct` (Ollama endpoint `/api/generate`, prompt timeout 60s)
- **Vector Embeddings:** `nomic-embed-text` (768-dimensional, unit-L2 normalized)
- **Benchmark Corpus:** 25 Star Schema queries (`benchmark/queries.json`), Category A (5), Category B (8), Category C (6), Category D (6)
- **Retrieval Similarity Threshold ($\tau$):** $0.50$
- **Admission Utility Threshold ($\text{Utility}_0$):** $0.25$
- **Max Retry Budget:** $3$ repair attempts
- **Negative Constraints:** Enabled in Modes 4 & 6; ablated in Mode 5
- **Temporal Decay ($\lambda$):** $\lambda = 0.05$ in Modes 4 & 5; $\lambda = 0.0$ in Mode 6 (normal benchmark clock, no artificial time injection)
- **Repetitions (Seeds):** $42$, $123$, $999$

---

## 3. SEEDS & DETERMINISTIC STABILITY REPETITIONS

Because generation utilizes `temperature = 0.0`, repetitions across seeds $42$, $123$, and $999$ evaluate **deterministic pipeline stability and multi-run orchestration reproducibility**, rather than stochastic sampling variance.

Seed propagation was verified:
- Seed parameter $s \in \{42, 123, 999\}$ is explicitly passed into `SQLGenerator(seed=s)` and `RepairSQLGenerator(seed=s)`.
- Propagated to Ollama payload under `options["seed"] = s`.
- Recorded in per-query records (`seed` column) and run metadata JSON files.

---

## 4. EXPERIMENTAL MODE DEFINITIONS

All 6 modes defined by the ARMG research protocol were executed:

1. **Mode 1 — Monolithic Zero-Shot Baseline:**
   Single-pass generation from question and pruned schema. Zero error observation, zero repair loops, zero memory.
2. **Mode 2 — Stateless Self-Correction Baseline:**
   Iterative repair loop using runtime observation and taxonomy diagnosis. Max retries = 3. Zero cross-query persistent memory.
3. **Mode 3 — Naive Vector RAG Baseline:**
   Naive vector store accumulating all successfully generated queries without governance filtering or decay. Injects raw previous query-SQL pairs as few-shot examples. Zero repair loops.
4. **Mode 4 — Full ARMG Architecture:**
   Closed-loop integration of taxonomy-driven error diagnosis, strict negative repair constraints, post-repair admission gating ($\text{Utility}_0 \ge 0.25$), and FAISS vector retrieval with similarity thresholding ($S \ge 0.50$) and recency decay ($\lambda = 0.05$).
5. **Mode 5 — ARMG without Negative Constraints (Ablation):**
   Full ARMG pipeline but omitting the `[NEGATIVE REPAIR CONSTRAINTS]` block from repair prompts to isolate the utility of negative guidance.
6. **Mode 6 — ARMG without Temporal Decay (Ablation with $\lambda = 0$):**
   Full ARMG pipeline operating with zero decay rate ($\lambda = 0.0$) under the normal benchmark clock. Zero artificial time injection.

---

## 5. STATE-RESET PROCEDURE & ISOLATION

Strict experimental isolation was maintained between runs:
- **Between Seeds:** Complete reset of memory stores, FAISS indices, and logging accumulators.
- **Between Modes (within a seed):**
  - Database validated to ensure no mutable state leaks.
  - In-memory vector store destroyed and recreated:
    - Mode 3: Fresh `NaiveVectorStore(dimension=768)`.
    - Modes 4, 5, 6: Fresh `FAISSMemoryStore()` with empty `IndexFlatL2` and empty metadata maps.
  - LangGraph workflow compiled freshly with isolated generator instances.
- **Within a Mode (Q01 $\to$ Q25):**
  - Queries executed sequentially (Q01 through Q25) to model genuine operational session dynamics.
  - Memory admitted during repair of an earlier query (e.g., Q04, Q13, Q15) persists across subsequent queries within the same mode.

---

## 6. RAW EVIDENCE REPOSITORY & PROVENANCE

All preliminary benchmark outputs from previous exploratory phases were backed up to:
- [`benchmark/historical_preliminary/`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/historical_preliminary/)

The authoritative Phase 4 evidence is structured in the canonical hierarchy:

```
benchmark/
├── environment.json                           # Pre-benchmark runtime environment capture
├── retrieval_telemetry.csv                    # 47 raw FAISS retrieval records (Mode 4)
├── statistical_summary.csv                    # Descriptive statistics across seeds 42, 123, 999
├── statistical_summary.json                   # Full programmatic metrics with numerators/denominators
├── multi_seed_summary.md                      # Markdown summary table
├── seed42/
│   ├── benchmark_results.csv                  # 150 evaluations (Modes 1-6 x 25 queries)
│   └── benchmark_summary.md
├── seed123/
│   ├── benchmark_results.csv                  # 150 evaluations
│   └── benchmark_summary.md
├── seed999/
│   ├── benchmark_results.csv                  # 150 evaluations
│   └── benchmark_summary.md
└── raw/                                       # 18 mode directories (3 seeds x 6 modes)
    └── seed_{seed}/
        └── mode_{1-6}/
            ├── per_query_results.csv          # 25 query records per mode
            ├── execution_log.jsonl            # Detailed JSON line log
            ├── environment.json               # Environment snapshot
            ├── run_metadata.json              # Seed, timing, and run ID metadata
            └── retrieval_telemetry.csv        # Mode 4 & Mode 3 candidate search events
```

---

## 7. QUERY & RUN ACCOUNTING

Total query evaluations:
$$\text{Evaluations} = 3\text{ seeds} \times 6\text{ modes} \times 25\text{ queries} = 450\text{ query executions}$$

- **Seed 42:** 150 queries accounted for (25 queries $\times$ 6 modes)
- **Seed 123:** 150 queries accounted for (25 queries $\times$ 6 modes)
- **Seed 999:** 150 queries accounted for (25 queries $\times$ 6 modes)
- **Duplicate Records:** `0`
- **Missing Records:** `0`
- **Total Execution Time:** `3313.2s` (55.22 minutes)

---

## 8. FAISS RETRIEVAL TELEMETRY ACCOUNTING

FAISS retrieval telemetry was logged directly from the live execution path across all three authoritative seeds (seeds 42, 123, 999) in [`benchmark/retrieval_telemetry.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/retrieval_telemetry.csv):

| Metric | Seed 42 | Seed 123 | Seed 999 | Canonical Aggregate | Requirement |
|---|:---:|:---:|:---:|:---:|---|
| **Total Telemetry Rows** | **47** | **47** | **47** | **141** | 141 raw records captured across 3 seeds |
| **Unique Benchmark Queries** | **25** | **25** | **25** | **25** | Q01 through Q25 evaluated |
| **Empty-Store Queries (Q01–Q04)** | **4** | **4** | **4** | **12** | Represented as `distance=null`, `similarity=null`, `retrieval_count=0` |
| **Total Candidates Evaluated by FAISS** | **43** | **43** | **43** | **129** | All candidates logged prior to threshold filtering |
| **Accepted Candidates ($S \ge 0.50$)** | **16** | **16** | **16** | **48** | Exactly 16 candidates admitted into repair context per seed |
| **Distinct Queries with Retrieval** | **12** | **12** | **12** | **12 / 25 (48.0%)** | Q08, Q10, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25 |
| **Distance Preservation** | **Squared L2 ($d^2$)** | **Squared L2 ($d^2$)** | **Squared L2 ($d^2$)** | **Squared L2 ($d^2$)** | Direct C++ FAISS `IndexFlatL2` distance |
| **Similarity Formula** | **$S = 1 / (1 + d^2)$** | **$S = 1 / (1 + d^2)$** | **$S = 1 / (1 + d^2)$** | **$S = 1 / (1 + d^2)$** | Strict mathematical transformation |
| **Synthetic / Derived Scores** | **0** | **0** | **0** | **0** | 100% empirical from live FAISS search |

---

## 9. MULTI-SEED STATISTICAL SUMMARY

Programmatic multi-seed statistics computed across seeds $42$, $123$, and $999$ ($n = 3$ runs; $N = 75$ evaluations per mode):

| Mode | PostgreSQL Success (Num/Den, Mean $\pm$ Std) | Relational Accuracy (Num/Den, Mean $\pm$ Std) | Mean Retries ($\pm$ Std) | Mean Latency ms ($\pm$ Std) | Mean Tokens ($\pm$ Std) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Mode 1 (Zero-Shot)** | 60/75 ($80.00\% \pm 0.00\%$) | 45/75 ($60.00\% \pm 0.00\%$) | $0.00 \pm 0.00$ | $4859.70 \pm 7.98$ | $360.57 \pm 0.37$ |
| **Mode 2 (Stateless Self-Correction)** | 72/75 ($96.00\% \pm 0.00\%$) | 51/75 ($68.00\% \pm 0.00\%$) | $0.28 \pm 0.00$ | $6441.56 \pm 105.51$ | $503.72 \pm 0.42$ |
| **Mode 3 (Naive Vector RAG)** | 69/75 ($92.00\% \pm 0.00\%$) | 51/75 ($68.00\% \pm 0.00\%$) | $0.00 \pm 0.00$ | $6776.25 \pm 34.40$ | $558.28 \pm 0.00$ |
| **Mode 4 (Full ARMG)** | 72/75 ($96.00\% \pm 0.00\%$) | 51/75 ($68.00\% \pm 0.00\%$) | $0.37 \pm 0.05$ | $9000.59 \pm 184.33$ | $602.85 \pm 28.49$ |
| **Mode 5 (ARMG - Neg Constraints)** | 72/75 ($96.00\% \pm 0.00\%$) | 51/75 ($68.00\% \pm 0.00\%$) | $0.32 \pm 0.00$ | $8768.48 \pm 100.30$ | $530.97 \pm 0.40$ |
| **Mode 6 — ARMG without Temporal Decay (λ = 0)** | 72/75 ($96.00\% \pm 0.00\%$) | 51/75 ($68.00\% \pm 0.00\%$) | $0.28 \pm 0.00$ | $8507.98 \pm 73.15$ | $542.27 \pm 0.39$ |

### Discrepancy Gap (ExecSucc $-$ ExecAcc)
- **Mode 1:** $80.00\% - 60.00\% = 20.00\text{ pp}$
- **Mode 2:** $96.00\% - 68.00\% = 28.00\text{ pp}$
- **Mode 3:** $92.00\% - 68.00\% = 24.00\text{ pp}$
- **Mode 4:** $96.00\% - 68.00\% = 28.00\text{ pp}$
- **Mode 5:** $96.00\% - 68.00\% = 28.00\text{ pp}$
- **Mode 6:** $96.00\% - 68.00\% = 28.00\text{ pp}$

The discrepancy gap reflects queries that successfully execute without PostgreSQL driver error but diverge from the gold relational truth (e.g., incorrect grouping granularity or join conditions on semantic edge cases).

---

## 10. FAILURE ANALYSIS ACROSS MODES

All failed queries were preserved as integral evidence:

1. **Mode 1 Failures (5 / 25 queries):**
   - `Q04`: UndefinedColumn error (`revenue` hallucinated instead of `gross_revenue`).
   - `Q11`: Complex multi-table join syntax error.
   - `Q13`: UndefinedColumn error (`product_type` hallucinated instead of `category`).
   - `Q15`: UndefinedColumn error (`net_sales` hallucinated instead of `net_profit`).
   - `Q22`: UndefinedColumn error (`item_cost` hallucinated instead of `unit_cost`).
2. **Mode 2 Failures (1 / 25 queries):**
   - `Q11`: Failed initial attempt and exhausted all 3 repair retries due to persistent AST join ambiguity.
3. **Mode 3 Failures (2 / 25 queries):**
   - `Q04`: Failed on initial attempt. Because Mode 3 has no repair loop, it terminated with failure.
   - `Q15`: Failed on initial attempt without repair mechanism.
4. **Mode 4 Failures (1 / 25 queries):**
   - `Q11`: Failed initial attempt and exhausted 3 repair retries. Correctly routed to `TERMINAL_FAILURE_NOT_ADMITTED` without polluting the memory store.
5. **Modes 5 & 6 Failures (1 / 25 queries):**
   - `Q11`: Same terminal failure trajectory as Mode 4.

---

## 11. REGRESSION & TEST VERIFICATION RESULTS

Immediately following benchmark execution, the test suite was verified:

```bash
# 1. Regression Suite (Phases 1A, 1B, 1C, 1D, Phase 2)
pytest tests/unit/test_phase1a_governance_provenance.py \
       tests/unit/test_memory_governance.py \
       tests/unit/test_phase1c_sql_extraction.py \
       tests/unit/test_phase1d_safety_guard.py \
       tests/unit/test_phase2_faiss_telemetry.py -q
# Result: 149 passed in 3.13s

# 2. Benchmark Reproducibility Unit Test
pytest tests/unit/test_phase3_benchmark_reproducibility.py -q
# Result: 4 passed in 0.61s

# 3. Hermetic Unit Suite
pytest tests/unit/ -q
# Result: 262 passed, 2 warnings in 30.79s

# 4. Integration Suite
pytest tests/integration/ -q
# Result: 17 passed in 22.80s

# 5. Environment Suite
pytest tests/test_env.py -q
# Result: 12 passed in 12.30s
```

All 291 tests across unit, integration, and environment suites pass without regression.

---

## 12. FILES CREATED / CHANGED

### Benchmark Evidence
- [`benchmark/environment.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/environment.json) — Fresh runtime environment capture.
- [`benchmark/seed42/benchmark_results.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/seed42/benchmark_results.csv) — 150 query records.
- [`benchmark/seed123/benchmark_results.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/seed123/benchmark_results.csv) — 150 query records.
- [`benchmark/seed999/benchmark_results.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/seed999/benchmark_results.csv) — 150 query records.
- [`benchmark/retrieval_telemetry.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/retrieval_telemetry.csv) — 141 real FAISS search records across 3 seeds (47 per seed).
- [`benchmark/raw/`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/raw/) — 18 mode directories with raw logs and per-query CSVs.
- [`benchmark/statistical_summary.csv`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/statistical_summary.csv) — Multi-seed descriptive statistics.
- [`benchmark/statistical_summary.json`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/statistical_summary.json) — Programmatic summary data.
- [`benchmark/multi_seed_summary.md`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/multi_seed_summary.md) — Statistical Markdown table.
- [`benchmark/historical_preliminary/`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/historical_preliminary/) — Archived preliminary benchmark artifacts.

### Scripts & Tests
- [`scripts/run_phase4_benchmark_suite.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/run_phase4_benchmark_suite.py) — Authoritative benchmark master orchestrator.
- [`scripts/verify_phase4_telemetry_provenance.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/verify_phase4_telemetry_provenance.py) — Telemetry provenance verification script (8/8 checks passed).
- [`scripts/verify_phase4_data_integrity.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/verify_phase4_data_integrity.py) — Benchmark data integrity and smoke-test exclusion script.
- [`tests/unit/test_phase3_benchmark_reproducibility.py`](file:///c:/Users/siddu/Pictures/armg%20main/tests/unit/test_phase3_benchmark_reproducibility.py) — Unit tests anchored to historical preliminary Phase 3 baseline data.

---

## 13. PHASE 4 ACCEPTANCE GATE CHECKLIST

```text
[PASS] Environment prerequisites verified.
[PASS] Exact runtime configuration recorded.
[PASS] All 3 approved repetitions executed (seeds 42, 123, 999).
[PASS] All 6 modes executed.
[PASS] All 25 queries executed per seed/mode.
[PASS] Expected 450 query evaluations accounted for (150 x 3 = 450).
[PASS] State isolation verified between seeds and modes.
[PASS] Real FAISS telemetry captured where applicable (141 rows, 47 per seed).
[PASS] Empty-store telemetry uses null semantics (null, never 0.0).
[PASS] No synthetic empirical values.
[PASS] No manually entered benchmark values.
[PASS] Raw evidence preserved across 18 mode directories.
[PASS] Failed executions preserved (Q11, Q04, Q15).
[PASS] No benchmark methodology was changed.
[PASS] No algorithmic redesign occurred.
[PASS] Dataset integrity checks pass.
[PASS] Phase 1–3 regression tests remain passing (291/291 passed).
```

---

## 14. FINAL ACCEPTANCE DECISION

```text
======================================================================
PHASE 4 — PASS
SAFE TO BEGIN FULL PROJECT FORENSIC AUDIT 4
======================================================================
```
