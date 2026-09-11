# Adaptive Runtime Memory Governance: A Governed Operational Knowledge Framework for Runtime Repair and Safety in Local Text-to-SQL Systems

**Primary Title**: Adaptive Runtime Memory Governance: A Governed Operational Knowledge Framework for Runtime Repair and Safety in Local Text-to-SQL Systems  
**Alternative Title Proposals**:
1. *Governed Operational Knowledge for Local Text-to-SQL: Architecture, Runtime Repair, and Execution Safety*
2. *Closed-Loop Runtime Memory Governance for Safe and Bounded Text-to-SQL Repair in Enterprise Warehouses*
3. *Adaptive Memory Governance in Local LLM Text-to-SQL: Operational Knowledge Extraction, Repair Efficiency, and Safety Boundaries*

---

## Abstract
Deploying local Large Language Models (LLMs) for enterprise Text-to-SQL workflows presents critical operational challenges: localized schema reasoning traps, unconstrained error repair loops, catastrophic memory accumulation in retrieval systems, and the hazard of executing destructive queries against enterprise warehouses. Standard stateless self-correction mechanisms repeatedly generate queries against raw database errors without cross-query memory, while unmanaged vector retrieval systems suffer from duplicate accumulation and memory poisoning. This paper presents **Adaptive Runtime Memory Governance (ARMG)**, a closed-loop runtime architecture that converts PostgreSQL execution feedback into governed, reusable operational memory. ARMG integrates deterministic AST- and catalog-based error diagnosis, ephemeral knowledge extraction, admission- and reinforcement-gated vector memory, diagnostic negative constraints, and a pre-execution AST safety guardrail.

In an empirical evaluation across 450 query runs (three repeated executions across six experimental configurations on a 25-query enterprise warehouse benchmark using `qwen2.5:7b-instruct`), ARMG achieved **100% pre-execution safety**, preventing any destructive SQL statement from reaching the database. Across the repeated evaluations, ARMG achieved a **34.38% reduction in mean repair iterations** (0.28 vs. 0.43 retries per query) and a **5.30% reduction in token consumption** relative to stateless self-correction, while increasing PostgreSQL execution success from 92.00% to 96.00%. However, end-to-end latency increased by 19.79% due to vector embedding and retrieval orchestration, and relational semantic equivalence plateaued at 68.00% across both ARMG and stateless self-correction. These findings demonstrate that governed operational memory provides bounded repair behavior, token economy, and verifiable execution safety, while highlighting that operational memory alone does not resolve the fundamental semantic window-function reasoning boundaries of 7B-parameter models.

---

## Index Terms
Text-to-SQL, Large Language Models, Runtime Memory Governance, Vector Retrieval, Database Safety, Query Repair, LangGraph, Enterprise Data Warehouses.

---

## 1. Introduction
Enterprise adoption of natural language interfaces to relational databases (Text-to-SQL) has accelerated with advances in instruction-tuned Large Language Models [REF]. However, organizations with stringent data privacy, sovereignty, or cost constraints often require fully on-premises deployment using localized open-weights models (e.g., 7B-parameter architectures) [REF]. Deploying smaller LLMs locally introduces acute challenges:
1. **Repetitive Repair Failures**: Stateless self-correction approaches [REF] prompt the model with raw execution errors, often causing the model to oscillate between identical invalid SQL constructs across repair cycles.
2. **Retrieval Corruption & Poisoning**: Naive vector retrieval-augmented generation (RAG) stores raw historical queries without lifecycle management, causing duplicate accumulation, out-of-date schema retention, and semantic drift [REF].
3. **Execution Safety Hazards**: Unbounded Text-to-SQL agents risk generating destructive DML or DDL statements (`DELETE`, `DROP`, `UPDATE`), posing catastrophic operational risks if connected to live warehouse environments [REF].
4. **The Executable vs. Semantic Correctness Gap**: While commercial evaluations frequently report database execution rates, executable SQL is frequently non-equivalent to the analytical intent of the user [REF].

