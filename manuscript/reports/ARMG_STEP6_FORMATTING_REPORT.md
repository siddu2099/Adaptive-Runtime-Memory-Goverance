# ARMG IEEE Step 6.1: Formatting Report

**Date**: 2026-10-02  
**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Workflow Stage**: STEP 6.1 — Author Integration + Provisional IEEE Conference Package  
**Document Status**: Provisional IEEE Conference Package Complete / Waiting for Official IEEE Template / Local Compiler  

---

## 1. Executive Metadata Summary

| Item | Specification / Value | Status |
| :--- | :--- | :---: |
| **1. Template Used** | IEEEtran Standard Document Class (`\documentclass[conference]{IEEEtran}`) | Provisional Base |
| **2. Venue / Publication Target** | Provisional IEEE 2-Column Conference Track (Specific Conference Unspecified) | Pending Target Venue Confirmation |
| **3. LaTeX Engine** | `pdflatex` (Target Standard Engine) | Missing in Local OS (Requires External TeX Live / Overleaf) |
| **4. Bibliography Engine** | `bibtex` (with `IEEEtran.bst` / `\bibliographystyle{IEEEtran}`) | Missing in Local OS (Requires External TeX Live / Overleaf) |
| **5. Source Manuscript** | `manuscript/ieee_manuscript.md` (588 lines, 19 sections) | Fully Converted |
| **6. Final LaTeX Source** | `manuscript/ieee_camera_ready.tex` (Labeled: PROVISIONAL --- NOT CAMERA-READY) | Generated & Validated |
| **7. Final Bibliography File** | `manuscript/references.bib` (26 verified entries) | Generated & Validated |
| **8. Figure Integration** | 6 Figures (300 DPI PNG rasters + SVG vector graphics) | Fully Integrated & Verified |
| **9. Table Integration** | 9 Tables (`tables/table1_taxonomy.tex` through `table9_failures.tex`) | Fully Integrated & Verified |
| **10. Author Block Status** | All 5 Canonical Authors Integrated Exactly per Step 6.1 Specification | **RESOLVED** |
| **11. Equation Conversion Status** | 8 Numbered IEEE Display Equations + Parameter Specifications | Fully Converted |
| **12. Citation Validation** | 26/26 Mutual Citation Resolution (Zero unreferenced / zero uncited) | 100% Resolved |
| **13. Compilation Result** | Local `pdflatex` not installed; compilation deferred to external build environment | Blocked Locally |
| **14. Warning Summary** | Zero LaTeX syntax errors, zero markdown artifacts, zero unescaped symbols | Verified via Automated QA |
| **15. Estimated Page Count** | Approximately 8--10 pages (Standard IEEE double-column typeset) | Estimated (Pre-Compilation) |
| **16. Unresolved Blockers** | 1. Official venue template (`IEEEtran.cls`), 2. Exact venue specification, 3. Local TeX compiler | 3 Blockers Recorded |

---

## 2. Author Block Integration (Step 6.1)

In strict accordance with Step 6.1 instructions, the placeholder author block in `manuscript/ieee_camera_ready.tex` was replaced with the exact 5-author specification:

```latex
\author{
\IEEEauthorblockN{Inampudi Govardhana Rao}
\IEEEauthorblockA{
School of Computer Science and Engineering\\
Email: govardhanarao.i@vitap.ac.in
}
\and
\IEEEauthorblockN{Ghanta Sundar Siddhartha}
\IEEEauthorblockA{
B.Tech CSE Core\\
Email: siddharthaghanta10@gmail.com
}
\and
\IEEEauthorblockN{Sudarsanan Shilpa}
\IEEEauthorblockA{
B.Tech CSE Core\\
Email: shilpasudarsanan4@gmail.com
}
\and
\IEEEauthorblockN{Bommadevara S N V Datta Prasada Rayulu}
\IEEEauthorblockA{
B.Tech CSE Core\\
Email: dattabommadevara123@gmail.com
}
\and
\IEEEauthorblockN{Velpuri Danaiah}
\IEEEauthorblockA{
B.Tech CSE Core\\
Email: danaiahvelpuri78@gmail.com
}
}
```

**Metadata Boundary Guardrails Upheld**:
- Zero additional affiliations added.
- Zero university names inferred or fabricated for authors 2--5.
- Zero departments inferred or fabricated for authors 2--5.
- Zero ORCIDs added.
- Zero corresponding-author labels added.
- Zero funding statements added.

