# ARMG IEEE Experiment Gap Register (Step 4)

**Document Role**: Forensic Evaluation of Empirical Boundaries & Proposed Follow-Up Experiments  
**Target Manuscript**: `manuscript/ieee_manuscript.md`  
**Master Technical Baseline**: `ARMG_IEEE_Paper_Revision_Dossier.md` (Sections 24, 26)  
**Policy**: ZERO New Experiments Performed in this Step; All Frozen Evidence Strictly Preserved  
**Date**: October 2026  
**Auditor**: Senior AI/ML Research Engineer & IEEE Technical Reviewer  

---

## 1. Experimental Policy & Verification Principle

In accordance with strict scientific integrity and workflow boundaries:
1. **Zero New Experiments Executed**: No new benchmark runs, synthetic evaluations, or model queries were performed during Step 4.
2. **Zero Modification of Frozen Evidence**: The frozen benchmark evidence package (`manuscript/evidence_package.md`) and raw benchmark CSV files (`benchmark/seed*/benchmark_results.csv`) remain completely unaltered.
3. **Explicit Gap Transparency**: Where empirical evidence is absent or unexercised, the manuscript transparently discloses the limitation rather than asserting unverified generalizations.

This register formally assesses the six proposed experimental extensions, documenting their exact research questions, implementation effort, evidentiary value, and submission necessity.

---

## 2. Comprehensive Experiment Gap Evaluations

### Experiment 1: Synthetic Epoch Advance Decay Experiment
- **Research Question**: Does continuous exponential decay ($C(t) = C_{\text{ref}} \exp(-\lambda \Delta t)$ with $\lambda = 0.05/\text{day}$) successfully down-weight, deactivate, and archive unreinforced memories over multi-week operational intervals without degrading query repair accuracy?
- **Gap Addressed**: The benchmark executed all 25 queries sequentially within ~3.5 minutes ($\Delta t \approx 0.002$ days), yielding $\exp(-\lambda \Delta t) \approx 0.9999$. This left continuous temporal decay experimentally unexercised, with Mode 6 acting merely as a static no-decay control.
- **Current Evidence**: The mathematical decay equation is fully implemented in `memory/governance.py` and validated via offline unit tests in `tests/unit/test_governance.py`. However, runtime empirical validation in the benchmark is absent.
- **Required Implementation Effort**: Low–Medium. Requires extending `scripts/eval_runner.py` with an optional `--simulate-epochs` parameter that advances synthetic timestamps by 30, 60, and 90 days between query batches.
- **Importance for Current Manuscript**: Moderate. The manuscript fully acknowledges this scope boundary in the Abstract, Section 6.5, Section 14.2, and Limitation 6.
- **Whether Required Before Submission**: **NO**. Transparent disclosure of unexercised decay is standard practice and fully acceptable for conference/workshop submissions.
- **Priority**: **Priority 0 (P0)** for future journal extension (e.g., IEEE TKDE); recommended follow-up.

---

### Experiment 2: Counterfactual Memory Masking Intervention
- **Research Question**: When retrieved operational memories for queries Q08 and Q19 are dynamically masked from the LLM prompt during inference while holding all other inputs identical, does the model fail or incur higher repair iterations, proving causal memory attribution?
- **Gap Addressed**: Current benchmark logs demonstrate an observational association between memory retrieval and zero-retry Attempt-1 execution on Q08 and Q19. However, the benchmark did not perform controlled counterfactual A/B masking to isolate memory as the definitive causal mechanism.
- **Current Evidence**: Observational traces confirm that Mode 4 retrieved admitted memories on Q08 and Q19, which altered prompt tokens and eliminated retries compared to Mode 2.
- **Required Implementation Effort**: Low. Requires an ablation script executing Q08 and Q19 with retrieved memory forced to null (`applied_memories = []`) under identical seeds.
- **Importance for Current Manuscript**: Moderate. The manuscript has removed all causal proof assertions, describing the effect strictly as an observational association.
- **Whether Required Before Submission**: **NO**. The observational framing is scientifically sound and defensible.
- **Priority**: **Priority 0 (P0)** for journal expansion; provides formal causal proof of memory utility.

---

### Experiment 3: Frontier Model Scale Evaluation (70B+ Architectures)
- **Research Question**: Does deploying ARMG with 70B+ parameter open-weights models (e.g., `Llama-3-70B`, `Qwen-2.5-72B`) break the 68.00% relational semantic accuracy plateau observed on complex window functions (`RANK() OVER`, `PARTITION BY`, cumulative framing)?
- **Gap Addressed**: The manuscript evaluates only a single 7B model (`qwen2.5:7b-instruct`). It remains unknown whether the 68.00% relational semantic accuracy ceiling is an intrinsic limitation of the ARMG architecture or a parameter-scale reasoning ceiling of 7B language models.
- **Current Evidence**: Theoretical grounding in Wei et al. (TMLR 2022) [26] suggests that multi-step nested analytical reasoning emerges at larger parameter scales. The ARMG benchmark observed that all 7 divergent queries involved complex windowing or ordering.
- **Required Implementation Effort**: Medium–High. Requires multi-GPU infrastructure (e.g., 4x A100 or 2x H100) to host 70B models via vLLM or Ollama.
- **Importance for Current Manuscript**: High scientifically, but Low as a submission blocker. The paper is explicitly scoped to on-premises, localized 7B deployments.
- **Whether Required Before Submission**: **NO**. Evaluating small models on commodity hardware is a legitimate, highly practical research scope.
- **Priority**: **Priority 1 (P1)**.

