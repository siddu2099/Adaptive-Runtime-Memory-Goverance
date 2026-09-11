"""
ARMG Phase 9: Evaluation Modes and Experimental Configurations.

Implements the six experimentally isolated evaluation configurations:
- Mode 1: Monolithic Zero-Shot Baseline
- Mode 2: Stateless Self-Correction Baseline
- Mode 3: Naive Vector RAG Baseline
- Mode 4: Full ARMG (Phase 7 Orchestration)
- Mode 5: ARMG - Negative Constraints (Ablation)
- Mode 6: ARMG - Temporal Decay (Ablation with lambda=0)

Guarantees:
- Zero modifications to frozen Phase 1-8 core semantics.
- Clean in-memory FAISS store instantiation per mode run (zero cross-mode contamination).
- Strict telemetry and result recording matching IEEE publication specifications.
"""

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import faiss
import numpy as np

from agents.repair_agent import RepairSQLGenerator
from agents.schema_introspector import SchemaIntrospector, format_catalog_to_markdown
from agents.schema_pruner import SchemaPruner
from agents.sql_generator import SQLGenerator, GenerationResult
from benchmark.equivalence import check_relational_equivalence
from environment.postgres import PostgreSQLEnvironment
from graph.state import (
    ARMGState,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_SUCCESS,
)


def create_initial_armg_state(user_query: str, max_retries: int = 3) -> Dict[str, Any]:
    """Helper to initialize the input state dictionary for the ARMG StateGraph."""
    return {"user_query": user_query, "max_retries": max_retries}

from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from memory.governance import MemoryGovernanceEngine
from memory.models import RuntimeMemory
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import ExecutionValidator


@dataclass
class QueryBenchmarkRecord:
    """Per-query evaluation record conforming to Section 10 specification."""
    run_id: str
    mode: str
    seed: int
    query_id: str
    category: str
    question: str
    success: bool
    execution_accuracy: int  # 1 or 0
    retry_count: int
    generation_attempts: int
    latency_ms: float
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    validation_failures: int
    execution_failures: int
    memory_retrieval_count: int
    memory_admission: Optional[str]
    memory_reinforcement: Optional[str]
    error_category: Optional[str]
    final_sql: str = ""
    gold_sql: str = ""
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ==============================================================================
# Mode 3: Naive Vector Store Helper
# ==============================================================================

class NaiveVectorStore:
    """Lightweight in-memory vector store for Mode 3 Naive Vector RAG.
    
    Stores raw historical (question, sql) pairs without RuntimeKnowledge abstraction,
    lifecycle governance, decay, or negative constraints.
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.records: List[Tuple[str, str]] = []

    def count(self) -> int:
        return len(self.records)

    def add(self, question: str, sql: str, embedding: List[float]) -> None:
        vec = np.array([embedding], dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        self.index.add(vec)
        self.records.append((question, sql))

    def search(self, embedding: List[float], top_k: int = 3) -> List[Tuple[str, str, float]]:
        if self.count() == 0:
            return []
        vec = np.array([embedding], dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        k = min(top_k, self.count())
        scores, indices = self.index.search(vec, k)
        results = []
        for sim, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.records):
                q, s = self.records[idx]
                results.append((q, s, float(sim)))
        return results


# ==============================================================================
# Mode 5: Ablation Workflow (Without Negative Constraints)
# ==============================================================================

class AblationNoNegConstraintsWorkflow(ARMGRepairWorkflow):
    """Subclass of ARMGRepairWorkflow that omits the [STRICT REPAIR CONSTRAINTS] block.
    
    Preserves: observation, deterministic diagnosis, knowledge extraction,
    governed memory retrieval, retry loop, memory admission, and reinforcement.
    Removes: negative-constraint injection block from repair prompt.
    """

    def repair_prompt_node(self, state: ARMGState) -> Dict[str, Any]:
        obs = state.get("observation")
        error_trace = (
            (obs.normalized_error if obs else None)
            or (obs.raw_error if obs else None)
            or state.get("validation_error")
            or "Unknown failure"
        )
        diag = state.get("diagnosis")
        retrieved_memories = state.get("retrieved_memories")

        memory_section = ""
        if retrieved_memories:
            mem_lines = []
            for mem in retrieved_memories:
                mem_lines.append(
                    f"- Memory [{mem.memory_id}] (Confidence: {mem.confidence:.2f}): "
                    f"Rule: {mem.repair_strategy} | Root Cause: {mem.root_cause}"
                )
            memory_section = f"\n\n### OPERATIONAL MEMORY CONTEXT:\n" + "\n".join(mem_lines)

        # Prompt WITHOUT [STRICT REPAIR CONSTRAINTS] block
        prompt = f"""### DATABASE SCHEMA:
{state['pruned_schema_markdown']}

