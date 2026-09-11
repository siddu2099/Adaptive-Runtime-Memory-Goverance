# ARMG Phase 9: IEEE Benchmark Results

## Comparative Results Table

| Mode | ExecAcc (%) | Mean Retries (+/- std) | Mean Latency ms (+/- std) | Mean Tokens (+/- std) |
| :--- | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 60.0% (15/25) | 0 +/- 0.0 | 4864.18 +/- 814.38 | 359.92 +/- 32.95 |
| Mode 2 (Stateless Self-Correction) | 68.0% (17/25) | 0.4 +/- 0.87 | 6901.61 +/- 4963.27 | 558.08 +/- 449.62 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 +/- 0.0 | 6790.07 +/- 768.98 | 558.28 +/- 77.31 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.28 +/- 0.68 | 8445.94 +/- 4607.7 | 542.36 +/- 480.02 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.36 +/- 0.76 | 8817.16 +/- 4925.38 | 553.96 +/- 429.03 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.36 +/- 0.76 | 8852.95 +/- 4925.49 | 591.64 +/- 522.65 |

## Category-Wise Accuracy Breakdown

### Mode 1 (Zero-Shot)
- **Category A**: 3/5 (60.0%)
- **Category B**: 6/8 (75.0%)
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