---

### Experiment 4: Cross-Domain Public Benchmarks (Spider & BIRD)
- **Research Question**: How does ARMG's operational memory governance and AST safety guardrail perform across the 200 databases of Spider and the 95 noisy databases of BIRD compared to published literature leaders (DIN-SQL, DAIL-SQL, MAC-SQL)?
- **Gap Addressed**: ARMG was evaluated exclusively on a single enterprise-style Star Schema data warehouse. Cross-domain generalizability across diverse relational schemas remains unverified.
- **Current Evidence**: High baseline performance documented in literature for prompting methods [1], [2], [14]. ARMG has zero experimental data on Spider/BIRD.
- **Required Implementation Effort**: High. Requires building evaluation harnesses for multi-database SQLite environments, batch ingestion of 10,000+ queries, and handling schema variability.
- **Importance for Current Manuscript**: Moderate. Spider and BIRD evaluate single-turn cross-database generalizability, whereas ARMG investigates multi-turn operational memory lifecycle over a persistent enterprise warehouse.
- **Whether Required Before Submission**: **NO**. The conceptual focus of ARMG is operational memory accumulation within a persistent data warehouse, not cross-database zero-shot transfer.
- **Priority**: **Priority 1 (P1)**.

---

### Experiment 5: Concurrent Multi-User Workload & Throughput Testing
- **Research Question**: How does ARMG's FAISS vector retrieval, SQLGlot AST validation, and PostgreSQL connection pool scale under concurrent multi-user query load (e.g., 10–50 concurrent users)?
- **Gap Addressed**: The current benchmark evaluated a single-user sequential query execution model. Concurrency contention, FAISS lock contention, and connection pool saturation remain uncharacterized.
- **Current Evidence**: Unit tests verify thread safety of stateless nodes. Benchmark logs report single-user sequential latency (8,564.89 ms).
- **Required Implementation Effort**: Medium. Requires implementing an asynchronous load testing harness (e.g., Locust or Python `asyncio` client pool) against `armg_db`.
- **Importance for Current Manuscript**: Low–Moderate. Single-user sequential evaluation is the standard evaluation paradigm for Text-to-SQL research papers.
- **Whether Required Before Submission**: **NO**. Disclosed explicitly as Limitation 9.
- **Priority**: **Priority 2 (P2)**.

---

### Experiment 6: Multi-Schema Enterprise Warehouse Evaluation
- **Research Question**: Does ARMG's 7-tier diagnostic taxonomy, candidate remapping heuristics, and mutual-exclusion deduplication generalize to highly normalized Snowflake, 3NF, or Data Vault enterprise schemas containing hundreds of tables?
- **Gap Addressed**: ARMG was evaluated on a 4-table Star Schema warehouse (`dim_time`, `dim_geography`, `dim_product`, `fact_sales_performance`). Performance on highly normalized schemas with deep join paths (5+ joins) is unmeasured.
- **Current Evidence**: Synthetic Star Schema benchmark with 2,000 fact records. Zero multi-schema benchmark data.
- **Required Implementation Effort**: Medium–High. Requires designing or importing realistic multi-schema enterprise databases and synthesizing corresponding complex query suites.
- **Importance for Current Manuscript**: Moderate. Disclosed explicitly as Limitation 2 and Threat to External Validity.
- **Whether Required Before Submission**: **NO**. Standard benchmark scope conventions accept single-warehouse or synthetic-warehouse evaluations when clearly disclosed.
- **Priority**: **Priority 2 (P2)**.

---

## 3. Executive Summary & Action Policy

| Experiment Description | Research Priority | Required Implementation Effort | Required Before Submission? | Rationale & Handling |
| :--- | :---: | :---: | :---: | :--- |
| **1. Synthetic Epoch Decay** | **P0** | Low–Medium | **NO** | Disclosed as unexercised in Abstract & Section 14.2; Mode 6 acts as static control. |
| **2. Counterfactual Memory Masking** | **P0** | Low | **NO** | Described strictly as an observational association in Section 10.3 & Section 15.4. |
| **3. 70B+ Frontier Model Scale** | **P1** | Medium–High | **NO** | Manuscript explicitly scoped to localized 7B open-weights deployments. |
| **4. Spider & BIRD Benchmarks** | **P1** | High | **NO** | Paradigm difference: ARMG evaluates persistent warehouse lifecycle, not cross-DB transfer. |
| **5. Concurrent Multi-User Load** | **P2** | Medium | **NO** | Standard Text-to-SQL literature evaluates sequential single-user workloads. |
| **6. Multi-Schema Evaluation** | **P2** | Medium–High | **NO** | Star Schema testbed is standard for data warehouse analytics; disclosed as limitation. |

- **Strict Mandate**: No new experiments were run or claimed in Step 4. All 6 experimental directions are formally cataloged as prioritized Future Work in Section 18 of the manuscript.
