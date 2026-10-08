# ARMG IEEE Revision Change Log

**Target File Modified**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md`  
**Frozen Evidence Package**: `manuscript/evidence_package.md`  
**Date of Revision**: October 2026  
**Auditor & Reviser**: Senior AI/ML Research Engineer & IEEE Technical Reviewer  

---

## 1. Revision Overview

This document provides a comprehensive, structured record of every substantive revision made to `manuscript/ieee_manuscript.md` during Step 2 and Step 3 of the ARMG IEEE revision workflow. All modifications were executed to enforce strict alignment with the canonical technical dossier (`ARMG_IEEE_Paper_Revision_Dossier.md`), the repository implementation (`C:\Users\siddu\Pictures\armg main\`), and the frozen experimental benchmark evidence (`manuscript/evidence_package.md`).

---

## 2. Substantive Change Log Table (Step 2 Forensic Corrections)

| Section | Original Problem in Draft | Change Made in Revised Manuscript | Methodological Rationale | Evidence Source |
| :--- | :--- | :--- | :--- | :--- |
| **Title & Subtitle** | Contained single proposal without clear technical focus on closed-loop governance. | Added recommended IEEE technical title: *Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*. | Emphasizes the operational, repair, and safety contributions over generalized accuracy claims. | Dossier Section 2 |
| **Abstract** | Implied live enterprise data; lacked explicit mention of the 68.00% relational semantic accuracy plateau and +19.79% latency overhead; claimed "100% pre-execution safety" without qualification. | Rewrote abstract completely: (1) qualified dataset as a synthetic enterprise-style Star Schema, (2) specified $n=3$ repeated runs evaluating pipeline reproducibility under greedy decoding, (3) reported 34.38% retry reduction, 5.30% token reduction, and 96% vs 92% PG success, (4) transparently reported +19.79% latency penalty and 68.00% accuracy plateau, (5) qualified temporal decay as experimentally unexercised. | Conforms to IEEE TKDE/ICDE standards requiring balanced reporting of trade-offs and honest representation of experimental scope. | Dossier Sections 2, 13, 15, 16, 22 |
| **Section 1 (Introduction)** | Pervasive promotional phrasing; implied 450 independent random trials; vague discussion of contributions. | (1) Formalized four acute operational challenges of local 7B models. (2) Clarified evaluation protocol ($n=3$ repeated runs, 450 total query runs, greedy decoding). (3) Added five structured, defensible research contributions (Architectural, Knowledge, Governance, Safety, Empirical). | Separates factual engineering contributions from unproven generalizations; prevents misleading statistical claims. | Dossier Sections 3, 13, 21 |
| **Section 2 (Related Work)** | Contained generic, unsourced claims with untracked `[REF]` placeholders. | Reorganized into three focused sub-domains (2.1 Text-to-SQL & Self-Correction, 2.2 Memory Systems & Vector RAG, 2.3 Database Safety) and mapped all citations to `ARMG_Literature_Gaps.md`. | Maintains academic rigor without inventing hallucinated citations. | Dossier Section 30; `ARMG_Literature_Gaps.md` |
| **Section 3 (Problem Formulation)** | Incomplete mathematical formalization; lacked explicit pre-execution AST validation operator; conflated execution success and relational accuracy. | (1) Added formal definitions for $\mathcal{S} = (\mathcal{T}, \mathcal{C}, \mathcal{R})$, generator $\mathcal{G}_{\theta}$, AST validator $\mathcal{V}_{\text{AST}}(s_k)$, execution environment $\mathcal{E}(s_k)$, and bounded repair agent $\mathcal{R}_{\theta}$. (2) Rigorously defined and contrasted $\text{ExecSucc}$ and $\text{ExecAcc}$, establishing that $\text{ExecSucc} = 1 \centernot\implies \text{ExecAcc} = 1$. | Eliminates metric confusion; establishes formal relational algebra baseline. | Dossier Section 3; `benchmark/equivalence.py` |
| **Section 4 (Architecture)** | Claimed a 9-stage architecture, omitting the passive observation node. | Updated to the canonical 10-node StateGraph specification matching `graph/workflow.py`, detailing the exact functional role and routing of each node. | Accurately reflects the LangGraph implementation in the codebase. | Dossier Section 4; `graph/workflow.py` |
| **Section 5 (Error Diagnosis)** | **CRITICAL DEFECT**: Claimed a 5-class taxonomy (`SYNTAX_ERROR`, `SCHEMA_VIOLATION`, `JOIN_ERROR`, `TYPE_MISMATCH`, `SEMANTIC_LOGIC`). Direct contradiction with source code. | **Completely replaced 5-class formulation** with the canonical 7-tier exception taxonomy (`Validation`, `Syntax`, `Semantic`, `Planning`, `Permission`, `Resource`, `Execution`) from `agents/taxonomy.py`. Added Table I detailing precedence tiers, regex detection patterns, and candidate resolution heuristics. | Restores factual truth between manuscript and repository code. | Dossier Section 9; `agents/taxonomy.py`; `agents/error_diagnosis.py` |
| **Section 5 (Knowledge Representation)** | Used inaccurate field names (`error_type`) and omitted candidate replacements. | Updated `RuntimeKnowledge` field definitions to match Pydantic model in `memory/models.py` (`failure_type`, `candidate_replacements`), explaining how volatile metadata is stripped during embedding formatting. | Ensures code-level fidelity. | Dossier Section 10; `memory/models.py` |
| **Section 6 (Memory Governance)** | Admission threshold stated as $\tau_{\text{admit}} = 0.50$; confidence escalation formula inaccurate; temporal decay presented as empirically validated. | (1) Corrected admission formula to $\text{Utility}_0 \ge \theta_{\text{admit}} = 0.25$ per `memory/governance.py`. (2) Aligned confidence escalation ($C_{t+1} = C_t + \alpha(1-C_t)$) and penalty equations with code. (3) Explicitly annotated temporal decay equation as "Mathematically Implemented & Unit-Tested; Experimentally Unexercised in Benchmark". (4) Formalized mutual exclusion invariant. | Replaces inaccurate mathematical equations with verified code implementations; eliminates false empirical decay claims. | Dossier Section 11; `memory/governance.py` |
| **Section 8 (Safety Enforcement)** | Claimed "guarantee safety in production data environments" and "universal security." | Replaced with evidence-bounded phrasing: "enforces strict pre-execution containment against destructive mutations." Detailed SQLGlot AST parsing, expression traversal, and immediate transition to `STATUS_BLOCKED`. | Distinguishes implemented safety mechanisms from unproven universal security guarantees. | Dossier Section 12 & 22; `validation/execution_validator.py` |
| **Section 9 (Experimental Setup)** | Vaguely described data as "enterprise warehouse"; did not explain greedy decoding implications for multi-seed runs. | (1) Specified synthetically seeded Star Schema (NumPy `seed=42`, 2,000 fact rows, 4 tables). (2) Documented greedy decoding (`temperature = 0.0`) and clarified that Seeds 42, 123, 999 evaluate pipeline reproducibility and state consistency ($n=3$ repeated runs), not stochastic model sampling. (3) Detailed comparator rules from `benchmark/equivalence.py`. | Accurately characterizes dataset nature and prevents invalid statistical inferences. | Dossier Section 6, 8, 13, 14; `scripts/seed_warehouse.py` |
| **Section 10 (Results)** | Table 1 omitted memory lifecycle metrics (store size, admissions, reinforcements). | Expanded Table II to include final store size across all six modes. Detailed Mode 4 vs Mode 2 deltas: −34.38% retries, −5.30% tokens, +4.00 pp PG success, +19.79% latency overhead, and 68.00% relational accuracy parity. | Provides complete, multi-dimensional view of experimental results matching the frozen evidence package. | Dossier Section 15 & 16; `manuscript/evidence_package.md` |
| **Section 10 (Query Divergence)** | Did not detail query-level differences between Mode 2 and Mode 4. | Added explicit query-level analysis detailing the two queries that differed (Q08 retry reduction, Q19 execution recovery) and the 23 queries that exhibited identical outcomes. | Demonstrates exactly where operational memory impacted execution and where it did not. | Dossier Section 16; `benchmark/seed*/benchmark_results.csv` |
| **Section 11 (Memory Retrieval)** | Did not fully contrast Mode 4 store size with Naive RAG bloat. | Explicitly highlighted that Mode 4 store size remained invariant at 3 memories from Q15 to Q25 due to mutual exclusion, whereas Mode 3 accumulated 23 unmanaged entries. | Provides concrete evidence of memory deduplication and lifecycle governance in action. | Dossier Section 18 |
| **Section 12 (Safety Evaluation)** | Stated "100% safety" without specifying evaluation scope. | Bounded safety evidence to 450 post-remediation + 150 baseline evaluations (600 total runs) and 18 unit tests in `tests/unit/test_safety_guard.py`. Post-run checksums confirmed zero data modification. | Provides verifiable, evidence-scoped safety reporting. | Dossier Section 20 |
| **Section 13 (Semantic Failure Analysis)** | Did not accurately explain why Q05 failed relational equivalence. | Clarified that Q05 executed cleanly on PostgreSQL but omitted `ORDER BY`; because the gold query specified ordering, the comparator enforced strict positional matching and rejected the unordered set. Categorized all 7 divergent queries into window reasoning failures (4), projection/ordering omissions (2), and projection permutation (1). | Provides technically precise database semantics; eliminates false impression that unordered SQL is inherently buggy. | Dossier Section 14 & 19; `benchmark/equivalence.py` |
| **Section 14 (Ablations)** | Implied negative constraints broadly improve repair across all queries; claimed temporal decay ablation was meaningful. | (1) Localized negative constraint retry reduction strictly to Query Q19, stating broad generalization was not demonstrated. (2) Explicitly stated that temporal decay effectiveness was NOT demonstrated by the benchmark due to the ~3.5-minute execution clock ($\Delta t \approx 0.002$ days). | Retracts overgeneralized claims; truthfully reports ablation limitations. | Dossier Section 17 |
| **Section 15 (Discussion)** | Brief, promotional paragraph. | Completely restructured into four balanced subsections: (15.1) What Improved, (15.2) What Did Not Improve (68% plateau), (15.3) Architectural Cost (+19.79% latency), (15.4) What Remains Untested. | Establishes a mature, objective engineering evaluation suitable for IEEE Transactions. | Dossier Section 22 & 33 |
| **Section 16 (Limitations)** | Incomplete list of 4 limitations. | Expanded to 9 canonical limitations matching Dossier Section 24 (model scale, benchmark scale, synthetic data, greedy decoding, $n=3$ sample size, unexercised decay, lack of public benchmarks, lack of counterfactual testing, single-user load). | Provides comprehensive disclosure of methodological constraints. | Dossier Section 24 |
| **Section 17 (Threats to Validity)** | Omitted statistical validity. | Added explicit Statistical Validity subsection explaining that $n=3$ repeated runs over 25 queries preclude inferential $p$-value hypothesis testing, requiring all results to be interpreted as descriptive empirical effect sizes. Expanded internal, construct, and external validity. | Enforces statistical rigor and prevents reviewer critique regarding sample size. | Dossier Section 25 |
| **Section 18 (Future Work)** | Unprioritized list of items. | Structured future work into prioritized research extensions: Priority 0 (Synthetic epoch decay experiments, counterfactual memory masking), Priority 1 (70B frontier models, Spider/BIRD benchmarks), Priority 2 (concurrent multi-user throughput). | Guides high-impact follow-up research. | Dossier Section 26 |
| **Section 19 (Conclusion)** | Overstated safety and omitted latency penalty. | Balanced conclusion reporting verified operational gains (retries, tokens, safety, deduplication) alongside operational costs (+19.79% latency) and the 68% semantic plateau. | Proportional, evidence-aligned concluding statement. | Dossier Section 21 & 33 |

---

## 3. Verification of Canonical Consistency (Step 2 Baseline)

Following the initial rewrite of `manuscript/ieee_manuscript.md`, the manuscript was verified against all 20 Phase 15 criteria:
1. **Taxonomy**: 7-tier taxonomy (`Validation`, `Syntax`, `Semantic`, `Planning`, `Permission`, `Resource`, `Execution`) is enforced; 5-class taxonomy completely eliminated.
2. **Dataset**: Explicitly described as a synthetic enterprise-style Star Schema benchmark (`seed=42`, 2,000 fact rows, 4 tables).
3. **Safety**: Bounded to verified pre-execution AST containment across 600 evaluated runs and 18 unit tests; "universal security" claims removed.
4. **Multi-Seed Protocol**: Described as three repeated benchmark executions assessing pipeline reproducibility and state stability under greedy decoding (`temp=0.0`), not stochastic sampling distributions.
5. **Sample Size**: Clearly framed as $n=3$ repeated executions across 25 queries.
6. **Semantic Accuracy**: Transparently reports that relational execution accuracy plateaued at 68.00% across both Mode 2 and Mode 4.
7. **Latency Overhead**: Prominently reports +19.79% end-to-end latency penalty (8,564.89 ms vs. 7,149.68 ms) in Abstract, Results, and Discussion.
8. **Negative Constraints**: Retry reduction between Mode 4 and Mode 5 explicitly localized to Query Q19.
9. **Temporal Decay**: Clearly identified as mathematically implemented and unit-tested, but unexercised under the benchmark execution clock.
10. **Memory Deduplication**: Mutual-exclusion deduplication verified: Mode 4 invariant at 3 memories vs. Mode 3 accumulating 23 entries.
11. **Q05 Ordering Semantics**: Correctly explains that gold SQL specified `ORDER BY`, triggering strict positional matching failure.
12. **Zero Fabricated Citations**: Literature requirements mapped to `ARMG_Literature_Gaps.md` without fabricating authors or venues.

---

## 4. STEP 3 — Literature Research & Citation Integration

### 4.1 Citations Added
- **Foundational Text-to-SQL**: Added Pourreza & Rafiei (DIN-SQL, NeurIPS 2023) `[1]`, Gao et al. (DAIL-SQL, PVLDB 2024) `[2]`, Wang et al. (MAC-SQL, COLING 2025) `[14]`, and Wang et al. (Execution-Guided Decoding, 2018) `[25]`.
- **LLM Foundation & Scale**: Added Qwen Team (Qwen2.5 Technical Report, 2024) `[3]` and Wei et al. (Emergent Abilities of Large Language Models, TMLR 2022) `[26]`.
- **Self-Correction & Program Repair**: Added Madaan et al. (Self-Refine, NeurIPS 2023) `[4]`, Shinn et al. (Reflexion, NeurIPS 2023) `[5]`, Chen et al. (Self-Debug, ICLR 2024) `[15]`, and Zhang et al. (Self-Edit, ACL 2023) `[16]`.
- **Retrieval & Dense Embeddings**: Added Lewis et al. (RAG, NeurIPS 2020) `[6]`, Johnson et al. (FAISS, IEEE TBD 2021) `[17]`, and Nussbaum et al. (Nomic Embed, 2024) `[18]`.
- **Agent Memory Architectures**: Added Park et al. (Generative Agents, ACM UIST 2023) `[7]`, Packer et al. (MemGPT, 2023) `[8]`, and Sumers et al. (CoALA, TMLR 2024) `[19]`.
- **SQL & LLM Safety**: Added Rebedea et al. (NeMo Guardrails, EMNLP 2023) `[9]`, Mao (SQLGlot, 2023) `[10]`, Halfond & Orso (AMNESIA, IEEE/ACM ASE 2005) `[11]`, Wei et al. (Jailbroken, NeurIPS 2023) `[20]`, and Zou et al. (Universal Adversarial Attacks, 2023) `[21]`.
- **Evaluation & Benchmarks**: Added Finegan-Dollak et al. (ACL 2018) `[12]`, Zhong et al. (EMNLP 2020) `[13]`, Yu et al. (Spider, EMNLP 2018) `[23]`, and Li et al. (BIRD, NeurIPS 2023) `[24]`.
- **Workflow Orchestration**: Added LangChain (LangGraph Documentation, 2024) `[22]`.

### 4.2 Citations Replaced
- Replaced informal or unverified placeholders `[REF-1]` through `[REF-15]` with permanently assigned, peer-reviewed numbered citations `[1]` through `[26]`.
- Replaced potential unverified web references for agent memory with formal peer-reviewed literature (Park et al., UIST '23 `[7]`; Packer et al., 2023 `[8]`; Sumers et al., TMLR 2024 `[19]`).
- Replaced commercial firewall references with foundational AST-based program analysis literature (Halfond & Orso, ASE '05 `[11]`).

### 4.3 Claims Rewritten
- **Safety Framing**: Rewrote all "absolute safety", "universal security", and "guaranteed database protection" claims to "verified pre-execution AST containment for prohibited mutation and administrative syntax implemented by the system" (`[9]`, `[10]`, `[11]`, `[20]`, `[21]`).
- **Reasoning Ceiling**: Rewrote "7B models cannot solve window functions" to "within the evaluated setting, the local Qwen2.5 7B model exhibited a systematic semantic reasoning plateau at 68.00% across complex window functions, consistent with parameter-scale capacity boundaries documented in LLM literature (`[26]`)" (`Section 13`, `Section 15`).
- **Negative Constraints**: Rewrote generalized repair claims to specify that negative constraint benefits were localized to Query Q19 in the benchmark dataset (`Section 14`).
- **Temporal Decay**: Rewrote temporal decay efficacy claims to explicitly state that decay was mathematically implemented and unit-tested, but unexercised under the benchmark execution duration (`Section 6`, `Section 14`).
- **Ablation Interpretation**: Rewrote ablation claims to distinguish between statistically observed differences (e.g., retries on Q19) and parity outcomes (e.g., semantic accuracy across all modes).

### 4.4 Claims Removed
- Removed claim of "first-ever integrated runtime governance architecture" (replaced with objective structural description of ARMG's nine integrated components).
- Removed unsupported assertions that prior self-correction frameworks are "fundamentally incapable of learning" (softened to noting their lack of persistent, cross-query memory storage across isolated query executions).
- Removed all marketing phrasing, such as "flawless", "bulletproof", and "unprecedented".
- Removed unverified claims regarding universal multi-user throughput.

### 4.5 Related Work Changes (Section 2 Rebuild)
- **Section 2.1 (Text-to-SQL and Self-Correction)**: Completely restructured to contrast modern prompting/decomposition approaches (DIN-SQL `[1]`, DAIL-SQL `[2]`, MAC-SQL `[14]`) and execution-trace repair methods (Self-Refine `[4]`, Reflexion `[5]`, Self-Debug `[15]`, Self-Edit `[16]`) with ARMG's deterministic diagnostic taxonomy and persistent operational memory.
- **Section 2.2 (Retrieval and Agent Memory)**: Rebuilt to establish the foundational differences between unstructured vector RAG (`[6]`), episodic agent memory streams (Generative Agents `[7]`, MemGPT `[8]`, CoALA `[19]`), and ARMG's strict lifecycle transition:
  $$\text{RuntimeObservation} \xrightarrow{\text{Diagnosis}} \text{RuntimeKnowledge} \xrightarrow{\text{Governance}} \text{RuntimeMemory} \xrightarrow{\text{FAISS}} \text{Retrieval}$$
  Clearly distinguished ephemeral execution artifacts (`RuntimeKnowledge`) from governed, persistent operational memories (`RuntimeMemory`).
- **Section 2.3 (Database Safety)**: Rewritten to review prompt-based guardrails (NeMo Guardrails `[9]`) and their vulnerability to adversarial jailbreaks (`[20]`, `[21]`), framing ARMG's pre-execution SQLGlot AST validation (`[10]`) as an imperative, deterministic containment layer inspired by foundational static analysis principles (AMNESIA `[11]`).

### 4.6 Research-Gap Changes (Section 1)
- Replaced informal gap statement with a formal, nine-dimensional research gap paragraph.
- Synthesized the specific combination addressed by ARMG: (1) local open-weights foundation models, (2) runtime database feedback, (3) deterministic 7-tier diagnosis, (4) ephemeral diagnostic knowledge separation, (5) multi-factor governed admission and reinforcement, (6) mutual-exclusion duplicate suppression, (7) diagnostic negative constraints, (8) deterministic AST-level safety containment, and (9) separation of relational execution accuracy ($\text{ExecAcc}$) from database execution success ($\text{ExecSucc}$).
- Strictly avoided unsupported novelty claims such as "no previous work has done this".

---

## 5. STEP 4 — Final Scientific Audit, Step-3 Correction & Content Freeze

During the Step 4 final scientific audit, the manuscript underwent sentence-by-sentence forensic scrutiny to ensure that every literature, empirical, and architectural claim can withstand reviewer critique:

1. **RAG Scope Overgeneralization Correction (Problem A)**:
   - *Section 1 (Item 2)*: Refined the claim regarding naive RAG from attributing raw query storage to Lewis et al. [6] to framing it as a vulnerability of naive retrieval implementations that append historical execution exemplars without lifecycle governance ([7], [8]).
   - *Section 2.2*: Replaced "In standard RAG, every executed query is appended unconditionally..." with evidence-safe wording contrasting the general conversational focus of existing agent memory systems with the operational execution constraints of database systems.
2. **Model Scale & Causal Reasoning Ceiling Correction (Problem C)**:
   - *Section 13*: Rewrote the root-cause interpretation of the 68.00% relational semantic accuracy plateau. Explicitly decoupled the empirical plateau on complex window functions from sweeping causal claims about 7B models, clarifying that model-scaling literature ([26]) provides contextual background on emergent abilities, but the benchmark does not causally isolate model size.
3. **Safety Wording Containment (Problem D)**:
   - *Section 15.1*: Replaced "provably blocked all tested destructive statements" with "successfully intercepted all tested destructive statements across unit and benchmark evaluations", completely eliminating absolute safety and proof terminology.
4. **Empirical Deduplication Framing (Problem E)**:
   - *Section 1 & Section 15.1*: Bounded memory deduplication claims strictly to the evaluated benchmark lifecycle, stating that mutual exclusion maintained the store invariant at 3 memories whereas unmanaged naive RAG accumulated 23 entries.
5. **Bibliographic Reclassification (Phase 1 Audit)**:
   - Audited all 26 references individually, correcting the classification from a coarse "22 peer-reviewed + 4 technical" to a precise breakdown: 19 peer-reviewed publications (14 conference, 4 journal, 1 demonstration), 3 scholarly preprints (MemGPT [8], GCG [21], Execution-Guided Decoding [25]), 2 official technical reports (Qwen2.5 [3], Nomic Embed [18]), and 2 official software specifications (SQLGlot [10], LangGraph [22]).
6. **Manuscript Content Freeze**:
   - Confirmed zero unresolved placeholders, zero prohibited hyperbole terms, zero numerical discrepancies against frozen evidence, and complete internal mathematical consistency. Freezing content for Step 5.

---

## 6. STEP 5 — Figure/Table Generation & Manuscript Visual Integration

During Step 5, all publication-quality figures and tables identified by the Step 4 readiness audit were generated, validated against frozen evidence, and integrated into `manuscript/ieee_manuscript.md`:

### 6.1 Pre-Production Visual Source Audit
- Conducted comprehensive source audit (`ARMG_STEP5_VISUAL_SOURCE_AUDIT.md`) mapping all 6 figures and 9 tables to exact source files, verified columns, numerical values, and intended scientific interpretations.
- Resolved all potential visual ambiguities prior to asset rendering:
  - Corrected Table III scope to include all six experimental modes.
  - Mandated that Figure 4 plot all six modes rather than a 2-mode subset.
  - Mandated that Figure 5 explicitly distinguish relative percentage changes (%) from percentage-point shifts (pp).
  - Ensured Figure 6 accurately reflects cumulative query-level progression and plateau without interpolation.

### 6.2 Generation of Publication-Quality Visual Figures (6 Figures)
- Generated six standalone, reproducible Python scripts under `manuscript/figures/source/` using `matplotlib` without hardcoded arbitrary numbers:
  - `fig1_architecture.py`: 10-node closed-loop LangGraph architecture with AST safety containment, bounded repair ($K \le 3$), and mutual exclusion.
  - `fig2_lifecycle.py`: 6-state memory lifecycle state transition machine with exact numerical thresholds ($\text{Utility}_0 \ge 0.25$, $\alpha=0.10$, $\beta=0.15$, $\lambda=0.05/\text{day}$).
  - `fig3_retrieval_geometry.py`: Two-panel retrieval geometry plot comparing unnormalized pre-remediation scores ($S \approx 0.0035$) against Unit-$L_2$ normalized scores restoring 16 retrieval events across 12 queries above $\tau = 0.50$.
  - `fig4_execsucc_execacc.py`: Grouped bar chart comparing PostgreSQL execution success and relational execution accuracy across all six modes.
  - `fig5_tradeoff.py`: Horizontal delta chart displaying the five core operational trade-offs of Full ARMG relative to Mode 2 ($-34.38\%$ retries, $-5.30\%$ tokens, $+4.00\,\text{pp}$ PG success, $+19.79\%$ latency, $0.00\,\text{pp}$ accuracy).
  - `fig6_memory_growth.py`: Cumulative store growth step plot comparing Mode 4 (plateau at 3 memories) against Mode 3 (accumulation to 23 memories).
- Exported all figures in both high-resolution 300 DPI PNG rasters (`manuscript/figures/png/`) and scalable vector SVG formats (`manuscript/figures/svg/`).

### 6.3 Generation of Publication-Quality Tables (9 Tables)
- Created `manuscript/tables/generate_tables.py` producing 9 camera-ready LaTeX table files (`manuscript/tables/table1_taxonomy.tex` through `table9_failures.tex`) conforming to IEEE journal/conference float standards.
- Integrated all 9 tables as clean Markdown tables directly into `manuscript/ieee_manuscript.md`:
  - Table I: Canonical 7-Tier Exception Taxonomy Matrix and Candidate Repair Heuristics (Section 5.1).
  - Table II: Comparative Empirical Benchmark Results Across Six Experimental Modes ($n=3$) (Section 10.1).
  - Table III: PostgreSQL Execution Success vs. Relational Semantic Accuracy Across All Six Modes (Section 13).
  - Table IV: Canonical System Configuration and Component Mapping (Section 9.1).
  - Table V: Relational Data Warehouse Star Schema Specification (Section 9.1).
  - Table VI: Benchmark Query Corpus Distribution Across Complexity Categories (Section 9.1).
  - Table VII: Mathematical Governance Engine Control Equations and Parameter Specifications (Section 6).
  - Table VIII: Mode 4 vs. Mode 2 Comparative Trade-Off Profile (Section 10.2).
  - Table IX: Forensic Diagnostic Breakdown of Seven Divergent Semantic Queries in Mode 4 (Section 13).

### 6.4 Manuscript Integration & Text Cross-Referencing
- Modified `manuscript/ieee_manuscript.md` to integrate all 6 figures and 9 tables.
- Guaranteed strict formatting and citation constraints:
  - Every figure and table is explicitly introduced in narrative text prior to appearing.
  - Sequential, unique numbering enforced (Fig. 1–6, Table I–IX).
  - Zero orphan assets, zero missing assets, zero unreferenced visual elements.
  - All captions are factual, self-contained, and free of unverified hyperbole.

### 6.5 Automated Data Integrity & Visual QA Verification
- Executed `scripts/verify_data_integrity.py` confirming 100% mathematical consistency across figures, tables, manuscript text, and frozen benchmark CSVs.
- Created `ARMG_IEEE_Visual_QA_Report.md` confirming single-column and double-column readability, absence of clipping, high grayscale contrast, and zero chartjunk.
- Created `ARMG_IEEE_Visual_Asset_Manifest.md` cataloging file paths, dimensions, DPI, source scripts, and manuscript sections for all visual assets.
- **Protected Files Invariant**: Confirmed that `ARMG_IEEE_Paper_Revision_Dossier.md`, `manuscript/evidence_package.md`, benchmark result CSVs, and repository source code remained strictly unmodified.

---

## 7. STEP 5.1: PRE-FORMATTING SCIENTIFIC + VISUAL CORRECTION GATE

### 7.1 Table V Canonical Warehouse Schema Alignment
- Audited `manuscript/tables/table5_schema.tex`, `manuscript/tables/generate_tables.py`, and `manuscript/ieee_manuscript.md` against `db/schema.sql` and `scripts/seed_warehouse.py`.
- Enforced canonical Star Schema table identities and row counts:
  - `dim_time`: 365 daily rows, PK: `time_key`
  - `dim_geography`: 6 enterprise geographic zones, PK: `geo_key`
  - `dim_product`: 8 products, PK: `product_key`
  - `fact_sales_performance`: 2,000 transaction records, PK: `fact_key`, FKs: `time_key`, `geo_key`, `product_key`
- Eliminated all stale values: `dim_geography = 50`, `dim_product = 100`, `fact_sales`, `sales_id`.

### 7.2 Table VI Canonical Query Corpus Distribution Alignment
- Audited `manuscript/tables/table6_queries.tex`, `manuscript/tables/generate_tables.py`, and `manuscript/ieee_manuscript.md` against `benchmark/queries.json`.
- Enforced exact 5/8/6/6 corpus complexity distribution across 25 benchmark queries:
  - Category A: Q01–Q05 (5 queries: simple aggregations/groupings)
  - Category B: Q06–Q13 (8 queries: multi-table analytical joins)
  - Category C: Q14–Q19 (6 queries: advanced window functions)
  - Category D: Q20–Q25 (6 queries: semantic/schema trap queries)
  - Total Corpus: Q01–Q25 (25 queries)
- Eliminated incorrect 6/7/8/4 category allocations.

### 7.3 Table LaTeX Sanitization & Duplicate Table Verification
- Audited all 9 `.tex` files in `manuscript/tables/`:
  - Removed all markdown syntax (`**`) embedded in LaTeX.
  - Verified brace balancing, escaping of underscores (`\_`) and percent signs (`\%`), math mode delimiters, and table environments (`table`, `table*`).
  - Verified uniqueness of all table labels (`tab:system_config` unique; zero duplicate Table IV or any other table).
  - Confirmed exactly 9 tables exist (Table I through Table IX).

### 7.4 Figure 1 Architecture Diagram Enhancement
- Audited `manuscript/figures/source/fig1_architecture.py` against `graph/workflow.py`:
  - Preserved exact canonical 10-node topology and directed edges.
  - Substantially expanded Node 10 (`memory_governance_node`) bounding dimensions ($W=18.0, H=9.0$), completely resolving text cramping and title overlap.
  - Structured Node 10 internally into two clear functional sub-panels: "Memory Reinforcement" and "Candidate Memory Admission".
  - Cleaned outer-perimeter repair loopback route ($x=1.5, y=-2.5 \to 3.5$), eliminating connector crossings and ambiguous arrowheads.
  - Re-rendered `manuscript/figures/png/fig1_architecture.png` (300 DPI) and `manuscript/figures/svg/fig1_architecture.svg`.

### 7.5 Figure 2 Lifecycle Transition Machine Arrow Direction Validation
- Audited `manuscript/figures/source/fig2_lifecycle.py` against `memory/governance.py`:
  - Validated exact 6 states: `NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`.
  - Audited transition arrowhead directions: verified forward transition from `NEW` to `ACTIVE` (pointing rightward) and terminal pruning transition from `ARCHIVED` to `DELETED` (pointing strictly downward from ARCHIVED at $y=38$ to DELETED at $y=22$).
  - Eliminated edge-label collisions, preserved explicit numerical governance controls ($C_0 = 0.50$, $\alpha = 0.10$, $\beta = 0.15$, $\lambda = 0.05/\text{day}$, archive $C < 0.20$, delete $C < 0.15$).
  - Re-rendered `manuscript/figures/png/fig2_lifecycle.png` (300 DPI) and `manuscript/figures/svg/fig2_lifecycle.svg`.

### 7.6 Figures 3–6 Raster/Vector Cleanliness
- Audited Figures 3–6 against frozen evidence:
  - Removed embedded "Figure X:" prefixes from image title strings in `fig4_execsucc_execacc.py`, `fig5_tradeoff.py`, and `fig6_memory_growth.py` to ensure captions are rendered exclusively via document typesetting.
  - Re-rendered 300 DPI PNG rasters and scalable vector SVGs.

### 7.7 Scientific Claim Language & Title Unification
- Enforced single authoritative canonical title across manuscript and handoff documents:
  *Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*
- Audited Table VIII and related prose to enforce descriptive non-causal language ("Observed identical relational execution accuracy in the evaluated benchmark").
- Preserved strict distinction between relative percentages (%) and percentage points (pp).
- Preserved 26 verified bibliographic citations (19 peer-reviewed, 3 preprints, 2 technical reports, 2 software specifications).

### 7.8 Data Integrity Verification Expansion
- Updated `scripts/verify_data_integrity.py` with Checks 8, 9, and 10 asserting canonical Table V schema, Table VI corpus distribution, and LaTeX table syntax/uniqueness.
- Executed automated integrity script: all 10 checks passed with zero errors.



