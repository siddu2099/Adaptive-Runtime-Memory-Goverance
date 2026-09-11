# ARMG Phase 9: IEEE Benchmark Results

## Comparative Results Table

| Mode | ExecAcc (%) | Mean Retries (+/- std) | Mean Latency ms (+/- std) | Mean Tokens (+/- std) |
| :--- | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 56.0% (14/25) | 0 +/- 0.0 | 5117.29 +/- 1361.0 | 360.76 +/- 32.84 |
| Mode 2 (Stateless Self-Correction) | 68.0% (17/25) | 0.44 +/- 0.87 | 7187.05 +/- 5082.26 | 580.04 +/- 455.57 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 +/- 0.0 | 6838.49 +/- 782.59 | 558.28 +/- 77.31 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.28 +/- 0.68 | 8629.83 +/- 4782.98 | 542.4 +/- 480.08 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.36 +/- 0.76 | 8987.36 +/- 5065.29 | 553.92 +/- 428.97 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.36 +/- 0.76 | 9048.46 +/- 5120.27 | 591.6 +/- 522.6 |

## Category-Wise Accuracy Breakdown

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
