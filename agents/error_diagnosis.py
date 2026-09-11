"""
ARMG Phase 4: Deterministic Error Diagnosis Engine.

Converts passive RuntimeObservation records and active schema catalog metadata into
deterministic, structured DiagnosticResult objects.

Zero-LLM, code-first architecture:
- 100% deterministic regex parsing and schema candidate resolution.
- Standardized 7-tier exception taxonomy classification.
- Explicit broken identifier extraction and negative constraint generation.
- Zero network, Ollama, or embedding dependencies.
"""

import difflib
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from agents.taxonomy import TaxonomyCategory
from environment.observation import ExecutionStatus, RuntimeObservation


class DiagnosticResult(BaseModel):
    """Immutable structured diagnostic record emitted by DeterministicErrorDiagnoser."""
    model_config = ConfigDict(frozen=True)

    taxonomy_category: TaxonomyCategory
    broken_identifier: Optional[str] = None
    root_cause: str
    candidate_replacements: List[str] = Field(default_factory=list)
    negative_constraints: List[str] = Field(default_factory=list)
    repair_rule: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize diagnosis to a clean dictionary representation."""
        return {
            "taxonomy_category": self.taxonomy_category.value,
            "broken_identifier": self.broken_identifier,
            "root_cause": self.root_cause,
            "candidate_replacements": list(self.candidate_replacements),
            "negative_constraints": list(self.negative_constraints),
            "repair_rule": self.repair_rule,
        }


# Pre-compiled deterministic regular expression patterns
RE_UNDEFINED_COLUMN = re.compile(
    r'column\s+(?:"?[a-zA-Z0-9_]+"?[.])?"?([a-zA-Z0-9_]+)"?\s+does not exist',
    re.IGNORECASE,
)
RE_UNDEFINED_RELATION = re.compile(
    r'(?:relation|table)\s+"?([a-zA-Z0-9_]+)"?\s+does not exist',
    re.IGNORECASE,
)
RE_GROUPING_ERROR = re.compile(
    r'column\s+"?([a-zA-Z0-9_.]+)"?\s+must appear in the GROUP BY clause',
    re.IGNORECASE,
)
RE_DIVISION_BY_ZERO = re.compile(
    r'division by zero',
    re.IGNORECASE,
)
RE_SYNTAX_ERROR = re.compile(
    r'syntax error at or near\s+"?([a-zA-Z0-9_]+)"?',
    re.IGNORECASE,
)
RE_PERMISSION_ERROR = re.compile(
    r'permission denied|insufficient_privilege|read-only|cannot execute',
    re.IGNORECASE,
)
RE_RESOURCE_ERROR = re.compile(
    r'timeout|timed out|canceling statement|connection exhausted|too many connections',
    re.IGNORECASE,
)


def _resolve_column_candidates(
    broken_col: str,
    schema_context: List[str],
    catalog_schema: Dict[str, Any],
) -> List[str]:
    """Deterministically resolve and rank candidate replacement columns from catalog schema.
    
    Ranking criteria (strictly deterministic):
    1. Lexical / token similarity (substring match, token overlap, difflib ratio).
    2. Data type compatibility: if broken column suggests metrics/amounts, prioritize numeric types.
    3. Alphabetical tie-breaker.
    
    Returns:
        List of valid column names present in the catalog schema.
    """
    tables = catalog_schema.get("tables", {})
    if not tables:
        return []

    # Scope search to schema_context tables if valid, otherwise all tables in catalog
    target_tables = [t for t in schema_context if t in tables]
    if not target_tables:
        target_tables = sorted(tables.keys())

    # Collect valid unique columns and their metadata
    available_cols: Dict[str, Dict[str, Any]] = {}
    for tbl_name in sorted(target_tables):
        cols = tables[tbl_name].get("columns", [])
        for col in cols:
            name = col.get("name")
            if name and name.lower() != broken_col.lower() and name not in available_cols:
                available_cols[name] = col

    broken_lower = broken_col.lower()
    broken_tokens = set(re.findall(r"[a-z0-9]+", broken_lower))

    # Metric/financial intent heuristic
    metric_keywords = {"revenue", "profit", "cost", "amount", "price", "units", "sales", "discount"}
    is_metric_intent = bool(broken_tokens & metric_keywords)

    def score_candidate(cand_name: str) -> Tuple[float, str]:
        c_lower = cand_name.lower()
        c_meta = available_cols[cand_name]
        c_type = c_meta.get("type", "").lower()
        score = 0.0

        # Substring match bonus
        if broken_lower in c_lower:
            score += 10.0
        elif c_lower in broken_lower:
            score += 5.0

        # Token overlap bonus
        c_tokens = set(re.findall(r"[a-z0-9]+", c_lower))
        shared_tokens = broken_tokens & c_tokens
        score += len(shared_tokens) * 8.0

        # String similarity ratio (0.0 to 1.0)
        sim = difflib.SequenceMatcher(None, broken_lower, c_lower).ratio()
        score += sim * 4.0

        # Metric type compatibility bonus
        is_numeric_type = any(t in c_type for t in ("numeric", "integer", "int", "double", "float", "decimal", "real"))
        if is_metric_intent and is_numeric_type:
            score += 6.0
            # Special domain affinity: if query broke on 'revenue', gross_revenue & net_profit are key metrics
            if "revenue" in broken_lower and "revenue" in c_lower:
                score += 15.0
            elif "revenue" in broken_lower and "profit" in c_lower:
                score += 10.0

        # Negative score for sorting descending, candidate name for ascending tie-breaker
        return (-score, cand_name)

    scored_candidates = sorted(available_cols.keys(), key=score_candidate)
    return scored_candidates


def _resolve_table_candidates(
    broken_tbl: str,
    catalog_schema: Dict[str, Any],
) -> List[str]:
    """Deterministically resolve candidate replacement tables from catalog schema."""
    tables = catalog_schema.get("tables", {})
    if not tables:
        return []

    available_tables = [t for t in sorted(tables.keys()) if t.lower() != broken_tbl.lower()]
    broken_lower = broken_tbl.lower()
    broken_tokens = set(re.findall(r"[a-z0-9]+", broken_lower))

    def score_table(cand_name: str) -> Tuple[float, str]:
        c_lower = cand_name.lower()
        score = 0.0

        if broken_lower in c_lower:
            score += 10.0
        elif c_lower in broken_lower:
            score += 5.0

        c_tokens = set(re.findall(r"[a-z0-9]+", c_lower))
        shared = broken_tokens & c_tokens
        score += len(shared) * 8.0

        sim = difflib.SequenceMatcher(None, broken_lower, c_lower).ratio()
        score += sim * 4.0

        return (-score, cand_name)

    return sorted(available_tables, key=score_table)


class DeterministicErrorDiagnoser:
    """Pure code-first deterministic runtime error diagnosis module."""

    def diagnose(
        self,
        observation: RuntimeObservation,
        catalog_schema: Dict[str, Any],
    ) -> DiagnosticResult:
        """Diagnose a runtime observation against the active database schema catalog.
        
        Args:
            observation: The RuntimeObservation produced by Phase 3.
            catalog_schema: The schema catalog dictionary from RuntimeEnvironment.inspect().
            
        Returns:
            DiagnosticResult containing taxonomy, root cause, candidates, negative constraints, and repair rule.
        """
        raw_error = observation.normalized_error or observation.raw_error or ""

        # ======================================================================
        # PRECEDENCE TIER 1: VALIDATION
        # ======================================================================
        if (
            observation.status == ExecutionStatus.VALIDATION_FAILURE
            or "rejected:" in raw_error.lower()
            or "mutation" in raw_error.lower()
        ):
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.VALIDATION,
                broken_identifier=None,
                root_cause="Pre-execution safety or AST guardrail validation rejected the query.",
                candidate_replacements=[],
                negative_constraints=[],
                repair_rule="Rewrite the request as a single read-only SELECT statement.",
            )

        # ======================================================================
        # PRECEDENCE TIER 2: SYNTAX
        # ======================================================================
        syntax_match = RE_SYNTAX_ERROR.search(raw_error)
        if syntax_match or ("syntax error" in raw_error.lower() and "syntax error at or near" in raw_error.lower()):
            broken_id = syntax_match.group(1) if syntax_match else None
            neg_constraints = [broken_id] if broken_id else []
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.SYNTAX,
                broken_identifier=broken_id,
                root_cause="SQL parser rejected the query syntax near the reported parser token.",
                candidate_replacements=[],
                negative_constraints=neg_constraints,
                repair_rule="Correct the SQL syntax near the reported parser location.",
            )

        # ======================================================================
        # PRECEDENCE TIER 3: SEMANTIC (Undefined Column & Undefined Relation)
        # ======================================================================
        col_match = RE_UNDEFINED_COLUMN.search(raw_error)
        if col_match:
            broken_id = col_match.group(1)
            candidates = _resolve_column_candidates(
                broken_id,
                observation.schema_context,
                catalog_schema,
            )
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.SEMANTIC,
                broken_identifier=broken_id,
                root_cause=f"Referenced column '{broken_id}' does not exist in the active schema.",
                candidate_replacements=candidates,
                negative_constraints=[broken_id],
                repair_rule="Replace the invalid column identifier with a schema-valid candidate.",
            )

        rel_match = RE_UNDEFINED_RELATION.search(raw_error)
        if rel_match:
            broken_id = rel_match.group(1)
            candidates = _resolve_table_candidates(broken_id, catalog_schema)
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.SEMANTIC,
                broken_identifier=broken_id,
                root_cause=f"Referenced relation '{broken_id}' does not exist in the active schema.",
                candidate_replacements=candidates,
                negative_constraints=[broken_id],
                repair_rule="Replace the invalid relation identifier with a schema-valid table.",
            )

        # ======================================================================
        # PRECEDENCE TIER 4: PLANNING (Grouping Requirements)
        # ======================================================================
        grouping_match = RE_GROUPING_ERROR.search(raw_error)
        if grouping_match:
            broken_id = grouping_match.group(1)
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.PLANNING,
                broken_identifier=broken_id,
                root_cause=f"Selected non-aggregated column '{broken_id}' is missing from GROUP BY.",
                candidate_replacements=[],
                negative_constraints=[],
                repair_rule="Ensure every selected non-aggregated expression is included in GROUP BY.",
            )

        # ======================================================================
        # PRECEDENCE TIER 5: PERMISSION
        # ======================================================================
        perm_match = RE_PERMISSION_ERROR.search(raw_error)
        if perm_match:
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.PERMISSION,
                broken_identifier=None,
                root_cause="Database operation rejected due to insufficient privileges or read-only restriction.",
                candidate_replacements=[],
                negative_constraints=[],
                repair_rule="Use only operations permitted by the configured database authorization.",
            )

        # ======================================================================
        # PRECEDENCE TIER 6: RESOURCE
        # ======================================================================
        resource_match = RE_RESOURCE_ERROR.search(raw_error)
        if resource_match:
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.RESOURCE,
                broken_identifier=None,
                root_cause="Query execution halted due to timeout, cancellation, or resource exhaustion.",
                candidate_replacements=[],
                negative_constraints=[],
                repair_rule="Reduce or restructure the query to avoid the reported runtime resource limitation.",
            )

        # ======================================================================
        # PRECEDENCE TIER 7: EXECUTION (Division by zero or unclassified fallback)
        # ======================================================================
        div_zero_match = RE_DIVISION_BY_ZERO.search(raw_error)
        if div_zero_match:
            return DiagnosticResult(
                taxonomy_category=TaxonomyCategory.EXECUTION,
                broken_identifier=None,
                root_cause="Runtime division by zero occurred.",
                candidate_replacements=[],
                negative_constraints=[],
                repair_rule="Protect the denominator using NULLIF or an equivalent non-zero safeguard.",
            )

        # Fallback for unclassified execution errors
        return DiagnosticResult(
            taxonomy_category=TaxonomyCategory.EXECUTION,
            broken_identifier=None,
            root_cause="Runtime execution error was not matched by a specialized deterministic rule.",
            candidate_replacements=[],
            negative_constraints=[],
            repair_rule="Review the execution error and ensure queries strictly adhere to runtime environment requirements.",
        )
