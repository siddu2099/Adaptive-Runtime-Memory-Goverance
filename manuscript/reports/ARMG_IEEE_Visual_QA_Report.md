# ARMG IEEE Paper — Step 5: Visual Quality Assurance (QA) Report

**Date**: 2026-10-01  
**Status**: COMPLETE / VERIFIED  
**Target Publication**: IEEE Conference / Journal (2-column format)

---

## 1. Visual QA Methodology

Each rendered visual asset was audited against IEEE formatting guidelines and empirical accuracy standards:
1. **Column Width Adaptation**: Evaluated for readability at IEEE single-column width (3.5 inches / ~88 mm) and double-column span (7.0 inches / ~181 mm).
2. **Typography & Legibility**: Minimum font size $\ge 8\,\text{pt}$ at target scale. Standard clean sans-serif typography (`Arial` / `Helvetica` style fallback).
3. **No Embedded Captions**: Captions are excluded from image rasters and rendered exclusively via document/LaTeX typesetting.
4. **Grayscale & High-Contrast Discriminability**: Colors are selected with high luminance contrast, distinct line styles (solid, dashed, dotted), and diverse markers (circle, square, diamond, triangle) to ensure legibility when printed in monochrome grayscale.
5. **No Chartjunk**: Avoids 3D shapes, artificial shadows, decorative gradient fills, or extraneous gridlines.
6. **Empirical Traceability**: All data loaded directly from frozen benchmark CSVs and canonical evidence tables.

---

## 2. Visual QA Matrix

| Figure | Single Column | Two Column | Text Readability | Label Clipping | Legend | Scientific Correctness | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Figure 1**: End-to-End ARMG Architecture and Closed-Loop State Machine | Readable (as full workflow) | Recommended (span 2 cols) | Clean hierarchical boxes; node numbers 1–10; font $\ge 8.5\,\text{pt}$ | Zero clipping; Node 10 expanded to eliminate title/text overlap | Clear edge styles; condition labels explicit; unambiguous loopback | Canonical 10-node LangGraph state machine from `graph/workflow.py` | **PASSED** (Step 5.1 Verified) |
| **Figure 2**: ARMG Runtime Memory Lifecycle State Transition Machine | Highly readable | Excellent | State names in bold uppercase; equation thresholds annotated ($\ge 8\,\text{pt}$) | Zero clipping; state radii and bounding boxes spacious | Edge labels distinguish admission, penalty, reinforcement; zero collisions | Exact 6 lifecycle states from `memory/governance.py`; arrow directions strictly verified (NEW $\to$ ACTIVE forward, ARCHIVED $\to$ DELETED downward) | **PASSED** (Step 5.1 Verified) |
| **Figure 3**: Pre-Remediation vs. Post-Remediation FAISS Retrieval Geometry | Readable | Recommended (side-by-side panels) | Panel titles bold; threshold $\tau=0.50$ highlighted; annotations $\ge 8\,\text{pt}$ | Zero clipping; tight layout padding = 1.8 | Red dashed threshold line with clear legend | Exact pre-remediation score $S\approx 0.0035$ vs 16 normalized events across 12 queries | **PASSED** |
| **Figure 4**: PostgreSQL Execution Success vs. Relational Execution Accuracy | Highly readable | Excellent | Axis labels, mode ticks, and percentage annotations crisp | Zero clipping; y-limits $[0, 110\%]$ prevent bar top truncation | Paired bars (shaded ExecSucc vs hatched ExecAcc) | All 6 modes plotted from Table II; preserves 92% vs 68% and 96% vs 68% | **PASSED** (Step 5.1: Clean title) |
| **Figure 5**: Mode 2 vs. Full ARMG Operational Trade-Off Profile | Highly readable | Excellent | Metric delta labels explicitly distinguish relative $\%$ from $\text{pp}$ | Zero clipping; symmetric horizontal bar layout | Color-coded directional deltas with bold value callouts | Mode 4 vs Mode 2 trade-offs ($-34.38\%$, $-5.30\%$, $+4.00\,\text{pp}$, $+19.79\%$, $0.00\,\text{pp}$) | **PASSED** (Step 5.1: Clean title) |
| **Figure 6**: Persistent Memory Store Growth: Full ARMG vs. Naive Vector RAG | Highly readable | Excellent | Query IDs Q01–Q25 on x-axis; store size on y-axis; callout text bold | Zero clipping; annotations positioned above step curves | Step curves with distinct markers (circle vs square) and shaded plateau | Mode 4 invariant plateau at 3 memories; Mode 3 expansion to 23 memories | **PASSED** (Step 5.1: Clean title) |

