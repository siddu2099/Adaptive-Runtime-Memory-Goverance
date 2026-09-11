"""
ARMG Phase 2: Code-First Schema Introspector.

Extracts live PostgreSQL database schema metadata from the RuntimeEnvironment
and converts it into a clean, deterministic Markdown representation for prompt construction
without consuming LLM inference tokens.
"""

from typing import Any, Dict, List, Optional
from environment.base import RuntimeEnvironment
from environment.postgres import PostgreSQLEnvironment


def format_catalog_to_markdown(
    catalog: Dict[str, Any], filter_tables: Optional[List[str]] = None
) -> str:
    """Convert raw catalog dictionary into a deterministic Markdown schema representation.
    
    Args:
        catalog: Dictionary emitted by RuntimeEnvironment.inspect().
        filter_tables: Optional list of table names to restrict the output to.
        
    Returns:
        Deterministic Markdown string listing tables, columns, and data types.
    """
    tables = catalog.get("tables", {})
    if not tables:
        return "No tables available in catalog."

    selected_tables = sorted(tables.keys())
    if filter_tables is not None:
        filter_set = {t.lower() for t in filter_tables}
        selected_tables = [t for t in selected_tables if t.lower() in filter_set]

    sections: List[str] = []
    for table_name in selected_tables:
        table_meta = tables[table_name]
        columns = table_meta.get("columns", [])
        # Ensure deterministic column ordering by ordinal_position
        sorted_cols = sorted(columns, key=lambda c: c.get("ordinal_position", 0))

        col_lines = []
        for col in sorted_cols:
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            is_pk = col.get("primary_key", False)
            pk_suffix = " (PK)" if is_pk else ""
            col_lines.append(f"- {col_name}: {col_type}{pk_suffix}")

        sections.append(f"## {table_name}\n" + "\n".join(col_lines))

    return "\n\n".join(sections)


class SchemaIntrospector:
    """Extracts and formats catalog metadata without LLM inference."""

    def __init__(self, env: Optional[RuntimeEnvironment] = None):
        self.env = env or PostgreSQLEnvironment()

    def get_raw_catalog(self) -> Dict[str, Any]:
        """Fetch raw catalog dictionary from target environment."""
        return self.env.inspect()

    def get_schema_markdown(self, filter_tables: Optional[List[str]] = None) -> str:
        """Fetch catalog and return deterministic Markdown representation."""
        catalog = self.get_raw_catalog()
        return format_catalog_to_markdown(catalog, filter_tables=filter_tables)
