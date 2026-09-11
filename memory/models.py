"""
ARMG Phase 5 & 6: Runtime Operational Memory Models.

Defines:
- RuntimeKnowledge: Ephemeral operational knowledge artifact (Phase 5).
- MemoryState: Six-stage operational lifecycle state machine (Phase 6).
- RuntimeMemory: Governed operational memory artifact with confidence, utility, and lifecycle metadata (Phase 6).
"""

from datetime import datetime, timezone
from enum import Enum
import json
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents.taxonomy import TaxonomyCategory


class RuntimeKnowledge(BaseModel):
    """Ephemeral operational knowledge object derived from execution failure diagnosis.
    
    Strictly immutable reasoning artifact (Phase 5).
    Does NOT persist to vector store, database, or disk.
    """
    model_config = ConfigDict(frozen=True)

    knowledge_id: str = Field(default_factory=lambda: f"kn-{uuid.uuid4().hex[:8]}")
    failure_type: TaxonomyCategory
    source_exception: str
    context: Dict[str, Any]
    root_cause: str
    repair_strategy: str
    negative_constraints: List[str] = Field(default_factory=list)
    candidate_replacements: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize knowledge artifact to a clean, standard Python dictionary."""
        ft_val = self.failure_type.value if hasattr(self.failure_type, "value") else str(self.failure_type)
        return {
            "knowledge_id": self.knowledge_id,
            "failure_type": ft_val,
            "source_exception": self.source_exception,
            "context": dict(self.context),
            "root_cause": self.root_cause,
            "repair_strategy": self.repair_strategy,
            "negative_constraints": list(self.negative_constraints),
            "candidate_replacements": list(self.candidate_replacements),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize knowledge artifact to a JSON formatted string."""
        return json.dumps(self.to_dict(), indent=indent)

    def format_for_embedding(self) -> str:
        """Construct deterministic text representation for future vectorization in Phase 6.
        
        Strictly excludes volatile metadata (knowledge_id, confidence, timestamp)
        to prevent metadata contamination of semantic similarity spaces.
        """
        tables = self.context.get("tables_referenced", [])
        sorted_tables = sorted(tables) if isinstance(tables, list) else []
        tables_str = ", ".join(sorted_tables) if sorted_tables else "None"
        ft_val = self.failure_type.value if hasattr(self.failure_type, "value") else str(self.failure_type)

        return (
            f"Failure: {ft_val} | "
            f"Tables: {tables_str} | "
            f"Root Cause: {self.root_cause} | "
            f"Repair: {self.repair_strategy}"
        )


class MemoryState(str, Enum):
    """The six discrete operational states in the ARMG memory lifecycle machine (Section 12.2)."""
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DECAYING = "DECAYING"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class RuntimeMemory(BaseModel):
    """Governed operational memory artifact persisted with governance metadata and vector embeddings."""
    model_config = ConfigDict(frozen=True)

    memory_id: str = Field(default_factory=lambda: f"mem-{uuid.uuid4().hex[:8]}")
    context: Dict[str, Any]
    failure_type: TaxonomyCategory
    root_cause: str
    repair_strategy: str
    negative_constraints: List[str] = Field(default_factory=list)
    candidate_replacements: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    utility: float = Field(default=0.25, ge=0.0, le=1.0)
    recency: float = Field(default=1.0, ge=0.0, le=1.0)
    embedding: Optional[List[float]] = None
    status: MemoryState = MemoryState.NEW
    successful_uses: int = Field(default=0, ge=0)
    total_uses: int = Field(default=0, ge=0)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_used_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    simulated_epoch: int = Field(default=0, ge=0)
    confidence_reference: float = Field(default=0.50, ge=0.0, le=1.0)
    reference_epoch: int = Field(default=0, ge=0)
    archive_epoch: Optional[int] = None

    @model_validator(mode="after")
    def validate_use_counts(self) -> "RuntimeMemory":
        """Verify successful_uses never exceeds total_uses."""
        if self.successful_uses > self.total_uses:
            raise ValueError(
                f"successful_uses ({self.successful_uses}) cannot exceed total_uses ({self.total_uses})"
            )
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory artifact to a clean, standard Python dictionary."""
        ft_val = self.failure_type.value if hasattr(self.failure_type, "value") else str(self.failure_type)
        st_val = self.status.value if hasattr(self.status, "value") else str(self.status)
        return {
            "memory_id": self.memory_id,
            "context": dict(self.context),
            "failure_type": ft_val,
            "root_cause": self.root_cause,
            "repair_strategy": self.repair_strategy,
            "negative_constraints": list(self.negative_constraints),
            "candidate_replacements": list(self.candidate_replacements),
            "confidence": self.confidence,
            "utility": self.utility,
            "recency": self.recency,
            "embedding": list(self.embedding) if self.embedding is not None else None,
            "status": st_val,
            "successful_uses": self.successful_uses,
            "total_uses": self.total_uses,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "simulated_epoch": self.simulated_epoch,
            "confidence_reference": self.confidence_reference,
            "reference_epoch": self.reference_epoch,
            "archive_epoch": self.archive_epoch,
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize memory artifact to a JSON formatted string."""
        return json.dumps(self.to_dict(), indent=indent)

    def copy_with(self, **updates: Any) -> "RuntimeMemory":
        """Immutable copy-on-update helper returning a new validated RuntimeMemory."""
        return self.model_copy(update=updates)