---

## 3. Source Manuscript to LaTeX Conversion Details

The conversion of `manuscript/ieee_manuscript.md` into `manuscript/ieee_camera_ready.tex` adheres strictly to IEEE formatting guidelines:

### A. Title Unification
- **Authoritative Canonical Title**:
  > *Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*
- Verified identical title in LaTeX `\title{...}`, abstract header, and all project metadata files.

### B. Section Structure Mapping (All 19 Major Sections Preserved)
1. `\section{Introduction}`
2. `\section{Related Work}` (Subsections: A. Text-to-SQL and Self-Correction, B. Retrieval-Augmented Generation and Agent Memory, C. Database Safety and Guardrails)
3. `\section{Problem Formulation}` (Subsections: A. SQL Generation Task, B. Pre-Execution Static Safety Validation, C. Execution Environment Feedback, D. Bounded Runtime Repair Task, E. Distinction: PostgreSQL Execution Success vs. Relational Accuracy)
4. `\section{ARMG Architecture}` (Integrates Fig.~\ref{fig:architecture} as `figure*`)
5. `\section{Runtime Observation and Error Diagnosis}` (Subsections: A. The Canonical 7-Tier Exception Taxonomy with Table~\ref{tab:taxonomy}, B. Deterministic Candidate Resolution Heuristic, C. Ephemeral RuntimeKnowledge Representation)
6. `\section{Memory Governance and Lifecycle}` (Integrates Table~\ref{tab:governance_equations}, Subsections: A. Multi-Factor Operational Utility, B. Admission Control, C. Asymptotic Confidence Escalation, D. Multiplicative Failure Penalty, E. Continuous Exponential Temporal Decay, F. Algorithmic Mutual Exclusion Invariant, G. Runtime Memory Lifecycle State Machine with Fig.~\ref{fig:lifecycle})
7. `\section{Runtime-Guided Repair and Negative Constraints}`
8. `\section{Safety Enforcement}`
9. `\section{Experimental Methodology}` (Subsections: A. Evaluation Configuration with Table~\ref{tab:system_config}, Table~\ref{tab:schema}, Table~\ref{tab:query_corpus}, B. The Six Experimental Modes, C. Relational Equivalence Comparator Rules)
10. `\section{Experimental Results}` (Subsections: A. Comparative Empirical Results across Six Modes with Table~\ref{tab:results} and Fig.~\ref{fig:exec_gap}, B. Mode 4 vs. Mode 2 Performance Trade-Off Analysis with Table~\ref{tab:tradeoff} and Fig.~\ref{fig:tradeoff}, C. Query-Level Divergence Analysis)
11. `\section{Memory Retrieval and Lifecycle Analysis}` (Subsections: A. Remediation of Vector Geometry with Fig.~\ref{fig:retrieval_geometry}, B. Lifecycle Metrics and Deduplication with Fig.~\ref{fig:memory_growth})
12. `\section{Safety Evaluation}`
13. `\section{Semantic Failure Analysis}` (Integrates Table~\ref{tab:gap}, Subsections: A. Analysis of the 7 Divergent Queries in Mode 4 with Table~\ref{tab:divergent_queries}, B. Root Cause Interpretation & Model Scale Boundaries)
14. `\section{Ablation Analysis}` (Subsections: A. Negative Constraints Ablation, B. Temporal Decay Ablation)
15. `\section{Discussion}` (Subsections: A. What Improved, B. What Did Not Improve, C. Architectural Cost: Latency Overhead, D. What Remains Untested)
16. `\section{Limitations}`
17. `\section{Threats to Validity}`
18. `\section{Future Work}`
19. `\section{Conclusion}`

---

## 4. Mathematical Equations Conversion

All mathematical formulations were typeset in standard IEEE math mode:
1. **Operational Utility Equation**:
   $$\text{Utility} = C \times \text{SuccessRate} \times \text{ContextSimilarity} \times \text{Recency}$$
2. **Admission Gating Equation**:
   $$\text{Admit}(K) \iff \text{Utility}_0(K) \ge \theta_{\text{admit}} \quad (\theta_{\text{admit}} = 0.25)$$
3. **Asymptotic Confidence Escalation**:
   $$C_{t+1} = C_t + \alpha (1.0 - C_t) \quad (\alpha = 0.10)$$
