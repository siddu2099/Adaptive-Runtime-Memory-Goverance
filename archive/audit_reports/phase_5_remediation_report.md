# ARMG PHASE 5 REMEDIATION REPORT
## STRICT IMPLEMENTATION, EVIDENCE & RUNTIME AUDIT REMEDIATION

**Project**: Adaptive Runtime Memory Governance (ARMG) for Text-to-SQL  
**Evaluation Target**: Phase 5 Remediation Gate & Evidence Pipeline  
**Date**: October 7, 2026  
**Auditor**: Antigravity Autonomous Coding & Forensic Systems  
**Status**: **REMEDIATION PASS**  

---

## EXECUTIVE SUMMARY

This remediation report addresses the two blocking code-level issues identified prior to authorizing the closure of Phase 5:
1. **Issue 1 — Integration Test Skips**: Investigation and forensic resolution of the 4 skipped tests in `tests/integration/test_baseline_integration.py` (`13 passed, 4 skipped` -> **`17 / 17 passed (100%)`**).
2. **Issue 2 — Full Code-Level Empirical Hardcoding Audit**: Exhaustive codebase audit for static empirical benchmark values across all canonical generation pipelines (`scripts/generate_results.py`, `benchmark/analysis.py`, and `manuscript/figures/source/fig{3,4,5,6}_*.py`), including dynamic refactoring of Figure 6 (memory growth), Table IX (semantic divergence), and Table D (store validation), accompanied by 5 end-to-end sandbox source-perturbation tests.

All verification gates have succeeded:
- **Integration Tests**: `17 / 17 passed` (0 skipped, 0 failed) with live Ollama (`qwen2.5:7b-instruct`, `nomic-embed-text`) and PostgreSQL 16.
- **Unit Tests**: `277 / 277 passed` (including all 15 Phase 5 canonical pipeline and perturbation tests).
- **Environment Tests**: `12 / 12 passed`.
- **Validation Table Checks**: `6 / 6 passed` with zero discrepancies.
- **Empirical Value Classification**: Zero Category C (empirical benchmark value) constants inside canonical calculation paths.
- **Controlled Perturbation Tests**: 5 distinct end-to-end sandbox perturbation tests verified for Figure 3, Figure 4, Figure 5, Figure 6, and Table IX with exact bidirectional baseline restoration.

---

## 1. ISSUE 1 — INTEGRATION TEST INVESTIGATION & PROOF

### 1.1 Identification of the Four Skipped Tests

During the initial Phase 5 execution report, pytest reported `13 passed, 4 skipped` in `tests/integration/`. Execution of `pytest tests/integration/ -q -rs` identified the exact four tests:

| Test Name | Module | Marker | Fixture Involved | Skip Reason Recorded |
| :--- | :--- | :--- | :--- | :--- |
| `test_generator_communication` | `tests/integration/test_baseline_integration.py` | `integration` | None (direct call) | `Ollama service is offline or unreachable on localhost:11434` |
| `test_e2e_query_1_simple_aggregation` | `tests/integration/test_baseline_integration.py` | `integration` | `pipeline` (module-scoped) | `Ollama service is offline or unreachable on localhost:11434` |
| `test_e2e_query_2_two_table_join` | `tests/integration/test_baseline_integration.py` | `integration` | `pipeline` (module-scoped) | `Ollama service is offline or unreachable on localhost:11434` |
| `test_e2e_query_3_three_table_join` | `tests/integration/test_baseline_integration.py` | `integration` | `pipeline` (module-scoped) | `Ollama service is offline or unreachable on localhost:11434` |

### 1.2 Comparison Against Phase 4 Baseline

Forensic comparison against the Phase 4 baseline established:
- `git diff -- tests/integration/`: **Zero changes** (empty diff).
- `git diff -- pytest.ini`: **Zero changes** (empty diff).
- `git diff -- tests/conftest.py`: **Zero changes** (empty diff).
- **Imports, Fixtures, and Markers**: Unmodified since Phase 3/4.
- **Skip Logic**:
  ```python
  def is_ollama_online() -> bool:
      url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
      try:
          res = requests.get(f"{url.rstrip('/')}/api/tags", timeout=2)
          return res.status_code == 200
      except Exception:
          return False
  ```
  In lines 63 and 85 of `tests/integration/test_baseline_integration.py`, tests explicitly execute `if not is_ollama_online(): pytest.skip(...)`.

