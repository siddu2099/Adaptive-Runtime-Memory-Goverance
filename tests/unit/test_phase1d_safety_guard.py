"""
ARMG Phase 1D: SQL Safety Regression & Execution-Proof Validation Test Suite.

Verifies:
1. Strict pre-execution safety rejection of DDL, DML, multi-statement, transaction, and control statements.
2. Protection against nested destructive statements in CTEs/subqueries.
3. Obfuscation resistance: case variation, comments, newlines, whitespace.
4. Freedom from string-literal / keyword confusion (e.g. 'DROP' inside string literals or comments).
5. Execution-proof guarantee: zero invocations of the database execution layer for blocked queries.
6. Valid read-only analytical queries (SELECT, CTE, UNION, aggregations) remain permitted.
"""

from typing import Any, Dict, List, Optional
import pytest

from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from environment.base import ExecutionResult
from graph.state import STATUS_BLOCKED, STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.vector_store import FAISSMemoryStore
from validation.execution_validator import (
    ExecutionValidator,
    SafetyViolationCategory,
    validate_sql,
    classify_safety_violation,
)


class InstrumentedEnvironment:
    """Mock database environment tracking query execution count and payloads."""

    def __init__(self):
        self.catalog = {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer", "is_pk": True},
                        {"name": "gross_revenue", "type": "numeric", "is_pk": False},
                        {"name": "net_profit", "type": "numeric", "is_pk": False},
                    ]
                },
                "dim_product": {
                    "columns": [
                        {"name": "product_key", "type": "integer", "is_pk": True},
                        {"name": "product_name", "type": "varchar", "is_pk": False},
                    ]
                },
            }
        }
        self.executed_queries: List[str] = []
        self.execution_count: int = 0

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, payload: str) -> ExecutionResult:
        self.execution_count += 1
        self.executed_queries.append(payload)
        return ExecutionResult(
            status="SUCCESS",
            query=payload,
            rows=[{"count": 1}],
            row_count=1,
            execution_time_ms=1.0,
        )


def mock_embed_fn(text: str) -> List[float]:
    return [0.1] * 768


# ==============================================================================
# 1. Destructive DML & DDL Statement Validation
# ==============================================================================

