# ARMG — FULL PROJECT FORENSIC AUDIT 2 (CODE FORENSIC REPORT)
## Comprehensive Source Code, Runtime Behavior, Architecture & Research Implementation Audit

**Audit Date**: 2026-10-05T23:50:00+05:30  
**Audit Scope**: Complete Codebase (`graph/`, `agents/`, `memory/`, `environment/`, `validation/`, `benchmark/`, `scripts/`, `tests/`, `ui/`)  
**Auditor**: Antigravity Full Project Forensic Audit Agent  
**Audit Priority**: **P0 (Code/Runtime) > P1 (Architecture/Algorithms) > P2 (Benchmark) > P3 (Security) > P4 (Research) > P5 (Documentation)**  
**Executive Verdict**: **FULL PROJECT FORENSIC AUDIT 2 — PASS**  
**Authorized Next Step**: **SAFE TO BEGIN PHASE 3**

---

## 1. EXECUTIVE VERDICT

The ARMG codebase has undergone an exhaustive, source-level adversarial forensic audit examining every module, class, method, data structure, and state transition across the entire repository.

### Audit Verdict: **AUDIT PASS**

- **Zero Blocking Code Defects (P0/P1)**: No critical implementation bugs, unintended algorithmic behavior changes, or runtime data corruption defects remain in the active codebase.
- **Retrieval Metric Restoration**: The initial Phase 2 metric violation (`IndexFlatIP` and forced normalization) has been completely eradicated. The approved Phase 1 Euclidean metric (`IndexFlatL2`), $d^2$ extraction, and $S = \frac{1}{1 + d^2}$ similarity transformation are restored and operating with complete mathematical fidelity.
- **Strict Observational Telemetry**: The telemetry logger instruments the retrieval boundary directly without altering candidate ranking, threshold evaluation, lifecycle filtering, or graph state transitions.
- **Deterministic Pre-Execution Safety**: Zero bypass paths exist to PostgreSQL. The deterministic SQLGlot AST guardrail intercepts 100% of destructive statements prior to database driver invocation. Execution-proof tests confirm that the database cursor is never called for rejected statements.
- **Hermetic Test Suite**: The hermetic unit test suite (`tests/unit/`) passes with **267 passed, 0 failed, 0 skipped** (100% pass rate).
- **Benchmark Integrity & Isolation**: Modes 1 through 6 instantiate independent, isolated memory stores, workflows, and state containers with zero cross-mode state leakage.

---

## 2. CRITICAL CODE FINDINGS REGISTER

| Finding ID | Severity | File / Module | Component | Description / Actual Behavior | Resolution / Expected Behavior | Status |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **CF-01** | **P0** (Remediated) | `memory/vector_store.py` | `FAISSMemoryStore` | Initial Phase 2 converted index to `IndexFlatIP` and forced unit-$L_2$ vector normalization in `_validate_vector`. | Reverted to `faiss.IndexFlatL2` and removed forced normalization. Verified by 20 unit tests. | **CLOSED** |
| **CF-02** | **P0** (Remediated) | `graph/workflow.py` | `knowledge_node` | Stale `applied_memory_id` persisted across retries when retry encountered different error category. | Implemented per-attempt provenance evaluation; resets `applied_memory_id` unless matched to current diagnosis. | **CLOSED** |
| **CF-03** | **P1** (Remediated) | `agents/sql_generator.py` | `extract_sql_from_response` | Extractor returned raw model response text if markdown code block delimiters were absent. | Enforced SQL-keyword validation heuristic; rejects arbitrary conversational text as `None`. | **CLOSED** |
| **CF-04** | **P1** (Remediated) | `manuscript/tables/` | Table A / Fig. 3 | Pre-remediation baseline $S \approx 0.0035$ was non-empirical and mixed with new empirical telemetry without explicit labeling. | Formally classified as **B — Mathematically Derived Value (Non-Empirical)**. Labeled in all captions, headers, and footnotes. | **CLOSED** |
| **CF-05** | **P2** (Operational) | `tests/test_env.py` | Local Ollama Daemon | 4 environment tests fail and 4 integration tests skip when local Ollama service is offline on port 11434. | Expected operational pre-condition. Hermetic unit tests (267/267) mock LLM responses and pass 100%. | **ACCEPTED RISK** |
| **CF-06** | **P2** (Architectural) | `memory/vector_store.py` | `FAISSMemoryStore` | Absence of thread mutex around `self.index.add_with_ids` and `self.index.search`. | Safe for single-process sequential benchmark execution. Thread lock recommended for concurrent multi-tenant serving. | **RECOMMENDED P2** |

