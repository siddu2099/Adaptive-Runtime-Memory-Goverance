# ARMG Experiment Readiness & Empirical Gaps Specification

**Document Role**: Forensic Evaluation of Proposed Future Experiments & Empirical Scope  
**Target Manuscript**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md` (Section 26)  
**Status**: Authoritative Experimental Gap Analysis (No Experiments Executed in this Step)  
**Date**: October 2026  

---

## 1. Experimental Policy & Scope Boundaries

In accordance with strict research integrity standards:
1. **Zero New Experiments Executed**: No new experimental scripts, benchmark runs, or model queries were executed during this workflow step.
2. **Zero Modification of Frozen Evidence**: The frozen benchmark evidence package (`manuscript/evidence_package.md`) and raw benchmark CSV artifacts (`benchmark/seed*/benchmark_results.csv`) remain completely unaltered.
3. **Explicit Gap Acknowledgment**: Where empirical evidence is absent or unexercised, the manuscript transparently discloses the gap rather than asserting unverified claims.

This document provides a structured assessment of the five proposed future experimental extensions, specifying their research questions, implementation complexity, current evidentiary status, and publication priority.

---

## 2. Future Experiment Evaluation Matrix

### Experiment 1: Synthetic Epoch Advance Decay Experiment
- **Purpose**: To empirically exercise the continuous exponential decay equation ($C(t) = C_{\text{ref}} \exp(-\lambda \Delta t)$) and validate archival state transitions ($C < 0.20 \implies \text{ARCHIVED}$) across simulated operational lifecycles.
- **Research Question**: Does continuous exponential decay with $\lambda = 0.05/\text{day}$ successfully down-weight and archive unreinforced memories over multi-week operational intervals without degrading query repair accuracy?
- **Expected Scientific Value**: High. Transforms temporal utility decay from a mathematically implemented/unit-tested mechanism into an empirically validated runtime capability.
- **Whether Required for Current Paper**: **NO**. The current paper explicitly and transparently bounds its findings, stating: *"Temporal decay effectiveness was NOT demonstrated by this benchmark. Mode 6 functioned as a static no-decay control."* This disclosure fully satisfies IEEE technical reviewing standards.
- **Implementation Complexity**: Low–Medium. Requires augmenting `scripts/eval_runner.py` with an optional `--simulate-epochs` parameter that advances the synthetic timestamp by 30, 60, and 90 days between query batches.
- **Current Evidence Gap**: The benchmark executed all 25 queries within ~3.5 minutes ($\Delta t \approx 0.002$ days), resulting in $\exp(-\lambda \Delta t) \approx 0.9999$, leaving decay unexercised.
- **Recommended Priority**: **Priority 0 (P0)** — Highly recommended prior to a major IEEE Transactions journal submission (e.g., TKDE), but not a blocker for conference proceedings (e.g., ICDE short/demo track).

---

### Experiment 2: Counterfactual Memory Masking Intervention
- **Purpose**: To establish formal causal proof that memory retrieval directly drove Attempt-1 execution recovery for queries Q08 and Q19, rather than coincidental prompt stochasticity.
- **Research Question**: When retrieved operational memories for Q08 and Q19 are dynamically masked from the LLM prompt while holding all other inputs identical, does the model fail or incur higher repair iterations, proving causal memory attribution?
- **Expected Scientific Value**: High. Elevates the observed correlation between memory retrieval and repair reduction into rigorous causal counterfactual evidence.
- **Whether Required for Current Paper**: **NO**. The current manuscript explicitly describes this finding as an observational association: *"Memory retrieval was observationally associated with Attempt-1 execution on specific queries."* Causal claims have been completely removed.
- **Implementation Complexity**: Low. Requires an A/B ablation script running Q08 and Q19 with retrieved memory forced to null (`applied_memories = []`).
- **Current Evidence Gap**: Current data demonstrates correlation (Q08 and Q19 retrieved memories and executed on Attempt 1), but lacks a controlled counterfactual intervention.
- **Recommended Priority**: **Priority 0 (P0)** — Strengthens the causal argument for operational memory efficacy.

---

### Experiment 3: Frontier Model Scale Evaluation (70B+ Architectures)
- **Purpose**: To determine whether larger language models break the 68.00% relational semantic accuracy ceiling observed in the 7B model.
- **Research Question**: Does deploying ARMG with 70B+ parameter open-weights models (e.g., `Llama-3-70B`, `Qwen-2.5-72B`) resolve the complex window-function reasoning failures (`RANK() OVER`, `PARTITION BY`, cumulative frames) that caused the 7B model to plateau at 68.00% relational accuracy?
- **Expected Scientific Value**: High. Disentangles the contribution of memory governance from base model parameter capacity, testing the hypothesis that window-function errors are scale-bound emergent capabilities.
- **Whether Required for Current Paper**: **NO**. The paper explicitly scopes its evaluation to localized 7B open-weights deployments, a distinct and practical enterprise deployment category.
- **Implementation Complexity**: Medium. Requires multi-GPU infrastructure (e.g., 4x A100 or 2x H100) to host 70B models with Ollama/vLLM.
- **Current Evidence Gap**: Evaluated exclusively with `qwen2.5:7b-instruct` on a single local GPU workstation.
- **Recommended Priority**: **Priority 1 (P1)** — Valuable follow-up study for a full journal expansion.

---

### Experiment 4: Cross-Domain Public Benchmarks (Spider & BIRD)
- **Purpose**: To benchmark ARMG's repair efficiency and safety guardrails across hundreds of diverse, public cross-domain database schemas.
- **Research Question**: How does ARMG's operational memory governance perform across the 200 databases of Spider and the 95 dirty/noisy databases of BIRD compared to published literature leaders (DIN-SQL, MAC-SQL)?
- **Expected Scientific Value**: Very High for general Text-to-SQL ranking; Moderate for ARMG's core thesis. Spider and BIRD evaluate single-turn schema generalizability rather than multi-turn operational session memory over a single enterprise warehouse.
- **Whether Required for Current Paper**: **NO**. The manuscript explicitly explains this methodological choice in Section 9.1: ARMG evaluates multi-turn operational knowledge accumulation and lifecycle deduplication across an analytical session over a controlled warehouse, which cross-domain single-turn benchmarks are not structured to test.
- **Implementation Complexity**: High. Requires porting the 10-node LangGraph pipeline to execute across 200 SQLite databases and mapping SQLite error drivers to the 7-tier taxonomy.
- **Current Evidence Gap**: ARMG has been evaluated exclusively on the 4-table Star Schema warehouse.
- **Recommended Priority**: **Priority 1 (P1)** — Important for broad community adoption, but represents a different evaluation paradigm than session-based operational governance.

---

### Experiment 5: Concurrent Multi-User Throughput & Connection Pooling
- **Purpose**: To evaluate FAISS vector retrieval latency, SQLite memory database locking, and PostgreSQL connection pooling under concurrent multi-user load.
- **Research Question**: What is the saturation profile of ARMG's state graph when multiple parallel user sessions concurrently query, read, and admit memories into the vector store?
- **Expected Scientific Value**: Moderate–High. Addresses enterprise software systems performance.
- **Whether Required for Current Paper**: **NO**. The paper explicitly states that ARMG is evaluated under a single-user sequential query workload.
- **Implementation Complexity**: Medium. Requires writing an asynchronous locust/locust-style stress testing harness.
- **Current Evidence Gap**: Zero multi-threaded or multi-process throughput testing has been conducted.
- **Recommended Priority**: **Priority 2 (P2)** — Systems/engineering extension.

---

## 3. Summary of Current Manuscript Readiness

| Evaluation Area | Current Manuscript Status | Reviewer Impact | Recommended Action |
| :--- | :---: | :---: | :--- |
| **Temporal Utility Decay** | Explicitly framed as unexercised | Low Risk | No change needed; honest disclosure is peer-review compliant. |
| **Causal Memory Attribution** | Scoped to observational association | Low Risk | No change needed; prevents overclaiming critique. |
| **7B Parameter Scope** | Explicitly stated throughout | Low Risk | Accurately frames enterprise on-prem motivation. |
| **Star Schema Warehouse** | Explicitly characterized as synthetic benchmark | Low Risk | Clarified in Section 6 and 9.1. |
| **Single-User Workload** | Listed explicitly in Limitations (Section 16) | Low Risk | Methodological limitation disclosed. |

**Final Assessment**: The current manuscript [manuscript/ieee_manuscript.md](file:///c:/Users/siddu/Pictures/armg%20main/manuscript/ieee_manuscript.md) is scientifically sound, fully defensible, and methodologically honest without executing any new experiments. All empirical gaps are properly positioned as scoped limitations and prioritized future work.
