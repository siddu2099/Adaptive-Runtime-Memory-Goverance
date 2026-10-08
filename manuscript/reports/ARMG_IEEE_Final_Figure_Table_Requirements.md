# ARMG IEEE Final Figure & Table Requirements

**Document Role**: Comprehensive Visual & Tabular Asset Specification  
**Target Manuscript**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md` (Sections 28 & 29)  
**Status**: Pre-Submission Specification & Production Readiness Audit  
**Date**: October 2026  

---

## 1. Overview & Verification Standard

This specification cross-references every figure and table required by the canonical technical dossier (`ARMG_IEEE_Paper_Revision_Dossier.md`) against `manuscript/ieee_manuscript.md`. Each visual and tabular asset is categorized according to its publication necessity, source data location, implementation status, and whether it is **READY TO GENERATE** (from existing frozen evidence) or **REQUIRES NEW EXPERIMENT**.

Under strict publication integrity rules:
- **Zero data fabrication**: All charts and tables must draw strictly from frozen CSV artifacts (`benchmark/seed*/benchmark_results.csv`, `benchmark/pre_remediation_results.csv`) and source code (`graph/workflow.py`, `memory/governance.py`).
- **Zero placeholder figures**: In-text markdown descriptions or formal ASCII tables must represent data accurately until vector graphics rendering is executed for final camera-ready layout.

---

## 2. Comprehensive Figure Specification

| Figure ID | Canonical Figure Title | Purpose & Architectural Role | Data Source / Implementation Anchor | Data Required | Manuscript Status | Production Readiness Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **Fig. 1** | End-to-End ARMG Architecture and Closed-Loop State Machine | Illustrates the 10-node directed state graph, zero-token schema pruning, pre-execution AST safety boundary, PostgreSQL execution, 7-tier diagnosis, and memory governance loop. | `graph/workflow.py:88-160` | Full node definitions, edge transitions, and conditional routing logic. | Described in Section 4 text; structural Mermaid diagram in Dossier. | **READY TO GENERATE** (From `graph/workflow.py`) |
| **Fig. 2** | Memory Lifecycle State Transition Machine | Details the six discrete lifecycle states (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`), transition conditions, and mathematical thresholds. | `memory/governance.py:23-339` | Transition formulas (Eq. 2–5), confidence thresholds ($0.80, 0.20, 0.15$), and admission gating. | Formalized in Section 6 text. | **READY TO GENERATE** (From `memory/governance.py`) |
| **Fig. 3** | Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry | Visualizes the geometric effect of Unit-L2 normalization on nomic-embed vectors, showing how unnormalized vectors ($d^2 \approx 280, S \approx 0.0035$) failed threshold $\tau = 0.50$ while normalized vectors restored 16 retrievals. | `benchmark/pre_remediation_results.csv` vs. `benchmark/seed*/benchmark_results.csv` | L2 distance distributions, vector norms ($\|\mathbf{v}\| \approx 19.8 \to 1.0$), and similarity scores. | Detailed in Section 11.1 text. | **READY TO GENERATE** (From benchmark CSVs) |
| **Fig. 4** | PostgreSQL Execution Success vs. Relational Semantic Equivalence Gap | Grouped bar chart illustrating the critical divergence between execution success ($76.0\% \to 96.0\%$) and relational execution accuracy ($57.3\% \to 68.0\%$) across all six modes. | Table III in manuscript; `manuscript/evidence_package.md` | Mean $\text{ExecSucc}$ and $\text{ExecAcc}$ percentages across Modes 1 through 6. | Data formalized in Table III. | **READY TO GENERATE** (From Table III data) |
| **Fig. 5** | Mode 2 vs. Mode 4 Operational Trade-Off Profile | Multi-dimensional radar or bar chart illustrating the operational trade-off: Retries ($-34.38\%$), Tokens ($-5.30\%$), Latency ($+19.79\%$), and Relational Accuracy ($0.00\%$). | Section 10.2 text; `benchmark/seed*/benchmark_results.csv` | Relative percentage deltas between Mode 2 and Mode 4 across all key metrics. | Data detailed in Section 10.2. | **READY TO GENERATE** (From Table II data) |
| **Fig. 6** | Memory Bank Growth Profile: Full ARMG vs. Naive Vector RAG | Step chart plotting persistent vector store size across queries Q01 through Q25, demonstrating the invariant plateau at 3 memories in Mode 4 vs. linear accumulation to 23 in Mode 3. | `benchmark/seed*/benchmark_results.csv` (`final_store_size` progression) | Query-by-query store count progression for Mode 3 and Mode 4. | Detailed in Section 11.2 text. | **READY TO GENERATE** (From benchmark CSV logs) |

---