### 1.3 Root Cause & Classification

The four tests skipped because the local Ollama background daemon (`ollama serve`) was offline at the exact moment the Phase 5 test suite ran (following a local workstation restart / session disconnect). The tests operated strictly as designed by guarding live service calls.

**Classification**: **F — Accepted design/environment condition**  
*Rationale*: The skips were not caused by any code change, fixture modification, or test regression in Phase 5. They represent an intentional environment precondition protecting CI/offline test suites against hanging on missing network services.

### 1.4 Mandatory Proof: Live Service Execution

The Ollama daemon was launched in the environment (`ollama serve`), hosting `qwen2.5:7b-instruct` and `nomic-embed-text:latest`.

Execution command:
```bash
pytest tests/integration/ -v
```

Execution output:
```text
tests/integration/test_baseline_integration.py::test_schema_introspector_live PASSED [  5%]
tests/integration/test_baseline_integration.py::test_generator_communication PASSED [ 11%]
tests/integration/test_baseline_integration.py::test_e2e_query_1_simple_aggregation PASSED [ 17%]
tests/integration/test_baseline_integration.py::test_e2e_query_2_two_table_join PASSED [ 23%]
tests/integration/test_baseline_integration.py::test_e2e_query_3_three_table_join PASSED [ 29%]
tests/integration/test_observation_integration.py::test_observation_live_postgres_execution_failure PASSED [ 35%]
tests/integration/test_postgres_integration.py::test_protocol_conformance PASSED [ 41%]
tests/integration/test_postgres_integration.py::test_catalog_inspection PASSED [ 47%]
tests/integration/test_postgres_integration.py::test_valid_analytical_query PASSED [ 52%]
tests/integration/test_postgres_integration.py::test_error_capture_undefined_column PASSED [ 58%]
tests/integration/test_postgres_integration.py::test_error_capture_undefined_table PASSED [ 64%]
tests/integration/test_postgres_integration.py::test_error_capture_grouping_error PASSED [ 70%]
tests/integration/test_postgres_integration.py::test_error_capture_division_by_zero PASSED [ 76%]
tests/integration/test_postgres_integration.py::test_error_capture_syntax_error PASSED [ 82%]
tests/integration/test_postgres_integration.py::test_pre_execution_validation PASSED [ 88%]
tests/integration/test_postgres_integration.py::test_connection_cleanup_and_lifecycle PASSED [ 94%]
tests/integration/test_repair_integration.py::test_live_postgres_repair_execution PASSED [100%]

======================== 17 passed in 63.93s (0:01:03) ========================
```
**Result**: **17 / 17 passed, 0 skipped, 0 failed**. Baseline restored with zero regressions.

---

## 2. ISSUE 2 — CODE-LEVEL AUDIT FOR HARDCODED EMPIRICAL RESULTS

An exhaustive lexical and AST code audit was conducted across all files composing the canonical Phase 5 results generation pipeline:
- `scripts/generate_results.py`
- `benchmark/analysis.py`
- `manuscript/figures/source/fig3_retrieval_geometry.py`
- `manuscript/figures/source/fig4_execsucc_execacc.py`
- `manuscript/figures/source/fig5_tradeoff.py`
- `manuscript/figures/source/fig6_memory_growth.py`

### 2.1 Taxonomy Classifications

Every numeric or string constant was classified into one of six categories:
- **A**: Configuration / mathematical constant (e.g., plot DPI, alpha, geometric limits).
- **B**: Test fixture / assertion baseline (used solely in unit test assertions).
- **C**: Empirical benchmark value (MUST NOT exist in canonical generation calculation paths).
- **D**: Derived value (computed programmatically from raw inputs).
- **E**: Static taxonomy / specification (e.g., query complexity taxonomy from `benchmark/queries.json`).
- **F**: Historical / superseded artifact (in legacy / scratch scripts).