### ORIGINAL USER QUESTION:
{state['user_query']}

### PREVIOUS FAILED SQL:
```sql
{state.get('generated_sql', '')}
```

The previous query attempt failed with the following database/validation error:
{error_trace.strip()}{memory_section}

### REPAIRED SQL QUERY:
Provide ONLY the corrected, executable PostgreSQL query enclosed in a ```sql ... ``` code block.
Do NOT include explanations or comments."""

        return {"repair_prompt": prompt}


# ==============================================================================
# Mode Executors
# ==============================================================================

def execute_mode_1_zero_shot(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    generator: Optional[SQLGenerator] = None,
    introspector: Optional[SchemaIntrospector] = None,
    pruner: Optional[SchemaPruner] = None,
    validator: Optional[ExecutionValidator] = None,
) -> QueryBenchmarkRecord:
    """Mode 1: Monolithic Zero-Shot Baseline."""
    generator = generator or SQLGenerator()
    introspector = introspector or SchemaIntrospector(env)
    pruner = pruner or SchemaPruner()
    validator = validator or ExecutionValidator()

    question = query_item["question"]
    qid = query_item["query_id"]
    category = query_item["category"]
    gold_sql = query_item["gold_sql"]

    start_time = time.perf_counter()

    # Step 1: Introspect and prune
    catalog = introspector.get_raw_catalog()
    pruned_tables = pruner.prune(question)
    schema_md = format_catalog_to_markdown(catalog, filter_tables=pruned_tables)

    # Step 2: Single generation attempt
    gen_res = generator.generate(question, schema_md)
    extracted_sql = gen_res.extracted_sql

    val_failures = 0
    exec_failures = 0
    error_cat = None
    fail_reason = None
    gen_rows = []
    is_success = False

    if not extracted_sql:
        val_failures = 1
        fail_reason = "Empty SQL generated"
        error_cat = "SyntaxError"
    else:
        # Step 3: AST validation
        is_valid, val_err = validator.validate(extracted_sql)
        if not is_valid:
            val_failures = 1
            fail_reason = f"AST validation rejected: {val_err}"
            error_cat = "SyntaxError"
        else:
            # Step 4: PostgreSQL execution
            exec_res = env.execute(extracted_sql)
            if exec_res.is_success:
                is_success = True
                gen_rows = exec_res.rows
            else:
                exec_failures = 1
                fail_reason = exec_res.error
                obs_dict = env.observe(exec_res.error or "")
                error_cat = obs_dict.get("error_class", "DatabaseError")

    total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    # Relational Equivalence
    gold_exec = env.execute(gold_sql)
    exec_acc = 0
    if is_success and gold_exec.is_success:
        if check_relational_equivalence(
            gen_rows=gen_rows,
            gold_rows=gold_exec.rows,
            gold_sql=gold_sql,
            gen_sql=extracted_sql,
            gen_success=True,
            gold_success=True,
        ):
            exec_acc = 1

    total_tokens = (
        (gen_res.prompt_tokens or 0) + (gen_res.completion_tokens or 0)
        if gen_res.prompt_tokens is not None
        else None
    )

    return QueryBenchmarkRecord(
        run_id=run_id,
        mode="Mode 1 (Zero-Shot)",
        seed=seed,
        query_id=qid,
        category=category,
        question=question,
        success=is_success,
        execution_accuracy=exec_acc,
        retry_count=0,
        generation_attempts=1,
        latency_ms=total_latency_ms,
        prompt_tokens=gen_res.prompt_tokens,
        completion_tokens=gen_res.completion_tokens,
        total_tokens=total_tokens,
        validation_failures=val_failures,
        execution_failures=exec_failures,
        memory_retrieval_count=0,
        memory_admission=None,
        memory_reinforcement=None,
        error_category=error_cat,
        final_sql=extracted_sql,
        gold_sql=gold_sql,
        failure_reason=fail_reason,
    )


def execute_mode_2_self_correction(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    generator: Optional[SQLGenerator] = None,
    repair_generator: Optional[RepairSQLGenerator] = None,
    introspector: Optional[SchemaIntrospector] = None,
    pruner: Optional[SchemaPruner] = None,
    validator: Optional[ExecutionValidator] = None,
    max_retries: int = 3,
) -> QueryBenchmarkRecord:
    """Mode 2: Stateless Self-Correction Baseline."""
    generator = generator or SQLGenerator()
    repair_generator = repair_generator or RepairSQLGenerator()
    introspector = introspector or SchemaIntrospector(env)
    pruner = pruner or SchemaPruner()
    validator = validator or ExecutionValidator()

    question = query_item["question"]
    qid = query_item["query_id"]
    category = query_item["category"]
    gold_sql = query_item["gold_sql"]

    start_time = time.perf_counter()

    catalog = introspector.get_raw_catalog()
    pruned_tables = pruner.prune(question)
    schema_md = format_catalog_to_markdown(catalog, filter_tables=pruned_tables)

    total_prompt_tokens = 0
    total_completion_tokens = 0
    val_failures = 0
    exec_failures = 0
    retries = 0
    gen_attempts = 0
    current_sql = ""
    is_success = False
    gen_rows = []
    error_cat = None
    last_error = ""

    # Initial attempt
    gen_attempts += 1
    gen_res = generator.generate(question, schema_md)
    current_sql = gen_res.extracted_sql
    if gen_res.prompt_tokens is not None:
        total_prompt_tokens += gen_res.prompt_tokens
        total_completion_tokens += gen_res.completion_tokens or 0

    while True:
        # Validate AST
        is_valid, val_err = validator.validate(current_sql)
        if not is_valid:
            val_failures += 1
            last_error = val_err or "SQLGlot validation failed"
            error_cat = "SyntaxError"
            need_repair = True
        else:
            # Execute on PostgreSQL
            exec_res = env.execute(current_sql)
            if exec_res.is_success:
                is_success = True
                gen_rows = exec_res.rows
                need_repair = False
                break
            else:
                exec_failures += 1
                last_error = exec_res.error or "Execution error"
                obs_dict = env.observe(last_error)
                error_cat = obs_dict.get("error_class", "DatabaseError")
                need_repair = True

        if need_repair:
            if retries >= max_retries:
                # Exhausted repair budget
                break
            retries += 1
            gen_attempts += 1

            # Build stateless repair prompt without negative constraints or diagnosis
            repair_prompt = f"""### DATABASE SCHEMA:
{schema_md}

