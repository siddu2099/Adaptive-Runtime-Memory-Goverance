# ARMG Manuscript Evidence Package
## Authoritative Experimental Data & Forensic Reference for IEEE Drafting
**Status**: Authoritative & Frozen  
**Date**: September 2026  
**Repository**: `armg main`  
**Execution Context**: Local Ollama (`qwen2.5:7b-instruct`), PostgreSQL 18.1 Warehouse, `nomic-embed-text` (768-dim, Unit-L2 normalized)

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
- **Seed Handling & Deterministic Decoding**: The benchmark seed argument (`--seed`) is plumbed directly through `SQLGenerator(seed)` and `RepairSQLGenerator(seed)` into Ollama API options (`options["seed"]`). However, because greedy decoding is strictly enforced (`temperature = 0.0`), repeated seed executions represent configuration-isolated repeated evaluations assessing pipeline reproducibility, execution stability, and memory-state consistency across identical deterministic prompts, rather than stochastic model-sampling trials over an unconstrained distribution.
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
- **PostgreSQL Execution Success (`is_success`)**: Boolean flag indicating whether generated SQL executed against PostgreSQL 18.1 without error and returned a result set.
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
| **Mode 1** | 60.00% ± 0.00% | 80.00% ± 0.00% | 0.00 ± 0.00 | 4,859.70 ± 7.98 | 360.57 ± 0.37 | 0 (0) | 0 | 0 | 0 |
| **Mode 2** | 68.00% ± 0.00% | 96.00% ± 0.00% | 0.28 ± 0.00 | 6,441.56 ± 105.51 | 503.72 ± 0.42 | 0 (0) | 0 | 0 | 0 |
| **Mode 3** | 68.00% ± 0.00% | 92.00% ± 0.00% | 0.00 ± 0.00 | 6,776.25 ± 34.40 | 558.28 ± 0.00 | 69 (24) | 23 | 0 | 23 |
| **Mode 4** | **68.00% ± 0.00%** | **96.00% ± 0.00%** | **0.37 ± 0.05** | **9,000.59 ± 184.33** | **602.85 ± 28.49** | **16 (12)** | **3** | **2.67 ± 0.58** | **3** |
| **Mode 5** | 68.00% ± 0.00% | 96.00% ± 0.00% | 0.32 ± 0.00 | 8,768.48 ± 100.30 | 530.97 ± 0.40 | 16 (12) | 3 | 2 | 4 |
| **Mode 6** | 68.00% ± 0.00% | 96.00% ± 0.00% | 0.28 ± 0.00 | 8,507.98 ± 73.15 | 542.27 ± 0.39 | 16 (12) | 3 | 2 | 3 |

*Note: All `±` values in the table above denote sample standard deviation across the three repeated benchmark runs ($n = 3$), capturing run-to-run execution variability.*

### 2. Individual Run Breakdowns
- **Seed 42**:
  - Mode 1: ExecAcc: 60.0%, PG: 80.0%, Retries: 0.00, Latency: 4,853.30 ms, Tokens: 360.16
  - Mode 2: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 6,563.40 ms, Tokens: 503.96
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,811.90 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.32, Latency: 8,787.93 ms, Tokens: 569.96
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.32, Latency: 8,713.49 ms, Tokens: 530.72
  - Mode 6: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,453.39 ms, Tokens: 542.00
- **Seed 123**:
  - Mode 1: ExecAcc: 60.0%, PG: 80.0%, Retries: 0.00, Latency: 4,857.15 ms, Tokens: 360.68
  - Mode 2: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 6,380.63 ms, Tokens: 503.24
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,773.60 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.40, Latency: 9,114.66 ms, Tokens: 619.36
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.32, Latency: 8,707.71 ms, Tokens: 531.44
  - Mode 6: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,479.46 ms, Tokens: 542.72
- **Seed 999**:
  - Mode 1: ExecAcc: 60.0%, PG: 80.0%, Retries: 0.00, Latency: 4,868.63 ms, Tokens: 360.88
  - Mode 2: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 6,380.67 ms, Tokens: 503.96
  - Mode 3: ExecAcc: 68.0%, PG: 92.0%, Retries: 0.00, Latency: 6,743.25 ms, Tokens: 558.28
  - Mode 4: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.40, Latency: 9,099.18 ms, Tokens: 619.24
  - Mode 5: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.32, Latency: 8,884.26 ms, Tokens: 530.76
  - Mode 6: ExecAcc: 68.0%, PG: 96.0%, Retries: 0.28, Latency: 8,591.09 ms, Tokens: 542.08

