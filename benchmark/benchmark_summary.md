# ARMG Multi-Seed Empirical Benchmark Statistical Summary

Descriptive multi-seed statistics across seeds 42, 123, and 999 (n = 3 runs; N = 75 queries evaluated per mode).

| Mode | PG Success (Num/Den, Mean +/- Std) | Relational Accuracy (Num/Den, Mean +/- Std) | Retries (Mean +/- Std) | Latency ms (Mean +/- Std) | Tokens (Mean +/- Std) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 60/75 (80.00% +/- 0.00%) | 45/75 (60.00% +/- 0.00%) | 0.00 +/- 0.00 | 4859.70 +/- 7.98 | 360.57 +/- 0.37 |
| Mode 2 (Stateless Self-Correction) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.28 +/- 0.00 | 6441.56 +/- 105.51 | 503.72 +/- 0.42 |
| Mode 3 (Naive Vector RAG) | 69/75 (92.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.00 +/- 0.00 | 6776.25 +/- 34.40 | 558.28 +/- 0.00 |
| Mode 4 (Full ARMG) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.37 +/- 0.05 | 9000.59 +/- 184.33 | 602.85 +/- 28.49 |
| Mode 5 (ARMG - Negative Constraints) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.32 +/- 0.00 | 8768.48 +/- 100.30 | 530.97 +/- 0.40 |
| Mode 6 (ARMG - Temporal Decay) | 72/75 (96.00% +/- 0.00%) | 51/75 (68.00% +/- 0.00%) | 0.28 +/- 0.00 | 8507.98 +/- 73.15 | 542.27 +/- 0.39 |
