# ARMG IEEE Final Pre-Submission Scientific Audit

**Target File Audited**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md`  
**Frozen Evidence Package**: `manuscript/evidence_package.md`  
**Citation Verification Baseline**: `ARMG_Citation_Verification_Matrix.md`  
**Audit Standard**: Exhaustive Pre-Submission Reviewer-Grade Inspection (IEEE TKDE / ICDE Standards)  
**Date of Audit**: October 2026  
**Auditor**: Senior AI/ML Research Engineer & IEEE Senior Member / Peer Reviewer  

---

## 1. Executive Pre-Submission Audit Verdict

Following the complete integration of verified academic literature, replacement of all citation placeholders, and sentence-by-sentence reconciliation against the technical dossier, `manuscript/ieee_manuscript.md` was subjected to an exhaustive scientific pre-submission audit.

### Audit Summary:
- **Technical Inconsistencies**: **0** (All components, equations, algorithms, and taxonomy tiers match source code).
- **Numerical Inconsistencies**: **0** (All metrics match raw CSV artifacts and the frozen evidence package exactly).
- **Citation Inconsistencies**: **0** (All 26 citations are cited, verified, and mapped to permanent IEEE bibliography entries; zero orphan or placeholder citations remain).
- **Terminology Violations**: **0** (Relational Execution Accuracy and PostgreSQL Execution Success are strictly distinguished).
- **Overstated / Prohibited Claims**: **0** (All universal safety, universal memory poisoning, and semantic accuracy claims have been eliminated or evidence-bounded).

---

## 2. Category 1: Technical Consistency Audit

| Technical Component | Implementation Baseline (Code / Dossier) | Manuscript Representation | Audit Status | Evidence & Verification Notes |
| :--- | :--- | :--- | :---: | :--- |
| **StateGraph Node Count** | 10 functional nodes in `graph/workflow.py:88-160` | Described as a 10-node directed state graph in Abstract, Section 1, and Section 4 | **VERIFIED** | Matches LangGraph workflow compilation exactly. |
| **Exception Taxonomy** | 7-tier precedence taxonomy in `agents/taxonomy.py:11-34` | Formally detailed in Table I and Section 5.1 across Tiers 1 through 7 | **VERIFIED** | The outdated 5-class formulation has been 100% eliminated. |
| **Candidate Resolution** | Deterministic substring, token overlap, SequenceMatcher in `agents/error_diagnosis.py` | Fully detailed in Section 5.2 with exact heuristic scoring weights ($+10, +8, +4, +15$) | **VERIFIED** | Matches diagnostic candidate remapping implementation. |
| **RuntimeKnowledge Model** | Immutable Pydantic model in `memory/models.py:20-78` | Specified as immutable ephemeral artifact with exact field names in Section 5.3 | **VERIFIED** | Clearly states volatile metadata is stripped during embedding. |
| **Operational Utility Formula** | $\text{Utility} = C \times \text{SuccessRate} \times \text{ContextSim} \times \text{Recency}$ in `memory/governance.py:44-100` | Formalized as Equation in Section 6.1 with identical variable definitions | **VERIFIED** | Mathematically identical to code implementation. |
| **Admission Gating** | $\text{Utility}_0 \ge 0.25$ and terminal failure exclusion in `memory/governance.py:136-190` | Formalized in Section 6.2 ($\theta_{\text{admit}} = 0.25$) with terminal failure rejection invariant | **VERIFIED** | Replaces earlier incorrect claim of $\tau = 0.50$. |
| **Confidence Escalation** | $C_{t+1} = C_t + \alpha(1 - C_t)$, $\alpha = 0.10$ in `memory/governance.py:192-242` | Formalized in Section 6.3 with $\alpha = 0.10$ and state transitions (`NEW` $\to$ `ACTIVE` $\to$ `STABLE`) | **VERIFIED** | Matches asymptotic escalation equation. |
| **Failure Penalty** | $C_{t+1} = \max(0, C_t \times (1 - \beta))$, $\beta = 0.15$ in `memory/governance.py:244-292` | Formalized in Section 6.4 with $\beta = 0.15$ and archival threshold ($C < 0.20$) | **VERIFIED** | Matches multiplicative failure penalty equation. |
| **Temporal Utility Decay** | $C(t) = C_{\text{ref}} \exp(-\lambda \Delta t)$, $\lambda = 0.05/\text{day}$ in `memory/governance.py:294-339` | Formalized in Section 6.5 with explicit qualifier: "Mathematically Implemented; Unexercised in Benchmark" | **VERIFIED** | Mathematical formula matches; empirical limitation disclosed. |
| **Mutual Exclusion Invariant** | Reinforce if applied memory exists; Admit if applied memory empty & success in `graph/workflow.py:388-426` | Formalized as Equation in Section 6.6 with detailed invariant explanation | **VERIFIED** | Algorithmic invariant matches execution behavior. |
| **AST Guardrail Traversal** | SQLGlot single-statement check and 11 mutation types in `validation/execution_validator.py` | Detailed in Section 8 with explicit expression types and administrative tokens | **VERIFIED** | Matches AST visitor implementation. |
| **Repair Retry Budget** | $K_{\max} = 3$ (maximum generation attempts $\le 4$) in `agents/repair_agent.py` | Explicitly stated in Section 3 and Section 4 ($K_{\max} = 3$) | **VERIFIED** | Matches loop termination conditions. |
| **Vector Index & Threshold** | FAISS `IndexFlatL2(768)` with threshold $\tau = 0.50$ in `memory/vector_store.py` | Fully specified in Section 4, 6.1, and 9.1 | **VERIFIED** | Matches Unit-L2 normalized Euclidean geometry. |
| **Metric Definitions** | Distinction between $\text{ExecSucc}$ and $\text{ExecAcc}$ in `benchmark/equivalence.py` | Rigorously formalized in Section 3 and Section 9.3 ($\text{ExecAcc} \implies \text{ExecSucc}$) | **VERIFIED** | Eliminates metric conflation across the manuscript. |

---

## 3. Category 2: Experimental Consistency Audit

All numerical entries reported in Table II and in-text summaries were checked against raw CSV logs across Seeds 42, 123, 999:

```
===================================================================================================================================================
NUMERICAL CONSISTENCY VERIFICATION MATRIX (CANONICAL FROZEN EVIDENCE VS. MANUSCRIPT)
===================================================================================================================================================
Mode                                Metric                Canonical Value (Dossier / CSV)     Manuscript Text & Table II    Discrepancy / Status
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 1 (Zero-Shot)                  Relational ExecAcc    57.33% ± 2.31%                      57.33% ± 2.31%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    76.00% ± 0.00%                      76.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.00 ± 0.00                         0.00 ± 0.00                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     5,087.73 ± 210.33                   5,087.73 ± 210.33             0.00 ms  [EXACT MATCH]
                                    Mean Tokens           360.48 ± 0.48                       360.48 ± 0.48                 0.00     [EXACT MATCH]
                                    Store Size            0                                   0                             0        [EXACT MATCH]
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 2 (Stateless Self-Correction)  Relational ExecAcc    68.00% ± 0.00%                      68.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    92.00% ± 0.00%                      92.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.43 ± 0.02 (0.4267)                0.43 ± 0.02                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     7,149.68 ± 231.65                   7,149.68 ± 231.65             0.00 ms  [EXACT MATCH]
                                    Mean Tokens           572.72 ± 12.68                      572.72 ± 12.68                0.00     [EXACT MATCH]
                                    Store Size            0                                   0                             0        [EXACT MATCH]
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 3 (Naive Vector RAG)           Relational ExecAcc    68.00% ± 0.00%                      68.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    92.00% ± 0.00%                      92.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.00 ± 0.00                         0.00 ± 0.00                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     6,844.01 ± 56.90                    6,844.01 ± 56.90              0.00 ms  [EXACT MATCH]
                                    Mean Tokens           558.28 ± 0.00                       558.28 ± 0.00                 0.00     [EXACT MATCH]
                                    Store Size            23                                  23                            0        [EXACT MATCH]
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 4 (Full ARMG)                  Relational ExecAcc    68.00% ± 0.00%                      68.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    96.00% ± 0.00%                      96.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.28 ± 0.00 (0.2800)                0.28 ± 0.00                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     8,564.89 ± 103.16                   8,564.89 ± 103.16             0.00 ms  [EXACT MATCH]
                                    Mean Tokens           542.37 ± 0.02                       542.37 ± 0.02                 0.00     [EXACT MATCH]
                                    Store Size            3                                   3                             0        [EXACT MATCH]
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 5 (ARMG − Neg Constraints)     Relational ExecAcc    68.00% ± 0.00%                      68.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    96.00% ± 0.00%                      96.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.36 ± 0.00 (0.3600)                0.36 ± 0.00                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     8,941.28 ± 108.68                   8,941.28 ± 108.68             0.00 ms  [EXACT MATCH]
                                    Mean Tokens           553.93 ± 0.02                       553.93 ± 0.02                 0.00     [EXACT MATCH]
                                    Store Size            3                                   3                             0        [EXACT MATCH]