4. **Multiplicative Failure Penalty**:
   $$C_{t+1} = \max(0.0, \, C_t \times (1.0 - \beta)) \quad (\beta = 0.15)$$
5. **Continuous Temporal Decay**:
   $$C(t) = C_{\text{ref}} \times \exp(-\lambda \Delta t) \quad (\lambda = 0.05\text{ day}^{-1})$$
6. **Algorithmic Mutual Exclusion Invariant**:
   $$\text{Action} = \begin{cases} \text{Reinforce}(M_{\text{applied}}), & \text{if } M_{\text{applied}} \neq \emptyset \\ \text{Admit}(K_{\text{new}}), & \text{if } M_{\text{applied}} = \emptyset \land \text{Success} \land \text{Retries} > 0 \\ \emptyset, & \text{otherwise} \end{cases}$$

---

## 5. Float Integration & Verification Matrix

### Figures (6 Figures)

| Asset ID | File Path | In-Text Cross Reference | LaTeX Float Type | Verified Arrowheads & Directions |
| :--- | :--- | :--- | :---: | :---: |
| **Figure 1** | `manuscript/figures/png/fig1_architecture.png` | `Fig.~\ref{fig:architecture}` | `figure*` (Page-width) | **PASSED** (Preflight check verified all arrow directions match `graph/workflow.py`; Node 10 expanded; perimeter feedback loop) |
| **Figure 2** | `manuscript/figures/png/fig2_lifecycle.png` | `Fig.~\ref{fig:lifecycle}` | `figure` (Single-column) | **PASSED** (Transitions audited against `memory/governance.py`: NEW $\to$ ACTIVE rightward, ARCHIVED $\to$ DELETED downward) |
| **Figure 3** | `manuscript/figures/png/fig3_retrieval_geometry.png` | `Fig.~\ref{fig:retrieval_geometry}` | `figure*` (Page-width) | **PASSED** (Pre vs Post remediation geometry) |
| **Figure 4** | `manuscript/figures/png/fig4_execsucc_execacc.png` | `Fig.~\ref{fig:exec_gap}` | `figure` (Single-column) | **PASSED** (Matches Table II data across all 6 modes) |
| **Figure 5** | `manuscript/figures/png/fig5_tradeoff.png` | `Fig.~\ref{fig:tradeoff}` | `figure` (Single-column) | **PASSED** (Distinguishes relative % from pp shifts) |
| **Figure 6** | `manuscript/figures/png/fig6_memory_growth.png` | `Fig.~\ref{fig:memory_growth}` | `figure` (Single-column) | **PASSED** (Mode 4 plateau strictly invariant at 3 memories vs Mode 3 growth to 23) |

### Tables (9 Tables)

| Table ID | File Path | In-Text Cross Reference | Canonical Label | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| **Table I** | `manuscript/tables/table1_taxonomy.tex` | `Table~\ref{tab:taxonomy}` | `tab:taxonomy` | **PASSED** |
| **Table II** | `manuscript/tables/table2_results.tex` | `Table~\ref{tab:results}` | `tab:results` | **PASSED** |
| **Table III** | `manuscript/tables/table3_gap.tex` | `Table~\ref{tab:gap}` | `tab:gap` | **PASSED** |
| **Table IV** | `manuscript/tables/table4_config.tex` | `Table~\ref{tab:system_config}` | `tab:system_config` | **PASSED** (Single unique occurrence) |
| **Table V** | `manuscript/tables/table5_schema.tex` | `Table~\ref{tab:schema}` | `tab:schema` | **PASSED** (Canonical 365/6/8/2000 schema) |
| **Table VI** | `manuscript/tables/table6_queries.tex` | `Table~\ref{tab:query_corpus}` | `tab:query_corpus` | **PASSED** (Canonical 5/8/6/6 query corpus) |
| **Table VII** | `manuscript/tables/table7_governance.tex` | `Table~\ref{tab:governance_equations}` | `tab:governance_equations` | **PASSED** |
| **Table VIII** | `manuscript/tables/table8_tradeoff.tex` | `Table~\ref{tab:tradeoff}` | `tab:tradeoff` | **PASSED** (Descriptive non-causal language) |
| **Table IX** | `manuscript/tables/table9_failures.tex` | `Table~\ref{tab:divergent_queries}` | `tab:divergent_queries` | **PASSED** |