---

## 3. Detailed Per-Figure Evaluation

### Figure 1: Architecture Topology (Step 5.1 Verified)
- **Source Script**: `manuscript/figures/source/fig1_architecture.py`
- **Output Files**: `manuscript/figures/png/fig1_architecture.png` (300 DPI, $3300 \times 1800$), `manuscript/figures/svg/fig1_architecture.svg`
- **Visual Structure**: 10 functional nodes arranged in closed-loop workflow:
  1. `introspect_and_prune_node` (Schema context)
  2. `memory_retrieval_node` (FAISS Unit-$L_2$ normalized retrieval)
  3. `sql_generator_node` (Qwen2.5 7B greedy decoding)
  4. `ast_guard_node` (Pre-execution AST containment)
  5. `postgres_executor_node` (PostgreSQL physical engine)
  6. `observation_node` (Raw error capture)
  7. `diagnosis_node` (7-tier deterministic error taxonomy)
  8. `knowledge_node` (Ephemeral `RuntimeKnowledge` artifact)
  9. `repair_prompt_node` (Bounded retry prompt, $K \le 3$, loopback to Node 3)
  10. `memory_governance_node` (Algorithmic mutual exclusion)
- **Step 5.1 QA Corrections**:
  - Node 10 box substantially widened and heightened ($W=18.0, H=9.0$, centered at $x=19.5, y=3.0$), completely resolving the cramped text and title overlap.
  - Divided Node 10 internally into two clear functional sub-panels: "Memory Reinforcement" and "Candidate Memory Admission".
  - Clean outer-perimeter repair loopback route ($x=1.5, y=-2.5 \to 3.5$) eliminating edge crossing and connector ambiguity.
  - Bounded retry condition label ($K \le 3$) and AST safety abort arrows validated against `graph/workflow.py`.

### Figure 2: Lifecycle State Transition Machine (Step 5.1 Verified)
- **Source Script**: `manuscript/figures/source/fig2_lifecycle.py`
- **Output Files**: `manuscript/figures/png/fig2_lifecycle.png` (300 DPI, $3300 \times 1950$), `manuscript/figures/svg/fig2_lifecycle.svg`
- **Visual Structure**: 6 state nodes in planar layout:
  - `NEW` ($C_0 = 0.50$, admission upon $\text{Utility}_0 \ge 0.25$)
  - `ACTIVE` ($C \ge 0.50$)
  - `STABLE` ($C \ge 0.80$, graduated via $\alpha = 0.10$)
  - `DECAYING` (continuous exponential decay $\lambda = 0.05/\text{day}$)
  - `ARCHIVED` ($C < 0.20$, demoted via $\beta = 0.15$ or decay)
  - `DELETED` ($C < 0.15$, terminal purge)
- **Step 5.1 QA Corrections**:
  - Arrow directions audited against `memory/governance.py`.
  - Fixed arrowhead direction from `NEW` to `ACTIVE` (forward admission transition pointing rightward).
  - Fixed arrowhead direction from `ARCHIVED` to `DELETED` (downward terminal purge transition pointing from ARCHIVED at $y=38$ down to DELETED at $y=22$).
  - Eliminated label collisions; clearly separated reinforcement loop from decay arcs.
  - Transparent callout emphasizing that continuous decay ($\lambda = 0.05/\text{day}$) is implemented and unit-tested but unexercised within the short ~3.5-minute sequential benchmark clock.

