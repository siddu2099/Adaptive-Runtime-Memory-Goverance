# ARMG Manuscript Evidence Package
## Authoritative Experimental Data & Forensic Reference for IEEE Drafting
**Status**: Authoritative & Frozen  
**Date**: September 2026  
**Repository**: `armg main`  
**Execution Context**: Local Ollama (`qwen2.5:7b-instruct`), PostgreSQL 16 Warehouse, `nomic-embed-text` (768-dim, Unit-L2 normalized)

---

## A. Final System Architecture Summary

The Adaptive Runtime Memory Governance (ARMG) framework operates as a closed-loop runtime architecture structured as a directed execution graph (implemented via LangGraph in `graph/workflow.py`).

```
[User Question]
       │
       ▼
[Node 1: Schema Introspection & Pruning] (SchemaIntrospector, SchemaPruner)
       │
       ▼
[Node 2: Vector Memory Retrieval] (FAISS IndexFlatL2, nomic-embed-text unit-L2 normalized, τ = 0.50)
       │
       ▼
[Node 3: SQL Generation] (SQLGenerator, qwen2.5:7b-instruct, temperature = 0.0)
       │
       ▼
[Node 4: AST Validation & Safety Guard] (ExecutionValidator: sqlglot read-only DQL filter)
       ├─── [Violation] ───► STATUS_BLOCKED (Terminates workflow, 0 execution against DB)
       │
       ▼ [Valid SELECT]
[Node 5: PostgreSQL Execution] (PostgreSQLEnvironment: localhost:5432/armg_db)
       ├─── [Success] ───► STATUS_SUCCESS (Workflow terminates)
       │
       ▼ [Runtime Failure]
[Node 6: Deterministic Diagnosis] (DiagnosticEngine: AST syntax, schema binding, catalog mapping)
       │
       ▼
[Node 7: Ephemeral Knowledge Extraction] (RuntimeKnowledge: error_type, root_cause, repair_rule)
       │
       ▼
[Node 8: Runtime Repair Prompting] (RepairSQLGenerator: previous SQL, error, negative constraints, memory)
       │
       ▼ (Loops back to Node 4; bounded by max_retries = 3)
       │
[Node 9: Memory Governance Engine] (MemoryGovernanceEngine)
       ├─── If repaired using applied memory: REINFORCE existing memory (Mutual Exclusion)
       ├─── If repaired without applied memory: ADMIT new RuntimeMemory to FAISS
       └─── If unrecoverable failure: TERMINAL_FAILURE_NOT_ADMITTED
```

### Key Architectural Boundaries & Source Files
1. **Embedding Normalization Boundary** (`graph/workflow.py:default_embed_fn`):
   - Raw embeddings from `nomic-embed-text` are unit-L2 normalized ($\|\mathbf{v}\|_2 = 1.0$) before insertion or querying in FAISS.
   - FAISS metric: `IndexFlatL2(768)` wrapped in `IndexIDMap2`.
   - Distance conversion: $S = \frac{1}{1 + d^2}$.
2. **Mutual Exclusion Boundary** (`graph/workflow.py:memory_governance_node`):
   - When a repair succeeds using an existing `applied_memory_id`, that memory is reinforced via utility update ($U_{t+1} = U_t + \alpha (1 - U_t)$) and new memory admission is suppressed.
   - When a repair succeeds without an applied memory, new `RuntimeKnowledge` is admitted as a fresh `RuntimeMemory`.