---

## 6. Bibliographic & Citation Validation

- **File**: `manuscript/references.bib`
- **Total References**: Exactly 26 verified bibliographic entries (`[1]` through `[26]`).
- **Citation Key Audit**:
  - Every `\cite{...}` in `ieee_camera_ready.tex` maps to a verified entry in `references.bib`.
  - Every entry in `references.bib` is cited at least once in `ieee_camera_ready.tex`.
  - Zero orphan or uncited bibliography entries.
  - Zero placeholder citations (`[REF-*]`).
- **Bibliographic Classification**:
  - 19 Peer-Reviewed Publications (NeurIPS, VLDB, ACL, EMNLP, ICLR, COLING, UIST, ASE, IEEE TBD).
  - 3 Scholarly Preprints (Qwen2.5 Tech Report, MemGPT, Nomic Embed).
  - 2 Official Technical Reports / Specifications (TMLR 2022 Emergent Abilities, TMLR 2024 CoALA).
  - 2 Official Open-Source Software Specifications (SQLGlot, LangGraph).

---

## 7. Automated Formatting & Data Integrity Audits

1. Executed `scripts/verify_step6_format.py` (**13/13 Checks Passed**):
   - Check 1: Canonical Title Consistency $\to$ **PASSED**
   - Check 2: 19 Expected Major Sections $\to$ **PASSED**
   - Check 3: 6 Figures Present (PNG, SVG, Source) $\to$ **PASSED**
   - Check 4: 9 Tables Imported via `\input` $\to$ **PASSED**
   - Check 5: 9 Unique Table Labels $\to$ **PASSED**
   - Check 6: 26 Bibliography Entries & 100% Citation Mapping $\to$ **PASSED**
   - Check 7: Float Cross-References via `\ref` $\to$ **PASSED**
   - Check 8: Zero Markdown Syntax Artifacts $\to$ **PASSED**
   - Check 9: Zero Stale Schema Values $\to$ **PASSED**
   - Check 10: Zero Stale Query Distributions $\to$ **PASSED**
   - Check 11: LaTeX Syntax & Balanced Braces $\to$ **PASSED**
   - Check 12: Frozen Numerical Evidence Invariants $\to$ **PASSED**
   - Check 13: Author Block Verification (Step 6.1) $\to$ **PASSED**

2. Executed `scripts/verify_data_integrity.py` (**10/10 Checks Passed**):
   - Check 1: Table II vs. Frozen Evidence Package $\to$ **PASSED**
   - Check 2: Figure 4 data equals Table II $\to$ **PASSED**
   - Check 3: Table III equals Table II $\to$ **PASSED**
   - Check 4: Table VIII computed from Table II $\to$ **PASSED**
   - Check 5: Figure 5 deltas equal Table VIII $\to$ **PASSED**
   - Check 6: Figure 6 store progression matches CSVs $\to$ **PASSED**
   - Check 7: Table IX divergent queries agree with CSVs $\to$ **PASSED**
   - Check 8: Table V matches Star Schema specification $\to$ **PASSED**
   - Check 9: Table VI matches 5/8/6/6 query corpus $\to$ **PASSED**
   - Check 10: LaTeX tables sanitized with unique labels $\to$ **PASSED**

---

## 8. Remaining Blockers for Final Camera-Ready Certification

While author block metadata has been successfully resolved in Step 6.1, final IEEE camera-ready certification requires resolving the following 3 environment/venue prerequisites:
1. **Official Venue Template (`IEEEtran.cls`)**: An official, venue-certified class file must be placed in the workspace (or the specific IEEE conference target confirmed to accept standard IEEEtran conference styling).
2. **Exact Publication Venue Target**: Specific conference name (e.g., IEEE BigData 2026, IEEE ICDE 2026) must be identified to verify camera-ready page limits and specific front-matter requirements.
3. **Local TeX Compiler Toolchain**: The local host OS lacks `pdflatex` / `bibtex`. PDF compilation must occur via an external TeX environment (TeX Live, MiKTeX, Overleaf) using the validated package.

---

## 9. Final Gate Status

**STEP 6 PROVISIONAL PACKAGE COMPLETE — WAITING FOR OFFICIAL IEEE TEMPLATE / PDF COMPILATION**
