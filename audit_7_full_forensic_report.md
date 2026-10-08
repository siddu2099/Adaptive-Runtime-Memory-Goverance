# ARMG — FULL PROJECT FORENSIC AUDIT 7
## POST-PHASE-7 REPRODUCIBILITY, DATA LINEAGE & STATISTICAL AUDIT
### CODE-FIRST ADVERSARIAL AUDIT & SCIENTIFIC VERIFICATION

**Audit Date:** October 7, 2026  
**Auditor:** Lead Forensic AI Engineer  
**Scope:** Complete post-Phase-7 codebase, data lineage architecture, query-level paired comparisons, statistical populations and aggregations, configuration provenance, telemetry provenance, and authoritative benchmark immutability.  
**Audit Gate Status:** **FULL PROJECT FORENSIC AUDIT 7 — PASS**  
**Authorization:** **PHASE 7 OFFICIALLY COMPLETE — READY FOR FINAL SYSTEM INTEGRATION / PHASE 8 ARCHITECTURE**

---

## 1. EXECUTIVE AUDIT SUMMARY & CORE VERDICT

This audit was conducted under the strict instruction:
> **Determine whether the project, in its current implementation state after Phase 7, contains any implementation defects, methodological defects, evidence defects, unnecessary components, inconsistencies, or reproducibility problems that could undermine engineering correctness, experimental validity, benchmark credibility, or examination standards.**

The forensic investigation confirms:
1. **Zero Implementation Defects (Category A: 0)**: Deep code-level auditing of the core governance engine, deterministic error diagnosis, SQLGlot execution guard, FAISS vector indexing, state workflow graph, and temporal decay engine revealed zero runtime or functional errors.
2. **Authoritative Evidence Immutability**: All five primary benchmark datasets were hashed and verified against frozen cryptographic baselines. Zero byte-level mutations, row reorderings, or synthetic injections have occurred.
3. **Data Lineage Integrity**: Every reported metric in the manuscript (Tables II, III, IV, VII, VIII, IX, Tables A–E, and Figures 3–6) traces directly and deterministically back to raw execution records in `benchmark/benchmark_results.csv` and `benchmark/retrieval_telemetry.csv`.
4. **Statistical Rigor & Population Segregation**:
   - Query-level paired analysis ($N = 75$ evaluations, joining strictly on `(seed, query_id)`) and seed-level aggregate analysis ($N = 3$ runs across seeds 42, 123, 999) are strictly segregated in data structures and reporting.
   - Dispersion metrics ($\pm \sigma$) explicitly specify $\text{ddof} = 1$ sample standard deviation across runs.
   - Generation temperature $\tau = 0.0$ is accurately disclosed as deterministic repeated trials under controlled environment conditions rather than independent stochastic sampling.
5. **Classification Accuracy & Latency Orthogonality**:
   - The mutually exclusive hierarchical partition strictly sums to **75 / 75 pairs (100.0%)**:
     - Execution Failure: 3 pairs (4.00%)
     - Mode 4 Extra Retries: 5 pairs (6.67%)
     - Semantic Divergence: 19 pairs (25.33%)
     - Parity with Token Overhead: 6 pairs (8.00%)
     - Outcome & Token Parity: 42 pairs (56.00%)
   - Latency overhead is correctly decoupled and treated as an independent, orthogonal runtime dimension (72/75 pairs exhibit positive latency delta due to memory governance and FAISS index search).
   - Overlapping operational annotations (21 divergent semantic queries, 5 extra-retry queries, 2 overlap queries at Q19) reconcile mathematically with the hierarchical partition ($21 = 19 + 2$).
6. **Active Test Suite Health**: All **401 active tests** (372 unit, 17 integration, 12 environment) pass with 0 failures, 0 errors, and 0 skips.

---

## 2. AUDIT SCOPE & METHODOLOGY

The audit examined nine primary architectural boundaries:

```text
[Raw Execution Data] ──> [Verification Scripts] ──> [Statistical Engine] ──> [LaTeX/Manuscript Outputs]
         │                          │                          │                        │
         ├── benchmark_results.csv  ├── verify_phase4_data     ├── analysis.py          ├── table2_results.tex
         ├── retrieval_telemetry    ├── verify_telemetry       ├── analyze_repro        ├── table8_tradeoff.tex
         └── seed partitions        └── verify_validation      └── statistical_summary  └── fig3-6 (PNG/SVG)
```