### 2.2 Exhaustive Token Audit Table

| Candidate Value | Occurrences in Canonical Pipeline | Classification | Context / Code Reference |
| :--- | :---: | :---: | :--- |
| `80.0` | 0 | **B** (in tests only) | Computed dynamically as `(60/75)*100` via `compute_benchmark_metrics()`. |
| `60.0` | 0 | **B** (in tests only) | Computed dynamically as `(45/75)*100` via `compute_benchmark_metrics()`. |
| `96.0` | 0 | **B** (in tests only) | Computed dynamically as `(72/75)*100`. |
| `68.0` | 0 | **B** (in tests only) | Computed dynamically as `(51/75)*100`. |
| `92.0` | 0 | **B** (in tests only) | Computed dynamically as `(69/75)*100`. |
| `417` | 0 | **B** (in tests only) | Computed dynamically as `root_df['success'].sum()`. |
| `300` | 12 | **A** | Matplotlib figure export resolution: `dpi=300`. Zero empirical meaning. |
| `45` | 2 | **A** | Scatter marker area `s=45` in Fig 3; tick rotation `rotation=45` in Fig 6. |
| `51` | 0 | **B** (in tests only) | Computed dynamically from raw seed accuracy columns. |
| `60` | 0 | **B** (in tests only) | Computed dynamically from raw seed success columns. |
| `72` | 0 | **B** (in tests only) | Computed dynamically from raw seed success columns. |
| `23` | 0 | **D** | Mode 3 unmanaged store size: computed dynamically via cumulative row count `cnt3`. |
| `3` | 46 | **A / E** | Section numbers, mode count ($n=3$), Python runtime `Python 3.11/3.13`. Zero empirical store counts. |
| `0.28` | 0 | **D** | Mode 2 mean retries: computed dynamically as `sub["retry_count"].mean()`. |
| `0.37` | 0 | **D** | Mode 4 mean retries: computed dynamically as `sub["retry_count"].mean()`. |
| `503.72` | 0 | **D** | Mode 2 mean tokens: computed dynamically as `sub["total_tokens"].mean()`. |
| `602.85` | 0 | **D** | Mode 4 mean tokens: computed dynamically as `sub["total_tokens"].mean()`. |
| `6441.56`| 0 | **D** | Mode 2 latency: computed dynamically as `sub["latency_ms"].mean()`. |
| `9000.59`| 0 | **D** | Mode 4 latency: computed dynamically as `sub["latency_ms"].mean()`. |
| `33.33` | 0 | **D** | Relative retries delta: computed dynamically as `((m4-m2)/m2)*100`. |
| `19.68` | 0 | **D** | Relative tokens delta: computed dynamically as `((m4-m2)/m2)*100`. |
| `39.73` | 0 | **D** | Relative latency delta: computed dynamically as `((m4-m2)/m2)*100`. |
| `Q05` | 2 | **E** | Present in Table VI (taxonomy `Q01--Q05`) and Table IX dictionary description. Filtered dynamically. |
| `Q14` | 2 | **E** | Present in Table VI (taxonomy `Q14--Q19`) and Table IX dictionary description. Filtered dynamically. |
| `Q15` | 1 | **E** | Present in Table IX diagnostic dictionary. Filtered dynamically. |
| `Q17` | 1 | **E** | Present in Table IX diagnostic dictionary. Filtered dynamically. |
| `Q18` | 1 | **E** | Present in Table IX diagnostic dictionary. Filtered dynamically. |
| `Q19` | 2 | **E** | Present in Table VI (taxonomy `Q14--Q19`) and Table IX dictionary description. Filtered dynamically. |
| `Q25` | 6 | **E** | Present in schema bounds checks (`Q01` to `Q25`), Table VI, Table IX dictionary description. Filtered dynamically. |
| `mem-4ff9e3d8` | 0 | **D** | Extracted dynamically from `r['memory_reinforcement']`. Zero hardcoding. |

**Audit Conclusion**: **Zero Category C constants exist in the canonical results pipeline**. All empirical outputs are calculated dynamically from raw CSV evidence.

---

