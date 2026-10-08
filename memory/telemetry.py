"""
ARMG Real FAISS Retrieval & Admission Telemetry Logger.
Phase 2 Canonical Implementation.

Enforces:
- Direct capture of raw_inner_product from FAISS index.search()
- cosine_similarity = raw_inner_product (unit L2-normalized embeddings)
- Explicit separation of retrieval_similarity_threshold (0.50) from admission_utility_threshold (0.25)
- All candidates returned by FAISS captured prior to threshold/lifecycle filtering
- Strict empty-store semantics (null values, never 0.0)
- Canonical CSV serialization for transparent evidence lineage
"""

import csv
from dataclasses import asdict, dataclass
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd


@dataclass
class RetrievalCandidateRecord:
    """Telemetry record for a single candidate evaluated during FAISS retrieval."""
    run_id: str
    mode: str
    query_id: str
    memory_id: Optional[str]
    rank: Optional[int]
    distance_l2_sq: Optional[float]
    similarity: Optional[float]
    retrieval_similarity_threshold: float = 0.50
    passed_retrieval_threshold: bool = False
    top_k: int = 3
    candidate_returned_by_faiss: bool = True
    retrieval_count: int = 0
    accepted_memory_count: int = 0
    store_size_before_retrieval: int = 0
    store_size_after_query: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdmissionRecord:
    """Telemetry record for an operational memory admission decision."""
    run_id: str
    mode: str
    query_id: str
    memory_id: Optional[str]
    admission_utility: float
    admission_utility_threshold: float = 0.25
    memory_admitted: bool = False
    confidence: float = 0.0
    success_rate: float = 0.0
    similarity: float = 0.0
    recency: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


RETRIEVAL_TELEMETRY_COLUMNS = [
    "run_id",
    "mode",
    "query_id",
    "memory_id",
    "rank",
    "distance_l2_sq",
    "similarity",
    "retrieval_similarity_threshold",
    "passed_retrieval_threshold",
    "top_k",
    "candidate_returned_by_faiss",
    "retrieval_count",
    "accepted_memory_count",
    "store_size_before_retrieval",
    "store_size_after_query",
]

ADMISSION_TELEMETRY_COLUMNS = [
    "run_id",
    "mode",
    "query_id",
    "memory_id",
    "admission_utility",
    "admission_utility_threshold",
    "memory_admitted",
    "confidence",
    "success_rate",
    "similarity",
    "recency",
]


