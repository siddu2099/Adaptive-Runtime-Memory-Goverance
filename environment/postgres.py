"""
ARMG Phase 1: PostgreSQL Runtime Environment Adapter.

Implements the PostgreSQLEnvironment adapter adhering strictly to the
RuntimeEnvironment Protocol. Provides zero-token direct catalog introspection,
pre-execution syntax validation, deterministic execution with timing, and
driver error trace normalization.
"""

import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import psycopg2
import psycopg2.errors
import sqlglot
from dotenv import load_dotenv

from environment.base import ExecutionResult, RuntimeEnvironment

# Load environment configuration
load_dotenv()


class PostgreSQLEnvironment:
    """PostgreSQL implementation of the RuntimeEnvironment protocol."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.dbname = dbname or os.getenv("POSTGRES_DB", "armg_db")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")
        self._connection: Optional[psycopg2.extensions.connection] = None

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Retrieve or create an active database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                connect_timeout=10,
            )
            self._connection.autocommit = False
        return self._connection

    def close(self) -> None:
        """Cleanly close the active database connection if open."""
        if self._connection is not None and not self._connection.closed:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None

    def __enter__(self):
        self._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def inspect(self) -> Dict[str, Any]:
        """Direct catalog inspection querying information_schema catalogs.
        
        Extracts tables, columns, data types, nullability, and primary key metadata
        without consuming any LLM inference tokens.
        """
        conn = self._get_connection()
        catalog: Dict[str, Any] = {"tables": {}}

        query_columns = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """

        query_pks = """
        SELECT
            kcu.table_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = 'public';
        """

        with conn.cursor() as cur:
            cur.execute(query_pks)
            pk_set = {(row[0], row[1]) for row in cur.fetchall()}

            cur.execute(query_columns)
            col_rows = cur.fetchall()

            for table_name, col_name, data_type, is_nullable, ord_pos in col_rows:
                if table_name not in catalog["tables"]:
                    catalog["tables"][table_name] = {
                        "table_name": table_name,
                        "columns": [],
                    }

                catalog["tables"][table_name]["columns"].append({
                    "name": col_name,
                    "type": data_type,
                    "nullable": is_nullable == "YES",
                    "primary_key": (table_name, col_name) in pk_set,
                    "ordinal_position": ord_pos,
                })

        return catalog

    def validate(self, payload: str) -> Tuple[bool, Optional[str]]:
        """Perform static pre-execution validation using SQLGlot AST parsing."""
        if not payload or not payload.strip():
            return False, "Query payload is empty"

        try:
            ast = sqlglot.parse_one(payload, read="postgres")
            if ast is None:
                return False, "Failed to parse SQL payload"
            return True, None
        except Exception as e:
            return False, f"SQL validation error: {str(e)}"

    def execute(self, payload: str) -> ExecutionResult:
        """Execute a query payload in PostgreSQL, capturing timing, rows, and errors."""
        conn = self._get_connection()
        start_time = time.perf_counter()
        
        try:
            with conn.cursor() as cur:
                cur.execute(payload)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                if cur.description:
                    rows = cur.fetchall()
                    row_count = len(rows)
                else:
                    rows = []
                    row_count = cur.rowcount if cur.rowcount != -1 else 0

                conn.commit()
                return ExecutionResult(
                    status="SUCCESS",
                    query=payload,
                    rows=rows,
                    error=None,
                    execution_time_ms=round(elapsed_ms, 3),
                    row_count=row_count,
                )
        except Exception as e:
            conn.rollback()
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_str = str(e).strip()
            return ExecutionResult(
                status="FAILURE",
                query=payload,
                rows=[],
                error=error_str,
                execution_time_ms=round(elapsed_ms, 3),
                row_count=0,
            )

    def observe(self, trace: str) -> Dict[str, Any]:
        """Normalize a raw database error trace into structured diagnostic components."""
        if not trace:
            return {
                "raw_trace": "",
                "error_class": "Unknown",
                "error_message": "",
                "line_reference": None,
            }

        lines = [line.strip() for line in trace.splitlines() if line.strip()]
        first_line = lines[0] if lines else ""

        # Determine error class name
        error_class = "DatabaseError"
        if "UndefinedColumn" in trace or "column" in trace and "does not exist" in trace:
            error_class = "UndefinedColumn"
        elif "UndefinedTable" in trace or "relation" in trace and "does not exist" in trace:
            error_class = "UndefinedTable"
        elif "GroupingError" in trace or "must appear in the GROUP BY clause" in trace:
            error_class = "GroupingError"
        elif "division by zero" in trace.lower() or "DivisionByZero" in trace:
            error_class = "DivisionByZero"
        elif "syntax error" in trace.lower() or "SyntaxError" in trace:
            error_class = "SyntaxError"

        # Extract line reference if present (e.g. LINE 1: ...)
        line_ref = None
        for line in lines:
            match = re.search(r"LINE\s+(\d+):", line, re.IGNORECASE)
            if match:
                line_ref = int(match.group(1))
                break

        return {
            "raw_trace": trace,
            "error_class": error_class,
            "error_message": first_line,
            "line_reference": line_ref,
        }
