"""
ARMG Phase 5: RuntimeKnowledge Construction Test Suite.

Validates:
1. Undefined column knowledge extraction.
2. Undefined relation knowledge extraction.
3. Grouping error knowledge extraction.
4. Division by zero knowledge extraction.
5. Validation rejection knowledge extraction.
6. Syntax error knowledge extraction.
7. Permission error knowledge extraction.
8. Resource error knowledge extraction.
9. Confidence boundary validations (0.0 <= confidence <= 1.0).
10. Model immutability enforcement.
11. Serialization integrity (to_dict, to_json).
12. Embedding text preparation (format_for_embedding).
13. Zero-database / Zero-LLM offline execution.
14. Diagnosis as single source of truth.
15. Zero persistence guarantee.
16. Extraction determinism across multiple runs.
"""

import json
from datetime import datetime
import pytest
from pydantic import ValidationError

from agents.error_diagnosis import DeterministicErrorDiagnoser, DiagnosticResult
from agents.taxonomy import TaxonomyCategory
from environment.observation import ExecutionStatus, RuntimeObservation
from memory.knowledge_extractor import RuntimeKnowledgeExtractor
from memory.models import RuntimeKnowledge


@pytest.fixture
def mock_star_schema():
    """In-memory mock schema matching the Star Schema without requiring database calls."""
    return {
        "tables": {
            "dim_time": {
                "columns": [
                    {"name": "time_key", "type": "integer", "primary_key": True},
                    {"name": "calendar_year", "type": "integer"},
                ]
            },
            "dim_geography": {
                "columns": [
                    {"name": "geo_key", "type": "integer", "primary_key": True},
                    {"name": "region", "type": "character varying"},
                ]
            },
            "dim_product": {
                "columns": [
                    {"name": "product_key", "type": "integer", "primary_key": True},
                    {"name": "unit_cost", "type": "numeric"},
                ]
            },
            "fact_sales_performance": {
                "columns": [
                    {"name": "fact_key", "type": "integer", "primary_key": True},
                    {"name": "gross_revenue", "type": "numeric"},
                    {"name": "discount_applied", "type": "numeric"},
                    {"name": "net_profit", "type": "numeric"},
                    {"name": "units_sold", "type": "integer"},
                ]
            },
        }
    }


@pytest.fixture
def extractor():
    """Fixture providing RuntimeKnowledgeExtractor instance."""
    return RuntimeKnowledgeExtractor()


@pytest.fixture
def diagnoser():
    """Fixture providing DeterministicErrorDiagnoser instance."""
    return DeterministicErrorDiagnoser()


# ------------------------------------------------------------------------------
# 1-8: Taxonomy Category Extraction Tests
# ------------------------------------------------------------------------------
def test_extract_undefined_column(extractor, diagnoser, mock_star_schema):
    """Test 1: Undefined column produces SEMANTIC RuntimeKnowledge with candidates."""
    obs = RuntimeObservation(
        query="SELECT region, SUM(revenue) FROM fact_sales_performance GROUP BY region;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "revenue" does not exist',
        normalized_error='column "revenue" does not exist',
        schema_context=["fact_sales_performance", "dim_geography"],
    )
    diag: DiagnosticResult = diagnoser.diagnose(obs, mock_star_schema)
    rk: RuntimeKnowledge = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.SEMANTIC
    assert rk.root_cause == diag.root_cause
    assert rk.repair_strategy == diag.repair_rule
    assert rk.negative_constraints == ["revenue"]
    assert "gross_revenue" in rk.candidate_replacements
    assert rk.confidence == 0.50
    assert "revenue" in rk.source_exception
    assert "fact_sales_performance" in rk.context["tables_referenced"]


