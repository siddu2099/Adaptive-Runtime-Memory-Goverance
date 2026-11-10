# Audit 9 — Repository Integrity & Final Pre-Phase-10 Forensic Audit Report

**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Audit Phase**: Audit 9 — Post-Phase-9 Repository Integrity & Pre-Phase-10 Forensic Audit  
**Status**: **PASS**  
**Execution Environment**: Python 3.13.2, PostgreSQL 18.1, Ollama (`qwen2.5:7b-instruct`, `nomic-embed-text`), FAISS-CPU 1.8.0  
**Authoritative Hash Invariant**: 100% Bit-for-Bit Verified across all 5 Canonical Benchmark Artifacts  

---

## 1. Executive Summary & Audit Objectives

Audit 9 was conducted following the completion of **Phase 9 (Repository Integrity & Necessary Cleanup)**. The objective was to perform a code-first, result-first, and reproducibility-first forensic audit of the repository, production code, test suites, canonical evidence, results-generation paths, dependency integrity, and security stance.

### Key Audit Findings:
1. **Production Code Immutability**: Phase 9 introduced **zero changes to production code** (`agents/`, `graph/`, `memory/`, `validation/`, `environment/`, `db/`). Production behavior, governance mathematics, AST safety rules, FAISS retrieval, and LangGraph workflow state flow remain 100% identical to the audited and validated baseline.
2. **Fresh-Environment Dependency Reproducibility**: Successfully demonstrated clean-environment installation and import execution using an isolated temporary virtual environment (`scratch/test_clean_venv`). Adding `pandas>=2.0.0` and `matplotlib>=3.7.0` to `requirements.txt` resolved the reproducibility gap without introducing dependency conflicts.
3. **Single Canonical Results Path**: Verified that `scripts/generate_results.py` is the single authoritative results generator. Legacy scripts (`scripts/compute_descriptive_statistics.py`, `scripts/generate_validation_tables.py`, `manuscript/tables/generate_tables.py`) were inspected and confirmed to be thin delegators that call `scripts/generate_results.py` directly.
4. **Historical Evidence Isolation**: Scanned the entire codebase for dependencies on `scratch/`, `archive/`, and `benchmark/historical_preliminary/`. Confirmed that zero production code or canonical results code depends on or consumes historical/scratch files.
5. **Authoritative Evidence Immutability**: All five authoritative benchmark evidence CSV files remain 100% bit-for-bit identical to their frozen SHA-256 baselines (zero bytes altered).
6. **Test Suite Integrity**: All 401 active tests pass (372 unit, 17 integration, 12 environment), with zero skipped tests and zero weakened assertions. All 6 verification scripts pass.
7. **Security Stance**: Zero hardcoded passwords, private tokens, or secrets exist across all tracked files. `.env` is uncommitted and properly gitignored.

**Overall Audit Result**: **Audit 9 — PASS**.

---

## 2. Phase 9 Scope & Modification Verification

The Git working tree was forensically audited to verify that Phase 9 executed strictly within its designated scope:

| Modified File | Classification | Scope / Rationale |
| :--- | :---: | :--- |
| `requirements.txt` | **Required Integrity Fix** | Added `pandas>=2.0.0` and `matplotlib>=3.7.0`. Genuinely required by `scripts/generate_results.py`, `scripts/analyze_reproducibility.py`, and `benchmark/analysis.py`. Prevents `ModuleNotFoundError` during clean clone setup. |
| `README.md` | **Documentation-Only Change** | Synchronized stale test count (from 263 to 401 tests) and documented Section 6 detailing the 7-command reproducibility verification pipeline. Zero executable impact. |
| `phase_9_repository_integrity_report.md` | **Phase Deliverable** | Formally documented Phase 9 inventory, duplicate analysis, and verification outcomes. |

**Zero production code files were altered during Phase 9**.

---

## 3. Fresh-Environment Dependency Reproducibility Proof

To independently prove dependency completeness, an isolated clean virtual environment was instantiated and tested:

```powershell
python -m venv scratch/test_clean_venv
.\scratch\test_clean_venv\Scripts\python -m pip install -r requirements.txt
```