---

## 3. REAL EXECUTION GRAPH & RUNTIME FLOW

The active runtime execution graph was reconstructed by inspecting `graph/workflow.py`:

```mermaid
graph TD
    START --> Node1[1. introspect_and_prune_node]
    Node1 --> Node2[2. memory_retrieval_node]
    Node2 --> Node3[3. sql_generator_node]
    Node3 --> Node4[4. ast_guard_node]
    
    Node4 -- "validation_passed == True" --> Node5[5. postgres_executor_node]
    Node4 -- "validation_passed == False" --> Node6[6. observation_node]
    
    Node5 --> Node6
    
    Node6 -- "status == SUCCESS or BLOCKED" --> Node10[10. memory_governance_node]
    Node6 -- "status == RETRYING" --> Node7[7. diagnosis_node]
    
    Node7 --> Node8[8. knowledge_node]
    
    Node8 -- "retry_count < max_retries (RETRYING)" --> Node9[9. repair_prompt_node]
    Node8 -- "retry_count >= max_retries (FAILED)" --> Node10
    
    Node9 --> Node3
    Node10 --> END
```

### Graph Invariant Verifications
1. **Unreachable Nodes**: None. All 10 registered nodes have defined inbound and outbound edges.
2. **Accidental Bypasses**: Bypassing PostgreSQL execution on AST validation failure is **intentional and mandatory** to prevent destructive mutations from touching the physical database.
3. **Loop Bounding**: The cycle `Node3 -> Node4 -> Node6 -> Node7 -> Node8 -> Node9 -> Node3` is strictly bounded by `max_retries = 3`. When `retry_count == 3`, `knowledge_node` sets `status = STATUS_FAILED` and routes directly to `memory_governance_node`. Infinite repair oscillation is mathematically impossible.
4. **Safety Violation Route**: When an explicit safety violation is detected (`is_safety_violation = True`), `observation_node` sets `status = STATUS_BLOCKED`. The graph routes directly to `memory_governance_node`, bypassing repair attempts and database execution entirely.

---

## 4. STATE MANAGEMENT & MUTATION AUDIT

Audit of `ARMGState` fields across node boundaries in `graph/workflow.py`:

| State Field | Writers | Readers | Reset / Overwrite Behavior | Stale State Risk Analysis |
| :--- | :--- | :--- | :--- | :--- |
| `user_query` | `START` | Nodes 1, 3, 9 | Immutable throughout execution. | None. |
| `schema_context` | Node 1 | Nodes 6, 7, 8 | Populated once at query start; cached. | None. |
| `pruned_schema_markdown` | Node 1 | Nodes 3, 9 | Populated once per query. | None. |
| `generated_sql` | Node 3 | Nodes 4, 5, 6, 9 | Overwritten upon each initial and repair generation. | None. Previous query preserved in `previous_sql`. |
| `previous_sql` | Node 3 | Node 9 | Preserved from prior attempt when `repair_prompt` exists. | None. Clean handoff during repair. |
| `validation_passed` | Node 4 | Edge router, Node 6 | Evaluated freshly on every candidate SQL. | None. Recomputed per attempt. |
| `validation_error` | Node 4 | Nodes 3, 6, 9 | Set to error string if invalid; None if valid. | None. Cleared on valid attempt. |
| `is_safety_violation` | Node 4 | Node 6 | Evaluated freshly per attempt. | None. |
| `execution_result` | Node 5 | Nodes 3, 6, 10 | Created by Node 5; cleared by Node 3 on next retry. | None. Does not bleed into next retry. |
| `observation` | Node 6 | Nodes 7, 8, 9 | Reconstructed freshly after each execution/validation. | None. Immutable dataclass. |
| `diagnosis` | Node 7 | Nodes 8, 9, 10 | Reconstructed freshly after each failure; cleared by Node 3. | None. |
| `runtime_knowledge` | Node 8 | Node 10 | Created on failure attempt; evaluated upon terminal outcome. | None. |
| `retrieved_memories` | Node 2 | Nodes 8, 9, 10 | Retrieved once per query; immutable across retries. | None. Fixed context for the query session. |
| `applied_memory_id` | Node 8 | Node 10 | **Per-attempt evaluated**; matched to current diagnosis. | **P0 Fixed (Phase 1A)**: Does not leak across retries. |
| `repair_history` | Node 8, 10 | Telemetry | Appended per attempt; records attempt, diagnosis, applied ID. | Full audit trail preserved. |
| `repair_prompt` | Node 9 | Node 3 | Built by Node 9; consumed and set to None by Node 3. | None. Single-use handoff. |
| `retry_count` | Node 8 | Node 10, routers | Incremented strictly in Node 8 up to `max_retries`. | None. Deterministic integer counter. |
| `status` | Nodes 6, 8, 10 | Router edges | Transition: RUNNING -> RETRYING -> SUCCESS / FAILED / BLOCKED. | None. Adheres to `CONTROLLED_STATUSES`. |
| `telemetry` | All nodes | Node 10 | Cumulative dict recording timings, tokens, counts. | None. Pure observational accumulator. |

