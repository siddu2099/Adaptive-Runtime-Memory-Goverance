"""
ARMG Operational Memory Subsystem.

Exposes:
- RuntimeKnowledge: Ephemeral operational knowledge artifact (Phase 5).
- RuntimeKnowledgeExtractor: Rule-based deterministic extractor (Phase 5).
- MemoryState: 6-stage operational lifecycle state machine (Phase 6).
- RuntimeMemory: Governed operational memory artifact (Phase 6).
- MemoryGovernanceEngine: Mathematical control and lifecycle engine (Phase 6).
- FAISSMemoryStore: 768-dimensional nearest-neighbor vector store (Phase 6).
"""

from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.knowledge_extractor import RuntimeKnowledgeExtractor
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore

__all__ = [
    "MemoryState",
    "RuntimeKnowledge",
    "RuntimeKnowledgeExtractor",
    "RuntimeMemory",
    "MemoryGovernanceEngine",
    "FAISSMemoryStore",
]
