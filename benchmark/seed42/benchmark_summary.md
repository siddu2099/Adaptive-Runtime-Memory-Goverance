# ARMG Authoritative Benchmark — Seed 42

| Mode | ExecAcc (%) | Mean Retries (+/- std) | Mean Latency ms (+/- std) | Mean Tokens (+/- std) |
| :--- | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 60.0% (15/25) | 0 +/- 0.0 | 4853.3 +/- 845.77 | 360.16 +/- 32.94 |
| Mode 2 (Stateless Self-Correction) | 68.0% (17/25) | 0.28 +/- 0.68 | 6563.4 +/- 4360.27 | 503.96 +/- 377.56 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 +/- 0.0 | 6811.9 +/- 762.38 | 558.28 +/- 77.31 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.32 +/- 0.69 | 8754.46 +/- 4751.51 | 565.44 +/- 482.91 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.32 +/- 0.69 | 8713.49 +/- 4641.76 | 530.72 +/- 391.73 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.28 +/- 0.68 | 8453.39 +/- 4597.64 | 542 +/- 479.56 |
