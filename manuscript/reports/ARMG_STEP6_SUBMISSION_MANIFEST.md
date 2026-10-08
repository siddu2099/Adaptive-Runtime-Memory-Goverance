# ARMG IEEE Step 6.1: Submission Manifest

**Date**: 2026-10-02  
**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Workflow Stage**: STEP 6.1 — Author Integration + Provisional IEEE Conference Package  
**Document Role**: Authoritative Listing of Submission Package Contents  

---

## 1. Submission Package Overview

This manifest defines the clean, minimal, publication-ready package to be submitted to the publisher (or uploaded to an IEEE submission portal/Overleaf). It strictly excludes benchmark databases, Ollama weights, local FAISS indexes, test caches, and internal audit files.

```
manuscript/
├── ieee_camera_ready.tex         # Primary LaTeX source file (PROVISIONAL — NOT CAMERA-READY)
├── references.bib                # Authoritative BibTeX database (26 verified entries)
├── ieee_camera_ready.pdf         # Compiled publication PDF (Generated upon external toolchain execution)
├── tables/                       # Nine standalone LaTeX table floats (\input{...})
│   ├── table1_taxonomy.tex
│   ├── table2_results.tex
│   ├── table3_gap.tex
│   ├── table4_config.tex
│   ├── table5_schema.tex
│   ├── table6_queries.tex
│   ├── table7_governance.tex
│   ├── table8_tradeoff.tex
│   └── table9_failures.tex
├── figures/                      # High-resolution raster and vector visual assets
│   ├── png/
│   │   ├── fig1_architecture.png (300 DPI)
│   │   ├── fig2_lifecycle.png (300 DPI)
│   │   ├── fig3_retrieval_geometry.png (300 DPI)
│   │   ├── fig4_execsucc_execacc.png (300 DPI)
│   │   ├── fig5_tradeoff.png (300 DPI)
│   │   └── fig6_memory_growth.png (300 DPI)
│   ├── svg/
│   │   ├── fig1_architecture.svg (Scalable vector)
│   │   ├── fig2_lifecycle.svg (Scalable vector)
│   │   ├── fig3_retrieval_geometry.svg (Scalable vector)
│   │   ├── fig4_execsucc_execacc.svg (Scalable vector)
│   │   ├── fig5_tradeoff.svg (Scalable vector)
│   │   └── fig6_memory_growth.svg (Scalable vector)
│   └── source/
│       ├── fig1_architecture.py
│       ├── fig2_lifecycle.py
│       ├── fig3_retrieval_geometry.py
│       ├── fig4_execsucc_execacc.py
│       ├── fig5_tradeoff.py
│       └── fig6_memory_growth.py
└── build/                        # Temporary compilation artifacts directory
```

---

## 2. Itemized File Inventory

### A. Primary Document Files

| File Name | Path | Description | Required by Venue |
| :--- | :--- | :--- | :---: |
| `ieee_camera_ready.tex` | `manuscript/ieee_camera_ready.tex` | Primary LaTeX manuscript source file, structured for IEEEtran documentclass with 19 major sections and integrated 5-author block. | **YES** |
| `references.bib` | `manuscript/references.bib` | Authoritative BibTeX database with exactly 26 references. Zero placeholder entries. | **YES** |
| `ieee_camera_ready.pdf` | `manuscript/ieee_camera_ready.pdf` | Compiled IEEE camera-ready document PDF (Produced upon toolchain execution). | **YES** |

### B. Tabular Float Files (`manuscript/tables/`)