### Execution Outcome:
1. **Pip Installation**: Succeeded with code 0. Installed all declared packages and their transitive dependencies:
   - `langgraph` (1.2.14), `sqlglot` (30.21.0), `faiss-cpu` (1.15.1), `pydantic` (2.13.5), `psycopg2-binary` (2.9.13), `streamlit` (1.65.0), `pytest` (9.1.1), `numpy` (2.5.3), `pandas` (3.0.6), `matplotlib` (3.11.2), `requests` (2.34.2), `python-dotenv` (1.2.4).
2. **Core & Production Module Imports**:
   - `import langgraph, sqlglot, faiss, pydantic, psycopg2, streamlit, pytest, numpy, pandas, matplotlib, requests, dotenv` -> **SUCCESS**
   - `import graph.workflow, memory.governance, memory.vector_store, agents.error_diagnosis, validation.execution_validator` -> **SUCCESS**
   - `import scripts.generate_results, scripts.analyze_reproducibility, benchmark.analysis` -> **SUCCESS**
3. **Pytest Test Collection in Clean Venv**:
   - `.\scratch\test_clean_venv\Scripts\pytest --collect-only -q` -> **401 tests collected in 6.80s** with code 0.
4. **Cleanup**: Temporary test environment was purged following successful verification.

---

## 4. Canonical Evidence Integrity

Cryptographic SHA-256 digests of all five authoritative benchmark CSVs were computed and verified against baseline digests:

| Canonical Evidence File | Authoritative SHA-256 Hash | Post-Phase-9 Hash | Status |
| :--- | :--- | :--- | :---: |
| `benchmark/benchmark_results.csv` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | **100% MATCH** |
| `benchmark/retrieval_telemetry.csv` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | **100% MATCH** |
| `benchmark/seed42/benchmark_results.csv` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | **100% MATCH** |
| `benchmark/seed123/benchmark_results.csv` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | **100% MATCH** |
| `benchmark/seed999/benchmark_results.csv` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | **100% MATCH** |

### Structural & Provenance Invariants:
- Exactly 450 total rows in `benchmark/benchmark_results.csv`.
- Exactly 150 rows in each seed partition (`seed42`, `seed123`, `seed999`).
- Exactly 141 rows in `benchmark/retrieval_telemetry.csv` (47 rows per seed).
- Zero synthetic telemetry records; zero smoke-test run IDs (`run_mode_1_1791274481`).
- Exact cell-level identity between root CSV and `concat(seed42, seed123, seed999)` verified via `pd.testing.assert_frame_equal`.

---

## 5. Results-Generation Single-Path Audit

The complete analytical derivation path was traced:

```text
Authoritative Benchmark CSVs (seed42, seed123, seed999) + Retrieval Telemetry
                                  │
                                  ▼
                     [benchmark/analysis.py]
                                  │
                                  ▼
                    [scripts/generate_results.py]
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    ▼                             ▼                             ▼
Derived Summaries            LaTeX Tables              Publication Figures
(statistical_summary.csv)   (table2_results.tex)      (fig3_retrieval_geometry.png/svg)
(multi_seed_summary.md)     (table8_tradeoff.tex)     (fig4_execsucc_execacc.png/svg)
(results_manifest.json)     (14 tables total)         (fig5_tradeoff.png/svg)
                                                      (fig6_memory_growth.png/svg)
```

### Delegator Script Inspection:
- `scripts/compute_descriptive_statistics.py`:
  ```python
  def compute_descriptive_stats():
      print("[SUPERSEDED GENERATOR] Delegating descriptive statistics to canonical pipeline: scripts/generate_results.py")
      results = compute_all_results_metrics()
      generated = generate_summary_artifacts(results)
      return results["stats_dict"]
  ```
- `scripts/generate_validation_tables.py`:
  ```python
  def generate_validation_tables():
      print("[SUPERSEDED GENERATOR] Delegating validation tables to canonical pipeline: scripts/generate_results.py")
      results = compute_all_results_metrics()
      return generate_publication_tables(results, output_dir=REPO_ROOT / "manuscript/tables")
  ```
- `manuscript/tables/generate_tables.py`:
  ```python
  def generate_tables():
      print("[SUPERSEDED GENERATOR] Delegating table generation to canonical pipeline: scripts/generate_results.py")
      results = compute_all_results_metrics()
      return generate_publication_tables(results, output_dir=REPO_ROOT / "manuscript/tables")
  ```