### Forensic Inspection Checklist:
- **Core ARMG Engine**: `graph/workflow.py`, `graph/state.py`, `memory/governance.py`, `memory/vector_store.py`, `agents/repair_agent.py`, `agents/sql_generator.py`, `validation/execution_validator.py`.
- **Phase 2 FAISS Telemetry**: Distance metric ($1 / (1 + d^2)$), index mapping, candidate logging, retrieval accounting.
- **Phase 3 Test Architecture**: Unit hermeticity, marker tagging, zero unauthorized network or database calls in unit tests.
- **Phase 4 Authoritative Benchmark**: Root dataset equivalence to seed partition concat, zero smoke-test contamination, SHA-256 verification.
- **Phase 5 Results Pipeline**: Dynamic data-driven derivation of figures and tables, zero hardcoded empirical metrics in generation scripts.
- **Phase 6 Temporal Decay**: Reference epoch stability, controlled clock idempotence, archive purge threshold (30 days), resurrection prevention.
- **Phase 7 Lineage & Reproducibility**: `analyze_reproducibility.py`, `query_level_mode2_vs_mode4.csv`, `configuration_provenance.json`, `metric_lineage.json`, `test_phase7_reproducibility.py`.

---

## 3. EVIDENCE IMMUTABILITY & HASH VERIFICATION

Cryptographic SHA-256 digests were computed for all five authoritative benchmark files and compared against the baseline hashes established in Phase 4:

| File Path | Authoritative Frozen SHA-256 Digest | Audit Verification Digest | Match Status |
|:---|:---|:---|:---:|
| `benchmark/benchmark_results.csv` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | **MATCH (100% Bit-for-Bit)** |
| `benchmark/retrieval_telemetry.csv` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | **MATCH (100% Bit-for-Bit)** |
| `benchmark/seed42/benchmark_results.csv` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | **MATCH (100% Bit-for-Bit)** |
| `benchmark/seed123/benchmark_results.csv` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | **MATCH (100% Bit-for-Bit)** |
| `benchmark/seed999/benchmark_results.csv` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | **MATCH (100% Bit-for-Bit)** |

**Forensic Finding:** Zero authoritative files have been overwritten, re-seeded, or re-run. The evidence package remains completely frozen and untampered.

---

## 4. COMPREHENSIVE FINDINGS CLASSIFICATION TABLE

| Finding ID | Classification | Subsystem | Description | Impact / Resolution | Status |
|:---|:---:|:---|:---|:---|:---:|
| **F-01** | **F (Accepted Choice)** | Phase 7 Reporting | Decoupling latency from Outcome & Token Parity | Correctly treats runtime latency overhead as an orthogonal architectural dimension | Verified |
| **F-02** | **F (Accepted Choice)** | Memory Geometry | Inverse squared Euclidean metric ($1/(1+d^2)$) | Monotonically bounds L2 distance into $[0, 1]$ similarity space | Verified |
| **F-03** | **F (Accepted Choice)** | Statistical Framework | Deterministic trials at $\tau=0.0$ | Accurately reported as deterministic session runs rather than random sampling | Verified |
| **F-04** | **C (Methodology)** | LLM Scope | Single LLM architecture (`qwen2.5:7b-instruct`) | Disclosed experimental boundary; multi-model generalization is future work | Disclosed |
| **F-05** | **C (Methodology)** | Domain Scope | Retail/enterprise data warehouse schema (25 queries) | Benchmark covers 5 structural complexity categories; general text-to-SQL is future work | Disclosed |
| **F-06** | **B (Unconfirmed Risk)** | Concurrency | Thread-safety of in-memory metadata mappings | Sequential execution in research pipeline is thread-safe; mutex needed if migrated to web API | Non-Blocking |

---

## 5. DETAILED SUBSYSTEM AUDIT REPORTS

### 5.1 Core ARMG Runtime & State Graph
- **State Immutability**: All nodes in `graph/workflow.py` return delta dictionary updates merged via LangGraph reducers rather than mutating shared references in place.
- **Provenance Isolation**: `applied_memory_id` is recomputed per repair attempt based strictly on the current attempt's diagnosis root cause and repair rule (`workflow.py` lines 390–408). A memory applied in attempt $k$ does not erroneously leak into attempt $k+1$.
- **Negative Constraints**: Pruned identifiers are extracted deterministically by `DiagnosticResult.negative_constraints` and rendered in the `[STRICT REPAIR CONSTRAINTS]` block. AST guard validates that forbidden identifiers do not recur in repaired SQL.
- **SQLGlot AST Safety Guard**: `validate_sql` rejects DDL/DML, multi-statement payloads, and destructive administrative commands while correctly ignoring SQL keywords inside single-quoted strings or comments (`execution_validator.py` lines 37–45).

