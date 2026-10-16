"""
ARMG: Explicit User Constraint Validator.

Extracts and enforces explicit user constraints across diagnosis, repair, and pre-execution validation:
- Preserves explicit source/table constraints (exact required tables, prohibited tables, substitution prohibition).
- Deterministically extracts table identifiers from SQL candidates using SQLGlot AST parsing.
- Rejects constraint-violating SQL candidates before database executor invocation.
- Ensures zero database calls and zero memory admissions for constraint-violating repairs.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlglot
import sqlglot.expressions as exp

# Common English stopwords to prevent spurious identifier extraction
TABLE_STOPWORDS = {
    "another", "other", "any", "a", "an", "the", "this", "that", "with",
    "table", "tables", "relation", "relations", "source", "sources",
    "one", "different", "all", "each", "every", "some", "named", "called", "name"
}

COLUMN_STOPWORDS = {
    "another", "other", "any", "a", "an", "the", "this", "that", "these", "those",
    "with", "table", "tables", "relation", "relations", "source", "sources",
    "one", "different", "all", "each", "every", "some", "named", "called", "name",
    "column", "columns", "field", "fields", "attribute", "attributes",
    "requested", "value", "values", "of", "from", "for", "transaction", "transactions",
    "directly", "and", "or", "to", "in", "row", "rows", "record", "records",
    "their", "its", "them", "it", "total", "totals", "sum", "count", "avg", "average",
    "min", "max", "by", "using", "rather", "than", "following"
}

# Regex for explicit required table (e.g. "exact table fact_sales_performance_archive", "table named fact_sales_performance_archive")
RE_EXACT_TABLE = re.compile(
    r"\b(?:use\s+(?:the\s+|this\s+)?exact\s+table|query\s+(?:the\s+|this\s+)?exact\s+table|exact\s+table|exact\s+relation|require\s+(?:the\s+)?exact\s+table|strictly\s+use\s+(?:the\s+)?table|(?:query|use)\s+(?:the\s+)?table(?:\s+named|\s+called)?)\s+['\"`]?([a-zA-Z0-9_]+)['\"`]?",
    re.IGNORECASE,
)

# Regex for explicit required table defined as exact source (e.g. "Use fact_sales_performance_archive as the exact source table name")
RE_EXACT_TABLE_AS = re.compile(
    r"\b(?:use|query)\s+['\"`]?([a-zA-Z0-9_]+)['\"`]?\s+as\s+(?:the\s+)?(?:exact\s+)?(?:source\s+)?table(?:\s+name)?\b",
    re.IGNORECASE,
)

# Regex for explicit prohibited table (e.g. "do not substitute with fact_sales_performance")
RE_PROHIBITED_TABLE = re.compile(
    r"\b(?:do\s+not|don't|never|cannot|prohibit|prohibiting|prohibited)\s+(?:substitute\s+(?:with\s+)?|substituting\s+with\s+|use\s+(?:the\s+)?(?:table\s+|relation\s+)?|query\s+(?:the\s+)?(?:table\s+|relation\s+)?|to\s+use\s+(?:the\s+)?(?:table\s+)?|substitution\s+with\s+)['\"`]?([a-zA-Z0-9_]+)['\"`]?",
    re.IGNORECASE,
)

# Regex for general substitution prohibitions (e.g. "do not select from another table", "do not rename or alias", "or any other table")
RE_NO_SUBSTITUTION = re.compile(
    r"\b(?:or\s+any\s+other\s+table|or\s+another\s+table|do\s+not\s+substitute\s+(?:with\s+)?(?:another|any\s+other)\s+table|do\s+not\s+select\s+from\s+(?:another|any\s+other)\s+table|do\s+not\s+use\s+another\s+(?:table|source)|do\s+not\s+change\s+(?:the\s+)?(?:requested\s+)?(?:identifier|table|source)|do\s+not\s+rename\s+or\s+alias|no\s+substitution|without\s+substitution|substitution\s+(?:is\s+)?(?:strictly\s+)?prohibited|keep\s+(?:the\s+)?exact\s+(?:table|identifier))\b",
    re.IGNORECASE,
)

# Regexes for explicit required output columns
RE_OUTPUT_COLUMN_NAMED = re.compile(
    r"\b(?:retrieve|select|display|project|fetch|return)\s+(?:the\s+)?(?:value\s+of\s+(?:the\s+)?)?columns?\s+(?:named|called)\s+['\"`]?([a-zA-Z0-9_]+)['\"`]?",
    re.IGNORECASE,
)

RE_OUTPUT_REQUESTED_COLUMNS = re.compile(
    r"\b(?:display|return|retrieve|select|project|fetch|show)\s+(?:the\s+)?requested\s+columns?\s+([a-zA-Z0-9_,\s]+?)(?:\s+(?:from|for|and\s+return|directly|rather\s+than|where)|\.|$|;)",
    re.IGNORECASE,
)

RE_OUTPUT_COLS_COLUMN = re.compile(
    r"\b(?:retrieve|select|display|project|fetch|return)\s+(?:the\s+)?([a-zA-Z0-9_,\s]+?)\s+columns?\s+(?:from|for|and\s+return|directly|rather\s+than|\.|$|;)",
    re.IGNORECASE,
)

RE_OUTPUT_COLUMN_DIRECTLY = re.compile(
    r"\breturn\s+(?:the\s+)?value\s+of\s+(?:the\s+)?column\s+['\"`]?([a-zA-Z0-9_]+)['\"`]?\s+directly\b",
    re.IGNORECASE,
)


def _clean_column_tokens(raw_text: str) -> List[str]:
    """Tokenize and filter candidate column names, discarding stopwords and invalid identifiers."""
    text = re.sub(r"\band\b", ",", raw_text, flags=re.IGNORECASE)
    parts = text.split(",")
    cols: List[str] = []
    for p in parts:
        token = p.strip().strip("'\"`").strip()
        if "." in token:
            subparts = token.split(".")
            if all(sp.isidentifier() for sp in subparts):
                token = subparts[-1]
        if token.isidentifier() and token.lower() not in COLUMN_STOPWORDS:
            cols.append(token.lower())
    return cols


def _get_projection_expressions(parsed: exp.Expression) -> List[exp.Expression]:
    """Extract top-level SELECT projection expressions from AST."""
    if isinstance(parsed, exp.Select):
        return parsed.selects
    if isinstance(parsed, exp.Union):
        return _get_projection_expressions(parsed.this)
    if hasattr(parsed, "selects"):
        return getattr(parsed, "selects")
    return []


def _column_in_projection(req_col: str, projections: List[exp.Expression]) -> bool:
    """Determine whether the required column or alias is represented in the projection expressions."""
    req_col_lower = req_col.lower()
    for proj in projections:
        # 1. Direct or qualified column (e.g. unmapped_metric or f.unmapped_metric)
        if isinstance(proj, exp.Column):
            if proj.name.lower() == req_col_lower:
                return True
        # 2. Aliased expression (e.g. f.gross_revenue AS revenue, or f.unmapped_metric AS m)
        elif isinstance(proj, exp.Alias):
            if proj.alias.lower() == req_col_lower:
                return True
            cols = [c.name.lower() for c in proj.find_all(exp.Column) if c.name]
            if req_col_lower in cols:
                return True
        # 3. Expressions / aggregates (e.g. SUM(f.gross_revenue), COALESCE(unmapped_metric, 0))
        else:
            cols = [c.name.lower() for c in proj.find_all(exp.Column) if c.name]
            if req_col_lower in cols:
                return True
    return False


@dataclass(frozen=True)
class ExplicitConstraints:
    """Immutable structured user constraints extracted from the natural-language request."""
    required_tables: List[str] = field(default_factory=list)
    prohibited_tables: List[str] = field(default_factory=list)
    allow_table_substitution: bool = True
    required_columns: List[str] = field(default_factory=list)
    raw_constraints: List[str] = field(default_factory=list)

    def has_constraints(self) -> bool:
        """Return True if any explicit source/table/column constraints are active."""
        return bool(
            self.required_tables
            or self.prohibited_tables
            or not self.allow_table_substitution
            or self.required_columns
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to serializable dictionary."""
        return {
            "required_tables": list(self.required_tables),
            "prohibited_tables": list(self.prohibited_tables),
            "allow_table_substitution": self.allow_table_substitution,
            "required_columns": list(self.required_columns),
            "raw_constraints": list(self.raw_constraints),
        }