- **Finding**: All three legacy scripts strictly delegate to `scripts/generate_results.py`. There is no competing or diverging analytical pipeline.

---

## 6. Historical Evidence Isolation & Duplicate File Integrity

1. **Isolation Verification**:
   - `benchmark/historical_preliminary/`: Contains old Phase 3 preliminary evaluation logs. Scanned the codebase: zero active production modules or canonical result scripts read from this directory.
   - `benchmark/pre_remediation_results.csv`: Contains preliminary unnormalized vector telemetry ($S \approx 0.0035$), cited in `manuscript/evidence_package.md` Section K and Figure 3 as a baseline comparator.
   - `archive/`: Contains pre-hardening archive `.zip`. Zero active imports.
2. **Duplicate Artifact Audit (`seed42_results.csv` and `seed42_summary.md`)**:
   - `benchmark/seed42_results.csv` is an exact bit-for-bit duplicate of `benchmark/historical_preliminary/seed42/benchmark_results.csv`.
   - `benchmark/seed42_summary.md` is an exact duplicate of `benchmark/historical_preliminary/seed42/benchmark_summary.md`.
   - Neither file is referenced or imported anywhere in the repository.
   - **Decision**: Classified as **Category F (Accepted Historical Artifacts)**. Per Phase 9 Rule 4 & 16 ("*If uncertain, leave it untouched... Do not invent cleanup work*"), they are retained to avoid breaking external links while having zero impact on canonical execution.

---

## 7. Independent Canonical Metric Recalculation

Recalculated directly from raw CSV evidence (`benchmark/benchmark_results.csv`):

| Metric | Raw Calculation | Stated Canonical Result | Match |
| :--- | :---: | :---: | :---: |
| **Mode 1 Success Rate** | $60 / 75 = 80.00\%$ | $80.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 1 Execution Accuracy** | $45 / 75 = 60.00\%$ | $60.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 2 Success Rate** | $72 / 75 = 96.00\%$ | $96.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 2 Execution Accuracy** | $51 / 75 = 68.00\%$ | $68.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 2 Mean Retries** | $0.2800$ | $0.28 \pm 0.00$ | **EXACT** |
| **Mode 2 Mean Latency** | $6,441.56 \text{ ms}$ | $6,441.56 \pm 105.51 \text{ ms}$ | **EXACT** |
| **Mode 2 Mean Tokens** | $503.72$ | $503.72 \pm 0.42$ | **EXACT** |
| **Mode 4 Success Rate** | $72 / 75 = 96.00\%$ | $96.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 4 Execution Accuracy** | $51 / 75 = 68.00\%$ | $68.00\% \pm 0.00\%$ | **EXACT** |
| **Mode 4 Mean Retries** | $0.3733$ | $0.37 \pm 0.05$ ($0.3733 \pm 0.0462$) | **EXACT** |
| **Mode 4 Mean Latency** | $9,000.59 \text{ ms}$ | $9,000.59 \pm 184.33 \text{ ms}$ | **EXACT** |
| **Mode 4 Mean Tokens** | $602.85$ | $602.85 \pm 28.49$ | **EXACT** |
| **Mode 4 − Mode 2 Retry Delta**| $+0.0933 \text{ (+33.33\%)}$ | $+0.09 \text{ (+33.33\%)}$ | **EXACT** |
| **Mode 4 − Mode 2 Token Delta**| $+99.13 \text{ (+19.68\%)}$ | $+99.13 \text{ (+19.68\%)}$ | **EXACT** |
| **Mode 4 − Mode 2 Latency Delta**| $+2,559.03 \text{ ms (+39.73\%)}$ | $+2,559.03 \text{ ms (+39.73\%)}$ | **EXACT** |

---

## 8. Test Quality & Verification Suite Audit

1. **Test Suite Execution**:
   - `pytest --collect-only -q`: **401 tests collected** in 2.43s.
   - `pytest tests/unit/ -q`: **372 passed** in 73.17s.
   - `pytest tests/integration/ -q`: **17 passed** in 35.07s.
   - `pytest tests/test_env.py -q`: **12 passed** in 15.60s.
   - **Total Active Test Count**: **401 / 401 passed** (zero failures, zero skips).