## 3. SPECIFIC VERIFICATIONS: FIGURE 6 & TABLE IX

### 3.1 Figure 6 (Memory Growth) & Table D Dynamic Refactoring

Figure 6 (`manuscript/figures/source/fig6_memory_growth.py`) and Table D (`scripts/generate_results.py` lines 825–898) were refactored to eliminate all static assumptions:
- **Cumulative Step Curves**:
  ```python
  m4_store = []
  cnt4 = 0
  for idx, (_, r) in enumerate(m4.iterrows()):
      if r.get('memory_admission') == 'ADMITTED':
          cnt4 += 1
          admissions.append({"idx": idx, "query_id": r['query_id'], "store_size": cnt4})
      elif r.get('memory_admission') == 'EXISTING_REINFORCED' or pd.notna(r.get('memory_reinforcement')):
          reinforcements.append({"idx": idx, "query_id": r['query_id'], "store_size": cnt4, "mem_id": str(r.get('memory_reinforcement')).strip()})
      m4_store.append(cnt4)
  ```
- **Dynamic Plateau Detection**:
  ```python
  final_m4 = m4_store[-1]
  plateau_start = m4_store.index(final_m4) if final_m4 in m4_store else len(queries) - 1
  ```
- **Dynamic Invariant Summary in Table D**:
  Query plateau boundaries (`plateau_start_q`), admissions descriptions, and reinforcement IDs are assembled directly from the row iteration loop.
- **Reinforcement UUID**: Derived dynamically from `r['memory_reinforcement']` rather than any static string.

### 3.2 Table IX (Failure Diagnostics) Dynamic Divergence Calculation

Table IX generation in `scripts/generate_results.py` (lines 628–678) derives the set of divergent queries purely from data:
```python
m4_rows = root_df[root_df["mode"].str.startswith("Mode 4")]
div_df = m4_rows[(m4_rows["success"] == True) & (m4_rows["execution_accuracy"] == 0)]
divergent_query_ids = sorted(div_df["query_id"].unique())
```
- The queries `['Q05', 'Q14', 'Q15', 'Q17', 'Q18', 'Q19', 'Q25']` are identified dynamically because their PostgreSQL execution succeeded while relational accuracy evaluated to `0`.
- The caption (`"Forensic Diagnostic Breakdown of the Seven Divergent Semantic Queries in Mode 4"`) formats the count word dynamically from `len(divergent_query_ids)`.
- If an empirical perturbation alters any query's accuracy or execution status, Table IX dynamically updates its row set and caption count.

---

## 4. COMPLETE EMPIRICAL OUTPUT AUDIT & PROVENANCE MAPPING

Every publication output generated by Phase 5 traces to an authoritative raw data source:

