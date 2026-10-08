# Adaptive Runtime Memory Governance (ARMG)

## Purpose
Adaptive Runtime Memory Governance (ARMG) is a runtime operational knowledge framework designed to convert execution feedback into structured, reusable operational knowledge and govern memory retention over time. Developed as a B.Tech Computer Science and Engineering Capstone Project at VIT-AP University (intended to support an IEEE research publication), Phase 1 of ARMG validates the architecture in an enterprise Text-to-SQL environment over an analytical PostgreSQL Data Warehouse using local agentic models (`qwen2.5:7b-instruct` and `nomic-embed-text` via Ollama).

---

## Prerequisites & Requirements
- **Operating System**: Windows / Linux / macOS (Tested on Windows 11 x64)
- **Python**: 3.11+ (Project Virtual Environment: Python 3.11.9; Host System: Python 3.13.2)
- **Database Engine**: PostgreSQL 15+ (Installed & Tested: PostgreSQL 18.1 on localhost:5432)
- **Local Inference Engine**: Ollama (Installed: 0.32.15)
- **Required Models**:
  - `qwen2.5:7b-instruct` (LLM inference and SQL generation)
  - `nomic-embed-text` (Local vector embeddings)

---

## Local Installation (Windows)

1. **Clone / Open Repository**:
   ```powershell
   cd "c:\Users\siddu\Pictures\armg main"
   ```

2. **Create and Activate Virtual Environment**:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Upgrade pip and Install Locked Dependencies**:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Environment Configuration

Copy the example environment template to `.env`:
```powershell
Copy-Item .env.example .env
```

Configure your local database credentials and Ollama URL in `.env`:
```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=armg_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b-instruct
EMBEDDING_MODEL=nomic-embed-text
```

> **Security Note**: Never commit `.env` to source control. Ensure PostgreSQL credentials remain local.

---

## Ollama Local Setup

Ensure the Ollama service is active and listening on port 11434:
```powershell
ollama serve
```

Pull the required models:
```powershell
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

---

---

## Running the ARMG System

### 1. Launch the Streamlit Interactive Dashboard (Phase 8 UI)

To launch the live inspection and governance dashboard:
```powershell
.\.venv\Scripts\streamlit run ui/dashboard.py
```
Open your browser at `http://localhost:8501`. The dashboard includes:
- **Tab 1: Live Query Execution & Trace**: Run natural language queries, inspect schema pruning, AST validation, generated SQL, PostgreSQL execution, deterministic error diagnosis, strict repair constraints, and runtime telemetry.
- **Tab 2: Governed Memory Bank Inspector**: Inspect persistent operational memories in FAISS, filter by lifecycle state (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`), and trigger simulated epoch decay sweeps.
- **Tab 3: Governance Mathematics & Decay Visualizer**: Interactive curves for exponential confidence decay, success escalation, failure penalty, and utility scoring.

---

### 2. Run the IEEE Empirical Evaluation Suite (Phase 9 Benchmark)

The evaluation runner supports isolated execution across all six experimental modes over the 25 benchmark queries:

- **Gate A: Verify Gold SQL Queries**:
  ```powershell
  .\.venv\Scripts\python scripts/eval_runner.py --verify-gold
  ```

- **Quick 2-Query Smoke Test**:
  ```powershell
  .\.venv\Scripts\python scripts/eval_runner.py --limit 2
  ```

- **Full 25-Query Benchmark across All Six Modes**:
  ```powershell
  .\.venv\Scripts\python scripts/eval_runner.py --output benchmark/benchmark_results.csv
  ```

- **Run an Individual Mode** (`mode_1`, `mode_2`, `mode_3`, `mode_4`, `mode_5`, `mode_6`):
  ```powershell
  .\.venv\Scripts\python scripts/eval_runner.py --mode mode_4
  ```

Results will be exported to `benchmark/benchmark_results.csv` and summarized in `benchmark/benchmark_summary.md`.

---

### 3. Run the Stateless Baseline Pipeline (Phase 2)

To run the single-pass baseline without memory or repair:
```powershell
.\.venv\Scripts\python scripts/run_baseline.py
```

---

### 4. Seed / Re-seed the PostgreSQL Data Warehouse (Phase 1)

To re-initialize the Star Schema tables and populate the 2,000 transactions (seed=42):
```powershell
.\.venv\Scripts\python scripts/seed_warehouse.py
```

---

### 5. Run the Automated Test Suite (401 Tests Total)
 
- **Hermetic Unit Test Suite (372 Tests)**:
  Zero external network dependencies, offline-safe, mocks external daemons:
  ```powershell
  pytest tests/unit/ -v
  ```

- **Live Integration & Environment Test Suite (29 Tests)**:
  Requires live PostgreSQL on port 5432 and live Ollama on port 11434 (17 integration + 12 environment):
  ```powershell
  pytest tests/integration/ tests/test_env.py -v
  ```

- **Run All Tests (401 Tests)**:
  ```powershell
  pytest tests/ -v
  ```

---

### 6. Reproducibility & Forensic Verification Pipeline

To independently verify empirical evidence integrity, validate provenance, and reproduce derived publication artifacts:

1. **Validate Benchmark Data Integrity & Smoke Exclusion**:
   ```powershell
   python scripts/verify_phase4_data_integrity.py
   ```

2. **Validate Retrieval Telemetry Provenance**:
   ```powershell
   python scripts/verify_phase4_telemetry_provenance.py
   ```

3. **Validate Numerical Validation Tables**:
   ```powershell
   python scripts/verify_validation_tables.py
   ```

4. **Validate Temporal Decay Mathematical Invariants**:
   ```powershell
   python scripts/validate_temporal_decay.py
   ```

5. **Run Reproducibility, Paired Analysis & Lineage Audit**:
   ```powershell
   python scripts/analyze_reproducibility.py
   ```

6. **Regenerate Canonical Derived Tables, Figures & Summaries**:
   ```powershell
   python scripts/generate_results.py
   ```

