"""
ARMG Phase 1: Environment Base Abstractions.

Defines the core ExecutionResult data structure and the RuntimeEnvironment
Protocol for decoupling agent reasoning from physical environment execution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable


@dataclass
class ExecutionResult:
    """Standardized record of query execution outcome within the target environment."""
    status: str  # "SUCCESS" or "FAILURE"
    query: str
    rows: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    row_count: int = 0

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"


@runtime_checkable
class RuntimeEnvironment(Protocol):
    """Standardized interface for target execution environments (Spec Section 9.1)."""

    def inspect(self) -> Dict[str, Any]:
        """Direct catalog inspection without LLM inference.
        
        Returns:
            Dictionary containing database schema metadata (tables, columns, types, keys).
        """
        ...

    def validate(self, payload: str) -> Tuple[bool, Optional[str]]:
        """Perform static pre-execution syntax and guardrail validation.
        
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str]).
        """
        ...

    def execute(self, payload: str) -> ExecutionResult:
        """Execute payload in target environment, capturing execution timing and outcome.
        
        Returns:
            ExecutionResult containing execution status, returned rows, and/or error trace.
        """
        ...

    def observe(self, trace: str) -> Dict[str, Any]:
        """Normalize raw driver error trace for diagnostic analysis.
        
        Returns:
            Dictionary containing normalized exception attributes.
        """
        ...