| Publication Output | Source Evidence File | Analysis Function | Specific Source Columns | Transformation / Calculation |
| :--- | :--- | :--- | :--- | :--- |
| **Figure 3** (Retrieval Geometry) | `benchmark/retrieval_telemetry.csv` | `generate_fig3()` | `mode`, `query_id`, `candidate_returned_by_faiss`, `similarity`, `retrieval_count` | Cosine similarity aggregation over candidate rows; threshold comparison $S \ge 0.50$ |
| **Figure 4** (ExecSucc vs ExecAcc) | `benchmark/seed*/benchmark_results.csv` | `compute_benchmark_metrics()`, `generate_fig4()` | `mode`, `success`, `execution_accuracy` | Group-by mode across 3 seeds; mean and sample std dev ($N=75$ per mode) |
| **Figure 5** (Operational Tradeoff) | `benchmark/seed*/benchmark_results.csv` | `compute_tradeoff_profile()`, `generate_fig5()` | `retry_count`, `total_tokens`, `success`, `latency_ms`, `execution_accuracy` | Arithmetic delta for % metrics; relative percentage change for rate metrics (Mode 4 vs Mode 2) |
| **Figure 6** (Memory Store Growth) | `benchmark/seed42/benchmark_results.csv` | `generate_fig6()` | `mode`, `query_id`, `memory_admission`, `memory_reinforcement` | Sequential row aggregation: cumulative count of `NAIVE_STORED` (Mode 3) vs `ADMITTED` (Mode 4) |
| **Table II** (Main Results) | `benchmark/seed*/benchmark_results.csv` | `compute_benchmark_metrics()` | `success`, `execution_accuracy`, `retry_count`, `latency_ms`, `total_tokens` | Across-seed mean $\pm$ std dev across 6 modes |
| **Table III** (Discrepancy Gap) | `benchmark/seed*/benchmark_results.csv` | `compute_benchmark_metrics()` | `success`, `execution_accuracy` | Arithmetic discrepancy gap: $\text{ExecSucc} - \text{ExecAcc}$ (pp) |
| **Table VII** (Governance Math) | Governance Engine Equations | LaTeX specification | N/A (Algorithmic equations) | Mathematical formulation of utility, confidence, admission, and decay |
| **Table VIII** (Trade-off Matrix) | `benchmark/seed*/benchmark_results.csv` | `compute_tradeoff_profile()` | `retry_count`, `total_tokens`, `success`, `latency_ms`, `execution_accuracy` | Pairwise comparison table between Mode 2 and Mode 4 |
| **Table IX** (Semantic Failures) | `benchmark/seed*/benchmark_results.csv` | `generate_publication_tables()` | `mode`, `query_id`, `success`, `execution_accuracy` | Filter condition: $\text{Success} == \text{True} \land \text{ExecAcc} == 0$; qualitative rationale catalog |
| **Table A** (Fig 3 Validation) | `benchmark/retrieval_telemetry.csv` | `compute_retrieval_telemetry_metrics()` | `query_id`, `similarity`, `retrieval_count` | Query-by-query validation table matching Figure 3 curve points |
| **Table B** (Fig 4 Validation) | `benchmark/seed*/benchmark_results.csv` | `compute_benchmark_metrics()` | `success`, `execution_accuracy` | Exact counts ($n/75$) and percentages matching Figure 4 bars |
| **Table C** (Fig 5 Validation) | `benchmark/seed*/benchmark_results.csv` | `compute_tradeoff_profile()` | `retry_count`, `total_tokens`, `success`, `latency_ms`, `execution_accuracy` | Numerical tabular reference for Figure 5 horizontal delta bars |
| **Table D** (Fig 6 Validation) | `benchmark/seed42/benchmark_results.csv` | `generate_publication_tables()` | `memory_admission`, `memory_reinforcement` | Query-by-query memory store size and event tracking matching Figure 6 |
| **Table E** (Traceability Matrix) | All validation tables | `generate_publication_tables()` | N/A (Meta-matrix) | LaTeX cross-reference linking Figures 3–6 to Tables A–D |
| **`statistical_summary.json`** | `benchmark/seed*/benchmark_results.csv` | `compute_all_results_metrics()` | All numerical columns | Comprehensive JSON summary with means, std devs, and 95% CIs |
| **`statistical_summary.csv`** | `benchmark/seed*/benchmark_results.csv` | `compute_all_results_metrics()` | All numerical columns | Flat tabular summary of mode evaluations |
| **`multi_seed_summary.md`** | `benchmark/seed*/benchmark_results.csv` | `generate_summary_artifacts()` | All numerical columns | Markdown report of descriptive statistics |
| **`results_manifest.json`** | All pipeline outputs | `generate_results_manifest()` | Input/output file hashes and counts | Machine-readable lineage manifest |

---

## 5. STRONGER CONTROLLED PERTURBATION TESTS

To ensure complete coverage across all major output pathways, five dedicated hermetic perturbation tests were implemented and verified in `tests/unit/test_phase5_results_pipeline.py`. Each test executes inside an isolated filesystem sandbox, perturbs raw evidence, validates downstream propagation across tables and figures, restores original data, and verifies exact baseline restoration.