To address these limitations, we introduce **Adaptive Runtime Memory Governance (ARMG)**, an operational framework that governs the extraction, admission, retrieval, reinforcement, and application of runtime operational knowledge. Rather than attempting to train or fine-tune model weights, ARMG structures execution feedback into an ephemeral diagnostic intermediate representation (`RuntimeKnowledge`) that undergoes mathematical admission gating before entering a persistent FAISS vector index. Crucially, ARMG enforces strict mutual exclusion between the reinforcement of existing memories and the admission of new memories, preventing memory duplication. A SQLGlot-based AST validation layer acts as a strict safety barrier prior to database execution.

We evaluate ARMG through an empirical evaluation protocol across 450 post-remediation query evaluations (three repeated executions across six experimental modes on an enterprise Star Schema benchmark). Our experimental findings demonstrate:
- **Verified Retrieval Geometry**: Unit-L2 normalization of runtime query embeddings restored the intended FAISS L2 similarity geometry, achieving 16 retrieval events across 12 benchmark queries.
- **Controlled Lifecycle & Deduplication**: Mutual exclusion successfully prevented duplicate memory growth, maintaining store size invariant at 3 memories across all runs.
- **Repair-Loop Efficiency**: ARMG achieved an observed 34.38% reduction in repair loop iterations (0.28 vs. 0.43 retries) and a 5.30% reduction in token consumption compared to stateless self-correction.
- **Architectural Latency Trade-Off**: ARMG incurred a 19.79% end-to-end latency penalty, establishing that ARMG trades wall-clock orchestration overhead for repair iteration efficiency.
- **Semantic Equivalence Plateau**: Relational semantic accuracy remained identical at 68.00% between ARMG and stateless self-correction, demonstrating that operational memory does not overcome the baseline semantic window-reasoning limitations of local 7B models.

---

## 2. Related Work
### 2.1 Text-to-SQL and Self-Correction
State-of-the-art Text-to-SQL frameworks typically utilize in-context learning, schema pruning, and multi-turn self-correction [REF]. Stateless self-correction methods feed runtime execution exceptions back to the LLM [REF]. However, without persistent memory, the agent cannot transfer repair strategies across sequential queries within a session, leading to redundant repair attempts on recurring schema traps.

### 2.2 Memory-Augmented LLM Systems and Vector RAG
Retrieval-Augmented Generation (RAG) architectures store historical text or SQL pairs in vector databases [REF]. Recent work has explored memory mechanisms for conversational agents [REF]. However, unmanaged vector stores lack lifecycle governance equations, admission filtering, utility decay, or duplicate suppression, resulting in memory poisoning and index saturation.

### 2.3 Database Safety and Guardrails
Prompt-based safety instructions are vulnerable to jailbreaks and semantic confusion [REF]. Runtime validation mechanisms employing deterministic Abstract Syntax Tree (AST) parsing [REF] provide strict formal safety guarantees by decoupling policy enforcement from probabilistic LLM behavior.

---

## 3. Problem Formulation
Let $q \in \mathcal{Q}$ denote a natural language analytical question over a relational warehouse schema $\mathcal{S} = (\mathcal{T}, \mathcal{C}, \mathcal{R})$ comprising tables $\mathcal{T}$, columns $\mathcal{C}$, and foreign-key relationships $\mathcal{R}$. A generator $\mathcal{G}_{\theta}$ parameterized by local model weights $\theta$ maps question $q$ and pruned schema $\mathcal{S}_q \subseteq \mathcal{S}$ to SQL query $s_0 = \mathcal{G}_{\theta}(q, \mathcal{S}_q)$.

Execution of query $s$ in environment $\mathcal{E}$ yields an execution result $R = \mathcal{E}(s)$, which is either a successful tuple set $\mathcal{D}_s$ or an execution error $e$. If $R$ fails, a repair agent generates replacement query $s_{k+1}$ conditioned on diagnostic feedback, bounded by maximum repair budget $K_{\max} = 3$.

Relational semantic equivalence is defined strictly: query $s$ is correct if and only if its execution result $\mathcal{D}_s$ is relationally equivalent to gold execution result $\mathcal{D}_{s^*}$ under bag/set equivalence: $\mathcal{D}_s \equiv_{\text{rel}} \mathcal{D}_{s^*}$. Crucially, PostgreSQL execution success ($\mathcal{E}(s) \neq \text{error}$) is a necessary but insufficient condition for relational equivalence.

---

