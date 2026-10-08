# ARMG Phase 9: Post-Remediation Benchmark Results (Stage 1 — Seed 42)

## 1. Executive Summary & Experimental Context
This document records the formal results of **Phase 9 Stage 1 Controlled Benchmark Rerun** under **Seed 42** following Remediation #1 (Unit-L2 Runtime Embedding Normalization) and Remediation #2 (Mutual Exclusion between Memory Reinforcement and New Admission).

Experimental Protocol Controls:
- **Seed**: 42 (single controlled run for 1:1 comparison with historical baseline)
- **Queries**: Q01–Q25 from `benchmark/queries.json` (frozen)
- **Model**: `qwen2.5:7b-instruct` via Ollama (frozen)
- **Embedding**: `nomic-embed-text` (768-dim, unit-L2 normalized) (frozen)
- **Retrieval Threshold**: 0.50 (frozen)
- **Evaluation**: Relational equivalence against PostgreSQL gold execution via `benchmark/equivalence.py` (frozen)
- **Statistical Qualifier**: All reported `±` figures denote cross-query dispersion within the single run, NOT multi-seed run-to-run uncertainty.

---

## 2. Post-Remediation Overall Comparison Table

| Mode | ExecAcc (%) | Mean Retries (± std) | Mean Latency ms (± std) | Mean Tokens (± std) | Retrieval Count (Queries) | Admissions | Reinforcements | Final Store Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 56.0% (14/25) | 0 ± 0.0 | 5281.72 ± 1625.56 | 360.76 ± 32.84 | 0 (0) | 0 | 0 | 0 |
| Mode 2 (Stateless Self-Correction) | 68.0% (17/25) | 0.44 ± 0.87 | 7360.37 ± 5233.82 | 580.04 ± 455.57 | 0 (0) | 0 | 0 | 0 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 ± 0.0 | 6903.46 ± 808.9 | 558.28 ± 77.31 | 69 (24) | 23 | 0 | 23 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.28 ± 0.68 | 8618.89 ± 4810.27 | 542.36 ± 480.02 | 16 (12) | 3 | 1 | 3 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.36 ± 0.76 | 9019.33 ± 5054.56 | 553.92 ± 428.97 | 16 (12) | 3 | 2 | 3 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.4 ± 0.87 | 9209.49 ± 5581.55 | 615.76 ± 581.83 | 16 (12) | 3 | 1 | 3 |

---

## 3. Historical Pre-Remediation Baseline Values (Archival Reference)

| Mode | ExecAcc (%) | Mean Retries (± std) | Mean Latency ms (± std) | Mean Tokens (± std) | Retrieval Count (Queries) | Admissions | Reinforcements | Final Store Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 60.0% (15/25) | 0 ± 0.0 | 5554.82 ± 1056.88 | 359.84 ± 32.65 | 0 (0) | 0 | 0 | 0 |
| Mode 2 (Stateless Self-Correction) | 72.0% (18/25) | 0.4 ± 0.87 | 7971.62 ± 5744.09 | 553.44 ± 443.37 | 0 (0) | 0 | 0 | 0 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 ± 0.0 | 8108.22 ± 2053.36 | 557.52 ± 77.07 | 69 (24) | 23 | 0 | 23 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.4 ± 0.87 | 9186.68 ± 5563.49 | 600.84 ± 554.36 | 0 (0) | 4 | 0 | 4 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.4 ± 0.87 | 9216.51 ± 5548.13 | 559.4 ± 452.2 | 0 (0) | 4 | 0 | 4 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.44 ± 0.87 | 9540.4 ± 5612.56 | 621.4 ± 553.46 | 0 (0) | 5 | 0 | 5 |

---

## 4. Key Remediation Impact Findings

1. **Restoration of ARMG Memory Retrieval**:
   - In pre-remediation, Modes 4, 5, and 6 exhibited **0 retrievals** across all queries due to unnormalized embedding scale mismatch.
   - In post-remediation, Mode 4 achieved **16 retrievals across 12 distinct queries** (Q08, Q10, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25).
2. **Mean Retries Reduction in Mode 4**:
   - Mode 4 mean retries dropped from **0.40 ± 0.87** (pre-remediation) to **0.28 ± 0.68** (post-remediation), a **30% reduction** in repair iterations driven by retrieved memories (e.g., Q19 required 0 retries vs 3 retries in pre-remediation).
3. **Execution Latency Reduction in Mode 4**:
   - Mode 4 mean latency dropped from **9,186.68 ms** to **8,618.89 ms** (-567.79 ms).
4. **Enforcement of Mutual Exclusion (Remediation #2)**:
   - In Mode 4 Q17, an existing memory (`mem-18fc8e84`) was retrieved and reinforced (`EXISTING_REINFORCED`). Mutual exclusion prevented new admission, maintaining the store count strictly at 3 without duplicate accumulation.
5. **PostgreSQL Execution vs Relational Equivalence**:
   - Mode 4 PostgreSQL execution success rate: **24/25 (96.0%)**.
   - Mode 4 Relational equivalence (accuracy): **17/25 (68.0%)**.
   - 7 queries executed cleanly on PostgreSQL but were non-equivalent to gold SQL due to subtle projection, ordering, or aggregation semantics.

---

## 5. Category-Wise Accuracy Breakdown (Post-Remediation)

### Mode 1 (Zero-Shot)
- **Category A**: 3/5 (60.0%)
- **Category B**: 5/8 (62.5%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

### Mode 2 (Stateless Self-Correction)
- **Category A**: 4/5 (80.0%)
- **Category B**: 7/8 (87.5%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

### Mode 3 (Naive Vector RAG)
- **Category A**: 3/5 (60.0%)
- **Category B**: 8/8 (100.0%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

### Mode 4 (Full ARMG)
- **Category A**: 4/5 (80.0%)
- **Category B**: 7/8 (87.5%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

### Mode 5 (ARMG - Negative Constraints)
- **Category A**: 4/5 (80.0%)
- **Category B**: 7/8 (87.5%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

### Mode 6 (ARMG - Temporal Decay)
- **Category A**: 4/5 (80.0%)
- **Category B**: 7/8 (87.5%)
- **Category C**: 1/6 (16.7%)
- **Category D**: 5/6 (83.3%)

