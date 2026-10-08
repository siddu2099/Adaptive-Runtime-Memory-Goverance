# ARMG IEEE Paper — Step 5: Visual Asset Manifest

**Date**: 2026-10-01  
**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Status**: COMPLETE / VERIFIED  

---

## 1. Visual Figures Manifest (6 Figures)

All quantitative figures are generated from reproducible Python scripts under `manuscript/figures/source/` using `matplotlib` without hardcoded arbitrary numbers. Both high-resolution 300 DPI PNG rasters and scalable vector SVG files are provided.

| Asset | File Path | Source Data | Format | DPI | Dimensions | Canonical Caption | Manuscript Section | Verified |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **Figure 1** | `manuscript/figures/png/fig1_architecture.png`<br>`manuscript/figures/svg/fig1_architecture.svg` | `graph/workflow.py`, Master Technical Dossier | PNG / SVG | 300 | $3300 \times 1800$ | *Fig. 1. End-to-End ARMG Architecture and Closed-Loop State Machine. The canonical 10-node LangGraph execution graph enforces deterministic AST safety gating prior to PostgreSQL execution, orchestrates bounded 7-tier diagnostic repair ($K \le 3$), and executes algorithmic mutual exclusion between memory reinforcement and admission at terminal outcomes.* | Section 4 (ARMG Architecture) | **YES** (Step 5.1: Node 10 expanded, zero text overlap, unambiguous perimeter loopback, directed edges verified) |
| **Figure 2** | `manuscript/figures/png/fig2_lifecycle.png`<br>`manuscript/figures/svg/fig2_lifecycle.svg` | `memory/governance.py` | PNG / SVG | 300 | $3300 \times 1950$ | *Fig. 2. ARMG Runtime Memory Lifecycle State Transition Machine. Operational memories progress across six discrete lifecycle states (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`) governed by mathematical admission gating ($\text{Utility}_0 \ge 0.25$), asymptotic confidence escalation ($\alpha = 0.10$), multiplicative penalty ($\beta = 0.15$), and continuous exponential decay ($\lambda = 0.05/\text{day}$).* | Section 6.7 (Memory Governance and Lifecycle) | **YES** (Step 5.1: Arrow directions verified against implementation: NEW $\to$ ACTIVE forward, ARCHIVED $\to$ DELETED downward terminal purge, zero collisions) |
| **Figure 3** | `manuscript/figures/png/fig3_retrieval_geometry.png`<br>`manuscript/figures/svg/fig3_retrieval_geometry.svg` | `benchmark/pre_remediation_results.csv`, `benchmark/seed42/benchmark_results.csv` | PNG / SVG | 300 | $3300 \times 1650$ | *Fig. 3. Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry. Left: Unnormalized `nomic-embed-text` embeddings generated large norms ($\|\mathbf{v}\| \approx 19.8$), driving all similarity scores to $S \approx 0.0035 \ll \tau = 0.50$ (zero retrievals). Right: Unit-$L_2$ normalization restored proper inner-product geometry, elevating 16 retrieval events above threshold $\tau = 0.50$ across 12 distinct queries ($48.0\%$ coverage).* | Section 11.1 (Remediation of Vector Geometry) | **YES** |
| **Figure 4** | `manuscript/figures/png/fig4_execsucc_execacc.png`<br>`manuscript/figures/svg/fig4_execsucc_execacc.svg` | `manuscript/evidence_package.md` (Table II) | PNG / SVG | 300 | $3300 \times 1800$ | *Fig. 4. PostgreSQL Execution Success vs. Relational Execution Accuracy across six experimental modes ($n = 3$ repeated runs). Shaded bars illustrate PostgreSQL execution success ($\text{ExecSucc}$), while dark hatched bars represent relational semantic accuracy ($\text{ExecAcc}$). Across Modes 2–6, relational execution accuracy plateaus at 68.00% despite execution success reaching up to 96.00%, illustrating the critical gap between execution and semantic equivalence.* | Section 10.1 (Comparative Empirical Results) | **YES** (Step 5.1: Figure prefix removed from plot title) |
| **Figure 5** | `manuscript/figures/png/fig5_tradeoff.png`<br>`manuscript/figures/svg/fig5_tradeoff.svg` | `manuscript/evidence_package.md` (Table II & Table VIII) | PNG / SVG | 300 | $3000 \times 1650$ | *Fig. 5. Mode 2 vs. Full ARMG Operational Trade-Off Profile. Demonstrates the observed operational trade-offs of Full ARMG relative to stateless self-correction: a 34.38% reduction in repair iterations, 5.30% token reduction, and +4.00 percentage points in execution success, balanced against a 19.79% latency overhead, with relational accuracy remaining identical (0.00 pp).* | Section 10.2 (Performance Trade-Off Analysis) | **YES** (Step 5.1: Figure prefix removed from plot title) |
| **Figure 6** | `manuscript/figures/png/fig6_memory_growth.png`<br>`manuscript/figures/svg/fig6_memory_growth.svg` | `benchmark/seed42/benchmark_results.csv` | PNG / SVG | 300 | $3300 \times 1650$ | *Fig. 6. Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG. In Full ARMG (Mode 4), algorithmic mutual exclusion between memory reinforcement and admission maintained the persistent store size strictly invariant at exactly 3 memories from Q15 through Q25. In contrast, unmanaged Naive Vector RAG (Mode 3) appended uncurated exemplars upon every execution success, expanding to 23 memories.* | Section 11.2 (Lifecycle Metrics and Deduplication) | **YES** (Step 5.1: Figure prefix removed from plot title) |

---

## 2. Tabular Manifest (9 Tables)

All nine tables are available in camera-ready LaTeX under `manuscript/tables/` and integrated as Markdown tables in `manuscript/ieee_manuscript.md`.

| Asset | LaTeX File | Markdown Embedded | Source Data | Canonical Caption | Manuscript Section | Verified |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: |
| **Table I** | `manuscript/tables/table1_taxonomy.tex` | Yes | `agents/taxonomy.py`, `agents/error_diagnosis.py` | Table I: Canonical 7-Tier Exception Taxonomy Matrix and Candidate Repair Heuristics | Section 5.1 (Exception Taxonomy) | **YES** |
| **Table II** | `manuscript/tables/table2_results.tex` | Yes | `manuscript/evidence_package.md` (Table II) | Table II: Comparative Empirical Benchmark Results Across Six Experimental Modes ($n = 3$ Repeated Executions) | Section 10.1 (Main Results) | **YES** |
| **Table III** | `manuscript/tables/table3_gap.tex` | Yes | `manuscript/evidence_package.md` (Table II, all 6 modes) | Table III: PostgreSQL Execution Success vs. Relational Semantic Accuracy Across All Six Modes | Section 13 (Semantic Failure Analysis) | **YES** |
| **Table IV** | `manuscript/tables/table4_config.tex` | Yes | Repository configuration & system metadata | Table IV: Canonical System Configuration and Component Mapping | Section 9.1 (Evaluation Configuration) | **YES** (Single unique tab:system_config) |
| **Table V** | `manuscript/tables/table5_schema.tex` | Yes | `scripts/seed_warehouse.py`, `db/schema.sql` | Table V: Relational Data Warehouse Star Schema Specification | Section 9.1 (Benchmark Warehouse) | **YES** (Step 5.1: Canonical 365/6/8/2000 rows; time_key, geo_key, product_key, fact_key) |
| **Table VI** | `manuscript/tables/table6_queries.tex` | Yes | `benchmark/queries.json` | Table VI: Benchmark Query Corpus Distribution Across Complexity Categories | Section 9.1 (Benchmark Corpus) | **YES** (Step 5.1: Canonical 5/8/6/6 distribution across Q01-Q05, Q06-Q13, Q14-Q19, Q20-Q25; Total 25) |
| **Table VII** | `manuscript/tables/table7_governance.tex` | Yes | `memory/governance.py` | Table VII: Mathematical Governance Engine Control Equations and Parameter Specifications | Section 6 (Memory Governance and Lifecycle) | **YES** |
| **Table VIII** | `manuscript/tables/table8_tradeoff.tex` | Yes | `manuscript/evidence_package.md` (Table II / VIII) | Table VIII: Mode 4 (Full ARMG) vs. Mode 2 (Stateless Self-Correction) Comparative Trade-Off Profile | Section 10.2 (Performance Trade-Off Analysis) | **YES** (Step 5.1: Non-causal empirical phrasing) |
| **Table IX** | `manuscript/tables/table9_failures.tex` | Yes | `benchmark/seed*/benchmark_results.csv`, query logs | Table IX: Forensic Diagnostic Breakdown of the Seven Divergent Semantic Queries in Mode 4 | Section 13 (Analysis of 7 Divergent Queries) | **YES** |

---

## 3. Directory Layout of Generated Visual Assets

```
manuscript/
├── figures/
│   ├── source/
│   │   ├── fig1_architecture.py
│   │   ├── fig2_lifecycle.py
│   │   ├── fig3_retrieval_geometry.py
│   │   ├── fig4_execsucc_execacc.py
│   │   ├── fig5_tradeoff.py
│   │   └── fig6_memory_growth.py
│   ├── png/
│   │   ├── fig1_architecture.png (300 DPI)
│   │   ├── fig2_lifecycle.png (300 DPI)
│   │   ├── fig3_retrieval_geometry.png (300 DPI)
│   │   ├── fig4_execsucc_execacc.png (300 DPI)
│   │   ├── fig5_tradeoff.png (300 DPI)
│   │   └── fig6_memory_growth.png (300 DPI)
│   └── svg/
│       ├── fig1_architecture.svg (Vector)
│       ├── fig2_lifecycle.svg (Vector)
│       ├── fig3_retrieval_geometry.svg (Vector)
│       ├── fig4_execsucc_execacc.svg (Vector)
│       ├── fig5_tradeoff.svg (Vector)
│       └── fig6_memory_growth.svg (Vector)
├── tables/
│   ├── generate_tables.py
│   ├── table1_taxonomy.tex
│   ├── table2_results.tex
│   ├── table3_gap.tex
│   ├── table4_config.tex
│   ├── table5_schema.tex
│   ├── table6_queries.tex
│   ├── table7_governance.tex
│   ├── table8_tradeoff.tex
│   └── table9_failures.tex
└── ieee_manuscript.md (Integrated with all 6 figures and 9 tables)
```