### 5.2 Phase 2 FAISS Telemetry & Retrieval
- **Index Architecture**: CPU-based `faiss.IndexFlatL2` wrapped in `faiss.IndexIDMap2`.
- **Normalization Invariant**: Queries and memory contexts are embedded using `nomic-embed-text` with unit L2 normalization ($||v||_2 = 1.0$).
- **Telemetry Accounting**: Exactly 141 rows recorded in `benchmark/retrieval_telemetry.csv` (47 rows per seed). Across all 3 seeds, exactly 16 candidate vectors per seed (48 total) exceed the retrieval threshold $\tau = 0.50$ and are admitted to prompt context.
- **Active Memory Filtering**: `workflow.py` line 200 explicitly excludes `ARCHIVED` and `DELETED` records from prompt injection even if similarity exceeds $\tau = 0.50$.

### 5.3 Phase 3 Testing Architecture
- **Hermetic Isolation**: All 371 unit tests execute in complete offline isolation without active connections to Ollama or PostgreSQL.
- **Explicit Markers**: Pytest configuration (`pytest.ini` and `tests/conftest.py`) automatically maps test paths to markers:
  - `tests/unit/` $\to$ `@pytest.mark.unit`
  - `tests/integration/` $\to$ `@pytest.mark.integration`
  - `tests/test_env.py` $\to$ `@pytest.mark.environment`
- **Zero Mock Contamination**: Unit tests employ pure Python stub fixtures with zero side-effects on disk benchmark files.

### 5.4 Phase 4 Authoritative Benchmark Integrity
- **Dataset Consistency**:
  - `benchmark/benchmark_results.csv` contains exactly 450 rows across 23 columns.
  - `benchmark/seed{42,123,999}/benchmark_results.csv` each contain exactly 150 rows.
  - Root dataset is cell-for-cell identical to the concatenation of the three seed files (`assert_frame_equal(df_root, df_concat, check_exact=True)` passes).
- **Smoke-Test Exclusion**: Verified zero test/smoke artifacts exist in any benchmark dataset (`scripts/verify_phase4_data_integrity.py` passes).

### 5.5 Phase 5 Automated Results Pipeline
- **Dynamically Derived Artifacts**:
  - All 14 LaTeX tables in `manuscript/tables/` are generated dynamically by `scripts/generate_results.py` and `manuscript/tables/generate_tables.py`.
  - Figures 3, 4, 5, and 6 are dynamically plotted from CSV run logs with zero hardcoded coordinate overrides.
- **Validation Table Audits**:
  - Table A (Figure 3 validation): Reproduces retrieval metrics across all 25 queries.
  - Table B (Figure 4 validation): Reproduces ExecSucc (417/450) and ExecAcc (300/450).
  - Table C (Figure 5 validation): Matches Mode 2 vs Mode 4 trade-off values.
  - Table D (Figure 6 validation): Matches memory store plateau (3 items) vs naive store growth (23 items).
  - Table E (Validation matrix): Confirms complete mathematical traceability.

### 5.6 Phase 6 Temporal Decay & Resurrection Prevention
- **Decay Equation**: Implemented continuous formulation $C(t) = C_{\text{ref}} e^{-\lambda \Delta t}$ with $\lambda = 0.05/\text{day}$ matches theoretical decay with $0.00000000$ error across all 63 condition points.
- **Resurrection Prevention**:
  - `record_success()` preserves `ARCHIVED` and `DELETED` states without escalating them back to `STABLE` or `ACTIVE`.
  - `record_failure()` preserves `ARCHIVED` and `DELETED` states without mutating them.
  - Verified by dedicated unit tests in `tests/unit/test_memory_governance.py` and `tests/unit/test_phase6_temporal_decay.py`.
- **Archive Retention Purge**: Memories in `ARCHIVED` status for $\ge 30$ days transition irrevocably to `DELETED`.

