"""
ARMG Phase 7: LangGraph State Definition.

Defines the strongly-typed ARMGState dictionary and controlled operational status constants.
"""

from typing import Any, Dict, List, Optional, TypedDict

from agents.error_diagnosis import DiagnosticResult
from environment.base import ExecutionResult
from environment.observation import RuntimeObservation
from memory.models import RuntimeKnowledge, RuntimeMemory

# Controlled status constants
# - SUCCESS: requested analytical operation executed successfully.
# - RETRYING: recoverable runtime/validation failure undergoing bounded repair.
# - FAILED: repair attempts exhausted or unrecoverable execution failure.
# - BLOCKED: execution was prevented by an explicit safety policy/AST guardrail.
STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_RETRYING = "RETRYING"
STATUS_FAILED = "FAILED"
STATUS_BLOCKED = "BLOCKED"

CONTROLLED_STATUSES = {
    STATUS_RUNNING,
    STATUS_SUCCESS,
    STATUS_RETRYING,
    STATUS_FAILED,
    STATUS_BLOCKED,
}


class ARMGState(TypedDict, total=False):
    """Execution state tracked across the LangGraph repair graph."""
    user_query: str
    schema_context: Dict[str, Any]
    pruned_schema_markdown: str
    generated_sql: Optional[str]
    previous_sql: Optional[str]
    previous_execution_error: Optional[str]
    validation_passed: bool
    validation_error: Optional[str]
    is_safety_violation: bool
    safety_category: Optional[str]

    execution_result: Optional[ExecutionResult]
    observation: Optional[RuntimeObservation]
    diagnosis: Optional[DiagnosticResult]
    runtime_knowledge: Optional[RuntimeKnowledge]
    retrieved_memories: List[RuntimeMemory]
    applied_memory_id: Optional[str]
    repair_history: Optional[List[Dict[str, Any]]]
    repair_prompt: Optional[str]
    retry_count: int
    max_retries: int
    status: str
    telemetry: Dict[str, Any]