---

## 5. MEMORY LIFECYCLE AUDIT

A complete lifecycle trace was conducted from initial failure to physical deletion:

```text
Query Execution Failure (e.g., UndefinedColumn on Q04)
        ↓
1. Observation: Immutable RuntimeObservation record constructed.
        ↓
2. Diagnosis: Deterministic 7-tier classification (SEMANTIC, broken_id="bad_col", candidate_replacements=[...]).
        ↓
3. Ephemeral Knowledge: RuntimeKnowledge created with confidence=0.50.
        ↓
4. Successful Repair: Query succeeds on Attempt 2; state carries runtime_knowledge.
        ↓
5. Admission Gating:
   - context_similarity = 1.0 (exact failure context match)
   - recency = 1.0
   - Utility = 0.4(1.0) + 0.3(0.50) + 0.2(0.50) + 0.1(1.0) = 0.75 >= 0.25 (PASS)
   - RuntimeMemory instantiated with unique memory_id="mem-Q04", status=ACTIVE.
        ↓
6. FAISS Insertion:
   - Vector store assigns next integer ID (int64).
   - FAISS: index.add_with_ids(v, ids).
   - Decoupled metadata: _id_to_memory[int_id] = memory; _memory_id_to_int_id["mem-Q04"] = int_id.
        ↓
7. Subsequent Retrieval (e.g., Query Q08):
   - FAISS nearest-neighbor search returns candidate "mem-Q04".
   - Raw distance d² extracted; S = 1 / (1 + d²) = 0.9214 >= 0.50 (PASS).
   - Lifecycle check: mem.status == ACTIVE (PASS).
   - Retrieved memory injected into prompt operational context.
        ↓
8. Reinforcement / Mutual Exclusion (e.g., Query Q17):
   - Query Q17 applies "mem-Q13" and succeeds.
   - Governance Node: applied_id == "mem-Q13" triggers record_success("mem-Q13").
   - Confidence updated: C_new = min(1.0, C_old + 0.15 * (1.0 - C_old)).
   - Status escalates to STABLE when C >= 0.80.
   - Mutual Exclusion: New admission is suppressed; vector store count remains invariant.
        ↓
9. Simulated Temporal Decay:
   - At advanced epochs, C(t) = C_ref * exp(-lambda * delta_t).
   - When C(t) < 0.80: STABLE -> DECAYING.
   - When C(t) < 0.30: DECAYING -> ARCHIVED; archive_epoch = current_epoch.
   - After archive_retention_days (30 days): ARCHIVED -> DELETED.
        ↓
10. Physical Purge / Deletion:
   - store.delete(memory_id) calls index.remove_ids(ids).
   - Physical vector removed from FAISS; metadata popped.
   - Verified: store.count() decrements; search() never returns deleted memory.
```

---

## 6. FAISS & VECTOR STORE AUDIT

Source inspection of `memory/vector_store.py`:

1. **Index Architecture**:
   - `self._flat_index = faiss.IndexFlatL2(768)`
   - `self.index = faiss.IndexIDMap2(self._flat_index)`
   - Confirmed: Arbitrary 64-bit integer IDs are assigned and mapped directly to `RuntimeMemory`.