### 5.1 Figure 3 & Table A: Telemetry Perturbation Test (`test_perturbation_fig3_telemetry`)
- **Perturbation**: In sandbox copy of `retrieval_telemetry.csv`, Query Q05 (seed 42) similarity was altered from $0.4917$ to $0.8500$, `passed_retrieval_threshold` set to True, and `retrieval_count` incremented to 1.
- **Downstream Delta Verified**:
  - Table A (`table_fig3_validation.tex`): Total retrieval events increased from `$16$` to `$17$`.
  - Distinct retrieval queries increased from `$12$ of 25 ($48.0\%$)` to `$13$ of 25 ($52.0\%$)`.
  - Row Q05 updated from `0.4917 & No (0) & No (0)` to `0.8500 & No (0) & Yes (1)`.
  - Figure 3 PNG and SVG regenerated.
- **Restoration Verified**: Restored authoritative telemetry; regenerated; exact baseline restored ($16$ events, $12$ queries, Q05 `0.4917 & No (0) & No (0)`).

### 5.2 Figure 4 & Table B: Execution Success/Accuracy Perturbation Test (`test_source_perturbation_propagation`)
- **Perturbation**: In sandbox copy of `seed42/benchmark_results.csv`, Mode 1 Query Q01 flipped from $\text{Success}=\text{True}, \text{Acc}=1$ to $\text{Success}=\text{False}, \text{Acc}=0$.
- **Downstream Delta Verified**:
  - Mode 1 ExecSucc dropped from $80.00\%$ ($60/75$) to $78.67\%$ ($59/75$).
  - Mode 1 ExecAcc dropped from $60.00\%$ ($45/75$) to $58.67\%$ ($44/75$).
  - `statistical_summary.json` numerators updated ($59$ and $44$).
  - Table B (`table_fig4_validation.tex`) updated to `59 / 75` and `44 / 75`.
- **Restoration Verified**: Restored authoritative CSVs; regenerated; exact baseline restored ($80.00\%$ ExecSucc, $60.00\%$ ExecAcc, $60/75$, $45/75$).

### 5.3 Figure 5 & Table C / Table VIII: Operational Trade-Off Perturbation Test (`test_perturbation_fig5_tradeoff`)
- **Perturbation**: In sandbox copy of `seed42/benchmark_results.csv`, Mode 4 Query Q01 `retry_count` modified from $0$ to $3$.
- **Downstream Delta Verified**:
  - Mode 4 mean retries across 75 evaluations increased from $0.37$ to $0.41$.
  - Relative retries delta (Mode 4 vs Mode 2) shifted from $+33.33\%$ to $+47.62\%$.
  - Table C (`table_fig5_validation.tex`) and Table VIII (`table8_tradeoff.tex`) updated to `0.41` and `+47.62%`.
  - Figure 5 PNG and SVG regenerated.
- **Restoration Verified**: Restored authoritative CSVs; regenerated; exact baseline restored ($0.37$ retries, $+33.33\%$).

### 5.4 Figure 6 & Table D: Memory Growth Perturbation Test (`test_perturbation_fig6_memory_growth`)
- **Perturbation**: In sandbox copy of `seed42/benchmark_results.csv`, Mode 4 Query Q07 `memory_admission` changed from unadmitted to `ADMITTED`.
- **Downstream Delta Verified**:
  - Mode 4 persistent memory store plateau increased from $3$ to $4$ memories.
  - Table D (`table_fig6_validation.tex`) updated to reflect Q07 admission (`Q07 (Store=2)`) and summary updated to `"Mode 4 store size is invariant at exactly 4 from Q15 to Q25"`.
  - Figure 6 PNG and SVG regenerated.
- **Restoration Verified**: Restored authoritative CSVs; regenerated; exact baseline restored (plateau at exactly $3$).

### 5.5 Table IX: Forensic Failure Diagnostics Perturbation Test (`test_perturbation_table9_divergence`)
- **Perturbation**: In sandbox copies across all three seeds, Mode 4 Query Q05 `execution_accuracy` modified from $0$ to $1$.
- **Downstream Delta Verified**:
  - Divergent query count dropped from $7$ to $6$.
  - Table IX caption dynamically updated to `"Forensic Diagnostic Breakdown of the Six Divergent Semantic Queries in Mode 4"`.
  - Row `Q05` completely disappeared from Table IX; `Q14` through `Q25` retained.