2. **Assertion Rigor Audit**:
   - Verified that unit tests are genuinely hermetic: offline-safe, mocking external LLM/Ollama services.
   - Verified that regression tests (`test_phase1a` to `test_phase7`) use real structural assertions (e.g., `pd.testing.assert_frame_equal(..., check_exact=True)`, non-zero database invocation proofs).
   - Zero assertions were weakened or removed during Phase 9.
3. **Verification Scripts Audit**:
   - `scripts/verify_phase4_data_integrity.py`: **PASS** (independently checks all 18 mode folders, root, and seed CSVs for 450 rows and 0 smoke records).
   - `scripts/verify_phase4_telemetry_provenance.py`: **PASS** (verifies that raw per-seed telemetry sums exactly to the canonical 141-row aggregate).
   - `scripts/verify_validation_tables.py`: **PASS** (parses LaTeX source tables and cross-checks numerical cells against raw benchmark CSV data).
   - `scripts/validate_temporal_decay.py`: **PASS** (evaluates 63 condition points with $\text{MaxAbsError} = 0.00000000 \le 10^{-4}$).
   - `scripts/analyze_reproducibility.py`: **PASS** (evaluates paired query differences, $ddof=1$, and perturbation sensitivity).
   - `scripts/generate_results.py`: **PASS** (master pipeline executes all 6 stages).

---

## 9. Security & Configuration Audit

- **Environment File**: `.env` is uncommitted and untracked (`git ls-files .env` is empty).
- **Gitignore Protection**: `.gitignore` explicitly ignores `.env`, `*.faiss`, `.pytest_cache/`, `venv/`, `.venv/`.
- **Credential Scan**: Regex and AST scans across all tracked files found **0 hardcoded secrets or API keys**.
- **Configuration Flexibility**: `environment/postgres.py` and `agents/sql_generator.py` consume parameters via `os.getenv` with safe local defaults (`localhost`, `5432`, `armg_db`, `postgres`, `""`).
- **Path Portability**: Zero machine-specific absolute paths in production code or analytical scripts (`REPO_ROOT` dynamically resolved via `Path(__file__).resolve().parent.parent`).

---

## 10. Classification of Findings

Applying the standardized classification taxonomy:

- **Category A (Confirmed Implementation Defect)**: **0 findings**. Core production implementation is defect-free.
- **Category B (Unconfirmed Technical Risk)**: **0 findings**.
- **Category C (Methodological Limitations)**:
  - **C-1**: 25-query cohort sensitivity under retrieved memory prompt syntax (observed on Q08 and Q19, yielding +0.09 retry overhead in Mode 4).
  - **C-2**: Primary benchmark runs under reference epoch $\Delta t = 0$; longitudinal temporal decay is validated separately via the dedicated 63-point simulation harness.
- **Category D (Evidence / Lineage Defect)**: **0 findings**. Canonical evidence is 100% frozen, validated, and traceable.
- **Category E (Unnecessary Component / Change)**: **0 findings**. Phase 9 made only required reproducibility and documentation fixes.
- **Category F (Accepted Design Choices)**:
  - **F-1**: Backwards-compatible delegator scripts (`compute_descriptive_statistics.py`, `generate_validation_tables.py`, `generate_tables.py`) retained to preserve legacy invocations.
  - **F-2**: Historical preliminary evidence retained in `benchmark/historical_preliminary/` and `benchmark/seed42_results.csv` for forensic audit lineage.
  - **F-3**: Explicit declaration of `pandas>=2.0.0` and `matplotlib>=3.7.0` in `requirements.txt`.

---

## 11. Audit 9 Acceptance Gate Decision

### Audit Gate: **PASS**

**Justification**:
1. Zero Category A defects and zero Category D defects exist.
2. Canonical benchmark hashes remain 100% bit-for-bit identical to their frozen baselines.
3. Production runtime logic, governance mathematics, AST validation, and LangGraph workflow behavior are unchanged.
4. Clean-environment installation and import execution were proven in an isolated virtual environment.
5. All 401 active tests and 6 verification scripts pass with zero failures.
6. The single-path results-generation architecture is verified.
7. Historical evidence remains cleanly isolated.

---

## 12. STOP RULE

In strict compliance with the Audit 9 Stop Rule:
- **Audit 9 — PASS** is officially issued.
- **STOP**: Execution is halted. Phase 10 will not begin automatically.
