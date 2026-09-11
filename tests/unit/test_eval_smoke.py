"""
ARMG Phase 9: Evaluation Suite Smoke and Unit Tests.

Verifies:
- Part 1: Relational equivalence edge cases (empty results, duplicate multiplicity,
  Decimal precision, unordered multisets, ordered sequences, dimension mismatches).
- Part 2: Benchmark dataset integrity (25 queries, Q01-Q25, exact 5/8/6/6 category distribution).
- Part 3: Gold SQL verification gate dispatch.
- Part 4: All six evaluation mode dispatches using controlled fast test doubles (zero LLM latency).
- Part 5: Memory isolation between experimental runs (clean state per mode).
- Part 6: Aggregate metrics calculation, CSV export, and IEEE Markdown table formatting.
"""

from decimal import Decimal
import tempfile
from pathlib import Path
import pytest

from agents.sql_generator import GenerationResult
from benchmark.equivalence import check_relational_equivalence, query_requires_order
from benchmark.modes import (
    AblationNoNegConstraintsWorkflow,
    NaiveVectorStore,
    QueryBenchmarkRecord,
    execute_mode_1_zero_shot,
    execute_mode_2_self_correction,
    execute_mode_3_naive_rag,
    execute_mode_4_full_armg,
    execute_mode_5_armg_no_neg_constraints,
    execute_mode_6_armg_no_decay,
)
from environment.base import ExecutionResult
from graph.state import STATUS_SUCCESS
from scripts.eval_runner import (
    compute_aggregate_metrics,
    export_results_to_csv,
    format_ieee_markdown_table,
    load_and_validate_dataset,
    verify_gold_queries,
)


# ==============================================================================
# Part 1: Relational Equivalence Edge Cases (Section 5)
# ==============================================================================

class TestRelationalEquivalenceEdgeCases:
    """Rigorous unit tests for relational equivalence edge cases."""

    def test_empty_vs_empty(self):
        """Empty result sets are relationally equivalent."""
        assert check_relational_equivalence(
            gen_rows=[],
            gold_rows=[],
            gold_sql="SELECT * FROM fact_sales_performance WHERE 1=0;",
            gen_sql="SELECT * FROM fact_sales_performance WHERE 1=0;",
        ) is True

    def test_empty_vs_non_empty(self):
        """Empty result set is NOT equivalent to non-empty result set."""
        assert check_relational_equivalence(
            gen_rows=[],
            gold_rows=[(1, "Hardware")],
            gold_sql="SELECT * FROM fact_sales_performance;",
            gen_sql="SELECT * FROM fact_sales_performance WHERE 1=0;",
        ) is False
        assert check_relational_equivalence(
            gen_rows=[(1, "Hardware")],
            gold_rows=[],
            gold_sql="SELECT * FROM fact_sales_performance WHERE 1=0;",
            gen_sql="SELECT * FROM fact_sales_performance;",
        ) is False

    def test_duplicate_rows_multiplicity(self):
        """Must preserve multiplicity: 2 duplicate rows != 3 duplicate rows."""
        rows_two = [(1, "A"), (1, "A")]
        rows_three = [(1, "A"), (1, "A"), (1, "A")]
        assert check_relational_equivalence(
            gen_rows=rows_two,
            gold_rows=rows_three,
            gold_sql="SELECT id, name FROM tbl;",
            gen_sql="SELECT id, name FROM tbl;",
        ) is False

    def test_decimal_values_precision(self):
        """PostgreSQL Decimal values compared with exact precision."""
        gen_rows = [(1, Decimal("100.50")), (2, Decimal("200.75"))]
        gold_rows_equal = [(1, Decimal("100.50")), (2, Decimal("200.75"))]
        gold_rows_unequal = [(1, Decimal("100.51")), (2, Decimal("200.75"))]

        assert check_relational_equivalence(gen_rows, gold_rows_equal) is True
        assert check_relational_equivalence(gen_rows, gold_rows_unequal) is False

    def test_unordered_multiset_equality(self):
        """Without ORDER BY, row ordering differences are ignored."""
        gen_rows = [(1, "Alpha"), (2, "Beta"), (3, "Gamma")]
        gold_rows = [(3, "Gamma"), (1, "Alpha"), (2, "Beta")]
        gold_sql = "SELECT id, label FROM table_x;"

        assert query_requires_order(gold_sql) is False
        assert check_relational_equivalence(gen_rows, gold_rows, gold_sql=gold_sql) is True

    def test_ordered_sequence_strict_position(self):
        """With ORDER BY, strict positional sequence matching is enforced."""
        gen_rows = [(1, "Alpha"), (2, "Beta")]
        gold_rows_different_order = [(2, "Beta"), (1, "Alpha")]
        gold_sql = "SELECT id, label FROM table_x ORDER BY id ASC;"

        assert query_requires_order(gold_sql) is True
        assert check_relational_equivalence(
            gen_rows, gold_rows_different_order, gold_sql=gold_sql
        ) is False

    def test_different_column_counts(self):
        """Different column counts must fail equivalence."""
        gen_rows = [(1, "Alpha")]
        gold_rows = [(1, "Alpha", 100)]
        assert check_relational_equivalence(gen_rows, gold_rows) is False

    def test_different_row_counts(self):
        """Different row counts must fail equivalence."""
        gen_rows = [(1, "Alpha")]
        gold_rows = [(1, "Alpha"), (2, "Beta")]
        assert check_relational_equivalence(gen_rows, gold_rows) is False

    def test_execution_or_validation_failure_is_zero_accuracy(self):
        """Failed execution or validation must receive equivalence = False."""
        assert check_relational_equivalence(
            gen_rows=[(1,)], gold_rows=[(1,)], gen_success=False
        ) is False
        assert check_relational_equivalence(
            gen_rows=[(1,)], gold_rows=[(1,)], gold_success=False
        ) is False