## 4. ARMG Architecture
The ARMG architecture is implemented as a state graph comprising nine functional stages:
1. **Schema Introspection and Pruning**: Dynamically inspects table schemas and prunes irrelevant tables via token matching.
2. **Vector Memory Retrieval**: Embeds the user question and queries FAISS for governed memories exceeding retrieval threshold $\tau = 0.50$.
3. **SQL Generation**: Synthesizes read-only PostgreSQL queries under greedy decoding (`temperature = 0.0`).
4. **AST Safety Guard**: Parses generated SQL into an AST via SQLGlot, halting any destructive statement before database access.
5. **PostgreSQL Execution**: Executes validated read-only queries against PostgreSQL 16.
6. **Deterministic Error Diagnosis**: Classifies execution failures into a deterministic error taxonomy.
7. **Ephemeral Knowledge Extraction**: Constructs an operational `RuntimeKnowledge` record.
8. **Runtime-Guided Repair**: Injects error diagnosis, negative constraints, and retrieved operational memory into the repair prompt.
9. **Memory Governance & Lifecycle**: Evaluates admission, reinforcement, utility updates, and store persistence.

---

## 5. Runtime Observation and Knowledge Extraction
When an execution error occurs, raw PostgreSQL stderr strings are ingested by the `RuntimeObserver` (`environment/observation.py`) and normalized into structured observations containing SQL state codes, error classes, and target identifiers.

The `DiagnosticEngine` (`agents/error_diagnosis.py`) deterministically maps normalized observations into a five-class taxonomy:
1. `SYNTAX_ERROR`: Malformed SQL grammar or invalid keywords.
2. `SCHEMA_VIOLATION`: Column or table identifiers not present in schema $\mathcal{S}$.
3. `JOIN_ERROR`: Ambiguous column references or missing foreign-key joins.
4. `TYPE_MISMATCH`: Incompatible operator data types.
5. `SEMANTIC_LOGIC`: Aggregation, grouping, or window function partition errors.

From this diagnosis, ARMG extracts an ephemeral `RuntimeKnowledge` object:
- `error_type`: Taxonomy classification.
- `root_cause`: Deterministic explanation of failure.
- `repair_strategy`: Actionable structural rule for the repair prompt.
- `negative_constraints`: Explicitly forbidden identifiers or patterns.

---

## 6. Memory Governance and Lifecycle
ARMG transforms ephemeral `RuntimeKnowledge` into persistent `RuntimeMemory` through a mathematical governance engine (`memory/governance.py`).

### 6.1 Admission Control
A newly derived `RuntimeKnowledge` instance is admitted to the vector store if and only if its initial confidence $C_0$ and utility $U_0$ satisfy:
$$\text{Admit}(M) \iff (C_0 \ge \tau_{\text{admit}}) \land (U_0 \ge \tau_{\text{admit}})$$
where $\tau_{\text{admit}} = 0.50$. Initial values are set to $C_0 = 0.55, U_0 = 0.55$. Unrecoverable terminal failures (`retry_count = 3`) are rejected under `TERMINAL_FAILURE_NOT_ADMITTED`.

### 6.2 Reinforcement & Mutual Exclusion
When query repair succeeds with an explicitly applied memory $M_{\text{applied}}$, ARMG reinforces the existing memory:
$$U_{t+1} = U_t + \alpha (1 - U_t)$$
$$C_{t+1} = C_t + \beta (1 - C_t)$$
where $\alpha = 0.10, \beta = 0.15$.

**Mutual Exclusion Invariant**: Reinforcing an applied memory and admitting new knowledge are mutually exclusive:
$$\text{Action} = \begin{cases} \text{Reinforce}(M_{\text{applied}}), & \text{if } M_{\text{applied}} \neq \emptyset \\ \text{Admit}(\text{Knowledge}), & \text{if } M_{\text{applied}} = \emptyset \land \text{Success} \end{cases}$$
This mechanism prevents duplicate memory accumulation when a known repair pattern is reused.

### 6.3 Temporal Utility Decay
Memory utility decays over elapsed time $\Delta t$ according to:
$$U(t + \Delta t) = U(t) \cdot \exp(-\lambda \Delta t)$$
where $\lambda = 0.05/\text{day}$. Memories with $U < 0.15$ are archived.

---