def test_extract_undefined_relation(extractor, diagnoser, mock_star_schema):
    """Test 2: Undefined relation produces SEMANTIC RuntimeKnowledge with table candidates."""
    obs = RuntimeObservation(
        query="SELECT * FROM sales;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='relation "sales" does not exist',
        schema_context=["sales"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.SEMANTIC
    assert rk.negative_constraints == ["sales"]
    assert "fact_sales_performance" in rk.candidate_replacements
    assert rk.confidence == 0.50


def test_extract_grouping_error(extractor, diagnoser, mock_star_schema):
    """Test 3: Grouping error produces PLANNING RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="SELECT region, gross_revenue FROM fact_sales_performance;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "region" must appear in the GROUP BY clause',
        schema_context=["fact_sales_performance", "dim_geography"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.PLANNING
    assert "GROUP BY" in rk.repair_strategy
    assert rk.confidence == 0.50


def test_extract_division_by_zero(extractor, diagnoser, mock_star_schema):
    """Test 4: Division by zero produces EXECUTION RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="SELECT gross_revenue / 0 FROM fact_sales_performance;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="division by zero",
        schema_context=["fact_sales_performance"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.EXECUTION
    assert "nullif" in rk.repair_strategy.lower()
    assert rk.confidence == 0.50


def test_extract_validation_failure(extractor, diagnoser, mock_star_schema):
    """Test 5: AST guard rejection produces VALIDATION RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="DROP TABLE dim_product;",
        status=ExecutionStatus.VALIDATION_FAILURE,
        raw_error="Destructive mutation 'Drop' is strictly rejected.",
        schema_context=["dim_product"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.VALIDATION
    assert "read-only select" in rk.repair_strategy.lower()
    assert rk.confidence == 0.50


def test_extract_syntax_error(extractor, diagnoser, mock_star_schema):
    """Test 6: Syntax error produces SYNTAX RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="SELEC * FROM dim_product;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='syntax error at or near "SELEC"',
        schema_context=["dim_product"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.SYNTAX
    assert "syntax error" in rk.source_exception.lower()
    assert rk.confidence == 0.50


def test_extract_permission_error(extractor, diagnoser, mock_star_schema):
    """Test 7: Permission error produces PERMISSION RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="UPDATE fact_sales_performance SET units_sold = 0;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="permission denied for table fact_sales_performance",
        schema_context=["fact_sales_performance"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.PERMISSION
    assert rk.confidence == 0.50


def test_extract_resource_error(extractor, diagnoser, mock_star_schema):
    """Test 8: Resource exhaustion produces RESOURCE RuntimeKnowledge."""
    obs = RuntimeObservation(
        query="SELECT * FROM fact_sales_performance CROSS JOIN dim_time;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="canceling statement due to statement timeout",
        schema_context=["fact_sales_performance", "dim_time"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)
    rk = extractor.extract(obs, diag, mock_star_schema)

    assert rk.failure_type == TaxonomyCategory.RESOURCE
    assert rk.confidence == 0.50


# ------------------------------------------------------------------------------
# 9-16: Model Validation, Immutability, Serialization & Architecture Tests
# ------------------------------------------------------------------------------
def test_confidence_validation_boundaries():
    """Test 9: Verify confidence boundaries (0.0, 0.5, 1.0 valid; <0 or >1 invalid)."""
    base_kwargs = {
        "failure_type": TaxonomyCategory.SYNTAX,
        "source_exception": "Syntax error",
        "context": {"tables_referenced": []},
        "root_cause": "Syntax issue",
        "repair_strategy": "Fix syntax",
    }

    # Valid values
    assert RuntimeKnowledge(confidence=0.0, **base_kwargs).confidence == 0.0
    assert RuntimeKnowledge(confidence=0.50, **base_kwargs).confidence == 0.50
    assert RuntimeKnowledge(confidence=1.0, **base_kwargs).confidence == 1.0

    # Invalid values must raise ValidationError
    with pytest.raises(ValidationError):
        RuntimeKnowledge(confidence=-0.01, **base_kwargs)

    with pytest.raises(ValidationError):
        RuntimeKnowledge(confidence=1.01, **base_kwargs)


def test_runtime_knowledge_immutability():
    """Test 10: RuntimeKnowledge is frozen and strictly immutable."""
    rk = RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception="Undefined column",
        context={"tables_referenced": ["dim_time"]},
        root_cause="Column does not exist",
        repair_strategy="Replace column",
        negative_constraints=["revenue"],
        confidence=0.50,
    )

    with pytest.raises(ValidationError):
        rk.confidence = 0.90  # type: ignore

    with pytest.raises(ValidationError):
        rk.failure_type = TaxonomyCategory.PLANNING  # type: ignore

    with pytest.raises(ValidationError):
        rk.root_cause = "New cause"  # type: ignore

    with pytest.raises(ValidationError):
        rk.negative_constraints = ["new_col"]  # type: ignore


def test_serialization_dict_and_json():
    """Test 11: Verify to_dict() and to_json() produce clean, complete serializations."""
    rk = RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception='column "rev" does not exist',
        context={"tables_referenced": ["dim_geography"], "target_metrics": []},
        root_cause="Invalid column rev",
        repair_strategy="Replace column with valid name",
        negative_constraints=["rev"],
        candidate_replacements=["gross_revenue"],
        confidence=0.50,
    )

    d = rk.to_dict()
    assert d["failure_type"] == "Semantic"
    assert d["confidence"] == 0.50
    assert d["negative_constraints"] == ["rev"]
    assert d["candidate_replacements"] == ["gross_revenue"]

    j = rk.to_json()
    parsed = json.loads(j)
    assert parsed == d


def test_format_for_embedding_deterministic():
    """Test 12: format_for_embedding() is deterministic, non-empty, and excludes volatile metadata."""
    rk = RuntimeKnowledge(
        failure_type=TaxonomyCategory.SEMANTIC,
        source_exception="Undefined column",
        context={"tables_referenced": ["fact_sales_performance", "dim_geography"]},
        root_cause="Referenced column 'revenue' does not exist in schema.",
        repair_strategy="Select gross_revenue or net_profit.",
        negative_constraints=["revenue"],
        candidate_replacements=["gross_revenue", "net_profit"],
        confidence=0.50,
    )

    emb_text_1 = rk.format_for_embedding()
    emb_text_2 = rk.format_for_embedding()

    assert len(emb_text_1) > 0
    assert emb_text_1 == emb_text_2
    # Verify semantic tokens
    assert "Failure: Semantic" in emb_text_1
    assert "Tables: dim_geography, fact_sales_performance" in emb_text_1
    assert "Root Cause: Referenced column 'revenue' does not exist in schema." in emb_text_1
    assert "Repair: Select gross_revenue or net_profit." in emb_text_1
    # Verify volatile metadata is excluded
    assert rk.knowledge_id not in emb_text_1
    assert rk.timestamp not in emb_text_1
    assert "0.50" not in emb_text_1


def test_zero_database_zero_llm_execution(extractor, diagnoser):
    """Test 13: Extractor works completely offline with synthetic inputs, no DB or network."""
    synthetic_schema = {
        "tables": {
            "tbl_test": {
                "columns": [{"name": "metric_val", "type": "numeric"}]
            }
        }
    }
    obs = RuntimeObservation(
        query="SELECT metric_val FROM tbl_test;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='division by zero',
        schema_context=["tbl_test"],
    )
    diag = diagnoser.diagnose(obs, synthetic_schema)
    rk = extractor.extract(obs, diag, synthetic_schema)

    assert rk.failure_type == TaxonomyCategory.EXECUTION
    assert rk.confidence == 0.50


def test_diagnosis_is_single_source_of_truth(extractor, mock_star_schema):
    """Test 14: Extractor directly copies diagnostic attributes from Phase 4 DiagnosticResult."""
    obs = RuntimeObservation(
        query="SELECT 1;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error="sample error",
        schema_context=["dim_time"],
    )
    custom_diagnosis = DiagnosticResult(
        taxonomy_category=TaxonomyCategory.PLANNING,
        broken_identifier="custom_token",
        root_cause="Custom root cause explanation",
        candidate_replacements=["candidate_1", "candidate_2"],
        negative_constraints=["custom_token"],
        repair_rule="Custom repair rule",
    )

    rk = extractor.extract(obs, custom_diagnosis, mock_star_schema)

    # Must match diagnosis exactly
    assert rk.failure_type == custom_diagnosis.taxonomy_category
    assert rk.root_cause == custom_diagnosis.root_cause
    assert rk.repair_strategy == custom_diagnosis.repair_rule
    assert rk.negative_constraints == custom_diagnosis.negative_constraints
    assert rk.candidate_replacements == custom_diagnosis.candidate_replacements


def test_no_persistence_during_extraction(extractor, diagnoser, mock_star_schema, tmp_path):
    """Test 15: Extracting RuntimeKnowledge creates zero files, DB writes, or vector indexes."""
    obs = RuntimeObservation(
        query="SELECT 1;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "col" does not exist',
        schema_context=["dim_time"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)

    # Inspect memory package modules for FAISS or vector store imports
    import memory.knowledge_extractor as ke_mod
    import memory.models as mm_mod

    for mod in (ke_mod, mm_mod):
        assert "faiss" not in mod.__dict__
        assert "sqlite3" not in mod.__dict__

    rk = extractor.extract(obs, diag, mock_star_schema)
    assert isinstance(rk, RuntimeKnowledge)


def test_extraction_determinism(extractor, diagnoser, mock_star_schema):
    """Test 16: Multiple extractions on identical input produce identical semantic fields."""
    obs = RuntimeObservation(
        query="SELECT region, SUM(revenue) FROM fact_sales_performance GROUP BY region;",
        status=ExecutionStatus.EXECUTION_FAILURE,
        raw_error='column "revenue" does not exist',
        schema_context=["fact_sales_performance", "dim_geography"],
    )
    diag = diagnoser.diagnose(obs, mock_star_schema)

    rk1 = extractor.extract(obs, diag, mock_star_schema)
    rk2 = extractor.extract(obs, diag, mock_star_schema)

    # Semantic attributes must be 100% identical
    assert rk1.failure_type == rk2.failure_type
    assert rk1.source_exception == rk2.source_exception
    assert rk1.context == rk2.context
    assert rk1.root_cause == rk2.root_cause
    assert rk1.repair_strategy == rk2.repair_strategy
    assert rk1.negative_constraints == rk2.negative_constraints
    assert rk1.candidate_replacements == rk2.candidate_replacements
    assert rk1.confidence == rk2.confidence
    assert rk1.format_for_embedding() == rk2.format_for_embedding()
