"""
ARMG Phase 3: Runtime Observation Data Model.

Defines the immutable RuntimeObservation data structure and ExecutionStatus enum
for capturing execution reality in a structured, passive manner without performing
diagnostic inference, candidate extraction, or error repair.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Broad execution status states recognized by the observation layer."""
    SUCCESS = "SUCCESS"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"


class RuntimeObservation(BaseModel):
    """Immutable record of runtime query execution outcome."""
    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    status: ExecutionStatus
    raw_error: Optional[str] = None
    normalized_error: Optional[str] = None
    execution_time_ms: float = 0.0
    row_count: int = 0
    schema_context: List[str] = Field(default_factory=list)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def is_failure(self) -> bool:
        """Return True if execution or validation failed, False otherwise."""
        return self.status != ExecutionStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Serialize observation to a clean dictionary representation."""
        status_val = self.status.value if isinstance(self.status, Enum) else str(self.status)
        return {
            "observation_id": self.observation_id,
            "query": self.query,
            "status": status_val,
            "raw_error": self.raw_error,
            "normalized_error": self.normalized_error,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "schema_context": list(self.schema_context),
            "timestamp": self.timestamp,
        }