### 5.7 Phase 7 Lineage & Statistical Layer
- **Pairing Integrity**: Mode 2 and Mode 4 are joined strictly on `(seed, query_id)` across all 75 evaluations, eliminating cross-seed contamination.
- **Population Segregation**:
  - Query-level population ($N = 75$) evaluates paired differences and distribution across all distinct queries and sessions.
  - Seed-level population ($N = 3$) evaluates run-to-run dispersion across experimental seeds.
  - Stored in distinct top-level keys in `benchmark/statistical_summary.json` to prevent population mixing.
- **Mutually Exclusive Classification**:
  - `Execution Failure`: 3 pairs (4.00%)
  - `Mode 4 Extra Retries`: 5 pairs (6.67%)
  - `Semantic Divergence`: 19 pairs (25.33%)
  - `Parity with Token Overhead`: 6 pairs (8.00%)
  - `Outcome & Token Parity`: 42 pairs (56.00%)
  - Sum: Exactly 75 pairs (100.0%).
- **Independent Orthogonal Overlaps**:
  - 21 queries exhibit semantic divergence (accuracy = 0.0 while execution succeeds).
  - 5 queries exhibit extra retries ($\Delta\text{Retries} > 0$).
  - Exactly 2 queries (Q19 in seeds 123 and 999) overlap both conditions.
  - Mathematical reconciliation verified: $21 = 19 \text{ (hierarchical)} + 2 \text{ (extra-retry overlap)}$.

---

## 6. TEST EXECUTION EVIDENCE

All test suites and verification scripts were executed locally in the audited environment:

```text
================================================================================
ARMG FULL TEST SUITE EXECUTION REPORT
================================================================================

1. Phase 7 Dedicated Unit Tests:
   pytest tests/unit/test_phase7_reproducibility.py -v
   -> 16/16 PASSED (0.58s)

2. Total Unit Tests:
   pytest tests/unit/ -q
   -> 372/372 PASSED (68.69s)

3. Total Integration Tests:
   pytest tests/integration/ -q
   -> 17/17 PASSED (30.84s)

4. Environment Diagnostic Tests:
   pytest tests/test_env.py -q
   -> 12/12 PASSED (13.35s)

--------------------------------------------------------------------------------
TOTAL ACTIVE TESTS: 401 / 401 PASSED (0 FAILED, 0 SKIPPED)
--------------------------------------------------------------------------------

5. Phase 4 Data Integrity Verification:
   python scripts/verify_phase4_data_integrity.py
   -> PASS (450 rows, 0 smoke records, 141 telemetry rows)

6. Phase 4 Telemetry Provenance Audit:
   python scripts/verify_phase4_telemetry_provenance.py
   -> PASS (All 8 provenance checks passed)

7. Numerical Validation Table Verification:
   python scripts/verify_validation_tables.py
   -> PASS (All 6 validation checks passed)

8. Master Results Generation Pipeline:
   python scripts/generate_results.py
   -> PASS (All 6 stages completed successfully)

9. Temporal Decay Validation Engine:
   python scripts/validate_temporal_decay.py
   -> PASS (All 10 steps passed, 63 condition points verified)

10. Reproducibility & Statistical Analysis Pipeline:
    python scripts/analyze_reproducibility.py
    -> PASS (All 10 steps passed, exact reconciliation confirmed)

================================================================================
ALL VERIFICATION SUITES AND AUDIT ENGINES PASSED WITH ZERO ERRORS
================================================================================
```

---

## 7. PUBLICATION & B.TECH EXAMINATION DEFENSE READINESS

### 7.1 Defense Against Peer-Review Skepticism
1. **"Does ARMG improve accuracy over stateless self-correction?"**
   - *Forensic Finding*: ARMG achieves identical $68.0\%$ execution accuracy and identical $96.0\%$ execution success compared to Mode 2. ARMG does not claim unearned accuracy gains; its documented contribution is bounded negative constraint enforcement and structured memory governance preventing memory growth ($3$ items vs $23$ items in naive RAG).
2. **"Why does Mode 4 take longer and use more tokens?"**
   - *Forensic Finding*: Mode 4 incurs $+19.68\%$ token overhead and $+39.73\%$ latency overhead due to embedding generation, FAISS index queries, and prompt memory injection. This trade-off is explicitly documented in Table VIII and Table C.