### Figure 3: FAISS Retrieval Geometry Remediation
- **Source Script**: `manuscript/figures/source/fig3_retrieval_geometry.py`
- **Output Files**: `manuscript/figures/png/fig3_retrieval_geometry.png` (300 DPI, $3300 \times 1650$), `manuscript/figures/svg/fig3_retrieval_geometry.svg`
- **Visual Structure**: Two-panel comparative plot:
  - Left Panel: Pre-Remediation (unnormalized embeddings, $\|\mathbf{v}\| \approx 19.8$, $d^2 \approx 280$, $S \approx 0.0035 \ll \tau = 0.50$, 0 retrievals).
  - Right Panel: Post-Remediation (Unit-$L_2$ normalized, inner-product geometry restored, 16 retrieval events across 12 queries, $48.0\%$ coverage).
- **QA Verification**: Threshold $\tau = 0.50$ displayed with prominent horizontal dashed line. Empirical counts match `benchmark/pre_remediation_results.csv` and `benchmark/seed42/benchmark_results.csv`.

### Figure 4: ExecSucc vs. ExecAcc Across Six Modes
- **Source Script**: `manuscript/figures/source/fig4_execsucc_execacc.py`
- **Output Files**: `manuscript/figures/png/fig4_execsucc_execacc.png` (300 DPI, $3300 \times 1800$), `manuscript/figures/svg/fig4_execsucc_execacc.svg`
- **Visual Structure**: Grouped bar chart plotting all 6 experimental modes:
  - Shaded steel blue bars: PostgreSQL Execution Success ($\text{ExecSucc}$)
  - Dark slate hatched bars: Relational Execution Accuracy ($\text{ExecAcc}$)
  - Numerical value annotations placed above each bar.
- **QA Verification**: Exact data matches Table II: Mode 1 (76.00% vs 57.33%), Mode 2 (92.00% vs 68.00%), Mode 3 (92.00% vs 68.00%), Mode 4 (96.00% vs 68.00%), Mode 5 (96.00% vs 68.00%), Mode 6 (94.67% vs 68.00%). Preserves central paper thesis regarding the execution-accuracy gap.

### Figure 5: Mode 2 vs. Full ARMG Trade-Off Profile
- **Source Script**: `manuscript/figures/source/fig5_tradeoff.py`
- **Output Files**: `manuscript/figures/png/fig5_tradeoff.png` (300 DPI, $3000 \times 1650$), `manuscript/figures/svg/fig5_tradeoff.svg`
- **Visual Structure**: Horizontal bar delta chart:
  - Retries: $-34.38\%$ (Relative %)
  - Tokens: $-5.30\%$ (Relative %)
  - PostgreSQL Exec Success: $+4.00\,\text{pp}$ (Percentage Points)
  - End-to-End Latency: $+19.79\%$ (Relative %)
  - Relational Accuracy: $0.00\,\text{pp}$ (Percentage Points)
- **QA Verification**: Mandatory distinction between relative percentage changes and percentage points strictly labeled. Value callouts centered and legible.

### Figure 6: Persistent Memory Store Growth
- **Source Script**: `manuscript/figures/source/fig6_memory_growth.py`
- **Output Files**: `manuscript/figures/png/fig6_memory_growth.png` (300 DPI, $3300 \times 1650$), `manuscript/figures/svg/fig6_memory_growth.svg`
- **Visual Structure**: Step curves across sequential queries Q01 through Q25:
  - Red dashed line with square markers: Mode 3 (Naive Vector RAG) accumulating to 23 memories.
  - Dark blue solid line with circular markers: Mode 4 (Full ARMG) plateauing at 3 memories.
  - Green shaded region: Invariant plateau spanning Q15 to Q25.
  - Annotations: Admission of Q04 (Store=1), Q13 (Store=2), Q15 (Store=3), and Reinforcement of Q17 (Store invariant at 3).
- **QA Verification**: Query-level values loaded directly from `seed42/benchmark_results.csv`. Demonstrates observed lifecycle deduplication without universal overclaims.

---

## 4. Final Visual QA Conclusion

All 6 figures and 9 tables pass all visual, scientific, and formatting checks:
- **Rendering Quality**: 300 DPI high-resolution PNG rasters and scalable vector SVGs generated for all 6 figures.
- **Reproducibility**: 100% of quantitative figures are generated from standalone, reproducible Python scripts.
- **Data Integrity**: Zero discrepancies across figures, tables, and frozen CSV data.
- **Visual Status**: **APPROVED FOR IEEE CAMERA-READY TYPESETTING**.
