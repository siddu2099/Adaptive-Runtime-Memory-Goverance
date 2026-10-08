# ARMG Step 4 Final Scientific Audit & Manuscript Freeze Report

**Workflow Stage**: STEP 4 — Final Scientific Audit, Step-3 Correction & Manuscript Freeze  
**Manuscript Target**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md`  
**Frozen Evidence Package**: `manuscript/evidence_package.md`  
**Date**: October 2026  
**Auditor**: Senior AI/ML Research Engineer & IEEE Technical Reviewer  
**Final Status**: **CONTENT-READY FOR FIGURE/TABLE GENERATION**  

---

## A. Step-3 Corrections Found

During the sentence-by-sentence forensic audit of the Step 3 outputs, the following issues were identified and corrected in `manuscript/ieee_manuscript.md` and associated documentation:

1. **Source Classification Refinement (Phase 1)**:
   - *Problem*: The Step 3 completion report coarsely classified sources into "22 peer-reviewed + 4 official technical", inadvertently grouping 3 unreviewed preprints under "peer-reviewed".
   - *Correction*: Audited each reference individually. Established the exact, defensible distribution: **19 peer-reviewed publications** (14 conference, 4 journal, 1 demonstration), **3 scholarly preprints** (MemGPT [8], GCG Universal Attacks [21], Execution-Guided Decoding [25]), **2 official technical reports** (Qwen2.5 [3], Nomic Embed [18]), and **2 official software specifications** (SQLGlot [10], LangGraph [22]).
2. **RAG Scope Overgeneralization (Problem A)**:
   - *Problem*: Section 1 (Item 2) and Section 2.2 previously asserted that "standard RAG" universally stores raw executed queries unconditionally, inappropriately generalizing the benchmark's Mode 3 (Naive Vector RAG) behavior to the entire retrieval-augmented generation literature (Lewis et al. [6]).
   - *Correction*: Rewrote both passages to evidence-safe phrasing: *"Naive implementations of retrieval augmentation [6] that append historical execution exemplars without explicit lifecycle governance risk accumulating duplicate, conflicting, or stale entries over time [7], [8]."*
3. **Existing Memory System Scope (Problem B)**:
   - *Problem*: Section 2.2 contained a universal negative assertion: *"existing memory-augmented frameworks do not address the specific requirements of database operational execution."*
   - *Correction*: Rewrote to contrast domain scopes rather than asserting universal absence: *"While these memory-augmented frameworks establish foundational principles for agent behavior, they focus primarily on conversational dialogue or general decision tasks rather than the operational constraints of database execution."*
4. **Model-Scale Literature & Causal Window Ceiling (Problem C)**:
   - *Problem*: Section 13 root-cause analysis previously stated that *"in light of foundational research on emergent reasoning capabilities in large language models [26], these findings establish that operational memory cannot compensate for the base model's fundamental semantic reasoning limitations on nested analytic SQL."* This inappropriately used Wei et al. [26] as causal proof of the ARMG benchmark failure.
   - *Correction*: Rewrote per Phase 3 guidelines: *"In the evaluated Qwen2.5 7B configuration, relational execution accuracy plateaued at 68.00%, with remaining failures concentrated in complex analytical window constructs (4 queries) and projection/ordering specifications (3 queries). Existing model-scaling literature provides broader context on capability variation and emergent reasoning with model scale [26], but the present benchmark does not causally isolate model size. Rather, the empirical results demonstrate that within the evaluated 7B setting, operational memory provides syntactic and error-avoidance guidance without elevating the model's baseline semantic reasoning capacity on nested window operations."*
5. **Safety Terminology Containment (Problem D)**:
   - *Problem*: Section 15.1 contained the phrase *"provably blocked all tested destructive statements"*, violating the ban on proof and absolute safety terms.
   - *Correction*: Replaced with bounded empirical language: *"Pre-execution AST containment successfully intercepted all tested destructive statements across unit and benchmark evaluations."*
6. **Memory Deduplication Framing (Problem E)**:
   - *Problem*: Section 1 and Section 15.1 implied that ARMG universally eliminates duplicate memory problems.
   - *Correction*: Explicitly bounded deduplication to the evaluated benchmark lifecycle: *"In the evaluated sequential workflow, algorithmic mutual exclusion maintained store size invariant at 3 memories, preventing the duplicate accumulation observed in unmanaged RAG (which expanded to 23 entries)."*

---

## B. Technical Audit

- **Taxonomy Verification**: Confirmed exact 7-tier exception taxonomy (`Validation`, `Syntax`, `Semantic`, `Planning`, `Permission`, `Resource`, `Execution`) matching `agents/taxonomy.py` and Dossier Section 9. Table I verified. Zero references to discarded 5-class formulation.
- **Architecture Verification**: Confirmed 10-node directed execution state graph in canonical topological order matching `graph/workflow.py` and Dossier Section 4: (1) `introspect_and_prune_node`, (2) `memory_retrieval_node`, (3) `sql_generator_node`, (4) `ast_guard_node`, (5) `postgres_executor_node`, (6) `observation_node`, (7) `diagnosis_node`, (8) `knowledge_node`, (9) `repair_prompt_node`, (10) `memory_governance_node`. LangGraph [22] cited.
- **Governance Equations**: Confirmed all 6 mathematical governance control equations in Section 6 matching `memory/governance.py`:
  - Operational utility: $\text{Utility} = C \times \text{SuccessRate} \times \text{ContextSimilarity} \times \text{Recency}$
  - Admission gating: $\text{Utility}_0 \ge \theta_{\text{admit}} = 0.25$
  - Asymptotic escalation: $C_{t+1} = C_t + \alpha (1.0 - C_t)$ with $\alpha = 0.10$
  - Multiplicative failure penalty: $C_{t+1} = \max(0, C_t(1 - \beta))$ with $\beta = 0.15$
  - Continuous exponential decay: $C(t) = C_{\text{ref}} \exp(-\lambda \Delta t)$ with $\lambda = 0.05/\text{day}$, annotated as *Mathematically Implemented & Unit-Tested; Experimentally Unexercised in Benchmark*.
  - Algorithmic mutual exclusion: $\text{Reinforce}(M)$ if applied; $\text{Admit}(K)$ only if no memory applied, execution succeeded, and retries $>0$.
- **Repair Budget**: Maximum retry budget $K_{\text{max}} = 3$ (total attempts $\le 4$). Verified in Section 4, 5.2, 9.2.
- **Safety Enforcement**: Confirmed pre-execution AST validation via SQLGlot [10] inspecting root AST nodes (`Drop`, `Delete`, `Update`, `Insert`, `Create`, `Alter`, `TruncateTable`, etc.), administrative syntax (`GRANT`, `REVOKE`, `EXEC`), and statement count $>1$, routing directly to `STATUS_BLOCKED`. Verified across 18 unit tests and 600 total evaluated runs. Zero destructive mutations reached PostgreSQL.
- **Metrics Separation**: Confirmed rigorous and consistent separation of PostgreSQL execution success ($\text{ExecSucc}$) from relational execution accuracy ($\text{ExecAcc}$). Formalized $\text{ExecSucc} = 1 \centernot\implies \text{ExecAcc} = 1$ in Section 3.3.
- **Experimental Protocol**: Confirmed synthetic Star Schema warehouse (2,000 fact records, 4 tables, seeded via NumPy `seed=42`), 25 queries, greedy decoding (`temperature = 0.0`), and $n = 3$ repeated runs (Seeds 42, 123, 999) measuring pipeline reproducibility and memory-state stability.
- **Relational Comparator & Semantic Failure Audit**: Confirmed comparator rules in `benchmark/equivalence.py`. Reconciled all 7 divergent queries (Q05, Q14, Q15, Q17, Q18, Q19, Q25). Explicitly verified that Q05 failure is comparator-specific (gold query specified `ORDER BY`, triggering strict positional matching) rather than an assertion that unordered SQL is inherently buggy.

---

## C. Numerical Audit

Every numerical value in `manuscript/ieee_manuscript.md` was cross-checked against `manuscript/evidence_package.md` and raw CSV logs:

| Metric / Parameter | Frozen Evidence Package | Manuscript Value | Audit Status |
| :--- | :---: | :---: | :---: |
| **Mode 1 ExecAcc** | $57.33\% \pm 2.31\%$ | $57.33\% \pm 2.31\%$ | **MATCH (100%)** |
| **Mode 1 PG Success** | $76.00\% \pm 0.00\%$ | $76.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 1 Retries** | $0.00 \pm 0.00$ | $0.00 \pm 0.00$ | **MATCH (100%)** |
| **Mode 1 Latency** | $5,087.73 \pm 210.33\text{ ms}$ | $5,087.73 \pm 210.33\text{ ms}$ | **MATCH (100%)** |
| **Mode 1 Tokens** | $360.48 \pm 0.48$ | $360.48 \pm 0.48$ | **MATCH (100%)** |
| **Mode 1 Store Size** | $0$ | $0$ | **MATCH (100%)** |
| **Mode 2 ExecAcc** | $68.00\% \pm 0.00\%$ | $68.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 2 PG Success** | $92.00\% \pm 0.00\%$ | $92.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 2 Retries** | $0.43 \pm 0.02$ | $0.43 \pm 0.02$ | **MATCH (100%)** |
| **Mode 2 Latency** | $7,149.68 \pm 231.65\text{ ms}$ | $7,149.68 \pm 231.65\text{ ms}$ | **MATCH (100%)** |
| **Mode 2 Tokens** | $572.72 \pm 12.68$ | $572.72 \pm 12.68$ | **MATCH (100%)** |
| **Mode 2 Store Size** | $0$ | $0$ | **MATCH (100%)** |
| **Mode 3 ExecAcc** | $68.00\% \pm 0.00\%$ | $68.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 3 PG Success** | $92.00\% \pm 0.00\%$ | $92.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 3 Retries** | $0.00 \pm 0.00$ | $0.00 \pm 0.00$ | **MATCH (100%)** |
| **Mode 3 Latency** | $6,844.01 \pm 56.90\text{ ms}$ | $6,844.01 \pm 56.90\text{ ms}$ | **MATCH (100%)** |
| **Mode 3 Tokens** | $558.28 \pm 0.00$ | $558.28 \pm 0.00$ | **MATCH (100%)** |
| **Mode 3 Store Size** | $23$ | $23$ | **MATCH (100%)** |
| **Mode 4 ExecAcc** | $68.00\% \pm 0.00\%$ | $68.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 4 PG Success** | $96.00\% \pm 0.00\%$ | $96.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 4 Retries** | $0.28 \pm 0.00$ | $0.28 \pm 0.00$ | **MATCH (100%)** |
| **Mode 4 Latency** | $8,564.89 \pm 103.16\text{ ms}$ | $8,564.89 \pm 103.16\text{ ms}$ | **MATCH (100%)** |
| **Mode 4 Tokens** | $542.37 \pm 0.02$ | $542.37 \pm 0.02$ | **MATCH (100%)** |
| **Mode 4 Store Size** | $3$ | $3$ | **MATCH (100%)** |
| **Mode 5 ExecAcc** | $68.00\% \pm 0.00\%$ | $68.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 5 PG Success** | $96.00\% \pm 0.00\%$ | $96.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 5 Retries** | $0.36 \pm 0.00$ | $0.36 \pm 0.00$ | **MATCH (100%)** |
| **Mode 5 Latency** | $8,941.28 \pm 108.68\text{ ms}$ | $8,941.28 \pm 108.68\text{ ms}$ | **MATCH (100%)** |
| **Mode 5 Tokens** | $553.93 \pm 0.02$ | $553.93 \pm 0.02$ | **MATCH (100%)** |
| **Mode 5 Store Size** | $3$ | $3$ | **MATCH (100%)** |
| **Mode 6 ExecAcc** | $68.00\% \pm 0.00\%$ | $68.00\% \pm 0.00\%$ | **MATCH (100%)** |
| **Mode 6 PG Success** | $94.67\% \pm 2.31\%$ | $94.67\% \pm 2.31\%$ | **MATCH (100%)** |
| **Mode 6 Retries** | $0.37 \pm 0.02$ | $0.37 \pm 0.02$ | **MATCH (100%)** |
| **Mode 6 Latency** | $9,036.97 \pm 178.55\text{ ms}$ | $9,036.97 \pm 178.55\text{ ms}$ | **MATCH (100%)** |
| **Mode 6 Tokens** | $599.67 \pm 13.94$ | $599.67 \pm 13.94$ | **MATCH (100%)** |
| **Mode 6 Store Size** | $3$ | $3$ | **MATCH (100%)** |
| **Retry Reduction Delta** | $-34.38\%$ | $-34.38\%$ | **MATCH (100%)** |
| **Token Reduction Delta** | $-5.30\%$ | $-5.30\%$ | **MATCH (100%)** |
| **PG Success Delta** | $+4.00\text{ pp}$ | $+4.00\text{ pp}$ | **MATCH (100%)** |
| **Latency Penalty Delta** | $+19.79\%$ | $+19.79\%$ | **MATCH (100%)** |
| **Relational Accuracy Delta**| $0.00\text{ pp}$ | $0.00\text{ pp}$ | **MATCH (100%)** |

- **Numerical Mismatches Found**: **ZERO (0)**.
- **Numerical Mismatches Corrected**: **ZERO (0)**.
- **Numerical Mismatches Remaining**: **ZERO (0)**.

---

## D. Literature Audit

- **Total References in Bibliography**: **26**
- **Peer-Reviewed Publications**: **19**
  - Peer-reviewed conference papers: 14 ([1], [4], [5], [6], [7], [11], [12], [13], [14], [15], [16], [20], [23], [24])
  - Peer-reviewed journal papers: 4 ([2] PVLDB, [17] IEEE TBD, [19] TMLR, [26] TMLR)
  - Peer-reviewed system demonstrations: 1 ([9] EMNLP 2023 System Demos)
- **Scholarly Preprints (arXiv)**: **3** ([8] MemGPT, [21] Universal Attacks / GCG, [25] Execution-Guided Decoding)
- **Official Technical Reports**: **2** ([3] Qwen2.5 Technical Report, [18] Nomic Embed Technical Report)
- **Official Software Documentation / Specifications**: **2** ([10] SQLGlot, [22] LangGraph)
- **Unsupported Citation Claims**: **ZERO (0)**.
- **Unresolved Literature Issues**: **ZERO (0)**.

---

## E. Manuscript Risk Analysis

| Risk Tier | Risk Item | Description & Strategic Handling |
| :--- | :--- | :--- |
| **HIGH RISKS** | 1. 68.00% Relational Accuracy Plateau | Disclosed prominently in Abstract, Tables II & III, and Section 15.2; framed as demonstrating that operational memory provides syntactic/repair guidance without overcoming the 7B model's intrinsic window-function reasoning limits. |
| | 2. Benchmark Corpus Scale (25 queries) | Explicitly acknowledged as Limitation 2 and External Validity threat; defended as a controlled testbed isolating multi-turn memory lifecycle and deduplication. |
| | 3. Single 7B Foundation Model | Scoped explicitly to on-premises localized deployments on commodity workstations; 70B+ model evaluation cataloged as Future Work. |
| | 4. Unexercised Continuous Decay | Disclosed in Abstract, Section 6.5, Section 14.2, and Limitation 6; Mode 6 verified as a static control. |
| | 5. Absence of Spider / BIRD Evaluation | Differentiated benchmark paradigms in Section 9.1: Spider/BIRD evaluate cross-database zero-shot generalization; ARMG evaluates multi-turn memory lifecycle in a persistent warehouse. |
| **MEDIUM RISKS** | 6. Latency Overhead (+19.79%) | Transparently reported in Abstract, Table II, Section 10.2, and Section 15.3; defended as an architectural trade-off prioritizing repair efficiency, token economy, and AST safety over raw speed. |
| | 7. Lack of Causal Memory Intervention | Framed strictly as an observational association in Section 10.3 and 15.4; dynamic memory masking cataloged as Priority 0 Future Work. |
| | 8. Synthetic Star Schema Testbed | Framed as a controlled data warehouse environment with verified ground truth; multi-schema testing cataloged as Future Work. |
| | 9. Small Sample Size ($n = 3$) | Framed strictly as repeated runs assessing pipeline reproducibility under greedy decoding; all inferential $p$-value claims eliminated. |
| | 10. Pre-Execution Safety Scope | Bounded to deterministic syntactic containment of implemented prohibited statements; "absolute security" eliminated. |
| | 11. Novelty & System Integration | Positioned as an integrated architectural and systems contribution; unsupported "first-ever" claims eliminated. |
| **LOW RISKS** | 12. Greedy Decoding | Justified as necessary for reproducible enterprise querying and eliminating random sampling confounding. |
| | 13. Executable vs Relational Correctness | Formulated as a key methodological contribution warning the community against conflating execution with correctness. |
| | 14. Literature Overclaiming | Fully audited and eliminated in Step 4 Phase 2. |
| | 15. Bibliographic Classification | Fully reconciled to strict publication taxonomy in Step 4 Phase 1. |

---

## F. New Experiments

- **Experiments Performed in Step 4**: **MUST = NONE (0)**.
- **Experiments Recommended for Future Work** (Cataloged in `ARMG_IEEE_Experiment_Gap_Register.md`):
  1. *Synthetic Epoch Advance Decay Experiment* (Priority 0 — Recommended for journal extension)
  2. *Counterfactual Dynamic Memory Masking* (Priority 0 — Recommended for journal extension)
  3. *70B+ Frontier Model Scale Evaluation* (Priority 1)
  4. *Cross-Domain Public Benchmarks (Spider & BIRD)* (Priority 1)
  5. *Concurrent Multi-User Workload & Throughput Testing* (Priority 2)
  6. *Multi-Schema Enterprise Warehouse Evaluation* (Priority 2)

---

## G. Protected Artifact Integrity Verification

| Protected Artifact | Modification Permitted? | Actually Modified? | Integrity Status |
| :--- | :---: | :---: | :---: |
| `ARMG_IEEE_Paper_Revision_Dossier.md` | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |
| `manuscript/evidence_package.md` | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |
| `benchmark/seed*/benchmark_results.csv` | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |
| Repository Source Implementation (`*.py`) | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |
| Experimental Numbers / Tables | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |
| Mathematical Governance Equations | **NO** | **NO** | **UNTOUCHED (100% PRESERVED)** |

---

## H. Final Manuscript Freeze Status

### **CONTENT-READY FOR FIGURE/TABLE GENERATION**

- **Zero Scientific Blockers Remaining**: All technical, numerical, literature, statistical, and safety claims have been forensically verified and brought into 100% alignment with the canonical technical dossier and frozen evidence package.
- **Frozen Manuscript State**: [`manuscript/ieee_manuscript.md`](file:///C:/Users/siddu/Pictures/armg%20main/manuscript/ieee_manuscript.md) is now officially frozen in content.
- **Handoff to Step 5**: The manuscript is ready for visual asset generation (rendering Figures 1–6), final tabular typesetting (formatting Tables I–IX), and IEEE formatting (LaTeX/IEEEtran or IEEE Word template).

---

STEP 4 COMPLETE — MANUSCRIPT CONTENT AUDITED
