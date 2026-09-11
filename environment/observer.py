"""
ARMG Phase 3: Runtime Observer Engine.

Implements the passive RuntimeObserver transformation layer that converts
execution and validation outcomes into structured, immutable RuntimeObservation objects.

Adheres strictly to Phase 3 boundaries:
- Purely passive observation; does not diagnose root cause or extract candidates.
- Conservative error normalization preserving PostgreSQL diagnostic detail.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from environment.base import ExecutionResult
from environment.observation import ExecutionStatus, RuntimeObservation


def normalize_error_string(error_text: Optional[str]) -> Optional[str]:
    """Conservatively normalize raw error text without losing diagnostic data.
    
    Allowed transformations:
    - Strip outer whitespace.
    - Normalize carriage returns (CRLF/CR) to standard newlines (LF).
    - Collapse runs of trailing spaces on individual lines.
    - Collapse excessive consecutive blank lines into single blank lines.
    
    Strictly forbidden:
    - No identifier rewriting or replacement.
    - No classification or root cause inference.
    - No error summarization or omission of PostgreSQL details (e.g. LINE, DETAIL, HINT).
    
    Args:
        error_text: Original raw error trace string.
        
    Returns:
        Cleaned error string, or None if input was None.
    """
    if error_text is None:
        return None

    # 1. Normalize line breaks to \n
    text = error_text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Strip trailing whitespace per line and strip outer padding
    lines = [line.rstrip() for line in text.strip().split("\n")]

    # 3. Collapse multiple consecutive empty lines to a single empty line
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        is_blank = (len(line.strip()) == 0)
        if is_blank:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    return "\n".join(cleaned_lines)


class RuntimeObserver:
    """Passive transformation layer converting execution reality into RuntimeObservation records."""

    @staticmethod
    def observe_execution(
        query: str,
        result: ExecutionResult,
        schema_context: List[str],
    ) -> RuntimeObservation:
        """Construct a RuntimeObservation from an executed query result.
        
        Args:
            query: Executed SQL query.
            result: ExecutionResult returned by target environment.
            schema_context: Active or pruned tables available to the query.
            
        Returns:
            Immutable RuntimeObservation record.
        """
        sorted_context = sorted(list(schema_context))
        current_time = datetime.now(timezone.utc).isoformat()
        obs_id = str(uuid.uuid4())

        if result.is_success:
            return RuntimeObservation(
                observation_id=obs_id,
                query=query,
                status=ExecutionStatus.SUCCESS,
                raw_error=None,
                normalized_error=None,
                execution_time_ms=result.execution_time_ms,
                row_count=result.row_count,
                schema_context=sorted_context,
                timestamp=current_time,
            )
        else:
            norm_err = normalize_error_string(result.error)
            return RuntimeObservation(
                observation_id=obs_id,
                query=query,
                status=ExecutionStatus.EXECUTION_FAILURE,
                raw_error=result.error,
                normalized_error=norm_err,
                execution_time_ms=result.execution_time_ms,
                row_count=0,
                schema_context=sorted_context,
                timestamp=current_time,
            )

    @staticmethod
    def observe_validation_failure(
        query: str,
        validation_error: str,
        schema_context: List[str],
    ) -> RuntimeObservation:
        """Construct a RuntimeObservation from a pre-execution validation rejection.
        
        No physical database execution is attempted.
        
        Args:
            query: Rejected SQL query.
            validation_error: Rejection reason emitted by AST validator.
            schema_context: Active or pruned tables available to the query.
            
        Returns:
            Immutable RuntimeObservation record with VALIDATION_FAILURE status.
        """
        sorted_context = sorted(list(schema_context))
        current_time = datetime.now(timezone.utc).isoformat()
        obs_id = str(uuid.uuid4())
        norm_err = normalize_error_string(validation_error)

        return RuntimeObservation(
            observation_id=obs_id,
            query=query,
            status=ExecutionStatus.VALIDATION_FAILURE,
            raw_error=validation_error,
            normalized_error=norm_err,
            execution_time_ms=0.0,
            row_count=0,
            schema_context=sorted_context,
            timestamp=current_time,
        )
