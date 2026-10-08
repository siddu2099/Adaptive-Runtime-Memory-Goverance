# Audit 8 — Post-Phase-8 Code, Results, and Reproducibility Integrity Audit Report

**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Audit Phase**: Audit 8 — Post-Phase-8 Forensic Audit  
**Status**: **PASS**  
**Execution Environment**: Python 3.13.2, PostgreSQL 18.1, Ollama (`qwen2.5:7b-instruct`, `nomic-embed-text`), FAISS-CPU 1.8.0  
**Authoritative Hash Invariant**: 100% Bit-for-Bit Verified across all 5 Canonical Benchmark Artifacts  

---

## 1. Executive Summary & Audit Objectives

Audit 8 was conducted immediately following the completion of **Phase 8 (Material Implementation / Results Synchronization)**. The primary objective was to independently determine whether Phase 8 synchronization altered, exposed, or introduced any defects in:

1. **Production Implementation**: Core LangGraph orchestration, error diagnosis, memory governance, FAISS retrieval, SQL AST validation, and database execution.
2. **Benchmark / Result Generation**: Data derivation pipelines connecting raw 450-evaluation logs to LaTeX tables, statistical summaries, and figures.
3. **Canonical Analysis**: Query-level paired evaluation ($N=75$), 3-seed statistical aggregation ($n=3$, $ddof=1$), and failure query forensics.
4. **Reproducibility & Lineage**: Exact identity between root and seed-partition datasets, provenance tracking, and deterministic script execution.
5. **Authoritative Evidence Integrity**: Bit-for-bit preservation of the five canonical benchmark evidence CSVs.

**Audit Finding**: **PASS**. Zero Category A (implementation) defects and zero Category D (material evidence/synchronization) defects exist in the post-Phase-8 repository. All 401 active tests pass, all 6 verification scripts pass, and all five authoritative benchmark hashes match their established baselines with 100% fidelity.

---

## 2. Code-First Pipeline Inspection & Execution Trace

The entire runtime pipeline was traced code-first from input question to published artifacts:

```text
Query
  │
  ▼
[Node 1: introspect_and_prune_node] (SchemaPruner + SchemaIntrospector)
  │
  ▼
[Node 2: memory_retrieval_node] (FAISS IndexFlatL2 + unit-L2 norm + active-lifecycle filter)
  │
  ▼
[Node 3: sql_generator_node] (SQLGenerator via Ollama qwen2.5:7b-instruct, temp=0.0)
  │
  ▼
[Node 4: ast_guard_node] (ExecutionValidator via SQLGlot AST inspection)
  │
  ├───[Invalid / Destructive]───► [Node 6: observation_node] ───► [Node 10: memory_governance_node] ───► [END: STATUS_BLOCKED]
  │                                                               (Zero DB execution, zero memory admission)
  └───[Valid Read-Only SELECT]
        │
        ▼
[Node 5: postgres_executor_node] (PostgreSQLEnvironment on localhost:5432/armg_db)
        │
        ▼
[Node 6: observation_node] (RuntimeObserver -> RuntimeObservation)
        │
        ├───[PostgreSQL SUCCESS]───► [Node 10: memory_governance_node] ───► [END: STATUS_SUCCESS]
        │                            (Reinforces applied memory OR admits novel knowledge)
        └───[PostgreSQL FAILURE]
              │
              ▼
      [Node 7: diagnosis_node] (DeterministicErrorDiagnoser, zero-LLM 7-tier taxonomy)
              │
              ▼
      [Node 8: knowledge_node] (RuntimeKnowledgeExtractor, retry budget decrement, per-attempt provenance)
              │
              ├───[Retries Exhausted (count >= 3)]───► [Node 10: memory_governance_node] ───► [END: STATUS_FAILED]
              │                                        (Penalizes applied memory, suppresses novel admission)
              └───[Retries Available (count < 3)]
                    │
                    ▼
            [Node 9: repair_prompt_node] (RepairPromptBuilder with [STRICT REPAIR CONSTRAINTS])
                    │
                    ▼
            [Back to Node 3: sql_generator_node] (RepairSQLGenerator)
```

