"""
ARMG Phase 4: Seven-Tier Runtime Exception Taxonomy.

Standardizes all execution environment and pre-execution safety failures into
a rigid, 7-category taxonomy (Document Section 8.2).
"""

from enum import Enum


class TaxonomyCategory(str, Enum):
    """The seven standardized ARMG taxonomy categories."""

    SYNTAX = "Syntax"
    """Malformed SQL grammar or parser-level syntax errors."""

    SEMANTIC = "Semantic"
    """References to schema objects that do not exist (undefined columns, relations)."""

    PLANNING = "Planning"
    """Query-structure / planning engine violations such as missing GROUP BY clauses."""

    VALIDATION = "Validation"
    """Pre-execution safety or AST guardrail violations (destructive mutations, stacked queries)."""

    EXECUTION = "Execution"
    """Runtime SQL computation failures (division by zero, numeric overflow, invalid casts)."""

    PERMISSION = "Permission"
    """Authorization/access failures or read-only connection permission violations."""

    RESOURCE = "Resource"
    """Timeouts, query cancellations, connection exhaustion, or memory limitations."""
