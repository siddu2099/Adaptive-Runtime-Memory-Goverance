"""
Regression and Safety Guard Tests for ARMG AST Guardrail and BLOCKED State.

Verifies:
- Test A: DELETE statement is rejected, workflow status is BLOCKED, zero repair attempts,
  zero PostgreSQL executions, zero RuntimeKnowledge, zero memory admissions, zero FAISS insertions.
- Test B: UPDATE statement is BLOCKED with zero executions and zero repair calls.
- Test C: DROP statement is BLOCKED with zero executions and zero repair calls.
- Test D: Multi-statement destructive input is BLOCKED with zero executions.
- Test E: Normal analytical SELECT produces STATUS_SUCCESS with zero retries.
- Test F: Repairable runtime error (semantic column mistake) routes through observation -> diagnosis
  -> knowledge -> repair and NOT BLOCKED.
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
from validation.execution_validator import ExecutionValidator, SafetyViolationCategory


class MockEnvironment:
    """Mock database environment tracking executed queries."""

    def __init__(self):
        self.catalog = {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer", "is_pk": True},
                        {"name": "gross_revenue", "type": "numeric", "is_pk": False},
                        {"name": "net_profit", "type": "numeric", "is_pk": False},
                    ]
                }
            }
        }
        self.executed_queries: List[str] = []

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, payload: str) -> ExecutionResult:
        self.executed_queries.append(payload)
        # Simulate PostgreSQL column error if querying unmapped 'revenue'
        if "revenue" in payload.lower() and "gross_revenue" not in payload.lower():
            return ExecutionResult(
                status="FAILURE",
                query=payload,
                error='column "revenue" does not exist',
                execution_time_ms=2.0,
            )
        return ExecutionResult(
            status="SUCCESS",
            query=payload,
            rows=[{"gross_revenue": 1000.0}],
            row_count=1,
            execution_time_ms=1.5,
        )


def mock_embed_fn(text: str) -> List[float]:
    return [0.1] * 768


class TestSafetyGuardrail:
    """Test suite verifying strict safety guard termination without repair."""

    def test_a_delete_statement_is_blocked(self):
        """Test A: DELETE FROM fact_sales_performance; is BLOCKED."""
        env = MockEnvironment()
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()

        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nDELETE FROM fact_sales_performance;\n```",
                extracted_sql="DELETE FROM fact_sales_performance;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(
                raw_response="```sql\nSELECT * FROM fact_sales_performance;\n```",
                extracted_sql="SELECT * FROM fact_sales_performance;",
            )

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            governance_engine=gov,
            vector_store=vstore,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({
            "user_query": "Delete all records from the sales table.",
            "max_retries": 3,
        })

        # 1. Validator rejected the DELETE
        assert result["validation_passed"] is False
        assert result["is_safety_violation"] is True
        assert result["safety_category"] == SafetyViolationCategory.DESTRUCTIVE_MUTATION

        # 2. Workflow status is BLOCKED
        assert result["status"] == STATUS_BLOCKED

        # 3. Zero repair attempts
        assert result.get("retry_count", 0) == 0
        assert repair_called["count"] == 0
        assert result.get("telemetry", {}).get("repair_count", 0) == 0

        # 4. Zero PostgreSQL execution attempts
        assert len(env.executed_queries) == 0
        assert "DELETE FROM fact_sales_performance;" not in env.executed_queries

        # 5. Zero RuntimeKnowledge
        assert result.get("runtime_knowledge") is None

        # 6. Zero memory admission
        assert result.get("telemetry", {}).get("memory_admission") == "SAFETY_VIOLATION_BLOCKED"
        assert result.get("telemetry", {}).get("admitted_memory_id") is None

        # 7. Zero FAISS insertion
        assert vstore.count() == 0

    def test_b_update_statement_is_blocked(self):
        """Test B: UPDATE fact_sales_performance SET gross_revenue = 0; is BLOCKED."""
        env = MockEnvironment()
        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nUPDATE fact_sales_performance SET gross_revenue = 0;\n```",
                extracted_sql="UPDATE fact_sales_performance SET gross_revenue = 0;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(raw_response="", extracted_sql="")

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Zero out sales revenue", "max_retries": 3})

        assert result["status"] == STATUS_BLOCKED
        assert result["is_safety_violation"] is True
        assert len(env.executed_queries) == 0
        assert repair_called["count"] == 0
        assert result.get("retry_count", 0) == 0

    def test_c_drop_statement_is_blocked(self):
        """Test C: DROP TABLE fact_sales_performance; is BLOCKED."""
        env = MockEnvironment()
        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nDROP TABLE fact_sales_performance;\n```",
                extracted_sql="DROP TABLE fact_sales_performance;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(raw_response="", extracted_sql="")

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Drop the sales table", "max_retries": 3})

        assert result["status"] == STATUS_BLOCKED
        assert result["is_safety_violation"] is True
        assert len(env.executed_queries) == 0
        assert repair_called["count"] == 0
        assert result.get("retry_count", 0) == 0

    def test_d_multi_statement_destructive_input_is_blocked(self):
        """Test D: SELECT 1; DROP TABLE fact_sales_performance; is BLOCKED."""
        env = MockEnvironment()
        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nSELECT 1; DROP TABLE fact_sales_performance;\n```",
                extracted_sql="SELECT 1; DROP TABLE fact_sales_performance;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(raw_response="", extracted_sql="")

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "Injected drop", "max_retries": 3})

        assert result["status"] == STATUS_BLOCKED
        assert result["is_safety_violation"] is True
        assert result["safety_category"] == SafetyViolationCategory.MULTI_STATEMENT
        assert len(env.executed_queries) == 0
        assert repair_called["count"] == 0

    def test_e_normal_analytical_select_succeeds(self):
        """Test E: SELECT SUM(gross_revenue) FROM fact_sales_performance; succeeds normally."""
        env = MockEnvironment()

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nSELECT SUM(gross_revenue) FROM fact_sales_performance;\n```",
                extracted_sql="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
            )

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "What is total revenue?", "max_retries": 3})

        assert result["status"] == STATUS_SUCCESS
        assert result["validation_passed"] is True
        assert result["is_safety_violation"] is False
        assert result.get("retry_count", 0) == 0
        assert len(env.executed_queries) == 1
        assert "SELECT SUM(gross_revenue) FROM fact_sales_performance;" in env.executed_queries[0]

    def test_f_repairable_runtime_error_not_blocked(self):
        """Test F: Ordinary repairable failure (e.g. unknown column) enters repair loop, NOT blocked."""
        env = MockEnvironment()
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()
        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            governance_engine=gov,
            vector_store=vstore,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": "What is total revenue?", "max_retries": 3})

        # Failure was semantic/execution, NOT an AST safety violation
        assert result["is_safety_violation"] is False
        # Repaired successfully through observation -> diagnosis -> knowledge -> repair
        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 1
        assert repair_called["count"] == 1
        assert len(env.executed_queries) == 2
        # Verify RuntimeKnowledge from Attempt 1 was preserved and admitted upon repair success
        assert result.get("runtime_knowledge") is not None
        assert result.get("telemetry", {}).get("memory_admission") == "ADMITTED"
        assert vstore.count() == 1

    def test_multi_attempt_runtime_failure_to_safety_block(self):
        """Test A (Multi-attempt): Attempt 1 execution failure -> retry 1 -> Attempt 2 DELETE -> BLOCKED.
        
        Verifies:
        - final status is BLOCKED
        - retry_count == 1 (preserved from Attempt 1)
        - generation_attempts == 2
        - validation_passed is False
        - is_safety_violation is True
        - safety_category == 'destructive_mutation'
        - execution_result is None for the final blocked attempt
        - diagnosis is None for the final blocked attempt
        - runtime_knowledge is None for the final blocked attempt
        - only Attempt 1 was executed in PostgreSQL (count == 1)
        - DELETE was never executed
        - previous_sql contains Attempt 1 SQL
        - previous_execution_error contains Attempt 1 error
        """
        env = MockEnvironment()
        vstore = FAISSMemoryStore()
        gov = MemoryGovernanceEngine()
        repair_called = {"count": 0}

        def mock_generate(question, schema_markdown, **kw):
            return GenerationResult(
                raw_response="```sql\nSELECT revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT revenue FROM fact_sales_performance;",
            )

        def mock_repair(prompt):
            repair_called["count"] += 1
            return GenerationResult(
                raw_response="```sql\nDELETE FROM fact_sales_performance;\n```",
                extracted_sql="DELETE FROM fact_sales_performance;",
            )

        mock_gen = SQLGenerator()
        mock_gen.generate = mock_generate
        mock_repair_gen = RepairSQLGenerator(generator_fn=mock_repair)

        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair_gen,
            governance_engine=gov,
            vector_store=vstore,
            embed_fn=mock_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({
            "user_query": "Delete all records from the sales table.",
            "max_retries": 3,
        })

        # 1. Final status is BLOCKED
        assert result["status"] == STATUS_BLOCKED

        # 2. Correct retry semantics: 1 retry occurred, 2 generations performed
        assert result["retry_count"] == 1
        assert result.get("telemetry", {}).get("generation_attempts") == 2
        assert repair_called["count"] == 1

        # 3. Safety rejection attributes
        assert result["validation_passed"] is False
        assert result["is_safety_violation"] is True
        assert result["safety_category"] == SafetyViolationCategory.DESTRUCTIVE_MUTATION

        # 4. State hygiene: final attempt MUST NOT carry stale execution, diagnosis, or knowledge
        assert result.get("execution_result") is None
        assert result.get("diagnosis") is None
        assert result.get("runtime_knowledge") is None

        # 5. PostgreSQL execution count = 1 (only Attempt 1 reached PostgreSQL)
        assert len(env.executed_queries) == 1
        assert "SELECT revenue FROM fact_sales_performance;" in env.executed_queries[0]
        assert "DELETE FROM fact_sales_performance;" not in env.executed_queries

        # 6. Historical preservation
        assert result.get("previous_sql") == "SELECT revenue FROM fact_sales_performance;"
        assert result.get("previous_execution_error") == 'column "revenue" does not exist'

        # 7. Memory governance: no admission, no FAISS insertion
        assert result.get("telemetry", {}).get("memory_admission") == "SAFETY_VIOLATION_BLOCKED"
        assert vstore.count() == 0