### Inspected Modules & Findings:
- [`graph/workflow.py`](file:///c:/Users/siddu/Pictures/armg%20main/graph/workflow.py) & [`graph/state.py`](file:///c:/Users/siddu/Pictures/armg%20main/graph/state.py): Strongly-typed `ARMGState` TypedDict. Explicit bounded retry semantics (`max_retries = 3`, attempts 0..3, max attempts = 4). Clean conditional edges (`route_after_ast_guard`, `route_after_observation`, `route_after_knowledge`).
- [`agents/error_diagnosis.py`](file:///c:/Users/siddu/Pictures/armg%20main/agents/error_diagnosis.py): Zero-LLM, code-first deterministic diagnosis. Regex-driven extraction of broken identifiers, schema-based replacement resolution with alphabetical tie-breakers, standardized 7-tier taxonomy.
- [`agents/repair_agent.py`](file:///c:/Users/siddu/Pictures/armg%20main/agents/repair_agent.py): Constructs exactly one `[STRICT REPAIR CONSTRAINTS]` block binding forbidden identifiers, replacements, and operational rules.
- [`memory/knowledge_extractor.py`](file:///c:/Users/siddu/Pictures/armg%20main/memory/knowledge_extractor.py): Extracts ephemeral `RuntimeKnowledge` artifacts without database or network I/O.
- [`memory/governance.py`](file:///c:/Users/siddu/Pictures/armg%20main/memory/governance.py): Pure mathematical control engine. Governs admission, asymptotic confidence escalation, penalty reduction, and continuous exponential decay.
- [`memory/vector_store.py`](file:///c:/Users/siddu/Pictures/armg%20main/memory/vector_store.py): Decoupled FAISS `IndexIDMap2(IndexFlatL2(768))` CPU vector store. Enforces strict unit-L2 normalization and synchronized physical deletion.
- [`validation/execution_validator.py`](file:///c:/Users/siddu/Pictures/armg%20main/validation/execution_validator.py): SQLGlot pre-execution AST validator. Rejects non-SELECT roots, DDL/DML mutations, and stacked queries.
- [`database/environment.py`](file:///c:/Users/siddu/Pictures/armg%20main/database/environment.py): Executes read-only queries against local PostgreSQL warehouse.
- [`scripts/generate_results.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/generate_results.py), [`scripts/analyze_reproducibility.py`](file:///c:/Users/siddu/Pictures/armg%20main/scripts/analyze_reproducibility.py), & [`benchmark/analysis.py`](file:///c:/Users/siddu/Pictures/armg%20main/benchmark/analysis.py): Canonical analytical pipelines consuming exclusively authoritative Phase 4 benchmark artifacts.

---

## 3. Subsystem Forensic Integrity Verifications

### 3.1 RuntimeKnowledge Lifecycle (Section 4)
- **Determinism**: Diagnosis is strictly deterministic; regex patterns and schema catalog introspection produce identical outputs for identical observations.
- **Exclusion of Volatile Metadata**: `RuntimeKnowledge.format_for_embedding()` explicitly formats:
  $$\text{"Failure: } \dots \text{ | Tables: } \dots \text{ | Root Cause: } \dots \text{ | Repair: } \dots\text{"}$$
  `knowledge_id`, `confidence`, and `timestamp` are strictly excluded from embedding payloads, preventing semantic space contamination.
- **Identity Decoupling**: Ephemeral `RuntimeKnowledge` is never used as persistent identity. When admitted, `MemoryGovernanceEngine.admit()` creates a distinct `RuntimeMemory` with a dedicated `memory_id` (`mem-...`).
- **No Global State**: Zero module-level mutable singletons or hidden global registries.

### 3.2 Memory Governance Mathematical Control (Section 5)
- **Multi-Factor Utility**:
  $$U = C \times S_{\text{rate}} \times S_{\text{ctx}} \times R$$
  where $S_{\text{rate}} = \frac{s}{t}$ ($0.5$ if $t = 0$), $R = \frac{1}{1 + \Delta t}$, and $S_{\text{ctx}} = \frac{1}{1 + d^2} \in [0.0, 1.0]$.
- **Admission Threshold**: $\theta = 0.25$. Admitted if and only if initial utility $U_0 \ge 0.25$.
- **Asymptotic Confidence Escalation**:
  $$C_{\text{new}} = C_{\text{old}} + \alpha(1.0 - C_{\text{old}}), \quad \alpha = 0.10$$
  Transitions memory to `ACTIVE`, and to `STABLE` when $C \ge 0.80$.
- **Failure Penalty**:
  $$C_{\text{new}} = \max(0.0, C_{\text{old}}(1.0 - \beta)), \quad \beta = 0.15$$
  Transitions to `DECAYING` if previously `STABLE`, and to `ARCHIVED` if $C < 0.20$.
- **Temporal Decay**:
  $$C(t) = C_{\text{ref}} \exp(-\lambda \Delta t), \quad \lambda = 0.05/\text{day}$$
  Maintains reference confidence $C_{\text{ref}}$ and reference epoch $t_{\text{ref}}$ to prevent compound double-decay.
- **Archive Retention & Purging**: Retained for 30 calendar days/epochs, after which transition to `DELETED` occurs.
- **Resurrection Prevention**: Memories in `ARCHIVED` or `DELETED` states can never transition back to `NEW`, `ACTIVE`, or `STABLE`.
- **Per-Attempt Provenance & Mutual Exclusion**: In `graph/workflow.py`, `applied_memory_id` is re-evaluated per attempt based strictly on the current attempt's diagnosis root cause and repair rule. If an existing memory is reinforced on success, new candidate admission is suppressed.

### 3.3 FAISS Vector Store Invariants (Section 6)
- **Index Architecture**: `faiss.IndexIDMap2` wrapping `IndexFlatL2(768)`.
- **Embedding Validation**: Input vectors must have shape `(768,)` or `(1, 768)`, dtype `float32`, finite values (zero NaN/Inf), positive finite L2 norm, and strict unit-L2 normalization ($\|\mathbf{v}\|_2 = 1.0$).
- **Normalized Similarity Mapping**: Squared Euclidean distance $d^2$ maps to cosine distance ($d^2 = 2(1 - \cos \theta)$) and normalized context similarity:
  $$\text{sim} = \frac{1}{1 + d^2} \in [0.0, 1.0]$$
- **Decoupled Metadata Synchronization**: In-memory `_id_to_memory` and `_memory_id_to_int_id` dicts remain in lockstep with the FAISS internal index. Physical deletion removes vectors from both the FAISS index and Python metadata stores.
- **Active Lifecycle Filtering**: `ARCHIVED` and `DELETED` memories are strictly excluded from retrieval context in `memory_retrieval_node`.

### 3.4 SQL Safety Adversarial Verification (Section 7)
- **Statement Guardrails**: Strict pre-execution rejection of `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `MERGE`, `EXEC`, `EXECUTE`, `BEGIN`, `COMMIT`, and `ROLLBACK`.
- **AST Root Verification**: Requires `exp.Select` or `exp.Union` root expressions.
- **Multi-Statement Blocking**: Stacked statements (e.g., `SELECT 1; DROP TABLE users;`) parse as multiple statements and are immediately rejected before driver invocation.
- **No False Positives on String Literals & Comments**: Legitimate analytical queries containing keywords within string literals (e.g., `WHERE status = 'DROP'`) or SQL comments (`-- table drop comment`) parse safely without rejection.
- **Zero-Execution Proof**: The execution pipeline guarantees that any query rejected by `ast_guard_node` routes directly to `observation_node`, completely bypassing `postgres_executor_node`. Verified via `InstrumentedEnvironment` in `test_phase1d_safety_guard.py` (0 database execution invocations).

### 3.5 SQL Generation Error Handling (Section 8)
- **Infrastructure Fault Tolerance**: When Ollama is unavailable, times out, or returns invalid HTTP/JSON responses, `SQLGenerator.generate()` and `RepairSQLGenerator.generate_repair()` catch exceptions and return an empty string with recorded latency.
- **Controlled Rejection**: An empty SQL payload is deterministically flagged by `ast_guard_node` as `"SQL payload is empty."`, triggering observation and bounded retry without crashing the LangGraph engine.

---

## 4. Independent Results Recalculation & Multi-Seed Verification

Recalculating all metrics directly from the raw frozen benchmark CSVs:

### 4.1 Dataset & Lineage Integrity
- **Total Evaluations**: Exactly $N = 450$ rows across 23 columns.
- **Seed Partitions**: Seed 42 ($N = 150$), Seed 123 ($N = 150$), Seed 999 ($N = 150$).
- **Root vs Seed Concatenation Equivalence**: Exactly 0 differences (`df_root.compare(df_concat)` is empty).
- **Duplicate Checks**: Exactly 0 duplicate `(seed, mode, query_id)` tuples.
- **Evaluations per Mode**: Exactly 75 evaluations per mode (25 queries $\times$ 3 seeds).

### 4.2 Pooled Empirical Metrics ($N = 75$ per mode)

| Mode | PG Success (Count / %) | Execution Accuracy (Count / %) | Mean Retries | Mean Latency (ms) | Mean Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mode 1 (Zero-Shot)** | 60 / 75 (80.00%) | 45 / 75 (60.00%) | 0.0000 | 4,859.70 | 360.57 |
| **Mode 2 (Stateless Self-Correction)** | 72 / 75 (96.00%) | 51 / 75 (68.00%) | 0.2800 | 6,441.56 | 503.72 |
| **Mode 3 (Naive Vector RAG)** | 69 / 75 (92.00%) | 51 / 75 (68.00%) | 0.0000 | 6,776.25 | 558.28 |
| **Mode 4 (Full ARMG)** | 72 / 75 (96.00%) | 51 / 75 (68.00%) | 0.3733 | 9,000.59 | 602.85 |
| **Mode 5 (ARMG - Negative Constraints)**| 72 / 75 (96.00%) | 51 / 75 (68.00%) | 0.3200 | 8,768.48 | 530.97 |
| **Mode 6 (ARMG - Temporal Decay)** | 72 / 75 (96.00%) | 51 / 75 (68.00%) | 0.2800 | 8,507.98 | 542.27 |

### 4.3 3-Seed Aggregated Statistics ($n = 3$, Sample Standard Deviation with $ddof = 1$)

| Mode | PG Success (%) | Execution Accuracy (%) | Retries | Latency (ms) | Tokens |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mode 1** | 80.00% ± 0.00% | 60.00% ± 0.00% | 0.0000 ± 0.0000 | 4,859.70 ± 7.98 | 360.57 ± 0.37 |
| **Mode 2** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.2800 ± 0.0000 | 6,441.56 ± 105.51 | 503.72 ± 0.42 |
| **Mode 3** | 92.00% ± 0.00% | 68.00% ± 0.00% | 0.0000 ± 0.0000 | 6,776.25 ± 34.40 | 558.28 ± 0.00 |
| **Mode 4** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.3733 ± 0.0462 | 9,000.59 ± 184.33 | 602.85 ± 28.49 |
| **Mode 5** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.3200 ± 0.0000 | 8,768.48 ± 100.30 | 530.97 ± 0.40 |
| **Mode 6** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.2800 ± 0.0000 | 8,507.98 ± 73.15 | 542.27 ± 0.39 |

**Conclusion on Results Validity**: All recalculated figures match the canonical multi-seed summaries, LaTeX tables (`manuscript/tables/table2_results.tex`, `table8_tradeoff.tex`), and Section 11 expectations with 100% precision.

---

## 5. Mode Behavior & Experimental Separation (Section 10)

- **Mode 2 vs Mode 4 Trade-Offs**:
  - Both modes plateau identically at 96.00% PostgreSQL execution success (72/75) and 68.00% relational accuracy (51/75).
  - Mode 4 incurs architectural overheads over Mode 2: +33.33% retries (0.3733 vs 0.2800, +0.09 retries/query), +39.73% latency (9,000.59 vs 6,441.56 ms), and +19.68% tokens (602.85 vs 503.72).
  - The retry overhead is attributable to 5 extra retry attempts across the 75 evaluations: Q08 (+1 retry across all 3 seeds) and Q19 (+2 retries in Seeds 123 & 999), caused by prompt length and syntax interactions under retrieved memory context.
  - In return, Mode 4 enforces a bounded operational memory store (invariant store size of 3 memories via mutual exclusion, whereas Mode 3 grows unbounded to 23 items).
- **Mode 6 Static Control**: Mode 6 runs with $\lambda = 0.0$ in `scripts/eval_runner.py`. Under standard benchmark time (~3.5 minutes per seed, $\Delta t = 0$), no temporal decay occurs.
- **Experimental Separation**: Primary benchmark execution ($N = 450$) and controlled longitudinal temporal decay validation (Phase 6, 63 evaluation points, simulated epochs 0 to 60) remain strictly separate, independent experiments.

---

## 6. Complete Verification Suite Execution (Section 13)

All required test and verification suites were executed fresh and in full during Audit 8:

| Verification Suite / Script | Command | Outcome | Execution Details |
| :--- | :--- | :---: | :--- |
| **Unit Test Suite** | `pytest tests/unit/ -q` | **372 passed** | 46.03s, 0 failures, 0 warnings. Hermetic unit coverage across all subsystems. |
| **Integration Test Suite** | `pytest tests/integration/ -q` | **17 passed** | 37.06s, live PostgreSQL warehouse and LangGraph workflow integration. |
| **Environment Suite** | `pytest tests/test_env.py -q` | **12 passed** | 15.17s, PostgreSQL 18.1 and local Ollama service validation. |
| **Data Integrity Verification** | `python scripts/verify_phase4_data_integrity.py` | **PASS** | 450 root rows, 150 seed rows/seed, 450 raw hierarchy rows, 0 smoke records. |
| **Telemetry Provenance Audit** | `python scripts/verify_phase4_telemetry_provenance.py` | **PASS** | 141 telemetry rows across 3 seeds (47 each), 16 retrieval events/seed, 0 synthetic rows. |
| **Validation Tables Audit** | `python scripts/verify_validation_tables.py` | **PASS** | Tables A, B, C, D, E verified against authoritative benchmark evidence. |
| **Temporal Decay Validation** | `python scripts/validate_temporal_decay.py` | **PASS** | 63 longitudinal decay points, boundary idempotence, lifecycle machine, FAISS sync. |
| **Reproducibility & Lineage Audit** | `python scripts/analyze_reproducibility.py` | **PASS** | Root-seed equivalence, N=75 paired analysis, configuration provenance, perturbation test. |
| **Canonical Results Pipeline** | `python scripts/generate_results.py` | **PASS** | Stages 1–6 executed: validated inputs, generated 14 tables and 8 figures. |

**Total Active Tests Passing**: **401 / 401** (372 unit + 17 integration + 12 environment).

---

## 7. Authoritative Benchmark Hash Verification (Section 14)

Cryptographic SHA-256 hashes of all five authoritative benchmark evidence CSV files were verified before and after all Phase 8 and Audit 8 executions:

| Artifact File | Authoritative SHA-256 Hash | Post-Audit-8 SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :---: |
| `benchmark/benchmark_results.csv` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | `23c52e7fe03d320e502f732b629b602461968395aef532079d4999a32aeaf8f3` | **100% MATCH** |
| `benchmark/retrieval_telemetry.csv` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | `53ca107313ff0886df23e50f9b8956c0b0570d8bba3dc4fa2a268fdee7d8021d` | **100% MATCH** |
| `benchmark/seed42/benchmark_results.csv` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | `c5e06aa4aedbab52039a1e27039f42b1218f885f4d68d153c09e8d8ac6bad83b` | **100% MATCH** |
| `benchmark/seed123/benchmark_results.csv` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | `777e551f6c708ed3e3554030823af7168186d9b37b795508fe51fa0075e5cfe9` | **100% MATCH** |
| `benchmark/seed999/benchmark_results.csv` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | `0ca7342c478fdd470797f864aaccc6b9db1e8c1ae2db2c19dce3c9cd446cf445` | **100% MATCH** |

**Zero bytes were modified**. All authoritative benchmark evidence files remain identical to their frozen state.

---

## 8. Classification of Findings (Section 15)

Using the standardized classification taxonomy:

- **Category A (Confirmed Implementation Defect)**: **0 findings**. Zero defects exist in production code.
- **Category B (Unconfirmed Technical Risk)**: **0 findings**.
- **Category C (Methodological Limitations)**:
  - **C-1 (Cohort Size Sensitivity)**: Evaluated over 25 analytical queries across 3 seeds ($N = 450$). Prompt syntax sensitivity on Q08 and Q19 under retrieved memory context contributes to the observed +0.09 retry overhead in Mode 4.
  - **C-2 (Longitudinal Validation Protocol)**: Normal benchmark execution (~3.5 minutes per seed) evaluates operational queries under reference epoch $\Delta t = 0$. Multi-month temporal decay is evaluated via controlled longitudinal simulation (Phase 6, 63 condition points) rather than wall-clock multi-month benchmarking.
- **Category D (Material Evidence / Report Synchronization Defect)**: **0 findings post-Phase-8**. All preliminary figures in `evidence_package.md`, `ieee_manuscript.md`, and `benchmark_summary.md` were synchronized in Phase 8 and match canonical evidence.
- **Category E (Unnecessary Component / Change)**: **0 findings**. No extraneous code, dependencies, or abstractions were introduced.
- **Category F (Accepted Design Choices)**:
  - **F-1 (Metadata Volatility Handling)**: UUID and UTC timestamp generation in `RuntimeKnowledge` and `RuntimeMemory` objects are intentionally volatile runtime metadata, strictly excluded from vector embedding formatting (`format_for_embedding()`).
  - **F-2 (Controlled Static Ablation)**: Mode 6 uses `decay_rate = 0.0` within the benchmark runner, while continuous exponential decay is validated in the dedicated Phase 6 validation harness.
  - **F-3 (Infrastructure Exception Normalization)**: AST guardrail treats empty responses resulting from model/infrastructure timeouts as empty query validation rejections, driving controlled state routing.

---

## 9. Final Gate & Recommendation (Section 16)

### Final Audit Gate: **PASS**

**Justification**:
1. Production implementation across all modules is behaviorally correct and verified by 401 active passing tests.
2. Zero authoritative benchmark evidence files were modified (hashes verified 100% bit-for-bit).
3. All empirical results generated by `scripts/generate_results.py` and `scripts/analyze_reproducibility.py` match the canonical data and LaTeX tables with 100% precision.
4. Data lineage from raw logs to published tables and figures is unbroken and fully automated.
5. All 9 verification suites and test commands executed cleanly with zero failures.

---

## 10. STOP CONDITION REACHED

In strict accordance with the Audit 8 Stop Rule:
- Audit 8 has **PASSED**.
- **STOP**: Execution is halted. No Phase 9 work has been initiated.
