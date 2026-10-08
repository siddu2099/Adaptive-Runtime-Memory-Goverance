"""
ARMG Phase 3: Environment Verification and Provenance Recorder.
Records complete runtime, library, database, and LLM daemon environment parameters
to benchmark/environment.json for immutable empirical lineage.
"""

import json
import os
from pathlib import Path
import platform
import sys
import requests
import psycopg2
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv()


def record_environment(output_path: Path = REPO_ROOT / "benchmark" / "environment.json") -> dict:
    env_info = {}

    # 1. OS & Python
    env_info["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    env_info["python"] = {
        "version": sys.version,
        "executable": sys.executable,
    }

    # 2. Key Libraries
    import faiss
    import sqlglot
    import langgraph
    import pydantic
    import numpy as np

    torch_ver = "N/A (faiss-cpu standalone)"
    try:
        import torch
        torch_ver = torch.__version__
    except ImportError:
        pass

    import importlib.metadata

    def get_pkg_version(name):
        try:
            return importlib.metadata.version(name)
        except Exception:
            return "unknown"

    env_info["libraries"] = {
        "torch": torch_ver,
        "faiss": get_pkg_version("faiss-cpu") if get_pkg_version("faiss-cpu") != "unknown" else getattr(faiss, "__version__", "unknown"),
        "sqlglot": get_pkg_version("sqlglot"),
        "langgraph": get_pkg_version("langgraph"),
        "psycopg2": get_pkg_version("psycopg2") if get_pkg_version("psycopg2") != "unknown" else psycopg2.__version__,
        "pydantic": get_pkg_version("pydantic"),
        "numpy": np.__version__,
    }

    # 3. PostgreSQL Database
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = int(os.getenv("POSTGRES_PORT", 5432))
    pg_db = os.getenv("POSTGRES_DB", "armg_db")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "")

    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        dbname=pg_db,
        user=pg_user,
        password=pg_pass,
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    pg_version = cur.fetchone()[0]

    # Inspect schema/tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    table_counts = {}
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t};")
        table_counts[t] = cur.fetchone()[0]

    cur.close()
    conn.close()

    env_info["postgresql"] = {
        "version": pg_version,
        "host": pg_host,
        "port": pg_port,
        "database": pg_db,
        "tables": tables,
        "row_counts": table_counts,
        "connectivity": "CONNECTED",
    }

    # 4. Ollama LLM & Embedding Daemon
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    res_version = requests.get(f"{ollama_url}/api/version", timeout=5)
    res_version.raise_for_status()
    ollama_ver = res_version.json().get("version", "unknown")

    res_tags = requests.get(f"{ollama_url}/api/tags", timeout=5)
    res_tags.raise_for_status()
    models = res_tags.json().get("models", [])
    model_names = [m.get("name") for m in models]

    gen_model = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")
    embed_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    gen_model_avail = any(gen_model in m for m in model_names)
    embed_model_avail = any(embed_model in m for m in model_names)

    env_info["ollama"] = {
        "base_url": ollama_url,
        "version": ollama_ver,
        "installed_models": model_names,
        "generation_model": gen_model,
        "generation_model_available": gen_model_avail,
        "embedding_model": embed_model,
        "embedding_model_available": embed_model_avail,
        "connectivity": "CONNECTED",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(env_info, f, indent=2)

    print(f"Environment successfully recorded to: {output_path}")
    return env_info


if __name__ == "__main__":
    info = record_environment()
    print("Environment Verification Complete:")
    print(f"  Python: {info['python']['version'].split()[0]}")
    print(f"  OS: {info['os']['system']} {info['os']['release']}")
    print(f"  FAISS: {info['libraries']['faiss']}")
    print(f"  PyTorch: {info['libraries']['torch']}")
    print(f"  PostgreSQL: {info['postgresql']['version']}")
    print(f"  Ollama: {info['ollama']['version']} @ {info['ollama']['base_url']}")
    print(f"  Generation Model ({info['ollama']['generation_model']}): {info['ollama']['generation_model_available']}")
    print(f"  Embedding Model ({info['ollama']['embedding_model']}): {info['ollama']['embedding_model_available']}")