3. **Safety Gate Boundary** (`validation/execution_validator.py`, `graph/workflow.py:validator_node`):
   - SQLGlot-based AST parser strictly validates query structure.
   - Destructive DML/DDL (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`) triggers `STATUS_BLOCKED` and halts execution before any database connection.

---

## B. Experimental Protocol

- **Inference Mode**: Fully local offline execution.
- **LLM**: `qwen2.5:7b-instruct` served via local Ollama instance (`http://localhost:11434`).
- **Sampling Settings**: Hardcoded `temperature = 0.0` (greedy decoding / argmax generation) across all initial and repair generations (`agents/sql_generator.py:122`, `agents/repair_agent.py:155`).
- **Seed Handling**: The benchmark seed argument (`--seed`) tracks experimental runs and initializes deterministic runtime components, but is not passed to Ollama API options.
- **Repair Policy**: Maximum 3 repair iterations (initial generation attempt 1 + up to 3 repair generations, max generation attempts = 4).
- **Temporal Clock**: Natural static real-time execution clock. No synthetic timestamps or artificial epoch offsets were injected ($\Delta t \approx 0.002$ days per 25-query run).
- **Evaluation Order**: Fixed chronological query order $Q01 \to Q25$ for every mode and seed.
- **Isolation Guarantee**: Every (Seed $\times$ Mode) combination initialized a brand-new, empty memory store. Zero cross-mode or cross-seed leakage.

---

## C. Benchmark Composition

**Source**: `benchmark/queries.json` (SHA-256: `8f3a11f238bf93187e29fa18204af44b926eb190a7bbae1598caa0ea97f38189`)

### 1. Query Set Breakdown (25 Queries)
- **Category A — Simple Aggregations & Groupings (5 Queries)**:
  - `Q01`: Total gross revenue across all transactions.
  - `Q02`: Total units sold by product category.
  - `Q03`: Average discount applied per transaction.
  - `Q04`: Transaction count per market type (joins `dim_geography`).
  - `Q05`: Total net profit by calendar quarter in 2025 (joins `dim_time`, traps ordering).
- **Category B — Multi-Table Analytical Joins (8 Queries)**:
  - `Q06`: Total revenue by product category and geographic region (`fact` + 2 dims).
  - `Q07`: Average profit margin by sales territory in 2024.
  - `Q08`: Units sold by region and calendar month in 2025 (`dim_geography` + `dim_time`).
  - `Q09`: Top customer segments by total net profit.
  - `Q10`: Average discount per product sub-category in Enterprise market.
  - `Q11`: Revenue by shipping mode and warehouse location.
  - `Q12`: Quarterly profit by sales channel in EMEA.
  - `Q13`: Total gross revenue by zone in North America (`dim_geography`).
- **Category C — Advanced Analytical & Window Queries (6 Queries)**:
  - `Q14`: Rank product categories by total gross revenue (`RANK() OVER (...)`).
  - `Q15`: Running total of gross revenue across calendar months of 2025 (`SUM(...) OVER (...)`).
  - `Q16`: Top 3 products by total net profit (`LIMIT / DENSE_RANK`).
  - `Q17`: Monthly revenue with previous month revenue via `LAG()`.
  - `Q18`: Rank products within each category by units sold (`PARTITION BY category`).
  - `Q19`: Percentage contribution of each region to total revenue (`SUM(...) OVER ()`).
- **Category D — Semantic & Schema Trap Queries (6 Queries)**:
  - `Q20`: Total revenue by region (ambiguous column reference resolution).
  - `Q21`: Total discount by product category (currency vs percentage trap).
  - `Q22`: Total profit for each product category (column naming ambiguity).
  - `Q23`: Average cost of products in each sub-category (cost vs price trap).
  - `Q24`: Total gross revenue by market (market vs market_type join trap).
  - `Q25`: Total profit and total revenue for each market type (multi-metric grouping).

### 2. Experimental Modes (6 Modes)
1. **Mode 1 — Monolithic Zero-Shot Baseline**: Single-pass prompt with full schema markdown; zero self-correction; zero memory.
2. **Mode 2 — Stateless Self-Correction Baseline**: Iterative repair loop (up to 3 retries) feeding raw PostgreSQL execution errors back to the model; memoryless across queries.
3. **Mode 3 — Naive Vector RAG Baseline**: Unmanaged vector store storing raw `(question, sql)` pairs upon execution success; retrieves top-3 few-shot examples; zero repair loop; zero lifecycle governance.
4. **Mode 4 — Full ARMG**: Complete architecture with governed vector retrieval, deterministic error diagnosis, AST negative constraints, bounded repair loop, and mutual-exclusion lifecycle governance.
5. **Mode 5 — ARMG − Negative Constraints (Ablation)**: Identical to Mode 4, but diagnostic negative constraints (forbidden identifiers, invalid join conditions) are omitted from repair prompts.
6. **Mode 6 — ARMG with $\lambda = 0.0$ (Temporal Decay Ablation)**: Identical to Mode 4, but decay rate set to 0.0 (static no-decay control).

### 3. Evaluation Metrics
- **PostgreSQL Execution Success (`is_success`)**: Boolean flag indicating whether generated SQL executed against PostgreSQL 16 without error and returned a result set.
- **Relational Execution Accuracy (`execution_accuracy`)**: Evaluated via `benchmark/equivalence.py`. Compares result tuples against PostgreSQL gold SQL execution, accounting for set/bag semantics, column ordering, and floating point rounding.
- **Mean Retries**: Number of repair generations required ($0, 1, 2, \text{ or } 3$).
- **Mean Latency (ms)**: Total end-to-end wall-clock time from question receipt to final state.
- **Mean Tokens**: Total prompt + completion tokens consumed across all generation attempts for a query.
- **Retrieval Count**: Number of memories returned with similarity $S \ge 0.50$.
- **Admissions**: New `RuntimeMemory` entries written to FAISS.
- **Reinforcements**: Existing memories whose utility was updated following applied repair.
- **Final Store Count**: Number of active memory vectors in the mode's FAISS index at the end of query Q25.

---

## D. Final Three Repeated Execution Summaries

**Sources**:
- `benchmark/seed42/benchmark_results.csv`
- `benchmark/seed123/benchmark_results.csv`
- `benchmark/seed999/benchmark_results.csv`

### 1. Overall Aggregated Results Across Runs ($n = 3$ Repeated Executions)

| Mode | Relational ExecAcc (%) | PostgreSQL Exec Success (%) | Mean Retries (± std across queries) | Mean Latency (ms) (± std across queries) | Mean Tokens (± std across queries) | Retrievals (Queries) | Admissions | Reinforcements | Final Store Size |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mode 1** | 57.33% ± 2.31% | 76.00% ± 0.00% | 0.00 ± 0.00 | 5,087.73 ± 210.33 | 360.48 ± 0.48 | 0 (0) | 0 | 0 | 0 |
| **Mode 2** | 68.00% ± 0.00% | 92.00% ± 0.00% | 0.43 ± 0.02 | 7,149.68 ± 231.65 | 572.72 ± 12.68 | 0 (0) | 0 | 0 | 0 |
| **Mode 3** | 68.00% ± 0.00% | 92.00% ± 0.00% | 0.00 ± 0.00 | 6,844.01 ± 56.90 | 558.28 ± 0.00 | 69 (24) | 23 | 0 | 23 |
| **Mode 4** | **68.00% ± 0.00%** | **96.00% ± 0.00%** | **0.28 ± 0.00** | **8,564.89 ± 103.16** | **542.37 ± 0.02** | **16 (12)** | **3** | **1** | **3** |
| **Mode 5** | 68.00% ± 0.00% | 96.00% ± 0.00% | 0.36 ± 0.00 | 8,941.28 ± 108.68 | 553.93 ± 0.02 | 16 (12) | 3 | 2 | 3 |
| **Mode 6** | 68.00% ± 0.00% | 94.67% ± 2.31% | 0.37 ± 0.02 | 9,036.97 ± 178.55 | 599.67 ± 13.94 | 16 (12) | 3 | 2 | 3 |

*Note: All `±` values in the table above denote sample standard deviation across the three repeated benchmark runs ($n = 3$), capturing run-to-run execution variability.*

### 2. Individual Run Breakdowns
- **Seed 42**:
  - Mode 1: ExecAcc: 56.0%, PG: 76.0%, Retries: 0.00, Latency: 5,281.72 ms, Tokens: 360.76
  - Mode 2: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.44, Latency: 7,360.37 ms, Tokens: 580.04
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,903.46 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,618.89 ms, Tokens: 542.36
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.36, Latency: 9,019.33 ms, Tokens: 553.92
  - Mode 6: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.40, Latency: 9,209.49 ms, Tokens: 615.76
- **Seed 123**:
  - Mode 1: ExecAcc: 56.0%, PG: 76.0%, Retries: 0.00, Latency: 5,117.29 ms, Tokens: 360.76
  - Mode 2: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.44, Latency: 7,187.05 ms, Tokens: 580.04
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,838.49 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,629.83 ms, Tokens: 542.40
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.36, Latency: 8,987.36 ms, Tokens: 553.92
  - Mode 6: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.36, Latency: 9,048.46 ms, Tokens: 591.60
- **Seed 999**:
  - Mode 1: ExecAcc: 60.0%, PG: 76.0%, Retries: 0.00, Latency: 4,864.18 ms, Tokens: 359.92
  - Mode 2: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.40, Latency: 6,901.61 ms, Tokens: 558.08
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,790.07 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,445.94 ms, Tokens: 542.36
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.36, Latency: 8,817.16 ms, Tokens: 553.96
  - Mode 6: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.36, Latency: 8,852.95 ms, Tokens: 591.64

---

## E. Mode 2 vs Mode 4 Comparison

**Source**: `scratch/generate_all_tables.py`, `benchmark/seed*/benchmark_results.csv`

### 1. Comparative Performance Metrics

| Dimension | Mode 2 (Stateless Self-Correction) | Mode 4 (Full ARMG) | Absolute Delta ($\Delta$) | Relative Delta (%) | Consistency Across Runs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Relational ExecAcc** | 68.00% ± 0.00% | 68.00% ± 0.00% | 0.00 pp | 0.00% | 17/25 in all 3 runs |
| **PostgreSQL Exec Success** | 92.00% ± 0.00% | 96.00% ± 0.00% | +4.00 pp | +4.35% | 24/25 vs 23/25 in all 3 runs |
| **Mean Retries** | 0.4267 ± 0.02 | 0.2800 ± 0.00 | −0.1467 | **−34.38%** | Lower in all 3 runs |
| **Mean Tokens** | 572.72 ± 12.68 | 542.37 ± 0.02 | −30.35 | **−5.30%** | Lower in all 3 runs |
| **Mean Latency (ms)** | 7,149.68 ± 231.65 | 8,564.89 ± 103.16 | +1,415.21 ms | **+19.79%** | Higher in all 3 runs |

### 2. Query-Level Divergence
Across the 25 queries, Mode 4 and Mode 2 differed on exactly **2 queries**:
- **`Q08` (Category B — Join Aggregation)**:
  - *Mode 2*: Failed on Attempt 1; required repair retry (mean 0.67 retries across runs).
  - *Mode 4*: Retrieved memory admitted during `Q04`; succeeded on Attempt 1 without retries (`retries = 0`) across all runs.
  - *Effect*: Retry reduction (−0.67 retries).
- **`Q19` (Category C — Percentage Contribution)**:
  - *Mode 2*: Encountered `GROUP BY` syntax error; exhausted all 3 repair retries; terminated with `is_success = False` across all runs (`retries = 3`).
  - *Mode 4*: Retrieved memory admitted during `Q13`; generated valid PostgreSQL query on Attempt 1 without retries (`retries = 0`, `is_success = True`).
  - *Effect*: Execution recovery (+1 PostgreSQL success) and retry reduction (−3.0 retries).
- **Remaining 23 Queries**: Exactly identical query outcomes between Mode 2 and Mode 4. Zero queries worsened in Mode 4. Zero queries exhibited relational semantic accuracy difference.

---

## F. Mode 4 vs Mode 5 Comparison (Ablation of Negative Constraints)

**Source**: `benchmark/seed*/benchmark_results.csv`

### 1. Comparative Metrics
- **Mean Retries**: Mode 4 required **0.28 ± 0.00 retries** vs Mode 5's **0.36 ± 0.00 retries** across all three runs.
- **Relational ExecAcc**: 68.00% vs 68.00% (identical).
- **PostgreSQL Exec Success**: 96.00% vs 96.00% (identical).
- **Mean Latency**: 8,564.89 ms vs 8,941.28 ms (+376.39 ms slower in Mode 5 due to extra repair cycles).

### 2. Query-Level Attribution
- The entire retry difference between Mode 4 and Mode 5 is isolated to **Query `Q19`**:
  - *Mode 4 (with negative constraints)*: Pruned known invalid AST structures from the repair context; executed on Attempt 1 (`retries = 0`).
  - *Mode 5 (without negative constraints)*: Repeated invalid grouping syntax on Attempt 1, requiring **2 repair retries** before succeeding on Attempt 3 (`retries = 2`).
- *Defensible Scope*: Negative constraints were associated with fewer repair iterations specifically for query `Q19`. Broader generalization to all analytical queries is not demonstrated.

---

## G. Mode 4 vs Mode 6 Interpretation (Ablation of Temporal Decay)

**Source**: `memory/governance.py`, `benchmark/seed*/benchmark_results.csv`

- **Benchmark Clock**: All 25 queries execute in continuous sequence within ~3.5 minutes ($\Delta t \approx 0.002$ days).
- **Mathematical Decay Factor**: For decay parameter $\lambda = 0.05/\text{day}$:
  $$\exp(-\lambda \Delta t) = \exp(-0.05 \times 0.002) \approx 0.9999$$
- **Operational Reality**: Under real-time static execution without simulated multi-day epoch advances, memory utility does not decay below the retention threshold ($\tau_{\text{archive}} = 0.15$). Mode 4 and Mode 6 exhibited identical final store sizes (3 memories) and identical retrieval counts (16 retrievals).
- *Defensible Conclusion*: **Temporal decay effectiveness was NOT demonstrated by this benchmark**. Mode 6 operates strictly as a static no-decay control.

---

## H. Memory Lifecycle Evidence

**Source**: `graph/workflow.py`, `memory/vector_store.py`, `scratch/verify_stage2_data.py`

### 1. Store Size Progression
In every post-remediation run, the Mode 4 FAISS store progressed deterministically:
- `Q01–Q03`: Store size = 0.
- `Q04`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (`mem-Q04`). Store size = 1.
- `Q05–Q12`: Store size = 1 (`Q11` terminal failure rejected by admission gate).
- `Q13`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (`mem-Q13`). Store size = 2.
- `Q14`: Store size = 2.
- `Q15`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (`mem-Q15`). Store size = 3.
- `Q16`: Store size = 3.
- `Q17`: Failed attempt 1; repaired attempt 2 using applied `mem-Q13` $\implies$ **Reinforced** `mem-Q13`. Mutual exclusion suppressed new admission. Store size = **3 (invariant)**.
- `Q18–Q25`: Store size = 3.

### 2. Operational Lifecycle Metrics (Precise Denominators)
- **Total Retrieval Events**: 16 events.
- **Retrieval-Bearing Queries**: 12 queries out of 25 (48.0% benchmark coverage).
- **Prompt-Context Application Rate**: $12 / 12 = 100.0\%$.
- **Explicit Repair Application Rate**: $1 / 1 = 100.0\%$ (occurred on `Q17`).
- **Successful Repair Following Memory Application**: $1 / 1 = 100.0\%$ (`Q17` succeeded on Attempt 2).
- **Reinforcement Following Applied Repair**: $1 / 1 = 100.0\%$ (`Q17` reinforced existing memory).
- **Duplicate Memory Accumulation**: **0 duplicate entries** across all runs.

---

## I. Safety Evidence

**Source**: `validation/execution_validator.py`, `benchmark/seed*/benchmark_results.csv`

- **Evaluations Audited**: 450 post-remediation evaluations (150 per seed $\times$ 3 seeds) + 150 historical baseline runs = 600 total query evaluations.
- **Destructive Statements Reaching PostgreSQL**: **ZERO (0)**.
- **AST Pre-Execution Validation**: 100% of generated queries were validated via SQLGlot before database execution.
- **Warehouse Integrity**: Checksums and record counts on `armg_db` confirmed zero mutation, deletion, or schema alteration.

---

## J. Semantic Divergence Analysis

**Source**: `benchmark/equivalence.py`, `scratch/check_semantic_failures.py`

### 1. The PostgreSQL Execution vs Relational Semantic Equivalence Gap
- PostgreSQL execution success rate: **96.00%** (24/25 queries).
- Relational semantic accuracy: **68.00%** (17/25 queries).
- Divergence: Exactly **7 queries (28.0%)** executed cleanly on PostgreSQL (`is_success = True`) but returned incorrect relational data (`execution_accuracy = 0`).

### 2. Taxonomy of the 7 Semantic Failures
1. **`Q05` (Category A — Ordering Omission)**:
   - *Failure Type*: Missing `ORDER BY`. Omitted sort clause specified in question, failing tuple sequence equivalence.
2. **`Q14` (Category C — Missing Window Ranking Function)**:
   - *Failure Type*: Missing projection column. Replaced `RANK() OVER (ORDER BY revenue DESC)` with a standard `ORDER BY` clause, omitting the required ranking attribute.
3. **`Q15` (Category C — Missing Cumulative Window Frame)**:
   - *Failure Type*: Missing cumulative framing. Computed simple monthly aggregations without the cumulative `SUM(SUM(...)) OVER (...)` running total.
4. **`Q17` (Category C — Window Grouping Partition Mismatch)**:
   - *Failure Type*: Invalid window partitioning. Grouped by `calendar_month, gross_revenue` instead of `calendar_month` alone, generating partitioned multi-row output.
5. **`Q18` (Category C — Missing Window Partition)**:
   - *Failure Type*: Missing `PARTITION BY`. Ranked products globally rather than partitioned within each category.
6. **`Q19` (Category C — Missing Projection Column & Rounding)**:
   - *Failure Type*: Missing output column. Calculated percentage contribution via subquery but omitted the required base revenue column and rounding.
7. **`Q25` (Category D — Inverted Column Projection Order)**:
   - *Failure Type*: Column permutation. Projected `(market_type, profit, revenue)` instead of `(market_type, revenue, profit)`.

---

## K. Historical Pre-Remediation vs Post-Remediation Comparison

**Source**: `benchmark/pre_remediation_results.csv`, `benchmark/seed42/benchmark_results.csv`

| Metric | Historical Pre-Remediation (Seed 42) | Post-Remediation (Seed 42) | Post-Remediation 3-Seed Mean | Remediation Attribution |
| :--- | :---: | :---: | :---: | :--- |
| **Memory Retrievals (Mode 4)** | 0 | 16 | 16 ± 0 | Restored by Unit-L2 embedding normalization |
| **Retrieval-Bearing Queries** | 0 / 25 (0%) | 12 / 25 (48%) | 12 ± 0 (48%) | Restored retrieval geometry |
| **Mean Retries (Mode 4)** | 0.40 ± 0.87 | 0.28 ± 0.68 | 0.28 ± 0.00 | Reduced via retrieved context on Q08 & Q19 |
| **Mean Latency (Mode 4)** | 9,186.68 ms | 8,618.89 ms | 8,564.89 ± 103.16 ms | Reduced repair loop iterations |
| **Mean Tokens (Mode 4)** | 600.84 | 542.36 | 542.37 ± 0.02 | Reduced repair token consumption |
| **PG Execution Success (Mode 4)** | 92.0% (23/25) | 96.0% (24/25) | 96.00% ± 0.00% | Q19 executed on Attempt 1 |
| **Relational ExecAcc (Mode 4)** | 68.0% (17/25) | 68.0% (17/25) | 68.00% ± 0.00% | Unchanged (7B semantic reasoning boundary) |
| **Final Store Count (Mode 4)** | 4 | 3 | 3 ± 0 | Deduplicated via mutual exclusion on Q17 |

---

## L. Statistical Limitations

1. **Deterministic Decoding**: With greedy decoding (`temperature = 0.0`) hardcoded at the LLM boundary and the benchmark seed not forwarded to Ollama, repeated runs test **pipeline stability and execution reproducibility**, not stochastic variance over a probability distribution.
2. **Replication Sample Size**: $n = 3$ repeated runs over a fixed 25-query benchmark. While 450 total query executions were performed, these represent 3 passes across 25 queries, not 450 independent random trials.
3. **Absence of Inferential Significance Tests**: Formal $p$-value testing (e.g., paired $t$-tests) is underpowered and inappropriate for $n = 3$. Results must be presented as **descriptive empirical effect sizes** with explicit confidence bounds.

---

## M. Explicit IEEE-Safe Claim Matrix

| Claim Item | Status | Empirical Basis | Approved IEEE Manuscript Wording |
| :--- | :---: | :--- | :--- |
| **1. Embedding Normalization** | **VERIFIED** | Retrievals restored from 0 to 16 in all 3 runs | "Unit-L2 normalization restored intended FAISS retrieval geometry above threshold $\tau = 0.50$." |
| **2. Duplicate Memory Suppression** | **VERIFIED** | Store count invariant at 3; Q17 reinforced | "Mutual exclusion prevented duplicate memory accumulation in the evaluated lifecycle." |
| **3. Execution Safety** | **VERIFIED** | 0 destructive statements reached PostgreSQL in 450 runs | "No destructive SQL reached PostgreSQL in the evaluated benchmark." |
| **4. Repair Iteration Reduction** | **OBSERVED** | 34.38% reduction in retries (0.43 to 0.28) across runs | "Mode 4 exhibited fewer mean repair iterations than stateless self-correction." |
| **5. Token Expenditure Reduction** | **OBSERVED** | 5.30% reduction in tokens (572.72 to 542.37) across runs | "Mode 4 exhibited lower mean token expenditure during repair." |
| **6. End-to-End Latency Reduction** | **NOT SUPPORTED** | Mode 4 is +19.79% slower than Mode 2 | "ARMG incurred latency overhead due to vector embedding and retrieval orchestration." |
| **7. Semantic Accuracy Improvement** | **NOT DEMONSTRATED** | Mode 4 and Mode 2 tied at 68.00% relational accuracy | "ARMG did not demonstrate an improvement in relational semantic equivalence over self-correction." |
| **8. Temporal Decay Effectiveness** | **NOT DEMONSTRATED** | Real-time static clock ($\Delta t \approx 0.002$ days) | "Temporal decay effectiveness remains experimentally untested under realistic elapsed-time conditions." |
| **9. General Negative Constraint Benefit**| **NOT DEMONSTRATED** | Retry reduction observed exclusively on Q19 | "Negative constraints were associated with fewer repair iterations specifically on query Q19." |
| **10. Causal Superiority of Memory** | **NOT DEMONSTRATED** | Observational association; counterfactual unproven | "Memory retrieval was associated with Attempt-1 execution on specific queries." |
| **11. Multi-Seed Stochastic Generalization**| **NOT DEMONSTRATED** | Greedy decoding (`temperature = 0.0`) | "The benchmark demonstrated deterministic pipeline reproducibility across repeated executions." |

---

## N. Known Limitations and Future Experiments

1. **Semantic Ceiling of 7B LLMs**: The 68% relational equivalence plateau across Modes 2, 3, 4, 5, 6 underscores that operational memory cannot overcome inherent structural window-function reasoning limitations of 7B models. Future work: evaluation with 70B+ frontier models.
2. **Synthetic Temporal Drift**: Demonstrating temporal decay requires synthetic epoch injection (e.g., simulating 30-day, 60-day intervals) or live continuous deployment over calendar months.
3. **Counterfactual Memory Intervention**: Rigorous causal attribution requires controlled A/B query-level ablation where specific memories are dynamically masked during repair.

---

## O. Reproducibility Information

- **Repository**: `armg main` (root commit)
- **Hardware Profile**: Local workstation, NVIDIA GPU acceleration via Ollama
- **Software Dependencies**: Python 3.11.9, PyTorch 2.x, FAISS-CPU 1.8.0, LangGraph 0.2.x, SQLGlot 25.x, psycopg2-binary 2.9.x
- **Ollama Models**:
  - `qwen2.5:7b-instruct` (Digest: verified local pull)
  - `nomic-embed-text` (Digest: verified local pull, 768 dimensions)
- **Database Warehouse**: PostgreSQL 16.2 running on port 5432, pre-seeded via `scripts/seed_warehouse.py`
- **Regression Suite**: 154 unit and integration tests passing (`pytest tests/ -q`)

---
