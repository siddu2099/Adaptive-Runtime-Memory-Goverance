# ARMG IEEE Step 6.1: Template & Submission Blocker Report

**Date**: 2026-10-02  
**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Workflow Stage**: STEP 6.1 — Author Integration + Provisional IEEE Conference Package  
**Current Gate Status**: **STEP 6 PROVISIONAL PACKAGE COMPLETE — WAITING FOR OFFICIAL IEEE TEMPLATE / PDF COMPILATION**  

---

## 1. Executive Summary

In accordance with Section 2 ("Identify the Exact IEEE Template"), Section 5 ("Author Block"), and Section 19 ("PDF Compilation") of the IEEE Camera-Ready Formatting Specification, an exhaustive audit was performed across the repository and local environment.

Following the execution of Step 6.1:
- **Author Metadata**: **RESOLVED**. All 5 authors, affiliations, and contact emails were integrated into `manuscript/ieee_camera_ready.tex` without unauthorized metadata.
- **LaTeX Source**: **VALIDATED**. All 19 sections, 8 display equations, 6 figures, 9 tables, 26 references, and frozen scientific results pass automated verification with zero discrepancies (13/13 checks).
- **Remaining Blockers**: Final IEEE camera-ready certification remains gated on the provision of the official venue template files (`IEEEtran.cls`), specific venue confirmation, and external PDF compilation.

---

## 2. Forensic Search Records

### A. Template Files Searched
A recursive directory search across the entire repository root (`C:\Users\siddu\Pictures\armg main\`) confirmed:
- `IEEEtran.cls`: **NOT FOUND** in workspace.
- `IEEEtran.bst` / official IEEE bibliography styles: **NOT FOUND** in workspace.
- Official IEEE conference / journal template `.tex` files: **NOT FOUND** in workspace.
- Found existing `.tex` files: Only `manuscript/ieee_camera_ready.tex` and the 9 generated tables under `manuscript/tables/`.

### B. Target Venue Identification
- The target venue is provisionally configured for IEEE 2-column conference format (`\documentclass[conference]{IEEEtran}`).
- Specific venue identity (e.g., IEEE BigData, IEEE ICDE, IEEE TKDE) remains unconfirmed in project files.

### C. Author Metadata (Resolved in Step 6.1)
- Author block specified in Step 6.1 was integrated with exact fidelity:
  1. Inampudi Govardhana Rao (School of Computer Science and Engineering, `govardhanarao.i@vitap.ac.in`)
  2. Ghanta Sundar Siddhartha (B.Tech CSE Core, `siddharthaghanta10@gmail.com`)
  3. Sudarsanan Shilpa (B.Tech CSE Core, `shilpasudarsanan4@gmail.com`)
  4. Bommadevara S N V Datta Prasada Rayulu (B.Tech CSE Core, `dattabommadevara123@gmail.com`)
  5. Velpuri Danaiah (B.Tech CSE Core, `danaiahvelpuri78@gmail.com`)
- Placeholder tags (`[Author Names Withheld...]`) completely eliminated.

### D. Local Compilation Toolchain Search
- Local TeX engine status:
  - `pdflatex`: **NOT INSTALLED / NOT IN SYSTEM PATH** (exit code 1).
  - `latexmk`: **NOT INSTALLED / NOT IN SYSTEM PATH** (exit code 1).
  - `bibtex`: **NOT INSTALLED / NOT IN SYSTEM PATH** (exit code 1).

---

## 3. Remaining Blocker Analysis

| Blocker ID | Blocker Category | Root Cause | Impact on Submission | Action Required for Resolution |
| :---: | :--- | :--- | :--- | :--- |
| **BLK-01** | Missing Official Template | Neither `IEEEtran.cls` nor venue-specific support files exist in workspace. | Camera-ready typesetting cannot guarantee exact geometry, leading, or font metrics mandated by publisher. | Place official `IEEEtran.cls` in `manuscript/` or upload package to Overleaf IEEE Conference template. |
| **BLK-02** | Target Venue Unspecified | Publication venue (specific conference) is not confirmed. | Exact page limits (e.g., 6 pages vs. 8 pages) cannot be certified without knowing target venue. | Author/User specifies target conference venue. |
| **BLK-03** | Missing Local LaTeX Compiler | `pdflatex` / `bibtex` are not available in the local execution environment. | Physical PDF generation cannot execute locally without an external TeX distribution. | Compile `manuscript/ieee_camera_ready.tex` on a system with TeX Live / MiKTeX or Overleaf. |

---

## 4. Provisional LaTeX Source Status

The complete, publication-grade manuscript is maintained at:
- **File**: `manuscript/ieee_camera_ready.tex`
- **Label**: `% PROVISIONAL — NOT CAMERA-READY`
- **BibTeX**: `manuscript/references.bib` (26 verified entries)
- **Tables**: All 9 tables imported via `\input{tables/tableX_...tex}` with unique canonical labels.
- **Figures**: All 6 figures integrated with verified arrowheads, canonical captions, and clean titles.
- **Automated Validation**: `python scripts/verify_step6_format.py` (13/13 passed); `python scripts/verify_data_integrity.py` (10/10 passed).

---

## 5. Certification Status

**CURRENT WORKFLOW GATE STATUS**:  
**STEP 6 PROVISIONAL PACKAGE COMPLETE — WAITING FOR OFFICIAL IEEE TEMPLATE / PDF COMPILATION**
