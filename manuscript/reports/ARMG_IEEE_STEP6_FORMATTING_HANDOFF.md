# ARMG IEEE Step 6 — Camera-Ready Formatting Handoff Document

**Date**: 2026-10-01  
**Source Workflow Stage**: STEP 5 (Visual Assets & Manuscript Integration) — COMPLETE  
**Target Workflow Stage**: STEP 6 (Final IEEE Camera-Ready Formatting)  
**Status**: **VISUAL ASSETS READY FOR IEEE FORMATTING**  

---

## 1. Primary Manuscript File

- **File Path**: `manuscript/ieee_manuscript.md`
- **Current State**: Fully revised, audited, literature-integrated (26 peer-reviewed/authoritative citations), and visually integrated with all 6 figures and 9 tables embedded in Markdown format.

---

## 2. Final Visual Figure Files

All figures are available in both high-resolution 300 DPI raster (`.png`) and scalable vector (`.svg`):

1. **Figure 1**:
   - `manuscript/figures/png/fig1_architecture.png`
   - `manuscript/figures/svg/fig1_architecture.svg`
2. **Figure 2**:
   - `manuscript/figures/png/fig2_lifecycle.png`
   - `manuscript/figures/svg/fig2_lifecycle.svg`
3. **Figure 3**:
   - `manuscript/figures/png/fig3_retrieval_geometry.png`
   - `manuscript/figures/svg/fig3_retrieval_geometry.svg`
4. **Figure 4**:
   - `manuscript/figures/png/fig4_execsucc_execacc.png`
   - `manuscript/figures/svg/fig4_execsucc_execacc.svg`
5. **Figure 5**:
   - `manuscript/figures/png/fig5_tradeoff.png`
   - `manuscript/figures/svg/fig5_tradeoff.svg`
6. **Figure 6**:
   - `manuscript/figures/png/fig6_memory_growth.png`
   - `manuscript/figures/svg/fig6_memory_growth.svg`

---

## 3. Final Camera-Ready Table Files

All tables are authored in LaTeX format (`.tex`) ready for `\input{...}` in IEEEtran:

1. **Table I**: `manuscript/tables/table1_taxonomy.tex`
2. **Table II**: `manuscript/tables/table2_results.tex`
3. **Table III**: `manuscript/tables/table3_gap.tex`
4. **Table IV**: `manuscript/tables/table4_config.tex`
5. **Table V**: `manuscript/tables/table5_schema.tex`
6. **Table VI**: `manuscript/tables/table6_queries.tex`
7. **Table VII**: `manuscript/tables/table7_governance.tex`
8. **Table VIII**: `manuscript/tables/table8_tradeoff.tex`
9. **Table IX**: `manuscript/tables/table9_failures.tex`

---

## 4. Figure & Table Numbering and Placement Mapping

| Asset ID | Title / Content | Target Section in IEEE Manuscript | LaTeX Placement Recommendation |
| :--- | :--- | :--- | :--- |
| **Figure 1** | End-to-End ARMG Architecture and Closed-Loop State Machine | Section 4 (ARMG Architecture) | `figure*` (double-column top float) |
| **Figure 2** | ARMG Runtime Memory Lifecycle State Transition Machine | Section 6.7 (Memory Governance and Lifecycle) | `figure` (single-column float) |
| **Figure 3** | Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry | Section 11.1 (Remediation of Vector Geometry) | `figure*` or `figure` |
| **Figure 4** | PostgreSQL Execution Success vs. Relational Execution Accuracy | Section 10.1 (Comparative Empirical Results) | `figure` (single-column float) |
| **Figure 5** | Mode 2 vs. Full ARMG Operational Trade-Off Profile | Section 10.2 (Performance Trade-Off Analysis) | `figure` (single-column float) |
| **Figure 6** | Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG | Section 11.2 (Lifecycle Metrics and Deduplication) | `figure` (single-column float) |
| **Table I** | Canonical 7-Tier Exception Taxonomy Matrix | Section 5.1 (Exception Taxonomy) | `table*` (double-column top float) |
| **Table II** | Comparative Empirical Benchmark Results Across Six Modes | Section 10.1 (Comparative Empirical Results) | `table*` (double-column top float) |
| **Table III** | PostgreSQL Execution Success vs. Relational Semantic Accuracy | Section 13 (Semantic Failure Analysis) | `table` (single-column float) |
| **Table IV** | Canonical System Configuration and Component Mapping | Section 9.1 (Evaluation Configuration) | `table` (single-column float) |
| **Table V** | Relational Data Warehouse Star Schema Specification | Section 9.1 (Benchmark Warehouse) | `table` (single-column float) |
| **Table VI** | Benchmark Query Corpus Distribution Across Categories | Section 9.1 (Benchmark Corpus) | `table` (single-column float) |
| **Table VII** | Mathematical Governance Engine Control Equations | Section 6 (Memory Governance and Lifecycle) | `table*` (double-column top float) |
| **Table VIII** | Mode 4 vs. Mode 2 Comparative Trade-Off Profile | Section 10.2 (Performance Trade-Off Analysis) | `table*` (double-column top float) |
| **Table IX** | Forensic Diagnostic Breakdown of 7 Divergent Semantic Queries | Section 13 (Analysis of 7 Divergent Queries) | `table*` (double-column top float) |