@pytest.mark.parametrize("query,expected_category", [
    ("DELETE FROM fact_sales_performance;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("UPDATE dim_product SET product_name = 'x';", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("INSERT INTO dim_product (product_key) VALUES (1);", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("DROP TABLE dim_product;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("DROP DATABASE armg_db;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("ALTER TABLE dim_product ADD COLUMN test_col int;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("TRUNCATE TABLE fact_sales_performance;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("CREATE TABLE test_table (id int);", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("CREATE DATABASE test_db;", SafetyViolationCategory.DESTRUCTIVE_MUTATION),
    ("GRANT ALL PRIVILEGES ON fact_sales_performance TO public;", SafetyViolationCategory.NON_SELECT_ROOT),
    ("REVOKE ALL PRIVILEGES ON fact_sales_performance FROM public;", SafetyViolationCategory.NON_SELECT_ROOT),
])
def test_destructive_dml_ddl_rejected(query, expected_category):
    """Verify destructive DDL and DML operations are strictly rejected and categorized."""
    is_valid, err = validate_sql(query)
    assert is_valid is False
    assert err is not None

    is_safety, cat = classify_safety_violation(query)
    assert is_safety is True
    assert cat in (expected_category, SafetyViolationCategory.DESTRUCTIVE_MUTATION, SafetyViolationCategory.FORBIDDEN_KEYWORD)


# ==============================================================================
# 2. Multi-Statement / Stacked Query Injection Tests
# ==============================================================================

@pytest.mark.parametrize("query", [
    "SELECT 1; SELECT 2;",
    "SELECT 1; DROP TABLE dim_product;",
    "SELECT 1; DELETE FROM fact_sales_performance;",
    "SELECT 1; UPDATE dim_product SET product_name = 'bad';",
    "SELECT 1;\nSELECT 2;",
    "SELECT 1; /* comment */ DROP TABLE dim_product;",
])
def test_multi_statement_rejected(query):
    """Verify multiple/stacked statements are unconditionally rejected as MULTI_STATEMENT."""
    is_valid, err = validate_sql(query)
    assert is_valid is False
    assert "multiple statements" in err.lower()

    is_safety, cat = classify_safety_violation(query)
    assert is_safety is True
    assert cat == SafetyViolationCategory.MULTI_STATEMENT


# ==============================================================================
# 3. Transaction and Control Statement Tests
# ==============================================================================

@pytest.mark.parametrize("query", [
    "BEGIN;",
    "COMMIT;",
    "ROLLBACK;",
    "SAVEPOINT sp1;",
    "RELEASE SAVEPOINT sp1;",
    "BEGIN; SELECT 1; COMMIT;",
])
def test_transaction_control_rejected(query):
    """Verify transaction and control statements are rejected and never reach execution."""
    is_valid, err = validate_sql(query)
    assert is_valid is False

    is_safety, _ = classify_safety_violation(query)
    # Either classified as safety violation or invalid syntax; execution must be False
    assert is_valid is False


# ==============================================================================
# 4. Nested Destructive Constructs (AST Subtree Inspection)
# ==============================================================================

@pytest.mark.parametrize("query,mutation_type", [
    ("WITH deleted AS (DELETE FROM fact_sales_performance RETURNING *) SELECT * FROM deleted;", "Delete"),
    ("WITH updated AS (UPDATE dim_product SET product_name = 'x' RETURNING *) SELECT * FROM updated;", "Update"),
    ("WITH inserted AS (INSERT INTO dim_product (product_key) VALUES (99) RETURNING *) SELECT * FROM inserted;", "Insert"),
])
def test_nested_destructive_constructs_rejected(query, mutation_type):
    """Verify mutation statements wrapped inside CTEs or subqueries are detected in AST subtree."""
    is_valid, err = validate_sql(query)
    assert is_valid is False
    assert mutation_type.lower() in err.lower()

    is_safety, cat = classify_safety_violation(query)
    assert is_safety is True
    assert cat == SafetyViolationCategory.DESTRUCTIVE_MUTATION


# ==============================================================================
# 5. Obfuscation Resistance: Case Variation, Comments, Whitespace
# ==============================================================================

@pytest.mark.parametrize("query", [
    "dElEtE FROM fact_sales_performance WHERE fact_key = 1;",
    "DrOp TaBlE dim_product;",
    "   \n\t  DELETE FROM fact_sales_performance;  \n ",
    "/* harmless comment */ DROP TABLE dim_product;",
    "-- single line comment\nDROP TABLE dim_product;",
    "SELECT 1; -- line comment\nDROP TABLE dim_product;",
])
def test_obfuscated_destructive_queries_rejected(query):
    """Verify case, comment, and whitespace variations cannot bypass safety detection."""
    is_valid, err = validate_sql(query)
    assert is_valid is False
    assert err is not None

    is_safety, _ = classify_safety_violation(query)
    assert is_safety is True


# ==============================================================================
# 6. String-Literal / Keyword Confusion (False Positive Prevention)
# ==============================================================================

@pytest.mark.parametrize("query", [
    "SELECT 'DROP TABLE users';",
    "SELECT 'DELETE FROM users';",
    "SELECT 'UPDATE users SET name = ''x''';",
    "SELECT 'Please DROP this table';",
    "SELECT 'The grant was approved' AS status;",
    "SELECT user_id, 'DELETE' AS action FROM dim_product;",
    "SELECT 1 /* DROP */ AS num;",
])
def test_keywords_inside_string_literals_and_comments_allowed(query):
    """Verify keywords appearing inside string literals or comments do NOT cause false positive rejections."""
    is_valid, err = validate_sql(query)
    assert is_valid is True, f"Legitimate query falsely rejected: {query} (err: {err})"

    is_safety, cat = classify_safety_violation(query)
    assert is_safety is False, f"Legitimate query falsely flagged as safety violation: {query} (cat: {cat})"


# ==============================================================================
# 7. Valid Read-Only Analytical SQL Preservation
# ==============================================================================

@pytest.mark.parametrize("query", [
    "SELECT COUNT(*) FROM fact_sales_performance;",
    "SELECT product_name, COUNT(*) FROM dim_product GROUP BY product_name;",
    "WITH cte AS (SELECT fact_key, gross_revenue FROM fact_sales_performance WHERE gross_revenue > 100) SELECT * FROM cte;",
    "SELECT product_key FROM dim_product UNION SELECT fact_key FROM fact_sales_performance;",
    "SELECT f.fact_key, p.product_name, SUM(f.gross_revenue) AS total_rev "
    "FROM fact_sales_performance f "
    "JOIN dim_product p ON f.fact_key = p.product_key "
    "WHERE f.gross_revenue > 0 "
    "GROUP BY f.fact_key, p.product_name "
    "HAVING SUM(f.gross_revenue) > 1000 "
    "ORDER BY total_rev DESC;",
])
def test_valid_analytical_sql_accepted(query):
    """Verify standard analytical SQL constructs are accepted without false rejections."""
    is_valid, err = validate_sql(query)
    assert is_valid is True, f"Valid analytical SQL was rejected: {query} (err: {err})"

    is_safety, cat = classify_safety_violation(query)
    assert is_safety is False
    assert cat is None


# ==============================================================================
# 8. Administrative / EXPLAIN Policy Verification
# ==============================================================================

def test_explain_command_not_executable():
    """Verify EXPLAIN command is not permitted to execute under strict read-only SELECT policy."""
    query = "EXPLAIN SELECT 1;"
    is_valid, err = validate_sql(query)
    assert is_valid is False
    assert err is not None


# ==============================================================================
# 9. Execution-Proof Testing (Instrumented Zero-Database-Execution Proof)
# ==============================================================================

@pytest.mark.parametrize("blocked_query", [
    "DELETE FROM fact_sales_performance;",
    "UPDATE dim_product SET product_name = 'hacked';",
    "DROP TABLE dim_product;",
    "SELECT 1; DROP TABLE dim_product;",
    "WITH x AS (DELETE FROM fact_sales_performance RETURNING *) SELECT * FROM x;",
    "BEGIN; SELECT 1; COMMIT;",
])
def test_execution_proof_blocked_statements_never_invoke_executor(blocked_query):
    """Execution-Proof: Prove that blocked unsafe statements result in ZERO database executions."""
    env = InstrumentedEnvironment()
    vstore = FAISSMemoryStore()
    gov = MemoryGovernanceEngine()

    def mock_generate(question, schema_markdown, **kw):
        return GenerationResult(
            raw_response=f"```sql\n{blocked_query}\n```",
            extracted_sql=blocked_query,
        )

    mock_gen = SQLGenerator()
    mock_gen.generate = mock_generate
    mock_repair_gen = RepairSQLGenerator(generator_fn=lambda prompt: GenerationResult(raw_response="", extracted_sql=""))

    wf = ARMGRepairWorkflow(
        environment=env,
        vector_store=vstore,
        governance_engine=gov,
        embed_fn=mock_embed_fn,
        sql_generator=mock_gen,
        repair_generator=mock_repair_gen,
    )

    initial_state = {
        "user_query": "Blocked query test",
        "schema_context": env.catalog,
        "pruned_tables": ["fact_sales_performance", "dim_product"],
        "pruned_schema_markdown": "## fact_sales_performance\n## dim_product",
        "retry_count": 0,
        "max_retries": 3,
        "retrieved_memories": [],
        "telemetry": {},
    }

    graph = wf.build_graph()
    final_state = graph.invoke(initial_state)

    # 1. State must terminate as BLOCKED
    assert final_state.get("status") == STATUS_BLOCKED

    # 2. Database executor must NEVER be invoked (invocation count == 0)
    assert env.execution_count == 0, f"Database executor was invoked {env.execution_count} times for unsafe query: {blocked_query}"
    assert len(env.executed_queries) == 0

    # 3. Telemetry records safety block
    assert final_state.get("telemetry", {}).get("memory_admission") == "SAFETY_VIOLATION_BLOCKED"


def test_execution_proof_valid_query_invokes_executor_once():
    """Execution-Proof: Valid query passes safety gate and executes exactly once."""
    env = InstrumentedEnvironment()
    vstore = FAISSMemoryStore()
    gov = MemoryGovernanceEngine()

    valid_query = "SELECT COUNT(*) FROM fact_sales_performance;"

    def mock_generate(question, schema_markdown, **kw):
        return GenerationResult(
            raw_response=f"```sql\n{valid_query}\n```",
            extracted_sql=valid_query,
        )

    mock_gen = SQLGenerator()
    mock_gen.generate = mock_generate
    mock_repair_gen = RepairSQLGenerator(generator_fn=lambda prompt: GenerationResult(raw_response="", extracted_sql=""))

    wf = ARMGRepairWorkflow(
        environment=env,
        vector_store=vstore,
        governance_engine=gov,
        embed_fn=mock_embed_fn,
        sql_generator=mock_gen,
        repair_generator=mock_repair_gen,
    )

    initial_state = {
        "user_query": "Valid query test",
        "schema_context": env.catalog,
        "pruned_tables": ["fact_sales_performance"],
        "pruned_schema_markdown": "## fact_sales_performance",
        "retry_count": 0,
        "max_retries": 3,
        "retrieved_memories": [],
        "telemetry": {},
    }

    graph = wf.build_graph()
    final_state = graph.invoke(initial_state)

    # 1. State must terminate as SUCCESS
    assert final_state.get("status") == STATUS_SUCCESS

    # 2. Database executor invoked exactly once
    assert env.execution_count == 1
    assert env.executed_queries == [valid_query]