- **Restoration Verified**: Restored authoritative CSVs; regenerated; exact baseline restored (7 divergent queries, caption `"Seven"`, Q05 row restored).

---

## 6. FULL REGRESSION TEST RESULTS

All test suites and verification scripts were executed on the active codebase:

| Test Suite / Script | Command | Result | Duration | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 5 Results Pipeline Suite** | `pytest tests/unit/test_phase5_results_pipeline.py -v` | **15 / 15 PASSED** | 38.44s | All 5 perturbation tests and schema checks passed. |
| **Full Unit Regression Suite** | `pytest tests/unit/ -v` | **277 / 277 PASSED** | 35.63s | 100% unit tests passing hermetically. |
| **Integration Test Suite** | `pytest tests/integration/ -v` | **17 / 17 PASSED** | 63.93s | Live PostgreSQL + live Ollama (0 skips). |
| **Environment Verification** | `pytest tests/test_env.py -v` | **12 / 12 PASSED** | 11.68s | Live Ollama LLM, embedding, and DB connectivity. |
| **Numerical Validation Table Audit**| `python scripts/verify_validation_tables.py` | **6 / 6 CHECKS PASSED** | 1.12s | Syntax, braces, and exact numerical alignment. |
| **Phase 4 Data Integrity Audit** | `python scripts/verify_phase4_data_integrity.py` | **7 / 7 CHECKS PASSED** | 0.85s | 450 evaluations, 0 smoke records. |
| **Phase 4 Telemetry Provenance Audit**| `python scripts/verify_phase4_telemetry_provenance.py` | **8 / 8 CHECKS PASSED** | 0.92s | 141 rows, 3 seeds (47 each), unit-$L_2$ norm. |
| **Canonical Pipeline Execution** | `python scripts/generate_results.py` | **STAGES 1–6 PASSED** | 3.80s | Exit code 0; all tables, figures, manifest emitted. |

**Total Test Coverage**: **306 / 306 active tests passing (100% pass rate, 0 skipped, 0 failed)**.

---

## 7. CLASSIFICATION OF FINDINGS

| Finding ID | Scope | Classification | Description & Remediation |
| :--- | :--- | :---: | :--- |
| **REM-P5-01** | Integration Tests | **F** (Accepted Design/Environment Condition) | 4 tests skipped in initial run because Ollama was offline. Verified 17/17 passing when service is active. |
| **REM-P5-02** | Figure 6 Store Growth | **Resolved** | Refactored `fig6_memory_growth.py` and Table D to derive store sizes, plateau, admissions, and UUIDs dynamically from raw rows. |
| **REM-P5-03** | Table IX Diagnostics | **Resolved** | Refactored Table IX to dynamically compute divergent query IDs from $\text{Success}==\text{True} \land \text{ExecAcc}==0$. |
| **REM-P5-04** | Output Perturbation | **Resolved** | Implemented 5 dedicated hermetic perturbation tests for Figures 3, 4, 5, 6, and Table IX with exact baseline restoration. |
| **REM-P5-05** | Empirical Hardcoding | **Resolved** | Audited all candidate empirical values; confirmed zero Category C constants exist in canonical generation paths. |

---

## 8. REMEDIATION CONCLUSION & GATE SIGN-OFF

The Phase 5 remediation requirements have been comprehensively fulfilled:
- No unresolved **A** finding exists.
- No unexplained integration-test skips exist (17/17 integration tests passing).
- All empirical outputs are demonstrably source-driven.
- No empirical benchmark values are hardcoded in canonical generation code.
- Five dedicated perturbation tests prove that the major output pathways are dynamic and responsive to underlying evidence.
- Full regression suite passes with 100% success (306/306 tests).

Phase 5 is officially closed. In accordance with the mandatory project rule:
$$\text{Major Phase} \to \text{Full Forensic Audit} \to \text{PASS} \to \text{Next Major Phase}$$
the project is now ready for **Full Project Forensic Audit 5**. Do not begin Phase 6 directly.

```text
============================================================
PHASE 5 REMEDIATION — PASS
SAFE TO BEGIN FULL PROJECT FORENSIC AUDIT 5
============================================================
```
