# ARMG IEEE Step 5.1: Pre-Formatting Scientific + Visual Correction Report

**Date**: 2026-10-01  
**Project**: Adaptive Runtime Memory Governance (ARMG)  
**Workflow Stage**: STEP 5.1 — Pre-Formatting Scientific + Visual Correction Gate  
**Status**: **STEP 5.1 COMPLETE — READY FOR STEP 6 IEEE CAMERA-READY FORMATTING**  

---

## Executive Summary

Step 5.1 served as a mandatory scientific and visual quality correction gate following Step 5. This forensic audit detected and corrected concrete inconsistencies between generated visual/tabular assets and the canonical ARMG technical baseline (`ARMG_IEEE_Paper_Revision_Dossier.md`, `manuscript/evidence_package.md`, `graph/workflow.py`, `memory/governance.py`, `db/schema.sql`, `scripts/seed_warehouse.py`, and `benchmark/queries.json`).

Zero benchmark experimental data, benchmark CSVs, repository source code, or hardware configurations were modified. All corrections strictly repaired formatting artifacts, graphical layout defects, mathematical transition directions, schema attributes, and query corpus distributions.

---

## A. Defects Found

1. **Table V Schema Specification Defect**:
   - Stale schema specifications contained non-canonical row counts and table/attribute names (`dim_geography = 50`, `dim_product = 100`, `fact_sales`, and `sales_id`).
   - The canonical synthetic warehouse implementation (`db/schema.sql` and `scripts/seed_warehouse.py`) actually instantiates 6 geographic zones, 8 products, 365 daily time records, and 2,000 fact records under `fact_sales_performance` (PK `fact_key`, FKs `time_key`, `geo_key`, `product_key`).

2. **Table VI Query Corpus Distribution Defect**:
   - Table VI reported an incorrect query distribution (Category A: 6, Category B: 7, Category C: 8, Category D: 4).
   - The canonical benchmark corpus (`benchmark/queries.json`) defines exactly 25 queries divided into:
     - Category A: Q01–Q05 (5 queries)
     - Category B: Q06–Q13 (8 queries)
     - Category C: Q14–Q19 (6 queries)
     - Category D: Q20–Q25 (6 queries)

3. **LaTeX Table Syntax & Embedded Markdown**:
   - Table headers in earlier drafts contained markdown bold asterisks embedded in LaTeX commands (e.g., `\textbf{**Tier**}`).
   - Tables required validation for IEEEtran compilation compatibility (proper environments, escaping of `_` and `%`, balanced braces).

4. **Duplicate Table Detection**:
   - Table IV required verification that only a single instance of `\label{tab:system_config}` exists and that no duplicated table floats persist.

5. **Figure 1 Graphical Overlap & Connector Routing**:
   - In `manuscript/figures/source/fig1_architecture.py`, Node 10 (`memory_governance_node`) was horizontally constricted ($W=11.0, H=2.8$), causing title text and explanatory bullet points to overlap and become unreadable.
   - The repair loopback route crossed edge boundaries, creating visual connector ambiguity.

6. **Figure 2 Lifecycle State Machine Arrow Direction Inconsistencies**:
   - In `manuscript/figures/source/fig2_lifecycle.py`, Matplotlib `annotate()` parameter ordering (`xy` vs. `xytext`) resulted in potentially inverted arrow directions:
     - The terminal purge transition between `ARCHIVED` and `DELETED` pointed upward towards `ARCHIVED` instead of downward to `DELETED`.
     - The admission transition between `NEW` and `ACTIVE` required clear forward directionality.
   - Text label positions overlapped near state transition arcs.

7. **Figure 3–6 Raster Title Formatting**:
   - Figure image rasters in Figures 4, 5, and 6 contained embedded "Figure X:" prefixes in the matplotlib axes title string, conflicting with IEEE publication standards where captions are typeset externally.