---------------------------------------------------------------------------------------------------------------------------------------------------
Mode 6 (ARMG with λ=0.0)            Relational ExecAcc    68.00% ± 0.00%                      68.00% ± 0.00%                0.00 pp  [EXACT MATCH]
                                    PostgreSQL Success    94.67% ± 2.31%                      94.67% ± 2.31%                0.00 pp  [EXACT MATCH]
                                    Mean Retries          0.37 ± 0.02 (0.3733)                0.37 ± 0.02                   0.00     [EXACT MATCH]
                                    Mean Latency (ms)     9,036.97 ± 178.55                   9,036.97 ± 178.55             0.00 ms  [EXACT MATCH]
                                    Mean Tokens           599.67 ± 13.94                      599.67 ± 13.94                0.00     [EXACT MATCH]
                                    Store Size            3                                   3                             0        [EXACT MATCH]
===================================================================================================================================================
```

### Calculated Deltas Verified:
- **Mean Retry Reduction (Mode 4 vs. Mode 2)**: $\frac{0.4267 - 0.2800}{0.4267} = 34.38\%$ reduction. **[VERIFIED]**
- **Token Expenditure Reduction (Mode 4 vs. Mode 2)**: $\frac{572.72 - 542.37}{572.72} = 5.30\%$ reduction. **[VERIFIED]**
- **PostgreSQL Execution Gain (Mode 4 vs. Mode 2)**: $96.00\% - 92.00\% = +4.00\text{ pp}$ (+4.35% relative). **[VERIFIED]**
- **Latency Overhead (Mode 4 vs. Mode 2)**: $\frac{8,564.89 - 7,149.68}{7,149.68} = +19.79\%$ overhead. **[VERIFIED]**
- **Relational Accuracy Change**: $68.00\% - 68.00\% = 0.00\text{ pp}$ (Identical 17/25 queries correct). **[VERIFIED]**

---

## 4. Category 3: Semantic Failure & Query-Level Divergence Audit

- **Total Queries Evaluated**: 25.
- **Mode 4 Executable Queries**: 24 of 25 queries ($96.00\%$).
- **Mode 4 Relationally Equivalent Queries**: 17 of 25 queries ($68.00\%$).
- **Divergent Queries Identified**: Exactly 7 queries (Q05, Q14, Q15, Q17, Q18, Q19, Q25).
- **Q05 Ordering Semantics**: The manuscript correctly explains that Q05 failed because gold SQL specified `ORDER BY t.calendar_quarter`; because ordering was present in gold SQL, `benchmark/equivalence.py` enforced strict positional sequence matching, which the unordered result set failed.
- **Mode 2 vs. Mode 4 Query-Level Differences**: Exactly 2 queries differed:
  - `Q08`: Mode 2 failed Attempt 1 (mean 0.67 retries); Mode 4 retrieved `mem-Q04` and executed on Attempt 1 without retries (`retries = 0`).
  - `Q19`: Mode 2 exhausted all retries and terminated with `is_success = False`; Mode 4 retrieved `mem-Q13` and executed cleanly on Attempt 1 (`is_success = True`).
- **Negative Constraints Ablation (Mode 4 vs. Mode 5)**: Retry delta (0.28 vs. 0.36) is accurately localized exclusively to Query `Q19` (0 retries with constraints vs. 2 retries without).

---

## 5. Category 4: Safety Claims & Containment Scope Audit

- **Prohibited Terminology Check**: A forensic search confirms zero occurrences of "universal security," "absolute safety," "guaranteed protection against all injection vectors," or "guarantees database security."
- **Approved Wording Verification**: The manuscript strictly employs evidence-bounded language: *"zero destructive SQL statements reached PostgreSQL in the evaluated benchmark and offline safety tests."*
- **Empirical Scope Audit**: Reports 600 total evaluated query executions (450 post-remediation evaluations + 150 historical baseline evaluations) and 18 unit tests in `tests/unit/test_safety_guard.py`.
- **Mechanism vs. Observation**: Explicitly separates the implemented mechanism (SQLGlot AST parsing, expression traversal, and state graph halt to `STATUS_BLOCKED`) from the observed empirical containment on the benchmark.

---

## 6. Category 5: Statistical Validity & Sampling Scope Audit

- **Sample Size Scoping**: The manuscript explicitly states: *"In an empirical evaluation across three isolated repeated benchmark executions ($n = 3$, comprising 450 total evaluated query runs across six experimental modes)..."*
- **Prohibited Terminology Check**: Zero occurrences of "$n=450$ independent random trials" or claims of inferential significance ($p < 0.05$).
- **Greedy Decoding & Stability**: Explicitly documents that greedy decoding (`temperature = 0.0`) was active and that `--seed` was not passed to Ollama API options.
- **Valid Inference Boundary**: The manuscript explicitly states that repeated runs assess **pipeline reproducibility, execution stability, and memory-state consistency**, and notes that reported figures represent descriptive empirical effect sizes.

---

## 7. Category 6: Memory Lifecycle & Deduplication Audit

- **Memory Counts Verified**: Naive Vector RAG (Mode 3) accumulated 23 unmanaged memories in 25 queries. Full ARMG (Mode 4) maintained store size invariant at exactly 3 memories from Q15 to Q25.
- **Algorithmic Invariant**: Explains that on Query Q17, `mem-Q13` was retrieved and reinforced, and mutual exclusion suppressed new memory admission.
- **Prohibited Claims Check**: Zero claims of "permanently eliminating vector database poisoning in general." Claims are strictly scoped to the evaluated Star Schema lifecycle.

---

## 8. Category 7: Temporal Utility Decay Audit

- **Empirical Status**: Explicitly annotated as: *"Mathematically Implemented & Unit-Tested; Experimentally Unexercised in Benchmark."*
- **Clock Reality Disclosed**: Discloses that the 25 benchmark queries execute within ~3.5 minutes ($\Delta t \approx 0.002$ days), resulting in $\exp(-\lambda \Delta t) \approx 0.9999$.
- **Ablation Interpretation**: Section 14.2 explicitly reports: *"Temporal decay effectiveness was NOT demonstrated by this benchmark. Mode 6 functioned as a static no-decay control."*

---

## 9. Category 8: Citation Integrity & Verification Audit

- **Placeholders Search**: Zero instances of `[REF`, `TODO`, `TBD` (outside of DOI strings), `citation needed`, or `unverified`.
- **Citation Total**: Exactly 26 verified references [1]–[26].
- **Orphan Reference Check**: Every reference listed in Section 20 is cited in the text.
- **Un-cited Entry Check**: Every in-text citation maps to a valid bibliography entry.
- **Peer-Reviewed Ratio**: 21 of 26 references (80.8%) are peer-reviewed conference or journal papers (NeurIPS, ICDE/PVLDB, ACL, EMNLP, COLING, UIST, ASE, TMLR, IEEE TBD). The remaining 5 references are official technical reports or software specifications (Qwen2.5, Nomic Embed, MemGPT, SQLGlot, LangGraph).

---

## 10. Category 9: Manuscript Structure & Logical Flow Audit

The manuscript follows standard IEEE Transactions structure with strict logical flow:
1. Title & Abstract $\to$ Scopes local LLM Text-to-SQL, operational memory, and honest trade-offs.
2. Section 1 (Introduction) $\to$ Four operational challenges, 9-part research gap, explicit contributions.
3. Section 2 (Related Work) $\to$ 3-part scholarly critique positioning ARMG against SOTA.
4. Section 3 (Problem Formulation) $\to$ Formal relational algebra, AST validation operator, ExecSucc vs ExecAcc.
5. Section 4 (Architecture) $\to$ 10-node StateGraph specification and component routing.
6. Section 5 (Diagnosis) $\to$ Table I, canonical 7-tier taxonomy, candidate resolution heuristics, RuntimeKnowledge.
7. Section 6 (Governance) $\to$ Equations 1–6 (Utility, Admission, Escalation, Penalty, Decay, Mutual Exclusion).
8. Section 7 (Repair) $\to$ Structured repair prompt assembly with negative constraints.
9. Section 8 (Safety) $\to$ SQLGlot AST guardrail and `STATUS_BLOCKED` containment.
10. Section 9 (Methodology) $\to$ Star Schema warehouse, 25 queries, greedy decoding, $n=3$ protocol, equivalence comparator.
11. Section 10 (Results) $\to$ Table II, Mode 4 vs Mode 2 trade-off analysis, Q08/Q19 query divergence.
12. Section 11 (Memory Analysis) $\to$ Vector geometry restoration, admissions/reinforcements, invariant store size at 3.
13. Section 12 (Safety Evaluation) $\to$ 600 evaluated runs, 18 unit tests, zero destructive statements.
14. Section 13 (Failure Analysis) $\to$ Table III, 7 divergent queries, Q05 ordering semantics, 7B window reasoning ceiling [26].
15. Section 14 (Ablations) $\to$ Negative constraints localized to Q19; temporal decay unexercised.
16. Section 15 (Discussion) $\to$ What improved, what did not improve (68% plateau), what it cost (+19.79% latency), what remains untested.
17. Section 16 (Limitations) $\to$ 9 canonical limitations.
18. Section 17 (Threats to Validity) $\to$ Internal, construct, external, statistical ($n=3$ descriptive scope), reproducibility.
19. Section 18 (Future Work) $\to$ Prioritized research extensions (P0, P1, P2).
20. Section 19 (Conclusion) $\to$ Evidence-bounded closing summary.
21. Section 20 (References) $\to$ 26 verified IEEE bibliography entries.

---

## 11. Category 10: IEEE Reviewer Risk Analysis

The manuscript was evaluated against 13 specific critical reviewer challenges:

| Risk Item | Reviewer Concern | Evidence / Ground Truth | Manuscript Treatment & Defensive Wording | Reviewer Risk Severity |
| :---: | :--- | :--- | :--- | :---: |
| **1. Novelty Positioning** | "Isn't this just LangChain RAG with self-correction?" | Implements code-first 7-tier taxonomy, mathematical admission gating, mutual exclusion deduplication, and AST pre-execution guardrail. | Section 1 and Section 2 explicitly distinguish ARMG's operational lifecycle and mathematical governance from standard RAG and conversational memory. | **LOW** |
| **2. Benchmark Size** | "Only 25 queries is too small for a general Text-to-SQL paper." | Fixed 25-query analytical benchmark evaluated across 6 modes and 3 repeated runs (450 runs). | Scoped as an operational reliability and lifecycle benchmark rather than broad multi-domain semantic parsing. Disclosed in Limitations (Section 16). | **MEDIUM** |
| **3. Synthetic Benchmark** | "Why evaluate on synthetic data instead of live production warehouses?" | Populated via deterministic NumPy `seed=42` with 2,000 facts modeling B2B tech transactions. | Explicitly characterized as a synthetically generated benchmark in Abstract, Section 6, 9.1, and 16. Never implies live production data. | **LOW** |
| **4. Single 7B Model** | "Findings are specific to Qwen-2.5-7B and do not generalize to frontier models." | Evaluated exclusively on `qwen2.5:7b-instruct` on local GPU workstation. | Scoped explicitly to on-premises enterprise local LLM deployments; acknowledged in Limitations (Section 16) and Future Work (Section 18). | **LOW** |
| **5. Repetition Sample Size** | "Three seeds ($n=3$) cannot prove statistical significance." | Evaluated under Seeds 42, 123, 999. | Explicitly discloses in Section 9.1 and Section 17 that results represent descriptive empirical effect sizes rather than inferential $p$-value hypothesis testing. | **LOW** |
| **6. Greedy Decoding** | "Temperature 0.0 eliminates sampling variance; seeds are redundant." | Hardcoded `temperature = 0.0`; seed not passed to Ollama. | Transparently explains in Section 9.1 and Section 17 that repeated runs evaluate pipeline reproducibility and memory-state consistency, not token sampling variance. | **LOW** |
| **7. Causal Memory Attribution** | "Did memory actually cause Attempt-1 success on Q08 and Q19?" | Memory retrieved and Attempt-1 executed, but counterfactual masking was not run. | Described as an observational association; causal claims are avoided; counterfactual intervention listed as Priority 0 future work. | **LOW** |
| **8. Unexercised Decay** | "Why include a decay equation if the benchmark clock didn't exercise it?" | Real-time clock ran for ~3.5 min ($\Delta t \approx 0.002$ days); factor was 0.9999. | Explicitly labeled as "Mathematically Implemented & Unit-Tested; Experimentally Unexercised in Benchmark" in Section 6.5 and 14.2. | **LOW** |
| **9. Lack of Spider/BIRD** | "Why not submit Spider or BIRD leaderboard scores?" | Spider and BIRD evaluate single-turn generalizability across 200/95 databases, not multi-turn operational memory sessions over a warehouse. | Explicitly contrasted in Section 9.1; explains that ARMG tests multi-turn operational session knowledge accumulation over a warehouse schema. | **MEDIUM** |
| **10. Latency Overhead** | "ARMG is 19.79% slower; this makes it worse than baseline." | Mode 4 latency is 8,564 ms vs. Mode 2's 7,149 ms (+19.79%). | Transparently reported in Abstract, Results, and Discussion as an architectural trade-off: trades wall-clock orchestration for repair efficiency and safety. | **LOW** |
| **11. Semantic Accuracy Plateau** | "ARMG didn't improve accuracy (68% vs 68%); what is the value?" | Relational accuracy plateaued at 68.00% across both Mode 2 and Mode 4. | Prominently reported; framed as a central finding that operational memory improves PostgreSQL execution success (92% to 96%) and repair efficiency, but cannot bridge 7B window reasoning limits. | **LOW** |
| **12. Safety Scope** | "AST parsing cannot prevent all SQL injection attacks (e.g. second-order)." | Intercepts single statements, 11 mutation types, and administrative keywords. | Bounded strictly to tested pre-execution AST containment on evaluated benchmark; universal security claims eliminated. | **LOW** |
| **13. ExecSucc vs. ExecAcc Mismatch** | "Execution success is misleading if queries return wrong data." | 96% execution success vs. 68% semantic accuracy. | Defined and contrasted in Section 3 and Section 13 (Table III); highlights the executable vs. relational gap as a major research contribution. | **LOW** |

---

## 12. Final Claim Control Matrix

| Claim in Revised Manuscript | Evidence Type | Scope of Claim | Concrete Evidence / Citation | Allowed? |
| :--- | :---: | :---: | :--- | :---: |
| "ARMG achieved verified pre-execution safety, preventing any destructive SQL statement from reaching PostgreSQL in the evaluated benchmark." | **VERIFIED** | Benchmark & Safety Test Suite | 0 destructive statements across 600 evaluations; 18 unit tests in `tests/unit/test_safety_guard.py`. | **YES** |
| "Mode 4 achieved an observed 34.38% reduction in mean repair iterations relative to stateless self-correction." | **OBSERVED** | Evaluated 25-query corpus ($n=3$) | Mean retries: 0.28 vs. 0.43 across Seeds 42, 123, 999 (`benchmark/seed*/benchmark_results.csv`). | **YES** |
| "Mode 4 consumed 5.30% fewer tokens per query relative to stateless self-correction." | **OBSERVED** | Evaluated 25-query corpus ($n=3$) | Mean tokens: 542.37 vs. 572.72 across Seeds 42, 123, 999. | **YES** |
| "PostgreSQL execution success improved from 92.00% to 96.00%." | **OBSERVED** | Evaluated 25-query corpus ($n=3$) | 24/25 vs. 23/25 queries executable across all three seeds. | **YES** |
| "ARMG incurred a 19.79% end-to-end latency penalty." | **OBSERVED** | Evaluated 25-query corpus ($n=3$) | Mean latency: 8,564.89 ms vs. 7,149.68 ms across Seeds 42, 123, 999. | **YES** |
| "Relational execution accuracy remained identical at 68.00% across both Mode 2 and Mode 4." | **VERIFIED** | Evaluated 25-query corpus ($n=3$) | 17/25 queries relationally equivalent across all three seeds. | **YES** |
| "Algorithmic mutual exclusion maintained store size strictly invariant at 3 memories from Q15 to Q25." | **VERIFIED** | Evaluated 25-query corpus ($n=3$) | Store size held at 3 memories; Q17 reinforced `mem-Q13` and suppressed new admission. | **YES** |
| "Unit-L2 normalization restored FAISS nearest-neighbor retrieval geometry above threshold $\tau = 0.50$." | **VERIFIED** | Evaluation Benchmark | 16 retrievals across 12 queries post-normalization vs. 0 retrievals pre-normalization. | **YES** |
| "Negative constraints were associated with fewer repair iterations in the evaluated ablation, with the observed difference localized to Q19." | **OBSERVED** | Ablation (Mode 4 vs. Mode 5) | Mode 4 (0 retries on Q19) vs. Mode 5 (2 retries on Q19); other queries identical. | **YES** |
| "Continuous exponential decay is mathematically implemented and unit-tested, but remained experimentally unexercised under the benchmark clock." | **IMPLEMENTED** | Codebase & Unit Test Suite | Code in `memory/governance.py:294-339`; unit tests pass; benchmark clock was ~3.5 min. | **YES** |
| "Operational memory does not overcome the baseline semantic window-function reasoning limitations of local 7B models." | **INFERENCE** | Evaluated 7B model setting | 4 of 7 semantic failures involved complex window clauses (`RANK`, `PARTITION BY`, `LAG`). | **YES** |
| "Prompt-based safety alignment is vulnerable to adversarial jailbreaks and prompt injection." | **LITERATURE-SUPPORTED** | Peer-Reviewed Literature | Documented in Wei et al. (NeurIPS 2023) [20] and Zou et al. (2023) [21]. | **YES** |

---

## 13. Remaining Blockers Before Formal Submission

While the manuscript is now **fully audited, technically consistent, and literature-verified**, the following items remain before formal submission to an IEEE conference or journal:

1. **LaTeX / IEEEtran Typesetting**: The manuscript is currently in standardized academic Markdown. It must be converted into standard two-column IEEEtran LaTeX format (`.tex`) with accompanying vector figures (`.eps` / `.pdf`).
2. **Figure Graphic Compilation**: Figures 1 through 6 (specified in `ARMG_IEEE_Final_Figure_Table_Requirements.md`) must be generated and compiled into high-resolution EPS/PDF vector format from existing frozen benchmark CSVs and repository code.
3. **Journal vs. Conference Decision**:
   - If submitting to an **IEEE Conference** (e.g., ICDE 2027 short/demo track): The current paper is **COMPLETE AND DEFICIT-FREE**.
   - If submitting to an **IEEE Transactions Journal** (e.g., IEEE TKDE): Executing Priority 0 experiments (Synthetic Epoch Advance Decay and Counterfactual Memory Masking, specified in `ARMG_Experiment_Readiness_and_Gaps.md`) will substantially elevate the experimental impact and pre-empt reviewer requests for temporal decay and causal validation.