| File Name | Path | Content / Table Number | Target Float Type |
| :--- | :--- | :--- | :---: |
| `table1_taxonomy.tex` | `manuscript/tables/table1_taxonomy.tex` | Table I: Canonical 7-Tier Exception Taxonomy Matrix | `table*` |
| `table2_results.tex` | `manuscript/tables/table2_results.tex` | Table II: Comparative Empirical Benchmark Results Across Six Modes ($n=3$) | `table*` |
| `table3_gap.tex` | `manuscript/tables/table3_gap.tex` | Table III: PostgreSQL Execution Success vs. Relational Semantic Accuracy | `table` |
| `table4_config.tex` | `manuscript/tables/table4_config.tex` | Table IV: Canonical System Configuration and Component Mapping | `table` |
| `table5_schema.tex` | `manuscript/tables/table5_schema.tex` | Table V: Relational Data Warehouse Star Schema Specification (6/8/2000) | `table` |
| `table6_queries.tex` | `manuscript/tables/table6_queries.tex` | Table VI: Benchmark Query Corpus Distribution Across Complexity (5/8/6/6) | `table` |
| `table7_governance.tex` | `manuscript/tables/table7_governance.tex` | Table VII: Mathematical Governance Engine Control Equations | `table*` |
| `table8_tradeoff.tex` | `manuscript/tables/table8_tradeoff.tex` | Table VIII: Mode 4 vs. Mode 2 Comparative Trade-Off Profile | `table*` |
| `table9_failures.tex` | `manuscript/tables/table9_failures.tex` | Table IX: Forensic Diagnostic Breakdown of 7 Divergent Semantic Queries | `table*` |

### C. Visual Figure Files (`manuscript/figures/`)

| Asset | High-Res PNG (300 DPI) | Vector SVG | Source Python Script |
| :--- | :--- | :--- | :--- |
| **Figure 1** | `manuscript/figures/png/fig1_architecture.png` | `manuscript/figures/svg/fig1_architecture.svg` | `manuscript/figures/source/fig1_architecture.py` |
| **Figure 2** | `manuscript/figures/png/fig2_lifecycle.png` | `manuscript/figures/svg/fig2_lifecycle.svg` | `manuscript/figures/source/fig2_lifecycle.py` |
| **Figure 3** | `manuscript/figures/png/fig3_retrieval_geometry.png` | `manuscript/figures/svg/fig3_retrieval_geometry.svg` | `manuscript/figures/source/fig3_retrieval_geometry.py` |
| **Figure 4** | `manuscript/figures/png/fig4_execsucc_execacc.png` | `manuscript/figures/svg/fig4_execsucc_execacc.svg` | `manuscript/figures/source/fig4_execsucc_execacc.py` |
| **Figure 5** | `manuscript/figures/png/fig5_tradeoff.png` | `manuscript/figures/svg/fig5_tradeoff.svg` | `manuscript/figures/source/fig5_tradeoff.py` |
| **Figure 6** | `manuscript/figures/png/fig6_memory_growth.png` | `manuscript/figures/svg/fig6_memory_growth.svg` | `manuscript/figures/source/fig6_memory_growth.py` |

---

## 3. Explicitly Excluded Artifacts (Do NOT Submit)

The following local developmental, experimental, and audit files must **never** be included in the submission bundle:
- Database files: `db/schema.sql`, PostgreSQL physical data containers, `.env` credentials.
- Benchmark data artifacts: `benchmark/seed*/benchmark_results.csv`, `benchmark/pre_remediation_results.csv`.
- Machine learning models: Ollama binary caches, model checkpoints, local FAISS indexes (`faiss.index`).
- Test scripts and temporary build logs: `tests/`, `manuscript/build/*.aux`, `*.log`, `*.out`, `*.bbl`, `*.blg`.
- Internal forensic audit dossiers: `ARMG_IEEE_Paper_Revision_Dossier.md`, `ARMG_STEP*.md`, `ARMG_IEEE_Reviewer_Risk_Register.md`.

---

## 4. Submission Package Verification Status

All 16 package files (1 `.tex` file, 1 `.bib` file, 9 `.tex` table floats, 6 PNG figures, 6 SVG figures) are fully generated and verified:
- `scripts/verify_step6_format.py`: **13/13 checks passed**.
- `scripts/verify_data_integrity.py`: **10/10 checks passed**.

**Remaining Prerequisites for Submission**:
1. Official IEEE class file (`IEEEtran.cls`) or venue-specific submission portal upload.
2. Target venue confirmation.
3. External LaTeX compilation pass on TeX Live / MiKTeX / Overleaf.

**PACKAGE STATUS**:  
**STEP 6 PROVISIONAL PACKAGE COMPLETE — WAITING FOR OFFICIAL IEEE TEMPLATE / PDF COMPILATION**
