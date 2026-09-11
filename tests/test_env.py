"""
ARMG Phase 0: Environment, Repository Foundation & Infrastructure Verification Test Suite.

This module validates that all core infrastructure dependencies work independently:
- Python version >= 3.11
- Package imports (langgraph, sqlglot, faiss, pydantic, psycopg2, streamlit, pytest, numpy, requests, dotenv)
- Ollama service reachability and model availability (qwen2.5:7b-instruct, nomic-embed-text)
- Ollama LLM inference (deterministic smoke test)
- Ollama embedding generation and dimension consistency measurement
- PostgreSQL database connectivity and SELECT 1 execution
- FAISS-CPU in-memory indexing and exact search
- SQLGlot PostgreSQL AST parsing
- Pydantic v2 validation semantics
- LangGraph trivial state-graph compilation and execution

No Phase 1+ application or domain logic is implemented here.
"""

import os
import sys
from typing import TypedDict
import numpy as np
import pytest
import requests
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "armg_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

REQUEST_TIMEOUT_SECONDS = 15


def test_python_version():
    """Verify runtime Python version satisfies >= 3.11."""
    major, minor = sys.version_info.major, sys.version_info.minor
    assert sys.version_info >= (3, 11), (
        f"Python >= 3.11 required. Detected Python {major}.{minor} at {sys.executable}"
    )


def test_required_package_imports():
    """Verify that every core stack package can be imported directly."""
    packages = [
        "numpy",
        "requests",
        "psycopg2",
        "faiss",
        "sqlglot",
        "pydantic",
        "langgraph",
        "streamlit",
        "pytest",
        "dotenv",
    ]
    imported = {}
    for pkg in packages:
        try:
            mod = __import__(pkg)
            imported[pkg] = getattr(mod, "__version__", "installed")
        except ImportError as e:
            pytest.fail(f"Required package '{pkg}' failed to import: {e}")
    assert len(imported) == len(packages)


def test_ollama_connectivity():
    """Verify Ollama is reachable and required models are available."""
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError:
        pytest.fail(
            f"Could not connect to Ollama at {OLLAMA_BASE_URL}.\n"
            "Ensure Ollama is installed and the Ollama service is running.\n"
            "Diagnostic check: Run 'ollama serve' or verify OLLAMA_BASE_URL in .env."
        )
    except requests.exceptions.Timeout:
        pytest.fail(f"Timeout connecting to Ollama at {OLLAMA_BASE_URL} (exceeded {REQUEST_TIMEOUT_SECONDS}s).")

    assert response.status_code == 200, (
        f"Ollama returned HTTP {response.status_code} from {url}: {response.text}"
    )

    data = response.json()
    models = [m.get("name", "") for m in data.get("models", [])]
    
    # Model matching: match exact tag or base name with :latest
    def model_matches(target: str, model_list: list[str]) -> bool:
        for m in model_list:
            if m == target or m == f"{target}:latest" or m.startswith(f"{target}:"):
                return True
        return False

    if not model_matches(LLM_MODEL, models):
        pytest.fail(
            f"Required LLM model '{LLM_MODEL}' not found in Ollama.\n"
            f"Available models: {models}\n"
            f"Run: ollama pull {LLM_MODEL}"
        )

    if not model_matches(EMBEDDING_MODEL, models):
        pytest.fail(
            f"Required embedding model '{EMBEDDING_MODEL}' not found in Ollama.\n"
            f"Available models: {models}\n"
            f"Run: ollama pull {EMBEDDING_MODEL}"
        )


def test_ollama_llm_inference():
    """Verify minimal deterministic LLM inference with qwen2.5:7b-instruct."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": "Respond with the single word OK.",
        "stream": False,
        "options": {
            "temperature": 0.0,
        },
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP request to Ollama generate endpoint failed: {e}")

    assert response.status_code == 200, (
        f"Ollama generate returned status {response.status_code}: {response.text}"
    )

    data = response.json()
    generated_text = data.get("response", "").strip()
    assert len(generated_text) > 0, "Ollama returned empty response for LLM test prompt."


def test_ollama_embedding_generation():
    """Verify nomic-embed-text can generate a non-empty numeric embedding."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    test_text = "ARMG deterministic embedding verification."
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": test_text,
    }
    try:
        response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"HTTP request to Ollama embeddings endpoint failed: {e}")

    assert response.status_code == 200, (
        f"Ollama embeddings returned status {response.status_code}: {response.text}"
    )

    data = response.json()
    embedding = data.get("embedding", [])
    assert isinstance(embedding, list), f"Expected list embedding, got {type(embedding)}"
    assert len(embedding) > 0, "Embedding returned by Ollama is empty"
    assert all(isinstance(val, (int, float)) for val in embedding), "Embedding elements must be numeric"

    # Store discovered dimension in test context / print for report
    print(f"\n[INFO] Discovered actual {EMBEDDING_MODEL} dimension: {len(embedding)}")