## 7. Runtime-Guided Repair and Negative Constraints
During repair, the `RepairSQLGenerator` constructs a structured prompt containing:
1. Database schema context.
2. Original user question.
3. Previously failed SQL query.
4. Specific PostgreSQL error message.
5. **Strict Negative Constraints**: Forbidden column names, prohibited join constructs, and banned AST subtrees derived during diagnosis.
6. **Operational Memory Context**: Actionable rules and root-cause explanations from retrieved memories.

---

## 8. Safety Enforcement
To guarantee safety in production data environments, ARMG implements a multi-layered guardrail:
- **Prompt Directive**: Instructs the LLM to output only read-only `SELECT` queries.
- **Deterministic AST Parser**: The `ExecutionValidator` parses every query using SQLGlot. Any AST root node matching `Delete`, `Drop`, `Update`, `Insert`, `Alter`, or `Truncate` is immediately rejected.
- **Blocked State**: Safety rejections transition the state graph directly to `STATUS_BLOCKED`, bypassing PostgreSQL execution entirely and rejecting memory admission.

---

## 9. Experimental Methodology
### 9.1 Evaluation Configuration
- Model: `qwen2.5:7b-instruct` (Ollama, local GPU inference).
- Embedding: `nomic-embed-text` (768 dimensions, Unit-L2 normalized).
- Vector Index: FAISS `IndexIDMap2(IndexFlatL2(768))`.
- Warehouse: PostgreSQL 16 on `localhost:5432` (`armg_db`).
- Benchmark: 25 queries across Categories A, B, C, D (`benchmark/queries.json`).
- Repeated Runs: Three repeated executions (Seeds 42, 123, 999) evaluating pipeline stability.
- Total Evaluations: 450 post-remediation query runs ($3 \text{ seeds} \times 6 \text{ modes} \times 25 \text{ queries}$).

---

## 10. Experimental Results

### 10.1 Comparative Results (Table 1)

Table 1 reports mean and sample standard deviations across the three repeated benchmark executions ($n = 3$).

```
Table 1: Comparative Evaluation Results across Three Repeated Executions (n=3)
===================================================================================================================================================
Mode                                Relational ExecAcc (%)   PostgreSQL Success (%)   Mean Retries      Mean Latency (ms)      Mean Tokens
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 1 (Zero-Shot)                  57.33% ± 2.31%           76.00% ± 0.00%           0.00 ± 0.00       5,087.73 ± 210.33      360.48 ± 0.48
Mode 2 (Stateless Self-Correction)  68.00% ± 0.00%           92.00% ± 0.00%           0.43 ± 0.02       7,149.68 ± 231.65      572.72 ± 12.68
Mode 3 (Naive Vector RAG)           68.00% ± 0.00%           92.00% ± 0.00%           0.00 ± 0.00       6,844.01 ± 56.90       558.28 ± 0.00
Mode 4 (Full ARMG)                  68.00% ± 0.00%           96.00% ± 0.00%           0.28 ± 0.00       8,564.89 ± 103.16      542.37 ± 0.02
Mode 5 (ARMG - Neg Constraints)     68.00% ± 0.00%           96.00% ± 0.00%           0.36 ± 0.00       8,941.28 ± 108.68      553.93 ± 0.02
Mode 6 (ARMG - Temporal Decay λ=0)  68.00% ± 0.00%           94.67% ± 2.31%           0.37 ± 0.02       9,036.97 ± 178.55      599.67 ± 13.94
===================================================================================================================================================
```

### 10.2 Mode 4 vs. Mode 2 Performance Analysis
- **Repair Iteration Efficiency**: Mode 4 achieved a **34.38% reduction in mean repair iterations** (0.28 vs. 0.43 retries per query), observed consistently across all three runs (Seed 42: 0.28 vs. 0.44; Seed 123: 0.28 vs. 0.44; Seed 999: 0.28 vs. 0.40).
- **Token Expenditure**: Mode 4 consumed **5.30% fewer tokens** (542.37 vs. 572.72 tokens per query) by avoiding repetitive repair prompt/completion cycles.
- **PostgreSQL Execution Success**: Mode 4 achieved **96.00% execution success** vs. 92.00% for Mode 2 (+4.00 percentage points).
- **Latency Trade-Off**: Mode 4 incurred a **19.79% end-to-end latency overhead** (8,564.89 ms vs. 7,149.68 ms) due to vector embedding and FAISS similarity computation.
- **Relational Accuracy Ceiling**: Both Mode 4 and Mode 2 achieved exactly **68.00% relational semantic accuracy** (17/25 queries correct).

