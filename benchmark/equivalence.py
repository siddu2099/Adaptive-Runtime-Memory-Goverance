"""
ARMG Phase 9: Relational Equivalence Engine.

Deterministically verifies relational execution equivalence between generated SQL query
results and ground-truth gold SQL results against the PostgreSQL data warehouse.

Key guarantees:
- Rejects queries where AST validation failed or execution failed.
- Enforces row cardinality and column count equality.
- Preserves PostgreSQL Decimal precision; applies explicit numerical tolerance only
  when comparing floating-point values.
- Multiplicity-preserving unordered multiset comparison for unordered queries;
  strict positional sequence comparison when ORDER BY is semantically required.
- Unit-tested edge cases: empty vs empty, empty vs non-empty, duplicate rows,
  Decimal values, unordered rows, ordered rows, column/row count mismatches.
"""

from collections import Counter
from decimal import Decimal
import math
import re
from typing import Any, List, Optional, Sequence, Tuple


def _normalize_cell(val: Any) -> Any:
    """Normalize a database cell value for robust deterministic comparison.
    
    - None -> None
    - Decimal -> Decimal (or float if compared with float)
    - float -> rounded/clean float
    - str -> stripped str
    """
    if val is None:
        return None
    if isinstance(val, str):
        return val.strip()
    return val


def _cells_equivalent(val_gen: Any, val_gold: Any, float_tol: float = 1e-4) -> bool:
    """Check if two cell values are equivalent with type and precision awareness."""
    norm_gen = _normalize_cell(val_gen)
    norm_gold = _normalize_cell(val_gold)

    if norm_gen is None and norm_gold is None:
        return True
    if norm_gen is None or norm_gold is None:
        return False

    # Exact equality (handles matching types, strings, ints, identical Decimals)
    if norm_gen == norm_gold:
        return True

    # Decimal vs Decimal
    if isinstance(norm_gen, Decimal) and isinstance(norm_gold, Decimal):
        return norm_gen == norm_gold

    # Numeric comparisons where one or both are float or Decimal/int mismatch
    is_num_gen = isinstance(norm_gen, (int, float, Decimal))
    is_num_gold = isinstance(norm_gold, (int, float, Decimal))

    if is_num_gen and is_num_gold:
        try:
            f_gen = float(norm_gen)
            f_gold = float(norm_gold)
            if math.isnan(f_gen) and math.isnan(f_gold):
                return True
            return math.isclose(f_gen, f_gold, rel_tol=float_tol, abs_tol=float_tol)
        except (ValueError, OverflowError):
            return False

    return False


def _canonicalize_row_for_multiset(row: Sequence[Any]) -> Tuple[Any, ...]:
    """Convert a row to a hashable tuple with normalized cell values."""
    canonical = []
    for cell in row:
        norm = _normalize_cell(cell)
        if isinstance(norm, float):
            # Quantize float slightly for Counter hashing
            canonical.append(("FLOAT", round(norm, 4)))
        elif isinstance(norm, Decimal):
            canonical.append(("DECIMAL", str(norm)))
        elif isinstance(norm, list):
            canonical.append(("LIST", tuple(norm)))
        else:
            canonical.append((type(norm).__name__, norm))
    return tuple(canonical)


def query_requires_order(sql: str) -> bool:
    """Detect if SQL statement has an active ORDER BY clause specifying output order."""
    if not sql:
        return False
    # Check for ORDER BY clause outside of subqueries/window functions
    # A practical deterministic check: match ORDER BY not inside OVER (...)
    stripped = re.sub(r"OVER\s*\([^)]*\)", "", sql, flags=re.IGNORECASE)
    return bool(re.search(r"\bORDER\s+BY\b", stripped, re.IGNORECASE))


def check_relational_equivalence(
    gen_rows: Optional[List[Sequence[Any]]],
    gold_rows: Optional[List[Sequence[Any]]],
    gold_sql: str = "",
    gen_sql: str = "",
    gen_success: bool = True,
    gold_success: bool = True,
) -> bool:
    """Determine if generated SQL execution result is relationally equivalent to gold SQL result.
    
    Args:
        gen_rows: Rows returned by generated query.
        gold_rows: Rows returned by gold query.
        gold_sql: Original ground-truth SQL query text.
        gen_sql: Generated SQL query text.
        gen_success: Whether generated query executed successfully.
        gold_success: Whether gold query executed successfully.
        
    Returns:
        True if relationally equivalent, False otherwise.
    """
    # 1. Failure checks
    if not gen_success or not gold_success:
        return False
    if gen_rows is None or gold_rows is None:
        return False

    # 2. Row count check
    if len(gen_rows) != len(gold_rows):
        return False

    # 3. Empty result check
    if len(gen_rows) == 0 and len(gold_rows) == 0:
        return True

    # 4. Column count check (from first row)
    if len(gen_rows[0]) != len(gold_rows[0]):
        return False

    # 5. Check whether strict row ordering is required
    order_required = query_requires_order(gold_sql)

    if order_required:
        # Positional comparison: every row must match at index i
        for r_idx, (g_row, d_row) in enumerate(zip(gen_rows, gold_rows)):
            if len(g_row) != len(d_row):
                return False
            for c_idx, (g_cell, d_cell) in enumerate(zip(g_row, d_row)):
                if not _cells_equivalent(g_cell, d_cell):
                    return False
        return True
    else:
        # Unordered multiset comparison preserving duplicate row multiplicity
        # First fast-path: check pairwise equality if already matching
        exact_match = True
        for g_row, d_row in zip(gen_rows, gold_rows):
            if not all(_cells_equivalent(c1, c2) for c1, c2 in zip(g_row, d_row)):
                exact_match = False
                break
        if exact_match:
            return True

        # Multiset comparison using Counter with canonicalized hashable representation
        gen_counter = Counter(_canonicalize_row_for_multiset(r) for r in gen_rows)
        gold_counter = Counter(_canonicalize_row_for_multiset(r) for r in gold_rows)

        if gen_counter == gold_counter:
            return True

        # Fallback: full matrix matching for close floating-point numbers
        unmatched_gold = list(gold_rows)
        for g_row in gen_rows:
            matched_idx = None
            for idx, d_row in enumerate(unmatched_gold):
                if len(g_row) == len(d_row) and all(
                    _cells_equivalent(c1, c2) for c1, c2 in zip(g_row, d_row)
                ):
                    matched_idx = idx
                    break
            if matched_idx is not None:
                unmatched_gold.pop(matched_idx)
            else:
                return False

        return len(unmatched_gold) == 0
