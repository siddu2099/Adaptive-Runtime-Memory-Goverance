"""
ARMG Phase 7: LangGraph Repair Orchestration Workflow.

Connects the verified components:
    User Query -> Schema Introspection -> Governed Memory Retrieval ->
    SQL Generation -> SQLGlot Validation -> PostgreSQL Execution ->
    RuntimeObservation -> Deterministic Diagnosis -> RuntimeKnowledge ->
    Strict Repair Prompt -> SQL Regeneration -> Validation -> Execution ->
    Success / Bounded Failure

Bounded retry semantics:
    max_retries = 3
    retry_count = 0 (Initial attempt)
    retry_count = 1 (First repair retry)
    retry_count = 2 (Second repair retry)
    retry_count = 3 (Third repair retry)
    Termination: status = "FAILED", retry_count = 3 (No fourth repair)
"""

import logging
import math
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import requests
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from agents.error_diagnosis import DeterministicErrorDiagnoser
from agents.repair_agent import RepairPromptBuilder, RepairSQLGenerator
from agents.schema_introspector import SchemaIntrospector
from agents.schema_pruner import SchemaPruner
from agents.sql_generator import SQLGenerator
from environment.base import ExecutionResult, RuntimeEnvironment
from environment.observation import ExecutionStatus, RuntimeObservation
from environment.observer import RuntimeObserver
from graph.state import (
    ARMGState,
    CONTROLLED_STATUSES,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_RUNNING,
    STATUS_SUCCESS,
)
from memory.governance import MemoryGovernanceEngine
from memory.knowledge_extractor import RuntimeKnowledgeExtractor
from memory.models import RuntimeKnowledge, RuntimeMemory
from memory.telemetry import RetrievalTelemetryLogger, get_telemetry_logger
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import ExecutionValidator

logger = logging.getLogger(__name__)

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


def default_embed_fn(
    text: str, base_url: str = OLLAMA_BASE_URL, timeout: int = 30
) -> Optional[List[float]]:
    """Generate 768-dimensional embedding vector via local nomic-embed-text.
    
    Validates:
    - Exactly 768 dimensions
    - Float32 values
    - Finite numerical sanity (no NaN, Inf)
    - Positive finite L2 norm
    - Strict unit L2 normalization (||v||₂ ≈ 1.0)
    """
    try:
        endpoint = f"{base_url}/api/embeddings"
        payload = {"model": EMBEDDING_MODEL, "prompt": text}
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        embedding = response.json().get("embedding")
        if not embedding or len(embedding) != 768:
            return None
        v = np.array(embedding, dtype=np.float32)
        if not np.isfinite(v).all():
            return None
        norm = float(np.linalg.norm(v))
        if not np.isfinite(norm) or norm <= 0.0:
            return None
        v_norm = v / norm
        return v_norm.tolist()
    except Exception as e:
        logger.warning("default_embed_fn failed (%s): %s: %s", endpoint, type(e).__name__, e)
        return None