---

## 11. Memory Retrieval and Lifecycle Analysis

### 11.1 Remediation of Vector Geometry
Prior to unit-L2 normalization, unnormalized embeddings generated by `nomic-embed-text` had norms $\|\mathbf{v}\| \approx 19.8$, resulting in squared L2 distances $d^2 \approx 280$ and similarity scores $S = \frac{1}{1 + d^2} \approx 0.0035 \ll 0.50$. Consequently, the historical pre-remediation Phase 9 run recorded zero retrievals across all queries. Normalizing embeddings to unit L2 length restored the intended similarity geometry, yielding 16 retrieval events across 12 distinct queries ($48.0\%$ benchmark coverage).

### 11.2 Lifecycle Metrics and Deduplication
- **New Admissions**: Exactly 3 memories admitted across all runs:
  - `Q04`: Admitted join pattern for `dim_geography`.
  - `Q13`: Admitted multi-table join and aggregation pattern.
  - `Q15`: Admitted window aggregation structure.
- **Reinforcement & Deduplication on `Q17`**: Query `Q17` retrieved all 3 stored memories, applied `mem-Q13` during repair, and succeeded on Attempt 2. The governance engine reinforced `mem-Q13` and suppressed new admission.
- **Store Stability**: Store count remained strictly invariant at **3 memories** from Q15 through Q25 across all three runs, confirming that mutual exclusion prevented duplicate accumulation.

---

## 12. Safety Evaluation
Across all 450 post-remediation benchmark query evaluations (and 150 historical baseline evaluations), **zero destructive SQL statements reached the PostgreSQL warehouse**. 

In offline safety verification testing, when adversarial user requests (e.g., *"Delete all records from the sales table"*) were presented to the system, the AST validation layer intercepted the generated `DELETE` statement, classified the violation as `destructive_mutation`, halted the repair loop, and transitioned directly to `STATUS_BLOCKED`.

---

## 13. Semantic Failure Analysis

A central methodological finding is the substantial divergence between database execution success and relational semantic equivalence:

```
Table 2: Execution Success vs. Semantic Equivalence Discrepancy
========================================================================================================
Mode                                PostgreSQL Execution Success   Relational Semantic Accuracy   Gap
--------------------------------------------------------------------------------------------------------
Mode 1 (Zero-Shot)                  76.00%                         57.33%                         18.67%
Mode 2 (Stateless Self-Correction)  92.00%                         68.00%                         24.00%
Mode 3 (Naive Vector RAG)           92.00%                         68.00%                         24.00%
Mode 4 (Full ARMG)                  96.00%                         68.00%                         28.00%
========================================================================================================
```

### Analysis of the 7 Divergent Queries in Mode 4
Exactly seven queries executed cleanly against PostgreSQL (`is_success = True`) but failed relational semantic equivalence (`execution_accuracy = 0`) across all three seeds:
1. `Q05`: Omitted the `ORDER BY` clause, failing tuple sequence equivalence.
2. `Q14`: Omitted the `RANK()` window function, relying solely on `ORDER BY`.
3. `Q15`: Omitted cumulative window framing, computing simple monthly aggregations.
4. `Q17`: Included an invalid grouping attribute in the `LAG()` partition, generating multi-row monthly output.
5. `Q18`: Omitted `PARTITION BY category` in the `RANK()` function, ranking across the entire table.
6. `Q19`: Omitted the intermediate revenue column and `ROUND(..., 2)` formatting.
7. `Q25`: Inverted the column projection order (`market_type, profit, revenue`).

These failures demonstrate that operational memory cannot compensate for the model's fundamental semantic reasoning limitations on complex window framing and schema projection order.

---

## 14. Ablation Analysis

### 14.1 Negative Constraints Ablation (Mode 4 vs. Mode 5)
Removing negative constraints increased mean retries from 0.28 to 0.36. Query-level inspection reveals that this entire difference is localized to **Query `Q19`**:
- In Mode 4 (with negative constraints), the model avoided invalid grouping constructs and executed on Attempt 1 (`retries = 0`).
- In Mode 5 (without negative constraints), Attempt 1 repeated a known syntax error, requiring 2 repair retries (`retries = 2`).
- *Finding*: Negative constraints prevented repetitive syntax errors on `Q19`, but broad generalization across all queries was not demonstrated.