class ConstraintValidator:
    """Deterministic extractor and AST-level validator for explicit query constraints."""

    def extract_constraints(self, query: str) -> ExplicitConstraints:
        """Deterministically extract explicit table, column, and substitution constraints from user query.
        
        Args:
            query: Natural-language user prompt.
            
        Returns:
            ExplicitConstraints instance with extracted exact tables, prohibited tables, required columns, and substitution policy.
        """
        if not query or not query.strip():
            return ExplicitConstraints()

        raw_exact = [m.lower() for m in RE_EXACT_TABLE.findall(query)]
        raw_exact.extend([m.lower() for m in RE_EXACT_TABLE_AS.findall(query)])
        exact_matches = [m for m in raw_exact if m not in TABLE_STOPWORDS]

        raw_prohib = [m.lower() for m in RE_PROHIBITED_TABLE.findall(query)]
        prohib_matches = [m for m in raw_prohib if m not in TABLE_STOPWORDS]

        no_sub_match = bool(RE_NO_SUBSTITUTION.search(query))

        allow_sub = True
        if no_sub_match:
            allow_sub = False
        elif exact_matches and prohib_matches:
            allow_sub = False

        unique_exact = sorted(list(set(exact_matches)))
        unique_prohib = sorted(list(set(prohib_matches)))

        # Extract explicit output columns
        col_matches: List[str] = []
        for m in RE_OUTPUT_COLUMN_NAMED.finditer(query):
            col_matches.extend(_clean_column_tokens(m.group(1)))
        for m in RE_OUTPUT_REQUESTED_COLUMNS.finditer(query):
            col_matches.extend(_clean_column_tokens(m.group(1)))
        for m in RE_OUTPUT_COLS_COLUMN.finditer(query):
            col_matches.extend(_clean_column_tokens(m.group(1)))
        for m in RE_OUTPUT_COLUMN_DIRECTLY.finditer(query):
            col_matches.extend(_clean_column_tokens(m.group(1)))

        seen_cols: Set[str] = set()
        unique_cols: List[str] = []
        for c in col_matches:
            if c not in seen_cols:
                seen_cols.add(c)
                unique_cols.append(c)

        raw: List[str] = []
        for req in unique_exact:
            raw.append(f"Require exact table '{req}'")
        for p in unique_prohib:
            raw.append(f"Prohibit table '{p}'")
        if not allow_sub:
            raw.append("Prohibit table substitution")
        for col in unique_cols:
            raw.append(f"Require output column '{col}'")

        return ExplicitConstraints(
            required_tables=unique_exact,
            prohibited_tables=unique_prohib,
            allow_table_substitution=allow_sub,
            required_columns=unique_cols,
            raw_constraints=raw,
        )

    def validate_sql(
        self,
        sql: str,
        constraints: Optional[ExplicitConstraints],
        is_repair: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Validate generated SQL candidate against explicit constraints.
        
        Enforces:
        - Rejection of any candidate referencing explicitly prohibited tables.
        - Rejection of any candidate substituting a required table when substitution is prohibited.
        - Preservation of required exact table identifiers.
        - Rejection of any candidate omitting explicitly requested output columns from its projection.
        
        Args:
            sql: SQL statement to validate.
            constraints: ExplicitConstraints extracted from user request.
            is_repair: Whether this SQL is a repair retry candidate.
            
        Returns:
            Tuple of (is_valid: bool, error_reason: Optional[str]).
        """
        if not constraints or not constraints.has_constraints():
            return True, None

        if not sql or not sql.strip():
            return False, "Empty SQL query cannot satisfy explicit constraints."

        try:
            parsed = sqlglot.parse_one(sql.strip().rstrip(";"), read="postgres")
        except Exception as e:
            return False, f"SQL parsing error during constraint validation: {e}"

        tables_in_sql = {t.name.lower() for t in parsed.find_all(exp.Table) if t.name}

        # 1. Prohibited tables enforcement
        for p in constraints.prohibited_tables:
            if p.lower() in tables_in_sql:
                return False, f"Referenced table '{p}' is explicitly prohibited by user constraint."

        # 2. Required exact tables & substitution prohibition enforcement
        if not constraints.allow_table_substitution:
            if constraints.required_tables:
                for req in constraints.required_tables:
                    if req.lower() not in tables_in_sql:
                        return (
                            False,
                            f"Required table '{req}' was omitted or substituted, violating explicit constraint prohibiting substitution.",
                        )
            elif is_repair and tables_in_sql:
                # If substitution is prohibited in repair even without a single identified exact table
                return False, "Table substitution is explicitly prohibited by user constraint."

        # 3. Required output column projection enforcement
        if constraints.required_columns:
            projections = _get_projection_expressions(parsed)
            if not projections:
                return False, "SQL statement has no result projection expressions."

            for req_col in constraints.required_columns:
                if not _column_in_projection(req_col, projections):
                    has_star = any(bool(p.find(exp.Star)) for p in projections)
                    if has_star:
                        return (
                            False,
                            f"Required output column '{req_col}' cannot be verified from wildcard projection.",
                        )
                    return (
                        False,
                        f"Required output column '{req_col}' was omitted from the SQL result projection.",
                    )

        return True, None