---

## 5. Remaining Formatting Tasks for Step 6

During Step 6 (Final IEEE Camera-Ready Formatting), the following mechanical formatting tasks will be performed:
1. **IEEEtran Template Typesetting**: Transitioning from Markdown to standard IEEE double-column conference/journal format (e.g., `IEEEtran.cls` or standard IEEE Word template).
2. **Author and Affiliation Block**: Structuring author names, affiliations, and email blocks according to IEEE guidelines.
3. **Float Tuning**: Balancing column lengths on the final page (`\usepackage{balance}` or `\balance`).
4. **Equation Formatting**: Converting inline equations to numbered `\begin{equation} ... \end{equation}` blocks where referenced.
5. **BibTeX Compilation**: Generating `references.bib` containing the 26 verified bibliographic entries.

---

## 6. Protected Scientific Content (DO NOT MODIFY IN STEP 6)

The following core findings and metrics are scientifically frozen and must not be altered during formatting:
1. **Relational Accuracy Plateau**: 68.00% across Modes 2, 3, 4, 5, 6 (17 of 25 queries).
2. **Repair Efficiency**: Observed 34.38% reduction in mean retries (0.28 vs. 0.43).
3. **Token Economy**: Observed 5.30% reduction in tokens (542.37 vs. 572.72).
4. **Execution Success**: 96.00% (Mode 4) vs. 92.00% (Mode 2) (+4.00 percentage points).
5. **Latency Overhead**: +19.79% penalty (8,564.89 ms vs. 7,149.68 ms).
6. **Store Deduplication**: Mode 4 invariant at 3 memories vs. Mode 3 expanding to 23.
7. **Pre-Execution Safety**: 0 destructive queries reaching PostgreSQL across 600 total evaluated runs.
8. **Temporal Decay Scope**: Mathematically implemented & unit-tested, but unexercised under the ~3.5-minute benchmark execution clock.

---

## 7. Exact Title to Use

**Canonical Title**:  
*Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*

*(Note: Use this single authoritative title throughout; do not alternate between title variants).*

---

## 8. Bibliography Status

- **Status**: 100% complete and verified.
- **Reference Count**: Exactly 26 references (`[1]` through `[26]`).
- **Composition**: 19 peer-reviewed publications, 3 academic preprints, 2 technical reports, 2 software specifications.
- **Traceability**: All citations mapped in `ARMG_Literature_Gaps.md` and `ARMG_IEEE_Reference_Metadata.md`. Zero placeholders remain.

---

## 9. Final Visual Asset List Summary

| Asset Category | Files Available | Status |
| :--- | :--- | :---: |
| Quantitative Figures | 6 PNGs (300 DPI) + 6 SVGs (Vector) + 6 Python Source Scripts | **COMPLETE** |
| LaTeX Floats | 9 `.tex` files under `manuscript/tables/` | **COMPLETE** |
| Manuscript Text Integration | `manuscript/ieee_manuscript.md` (all 6 figures + 9 tables embedded) | **COMPLETE** |
| Data Integrity Validation | Verified via `scripts/verify_data_integrity.py` (0 errors) | **COMPLETE** |
