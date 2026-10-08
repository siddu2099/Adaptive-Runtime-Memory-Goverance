# ARMG IEEE Figure & Table Readiness Audit (Step 4)

**Document Role**: Forensic Visual & Tabular Asset Production Readiness Audit  
**Target Manuscript**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md` (Sections 27, 28, 29)  
**Frozen Evidence Package**: `manuscript/evidence_package.md`  
**Verification Standard**: 100% Traceability to Frozen Data, Code, and Evidence Package; Zero New Experiments Required  
**Date**: October 2026  
**Auditor**: Senior AI/ML Research Engineer & IEEE Technical Reviewer  

---

## 1. Figures Readiness Table

| Figure Number | Figure Title | Figure Purpose | Exact Data Source | Already Available? | Derivable from Frozen Evidence? | Requires New Experiment? | Ready for Step 5? |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Fig. 1** | End-to-End ARMG Architecture and Closed-Loop State Machine | Illustrates the 10-node directed state graph, zero-token schema pruning, pre-execution AST safety boundary, PostgreSQL execution, 7-tier diagnosis, and memory governance loop. | `graph/workflow.py:88-160`, Dossier Section 4 | Yes (Textual & Mermaid in Dossier) | Yes (Directly from `graph/workflow.py`) | **NO** | **YES** |
| **Fig. 2** | Memory Lifecycle State Transition Machine | Details the six discrete lifecycle states (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`), transition conditions, and mathematical thresholds. | `memory/governance.py:23-339`, Dossier Section 11 | Yes (Formal equations in Section 6) | Yes (Directly from `memory/governance.py`) | **NO** | **YES** |
| **Fig. 3** | Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry | Visualizes the geometric effect of Unit-L2 normalization on nomic-embed vectors, showing how unnormalized vectors ($d^2 \approx 280, S \approx 0.0035$) failed threshold $\tau = 0.50$ while normalized vectors restored 16 retrievals. | `benchmark/pre_remediation_results.csv` and `benchmark/seed*/benchmark_results.csv` | Yes (Described in Section 11.1) | Yes (CSV files contain exact L2 distances and similarity scores) | **NO** | **YES** |
| **Fig. 4** | PostgreSQL Execution Success vs. Relational Semantic Equivalence Gap | Grouped bar chart illustrating the critical divergence between execution success ($76.0\% \to 96.0\%$) and relational execution accuracy ($57.3\% \to 68.0\%$) across all six modes. | Table III in manuscript; `manuscript/evidence_package.md` | Yes (Table III in manuscript) | Yes (Directly from Table III data) | **NO** | **YES** |
| **Fig. 5** | Mode 2 vs. Mode 4 Operational Trade-Off Profile | Multi-dimensional radar or grouped bar chart illustrating the operational trade-off: Retries ($-34.38\%$), Tokens ($-5.30\%$), Latency ($+19.79\%$), and Relational Accuracy ($0.00\%$). | Section 10.2 text; `manuscript/evidence_package.md` | Yes (Table II and Section 10.2 text) | Yes (Directly from Table II deltas) | **NO** | **YES** |
| **Fig. 6** | Memory Bank Growth Profile: Full ARMG vs. Naive Vector RAG | Step chart plotting persistent vector store size across queries Q01 through Q25, demonstrating the invariant plateau at 3 memories in Mode 4 vs. linear accumulation to 23 in Mode 3. | `benchmark/seed*/benchmark_results.csv` (`final_store_size` column) | Yes (Described in Section 11.2) | Yes (Query-by-query CSV rows record store size progression) | **NO** | **YES** |

---

## 2. Tables Readiness Table

