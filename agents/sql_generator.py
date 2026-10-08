"""
ARMG Phase 2: Baseline SQL Generator.

Interfaces with the local Ollama instance (qwen2.5:7b-instruct) to generate single-pass
stateless PostgreSQL queries from user questions and deterministic schema metadata.
Captures inference metrics without utilizing memory, retry loops, or error feedback.
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")


@dataclass
class GenerationResult:
    """Records the outcome and telemetry of a single LLM generation attempt."""
    raw_response: str
    extracted_sql: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    generation_duration_ms: float = 0.0


def extract_sql_from_response(text: str) -> str:
    """Deterministically extract SQL from LLM generated response text.
    
    Prefers ```sql ... ``` fenced blocks. Falls back to general code blocks
    or raw SQL query text if they contain recognizable SQL statements.
    Never returns arbitrary natural-language text as SQL.
    """
    if not text:
        return ""

    # 1. Match explicitly tagged ```sql / ```postgresql block
    sql_block_match = re.search(
        r"```(?:sql|postgresql|pgsql)\s*([\s\S]*?)\s*```", text, re.IGNORECASE
    )
    if sql_block_match:
        extracted = sql_block_match.group(1).strip()
        if extracted:
            return extracted

    # SQL statement start keywords for detecting valid SQL in generic blocks or plain text
    sql_start_pattern = r"^(SELECT|WITH|DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE|CREATE|EXPLAIN)\b"

    # 2. Match generic ``` ... ``` block (only if it contains a SQL statement, not non-sql tags like ```text)
    fence_pattern = re.compile(r"```([a-zA-Z0-9_-]*)[ \t]*\r?\n?([\s\S]*?)```")
    for tag, content in fence_pattern.findall(text):
        tag_clean = tag.strip().lower()
        if tag_clean and tag_clean not in ("sql", "postgresql", "pgsql"):
            continue
        content_stripped = content.strip()
        if re.search(sql_start_pattern, content_stripped, re.IGNORECASE):
            return content_stripped

    # 3. Fallback: Check if un-fenced text contains a SQL statement
    lines = text.strip().splitlines()
    sql_lines = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started:
            if re.match(sql_start_pattern, stripped, re.IGNORECASE):
                started = True
                sql_lines.append(stripped)
        else:
            sql_lines.append(line)
            if stripped.endswith(";"):
                break

    if sql_lines:
        return "\n".join(sql_lines).strip()

    return ""


class SQLGenerator:
    """Stateless single-pass SQL generation engine."""

    SYSTEM_PROMPT = """You are an expert PostgreSQL data warehouse query generator.
Generate a single, syntactically correct, read-only PostgreSQL query that answers the user question based strictly on the provided schema.

STRICT INSTRUCTIONS:
1. Output ONLY the executable SQL query enclosed in a ```sql ... ``` markdown code block.
2. Do NOT provide any explanations, notes, or commentary.
3. Use ONLY the tables and columns explicitly present in the provided schema. Never invent identifiers.
4. Generate ONLY read-only SELECT queries. Never use DDL or DML (DROP, DELETE, UPDATE, INSERT, ALTER).
5. Join tables using explicit foreign-to-primary key relationships.
6. Ensure all non-aggregated SELECT columns appear in the GROUP BY clause."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        seed: Optional[int] = None,
    ):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.model = model or DEFAULT_LLM_MODEL
        self.timeout = timeout
        self.seed = seed

    def generate(self, question: str, schema_markdown: str) -> GenerationResult:
        """Generate SQL for user question given deterministic schema Markdown.
        
        Args:
            question: Natural language question.
            schema_markdown: Deterministically pruned schema Markdown string.
            
        Returns:
            GenerationResult containing raw response, extracted SQL, and token metrics.
        """
        user_prompt = f"""### DATABASE SCHEMA:
{schema_markdown}

### USER QUESTION:
{question}

### SQL QUERY:"""

        endpoint = f"{self.base_url}/api/generate"
        options = {
            "temperature": 0.0,
        }
        if self.seed is not None:
            options["seed"] = self.seed

        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": self.SYSTEM_PROMPT,
            "stream": False,
            "options": options,
        }

        start_time = time.perf_counter()
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return GenerationResult(
                raw_response="",
                extracted_sql="",
                prompt_tokens=None,
                completion_tokens=None,
                generation_duration_ms=round(elapsed_ms, 3),
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        raw_text = data.get("response", "")
        extracted = extract_sql_from_response(raw_text)

        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")

        return GenerationResult(
            raw_response=raw_text,
            extracted_sql=extracted,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            generation_duration_ms=round(elapsed_ms, 3),
        )
