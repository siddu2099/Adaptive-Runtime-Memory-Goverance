"""
ARMG Phase 5: RuntimeKnowledge Extractor.

Extracts ephemeral RuntimeKnowledge objects from a RuntimeObservation,
DiagnosticResult, and schema catalog metadata.

Guarantees:
- Zero-LLM, zero-database, zero-network execution.
- Deterministic, side-effect free in-memory transformation.
- Direct propagation of Phase 4 diagnosis as the single source of truth.
- Zero persistence or vector indexing (strictly Phase 5).
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Set
import uuid

from agents.error_diagnosis import DiagnosticResult
from environment.observation import RuntimeObservation
from memory.models import RuntimeKnowledge


class RuntimeKnowledgeExtractor:
    """Extracts structured, ephemeral RuntimeKnowledge artifacts."""

    @staticmethod
    def _extract_target_metrics(
        query: str,
        candidate_replacements: List[str],
        tables_referenced: List[str],
        catalog_schema: Dict[str, Any],
    ) -> List[str]:
        """Conservatively derive target metrics referenced in query or suggested by diagnosis.
        
        Extracts only valid numeric/metric columns existing in catalog_schema.
        """
        tables = catalog_schema.get("tables", {})
        valid_metric_cols: Set[str] = set()

        for tbl_name in tables_referenced:
            tbl_meta = tables.get(tbl_name, {})
            for col in tbl_meta.get("columns", []):
                col_name = col.get("name", "")
                col_type = col.get("type", "").lower()
                # Metric columns in OLAP schema are numeric or integer types
                if any(t in col_type for t in ("numeric", "integer", "int", "decimal", "real", "double")):
                    valid_metric_cols.add(col_name)

        if not valid_metric_cols:
            return []

        query_tokens = set(re.findall(r"\b[a-zA-Z0-9_]+\b", query.lower()))
        matched_metrics: Set[str] = set()

        # Check if query directly references any valid metric column
        for col in valid_metric_cols:
            if col.lower() in query_tokens:
                matched_metrics.add(col)

        # Include candidate replacements that are recognized valid metrics
        for cand in candidate_replacements:
            if cand in valid_metric_cols:
                matched_metrics.add(cand)

        return sorted(list(matched_metrics))

    def extract(
        self,
        observation: RuntimeObservation,
        diagnosis: DiagnosticResult,
        catalog_schema: Dict[str, Any],
    ) -> RuntimeKnowledge:
        """Construct an ephemeral RuntimeKnowledge artifact.
        
        Args:
            observation: The Phase 3 RuntimeObservation.
            diagnosis: The Phase 4 DiagnosticResult (source of truth for diagnosis).
            catalog_schema: Schema catalog dictionary from RuntimeEnvironment.inspect().
            
        Returns:
            Immutable RuntimeKnowledge instance with confidence initialized to 0.50.
        """
        # 1. Map source exception preserving normalized text
        source_exc = observation.normalized_error or observation.raw_error or "Unknown execution failure"

        # 2. Derive valid referenced tables deterministically
        raw_tables = observation.schema_context or []
        catalog_tables = catalog_schema.get("tables", {})
        valid_tables = [t for t in raw_tables if t in catalog_tables]
        if not valid_tables:
            valid_tables = sorted(catalog_tables.keys())
        tables_referenced = sorted(list(set(valid_tables)))

        # 3. Derive target metrics conservatively
        target_metrics = self._extract_target_metrics(
            query=observation.query,
            candidate_replacements=diagnosis.candidate_replacements,
            tables_referenced=tables_referenced,
            catalog_schema=catalog_schema,
        )

        # 4. Construct compact, deterministic context
        context = {
            "tables_referenced": tables_referenced,
            "target_metrics": target_metrics,
            "schema_context": sorted(list(observation.schema_context)),
        }

        # 5. Build RuntimeKnowledge object
        return RuntimeKnowledge(
            knowledge_id=f"kn-{uuid.uuid4().hex[:8]}",
            failure_type=diagnosis.taxonomy_category,
            source_exception=source_exc,
            context=context,
            root_cause=diagnosis.root_cause,
            repair_strategy=diagnosis.repair_rule,
            negative_constraints=list(diagnosis.negative_constraints),
            candidate_replacements=list(diagnosis.candidate_replacements),
            confidence=0.50,  # Fixed initial prior (Spec Section 12.3)
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