3. **"Are results reproducible across random seeds?"**
   - *Forensic Finding*: Generation was executed at temperature $0.0$ under deterministic repeated trials. Query-level operational behaviors and pair-level mutually exclusive classifications are precisely distinguished by canonical evidence:
     - **Query-Level Dimensions (Non-mutually exclusive due to empirical overlap)**:
       - **14 Outcome & Token Parity queries**: 14 benchmark queries (Q01, Q02, Q03, Q06, Q07, Q09, Q10, Q12, Q16, Q20, Q21, Q22, Q23, Q24) exhibit Outcome & Token Parity across the three repeated runs; latency remains an independent runtime-overhead dimension.
       - **7 Semantic Divergence queries**: 7 distinct queries (Q05, Q14, Q15, Q17, Q18, Q19, Q25) succeed in PostgreSQL execution but consistently fail relational tuple equivalence against gold SQL across all three seeds.
       - **1 persistent Execution Failure query**: Query Q11 fails PostgreSQL syntax execution across all three seeds in both Mode 2 and Mode 4 due to a persistent schema attribute error (`column g.full_date does not exist`).
       - **2 queries with Mode 4 extra-retry behavior**:
         - Q08 incurs $+1$ retry in all three seeds ($3$ positive retry-delta pairs).
         - Q19 incurs $+2$ retries in seeds 123 and 999 ($2$ positive retry-delta pairs).
         - Total positive retry-delta pairs across the benchmark = $3 + 2 = 5$ pairs.
       - **2 queries with Parity with Token Overhead**: Queries Q04 and Q13 achieve relational accuracy with identical retries, but Mode 4 incurs token overhead due to memory prompt context injection across all three seeds ($6$ pairs).
       - *Note on Overlap*: Query Q19 simultaneously exhibits semantic divergence (all 3 seeds) and Mode 4 extra retries (seeds 123, 999), demonstrating why query-level dimensions cannot be forced into a naive mutually exclusive sum.
     - **Pair-Level Mutually Exclusive Classification ($N = 75$ pairs, summing strictly to $100.0\%$)**:
       - `Execution Failure`: 3 pairs (4.00%)
       - `Mode 4 Extra Retries`: 5 pairs (6.67%)
       - `Semantic Divergence`: 19 pairs (25.33%) (21 total divergent pairs minus 2 extra-retry overlap pairs)
       - `Parity with Token Overhead`: 6 pairs (8.00%)
       - `Outcome & Token Parity`: 42 pairs (56.00%)
       - $\text{Total} = 3 + 5 + 19 + 6 + 42 = 75\text{ pairs } (100.00\%)$.

### 7.2 Examiner Checklist
- [x] Mathematics of utility, admission, decay, and reinforcement explicitly proven and implemented in Python.
- [x] Memory lifecycle transitions (NEW $\to$ ACTIVE $\to$ STABLE $\to$ DECAYING $\to$ ARCHIVED $\to$ DELETED) strictly enforced and tested against resurrection bugs.
- [x] Zero empirical numbers hardcoded in tables or charts.
- [x] Clean separation of unit tests (offline/mocked) and integration tests (live PostgreSQL/Ollama).
- [x] 100% reproducible data pipeline starting from frozen raw logs.

---

## 8. FINAL AUDIT VERDICT & GATE DECISION

```text
======================================================================
           FULL PROJECT FORENSIC AUDIT 7 VERDICT: PASS
======================================================================

  [PASS] Core ARMG Implementation & Graph Architecture
  [PASS] Phase 2 FAISS Retrieval & Telemetry Provenance
  [PASS] Phase 3 Test Architecture & Hermetic Isolation
  [PASS] Phase 4 Authoritative Benchmark Integrity & Frozen Hashes
  [PASS] Phase 5 Automatic Data-Driven Results Pipeline
  [PASS] Phase 6 Temporal-Decay Engine & Lifecycle Immutability
  [PASS] Phase 7 Reproducibility, Lineage & Statistical Rigor
  [PASS] 401/401 Active Regression & Unit Tests Passing
  [PASS] Authoritative Benchmark Hashes 100% Bit-for-Bit Verified

GATE STATUS: PASS
PHASE 7 IS OFFICIALLY CLOSED.
THE PROJECT IS FULLY AUDITED, REPRODUCIBLE, AND STABLE.
======================================================================
```

**STOPPING POINT**: Audit 7 is complete. As mandated by project rules, Phase 8 is **not** automatically initiated. Further actions await user instructions.