---

## E. Mode 2 vs Mode 4 Comparison

**Source**: `scratch/generate_all_tables.py`, `benchmark/seed*/benchmark_results.csv`

### 1. Comparative Performance Metrics

| Dimension | Mode 2 (Stateless Self-Correction) | Mode 4 (Full ARMG) | Absolute Delta ($\Delta$) | Relative Delta (%) | Consistency Across Runs |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Relational ExecAcc** | 68.00% ± 0.00% | 68.00% ± 0.00% | 0.00 pp | 0.00% | 17/25 in all 3 runs (51/75 total) |
| **PostgreSQL Exec Success** | 96.00% ± 0.00% | 96.00% ± 0.00% | 0.00 pp | 0.00% | 24/25 in all 3 runs (72/75 total; Q11 failed in both) |
| **Mean Retries** | 0.2800 ± 0.00 | 0.3733 ± 0.05 | +0.0933 | **+33.33%** | Higher in Mode 4 across all 3 runs (0.32, 0.40, 0.40 vs 0.28) |
| **Mean Tokens** | 503.72 ± 0.42 | 602.85 ± 28.49 | +99.13 | **+19.68%** | Higher in Mode 4 across all 3 runs (569.96, 619.36, 619.24 vs 503.72) |
| **Mean Latency (ms)** | 6,441.56 ± 105.51 | 9,000.59 ± 184.33 | +2,559.03 ms | **+39.73%** | Higher in Mode 4 across all 3 runs (8,787.93, 9,114.66, 9,099.18 vs ~6,441.56) |

### 2. Query-Level Divergence
Across the 25 queries, Mode 4 and Mode 2 exhibited retry divergence on exactly **2 queries**:
- **`Q08` (Category B — Join Aggregation)**:
  - *Mode 2*: Executed cleanly on Attempt 1 without retries (`retries = 0`) across all 3 seeds.
  - *Mode 4*: Retrieved memory admitted during `Q04` (`mem-f5e66b70` / `mem-9a657f60` / `mem-67c56e5b`); encountered an initial syntax error on Attempt 1 and required 1 repair retry before succeeding on Attempt 2 (`retries = 1`) across all 3 seeds.
  - *Effect*: Extra repair retry (+1 retry, +677.7 tokens) in Mode 4 across all 3 runs.
- **`Q19` (Category C — Percentage Contribution)**:
  - *Mode 2*: Executed cleanly on Attempt 1 without retries (`retries = 0`) across all 3 seeds.
  - *Mode 4*: Executed cleanly on Attempt 1 in Seed 42 (`retries = 0`), but in Seeds 123 and 999 retrieved memory and required 2 repair retries before succeeding on Attempt 3 (`retries = 2`, +1230 tokens).
  - *Effect*: Extra repair retries (+2 retries) in Seeds 123 and 999.
- **`Q11` (Category B — Multi-Table Join on Market Type)**:
  - Persistent execution failure in both Mode 2 and Mode 4 across all 3 runs (exhausted 3 retries, `is_success = False`). Rejected by Mode 4 admission gate (`TERMINAL_FAILURE_NOT_ADMITTED`).
- **Remaining 22 Queries**: Exactly identical retry counts between Mode 2 and Mode 4. Zero queries exhibited relational semantic accuracy difference (51/75 correct in both modes; 7 semantic divergence queries in both modes).

---

## F. Mode 4 vs Mode 5 Comparison (Ablation of Negative Constraints)

**Source**: `benchmark/seed*/benchmark_results.csv`

### 1. Comparative Metrics
- **Mean Retries**: Mode 4 required **0.37 ± 0.05 retries** vs Mode 5's **0.32 ± 0.00 retries** across the three runs.
- **Relational ExecAcc**: 68.00% vs 68.00% (identical; 51/75 correct).
- **PostgreSQL Exec Success**: 96.00% vs 96.00% (identical; 72/75 correct).
- **Mean Latency**: 9,000.59 ± 184.33 ms vs 8,768.48 ± 100.30 ms.
- **Mean Tokens**: 602.85 ± 28.49 vs 530.97 ± 0.40.
- **Store Size**: 3 in Mode 4 vs 4 in Mode 5 (an additional memory was admitted in Mode 5 in the absence of negative constraint pruning).