### 14.2 Temporal Decay Ablation (Mode 4 vs. Mode 6)
Mode 6 ($\lambda = 0.0$) exhibited identical final store sizes (3 memories) and retrieval counts (16 retrievals) to Mode 4. Because the 25 benchmark queries execute in continuous sequence within ~3.5 minutes ($\Delta t \approx 0.002$ days), exponential decay factor $\exp(-\lambda \Delta t) \approx 0.9999$ was insufficient to age memories.
- *Finding*: **Temporal decay effectiveness was NOT demonstrated by this benchmark**. Mode 6 functioned as a static no-decay control.

---

## 15. Discussion
The empirical results establish a clear architectural trade-off: ARMG successfully establishes a governed operational memory cycle that reduces repair loop overhead (−34.38% retries) and token consumption (−5.30%) while guaranteeing execution safety. However, this comes at the expense of additional vector search latency (+19.79%). Furthermore, operational memory did not improve relational semantic equivalence over stateless self-correction (both at 68.00%).

---

## 16. Limitations
1. **Model Parameter Scale**: Evaluated strictly with a local 7B model (`qwen2.5:7b-instruct`). Frontier models (70B+) may exhibit different baseline repair dynamics.
2. **Benchmark Scale**: The benchmark comprises 25 enterprise queries across a single Star Schema warehouse.
3. **Temporal Invariant**: The natural execution clock precluded evaluation of long-term utility decay and archival over multi-week intervals.
4. **Hardware Environment**: All evaluations were conducted on a single workstation environment.

---

## 17. Threats to Validity
- **Internal Validity**: The hardcoded greedy decoding (`temperature = 0.0`) and unpassed seed arguments mean that repeated runs evaluate deterministic pipeline stability rather than stochastic variance across random initializations.
- **Construct Validity**: While relational equivalence via bag/set comparison is substantially more rigorous than raw execution rate, slight variations in gold SQL aliases can flag semantically reasonable queries as incorrect.
- **External Validity**: Results on a Star Schema data warehouse with standard dimension-fact relationships may not generalize directly to highly normalized OLTP schemas or unstructured databases.

---

## 18. Future Work
1. Evaluation of ARMG on 70B-parameter open models and commercial API endpoints.
2. Evaluation under simulated multi-month epoch intervals to assess temporal decay and archival mechanics.
3. Integration of counterfactual ablation testing during repair to quantify the isolated causal weight of retrieved memory prompts.

---

## 19. Conclusion
This paper presented Adaptive Runtime Memory Governance (ARMG), an operational knowledge framework for local Text-to-SQL systems. Across 450 experimental evaluations, ARMG demonstrated verified retrieval restoration, mutual-exclusion duplicate suppression, 100% pre-execution safety, an observed 34.38% reduction in repair loop iterations, and a 5.30% reduction in token consumption compared to stateless self-correction. Simultaneously, the evaluation established that ARMG incurs a 19.79% latency overhead and does not overcome the baseline semantic accuracy plateau of 7B language models on complex window queries. ARMG provides a principled, governed operational memory architecture for enterprise Text-to-SQL systems prioritizing safety and repair efficiency.

---

## 20. References
- [REF-1]: Language Models for Text-to-SQL: A Comprehensive Survey.
- [REF-2]: In-Context Learning and Schema Pruning in Enterprise Relational Warehouses.
- [REF-3]: Self-Correction and Iterative Debugging in Code Generation Models.
- [REF-4]: Retrieval-Augmented Generation for Relational Databases.
- [REF-5]: Memory Architectures and Catastrophic Forgetting in Autonomous Agents.
- [REF-6]: AST Parsing and Deterministic Guardrails for Safe Database Interactions.
- [REF-7]: SQLGlot: High-Performance SQL Parser and Transpiler.
- [REF-8]: FAISS: Efficient Similarity Search and Clustering of Dense Vectors.
- [REF-9]: Benchmarking Text-to-SQL Systems: Relational Equivalence vs. Execution Match.
- [REF-10]: Qwen2.5 Technical Report: Advanced Foundation and Instruction Models.

---