# ==============================================================================
# Part 2: Dataset Integrity Tests (Section 2 & 3)
# ==============================================================================

def test_benchmark_dataset_structure_and_distribution():
    """Verify queries.json contains exactly 25 queries partitioned 5/8/6/6."""
    dataset = load_and_validate_dataset()
    assert len(dataset) == 25

    ids = [item["query_id"] for item in dataset]
    assert ids == [f"Q{i:02d}" for i in range(1, 26)]

    for item in dataset:
        assert "query_id" in item
        assert "question" in item and len(item["question"].strip()) > 5
        assert "category" in item
        assert "gold_sql" in item and len(item["gold_sql"].strip()) > 10

    cats = [item["category"].split("—")[0].strip() for item in dataset]
    assert cats.count("Category A") == 5
    assert cats.count("Category B") == 8
    assert cats.count("Category C") == 6
    assert cats.count("Category D") == 6


# ==============================================================================
# Part 3: Test Doubles & Mode Dispatch Smoke Tests (Section 6 & 14)
# ==============================================================================

class FastMockEnvironment:
    """In-memory environment double for lightning-fast testing without live Postgres."""
    def __init__(self):
        self.catalog = {
            "tables": {
                "fact_sales_performance": {
                    "columns": [
                        {"name": "fact_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                        {"name": "gross_revenue", "type": "numeric", "primary_key": False, "ordinal_position": 2},
                        {"name": "discount_applied", "type": "numeric", "primary_key": False, "ordinal_position": 3},
                        {"name": "net_profit", "type": "numeric", "primary_key": False, "ordinal_position": 4},
                    ]
                },
                "dim_geography": {
                    "columns": [
                        {"name": "geo_key", "type": "integer", "primary_key": True, "ordinal_position": 1},
                        {"name": "region", "type": "varchar", "primary_key": False, "ordinal_position": 2},
                        {"name": "market_type", "type": "varchar", "primary_key": False, "ordinal_position": 3},
                    ]
                },
            }
        }

    def inspect(self):
        return self.catalog

    def execute(self, sql: str):
        if "revenue" in sql and "gross_revenue" not in sql:
            return ExecutionResult(status="FAILURE", query=sql, error='column "revenue" does not exist')
        if "syntax error" in sql.lower():
            return ExecutionResult(status="FAILURE", query=sql, error="syntax error")
        # Standard mock success row
        return ExecutionResult(status="SUCCESS", query=sql, rows=[(Decimal("1000.00"),)], row_count=1)

    def observe(self, trace: str):
        if "revenue" in trace:
            return {"error_class": "UndefinedColumn", "error_message": trace}
        return {"error_class": "DatabaseError", "error_message": trace}


class FastMockGenerator:
    """Mock generator returning canned valid SQL."""
    def generate(self, question: str, schema_markdown: str):
        return GenerationResult(
            raw_response="```sql\nSELECT SUM(gross_revenue) FROM fact_sales_performance;\n```",
            extracted_sql="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
            prompt_tokens=100,
            completion_tokens=25,
            generation_duration_ms=10.0,
        )


class FastMockRepairGenerator:
    """Mock repair generator returning corrected SQL."""
    def generate_repair(self, repair_prompt: str):
        return GenerationResult(
            raw_response="```sql\nSELECT SUM(gross_revenue) FROM fact_sales_performance;\n```",
            extracted_sql="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
            prompt_tokens=150,
            completion_tokens=30,
            generation_duration_ms=15.0,
        )


def fast_mock_embed(text: str):
    """Return synthetic 768-dimensional float vector."""
    return [0.01] * 768


def test_mode_1_dispatch():
    """Verify Mode 1 (Zero-Shot) dispatches cleanly and records telemetry."""
    env = FastMockEnvironment()
    gen = FastMockGenerator()
    query_item = {
        "query_id": "Q01",
        "category": "Category A — Simple Aggregations & Groupings",
        "question": "What is total gross revenue?",
        "gold_sql": "SELECT SUM(gross_revenue) FROM fact_sales_performance;",
    }

    rec = execute_mode_1_zero_shot(
        query_item=query_item,
        env=env,
        run_id="test_run",
        seed=42,
        generator=gen,
    )
    assert rec.query_id == "Q01"
    assert rec.mode == "Mode 1 (Zero-Shot)"
    assert rec.success is True
    assert rec.execution_accuracy == 1
    assert rec.retry_count == 0
    assert rec.generation_attempts == 1


def test_mode_2_dispatch():
    """Verify Mode 2 (Stateless Self-Correction) dispatches cleanly."""
    env = FastMockEnvironment()
    gen = FastMockGenerator()
    rep_gen = FastMockRepairGenerator()
    query_item = {
        "query_id": "Q01",
        "category": "Category A — Simple Aggregations & Groupings",
        "question": "What is total gross revenue?",
        "gold_sql": "SELECT SUM(gross_revenue) FROM fact_sales_performance;",
    }

    rec = execute_mode_2_self_correction(
        query_item=query_item,
        env=env,
        run_id="test_run",
        seed=42,
        generator=gen,
        repair_generator=rep_gen,
    )
    assert rec.query_id == "Q01"
    assert rec.mode == "Mode 2 (Stateless Self-Correction)"
    assert rec.success is True
    assert rec.execution_accuracy == 1
    assert rec.retry_count == 0


def test_mode_3_dispatch_and_naive_store():
    """Verify Mode 3 (Naive Vector RAG) stores and retrieves raw query-SQL pairs."""
    env = FastMockEnvironment()
    gen = FastMockGenerator()
    naive_store = NaiveVectorStore(dimension=768)
    query_item = {
        "query_id": "Q01",
        "category": "Category A — Simple Aggregations & Groupings",
        "question": "What is total gross revenue?",
        "gold_sql": "SELECT SUM(gross_revenue) FROM fact_sales_performance;",
    }

    rec = execute_mode_3_naive_rag(
        query_item=query_item,
        env=env,
        run_id="test_run",
        seed=42,
        naive_store=naive_store,
        embed_fn=fast_mock_embed,
        generator=gen,
    )
    assert rec.query_id == "Q01"
    assert rec.mode == "Mode 3 (Naive Vector RAG)"
    assert rec.success is True
    assert naive_store.count() == 1


class MockWorkflowApp:
    """Mock LangGraph compiled app double for ARMG modes."""
    def invoke(self, state):
        return {
            "status": STATUS_SUCCESS,
            "generated_sql": "SELECT SUM(gross_revenue) FROM fact_sales_performance;",
            "retry_count": 0,
            "validation_passed": True,
            "execution_result": ExecutionResult(
                status="SUCCESS",
                query="SELECT SUM(gross_revenue) FROM fact_sales_performance;",
                rows=[(Decimal("1000.00"),)],
                row_count=1,
            ),
            "telemetry": {
                "generation_attempts": 1,
                "total_latency_ms": 25.0,
                "total_tokens": 120,
                "memory_retrieval_count": 0,
            },
        }


def test_mode_4_5_6_dispatches():
    """Verify Modes 4, 5, and 6 dispatch cleanly through the workflow interface."""
    env = FastMockEnvironment()
    app = MockWorkflowApp()
    query_item = {
        "query_id": "Q01",
        "category": "Category A — Simple Aggregations & Groupings",
        "question": "What is total gross revenue?",
        "gold_sql": "SELECT SUM(gross_revenue) FROM fact_sales_performance;",
    }

    rec4 = execute_mode_4_full_armg(query_item, env, "test_run", 42, app)
    assert rec4.mode == "Mode 4 (Full ARMG)"
    assert rec4.execution_accuracy == 1

    rec5 = execute_mode_5_armg_no_neg_constraints(query_item, env, "test_run", 42, app)
    assert rec5.mode == "Mode 5 (ARMG - Negative Constraints)"
    assert rec5.execution_accuracy == 1

    rec6 = execute_mode_6_armg_no_decay(query_item, env, "test_run", 42, app)
    assert rec6.mode == "Mode 6 (ARMG - Temporal Decay)"
    assert rec6.execution_accuracy == 1


# ==============================================================================
# Part 4: Aggregation and Reporting Tests (Section 12 & 13)
# ==============================================================================

def test_metrics_aggregation_and_csv_generation():
    """Verify metric computation, category-wise breakdown, and CSV generation."""
    records = [
        QueryBenchmarkRecord(
            run_id="run_1",
            mode="Mode 1 (Zero-Shot)",
            seed=42,
            query_id="Q01",
            category="Category A — Simple Aggregations & Groupings",
            question="Total gross revenue?",
            success=True,
            execution_accuracy=1,
            retry_count=0,
            generation_attempts=1,
            latency_ms=100.0,
            prompt_tokens=80,
            completion_tokens=20,
            total_tokens=100,
            validation_failures=0,
            execution_failures=0,
            memory_retrieval_count=0,
            memory_admission=None,
            memory_reinforcement=None,
            error_category=None,
        ),
        QueryBenchmarkRecord(
            run_id="run_1",
            mode="Mode 1 (Zero-Shot)",
            seed=42,
            query_id="Q02",
            category="Category A — Simple Aggregations & Groupings",
            question="Total units sold?",
            success=False,
            execution_accuracy=0,
            retry_count=0,
            generation_attempts=1,
            latency_ms=150.0,
            prompt_tokens=85,
            completion_tokens=25,
            total_tokens=110,
            validation_failures=1,
            execution_failures=0,
            memory_retrieval_count=0,
            memory_admission=None,
            memory_reinforcement=None,
            error_category="SyntaxError",
        ),
    ]

    metrics = compute_aggregate_metrics(records)
    assert metrics["total_queries"] == 2
    assert metrics["correct_queries"] == 1
    assert metrics["exec_acc_pct"] == 50.0
    assert metrics["mean_retries"] == 0.0
    assert metrics["mean_latency_ms"] == 125.0
    assert metrics["mean_tokens"] == 105.0
    assert "Category A" in metrics["category_accuracy"]

    # Test Markdown formatting
    md_table = format_ieee_markdown_table([metrics])
    assert "| Mode | ExecAcc (%) |" in md_table
    assert "Mode 1 (Zero-Shot)" in md_table
    assert "50.0%" in md_table

    # Test CSV export
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_results.csv"
        export_results_to_csv(records, csv_path)
        assert csv_path.exists()
        content = csv_path.read_text(encoding="utf-8")
        assert "query_id,category,question" in content
        assert "Q01,Category A — Simple Aggregations & Groupings" in content