2. **Input Validation (`_validate_vector`)**:
   - Rejects non-768 dimensions with descriptive `ValueError`.
   - Rejects `NaN` and `Inf` with explicit exceptions.
   - **No Vector Mutation**: Vectors are never divided or altered inside `_validate_vector`.
3. **Retrieval Transformation & Ranking**:
   - `d2 = float(dist)` (squared Euclidean distance directly from FAISS)
   - `sim = 1.0 / (1.0 + d2)`
   - `sim = max(0.0, min(1.0, round(sim, 6)))`
   - Sorted ascending by distance: `results.sort(key=lambda r: (r[1], r[0].memory_id))`.
4. **Physical Deletion**:
   - `self.index.remove_ids(np.array([int_id], dtype=np.int64))`
   - Metadata entries popped from `_id_to_memory` and `_memory_id_to_int_id`.
   - Duplicate prevention: If a memory with the same `memory_id` is re-added, the previous vector is automatically deleted before re-insertion.

---

## 7. TELEMETRY INTEGRITY & CODE-LEVEL AUDIT

Source inspection of `memory/telemetry.py`:

1. **Observational Invariant**:
   - Telemetry logging methods (`log_retrieval_event`, `log_admission_event`, `update_store_size_after_query`) are strictly passive accumulators.
   - They do not mutate candidate lists, alter similarity scores, or return flow-control values.
2. **Null Representation**:
   - Empty store queries log `distance_l2_sq = None`, `similarity = None`, `memory_id = None`, `candidate_returned_by_faiss = False`.
   - Serialized to CSV as empty strings (`""`), never numeric `0.0`.
3. **Data Pre-Filtering**:
   - All candidates returned by `FAISS index.search()` are logged with `rank` and `distance_l2_sq` before threshold and lifecycle checks are performed.
4. **Schema Conformance**:
   - All 15 required canonical fields are present in exact order:
     `run_id, mode, query_id, memory_id, rank, distance_l2_sq, similarity, retrieval_similarity_threshold, passed_retrieval_threshold, top_k, candidate_returned_by_faiss, retrieval_count, accepted_memory_count, store_size_before_retrieval, store_size_after_query`.

---

## 8. SEARCH & RETRIEVAL LOGIC AUDIT

Audit of `memory_retrieval_node` in `graph/workflow.py`:

```python
raw_matches = self.vector_store.search_raw_candidates(query_vec, top_k=top_k)
for mem, rank, d2, sim in raw_matches:
    passed_thresh = bool(sim >= threshold)
    is_active = mem.status.value not in ("ARCHIVED", "DELETED")
    if passed_thresh and is_active:
        retrieved.append(mem)
```

1. **Order of Operations**:
   - FAISS searches the index and ranks nearest candidates by Euclidean proximity ($d^2$).
   - `search_raw_candidates` assigns ranks $1 \dots K$ based on raw geometric distance.
   - Threshold evaluation ($S \ge \tau$) and lifecycle filtering (`not in ("ARCHIVED", "DELETED")`) occur **after** candidate ranking.
   - This order is mathematically correct: candidate ranking reflects the intrinsic geometry of the embedding space, while acceptance into graph state reflects runtime policy.
2. **Threshold Float Behavior**:
   - Evaluated around critical boundary points:
     - $S = 0.499999 < 0.50$ (**REJECTED**)
     - $S = 0.500000 \ge 0.50$ (**ACCEPTED**)
     - $S = 0.500001 \ge 0.50$ (**ACCEPTED**)
   - Floating-point rounding to 6 decimal places ensures zero spurious precision artifacts.

---

## 9. GOVERNANCE MATHEMATICS AUDIT

Audit of `memory/governance.py`:

1. **Multi-Factor Operational Utility**:
   $$\text{Utility} = w_s \cdot S + w_c \cdot C + w_{sr} \cdot SR + w_r \cdot R$$
   With weights $w_s = 0.4, w_c = 0.3, w_{sr} = 0.2, w_r = 0.1$ ($\sum w_i = 1.0$).
   - All inputs bounded in $[0.0, 1.0]$.
   - Utility bounded in $[0.0, 1.0]$.
   - Admission threshold $\text{Utility}_0 \ge 0.25$.
