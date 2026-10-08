"""
ARMG Phase 7: Repair Agent & Strict Repair Prompt Builder.

Implements Component 4:
- RepairPromptBuilder: Assembles the deterministic [STRICT REPAIR CONSTRAINTS] block,
  binding negative constraints, candidate replacements, and diagnostic repair rules.
- RepairSQLGenerator: Executes single-pass repair query generation via Ollama (qwen2.5:7b-instruct),
  with optional pluggable generator support for deterministic testing.
"""

import os
import time
from typing import Any, Callable, Dict, List, Optional
import requests
from dotenv import load_dotenv

from agents.error_diagnosis import DiagnosticResult
from agents.sql_generator import DEFAULT_LLM_MODEL, OLLAMA_BASE_URL, GenerationResult, extract_sql_from_response
from memory.models import RuntimeMemory

load_dotenv()


class RepairPromptBuilder:
    """Constructs deterministic, strictly constrained repair prompts for failed SQL queries."""

    @staticmethod
    def build_repair_prompt(
        original_query: str,
        schema_context: str,
        previous_sql: str,
        error_trace: str,
        diagnosis: DiagnosticResult,
        retrieved_memories: Optional[List[RuntimeMemory]] = None,
    ) -> str:
        """Assemble the strictly bounded repair prompt.
        
        Args:
            original_query: Natural language analytical question.
            schema_context: Deterministically pruned schema Markdown string.
            previous_sql: The failed SQL statement.
            error_trace: Raw or normalized exception trace from execution/validation.
            diagnosis: Phase 4 DiagnosticResult containing taxonomy, constraints, and repair rule.
            retrieved_memories: Optional governed RuntimeMemory items from FAISS.
            
        Returns:
            Formatted prompt string containing the [STRICT REPAIR CONSTRAINTS] block.
        """
        # Format negative constraints deterministically
        neg_constraints_list = list(diagnosis.negative_constraints)
        if neg_constraints_list:
            neg_constraints_str = ", ".join(f"'{c}'" for c in sorted(neg_constraints_list))
        else:
            neg_constraints_str = "None"

        # Format candidate replacements deterministically
        cand_list = list(diagnosis.candidate_replacements)
        if cand_list:
            cand_str = ", ".join(f"'{c}'" for c in sorted(cand_list))
        else:
            cand_str = "None"

        # Section 5 requirement: Exactly one clearly identifiable [STRICT REPAIR CONSTRAINTS] block
        strict_constraints_block = f"""[STRICT REPAIR CONSTRAINTS]

The previous query attempt failed with the following database/validation error:
{error_trace.strip()}

DIAGNOSTIC INSTRUCTIONS:

1. FORBIDDEN IDENTIFIERS:
   Do not use the identifiers [{neg_constraints_str}] anywhere in the SQL query.

2. REPLACEMENT REMAPPING:
   Choose strictly from valid schema columns: [{cand_str}].

3. OPERATIONAL RULE:
   {diagnosis.repair_rule}"""

        # Optional governed memory context
        memory_section = ""
        if retrieved_memories:
            mem_lines = []
            for mem in retrieved_memories:
                mem_lines.append(
                    f"- Memory [{mem.memory_id}] (Confidence: {mem.confidence:.2f}): "
                    f"Rule: {mem.repair_strategy} | Root Cause: {mem.root_cause}"
                )
            memory_section = f"\n\n### OPERATIONAL MEMORY CONTEXT:\n" + "\n".join(mem_lines)

        prompt = f"""### DATABASE SCHEMA:
{schema_context}

### ORIGINAL USER QUESTION:
{original_query}

### PREVIOUS FAILED SQL:
```sql
{previous_sql}
```

{strict_constraints_block}{memory_section}

### REPAIRED SQL QUERY:
Provide ONLY the corrected, executable PostgreSQL query enclosed in a ```sql ... ``` code block.
Do NOT include explanations or comments."""

        return prompt


class RepairSQLGenerator:
    """Executes repair SQL generation against local Ollama or injected test generator."""

    SYSTEM_PROMPT = """You are an expert PostgreSQL repair agent for an enterprise data warehouse.
Your job is to repair a failed SQL query to answer the user question correctly while strictly obeying all diagnostic constraints.

STRICT INSTRUCTIONS:
1. Output ONLY the executable SQL query enclosed in a ```sql ... ``` markdown code block.
2. Do NOT provide any explanations, notes, or commentary.
3. Obey every constraint in [STRICT REPAIR CONSTRAINTS] without exception.
4. Never reference forbidden identifiers.
5. Use ONLY columns that exist in the provided schema."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        generator_fn: Optional[Callable[[str], GenerationResult]] = None,
        seed: Optional[int] = None,
    ):
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.model = model or DEFAULT_LLM_MODEL
        self.timeout = timeout
        self.generator_fn = generator_fn
        self.seed = seed

    def generate_repair(self, repair_prompt: str) -> GenerationResult:
        """Generate replacement SQL query for the given repair prompt.
        
        Args:
            repair_prompt: Assembled prompt from RepairPromptBuilder.
            
        Returns:
            GenerationResult containing extracted SQL and generation metrics.
        """
        if self.generator_fn is not None:
            return self.generator_fn(repair_prompt)

        endpoint = f"{self.base_url}/api/generate"
        options = {
            "temperature": 0.0,
        }
        if self.seed is not None:
            options["seed"] = self.seed

        payload = {
            "model": self.model,
            "prompt": repair_prompt,
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