## 3. Comprehensive Table Specification

| Table ID | Canonical Table Title | Purpose & Architectural Role | Data Source / Implementation Anchor | Data Required | Manuscript Status | Production Readiness Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **Table I** | Canonical 7-Tier Exception Taxonomy Matrix | Formally defines the 7 precedence tiers, taxonomy categories, detection regexes, and operational repair rules. | `agents/taxonomy.py:11-34`; `agents/error_diagnosis.py:189-340` | Precedence tier, category name, regex trigger, implementation definition. | **Present in Manuscript** (Section 5.1). | **COMPLETE & VERIFIED** |
| **Table II** | Comparative Empirical Benchmark Results across Six Modes ($n = 3$) | The primary experimental results table presenting mean and sample standard deviation for ExecAcc, PG Success, Retries, Latency, Tokens, and Store Size across all 6 modes. | `manuscript/evidence_package.md`; `benchmark/seed*/benchmark_results.csv` | 6 modes $\times$ 6 metrics with $\pm$ sample standard deviations across Seeds 42, 123, 999. | **Present in Manuscript** (Section 10.1). | **COMPLETE & VERIFIED** |
| **Table III** | PostgreSQL Execution Success vs. Relational Semantic Accuracy Discrepancy | Documents the exact percentage gap between physical execution success and semantic relational equivalence across Modes 1 through 4. | Section 13 in manuscript; Dossier Section 15 | Mode name, ExecSucc %, ExecAcc %, and absolute divergence gap. | **Present in Manuscript** (Section 13). | **COMPLETE & VERIFIED** |
| **Table IV** | Canonical System Configuration and Component Mapping | Exhaustive specification of all 10 LangGraph nodes, software libraries, model versions, and hardware environments. | Dossier Section 5; `graph/workflow.py` | Component name, repo path, class/function, input/output types. | Detailed in text Section 4 & 9; ready for Appendix. | **READY TO GENERATE** (From Dossier Section 5) |
| **Table V** | Relational Data Warehouse Star Schema Specification | Full relational specification of the 4 tables (`dim_time`, `dim_geography`, `dim_product`, `fact_sales_performance`), row counts, attributes, and foreign keys. | `db/schema.sql`; `scripts/seed_warehouse.py` | Table name, row count, attribute list, primary/foreign key definitions. | Summarized in text Section 9.1; ready for Appendix. | **READY TO GENERATE** (From `db/schema.sql`) |
| **Table VI** | Benchmark Query Corpus Distribution | Breakdown of the 25 queries across Categories A, B, C, D, detailing query intent and schema traversal complexity. | `benchmark/queries.json` | Query ID, category, natural language question, SQL clause complexity. | Summarized in text Section 9.1; ready for Appendix. | **READY TO GENERATE** (From `benchmark/queries.json`) |
| **Table VII** | Mathematical Governance Control Equations | Formal compilation of the 6 control equations (Utility, Admission, Escalation, Penalty, Decay, Mutual Exclusion). | `memory/governance.py:44-339` | Equation name, formula, parameter defaults ($\theta=0.25, \alpha=0.10, \beta=0.15, \lambda=0.05$). | Formalized in Section 6 text equations. | **COMPLETE & VERIFIED** |
| **Table VIII** | Mode 4 vs. Mode 2 Comparative Trade-Off Analysis | Tabular presentation of absolute and relative deltas for accuracy, retries, tokens, and latency between Mode 2 and Mode 4. | Section 10.2 text; Dossier Section 16 | Absolute deltas, percentage changes, consistency across seeds. | Formalized in Section 10.2 text. | **COMPLETE & VERIFIED** |
| **Table IX** | Forensic Diagnostic Breakdown of the 7 Divergent Semantic Queries | Case-by-case analysis of queries Q05, Q14, Q15, Q17, Q18, Q19, Q25 explaining the exact SQL construct failure. | Section 13 text; Dossier Section 19 | Query ID, category, gold SQL requirement, generated SQL failure mode. | Fully detailed in Section 13 text. | **COMPLETE & VERIFIED** |

---

## 4. Production Checklist for Camera-Ready Submission

- [x] **Core Manuscript Tables (Tables I, II, III)**: Fully integrated into `manuscript/ieee_manuscript.md` with verified frozen data.
- [x] **Figure Source Data**: All 6 figures have 100% frozen source data available in repository code and CSVs; zero new experiments are required to generate them.
- [ ] **Figure Vector Rendering**: Figures 1–6 must be compiled into high-resolution EPS/PDF vector graphics during final LaTeX/IEEEtran document assembly.
- [ ] **Appendix Tables (Tables IV, V, VI)**: Tables IV, V, VI can be placed directly into an extended technical appendix or submitted as supplementary materials.
