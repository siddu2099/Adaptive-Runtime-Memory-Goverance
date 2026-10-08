# ARMG Authoritative Multi-Seed Benchmark Summary

| Mode | ExecSucc (%) | RelAcc (%) | Mean Retries | Mean Latency (ms) | Mean Tokens | Store Size |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mode 1 (Zero-Shot)** | 80.00% ± 0.00% | 60.00% ± 0.00% | 0.00 ± 0.00 | 4,859.70 ± 7.98 | 360.57 ± 0.37 | 0 |
| **Mode 2 (Stateless Self-Correction)** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.28 ± 0.00 | 6,441.56 ± 105.51 | 503.72 ± 0.42 | 0 |
| **Mode 3 (Naive Vector RAG)** | 92.00% ± 0.00% | 68.00% ± 0.00% | 0.00 ± 0.00 | 6,776.25 ± 34.40 | 558.28 ± 0.00 | 23 |
| **Mode 4 (Full ARMG)** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.37 ± 0.05 | 9,000.59 ± 184.33 | 602.85 ± 28.49 | 3 |
| **Mode 5 (ARMG - Negative Constraints)** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.32 ± 0.00 | 8,768.48 ± 100.30 | 530.97 ± 0.40 | 4 |
| **Mode 6 (ARMG - Temporal Decay)** | 96.00% ± 0.00% | 68.00% ± 0.00% | 0.28 ± 0.00 | 8,507.98 ± 73.15 | 542.27 ± 0.39 | 3 |

Dynamically generated from authoritative benchmark evidence via `scripts/generate_results.py`.
