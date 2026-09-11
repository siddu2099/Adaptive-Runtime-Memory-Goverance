"""
ARMG Phase 2: SQLGlot Execution Guard.

Implements strict static AST-level pre-execution safety validation for PostgreSQL queries:
- Enforces single-statement execution (blocks stacked / multi-statement injections).
- Strictly rejects destructive DDL/DML statements (DROP, DELETE, UPDATE, INSERT, ALTER, etc.).
- Enforces read-only SELECT root expressions.
"""

from typing import Optional, Tuple
import sqlglot
import sqlglot.expressions as exp

# Forbidden AST statement expression types
MUTATION_EXPRESSION_TYPES = (
    exp.Drop,
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
)

# Forbidden SQL keywords to catch unparsed dialect-specific commands (e.g. GRANT, REVOKE)
FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "MERGE", "EXEC", "EXECUTE",
}


def validate_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """Validate that SQL string is a single, safe, read-only SELECT statement.
    
    Args:
        sql: Raw SQL query string to inspect.
        
    Returns:
        Tuple of (is_valid: bool, error_reason: Optional[str]).
    """
    if not sql or not sql.strip():
        return False, "SQL payload is empty."

    trimmed_sql = sql.strip().rstrip(";")

    # 1. Multi-statement validation via sqlglot.parse
    try:
        parsed_statements = sqlglot.parse(trimmed_sql, read="postgres")
    except Exception as e:
        return False, f"SQL syntax error during parsing: {str(e)}"

    non_empty_stmts = [s for s in parsed_statements if s is not None]
    if len(non_empty_stmts) == 0:
        return False, "SQL payload contains no executable statements."

    if len(non_empty_stmts) > 1:
        return False, f"Multiple statements rejected: found {len(non_empty_stmts)} statements."

    root_expr = non_empty_stmts[0]

    # 2. Check for DDL / DML mutation types in AST root or subtree
    for mut_type in MUTATION_EXPRESSION_TYPES:
        if isinstance(root_expr, mut_type) or root_expr.find(mut_type) is not None:
            return False, f"Destructive mutation '{mut_type.__name__}' is strictly rejected."

    # 3. Keyword check for grant/revoke and unparsed administrative statements
    sql_upper_tokens = set(trimmed_sql.upper().split())
    for kw in FORBIDDEN_KEYWORDS:
        if kw in sql_upper_tokens:
            # If keyword is present as a standalone token and not in allowed context
            if isinstance(root_expr, (exp.Select, exp.Union)):
                # Check if it's a DDL command keyword that might have leaked
                if kw in {"GRANT", "REVOKE", "TRUNCATE", "DROP", "ALTER"}:
                    return False, f"Forbidden administrative keyword '{kw}' rejected."
            else:
                return False, f"Forbidden mutation keyword '{kw}' rejected."

    # 4. AST root type verification: must be SELECT or UNION of SELECTs
    if not isinstance(root_expr, (exp.Select, exp.Union)):
        return False, f"Non-SELECT root expression rejected: '{type(root_expr).__name__}'."

    return True, None


class SafetyViolationCategory:
    """Deterministic taxonomy of explicit pre-execution safety violations."""
    DESTRUCTIVE_MUTATION = "destructive_mutation"
    MULTI_STATEMENT = "multi_statement"
    FORBIDDEN_KEYWORD = "forbidden_administrative_keyword"
    NON_SELECT_ROOT = "non_select_root"


def classify_safety_violation(sql: str) -> Tuple[bool, Optional[str]]:
    """Deterministically classify whether SQL violates static safety policy.
    
    Distinguishes explicit safety policy violations (destructive mutations,
    multi-statement injections, non-SELECT roots) from ordinary repairable
    syntax parse errors or schema errors.
    
    Returns:
        Tuple of (is_safety_violation: bool, violation_category: Optional[str]).
    """
    if not sql or not sql.strip():
        return False, None

    trimmed_sql = sql.strip().rstrip(";")
    try:
        parsed_statements = sqlglot.parse(trimmed_sql, read="postgres")
    except Exception:
        # Parsing syntax errors are ordinary syntax errors, NOT safety policy mutations
        return False, None

    non_empty_stmts = [s for s in parsed_statements if s is not None]
    if len(non_empty_stmts) > 1:
        return True, SafetyViolationCategory.MULTI_STATEMENT

    if len(non_empty_stmts) == 0:
        return False, None

    root_expr = non_empty_stmts[0]

    # Check for DDL / DML mutation types in AST root or subtree
    for mut_type in MUTATION_EXPRESSION_TYPES:
        if isinstance(root_expr, mut_type) or root_expr.find(mut_type) is not None:
            return True, SafetyViolationCategory.DESTRUCTIVE_MUTATION

    # Check forbidden administrative/mutation keywords
    sql_upper_tokens = set(trimmed_sql.upper().split())
    for kw in FORBIDDEN_KEYWORDS:
        if kw in sql_upper_tokens:
            return True, SafetyViolationCategory.FORBIDDEN_KEYWORD

    # Non-SELECT root expression
    if not isinstance(root_expr, (exp.Select, exp.Union)):
        return True, SafetyViolationCategory.NON_SELECT_ROOT

    return False, None


class ExecutionValidator:
    """Class wrapper for SQL AST validation and safety policy enforcement."""

    @staticmethod
    def validate(sql: str) -> Tuple[bool, Optional[str]]:
        """Validate query safety."""
        return validate_sql(sql)

    @staticmethod
    def classify_safety_violation(sql: str) -> Tuple[bool, Optional[str]]:
        """Deterministically classify whether a query is an explicit safety violation."""
        return classify_safety_violation(sql)

