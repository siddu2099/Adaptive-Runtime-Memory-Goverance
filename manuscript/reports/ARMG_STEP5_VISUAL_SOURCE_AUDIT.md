# ARMG Step 5 Visual Source & Pre-Production Audit

**Document Role**: Forensic Pre-Production Audit of All Visual & Tabular Assets  
**Workflow Stage**: STEP 5 — Figure/Table Generation & Visual Integration  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md`  
**Frozen Evidence Package**: `manuscript/evidence_package.md`  
**Raw Benchmark Sources**: `benchmark/seed*/benchmark_results.csv`, `benchmark/pre_remediation_results.csv`  
**Date**: October 2026  
**Auditor**: Senior AI/ML Research Engineer & IEEE Technical Reviewer  

---

## 1. Audit Principles & Policy

1. **Zero Data Fabrication**: All plot coordinates, bar heights, distributions, and table cells must be bound to frozen evidence artifacts.
2. **Strict Metric Distinction**: Percentage points ($\text{pp}$) and relative percentages ($\%$) must never be conflated.
3. **Scientific Accuracy over Cosmetic Styling**: Plots must use publication-standard, clean, neutral styling using `matplotlib`. No seaborn, no 3D graphics, no chartjunk.
4. **Resolution of Ambiguities**: Any figure title or description in prior readiness notes that overstates findings (e.g., claiming universal memory poisoning prevention) is reconciled to empirical benchmark boundaries.

---

## 2. Pre-Production Audit for Figures (Figs. 1–6)

### Figure 1: End-to-End ARMG Architecture and Closed-Loop State Machine
- **Exact Source**: `graph/workflow.py:88-160`, Dossier Section 4.
- **Exact Nodes & Sequence**: Canonical 10-node StateGraph:
  1. `introspect_and_prune_node`
  2. `memory_retrieval_node`
  3. `sql_generator_node`
  4. `ast_guard_node`
  5. `postgres_executor_node`
  6. `observation_node`
  7. `diagnosis_node`
  8. `knowledge_node`
  9. `repair_prompt_node`
  10. `memory_governance_node`
- **Exact Intended Interpretation**: Illustrates the closed-loop runtime architecture. User question enters Node 1; Node 4 provides a deterministic pre-execution AST safety barrier blocking mutations; Node 5 executes on physical PostgreSQL; exceptions route through passive observation (Node 6), deterministic 7-tier diagnosis (Node 7), ephemeral knowledge formulation (Node 8), bounded repair assembly (Node 9, $K \le 3$) routing back to Node 3; terminal states route to Node 10 where algorithmic mutual exclusion enforces reinforcement vs. admission.
- **Potential Misleading Wording Resolved**: Explicitly confirmed that this is a 10-node architecture, not an outdated 9-node draft.
- **Visual Design**: High-contrast, clean vector diagram with clear decision branches, bounded repair loop, and terminal governance transitions.

### Figure 2: ARMG Runtime Memory Lifecycle State Transition Machine
- **Exact Source**: `memory/governance.py:23-339`, Dossier Section 11.
- **Exact States**: Six discrete lifecycle states: `NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`.
- **Exact Numerical Thresholds**:
  - Admission gating: $\text{Utility}_0 \ge 0.25$
  - Activation: Application during successful repair ($C_{t+1} \ge 0.50$)
  - Stabilization: $C_{t+1} \ge 0.80$
  - Failure penalty: $-15\%$ per failed repair
  - Archival: $C_{t+1} < 0.20$
  - Deletion: $C_{t+1} < 0.15$
  - Continuous decay: $\lambda = 0.05/\text{day}$ (annotated as mathematically implemented, unexercised under 3.5-min benchmark clock).
- **Exact Intended Interpretation**: Graph of operational memory state machine showing how memories evolve, stabilize, or get pruned.
- **Potential Misleading Wording Resolved**: Avoid inferring generic cognitive agent transitions; adhere strictly to `memory/governance.py`.

### Figure 3: Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry
- **Exact Source**: `benchmark/pre_remediation_results.csv` and `benchmark/seed42/benchmark_results.csv`, `manuscript/evidence_package.md` Section E.
- **Exact Values**:
  - Pre-remediation: Unnormalized embeddings ($\|\mathbf{v}\| \approx 19.8$), L2 squared distance $d^2 \approx 280$, similarity $S = \frac{1}{1 + d^2} \approx 0.0035 \ll \tau = 0.50$. Zero retrievals across all 25 queries ($0.0\%$).
  - Post-remediation: Unit-L2 normalized embeddings ($\|\mathbf{v}\| = 1.0$), L2 squared distance $d^2 \in [0, 4]$, similarity $S \ge 0.50$ breached. 16 retrieval events across 12 distinct queries ($48.0\%$ query coverage).
- **Exact Intended Interpretation**: Demonstrates the mathematical and empirical necessity of Unit-L2 normalization for Euclidean FAISS retrieval.
- **Potential Misleading Wording Resolved**: Does not claim normalization universally solves all vector stores; frames it as resolving the specific retrieval geometry breakdown in this system.

### Figure 4: PostgreSQL Execution Success vs. Relational Execution Accuracy Across Experimental Modes
- **Exact Source**: Table II / Table III; `manuscript/evidence_package.md` Section D.
- **Exact Values**:
  - Mode 1: ExecSucc = $76.00\%$, ExecAcc = $57.33\%$ (Gap = $18.67\text{ pp}$)
  - Mode 2: ExecSucc = $92.00\%$, ExecAcc = $68.00\%$ (Gap = $24.00\text{ pp}$)
  - Mode 3: ExecSucc = $92.00\%$, ExecAcc = $68.00\%$ (Gap = $24.00\text{ pp}$)
  - Mode 4: ExecSucc = $96.00\%$, ExecAcc = $68.00\%$ (Gap = $28.00\text{ pp}$)
  - Mode 5: ExecSucc = $96.00\%$, ExecAcc = $68.00\%$ (Gap = $28.00\text{ pp}$)
  - Mode 6: ExecSucc = $94.67\%$, ExecAcc = $68.00\%$ (Gap = $26.67\text{ pp}$)
- **Exact Intended Interpretation**: Visual evidence of the central paper thesis: physical execution success ($\text{ExecSucc}$) does not imply relational correctness ($\text{ExecAcc}$). Accuracy plateaus at 68.00% across Modes 2–6 despite execution success reaching 96.00%.
- **Potential Misleading Wording Resolved**: Chart includes ALL SIX MODES rather than restricting to Modes 1–4.

### Figure 5: Mode 2 vs. Full ARMG Operational Trade-Off Profile
- **Exact Source**: Table II and Table VIII; `manuscript/evidence_package.md` Section D.
- **Exact Values**:
  - Mean Retries: $0.43 \to 0.28$ ($-34.38\%$ relative reduction)
  - Mean Tokens: $572.72 \to 542.37$ ($-5.30\%$ relative reduction)
  - PostgreSQL Success: $92.00\% \to 96.00\%$ ($+4.00\text{ pp}$ execution increase)
  - End-to-End Latency: $7,149.68\text{ ms} \to 8,564.89\text{ ms}$ ($+19.79\%$ relative latency penalty)
  - Relational Accuracy: $68.00\% \to 68.00\%$ ($0.00\text{ pp}$ parity)
- **Exact Intended Interpretation**: Transparent multi-dimensional representation of ARMG's trade-off: trading wall-clock latency (+19.79%) for repair iteration efficiency (-34.38%), token economy (-5.30%), and execution recovery (+4.00 pp), while acknowledging relational semantic parity (68.00%).
- **Potential Misleading Wording Resolved**: Explicitly separates relative percentage changes ($\%$) from percentage-point changes ($\text{pp}$).

### Figure 6: Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG
- **Exact Source**: `benchmark/seed42/benchmark_results.csv` (and Seeds 123, 999), `final_store_size` progression across Q01–Q25.
- **Exact Values**:
  - Mode 4: Store size grows at Q04 (1), Q13 (2), Q15 (3). Sits strictly invariant at 3 memories from Q15 to Q25 due to mutual-exclusion deduplication.
  - Mode 3: Appends every successful execution, growing monotonically: Q01 (1) $\to$ Q02 (2) $\to$ Q03 (3) $\to$ Q05 (4) $\to \dots \to$ Q25 (23).
- **Exact Intended Interpretation**: Shows the empirical effect of algorithmic mutual exclusion preventing memory bloat during sequential query processing.
- **Potential Misleading Wording Resolved**: Bounded strictly to the evaluated sequential benchmark; avoids claiming universal memory poisoning elimination.

---

## 3. Pre-Production Audit for Tables (Tables I–IX)

| Table ID | Table Name | Source Files | Key Values / Dimensions | Verification Status |
| :---: | :--- | :--- | :--- | :---: |
| **Table I** | Canonical 7-Tier Exception Taxonomy | `agents/taxonomy.py`, `agents/error_diagnosis.py` | 7 tiers: Validation, Syntax, Semantic, Planning, Permission, Resource, Execution. | **VERIFIED (Code-locked)** |
| **Table II** | Comparative Empirical Benchmark Results | `manuscript/evidence_package.md` | 6 modes $\times$ 6 metrics with sample standard deviations over $n=3$ repeated runs. | **VERIFIED (Frozen)** |
| **Table III** | ExecSucc vs. ExecAcc Discrepancy Matrix | `manuscript/evidence_package.md`, Table II | All 6 modes; ExecSucc, ExecAcc, Gap in percentage points ($18.67\text{ pp} \to 28.00\text{ pp}$). | **VERIFIED (Frozen)** |
| **Table IV** | Canonical System Configuration | `graph/workflow.py`, environment specs | Qwen2.5 7B, Ollama, PostgreSQL 16.2, Nomic-Embed-Text 768d, FAISS CPU, LangGraph 0.2.x, Python 3.11.9. | **VERIFIED (Environment-locked)** |
| **Table V** | Star Schema Warehouse Specification | `db/schema.sql`, `scripts/seed_warehouse.py` | 4 tables: `dim_time` (365), `dim_geography` (50), `dim_product` (100), `fact_sales_performance` (2,000). | **VERIFIED (SQL-locked)** |
| **Table VI** | Benchmark Query Corpus Distribution | `benchmark/queries.json` | 25 queries: Cat A (6), Cat B (7), Cat C (8), Cat D (4). | **VERIFIED (JSON-locked)** |
| **Table VII** | Mathematical Governance Control Equations | `memory/governance.py` | 6 equations: Utility, Admission, Escalation, Penalty, Decay, Mutual Exclusion. Default parameters: $\alpha=0.10, \beta=0.15, \lambda=0.05, \theta=0.25$. | **VERIFIED (Math-locked)** |
| **Table VIII** | Mode 4 vs. Mode 2 Comparative Trade-Off | Table II, Dossier Section 16 | Retries ($-34.38\%$), Tokens ($-5.30\%$), PG Success ($+4.00\text{ pp}$), Latency ($+19.79\%$), Accuracy ($0.00\text{ pp}$). | **VERIFIED (Calculated)** |
| **Table IX** | Forensic Diagnostic of 7 Semantic Queries | `manuscript/evidence_package.md`, Section 13 | Q05, Q14, Q15, Q17, Q18, Q19, Q25. Detailed SQL failure mode and comparator rationale. | **VERIFIED (Trace-locked)** |

---

## 4. Production Release Approval

All source data, exact fields, and intended interpretations have been forensically verified. Asset generation can proceed with 100% adherence to publication integrity rules.