### USER QUESTION:
{question}

### PREVIOUS FAILED SQL:
```sql
{current_sql}
```

The previous SQL query failed with the following error:
{last_error}

### REPAIRED SQL QUERY:
Provide ONLY the corrected, executable PostgreSQL query enclosed in a ```sql ... ``` code block.
Do NOT include explanations or comments."""

            rep_res = repair_generator.generate_repair(repair_prompt)
            current_sql = rep_res.extracted_sql
            if rep_res.prompt_tokens is not None:
                total_prompt_tokens += rep_res.prompt_tokens
                total_completion_tokens += rep_res.completion_tokens or 0

    total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    gold_exec = env.execute(gold_sql)
    exec_acc = 0
    if is_success and gold_exec.is_success:
        if check_relational_equivalence(
            gen_rows=gen_rows,
            gold_rows=gold_exec.rows,
            gold_sql=gold_sql,
            gen_sql=current_sql,
            gen_success=True,
            gold_success=True,
        ):
            exec_acc = 1

    total_tokens = total_prompt_tokens + total_completion_tokens if total_prompt_tokens > 0 else None

    return QueryBenchmarkRecord(
        run_id=run_id,
        mode="Mode 2 (Stateless Self-Correction)",
        seed=seed,
        query_id=qid,
        category=category,
        question=question,
        success=is_success,
        execution_accuracy=exec_acc,
        retry_count=retries,
        generation_attempts=gen_attempts,
        latency_ms=total_latency_ms,
        prompt_tokens=total_prompt_tokens if total_prompt_tokens > 0 else None,
        completion_tokens=total_completion_tokens if total_completion_tokens > 0 else None,
        total_tokens=total_tokens,
        validation_failures=val_failures,
        execution_failures=exec_failures,
        memory_retrieval_count=0,
        memory_admission=None,
        memory_reinforcement=None,
        error_category=error_cat,
        final_sql=current_sql,
        gold_sql=gold_sql,
        failure_reason=last_error if not is_success else None,
    )


def execute_mode_3_naive_rag(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    naive_store: NaiveVectorStore,
    embed_fn: Optional[Callable[[str], Optional[List[float]]]] = None,
    generator: Optional[SQLGenerator] = None,
    introspector: Optional[SchemaIntrospector] = None,
    pruner: Optional[SchemaPruner] = None,
    validator: Optional[ExecutionValidator] = None,
) -> QueryBenchmarkRecord:
    """Mode 3: Naive Vector RAG Baseline."""
    generator = generator or SQLGenerator()
    introspector = introspector or SchemaIntrospector(env)
    pruner = pruner or SchemaPruner()
    validator = validator or ExecutionValidator()
    embed_fn = embed_fn or default_embed_fn

    question = query_item["question"]
    qid = query_item["query_id"]
    category = query_item["category"]
    gold_sql = query_item["gold_sql"]

    start_time = time.perf_counter()

    catalog = introspector.get_raw_catalog()
    pruned_tables = pruner.prune(question)
    schema_md = format_catalog_to_markdown(catalog, filter_tables=pruned_tables)

    # Retrieval from naive store
    retrieved_count = 0
    few_shot_examples = ""
    query_vec = embed_fn(question) if embed_fn else None

    if query_vec is not None and naive_store.count() > 0:
        matches = naive_store.search(query_vec, top_k=3)
        retrieved_count = len(matches)
        if matches:
            ex_lines = []
            for i, (m_q, m_s, score) in enumerate(matches, 1):
                ex_lines.append(f"Example {i}:\nQuestion: {m_q}\nSQL:\n```sql\n{m_s}\n```")
            few_shot_examples = "\n\n### RELEVANT PREVIOUS EXAMPLES:\n" + "\n\n".join(ex_lines)

    # Prompt with raw few-shot examples
    prompt_schema_with_rag = schema_md + few_shot_examples
    gen_res = generator.generate(question, prompt_schema_with_rag)
    extracted_sql = gen_res.extracted_sql

    val_failures = 0
    exec_failures = 0
    error_cat = None
    fail_reason = None
    gen_rows = []
    is_success = False

    if not extracted_sql:
        val_failures = 1
        fail_reason = "Empty SQL generated"
        error_cat = "SyntaxError"
    else:
        is_valid, val_err = validator.validate(extracted_sql)
        if not is_valid:
            val_failures = 1
            fail_reason = f"AST validation rejected: {val_err}"
            error_cat = "SyntaxError"
        else:
            exec_res = env.execute(extracted_sql)
            if exec_res.is_success:
                is_success = True
                gen_rows = exec_res.rows
                # Naive memory update upon success
                if query_vec is not None:
                    naive_store.add(question, extracted_sql, query_vec)
            else:
                exec_failures = 1
                fail_reason = exec_res.error
                obs_dict = env.observe(exec_res.error or "")
                error_cat = obs_dict.get("error_class", "DatabaseError")

    total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    gold_exec = env.execute(gold_sql)
    exec_acc = 0
    if is_success and gold_exec.is_success:
        if check_relational_equivalence(
            gen_rows=gen_rows,
            gold_rows=gold_exec.rows,
            gold_sql=gold_sql,
            gen_sql=extracted_sql,
            gen_success=True,
            gold_success=True,
        ):
            exec_acc = 1

    total_tokens = (
        (gen_res.prompt_tokens or 0) + (gen_res.completion_tokens or 0)
        if gen_res.prompt_tokens is not None
        else None
    )

    return QueryBenchmarkRecord(
        run_id=run_id,
        mode="Mode 3 (Naive Vector RAG)",
        seed=seed,
        query_id=qid,
        category=category,
        question=question,
        success=is_success,
        execution_accuracy=exec_acc,
        retry_count=0,
        generation_attempts=1,
        latency_ms=total_latency_ms,
        prompt_tokens=gen_res.prompt_tokens,
        completion_tokens=gen_res.completion_tokens,
        total_tokens=total_tokens,
        validation_failures=val_failures,
        execution_failures=exec_failures,
        memory_retrieval_count=retrieved_count,
        memory_admission="NAIVE_STORED" if is_success else None,
        memory_reinforcement=None,
        error_category=error_cat,
        final_sql=extracted_sql,
        gold_sql=gold_sql,
        failure_reason=fail_reason,
    )


def execute_mode_4_full_armg(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    workflow_app: Any,
    max_retries: int = 3,
) -> QueryBenchmarkRecord:
    """Mode 4: Full ARMG Architecture."""
    question = query_item["question"]
    qid = query_item["query_id"]
    category = query_item["category"]
    gold_sql = query_item["gold_sql"]

    start_time = time.perf_counter()

    initial_state = create_initial_armg_state(user_query=question, max_retries=max_retries)
    final_state = workflow_app.invoke(initial_state)

    total_latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    status = final_state.get("status")
    is_success = (status == STATUS_SUCCESS)
    exec_res = final_state.get("execution_result")
    gen_sql = final_state.get("generated_sql", "")
    telemetry = final_state.get("telemetry", {})
    retry_count = final_state.get("retry_count", 0)
    gen_attempts = telemetry.get("generation_attempts", 1)

    val_failures = 1 if not final_state.get("validation_passed", True) else 0
    exec_failures = 1 if (exec_res and not exec_res.is_success) else 0

    obs = final_state.get("observation")
    diag = final_state.get("diagnosis")
    error_cat = diag.taxonomy_category.value if diag else None

    # Gold SQL execution and equivalence check
    gold_exec = env.execute(gold_sql)
    exec_acc = 0
    if is_success and gold_exec.is_success and exec_res is not None:
        if check_relational_equivalence(
            gen_rows=exec_res.rows,
            gold_rows=gold_exec.rows,
            gold_sql=gold_sql,
            gen_sql=gen_sql,
            gen_success=True,
            gold_success=True,
        ):
            exec_acc = 1

    fail_reason = None
    if not is_success:
        fail_reason = (
            (obs.normalized_error if obs else None)
            or (obs.raw_error if obs else None)
            or (exec_res.error if exec_res else None)
            or "Repair budget exhausted without success"
        )

    return QueryBenchmarkRecord(
        run_id=run_id,
        mode="Mode 4 (Full ARMG)",
        seed=seed,
        query_id=qid,
        category=category,
        question=question,
        success=is_success,
        execution_accuracy=exec_acc,
        retry_count=retry_count,
        generation_attempts=gen_attempts,
        latency_ms=total_latency_ms,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=telemetry.get("total_tokens"),
        validation_failures=val_failures,
        execution_failures=exec_failures,
        memory_retrieval_count=telemetry.get("memory_retrieval_count", 0),
        memory_admission=telemetry.get("memory_admission"),
        memory_reinforcement=telemetry.get("reinforced_memory_id"),
        error_category=error_cat,
        final_sql=gen_sql,
        gold_sql=gold_sql,
        failure_reason=fail_reason,
    )


def execute_mode_5_armg_no_neg_constraints(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    workflow_app: Any,
    max_retries: int = 3,
) -> QueryBenchmarkRecord:
    """Mode 5: Ablation - ARMG without Negative Constraints."""
    rec = execute_mode_4_full_armg(
        query_item=query_item,
        env=env,
        run_id=run_id,
        seed=seed,
        workflow_app=workflow_app,
        max_retries=max_retries,
    )
    rec.mode = "Mode 5 (ARMG - Negative Constraints)"
    return rec


def execute_mode_6_armg_no_decay(
    query_item: Dict[str, Any],
    env: PostgreSQLEnvironment,
    run_id: str,
    seed: int,
    workflow_app: Any,
    max_retries: int = 3,
) -> QueryBenchmarkRecord:
    """Mode 6: Ablation - ARMG without Temporal Decay (lambda=0)."""
    rec = execute_mode_4_full_armg(
        query_item=query_item,
        env=env,
        run_id=run_id,
        seed=seed,
        workflow_app=workflow_app,
        max_retries=max_retries,
    )
    rec.mode = "Mode 6 (ARMG - Temporal Decay)"
    return rec
