# ARMG Multi-Seed Empirical Benchmark Statistical Summary

Descriptive multi-seed statistics across seeds 42, 123, and 999 (n = 3 runs; N = 75 queries evaluated per mode).

| Mode | PG Success (Num/Den, Mean +/- Std) | Relational Accuracy (Num/Den, Mean +/- Std) | Retries (Mean +/- Std) | Latency ms (Mean +/- Std) | Tokens (Mean +/- Std) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 57/75 (76.00% +/- 0.00%) | 43/75 (57.33% +/- 2.31%) | 0.00 +/- 0.00 | 5087.73 +/- 210.33 | 360.48 +/- 0.48 |
| Mode 2 (Stateless Self-Correction) | 69/75 (92.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.43 +/- 0.02 | 7149.68 +/- 231.65 | 572.72 +/- 12.68 |
| Mode 3 (Naive Vector RAG) | 69/75 (92.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.00 +/- 0.00 | 6844.01 +/- 56.89 | 558.28 +/- 0.00 |
| Mode 4 (Full ARMG) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.28 +/- 0.00 | 8564.89 +/- 103.15 | 542.37 +/- 0.02 |
| Mode 5 (ARMG - Negative Constraints) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.36 +/- 0.00 | 8941.29 +/- 108.68 | 553.93 +/- 0.02 |
| Mode 6 (ARMG - Temporal Decay) | 71/75 (94.67% +/- 2.31%) | 51/75 (68.00% +/- 0.00%) | 0.37 +/- 0.02 | 9036.96 +/- 178.55 | 599.67 +/- 13.94 |