8. **Title and Interpretation Language Inconsistencies**:
   - The manuscript and handoff documents contained alternative title proposals rather than a single unified title.
   - Table VIII interpretation required strictly descriptive empirical wording rather than causal claims regarding 7B model size.

---

## B. Defects Corrected

1. **Table V Corrected**:
   - Updated `manuscript/tables/generate_tables.py`, `manuscript/tables/table5_schema.tex`, and `manuscript/ieee_manuscript.md`.
   - Exact canonical schema enforced:
     - `dim_time`: 365 daily rows, PK `time_key`
     - `dim_geography`: 6 geographic zones, PK `geo_key`
     - `dim_product`: 8 products, PK `product_key`
     - `fact_sales_performance`: 2,000 transaction records, PK `fact_key`, FKs `time_key`, `geo_key`, `product_key`
   - Verified zero occurrences of stale values (50, 100, `sales_id`, `fact_sales` alone).

2. **Table VI Corrected**:
   - Updated `manuscript/tables/generate_tables.py`, `manuscript/tables/table6_queries.tex`, and `manuscript/ieee_manuscript.md`.
   - Enforced exact 5/8/6/6 corpus complexity distribution:
     - Category A (Simple aggregations/groupings): Q01–Q05 (5 queries)
     - Category B (Multi-table analytical joins): Q06–Q13 (8 queries)
     - Category C (Advanced window functions): Q14–Q19 (6 queries)
     - Category D (Semantic/schema trap queries): Q20–Q25 (6 queries)
     - Total Corpus: Q01–Q25 (25 queries)

3. **LaTeX Table Sanitization**:
   - Sanitized all 9 `.tex` files in `manuscript/tables/`.
   - Converted all `\textbf{**...**}` into clean `\textbf{...}`.
   - Verified that braces `{}` are 100% balanced across all files.
   - Escaped all underscores (`\_`) and percentages (`\%`).
   - Ensured valid `table` and `table*` float environments.

4. **Duplicate Table Validation**:
   - Confirmed exactly 9 tables exist (Table I through Table IX).
   - Confirmed unique labels across all tables:
     - `\label{tab:taxonomy}` (Table I)
     - `\label{tab:results}` (Table II)
     - `\label{tab:gap}` (Table III)
     - `\label{tab:system_config}` (Table IV — unique, 0 duplicates)
     - `\label{tab:schema}` (Table V)
     - `\label{tab:query_corpus}` (Table VI)
     - `\label{tab:governance_equations}` (Table VII)
     - `\label{tab:tradeoff}` (Table VIII)
     - `\label{tab:divergent_queries}` (Table IX)

5. **Figure 1 Re-Engineered**:
   - Redesigned `manuscript/figures/source/fig1_architecture.py`.
   - Preserved canonical 10-node topology from `graph/workflow.py`.
   - Expanded Node 10 (`memory_governance_node`) bounding dimensions to $W=18.0, H=9.0$, centered at $(19.5, 3.0)$.
   - Subdivided Node 10 internally into two clear functional sub-panels: "Memory Reinforcement" and "Candidate Memory Admission".
   - Routed the repair loopback connector along an external perimeter path ($x=1.5, y=-2.5 \to 3.5$) with zero edge crossings.
   - Re-rendered `manuscript/figures/png/fig1_architecture.png` (300 DPI) and `manuscript/figures/svg/fig1_architecture.svg`.