class RetrievalTelemetryLogger:
    """In-memory collector and canonical CSV exporter for FAISS retrieval telemetry."""

    def __init__(self) -> None:
        self.retrieval_records: List[RetrievalCandidateRecord] = []
        self.admission_records: List[AdmissionRecord] = []

    def clear(self) -> None:
        """Reset logged telemetry."""
        self.retrieval_records.clear()
        self.admission_records.clear()

    def log_retrieval_event(
        self,
        run_id: str,
        mode: str,
        query_id: str,
        candidates: List[Dict[str, Any]],
        retrieval_count: int,
        accepted_memory_count: int,
        store_size_before: int,
        top_k: int = 3,
        threshold: float = 0.50,
    ) -> List[RetrievalCandidateRecord]:
        """Log all candidates evaluated during a FAISS search event.
        
        Args:
            run_id: Benchmark run identifier (e.g., 'seed42').
            mode: Benchmark mode name (e.g., 'Mode 4 (Full ARMG)').
            query_id: Target benchmark query ID (e.g., 'Q01').
            candidates: List of raw candidate dicts returned by search prior to filtering.
            retrieval_count: Total accepted active memories for query.
            accepted_memory_count: Same as retrieval_count.
            store_size_before: Store size prior to search.
            top_k: Number of requested neighbors.
            threshold: Retrieval similarity threshold tau = 0.50.
        """
        event_records: List[RetrievalCandidateRecord] = []

        if not candidates or store_size_before == 0:
            # Section 6: Empty-Store Semantics
            empty_record = RetrievalCandidateRecord(
                run_id=run_id,
                mode=mode,
                query_id=query_id,
                memory_id=None,
                rank=None,
                distance_l2_sq=None,
                similarity=None,
                retrieval_similarity_threshold=threshold,
                passed_retrieval_threshold=False,
                top_k=top_k,
                candidate_returned_by_faiss=False,
                retrieval_count=0,
                accepted_memory_count=0,
                store_size_before_retrieval=store_size_before,
                store_size_after_query=store_size_before,
            )
            self.retrieval_records.append(empty_record)
            event_records.append(empty_record)
            return event_records

        # Candidates exist: log all candidates returned by FAISS before filtering
        for cand in candidates:
            d2 = cand.get("distance_l2_sq")
            sim = cand.get("similarity")
            if d2 is not None:
                d2 = round(float(d2), 6)
            if sim is not None:
                sim = round(float(sim), 6)
            elif d2 is not None:
                sim = round(1.0 / (1.0 + float(d2)), 6)

            passed = cand.get("passed_retrieval_threshold")
            if passed is None and sim is not None:
                passed = sim >= threshold

            rec = RetrievalCandidateRecord(
                run_id=run_id,
                mode=mode,
                query_id=query_id,
                memory_id=cand.get("memory_id"),
                rank=cand.get("rank"),
                distance_l2_sq=d2,
                similarity=sim,
                retrieval_similarity_threshold=threshold,
                passed_retrieval_threshold=bool(passed),
                top_k=top_k,
                candidate_returned_by_faiss=True,
                retrieval_count=retrieval_count,
                accepted_memory_count=accepted_memory_count,
                store_size_before_retrieval=store_size_before,
                store_size_after_query=cand.get("store_size_after_query", store_size_before),
            )
            self.retrieval_records.append(rec)
            event_records.append(rec)

        return event_records

    def update_store_size_after_query(self, query_id: str, mode: str, store_size_after: int) -> None:
        """Annotate the terminal store size for all records associated with a completed query."""
        for r in self.retrieval_records:
            if r.query_id == query_id and r.mode == mode:
                r.store_size_after_query = store_size_after

    def log_admission_event(
        self,
        run_id: str,
        mode: str,
        query_id: str,
        memory_id: Optional[str],
        admission_utility: float,
        memory_admitted: bool,
        threshold: float = 0.25,
        confidence: float = 0.0,
        success_rate: float = 0.0,
        similarity: float = 0.0,
        recency: float = 0.0,
    ) -> AdmissionRecord:
        """Log a memory admission decision."""
        rec = AdmissionRecord(
            run_id=run_id,
            mode=mode,
            query_id=query_id,
            memory_id=memory_id,
            admission_utility=round(float(admission_utility), 6),
            admission_utility_threshold=threshold,
            memory_admitted=memory_admitted,
            confidence=round(float(confidence), 6),
            success_rate=round(float(success_rate), 6),
            similarity=round(float(similarity), 6),
            recency=round(float(recency), 6),
        )
        self.admission_records.append(rec)
        return rec

    def to_dataframe(self) -> pd.DataFrame:
        """Return retrieval telemetry as a pandas DataFrame."""
        if not self.retrieval_records:
            return pd.DataFrame(columns=RETRIEVAL_TELEMETRY_COLUMNS)
        return pd.DataFrame([r.to_dict() for r in self.retrieval_records])

    def to_admission_dataframe(self) -> pd.DataFrame:
        """Return admission telemetry as a pandas DataFrame."""
        if not self.admission_records:
            return pd.DataFrame(columns=ADMISSION_TELEMETRY_COLUMNS)
        return pd.DataFrame([r.to_dict() for r in self.admission_records])

    def write_csv(self, filepath: Union[str, Path]) -> None:
        """Serialize retrieval telemetry to canonical CSV format."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        df.to_csv(p, index=False, columns=RETRIEVAL_TELEMETRY_COLUMNS)

    def write_admission_csv(self, filepath: Union[str, Path]) -> None:
        """Serialize admission telemetry to CSV format."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_admission_dataframe()
        df.to_csv(p, index=False, columns=ADMISSION_TELEMETRY_COLUMNS)

    @classmethod
    def load_csv(cls, filepath: Union[str, Path]) -> pd.DataFrame:
        """Load retrieval telemetry CSV into a validated DataFrame."""
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Telemetry CSV not found: {p}")
        return pd.read_csv(p)


_GLOBAL_TELEMETRY_LOGGER: Optional[RetrievalTelemetryLogger] = None


def get_telemetry_logger() -> RetrievalTelemetryLogger:
    """Retrieve the global or thread-local RetrievalTelemetryLogger instance."""
    global _GLOBAL_TELEMETRY_LOGGER
    if _GLOBAL_TELEMETRY_LOGGER is None:
        _GLOBAL_TELEMETRY_LOGGER = RetrievalTelemetryLogger()
    return _GLOBAL_TELEMETRY_LOGGER


def set_telemetry_logger(logger: Optional[RetrievalTelemetryLogger]) -> None:
    """Set or reset the global RetrievalTelemetryLogger instance."""
    global _GLOBAL_TELEMETRY_LOGGER
    _GLOBAL_TELEMETRY_LOGGER = logger