2. **Asymptotic Confidence Escalation**:
   $$C_{\text{new}} = \min(1.0, C_{\text{old}} + \alpha \cdot (1.0 - C_{\text{old}})), \quad \alpha = 0.15$$
   - Strictly monotonic increasing; bounded by $1.0$; zero overshoot.
3. **Multiplicative Failure Penalty**:
   $$C_{\text{new}} = \max(0.0, C_{\text{old}} \cdot (1.0 - \beta)), \quad \beta = 0.20$$
   - Strictly monotonic decreasing; bounded below by $0.0$.
4. **Continuous Exponential Temporal Decay**:
   $$C(t) = C_{\text{ref}} \cdot e^{-\lambda \Delta t}, \quad \lambda = 0.05$$
   - Evaluated relative to $C_{\text{ref}}$ and $\Delta t = \max(0, \text{epoch} - \text{epoch}_{\text{ref}})$.
   - Eliminates compound double-decay and guarantees numerical determinism.

---

## 10. TEMPORAL DECAY PRODUCTION AUDIT

1. **Per-Query Workflow Invariance**:
   - Confirmed: Temporal decay is **not** called within `ARMGRepairWorkflow.memory_retrieval_node` or `memory_governance_node`.
   - Per-query operations evaluate operational utility using $\Delta t = 0$, reflecting sequential execution within the benchmark session.
2. **Lifecycle Maintenance**:
   - Implemented via `apply_decay_sweep(memories, current_epoch)`.
   - Used in the interactive Streamlit dashboard (`ui/dashboard.py` line 403) and tested in unit suite (`test_memory_governance.py`).
   - The primary benchmark does not artificially accelerate calendar time, accurately reporting that continuous temporal decay remained unexercised over the ~3.5-minute benchmark run.

---

## 11. DIAGNOSIS SYSTEM AUDIT

Audit of `agents/error_diagnosis.py`:

1. **Deterministic 7-Tier Precedence**:
   - **Tier 1 (VALIDATION)**: Catches pre-execution AST safety failures and blocked statements.
   - **Tier 2 (SYNTAX)**: Catches PostgreSQL syntax parser errors.
   - **Tier 3 (SEMANTIC)**: Catches missing columns (`UndefinedColumn`) and missing tables (`UndefinedTable`). Resolves candidates from schema catalog.
   - **Tier 4 (PLANNING)**: Catches missing `GROUP BY` column requirements (`GroupingError`).
   - **Tier 5 (PERMISSION)**: Catches read-only or insufficient privilege errors.
   - **Tier 6 (RESOURCE)**: Catches statement timeouts and connection cancellations.
   - **Tier 7 (EXECUTION)**: Catches division by zero and unclassified runtime database errors.
2. **Deterministic Resolution**:
   - Candidate ranking uses lexical overlap, type compatibility, and alphabetical tie-breaking.
   - Zero LLM tokens, zero heuristics, zero non-determinism.

---

## 12. REPAIR SYSTEM & PROMPT BOUNDING AUDIT

Audit of `agents/repair_agent.py`:

1. **Negative Constraint Isolation**:
   - Identifiers extracted by diagnosis (e.g., broken column `d.time_key`) are bound into:
     ```text
     1. FORBIDDEN IDENTIFIERS:
        Do not use the identifiers ['d.time_key'] anywhere in the SQL query.
     ```
   - Constraints are strictly scoped to the active query's repair prompt and do not contaminate global state or future queries.
2. **Candidate Replacement Injection**:
   - Resolved valid columns are presented as strictly bounded alternatives.
3. **Safety Verification on Repaired SQL**:
   - Repaired queries generated by Node 9 route directly to Node 3 (`sql_generator_node`) and must pass through Node 4 (`ast_guard_node`) prior to any database execution.
   - Repaired SQL has zero privilege bypass.

---

## 13. SQL SAFETY RUNTIME BYPASS ANALYSIS

An exhaustive source search was conducted for every database execution call across the entire repository:

```text
c:\Users\siddu\Pictures\armg main\graph\workflow.py:301:
    exec_res = self.environment.execute(sql)
```

### Bypass Analysis Findings
1. In `graph/workflow.py`, `self.environment.execute(sql)` is called **exclusively** inside `postgres_executor_node` (Node 5).
2. The LangGraph routing rule `route_after_ast_guard` governs entry to Node 5:
   ```python
   if state.get("validation_passed", False):
       return "postgres_executor_node"
   return "observation_node"
   ```