6. **Figure 2 Transition Directions Verified & Re-Engineered**:
   - Audited `memory/governance.py` for mathematical state transitions.
   - Corrected arrow directions in `manuscript/figures/source/fig2_lifecycle.py`:
     - `NEW` $\to$ `ACTIVE`: Arrowhead points forward (rightward) upon admission ($\text{Utility}_0 \ge 0.25$).
     - `ARCHIVED` $\to$ `DELETED`: Arrowhead points downward from ARCHIVED ($y=38$) down to DELETED ($y=22$) upon terminal purge ($C < 0.15$).
     - `ACTIVE` $\to$ `ARCHIVED`: Multiplicative penalty demotion ($\beta = 0.15$) points downward.
     - `ACTIVE` $\to$ `STABLE`: Asymptotic confidence escalation ($\alpha = 0.10, C \ge 0.80$) points upward.
   - Repositioned text labels to eliminate all collisions.
   - Preserved explicit callout regarding continuous exponential decay ($\lambda = 0.05/\text{day}$) being unexercised under the ~3.5-minute sequential benchmark clock.
   - Re-rendered `manuscript/figures/png/fig2_lifecycle.png` (300 DPI) and `manuscript/figures/svg/fig2_lifecycle.svg`.

7. **Figures 3–6 Titles Cleaned**:
   - Removed embedded "Figure X:" prefixes from image title strings in `fig4_execsucc_execacc.py`, `fig5_tradeoff.py`, and `fig6_memory_growth.py`.
   - Re-rendered all PNG rasters (300 DPI) and vector SVGs.

8. **Title and Non-Causal Language Unified**:
   - Standardized single authoritative title across all files:
     *Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*
   - Table VIII interpretation updated to descriptive empirical language:
     "Observed identical relational execution accuracy in the evaluated benchmark."
   - Eliminated unsupported causal statements attributing parity directly to model scale.

---

## C. Files Modified

| File Path | Description of Modifications |
| :--- | :--- |
| `manuscript/tables/generate_tables.py` | Updated Table V (6/8/2000 schema), Table VI (5/8/6/6 corpus), and Table VIII non-causal phrasing. |
| `manuscript/tables/table5_schema.tex` | Regenerated with canonical Star Schema (365, 6, 8, 2000 rows; correct keys). |
| `manuscript/tables/table6_queries.tex` | Regenerated with canonical 5/8/6/6 corpus distribution across 25 queries. |
| `manuscript/tables/table8_tradeoff.tex` | Regenerated with descriptive non-causal empirical phrasing. |
| `manuscript/figures/source/fig1_architecture.py` | Expanded Node 10 box ($W=18.0, H=9.0$), resolved text overlap, perimeter loopback routing. |
| `manuscript/figures/source/fig2_lifecycle.py` | Fixed transition arrow directions (NEW $\to$ ACTIVE, ARCHIVED $\to$ DELETED), resolved label collisions. |
| `manuscript/figures/source/fig4_execsucc_execacc.py` | Removed embedded "Figure 4:" prefix from plot title string. |
| `manuscript/figures/source/fig5_tradeoff.py` | Removed embedded "Figure 5:" prefix from plot title string. |
| `manuscript/figures/source/fig6_memory_growth.py` | Removed embedded "Figure 6:" prefix from plot title string. |
| `manuscript/figures/png/*.png` (6 files) | Re-rendered high-resolution 300 DPI rasters. |
| `manuscript/figures/svg/*.svg` (6 files) | Re-rendered scalable vector graphics. |
| `manuscript/ieee_manuscript.md` | Standardized canonical title, updated embedded Table V and Table VI, updated Table VIII text, verified non-causal prose. |
| `scripts/verify_data_integrity.py` | Added Checks 8, 9, 10 validating Table V schema, Table VI corpus, and LaTeX table syntax. |
| `ARMG_IEEE_Visual_Asset_Manifest.md` | Updated asset catalog with Step 5.1 metadata and verified status. |
| `ARMG_IEEE_Visual_QA_Report.md` | Updated QA matrix and detailed evaluations with Step 5.1 visual and direction audits. |
| `ARMG_IEEE_STEP6_FORMATTING_HANDOFF.md` | Enforced single canonical title, updated Table V and Table VI mapping descriptions. |
| `ARMG_IEEE_Revision_Change_Log.md` | Appended Section 7 documenting Step 5.1 correction gate. |

---

## D. Numerical Consistency Checks

All numerical data across figures, tables, and manuscript prose were audited and verified against the canonical frozen evidence:

1. **Table II / Figure 4**:
   - Mode 1: ExecSucc = $76.00\%$, ExecAcc = $57.33\%$, Retries = $0.00$, Latency = $5,087.73\,\text{ms}$, Tokens = $360.48$, Store = $0$.
   - Mode 2: ExecSucc = $92.00\%$, ExecAcc = $68.00\%$, Retries = $0.43$, Latency = $7,149.68\,\text{ms}$, Tokens = $572.72$, Store = $0$.
   - Mode 3: ExecSucc = $92.00\%$, ExecAcc = $68.00\%$, Retries = $0.00$, Latency = $6,844.01\,\text{ms}$, Tokens = $558.28$, Store = $23$.
   - Mode 4: ExecSucc = $96.00\%$, ExecAcc = $68.00\%$, Retries = $0.28$, Latency = $8,564.89\,\text{ms}$, Tokens = $542.37$, Store = $3$.
   - Mode 5: ExecSucc = $96.00\%$, ExecAcc = $68.00\%$, Retries = $0.36$, Latency = $8,941.28\,\text{ms}$, Tokens = $553.93$, Store = $3$.
   - Mode 6: ExecSucc = $94.67\%$, ExecAcc = $68.00\%$, Retries = $0.37$, Latency = $9,036.97\,\text{ms}$, Tokens = $599.67$, Store = $3$.

2. **Table VIII / Figure 5**:
   - Mean Repair Retries: Mode 2 ($0.43$) vs. Mode 4 ($0.28$) $\to$ Delta = $-0.15$ retries ($-34.38\%$ relative).
   - Token Expenditure: Mode 2 ($572.72$) vs. Mode 4 ($542.37$) $\to$ Delta = $-30.35$ tokens ($-5.30\%$ relative).
   - PostgreSQL Execution Success: Mode 2 ($92.00\%$) vs. Mode 4 ($96.00\%$) $\to$ Delta = $+4.00\,\text{pp}$ ($+4.35\%$ relative).
   - End-to-End Latency: Mode 2 ($7,149.68\,\text{ms}$) vs. Mode 4 ($8,564.89\,\text{ms}$) $\to$ Delta = $+1,415.21\,\text{ms}$ ($+19.79\%$ relative).
   - Relational Semantic Accuracy: Mode 2 ($68.00\%$) vs. Mode 4 ($68.00\%$) $\to$ Delta = $0.00\,\text{pp}$ ($0.00\%$ relative).
   - Strict distinction between percentage points ($\text{pp}$) and relative percentages ($\%$) verified.

3. **Figure 6**:
   - Mode 4: Q04 admission (Store = 1), Q13 admission (Store = 2), Q15 admission (Store = 3), Q17 reinforcement (Store = 3), Q15–Q25 invariant plateau at 3.
   - Mode 3: Monotonic uncontrolled expansion reaching 23 memories at Q25.

4. **Figure 3**:
   - Pre-remediation: Unnormalized embedding norm $\|\mathbf{v}\| \approx 19.8$, score $S \approx 0.0035 \ll \tau = 0.50$, zero retrievals.
   - Post-remediation: Unit-$L_2$ normalized inner-product geometry, 16 retrieval events across 12 distinct queries ($48.0\%$ coverage).

5. **Table V**:
   - `dim_time`: 365 daily rows.
   - `dim_geography`: 6 geographic zones.
   - `dim_product`: 8 products.
   - `fact_sales_performance`: 2,000 transaction records.

6. **Table VI**:
   - Category A: 5 queries.
   - Category B: 8 queries.
   - Category C: 6 queries.
   - Category D: 6 queries.
   - Total: 25 queries.

---

## E. Figure-Direction Validation