### 2. Query-Level Attribution
- In Mode 5 (ablating diagnostic negative constraints), prompt construction omitted forbidden tokens and invalid join predicates. Both modes achieved identical overall execution success (96.00%) and relational accuracy (68.00%).
- *Defensible Scope*: Diagnostic negative constraints provide structured prompt exclusion, though empirical overall success rates remained identical on the evaluated benchmark.

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

**Source**: `graph/workflow.py`, `memory/vector_store.py`, `benchmark/benchmark_results.csv`, `benchmark/retrieval_telemetry.csv`, `benchmark/seed*/benchmark_results.csv`

### 1. Store Size Progression and Event Narrative
Across all three repeated benchmark executions, the Mode 4 FAISS store progressed deterministically along the identical store-size trajectory: **$0 \to 1 \to 2 \to 3$**:
- `Q01–Q03`: Store size = 0 (no operational memories admitted yet).
- `Q04`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (memory admitted following Q04; representative Seed-42 runtime ID: `mem-f5e66b70`, Seed-123: `mem-9a657f60`, Seed-999: `mem-67c56e5b`). Store size = 1.
- `Q05–Q07`: Store size = 1.
- `Q08`: Failed attempt 1; repaired attempt 2 using applied memory admitted following Q04 $\implies$ **Reinforced** across all three seeds (`EXISTING_REINFORCED`: Seed 42: `mem-f5e66b70`, Seed 123: `mem-9a657f60`, Seed 999: `mem-67c56e5b`). Algorithmic mutual exclusion suppressed new admission. Store size = 1.
- `Q09–Q10`: Store size = 1.
- `Q11`: Persistent failure through attempt 3; rejected by admission gate (`TERMINAL_FAILURE_NOT_ADMITTED`). Store size = 1.
- `Q12`: Store size = 1.
- `Q13`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (memory admitted following Q13; representative Seed-42 runtime ID: `mem-4ff9e3d8`, Seed-123: `mem-3a591268`, Seed-999: `mem-eff35a5a`). Store size = 2.
- `Q14`: Store size = 2.
- `Q15`: Failed attempt 1; repaired attempt 2 without applied memory $\implies$ **Admitted** (memory admitted following Q15; representative Seed-42 runtime ID: `mem-3663aecf`, Seed-123: `mem-b89b015e`, Seed-999: `mem-35e3ff3f`). Store size = 3.
- `Q16`: Store size = 3.
- `Q17`: Failed attempt 1; repaired attempt 2 using applied memory $\implies$ **Reinforced** across all three seeds (`EXISTING_REINFORCED`: Seed 42: `mem-4ff9e3d8`, Seed 123: `mem-3a591268`, Seed 999: `mem-67c56e5b`). Mutual exclusion suppressed new admission. Store size = **3 (invariant plateau)**.
- `Q18`: Store size = 3.
- `Q19`:
  - *Seed 42*: Executed cleanly on Attempt 1 without retries (`retries = 0`). No repair was required; no memory was reinforced. Store size = 3.
  - *Seeds 123 & 999*: Repaired on Attempt 3 using applied memory admitted following Q15 $\implies$ **Reinforced** across both seeds (`EXISTING_REINFORCED`: Seed 123: `mem-b89b015e`, Seed 999: `mem-35e3ff3f`). Mutual exclusion suppressed new admission. Store size = **3 (invariant plateau)**.
- `Q20–Q25`: Store size = 3.

**Key Invariant**: The persistent store-size trajectory remained deterministically identical at **$0 \to 1 \to 2 \to 3$** across all three seeds despite the seed-specific reinforcement distributions on Q19. Mode 4 held strictly invariant at exactly 3 memories from Q15 through Q25.

### 2. Operational Lifecycle Metrics (Precise Denominators)
To maintain complete empirical rigor, metrics are explicitly distinguished across the 4 operational lifecycle stages rather than collapsed into a single metric:

1. **Retrieval**:
   - **Total Retrieval Events**: 16 retrieval events per run passing similarity threshold $\tau = 0.50$ ($16 \times 3 = 48$ aggregate retrieval events across all 3 seeds).
   - **Retrieval-Bearing Queries**: 12 queries out of 25 per run (48.0% benchmark coverage: `Q08`, `Q10`, `Q16–Q25`).
   - **Prompt-Context Application Rate**: $12 / 12 = 100.0\%$ per run ($36 / 36 = 100.0\%$ aggregate across seeds). All retrieved operational memories were injected into the generation prompt.

2. **Memory Application During Repair**:
   - **Memory-Applied Repair Events**: Exactly **8 events** across the 3-seed benchmark:
     - `Q08`: 3 events (seeds 42, 123, 999; repaired using memory admitted following Q04).
     - `Q17`: 3 events (seeds 42, 123, 999; repaired using memory admitted following Q13).
     - `Q19`: 2 events (seeds 123, 999; repaired using memory admitted following Q15).
   - **Distinct Query IDs Involved in Memory-Applied Repair**: Exactly **3 queries** (`Q08`, `Q17`, `Q19`).

3. **Execution Success Following Memory Application**:
   - **Successful PostgreSQL Execution Rate**: **$8 / 8 = 100.0\%$**. All 8 memory-applied repair attempts executed successfully on PostgreSQL 18.1.

4. **Reinforcement Following Applied Repair**:
   - **Existing-Memory Reinforcement Rate**: **$8 / 8 = 100.0\%$**. In all 8 successful memory-applied repair events, the governance engine reinforced the existing memory's utility and suppressed new admission (`memory_admission == "EXISTING_REINFORCED"`).

5. **New Admissions**:
   - **New Admission Events**: Exactly **3 queries** admitted new memories across all runs (`Q04`, `Q13`, `Q15`), totaling 9 admission events across the 3 seeds (3 per run).
   - **Admitted Operational Patterns**: Join structure on `dim_geography` (`Q04`), multi-table join and aggregation (`Q13`), and window aggregation structure (`Q15`).

6. **Duplicate Memory Accumulation**:
   - **0 duplicate entries** across all runs. Store size plateaued at 3 memories in Mode 4, whereas unmanaged Naive Vector RAG (Mode 3) accumulated 23 uncurated entries.

### 3. Representation Distinctions (Figure 6 & Table D vs Cross-Seed Aggregate)
- **Representative Single-Seed Artifacts**: Figure 6 (`manuscript/figures/png/fig6_memory_growth.png`) and Table D (`manuscript/tables/table_fig6_validation.tex`) are dynamically generated from Seed 42 (`benchmark/seed42/benchmark_results.csv`). In Seed 42, `Q19` succeeded on Attempt 1 without retries, displaying 2 reinforcement events (`Q08` reinforcing `mem-f5e66b70` and `Q17` reinforcing `mem-4ff9e3d8`).
- **Cross-Seed Aggregate Evidence**: Across the full 3-seed benchmark (75 Mode 4 evaluations), 8 reinforcement events occurred across queries `Q08`, `Q17`, and `Q19` (2 reinforcements in Seed 42; 3 in Seed 123; 3 in Seed 999; mean $2.67 \pm 0.58$). In all cases, runtime FAISS IDs are run-specific hex UUIDs, while the store-size progression ($0 \to 1 \to 2 \to 3$) and plateau at 3 remain invariant.

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
| **Mean Retries (Mode 4)** | 0.40 ± 0.87 | 0.32 ± 0.69 | 0.37 ± 0.05 | Extra retry on Q08 (+1) and Q19 (+2 in seeds 123, 999) |
| **Mean Latency (Mode 4)** | 9,186.68 ms | 8,787.93 ms | 9,000.59 ± 184.33 ms | Orchestration overhead of LangGraph and FAISS |
| **Mean Tokens (Mode 4)** | 600.84 | 569.96 | 602.85 ± 28.49 | Prompt augmentation and repair token consumption |
| **PG Execution Success (Mode 4)** | 92.0% (23/25) | 96.0% (24/25) | 96.00% ± 0.00% | 24/25 queries executed (Q11 persistent failure) |
| **Relational ExecAcc (Mode 4)** | 68.0% (17/25) | 68.0% (17/25) | 68.00% ± 0.00% | Invariant across modes (7B semantic reasoning boundary) |
| **Final Store Count (Mode 4)** | 4 | 3 | 3 ± 0 | Deduplicated via mutual exclusion (8 reinforcement events across Q08, Q17, Q19) |

