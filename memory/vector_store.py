"""
ARMG Phase 6: Vector Storage Engine for RuntimeMemory.

Implements FAISS CPU nearest-neighbor vector indexing:
- Fixed 768-dimensional space (derived from nomic-embed-text).
- faiss.IndexIDMap2 wrapping IndexFlatL2(768).
- Strict vector validation (shape, float32, NaN, Inf rejection).
- Decoupled metadata mapping: FAISS stores only int64 IDs and vectors;
  Python metadata maps int64 IDs to immutable RuntimeMemory objects.
- Explicit L2 distance and normalized context similarity calculation:
  context_similarity = 1.0 / (1.0 + l2_distance).
- Synchronized physical deletion removing vectors from both FAISS and metadata.

Zero-LLM, zero-database, pure vector mathematics and metadata management.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import faiss

from memory.models import MemoryState, RuntimeMemory


class FAISSMemoryStore:
    """CPU FAISS Vector Store with ID mapping and decoupled metadata storage."""

    DIMENSION: int = 768

    def __init__(self) -> None:
        """Initialize fixed 768-dimensional FAISS index with IDMap2."""
        self.dimension: int = self.DIMENSION
        # IndexFlatL2 provides exact Euclidean nearest-neighbor search.
        # IndexIDMap2 allows arbitrary int64 ID assignment and physical removal.
        self._flat_index = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIDMap2(self._flat_index)

        # Decoupled metadata mappings
        self._id_to_memory: Dict[int, RuntimeMemory] = {}
        self._memory_id_to_int_id: Dict[str, int] = {}
        self._next_id: int = 1

    def _validate_vector(self, vector: Union[np.ndarray, List[float]]) -> np.ndarray:
        """Validate vector dimensionality, dtype, and numerical sanity.
        
        Architectural Invariant:
        Vectors generated via the runtime boundary (default_embed_fn) are strictly
        unit L2-normalized (||v||₂ ≈ 1.0), ensuring IndexFlatL2 squared Euclidean
        distance maps directly to cosine distance (d = 2(1 - cos θ)) and normalized
        context similarity (sim = 1 / (1 + d)).
        
        Rejects:
        - Wrong dimensions (anything other than (768,) or (1, 768))
        - NaN values
        - Infinite values
        
        Returns:
            2D float32 numpy array with shape (1, 768).
        """
        if isinstance(vector, list):
            v = np.array(vector, dtype=np.float32)
        elif isinstance(vector, np.ndarray):
            if vector.dtype != np.float32:
                v = vector.astype(np.float32)
            else:
                v = vector
        else:
            raise TypeError(f"Expected numpy.ndarray or list of floats, got {type(vector)}")

        # Strict shape validation: do NOT silently reshape arbitrary shapes like (2, 384)
        if v.shape == (self.dimension,):
            v_2d = v.reshape(1, self.dimension)
        elif v.shape == (1, self.dimension):
            v_2d = v
        else:
            raise ValueError(
                f"Invalid vector dimension: expected shape ({self.dimension},) or (1, {self.dimension}), got {v.shape}"
            )

        # Check for NaN and Inf
        if np.isnan(v_2d).any():
            raise ValueError("Vector contains NaN values; rejected by vector validation.")
        if np.isinf(v_2d).any():
            raise ValueError("Vector contains infinite values; rejected by vector validation.")

        return v_2d

    def add(self, memory: RuntimeMemory, vector: Union[np.ndarray, List[float]]) -> int:
        """Insert a RuntimeMemory and its 768-dimensional vector into the store.
        
        Args:
            memory: Validated RuntimeMemory object.
            vector: 768-dimensional embedding vector.
            
        Returns:
            Assigned internal integer ID in FAISS index.
        """
        v_2d = self._validate_vector(vector)

        # If memory already exists, remove previous vector to ensure 1:1 mapping
        if memory.memory_id in self._memory_id_to_int_id:
            self.delete(memory.memory_id)

        int_id = self._next_id
        self._next_id += 1

        # Add to FAISS with explicit int64 ID
        ids = np.array([int_id], dtype=np.int64)
        self.index.add_with_ids(v_2d, ids)

        # Store in metadata mappings
        self._id_to_memory[int_id] = memory
        self._memory_id_to_int_id[memory.memory_id] = int_id

        return int_id

    def search(
        self,
        query_vector: Union[np.ndarray, List[float]],
        top_k: int = 5,
    ) -> List[Tuple[RuntimeMemory, float, float]]:
        """Perform nearest-neighbor search for the query vector.
        
        Args:
            query_vector: 768-dimensional query vector.
            top_k: Number of nearest neighbors to retrieve.
            
        Returns:
            List of tuples: (RuntimeMemory, distance_l2_sq, similarity).
            Semantic similarity is explicitly transformed from squared L2 distance:
                similarity = 1.0 / (1.0 + distance_l2_sq) in [0.0, 1.0].
            Ties are broken deterministically by (distance_l2_sq, memory_id).
        """
        # Strictly validate query vector before any early return
        v_2d = self._validate_vector(query_vector)

        if top_k <= 0 or self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)

        distances, indices = self.index.search(v_2d, k)

        results: List[Tuple[RuntimeMemory, float, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            int_id = int(idx)
            if int_id in self._id_to_memory:
                mem = self._id_to_memory[int_id]
                # Filter out deleted memories if any linger
                if mem.status == MemoryState.DELETED:
                    continue
                d2 = float(dist)
                # Deterministic normalized similarity
                sim = 1.0 / (1.0 + d2)
                sim = max(0.0, min(1.0, round(sim, 6)))
                results.append((mem, d2, sim))

        # Deterministic sorting: ascending distance, then deterministic memory_id tie-break
        results.sort(key=lambda r: (r[1], r[0].memory_id))
        return results

    def search_raw_candidates(
        self,
        query_vector: Union[np.ndarray, List[float]],
        top_k: int = 5,
    ) -> List[Tuple[RuntimeMemory, int, float, float]]:
        """Perform search returning all raw candidates with rank before threshold or lifecycle filtering.
        
        Returns:
            List of tuples: (RuntimeMemory, rank, distance_l2_sq, similarity)
            where rank is 1-based, sorted ascending by distance_l2_sq (highest similarity first).
        """
        v_2d = self._validate_vector(query_vector)
        if top_k <= 0 or self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(v_2d, k)

        raw_candidates = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            int_id = int(idx)
            if int_id in self._id_to_memory:
                mem = self._id_to_memory[int_id]
                d2 = float(dist)
                sim = 1.0 / (1.0 + d2)
                sim = max(0.0, min(1.0, round(sim, 6)))
                raw_candidates.append((mem, d2, sim))

        # Sorting: lowest distance first (highest similarity first)
        raw_candidates.sort(key=lambda r: (r[1], r[0].memory_id))
        return [(r[0], rank_idx, r[1], r[2]) for rank_idx, r in enumerate(raw_candidates, 1)]

    def delete(self, memory_id: str) -> bool:
        """Physically delete a memory from both the FAISS index and metadata store.
        
        Args:
            memory_id: Unique string identifier of the memory.
            
        Returns:
            True if memory was found and deleted, False otherwise.
        """
        int_id = self._memory_id_to_int_id.get(memory_id)
        if int_id is None:
            return False

        # Remove from FAISS index physically
        ids = np.array([int_id], dtype=np.int64)
        self.index.remove_ids(ids)

        # Remove from metadata mappings
        self._id_to_memory.pop(int_id, None)
        self._memory_id_to_int_id.pop(memory_id, None)

        return True

    def get(self, memory_id: str) -> Optional[RuntimeMemory]:
        """Retrieve RuntimeMemory by its memory_id from metadata."""
        int_id = self._memory_id_to_int_id.get(memory_id)
        if int_id is None:
            return None
        return self._id_to_memory.get(int_id)

    def update_memory(self, memory: RuntimeMemory) -> bool:
        """Update in-memory metadata for an existing memory without re-embedding.
        
        Args:
            memory: RuntimeMemory object with updated metadata.
            
        Returns:
            True if memory was found and updated, False otherwise.
        """
        int_id = self._memory_id_to_int_id.get(memory.memory_id)
        if int_id is None:
            return False
        self._id_to_memory[int_id] = memory
        return True

    def count(self) -> int:
        """Return total active vector count in the FAISS index."""
        return self.index.ntotal

    def all_memories(self) -> List[RuntimeMemory]:
        """Return list of all registered RuntimeMemory objects in the store."""
        return list(self._id_to_memory.values())
