# ARMG Manual Testing Readiness

## Environment
- Python: 3.11.9 (`.venv` virtual environment)
- PostgreSQL: PostgreSQL 18.1 on x86_64-windows (Service: `postgresql-x64-18`, Port: 5432)
- Ollama: Local Inference Engine (PID 8292, Port: 11434)
- LLM: `qwen2.5:7b-instruct` (7.6B parameters, Q4_K_M)
- Embedding model: `nomic-embed-text:latest` (137M parameters, 768-dimensional)
- FAISS: `faiss-cpu` 1.15.0 (IndexFlatL2 with unit-L2 normalization)

## Connectivity
- PostgreSQL: PASS (TCP port 5432 active and reachable)
- PostgreSQL authentication: PASS (User `postgres`, database `armg_db`, password configured and authenticated)
- Ollama: PASS (HTTP `http://localhost:11434/api/tags` returned HTTP 200 with available models)
- Embedding API: PASS (HTTP `http://localhost:11434/api/embeddings` returned 768-dim embedding with unit norm)

## Database
- Database: `armg_db`
- Schema: PASS
  - `dim_time`: 365 rows
  - `dim_geography`: 6 rows
  - `dim_product`: 8 rows
  - `fact_sales_performance`: 2,000 rows

## Tests
- Unit: PASS (374 passed in 54.49s)
- Integration: PASS (17 passed in 22.26s)
- Environment: PASS (12 passed in 23.46s)

## Dashboard
- Startup: PASS (Streamlit server active on `http://localhost:8501`, HTTP GET returned 200 OK)
- Manual query interface: PASS (Tab 1 Live Query Execution, Tab 2 Governed Memory Bank Inspector, Tab 3 Governance Mathematics Visualizer)

## Problems Found

### Problem 1: Missing `matplotlib` dependency in `.venv`
- **Observed evidence**: `pytest tests/unit/ -q` halted during collection with `ModuleNotFoundError: No module named 'matplotlib'` in `test_phase2_faiss_telemetry.py` and `test_phase5_results_pipeline.py`.
- **Root cause**: `matplotlib>=3.7.0` is specified in `requirements.txt` (line 10), but was not yet installed into the local `.venv` environment.
- **Fix**: Executed `.\.venv\Scripts\pip.exe install "matplotlib>=3.7.0"`, successfully installing `matplotlib-3.11.2` and its core dependencies (`contourpy-1.3.3`, `cycler-0.12.1`, `fonttools-4.66.1`, `kiwisolver-1.5.1`, `pyparsing-3.3.3`).
- **Verification**: Re-ran `pytest tests/unit/ -q`, which ran to 100% completion with 374 passed tests.