def test_embedding_dimension_consistency():
    """Verify repeated embedding generation yields identical dimensionality."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    samples = [
        "First test string for dimensional consistency.",
        "Second test string with completely different semantic tokens.",
    ]
    dims = []
    for sample in samples:
        response = requests.post(
            url,
            json={"model": EMBEDDING_MODEL, "prompt": sample},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        assert response.status_code == 200
        emb = response.json().get("embedding", [])
        dims.append(len(emb))

    assert len(dims) == 2
    assert dims[0] > 0, "Dimension must be positive"
    assert dims[0] == dims[1], f"Embedding dimensions inconsistent across calls: {dims[0]} != {dims[1]}"


def test_postgresql_connection():
    """Verify PostgreSQL connectivity and query server version."""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=10,
        )
    except Exception as e:
        pytest.fail(
            f"PostgreSQL connection failed: {e}\n"
            "Check:\n"
            "- PostgreSQL service status (e.g., Get-Service *postgres*)\n"
            f"- POSTGRES_HOST={POSTGRES_HOST}\n"
            f"- POSTGRES_PORT={POSTGRES_PORT}\n"
            f"- POSTGRES_DB={POSTGRES_DB}\n"
            f"- POSTGRES_USER={POSTGRES_USER}\n"
            "- POSTGRES_PASSWORD"
        )

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version_row = cur.fetchone()
            assert version_row is not None and len(version_row) > 0
            print(f"\n[INFO] Connected to PostgreSQL: {version_row[0]}")
    finally:
        conn.close()


def test_postgresql_select_one():
    """Verify execution of SELECT 1 returns exactly (1,)."""
    import psycopg2

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=10,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            assert result == (1,), f"Expected (1,), got {result}"
    finally:
        conn.close()


def test_faiss_index():
    """Verify in-memory FAISS-CPU index creation, vector addition, and exact nearest-neighbor search."""
    import faiss

    np.random.seed(42)
    dim = 64
    num_vectors = 10
    vectors = np.random.random((num_vectors, dim)).astype("float32")

    # Construct in-memory L2 index
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    assert index.ntotal == num_vectors, f"Expected {num_vectors} vectors in index, found {index.ntotal}"

    # Search for vector at index 0 (self-search)
    query_vector = vectors[0:1]
    k = 3
    distances, indices = index.search(query_vector, k)

    # Nearest neighbor must be index 0 with ~0 distance
    assert indices[0][0] == 0, f"Expected nearest neighbor 0, got {indices[0][0]}"
    assert distances[0][0] < 1e-5, f"Expected self-distance ~0, got {distances[0][0]}"


def test_sqlglot_postgres_parsing():
    """Verify SQLGlot can parse valid PostgreSQL SQL and returns a Select AST root."""
    import sqlglot
    import sqlglot.expressions as exp

    query = """
    SELECT region, SUM(gross_revenue)
    FROM fact_sales_performance
    GROUP BY region;
    """
    ast = sqlglot.parse_one(query, read="postgres")
    assert ast is not None, "SQLGlot returned None for valid SQL"
    assert isinstance(ast, exp.Select), f"Expected AST root exp.Select, got {type(ast)}"


def test_pydantic_validation():
    """Verify Pydantic v2 validation semantics with valid and invalid payloads."""
    import pydantic

    class TempVerificationModel(pydantic.BaseModel):
        identifier: str
        score: float

    # 1. Valid input succeeds
    valid_instance = TempVerificationModel(identifier="test_node_01", score=0.95)
    assert valid_instance.identifier == "test_node_01"
    assert valid_instance.score == 0.95

    # 2. Invalid input raises ValidationError
    with pytest.raises(pydantic.ValidationError):
        TempVerificationModel(identifier="test_node_02", score="not_a_valid_float_value")


def test_langgraph_trivial_execution():
    """Verify LangGraph compilation and execution of a minimal state graph."""
    from langgraph.graph import StateGraph, START, END

    class TrivialState(TypedDict):
        count: int

    def increment_node(state: TrivialState) -> TrivialState:
        return {"count": state["count"] + 1}

    builder = StateGraph(TrivialState)
    builder.add_node("increment", increment_node)
    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    graph = builder.compile()
    initial_state: TrivialState = {"count": 0}
    final_state = graph.invoke(initial_state)

    assert final_state == {"count": 1}, f"Expected {{'count': 1}}, got {final_state}"