3. If `validation_passed` is `False`, the executor node is **completely unreachable**.
4. In `ExecutionValidator.validate(sql)`:
   - Statements are parsed via `sqlglot.parse(sql, read="postgres")`.
   - Statement count must equal exactly 1 (`len(statements) == 1`). Multi-statement stacked queries are immediately rejected.
   - Root expression must be `sqlglot.exp.Select`.
   - All AST expression descendants are checked against prohibited DML/DDL types (`Delete`, `Update`, `Drop`, `Insert`, `Create`, `AlterTable`, `Truncate`, `Grant`, `Revoke`, `Command`).
   - Obfuscated queries (mixed case, inline comments, CTE-wrapped mutations) are rejected at the AST level.
5. In `test_phase1d_safety_guard.py`:
   - `test_execution_proof_blocked_statements_never_invoke_executor` proves that for every blocked statement category, a mock database executor is **never invoked**.
   - **Conclusion: Zero SQL safety bypass paths exist in ARMG.**

---

## 14. DATABASE EXECUTION AUDIT

Audit of `environment/postgres.py`:

1. **Connection Lifecycle**:
   - Connection established with `connect_timeout=10` and `autocommit=False`.
   - Re-used across queries within the session; cleaned up cleanly on `close()` and context manager exit.
2. **Transaction Integrity**:
   - Upon execution success: `conn.commit()`.
   - Upon execution failure: `conn.rollback()` is executed immediately, ensuring failed queries never leave transactions in an aborted/dirty state.
3. **Timing Precision**:
   - High-precision wall-clock timing captured via `time.perf_counter()`.
4. **Exception Containment**:
   - Database driver errors are caught, formatted, and packaged into `ExecutionResult(status="FAILURE", error=error_str, ...)`. No unhandled psycopg2 driver crashes can terminate the state graph.

---

## 15. ERROR HANDLING AUDIT

| Failure Mode | Component | Handling Behavior | State Graph Integrity |
| :--- | :--- | :--- | :--- |
| **Ollama Service Offline** | `sql_generator.py` | Catches `requests.exceptions.ConnectionError`; returns fallback/error result. | Handled gracefully; produces execution error. |
| **Malformed LLM Output** | `sql_generator.py` | `extract_sql_from_response` checks SQL keyword presence; returns `None`. | Routes to validation failure -> repair. |
| **Embedding Service Offline** | `graph/workflow.py` | `default_embed_fn` catches exception; returns `None`. | Logs empty candidate telemetry; skips retrieval safely. |
| **SQLGlot Parse Error** | `execution_validator.py` | Catches parse exception; flags `validation_passed=False`. | Routes to observation -> diagnosis -> repair. |
| **PostgreSQL Timeout** | `postgres.py` | Driver raises timeout; caught, rolled back; classified as `RESOURCE`. | Diagnosed and bounded by retry budget. |
| **Empty Vector Index** | `vector_store.py` | Early exit: returns empty candidates list `[]`. | Logs null telemetry; routes cleanly to initial generation. |

---

## 16. CONCURRENCY & SHARED STATE AUDIT

1. **Sequential Benchmark Execution**:
   - In benchmark and evaluation modes (`eval_runner.py`), queries are processed sequentially per mode.
   - All state is encapsulated within `ARMGState` dicts passed through LangGraph.
2. **Dependency Injection**:
   - `ARMGRepairWorkflow` receives all stores and engines via constructor arguments. There are zero mutable global singletons in `graph/workflow.py`.
3. **Concurrency Finding (P2)**:
   - `FAISSMemoryStore` maintains internal state in `self.index` (FAISS C++ object) and Python dictionaries (`_id_to_memory`, `_memory_id_to_int_id`).
   - If accessed across concurrent threads in a multi-tenant web application, a mutex lock (`threading.Lock`) should wrap `add()` and `delete()` operations to prevent race conditions.
   - This does not impact single-process benchmark execution.

---

## 17. BENCHMARK INTEGRITY & MODE ISOLATION AUDIT

Audit of `scripts/eval_runner.py` and `benchmark/modes.py`:

1. **Mode Isolation**:
   - Running Modes 1 through 6 sequentially within one process creates completely fresh, isolated instances for each mode:
     - Mode 1: Fresh generators, no vector store.
     - Mode 2: Fresh repair generator, max 3 retries, stateless prompt without memory.
     - Mode 3: Fresh `NaiveVectorStore(dimension=768)`.
     - Mode 4: Fresh `FAISSMemoryStore()`, fresh `ARMGRepairWorkflow`.
     - Mode 5: Fresh `FAISSMemoryStore()`, fresh `AblationNoNegConstraintsWorkflow` (omits strict constraints block).
     - Mode 6: Fresh `FAISSMemoryStore()`, fresh `MemoryGovernanceEngine(decay_rate=0.0)`.
   - **Zero cross-mode memory or telemetry contamination**.
2. **Data Leakage Check**:
   - `gold_sql` is used **strictly after** query execution completes to compute `check_relational_equivalence()`.
   - Neither `gold_sql` nor expected results are ever passed into LLM prompts, memory stores, or repair contexts.
   - **Zero data leakage**.

---

## 18. TEST SUITE RECONCILIATION

```text
======================================================================
ARMG TEST SUITE RECONCILIATION (AUDIT 2)
======================================================================
1. Hermetic Unit Tests (tests/unit/):
   - Passed:   267
   - Failed:     0
   - Skipped:    0
   - Status:   100% PASS (Hermetic, offline, zero network dependencies)

2. Live Integration Tests (tests/integration/):
   - Passed:     1 (Live PostgreSQL catalog inspection)
   - Failed:     0
   - Skipped:    4 (Skipped due to local Ollama daemon offline)
   - Status:   PASS (Conditional on local Ollama service)

3. Environment Verification Tests (tests/test_env.py):
   - Passed:     8 (Python 3.13, PyTorch, FAISS, SQLGlot, LangGraph, etc.)
   - Failed:     4 (Ollama HTTP connection refused on port 11434)
   - Status:   ENVIRONMENT DIAGNOSTIC (Expected when Ollama daemon offline)

TOTAL COLLECTED: 284 tests
======================================================================
```

---

## 19. REMEDIATION PRIORITIES

### P0 (Correctness Blockers): **ZERO (None)**
All P0 defects from Audit 1 and Phase 2 have been completely resolved and verified.

### P1 (Major Risks): **ZERO (None)**
All Phase 1 and Phase 2 governance, provenance, extraction, safety, and telemetry invariants are fully green.

### P2 (Important Improvements for Future Phases):
1. **Thread Mutex on Vector Store**: Wrap `FAISSMemoryStore` mutations with a `threading.Lock` if deploying to multi-threaded web servers.
2. **Ollama Daemon Pre-Flight Check**: In `eval_runner.py`, add an explicit ping to `localhost:11434` with an actionable prompt if the service is offline prior to running Phase 3 benchmarks.

### P3 (Optional Polish):
1. Clean up scratch directory test artifacts prior to final submission.

---

## 20. FINAL GATE VERDICT & AUTHORIZATION

Every audit priority (P0 through P5) has been thoroughly examined against the active source code, execution graphs, test suites, and empirical datasets.

```text
FULL PROJECT FORENSIC AUDIT 2 — PASS
SAFE TO BEGIN PHASE 3
```

---

## 21. PHASE 3 AUTHORIZATION & PROMPT SPECIFICATION

The project is cleared to initiate **Phase 3**:

```text
# ARMG — PHASE 3
## BENCHMARK RE-EXECUTION & STATISTICAL HARDENING

### Phase Authorization
- Phase 0: PASS
- Phase 1 (1A, 1B, 1C, 1D): PASS
- Audit 1R: FINAL PASS
- Phase 2: PASS (Technical & Documentation Remediation Complete)
- Full Project Forensic Audit 2: PASS

Phase 3 is authorized to begin.

### Primary Objectives
1. Verify live local Ollama environment connectivity and model availability (qwen2.5:7b-instruct, nomic-embed-text).
2. Execute the full end-to-end multi-seed benchmark across all 6 experimental modes with live PostgreSQL 18.1 execution.
3. Capture live FAISS retrieval telemetry directly to benchmark/retrieval_telemetry.csv during Mode 4 execution.
4. Regenerate benchmark_results.csv and compute multi-seed descriptive metrics (mean ± std).
5. Compile and render final publication artifacts (Figures 1-6 and Tables I-VIII).
```