---

## L. Statistical Limitations

1. **Deterministic Decoding & Seed Propagation**: While benchmark seeds (42, 123, 999) are propagated to the local Ollama instance (`options["seed"]`), greedy decoding (`temperature = 0.0`) is enforced at the LLM boundary. Consequently, repeated runs test **pipeline execution stability, reproducibility, and memory-state consistency** under identical prompt conditions, rather than stochastic variance over a probability distribution.
2. **Replication Sample Size**: $n = 3$ repeated runs over a fixed 25-query benchmark. While 450 total query executions were performed, these represent 3 passes across 25 queries, not 450 independent random trials.
3. **Absence of Inferential Significance Tests**: Formal $p$-value testing (e.g., paired $t$-tests) is underpowered and inappropriate for $n = 3$. Results must be presented as **descriptive empirical effect sizes** with explicit confidence bounds.

---

## M. Explicit IEEE-Safe Claim Matrix

| Claim Item | Status | Empirical Basis | Approved IEEE Manuscript Wording |
| :--- | :---: | :--- | :--- |
| **1. Embedding Normalization** | **VERIFIED** | Retrievals restored from 0 to 16 in all 3 runs | "Unit-L2 normalization restored intended FAISS retrieval geometry above threshold $\tau = 0.50$." |
| **2. Duplicate Memory Suppression** | **VERIFIED** | Store count invariant at 3 across Q15–Q25; existing memories reinforced on Q08, Q17, Q19 | "Mutual exclusion prevented duplicate memory accumulation in the evaluated lifecycle." |
| **3. Execution Safety** | **VERIFIED** | 0 destructive statements reached PostgreSQL in 450 runs | "No destructive SQL reached PostgreSQL in the evaluated benchmark." |
| **4. Repair Iteration Shift** | **OBSERVED** | 33.33% increase in retries (0.28 to 0.37) across runs | "Mode 4 exhibited +0.09 mean repair iterations relative to stateless self-correction due to retrieved context syntax interactions on Q08 and Q19." |
| **5. Token Expenditure Shift** | **OBSERVED** | 19.68% increase in tokens (503.72 to 602.85) across runs | "Mode 4 exhibited higher mean token expenditure due to few-shot memory context injection and associated repair prompt expansions." |
| **6. End-to-End Latency Overhead** | **OBSERVED** | Mode 4 is +39.73% (+2,559.03 ms) slower than Mode 2 | "ARMG incurred latency overhead due to vector embedding and retrieval orchestration." |
| **7. Semantic Accuracy Parity** | **OBSERVED** | Mode 4 and Mode 2 tied at 68.00% relational accuracy | "ARMG did not demonstrate an improvement in relational semantic equivalence over stateless self-correction." |
| **8. Temporal Decay Effectiveness** | **NOT DEMONSTRATED** | Real-time static clock ($\Delta t \approx 0.002$ days) | "Temporal decay effectiveness remains experimentally untested under realistic elapsed-time conditions." |
| **9. General Negative Constraint Benefit**| **NOT DEMONSTRATED** | Success rates identical between Mode 4 and Mode 5 | "Negative constraints provided structured syntax guidance, but empirical execution success was identical across modes." |
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
- **Software Dependencies**: Python 3.11.9 (.venv) / Python 3.13.2 (system), PyTorch 2.x, FAISS-CPU 1.8.0, LangGraph 0.2.x, SQLGlot 25.x, psycopg2-binary 2.9.x
- **Ollama Models**:
  - `qwen2.5:7b-instruct` (Digest: verified local pull)
  - `nomic-embed-text` (Digest: verified local pull, 768 dimensions)
- **Database Warehouse**: PostgreSQL 18.1 running on port 5432, pre-seeded via `scripts/seed_warehouse.py`
- **Regression Suite**: 401 total active tests (372 unit tests + 17 integration tests + 12 environment tests) passing (`pytest tests/`)

---