class ARMGRepairWorkflow:
    """Encapsulates LangGraph nodes, edges, and dependencies for ARMG Runtime-Guided Repair."""

    def __init__(
        self,
        environment: RuntimeEnvironment,
        introspector: Optional[SchemaIntrospector] = None,
        pruner: Optional[SchemaPruner] = None,
        sql_generator: Optional[SQLGenerator] = None,
        repair_generator: Optional[RepairSQLGenerator] = None,
        validator: Optional[ExecutionValidator] = None,
        observer: Optional[RuntimeObserver] = None,
        diagnoser: Optional[DeterministicErrorDiagnoser] = None,
        knowledge_extractor: Optional[RuntimeKnowledgeExtractor] = None,
        governance_engine: Optional[MemoryGovernanceEngine] = None,
        vector_store: Optional[FAISSMemoryStore] = None,
        embed_fn: Optional[Callable[[str], Optional[List[float]]]] = None,
        telemetry_logger: Optional[RetrievalTelemetryLogger] = None,
    ):
        self.environment = environment
        self.introspector = introspector or SchemaIntrospector(environment)
        self.pruner = pruner or SchemaPruner()
        self.sql_generator = sql_generator or SQLGenerator()
        self.repair_generator = repair_generator or RepairSQLGenerator()
        self.validator = validator or ExecutionValidator()
        self.observer = observer or RuntimeObserver()
        self.diagnoser = diagnoser or DeterministicErrorDiagnoser()
        self.knowledge_extractor = knowledge_extractor or RuntimeKnowledgeExtractor()
        self.governance_engine = governance_engine or MemoryGovernanceEngine()
        self.vector_store = vector_store or FAISSMemoryStore()
        self.embed_fn = embed_fn or default_embed_fn
        self.telemetry_logger = telemetry_logger

    # =========================================================================
    # Nodes (Section 12)
    # =========================================================================

    def introspect_and_prune_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 1: Inspect database catalog and deterministically prune schema for query."""
        schema_context = state.get("schema_context")
        if not schema_context:
            schema_context = self.environment.inspect()

        pruned_tables = self.pruner.prune(state["user_query"])
        pruned_markdown = self.introspector.get_schema_markdown(filter_tables=pruned_tables)

        telemetry = dict(state.get("telemetry", {}))
        telemetry.setdefault("generation_latency_ms", 0.0)
        telemetry.setdefault("validation_latency_ms", 0.0)
        telemetry.setdefault("execution_latency_ms", 0.0)
        telemetry.setdefault("total_tokens", 0)
        telemetry.setdefault("repair_count", 0)
        telemetry.setdefault("generation_attempts", 0)

        return {
            "schema_context": schema_context,
            "pruned_schema_markdown": pruned_markdown,
            "status": STATUS_RUNNING,
            "telemetry": telemetry,
            "retry_count": state.get("retry_count", 0),
            "max_retries": state.get("max_retries", 3),
        }

    def memory_retrieval_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 2: Retrieve relevant governed memories from FAISS vector store with full telemetry."""
        retrieved: List[RuntimeMemory] = []
        telemetry = dict(state.get("telemetry", {}))
        run_id = telemetry.get("run_id", "default_run")
        mode = telemetry.get("mode", "Mode 4 (Full ARMG)")
        query_id = telemetry.get("query_id", state.get("query_id", "Q00"))
        store_size_before = self.vector_store.count()
        top_k = 3
        threshold = 0.50

        t_logger = self.telemetry_logger or get_telemetry_logger()
        raw_candidates_telemetry: List[Dict[str, Any]] = []

        if store_size_before == 0 or self.embed_fn is None:
            # Section 6: Empty-Store Semantics
            if t_logger:
                t_logger.log_retrieval_event(
                    run_id=run_id,
                    mode=mode,
                    query_id=query_id,
                    candidates=[],
                    retrieval_count=0,
                    accepted_memory_count=0,
                    store_size_before=store_size_before,
                    top_k=top_k,
                    threshold=threshold,
                )
        else:
            query_vec = self.embed_fn(state["user_query"])
            if query_vec is None:
                if t_logger:
                    t_logger.log_retrieval_event(
                        run_id=run_id,
                        mode=mode,
                        query_id=query_id,
                        candidates=[],
                        retrieval_count=0,
                        accepted_memory_count=0,
                        store_size_before=store_size_before,
                        top_k=top_k,
                        threshold=threshold,
                    )
            else:
                # Section 4: Capture ALL candidates returned by FAISS index.search() before threshold and governance filtering
                raw_matches = self.vector_store.search_raw_candidates(query_vec, top_k=top_k)
                for mem, rank, d2, sim in raw_matches:
                    passed_thresh = bool(sim >= threshold)
                    is_active = mem.status.value not in ("ARCHIVED", "DELETED")
                    if passed_thresh and is_active:
                        retrieved.append(mem)

                    raw_candidates_telemetry.append({
                        "memory_id": mem.memory_id,
                        "rank": rank,
                        "distance_l2_sq": d2,
                        "similarity": sim,
                        "passed_retrieval_threshold": passed_thresh,
                    })

                if t_logger:
                    t_logger.log_retrieval_event(
                        run_id=run_id,
                        mode=mode,
                        query_id=query_id,
                        candidates=raw_candidates_telemetry,
                        retrieval_count=len(retrieved),
                        accepted_memory_count=len(retrieved),
                        store_size_before=store_size_before,
                        top_k=top_k,
                        threshold=threshold,
                    )

        telemetry["memory_retrieval_count"] = len(retrieved)

        return {
            "retrieved_memories": retrieved,
            "telemetry": telemetry,
        }

    def sql_generator_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 3: Generate initial SQL query or replacement repair query."""
        telemetry = dict(state.get("telemetry", {}))
        telemetry["generation_attempts"] = telemetry.get("generation_attempts", 0) + 1

        repair_prompt = state.get("repair_prompt")
        prev_exec_err = None
        if repair_prompt:
            # Repair attempt
            prev_sql = state.get("generated_sql")
            if state.get("execution_result") and not state["execution_result"].is_success:
                prev_exec_err = state["execution_result"].error
                telemetry["previous_execution_error"] = prev_exec_err
            elif state.get("validation_error"):
                prev_exec_err = state["validation_error"]
                telemetry["previous_execution_error"] = prev_exec_err
            gen_result = self.repair_generator.generate_repair(repair_prompt)
        else:
            # Initial generation attempt
            prev_sql = None
            gen_result = self.sql_generator.generate(
                question=state["user_query"],
                schema_markdown=state["pruned_schema_markdown"],
            )

        telemetry["generation_latency_ms"] = round(
            telemetry.get("generation_latency_ms", 0.0) + gen_result.generation_duration_ms, 3
        )
        tokens = (gen_result.prompt_tokens or 0) + (gen_result.completion_tokens or 0)
        telemetry["total_tokens"] = telemetry.get("total_tokens", 0) + tokens

        return {
            "generated_sql": gen_result.extracted_sql,
            "previous_sql": prev_sql,
            "previous_execution_error": prev_exec_err,
            "repair_prompt": None,
            "execution_result": None,
            "diagnosis": None,
            "telemetry": telemetry,
        }

    def ast_guard_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 4: Validate generated SQL via SQLGlot AST guardrail."""
        sql = state.get("generated_sql", "")
        start_time = time.perf_counter()
        is_valid, error_reason = self.validator.validate(sql)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry = dict(state.get("telemetry", {}))
        telemetry["validation_latency_ms"] = round(
            telemetry.get("validation_latency_ms", 0.0) + duration_ms, 3
        )

        is_safety = False
        safety_cat = None
        if not is_valid:
            is_safety, safety_cat = self.validator.classify_safety_violation(sql)

        return {
            "validation_passed": is_valid,
            "validation_error": error_reason if not is_valid else None,
            "is_safety_violation": is_safety,
            "safety_category": safety_cat,
            "telemetry": telemetry,
        }

    def postgres_executor_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 5: Execute validated SQL query against PostgreSQL warehouse."""
        sql = state.get("generated_sql", "")
        exec_res = self.environment.execute(sql)

        telemetry = dict(state.get("telemetry", {}))
        telemetry["execution_latency_ms"] = round(
            telemetry.get("execution_latency_ms", 0.0) + exec_res.execution_time_ms, 3
        )

        return {
            "execution_result": exec_res,
            "telemetry": telemetry,
        }

    def observation_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 6: Construct immutable RuntimeObservation from validation or execution outcome."""
        schema_ctx = state.get("schema_context", {})
        table_names = list(schema_ctx.get("tables", {}).keys())

        query_sql = state.get("generated_sql", "")
        if not state.get("validation_passed", True):
            # Validation failure observation
            obs = self.observer.observe_validation_failure(
                query=query_sql,
                validation_error=state.get("validation_error") or "SQLGlot validation failed",
                schema_context=table_names,
            )
            # Deterministic check: explicit safety violations terminate immediately as STATUS_BLOCKED
            if state.get("is_safety_violation", False):
                status = STATUS_BLOCKED
                return {
                    "observation": obs,
                    "status": status,
                    "execution_result": None,
                    "diagnosis": None,
                    "runtime_knowledge": None,
                }
            else:
                status = STATUS_RETRYING
        else:
            # Execution outcome observation
            exec_res = state.get("execution_result")
            if exec_res is None:
                exec_res = ExecutionResult(status="FAILURE", query=query_sql, error="No execution result")
            obs = self.observer.observe_execution(
                query=query_sql,
                result=exec_res,
                schema_context=table_names,
            )
            status = STATUS_SUCCESS if exec_res.is_success else STATUS_RETRYING

        return {
            "observation": obs,
            "status": status,
        }


    def diagnosis_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 7: Deterministically diagnose failure using Phase 4 taxonomy engine."""
        obs = state.get("observation")
        if obs is None:
            raise ValueError("Observation is required for error diagnosis")
        diag = self.diagnoser.diagnose(obs, state.get("schema_context", {}))
        return {
            "diagnosis": diag,
        }

    def knowledge_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 8: Extract ephemeral RuntimeKnowledge and evaluate retry budget."""
        obs = state.get("observation")
        diag = state.get("diagnosis")
        schema_ctx = state.get("schema_context", {})
        if obs is None or diag is None:
            raise ValueError("Observation and diagnosis are required for knowledge extraction")

        knowledge = self.knowledge_extractor.extract(obs, diag, schema_ctx)

        curr_retry = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        telemetry = dict(state.get("telemetry", {}))

        if curr_retry < max_retries:
            new_retry = curr_retry + 1
            new_status = STATUS_RETRYING
            telemetry["repair_count"] = telemetry.get("repair_count", 0) + 1
        else:
            # Exhausted all 3 repair retries
            new_retry = max_retries
            new_status = STATUS_FAILED

        # Invariant (Phase 1A): Provenance must be evaluated per-attempt.
        # A memory is applied ONLY if it directly matches THIS attempt's diagnosis/rule.
        # A stale applied_memory_id from a prior failed attempt must not persist across retries.
        applied_id: Optional[str] = None
        if state.get("retrieved_memories"):
            for mem in state["retrieved_memories"]:
                if mem.root_cause == diag.root_cause or mem.repair_strategy == diag.repair_rule:
                    applied_id = mem.memory_id
                    break

        repair_history = list(state.get("repair_history") or telemetry.get("repair_history") or [])
        repair_history.append({
            "attempt": new_retry,
            "taxonomy_category": diag.taxonomy_category.value if diag.taxonomy_category else None,
            "root_cause": diag.root_cause,
            "repair_rule": diag.repair_rule,
            "candidate_memories": [m.memory_id for m in (state.get("retrieved_memories") or [])],
            "applied_memory_id": applied_id,
        })
        telemetry["repair_history"] = repair_history

        return {
            "runtime_knowledge": knowledge,
            "applied_memory_id": applied_id,
            "repair_history": repair_history,
            "retry_count": new_retry,
            "status": new_status,
            "telemetry": telemetry,
        }

    def repair_prompt_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 9: Assemble strict repair prompt containing [STRICT REPAIR CONSTRAINTS]."""
        obs = state.get("observation")
        error_trace = (
            (obs.normalized_error if obs else None)
            or (obs.raw_error if obs else None)
            or state.get("validation_error")
            or "Unknown failure"
        )
        diag = state.get("diagnosis")
        if diag is None:
            raise ValueError("Diagnosis is required to build repair prompt")

        prompt = RepairPromptBuilder.build_repair_prompt(
            original_query=state["user_query"],
            schema_context=state["pruned_schema_markdown"],
            previous_sql=state.get("generated_sql", ""),
            error_trace=error_trace,
            diagnosis=diag,
            retrieved_memories=state.get("retrieved_memories"),
        )

        return {
            "repair_prompt": prompt,
        }

    def memory_governance_node(self, state: ARMGState) -> Dict[str, Any]:
        """Node 10: Govern memory admission and reinforcement upon final terminal outcome."""
        telemetry = dict(state.get("telemetry", {}))
        status = state.get("status", STATUS_FAILED)
        retry_count = state.get("retry_count", 0)
        applied_id = state.get("applied_memory_id")

        t_logger = self.telemetry_logger or get_telemetry_logger()
        run_id = telemetry.get("run_id", "default_run")
        mode = telemetry.get("mode", "Mode 4 (Full ARMG)")
        query_id = telemetry.get("query_id", state.get("query_id", "Q00"))

        if status == STATUS_BLOCKED:
            # Explicit safety policy violation: terminal block
            # Enforces: zero admission, zero reinforcement, zero FAISS insertion
            telemetry["memory_admission"] = "SAFETY_VIOLATION_BLOCKED"
            telemetry["terminal_reason"] = state.get("safety_category", "safety_rejection")
            if t_logger:
                t_logger.update_store_size_after_query(query_id=query_id, mode=mode, store_size_after=self.vector_store.count())
            return {
                "status": status,
                "execution_result": None,
                "diagnosis": None,
                "runtime_knowledge": None,
                "telemetry": telemetry,
            }

        elif status == STATUS_SUCCESS:
            # If an existing memory was explicitly used as the repair rule, reinforce ONLY that memory
            if applied_id:
                existing_mem = self.vector_store.get(applied_id)
                if existing_mem and existing_mem.embedding:
                    reinforced = self.governance_engine.record_success(existing_mem)
                    self.vector_store.add(reinforced, reinforced.embedding)
                    telemetry["reinforced_memory_id"] = applied_id
                    telemetry["memory_admission"] = "EXISTING_REINFORCED"
            elif retry_count > 0 and state.get("runtime_knowledge"):
                # Causal evidence: failure -> repair -> PostgreSQL SUCCESS without prior memory
                rk = state["runtime_knowledge"]
                embed_text = rk.format_for_embedding()
                vec = self.embed_fn(embed_text) if self.embed_fn else None

                if vec is not None and len(vec) == 768:
                    admitted = self.governance_engine.admit(rk, embedding=vec, context_similarity=1.0)
                    conf = rk.confidence
                    succ = 0.5
                    sim = 1.0
                    rec = 1.0
                    utility = (
                        admitted.utility
                        if admitted is not None
                        else self.governance_engine.calculate_utility(
                            context_similarity=sim,
                            delta_t=0.0,
                            confidence=conf,
                            successful_uses=0,
                            total_uses=0,
                        )
                    )
                    thresh = self.governance_engine.admission_threshold
                    is_admitted = (admitted is not None)

                    if admitted is not None:
                        # Positively reinforce admitted operational knowledge
                        recorded = self.governance_engine.record_success(admitted)
                        self.vector_store.add(recorded, vec)
                        telemetry["memory_admission"] = "ADMITTED"
                        telemetry["admitted_memory_id"] = recorded.memory_id
                        mem_id = recorded.memory_id
                    else:
                        telemetry["memory_admission"] = "REJECTED_BELOW_THRESHOLD"
                        mem_id = None

                    if t_logger:
                        t_logger.log_admission_event(
                            run_id=run_id,
                            mode=mode,
                            query_id=query_id,
                            memory_id=mem_id,
                            admission_utility=utility,
                            memory_admitted=is_admitted,
                            threshold=thresh,
                            confidence=conf,
                            success_rate=succ,
                            similarity=sim,
                            recency=rec,
                        )
                else:
                    telemetry["memory_admission"] = "EMBEDDING_FAILED"

        elif status == STATUS_FAILED:
            # Terminal failure: do NOT admit current runtime knowledge
            telemetry["memory_admission"] = "TERMINAL_FAILURE_NOT_ADMITTED"
            # If an existing memory was used and failed, penalize ONLY that memory
            if applied_id:
                existing_mem = self.vector_store.get(applied_id)
                if existing_mem and existing_mem.embedding:
                    penalized = self.governance_engine.record_failure(existing_mem)
                    self.vector_store.add(penalized, penalized.embedding)

        # Update terminal store size after query across all retrieval records for this query
        if t_logger:
            store_size_after = self.vector_store.count()
            t_logger.update_store_size_after_query(
                query_id=query_id,
                mode=mode,
                store_size_after=store_size_after,
            )

        # Annotate terminal status and reinforcement in repair history
        repair_history = list(state.get("repair_history") or telemetry.get("repair_history") or [])
        if repair_history:
            repair_history[-1]["terminal_status"] = status
            if status == STATUS_SUCCESS and applied_id:
                repair_history[-1]["reinforced_memory_id"] = applied_id
            telemetry["repair_history"] = repair_history

        # Compute total latency
        telemetry["total_latency_ms"] = round(
            telemetry.get("generation_latency_ms", 0.0)
            + telemetry.get("validation_latency_ms", 0.0)
            + telemetry.get("execution_latency_ms", 0.0),
            3,
        )

        return {
            "status": status,
            "telemetry": telemetry,
        }

    # =========================================================================
    # Conditional Routing Edges (Sections 13, 14, 15, 19)
    # =========================================================================

    @staticmethod
    def route_after_ast_guard(state: ARMGState) -> str:
        """Route to PostgreSQL executor if valid, else route directly to observation."""
        if state.get("validation_passed", False):
            return "postgres_executor_node"
        return "observation_node"

    @staticmethod
    def route_after_observation(state: ARMGState) -> str:
        """Route to memory governance if successful or blocked, else route to error diagnosis."""
        if state.get("status") in (STATUS_SUCCESS, STATUS_BLOCKED):
            return "memory_governance_node"
        return "diagnosis_node"


    @staticmethod
    def route_after_knowledge(state: ARMGState) -> str:
        """Route to repair prompt if retries remain, else terminate to memory governance."""
        if state.get("status") == STATUS_RETRYING:
            return "repair_prompt_node"
        return "memory_governance_node"

    # =========================================================================
    # Graph Construction
    # =========================================================================

    def build_graph(self) -> Any:
        """Construct and compile the complete LangGraph StateGraph."""
        workflow = StateGraph(ARMGState)

        # Register nodes
        workflow.add_node("introspect_and_prune_node", self.introspect_and_prune_node)
        workflow.add_node("memory_retrieval_node", self.memory_retrieval_node)
        workflow.add_node("sql_generator_node", self.sql_generator_node)
        workflow.add_node("ast_guard_node", self.ast_guard_node)
        workflow.add_node("postgres_executor_node", self.postgres_executor_node)
        workflow.add_node("observation_node", self.observation_node)
        workflow.add_node("diagnosis_node", self.diagnosis_node)
        workflow.add_node("knowledge_node", self.knowledge_node)
        workflow.add_node("repair_prompt_node", self.repair_prompt_node)
        workflow.add_node("memory_governance_node", self.memory_governance_node)

        # Initial execution path
        workflow.add_edge(START, "introspect_and_prune_node")
        workflow.add_edge("introspect_and_prune_node", "memory_retrieval_node")
        workflow.add_edge("memory_retrieval_node", "sql_generator_node")
        workflow.add_edge("sql_generator_node", "ast_guard_node")

        # Conditional branch after AST guard: pass -> execute, fail -> observe
        workflow.add_conditional_edges(
            "ast_guard_node",
            self.route_after_ast_guard,
            {
                "postgres_executor_node": "postgres_executor_node",
                "observation_node": "observation_node",
            },
        )

        # Postgres executor always feeds observation
        workflow.add_edge("postgres_executor_node", "observation_node")

        # Conditional branch after observation: success -> governance, failure -> diagnosis
        workflow.add_conditional_edges(
            "observation_node",
            self.route_after_observation,
            {
                "memory_governance_node": "memory_governance_node",
                "diagnosis_node": "diagnosis_node",
            },
        )

        # Diagnosis feeds knowledge
        workflow.add_edge("diagnosis_node", "knowledge_node")

        # Conditional branch after knowledge: retrying -> repair prompt, failed -> governance
        workflow.add_conditional_edges(
            "knowledge_node",
            self.route_after_knowledge,
            {
                "repair_prompt_node": "repair_prompt_node",
                "memory_governance_node": "memory_governance_node",
            },
        )

        # Repair prompt feeds SQL generator for regeneration
        workflow.add_edge("repair_prompt_node", "sql_generator_node")

        # Final exit from governance
        workflow.add_edge("memory_governance_node", END)

        return workflow.compile()
