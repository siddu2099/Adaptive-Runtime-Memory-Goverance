# ARMG Phase 9: IEEE Benchmark Results

## Comparative Results Table

| Mode | ExecAcc (%) | Mean Retries (+/- std) | Mean Latency ms (+/- std) | Mean Tokens (+/- std) |
| :--- | :---: | :---: | :---: | :---: |
| Mode 1 (Zero-Shot) | 60.0% (15/25) | 0 +/- 0.0 | 5554.82 +/- 1056.88 | 359.84 +/- 32.65 |
| Mode 2 (Stateless Self-Correction) | 72.0% (18/25) | 0.4 +/- 0.87 | 7971.62 +/- 5744.09 | 553.44 +/- 443.37 |
| Mode 3 (Naive Vector RAG) | 68.0% (17/25) | 0 +/- 0.0 | 8108.22 +/- 2053.36 | 557.52 +/- 77.07 |
| Mode 4 (Full ARMG) | 68.0% (17/25) | 0.4 +/- 0.87 | 9186.68 +/- 5563.49 | 600.84 +/- 554.36 |
| Mode 5 (ARMG - Negative Constraints) | 68.0% (17/25) | 0.4 +/- 0.87 | 9216.51 +/- 5548.13 | 559.4 +/- 452.2 |
| Mode 6 (ARMG - Temporal Decay) | 68.0% (17/25) | 0.44 +/- 0.87 | 9540.4 +/- 5612.56 | 621.4 +/- 553.46 |

## Category-Wise Accuracy Breakdown

### Mode 1 (Zero-Shot)
- **Category A**: 3/5 (60.0%)
- **Category B**: 6/8 (75.0%)
- **Category C**: 2/6 (33.3%)
- **Category D**: 4/6 (66.7%)

### Mode 2 (Stateless Self-Correction)
- **Category A**: 4/5 (80.0%)
- **Category B**: 7/8 (87.5%)
- **Category C**: 2/6 (33.3%)
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