| Figure | Component / Transition | Verified Source Implementation | Direction Audited & Confirmed |
| :--- | :--- | :--- | :--- |
| **Figure 1** | Node 1 $\to$ Node 2 | `graph/workflow.py` (`START` $\to$ `introspect_and_prune` $\to$ `memory_retrieval`) | Forward directed edge |
| **Figure 1** | Node 4 (AST Guard) $\to$ Terminal Abort | `graph/workflow.py` (`ast_guard_node` blocks destructive statements) | Conditional abort arrow to Node 10 without DB execution |
| **Figure 1** | Node 9 $\to$ Node 3 (Bounded Repair Loop) | `graph/workflow.py` (`repair_prompt` loops to `sql_generator` if $K \le 3$) | Upward perimeter loopback routing ($x=1.5, y=-2.5 \to 3.5$) |
| **Figure 1** | Terminal Execution $\to$ Node 10 | `graph/workflow.py` (Success or Exceeded Retries $\to$ `memory_governance`) | Inward directed arrows to Node 10 |
| **Figure 2** | `NEW` $\to$ `ACTIVE` | `memory/governance.py` (`admit_memory()` when $\text{Utility}_0 \ge 0.25$) | **Forward rightward arrow** pointing to `ACTIVE` |
| **Figure 2** | `ACTIVE` $\to$ `STABLE` | `memory/governance.py` (Reinforcement: $C \leftarrow C + \alpha(1-C)$, $C \ge 0.80$) | Upward progression arrow |
| **Figure 2** | `ACTIVE` $\to$ `ARCHIVED` | `memory/governance.py` (Penalty: $C \leftarrow C \cdot (1-\beta)$, $C < 0.20$) | Downward demotion arrow |
| **Figure 2** | `ARCHIVED` $\to$ `DELETED` | `memory/governance.py` (Terminal prune when $C < 0.15$) | **Downward terminal purge arrow** pointing from `ARCHIVED` to `DELETED` |
| **Figure 2** | `ACTIVE` / `STABLE` $\to$ `DECAYING` | `memory/governance.py` (Continuous exponential decay $\lambda = 0.05/\text{day}$) | Directed rightward arcs into `DECAYING` |

---

## F. LaTeX Syntax Validation

All 9 `.tex` files in `manuscript/tables/` were audited against LaTeX standards for IEEEtran compatibility:
- **Markdown Asterisks**: Exactly 0 occurrences of `**` found across all `.tex` files.
- **Brace Balancing**: Braces `{` and `}` are strictly matched and balanced across all 9 files.
- **Character Escaping**: Underscores (`\_`) and percent symbols (`\%`) are escaped in text mode.
- **Math Mode**: Math formulas use explicit `$` delimiters (e.g., `$n = 3$`, `$\text{pp}$`, `$K \le 3$`).
- **Float Enclosing**: All tables are wrapped in standard `\begin{table}[h] ... \end{table}` or `\begin{table*}[t] ... \end{table*}` environments with `\centering`, `\caption{...}`, and `\label{...}`.

---

## G. Duplicate Table Validation

A comprehensive scan of `manuscript/tables/*.tex` and `manuscript/ieee_manuscript.md` confirmed:
- Exactly 9 tables exist: Table I through Table IX.
- Exactly 9 unique labels exist:
  1. `tab:taxonomy`
  2. `tab:results`
  3. `tab:gap`
  4. `tab:system_config` (Verified single occurrence; zero duplicate Table IV content)
  5. `tab:schema`
  6. `tab:query_corpus`
  7. `tab:governance_equations`
  8. `tab:tradeoff`
  9. `tab:divergent_queries`

---

## H. Manuscript Consistency Validation

An end-to-end consistency audit across `manuscript/ieee_manuscript.md` confirmed:
- **Canonical Title**: Uniformly set to:  
  *Adaptive Runtime Memory Governance: Closed-Loop Operational Knowledge Extraction, Repair Efficiency, and Execution Safety in Local Text-to-SQL Systems*