| Table Number | Table Title | Table Purpose | Exact Data Source | Already Available? | Derivable from Frozen Evidence? | Requires New Experiment? | Ready for Step 5? |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Table I** | Canonical 7-Tier Exception Taxonomy Matrix | Formally defines the 7 precedence tiers, taxonomy categories, detection regexes, and operational repair rules. | `agents/taxonomy.py:11-34`; `agents/error_diagnosis.py:189-340` | Yes (Embedded in manuscript Section 5.1) | Yes (Source code and Dossier Section 9) | **NO** | **YES** |
| **Table II** | Comparative Empirical Benchmark Results across Six Modes ($n = 3$) | The primary experimental results table presenting mean and sample standard deviation for ExecAcc, PG Success, Retries, Latency, Tokens, and Store Size across all 6 modes. | `manuscript/evidence_package.md`; `benchmark/seed*/benchmark_results.csv` | Yes (Embedded in manuscript Section 10.1) | Yes (Directly from frozen evidence package) | **NO** | **YES** |
| **Table III** | PostgreSQL Execution Success vs. Relational Semantic Accuracy Discrepancy | Documents the exact percentage gap between physical execution success and semantic relational equivalence across Modes 1 through 4. | Section 13 in manuscript; Dossier Section 15 | Yes (Embedded in manuscript Section 13) | Yes (Directly from Table II data) | **NO** | **YES** |
| **Table IV** | Canonical System Configuration and Component Mapping | Exhaustive specification of all 10 LangGraph nodes, software libraries, model versions, and hardware environments. | Dossier Section 5; `graph/workflow.py` | Yes (Documented in Dossier Section 5) | Yes (System environment and repository files) | **NO** | **YES** |
| **Table V** | Relational Data Warehouse Star Schema Specification | Full relational specification of the 4 tables (`dim_time`, `dim_geography`, `dim_product`, `fact_sales_performance`), row counts, attributes, and foreign keys. | `db/schema.sql`; `scripts/seed_warehouse.py` | Yes (Documented in Dossier Section 6) | Yes (Database schema SQL and seeding script) | **NO** | **YES** |
| **Table VI** | Benchmark Query Corpus Distribution | Breakdown of the 25 queries across Categories A, B, C, D, detailing query intent and schema traversal complexity. | `benchmark/queries.json` | Yes (Documented in Dossier Section 7) | Yes (`benchmark/queries.json` metadata) | **NO** | **YES** |
| **Table VII** | Mathematical Governance Control Equations | Formal compilation of the 6 control equations (Utility, Admission, Escalation, Penalty, Decay, Mutual Exclusion). | `memory/governance.py:44-339` | Yes (Embedded in manuscript Section 6) | Yes (Source code and mathematical specification) | **NO** | **YES** |
| **Table VIII** | Mode 4 vs. Mode 2 Comparative Trade-Off Analysis | Tabular presentation of absolute and relative deltas for accuracy, retries, tokens, and latency between Mode 2 and Mode 4. | Section 10.2 text; Dossier Section 16 | Yes (Detailed in manuscript Section 10.2) | Yes (Directly computable from Table II) | **NO** | **YES** |
| **Table IX** | Forensic Diagnostic Breakdown of the 7 Divergent Semantic Queries | Case-by-case analysis of queries Q05, Q14, Q15, Q17, Q18, Q19, Q25 explaining the exact SQL construct failure. | Section 13 text; Dossier Section 19 | Yes (Detailed in manuscript Section 13) | Yes (Benchmark failure logs and SQL comparison traces) | **NO** | **YES** |

---

## 3. Summary Assessment

- **Total Visual & Tabular Assets Audited**: 6 Figures, 9 Tables.
- **Assets Already Integrated in Manuscript Text**: 3 Core Tables (Tables I, II, III).
- **Assets Derivable from Frozen Evidence**: 15 / 15 (100%).
- **Assets Requiring New Experiments**: **ZERO (0)**.
- **Step 5 Readiness**: **100% READY FOR STEP 5**.
- **Action for Step 5**: Render Figures 1–6 using standard Python matplotlib/seaborn or TikZ/vector export, and format Tables I–IX into camera-ready IEEE two-column / single-column format.