- **Warehouse Schema References**: 4 tables, 365 daily rows, 6 geographic zones, 8 products, 2,000 fact rows (`fact_sales_performance`).
- **Corpus References**: 25 queries, 5/8/6/6 category distribution.
- **Safety Evaluation Count**: 450 post-remediation runs, 150 historical baseline evaluations, 600 total evaluated safety runs.
- **Decoding Configuration**: Greedy decoding (`temperature = 0.0`, `top_p = 1.0`), seeds represent execution replication across identical deterministic queries, not stochastic model sampling.
- **Non-Causal Framing**: Parity across Modes 2–6 framed as an empirical observation in this benchmark rather than a causal proof regarding model capacity.
- **Bibliography Classification**: 26 verified references (19 peer-reviewed publications, 3 scholarly preprints, 2 official technical reports, 2 software specifications). Zero placeholder references.

---

## I. Automated Data Integrity Script Output

```
======================================================================
PHASE 9: AUTOMATED DATA INTEGRITY CHECK
======================================================================

[CHECK 1] Table II vs. Frozen Evidence Package...
  -> PASSED: Table II LaTeX matches frozen evidence package exactly.

[CHECK 2] Figure 4 data equals Table II...
  -> PASSED: Figure 4 data equals Table II exactly across all 6 modes.

[CHECK 3] Table III equals Table II...
  -> PASSED: Table III values and gaps equal Table II exactly across all 6 modes.

[CHECK 4] Table VIII computed from Table II...
  -> PASSED: Table VIII values (-34.38%, -5.30%, +4.00 pp, +19.79%, 0.00 pp) strictly match Table II.

[CHECK 5] Figure 5 deltas equal Table VIII...
  -> PASSED: Figure 5 deltas strictly equal Table VIII.

[CHECK 6] Figure 6 values equal benchmark CSVs...
  -> PASSED: Figure 6 store progression (Mode 4 plateau at 3, Mode 3 reaching 23) strictly matches benchmark CSVs.

[CHECK 7] Table IX agrees with frozen query analysis...
  -> PASSED: Table IX divergent queries (Q05, Q14, Q15, Q17, Q18, Q19, Q25) strictly agree with benchmark CSVs.

[CHECK 8] Table V Canonical Schema Specification...
  -> PASSED: Table V strictly matches canonical Star Schema (365, 6, 8, 2000 rows; time_key, geo_key, product_key, fact_key).

[CHECK 9] Table VI Canonical Query Corpus Distribution...
  -> PASSED: Table VI strictly matches canonical 5/8/6/6 corpus distribution (total 25 queries).

[CHECK 10] LaTeX Tables Sanitization and Unique Labels...
  -> PASSED: All 9 LaTeX tables sanitized with zero markdown syntax, balanced braces, and unique labels.

======================================================================
ALL 10 AUTOMATED DATA INTEGRITY CHECKS PASSED WITH ZERO DISCREPANCIES!
======================================================================
```

---

## J. Remaining Blockers

**Zero blockers remain for Step 6.**

All visual figures (PNG/SVG), LaTeX table floats, manuscript markdown tables, and empirical cross-references have passed full forensic validation.

---

## Final Gate Verification

- [x] Table V matches canonical 6/8/2000 schema
- [x] Table VI matches canonical 5/8/6/6 corpus
- [x] No duplicate tables (single `tab:system_config`)
- [x] No Markdown syntax inside LaTeX tables
- [x] Figure 1 topology and arrows verified against `graph/workflow.py` (Node 10 expanded, zero overlap)
- [x] Figure 2 lifecycle arrows verified against `memory/governance.py` (NEW $\to$ ACTIVE, ARCHIVED $\to$ DELETED)
- [x] Figures 3–6 match frozen evidence with clean titles
- [x] Title is consistent across all documents
- [x] No stale numerical values remain
- [x] No unsupported causal claims introduced
- [x] Integrity verification (`scripts/verify_data_integrity.py`) passes 10/10 checks

**FINAL STATUS**:  
**STEP 5.1 COMPLETE — READY FOR STEP 6 IEEE CAMERA-READY FORMATTING**
