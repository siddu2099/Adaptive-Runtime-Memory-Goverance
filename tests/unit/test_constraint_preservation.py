"""
Unit tests for ARMG Explicit User Constraint Preservation and Governed Memory Protection.

Verifies:
1. Exact Forbidden Table Substitution:
   - Initial candidate references exact requested table ('fact_sales_performance_archive').
   - Database returns relation-not-found error.
   - Proposed repair switches to prohibited table ('fact_sales_performance').
   - Constraint validator rejects repair candidate before executor invocation (0 database calls on repair).
   - Terminal status is FAILED with EXPLICIT_CONSTRAINT_VIOLATION (NOT SUCCESS or SUCCESS REPAIRED).
   - Memory admission is CONSTRAINT_VIOLATION_NOT_ADMITTED (zero admission, zero positive reinforcement).
2. Preservation of Legitimate Repair:
   - Unconstrained queries permitting schema correction successfully repair and admit operational memory.
3. Constraint and Memory Consistency:
   - Negated/explicit constraints survive diagnosis and repair.
   - Incompatible prior repair memories are excluded from retrieval for constrained queries.
   - Contradictory repairs cannot reinforce incompatible prior rules.
4. Authorized Governance Quarantine:
   - Quarantine transition explicitly archives invalid memories, permanently excluding them from retrieval.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pytest

from agents.error_diagnosis import DeterministicErrorDiagnoser, DiagnosticResult
from agents.repair_agent import RepairSQLGenerator
from agents.sql_generator import GenerationResult, SQLGenerator
from agents.taxonomy import TaxonomyCategory
from environment.base import ExecutionResult
from graph.state import (
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeKnowledge, RuntimeMemory
from memory.vector_store import FAISSMemoryStore
from validation.constraint_validator import ConstraintValidator, ExplicitConstraints


# =====================================================================
# Fixtures & Test Doubles
# =====================================================================

class ConstrainedMockEnvironment:
    """Mock database environment with realistic PostgreSQL relation errors."""

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
                "dim_time": {
                    "columns": [
                        {"name": "time_key", "type": "integer", "is_pk": True},
                        {"name": "year", "type": "integer", "is_pk": False},
                    ]
                },
            }
        }
        self.executed_queries: List[str] = []

    def inspect(self) -> Dict[str, Any]:
        return self.catalog

    def execute(self, payload: str) -> ExecutionResult:
        self.executed_queries.append(payload)
        payload_lower = payload.lower()

        # Simulate missing table error for archive table
        if "fact_sales_performance_archive" in payload_lower:
            return ExecutionResult(
                status="FAILURE",
                query=payload,
                error='relation "fact_sales_performance_archive" does not exist\nLINE 1: SELECT * FROM fact_sales_performance_archive;\n                      ^',
                execution_time_ms=2.1,
            )

        # Simulate missing table error for unconstrained typo table
        if "fact_sales" in payload_lower and "fact_sales_performance" not in payload_lower:
            return ExecutionResult(
                status="FAILURE",
                query=payload,
                error='relation "fact_sales" does not exist\nLINE 1: SELECT * FROM fact_sales;\n                      ^',
                execution_time_ms=1.8,
            )

        # Successful execution for schema-valid table
        if "fact_sales_performance" in payload_lower:
            return ExecutionResult(
                status="SUCCESS",
                query=payload,
                rows=[(1, 5000.0, 1200.0)],
                error=None,
                execution_time_ms=3.4,
                row_count=1,
            )

        return ExecutionResult(
            status="FAILURE",
            query=payload,
            error='syntax error at or near "UNKNOWN"',
            execution_time_ms=1.0,
        )


def deterministic_embed_fn(text: str) -> List[float]:
    """Deterministic normalized 768-dim mock vector."""
    rng = np.random.RandomState(abs(hash(text)) % (2**31))
    vec = rng.randn(768).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


# =====================================================================
# Test Suite 1: Exact Forbidden Table Substitution
# =====================================================================

class TestExactForbiddenTableSubstitution:
    """Requirement 5.A: Exact forbidden table substitution must be blocked before execution."""

    EXACT_ORIGINAL_REQUEST = (
        "Query the table named fact_sales_performance_archive and retrieve its gross_revenue "
        "column for every transaction. Use fact_sales_performance_archive as the exact source "
        "table name. Do not substitute fact_sales_performance, do not select from another table, "
        "and do not rename or alias a different table as this table."
    )

    def test_exact_original_request_constraint_extraction(self):
        """Pass the exact original natural-language request through constraint extraction
        and assert that the required relation is fact_sales_performance_archive and that
        table substitution is prohibited.
        """
        cv = ConstraintValidator()
        c = cv.extract_constraints(self.EXACT_ORIGINAL_REQUEST)

        assert "fact_sales_performance_archive" in c.required_tables
        assert c.required_tables == ["fact_sales_performance_archive"]
        assert "fact_sales_performance" in c.prohibited_tables
        assert c.allow_table_substitution is False

    def test_exact_original_request_workflow_rejection_of_fact_sales_performance(self):
        """Using the exact original request:
        1. Initial SQL candidate referencing fact_sales_performance_archive passes constraint check.
        2. Database reports relation-not-found error.
        3. Repair candidate referencing fact_sales_performance is rejected before a second database call.
        4. Status is FAILED (NOT SUCCESS or SUCCESS REPAIRED), and zero memory is admitted.
        """
        env = ConstrainedMockEnvironment()
        cv = ConstraintValidator()

        # Step 1: Initial query validation
        initial_sql = "SELECT gross_revenue FROM fact_sales_performance_archive;"
        constraints = cv.extract_constraints(self.EXACT_ORIGINAL_REQUEST)
        ok_initial, err_initial = cv.validate_sql(initial_sql, constraints, is_repair=False)
        assert ok_initial is True
        assert err_initial is None

        # Step 2 & 3: Workflow execution with failing initial query and violating repair
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{initial_sql}\n```",
            extracted_sql=initial_sql,
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT gross_revenue FROM fact_sales_performance;\n```",
                extracted_sql="SELECT gross_revenue FROM fact_sales_performance;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": self.EXACT_ORIGINAL_REQUEST, "max_retries": 3})

        # Assertions
        assert result["status"] == STATUS_FAILED
        assert result["status"] != STATUS_SUCCESS
        assert result["decision_source"] == "constraint_validator"
        assert result["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"

        # Exactly 1 database call (the initial attempt); 0 database calls on repair
        assert len(env.executed_queries) == 1
        assert "fact_sales_performance_archive" in env.executed_queries[0]
        assert not any("fact_sales_performance;" in q for q in env.executed_queries)

        # Zero memory admission and zero positive reinforcement
        assert vector_store.count() == 0
        assert result.get("telemetry", {}).get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"

    def test_exact_original_request_workflow_rejection_of_dim_geography(self):
        """Using the exact original request:
        Verify that a repair substituting dim_geography is also rejected before database execution.
        """
        env = ConstrainedMockEnvironment()

        initial_sql = "SELECT gross_revenue FROM fact_sales_performance_archive;"
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{initial_sql}\n```",
            extracted_sql=initial_sql,
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM dim_geography;\n```",
                extracted_sql="SELECT * FROM dim_geography;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": self.EXACT_ORIGINAL_REQUEST, "max_retries": 3})

        # Assertions
        assert result["status"] == STATUS_FAILED
        assert result["status"] != STATUS_SUCCESS
        assert result["decision_source"] == "constraint_validator"
        assert result["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"

        # Exactly 1 database call (the initial attempt); 0 on dim_geography
        assert len(env.executed_queries) == 1
        assert "fact_sales_performance_archive" in env.executed_queries[0]
        assert not any("dim_geography" in q for q in env.executed_queries)

        # Zero memory admission
        assert vector_store.count() == 0
        assert result.get("telemetry", {}).get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"

    def test_reproduced_relation_substitution_blocked_before_execution(self):
        """Verify that substituting fact_sales_performance for fact_sales_performance_archive
        is rejected by the constraint validator before PostgreSQL execution.
        """
        env = ConstrainedMockEnvironment()

        user_query = (
            "Query the exact table fact_sales_performance_archive. "
            "Do not substitute with fact_sales_performance or any other table."
        )

        # 1. Initial generator faithfully references the exact requested table
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT * FROM fact_sales_performance_archive;\n```",
            extracted_sql="SELECT * FROM fact_sales_performance_archive;",
        )

        # 2. Repair generator attempts to substitute the prohibited table 'fact_sales_performance'
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM fact_sales_performance;\n```",
                extracted_sql="SELECT * FROM fact_sales_performance;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": user_query, "max_retries": 3})

        # --- Assertions ---
        # 1. Terminal outcome must be FAILED, NOT SUCCESS or SUCCESS (REPAIRED)
        assert result["status"] == STATUS_FAILED
        assert result["decision_source"] == "constraint_validator"
        assert result["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"

        # 2. Candidate that violates constraint must NEVER be executed against database
        # Exactly 1 query executed: the initial candidate on fact_sales_performance_archive
        assert len(env.executed_queries) == 1
        assert "fact_sales_performance_archive" in env.executed_queries[0]
        # The repair query on fact_sales_performance was NEVER passed to PostgreSQL executor
        assert not any("fact_sales_performance;" in q for q in env.executed_queries)

        # 3. Constraint violation recorded accurately in telemetry and attempts trace
        telemetry = result.get("telemetry", {})
        assert telemetry.get("terminal_reason") == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert telemetry.get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"
        assert result.get("is_constraint_violation") is True
        assert "fact_sales_performance" in result.get("violated_constraint", "")

        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 2
        # First attempt: executed and failed in DB
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert "does not exist" in attempts[0]["exec_error"]
        # Second attempt (repair): rejected by constraint validator, NOT executed in DB
        assert attempts[1]["is_repair"] is True
        assert attempts[1]["is_constraint_violation"] is True
        assert attempts[1]["ast_valid"] is False
        assert attempts[1].get("executed_in_db") is not True

        # 4. Zero memory admitted to vector store
        assert vector_store.count() == 0

    def test_reproduced_relation_substitution_with_dim_geography_blocked_before_execution(self):
        """Verify that substituting an alternative table like dim_geography when all
        substitution is prohibited is rejected before database execution.
        """
        env = ConstrainedMockEnvironment()

        user_query = (
            "Query the exact table fact_sales_performance_archive. "
            "Do not substitute with fact_sales_performance or any other table."
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT * FROM fact_sales_performance_archive;\n```",
            extracted_sql="SELECT * FROM fact_sales_performance_archive;",
        )

        # Repair generator attempts to substitute alternative table 'dim_geography'
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM dim_geography;\n```",
                extracted_sql="SELECT * FROM dim_geography;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": user_query, "max_retries": 3})

        # 1. Terminal outcome must be FAILED with EXPLICIT_CONSTRAINT_VIOLATION
        assert result["status"] == STATUS_FAILED
        assert result["decision_source"] == "constraint_validator"
        assert result["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"

        # 2. Database must NOT have been called with dim_geography
        assert len(env.executed_queries) == 1
        assert "fact_sales_performance_archive" in env.executed_queries[0]
        assert not any("dim_geography" in q for q in env.executed_queries)

        # 3. Telemetry and zero memory admission
        telemetry = result.get("telemetry", {})
        assert telemetry.get("terminal_reason") == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert telemetry.get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"
        assert result.get("is_constraint_violation") is True
        assert vector_store.count() == 0

    def test_initial_query_passes_constraint_check_fails_in_db_and_blocks_violating_repair_without_second_executor_call(self):
        """Confirm that:
        1. Original requested table passes initial constraint check.
        2. Database reports that the table does not exist.
        3. Violating repair is rejected without a second database executor call.
        4. Final status is NOT SUCCESS or SUCCESS (REPAIRED).
        5. Zero successful memory admitted.
        """
        env = ConstrainedMockEnvironment()
        cv = ConstraintValidator()

        user_query = (
            "Query the exact table fact_sales_performance_archive. "
            "Do not substitute with fact_sales_performance or any other table."
        )
        constraints = cv.extract_constraints(user_query)

        # Step 1: Initial query passes constraint validation
        initial_sql = "SELECT * FROM fact_sales_performance_archive;"
        is_valid_initial, err_initial = cv.validate_sql(initial_sql, constraints, is_repair=False)
        assert is_valid_initial is True
        assert err_initial is None

        # Step 2 & 3: Run full workflow with failing initial execution and violating repair
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{initial_sql}\n```",
            extracted_sql=initial_sql,
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM fact_sales_performance;\n```",
                extracted_sql="SELECT * FROM fact_sales_performance;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": user_query, "max_retries": 3})

        # Step 4: Final status must NOT be SUCCESS or SUCCESS (REPAIRED)
        assert result["status"] == STATUS_FAILED
        assert result["status"] != STATUS_SUCCESS
        assert result.get("decision_source") == "constraint_validator"
        assert result.get("block_reason") == "EXPLICIT_CONSTRAINT_VIOLATION"

        # Step 5: Exactly 1 database executor call (no second call for repair)
        assert len(env.executed_queries) == 1
        assert "fact_sales_performance_archive" in env.executed_queries[0]
        assert not any("fact_sales_performance;" in q for q in env.executed_queries)

        # Step 6: Zero memory admitted
        assert vector_store.count() == 0
        assert result.get("telemetry", {}).get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"

    def test_direct_constraint_validator_rejection(self):
        """Unit test for ConstraintValidator extraction and rejection contract."""
        cv = ConstraintValidator()
        query = (
            "Query the exact table fact_sales_performance_archive. "
            "Do not substitute fact_sales_performance or any other table."
        )
        constraints = cv.extract_constraints(query)

        assert constraints.has_constraints() is True
        assert "fact_sales_performance_archive" in constraints.required_tables
        assert "fact_sales_performance" in constraints.prohibited_tables
        assert constraints.allow_table_substitution is False

        # Initial query referencing requested table passes
        ok_initial, err_initial = cv.validate_sql(
            "SELECT * FROM fact_sales_performance_archive;", constraints, is_repair=False
        )
        assert ok_initial is True
        assert err_initial is None

        # Repaired query referencing prohibited table fails
        ok_repair, err_repair = cv.validate_sql(
            "SELECT * FROM fact_sales_performance;", constraints, is_repair=True
        )
        assert ok_repair is False
        assert "fact_sales_performance" in err_repair
        assert "prohibited" in err_repair

        # Repaired query referencing dim_geography fails due to substitution prohibition
        ok_geo, err_geo = cv.validate_sql(
            "SELECT * FROM dim_geography;", constraints, is_repair=True
        )
        assert ok_geo is False
        assert "violating explicit constraint prohibiting substitution" in err_geo

        # Repaired query referencing dim_time also fails due to substitution prohibition
        ok_time, err_time = cv.validate_sql(
            "SELECT * FROM dim_time;", constraints, is_repair=True
        )
        assert ok_time is False
        assert "violating explicit constraint prohibiting substitution" in err_time


# =====================================================================
# Test Suite 2: Preservation of Legitimate Repair
# =====================================================================

class TestPreserveLegitimateRepair:
    """Requirement 5.B: Legitimate repairs must remain allowed when no explicit prohibition exists."""

    def test_unconstrained_relation_repair_succeeds_and_admits_memory(self):
        """Verify that when a user does NOT prohibit substitution, a repair from
        an erroneous relation identifier to a schema-valid table proceeds normally.
        """
        env = ConstrainedMockEnvironment()

        unconstrained_query = "What is the total sales revenue from fact_sales?"

        # Initial generator references typo table 'fact_sales'
        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response="```sql\nSELECT * FROM fact_sales;\n```",
            extracted_sql="SELECT * FROM fact_sales;",
        )

        # Repair generator substitutes schema-valid 'fact_sales_performance'
        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response="```sql\nSELECT * FROM fact_sales_performance;\n```",
                extracted_sql="SELECT * FROM fact_sales_performance;",
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        result = graph.invoke({"user_query": unconstrained_query, "max_retries": 3})

        # --- Assertions ---
        # 1. Normal legitimate repair succeeds
        assert result["status"] == STATUS_SUCCESS
        assert result["retry_count"] == 1
        assert "fact_sales_performance" in result["generated_sql"]

        # 2. Both candidates executed against database (1 failure, 1 success)
        assert len(env.executed_queries) == 2
        assert "fact_sales" in env.executed_queries[0]
        assert "fact_sales_performance" in env.executed_queries[1]

        # 3. Operational memory successfully admitted under existing governance rules
        telemetry = result.get("telemetry", {})
        assert telemetry.get("memory_admission") == "ADMITTED"
        assert vector_store.count() == 1


# =====================================================================
# Test Suite 3: Constraint and Memory Consistency
# =====================================================================

class TestConstraintAndMemoryConsistency:
    """Requirement 5.C: Constraint and memory consistency."""

    def test_negative_constraints_propagate_into_diagnosis(self):
        """Verify that explicit negative constraints survive into DiagnosticResult."""
        diagnoser = DeterministicErrorDiagnoser()
        obs_error = 'relation "fact_sales_performance_archive" does not exist'
        from environment.observation import ExecutionStatus, RuntimeObservation
        obs = RuntimeObservation(
            query="SELECT * FROM fact_sales_performance_archive;",
            status=ExecutionStatus.EXECUTION_FAILURE,
            raw_error=obs_error,
            normalized_error=obs_error,
        )

        catalog = {
            "tables": {
                "fact_sales_performance": {"columns": []},
            }
        }

        cv = ConstraintValidator()
        constraints = cv.extract_constraints(
            "Query exact table fact_sales_performance_archive. Do not substitute fact_sales_performance."
        )

        diag = diagnoser.diagnose(obs, catalog, explicit_constraints=constraints)

        # Prohibited table must NOT be offered as a candidate replacement
        assert "fact_sales_performance" not in diag.candidate_replacements
        # Prohibited table must be included in negative constraints
        assert "fact_sales_performance" in diag.negative_constraints
        # Repair rule must explicitly acknowledge substitution prohibition
        assert "prohibited" in diag.repair_rule.lower()

    def test_incompatible_memory_excluded_from_retrieval(self):
        """Verify that a memory containing a rule that contradicts query constraints is NOT retrieved."""
        vector_store = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        # Seed vector store with the problematic rule from the reproduced incident
        incompatible_mem = RuntimeMemory(
            memory_id="mem-60757101",
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced relation 'fact_sales_performance_archive' does not exist in the active schema.",
            repair_strategy="Replace the invalid relation identifier with a schema-valid table.",
            negative_constraints=["fact_sales_performance_archive"],
            candidate_replacements=["fact_sales_performance"],
            confidence=0.55,
            utility=0.28,
            context={"tables_referenced": ["fact_sales_performance_archive"]},
            status=MemoryState.ACTIVE,
        )
        vec = deterministic_embed_fn("relation fact_sales_performance_archive does not exist")
        vector_store.add(incompatible_mem, vec)

        env = ConstrainedMockEnvironment()
        wf = ARMGRepairWorkflow(
            environment=env,
            vector_store=vector_store,
            governance_engine=gov_engine,
            embed_fn=lambda text: vec,  # Force match
        )

        # A: Query with explicit prohibition of table substitution
        state_constrained = {
            "user_query": "Query exact table fact_sales_performance_archive. Do not substitute another table.",
            "explicit_constraints": ConstraintValidator().extract_constraints(
                "Query exact table fact_sales_performance_archive. Do not substitute another table."
            ),
            "telemetry": {},
        }
        retrieval_res = wf.memory_retrieval_node(state_constrained)
        # Memory recommending relation substitution must be excluded from retrieved memories
        assert len(retrieval_res["retrieved_memories"]) == 0

        # B: Query without substitution prohibition
        state_unconstrained = {
            "user_query": "What is the total revenue in fact_sales_performance_archive?",
            "explicit_constraints": ExplicitConstraints(),
            "telemetry": {},
        }
        retrieval_res_unconstrained = wf.memory_retrieval_node(state_unconstrained)
        # When unconstrained, the memory is retrievable normally
        assert len(retrieval_res_unconstrained["retrieved_memories"]) == 1
        assert retrieval_res_unconstrained["retrieved_memories"][0].memory_id == "mem-60757101"

    def test_contradictory_repair_cannot_reinforce_prior_memory(self):
        """Verify that an attempt violating explicit constraints cannot apply positive reinforcement."""
        vector_store = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        vec = deterministic_embed_fn("prior rule")
        prior_mem = RuntimeMemory(
            memory_id="mem-test-prior",
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Relation error",
            repair_strategy="Substitute table",
            confidence=0.50,
            utility=0.25,
            context={},
            status=MemoryState.ACTIVE,
            successful_uses=1,
            total_uses=1,
            embedding=vec,
        )
        vector_store.add(prior_mem, vec)

        env = ConstrainedMockEnvironment()
        wf = ARMGRepairWorkflow(
            environment=env,
            vector_store=vector_store,
            governance_engine=gov_engine,
            embed_fn=deterministic_embed_fn,
        )

        # State representing a terminal constraint violation where prior memory was candidate
        state_violation = {
            "status": STATUS_FAILED,
            "applied_memory_id": "mem-test-prior",
            "is_constraint_violation": True,
            "violated_constraint": "Referenced prohibited table",
            "telemetry": {"terminal_reason": "EXPLICIT_CONSTRAINT_VIOLATION"},
        }

        gov_res = wf.memory_governance_node(state_violation)
        assert gov_res["telemetry"]["memory_admission"] == "CONSTRAINT_VIOLATION_NOT_ADMITTED"

        # The prior memory must NOT have gained a successful use; it was penalized on failure
        updated_mem = vector_store.get("mem-test-prior")
        assert updated_mem.successful_uses == 1  # Unchanged, NOT incremented
        assert updated_mem.total_uses == 2       # Incremented on failure penalty
        assert updated_mem.confidence < 0.50     # Confidence penalized


# =====================================================================
# Test Suite 4: Authorized Governance Quarantine
# =====================================================================

class TestAuthorizedGovernanceQuarantine:
    """Requirement 6: Verify memory inspection and safe governance transition."""

    def test_quarantine_memory_by_id_transitions_to_archived(self):
        """Verify that quarantine_memory_by_id transitions target memory to ARCHIVED state."""
        vector_store = FAISSMemoryStore()
        gov_engine = MemoryGovernanceEngine()

        # Seed target memory
        mem = RuntimeMemory(
            memory_id="mem-60757101",
            failure_type=TaxonomyCategory.SEMANTIC,
            root_cause="Referenced relation does not exist",
            repair_strategy="Replace with schema-valid table",
            confidence=0.50,
            utility=0.25,
            context={},
            status=MemoryState.ACTIVE,
        )
        vec = deterministic_embed_fn("rule text")
        vector_store.add(mem, vec)

        env = ConstrainedMockEnvironment()
        wf = ARMGRepairWorkflow(
            environment=env,
            vector_store=vector_store,
            governance_engine=gov_engine,
            embed_fn=deterministic_embed_fn,
        )

        # Verify initial active state
        assert vector_store.get("mem-60757101").status == MemoryState.ACTIVE

        # Quarantine memory
        archived = wf.quarantine_memory_by_id("mem-60757101", reason="Violates explicit user constraints")
        assert archived is not None
        assert archived.status == MemoryState.ARCHIVED

        # Verify updated in vector store
        store_mem = vector_store.get("mem-60757101")
        assert store_mem.status == MemoryState.ARCHIVED

        # Verify that ARCHIVED memories are excluded from search results
        results = vector_store.search(vec, top_k=5)
        # Search filters out deleted, but let's verify retrieval node excludes ARCHIVED
        state = {
            "user_query": "Any query",
            "explicit_constraints": ExplicitConstraints(),
            "telemetry": {},
        }
        wf.embed_fn = lambda text: vec
        retrieval = wf.memory_retrieval_node(state)
        # mem-60757101 must NOT be in retrieved memories because status is ARCHIVED
        assert not any(m.memory_id == "mem-60757101" for m in retrieval["retrieved_memories"])

    def test_quarantine_nonexistent_memory_returns_none(self):
        """Verify that attempting to quarantine a non-existent memory safely returns None."""
        vector_store = FAISSMemoryStore()
        env = ConstrainedMockEnvironment()
        wf = ARMGRepairWorkflow(
            environment=env,
            vector_store=vector_store,
        )
        res = wf.quarantine_memory_by_id("mem-does-not-exist")
        assert res is None


# =====================================================================
# Test Suite 5: Explicit Output Column Constraints & Projection Validation
# =====================================================================

class TestExplicitOutputColumnConstraints:
    """Requirement Phase B & C: Extraction of explicit output column constraints and projection AST validation."""

    def test_extract_single_output_column(self):
        cv = ConstraintValidator()
        c = cv.extract_constraints(
            "Retrieve the unmapped_metric column from fact_sales_performance for every transaction. "
            "Return the value of this column directly."
        )
        assert c.required_columns == ["unmapped_metric"]

    def test_extract_multiple_output_columns(self):
        cv = ConstraintValidator()
        c1 = cv.extract_constraints(
            "Select the fact_key and gross_revenue columns and return them for every transaction."
        )
        assert c1.required_columns == ["fact_key", "gross_revenue"]

        c2 = cv.extract_constraints("Display the requested columns fact_key and net_profit.")
        assert c2.required_columns == ["fact_key", "net_profit"]

    def test_extract_column_named_directly(self):
        cv = ConstraintValidator()
        c = cv.extract_constraints("Return the value of the column named unmapped_metric directly.")
        assert c.required_columns == ["unmapped_metric"]

    def test_negative_extractions_do_not_produce_output_columns(self):
        cv = ConstraintValidator()
        # Conceptual metric
        assert cv.extract_constraints("Calculate total revenue by region.").required_columns == []
        # Aggregation totals
        assert cv.extract_constraints("Show the total sales revenue and total net profit across all transactions.").required_columns == []
        # Source column in expression
        assert cv.extract_constraints("Calculate regional totals using the column named revenue and group the results by region.").required_columns == []
        # Filter condition
        assert cv.extract_constraints("Filter transactions where gross_revenue is greater than zero.").required_columns == []
        # Join condition
        assert cv.extract_constraints("Join the sales table to the geography table using geo_key.").required_columns == []
        # Test 8 regional revenue query
        test8_query = (
            "Calculate total revenue by region using the column named revenue, and group the results by region. "
            "If that column is invalid, use the database error to correct the query and return the regional revenue totals."
        )
        assert cv.extract_constraints(test8_query).required_columns == []

    def test_projection_validation_passes_when_column_present(self):
        cv = ConstraintValidator()
        c = ExplicitConstraints(required_columns=["unmapped_metric"])
        # Direct column
        ok, err = cv.validate_sql("SELECT unmapped_metric FROM fact_sales_performance;", c)
        assert ok is True
        assert err is None

        # Qualified column
        ok, err = cv.validate_sql("SELECT f.unmapped_metric FROM fact_sales_performance AS f;", c)
        assert ok is True
        assert err is None

        # Aliased column
        ok, err = cv.validate_sql("SELECT f.unmapped_metric AS m FROM fact_sales_performance AS f;", c)
        assert ok is True
        assert err is None

    def test_projection_validation_rejects_column_in_where_only_test4a(self):
        """Test 4A validation check: required column in WHERE but omitted from projection."""
        cv = ConstraintValidator()
        c = ExplicitConstraints(required_columns=["unmapped_metric"])
        sql = (
            "SELECT fact_key, gross_revenue, discount_applied, net_profit "
            "FROM fact_sales_performance "
            "WHERE unmapped_metric IS NOT NULL;"
        )
        ok, err = cv.validate_sql(sql, c)
        assert ok is False
        assert "Required output column 'unmapped_metric' was omitted from the SQL result projection." in err

    def test_projection_validation_rejects_wildcard(self):
        """Wildcard cannot prove that a specific required column is present."""
        cv = ConstraintValidator()
        c = ExplicitConstraints(required_columns=["unmapped_metric"])
        ok, err = cv.validate_sql("SELECT * FROM fact_sales_performance;", c)
        assert ok is False
        assert "cannot be verified from wildcard projection" in err

    def test_projection_preserves_valid_aggregations_and_aliases(self):
        cv = ConstraintValidator()
        # Aggregation with alias matching required column
        c1 = ExplicitConstraints(required_columns=["revenue"])
        sql1 = (
            "SELECT d.region, SUM(f.gross_revenue) AS revenue "
            "FROM fact_sales_performance AS f "
            "JOIN dim_geography AS d ON f.geo_key = d.geo_key "
            "GROUP BY d.region;"
        )
        ok1, err1 = cv.validate_sql(sql1, c1)
        assert ok1 is True
        assert err1 is None

        # Underlying source column represented inside aggregation
        c2 = ExplicitConstraints(required_columns=["gross_revenue"])
        ok2, err2 = cv.validate_sql(sql1, c2)
        assert ok2 is True
        assert err2 is None


# =====================================================================
# Test Suite 6: Test 4A and Test 8 Workflow Verification
# =====================================================================

class TestSemanticValidationWorkflowClosure:
    """Verifies end-to-end workflow behavior for Test 4A and Test 8."""

    def test_test4a_missing_output_column_rejected_before_database_execution(self):
        """Test 4A:
        Request explicitly demands 'unmapped_metric' column value directly.
        Scripted candidate only references it in WHERE clause while projecting other columns.
        Expected:
        - Rejected before PostgreSQL executor (0 DB calls).
        - Terminal status FAILED with EXPLICIT_CONSTRAINT_VIOLATION.
        - 0 repair retries attempted.
        - Memory admission is CONSTRAINT_VIOLATION_NOT_ADMITTED (0 FAISS additions).
        """
        env = ConstrainedMockEnvironment()
        user_query = (
            "Retrieve the unmapped_metric column from fact_sales_performance for every transaction. "
            "Return the value of this column directly, rather than counting transactions with missing foreign keys."
        )
        scripted_sql = (
            "SELECT fact_key, gross_revenue, discount_applied, net_profit\n"
            "FROM fact_sales_performance\n"
            "WHERE unmapped_metric IS NOT NULL;"
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{scripted_sql}\n```",
            extracted_sql=scripted_sql,
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 3})

        # 1. Terminal status FAILED with constraint validator decision source
        assert res["status"] == STATUS_FAILED
        assert res["decision_source"] == "constraint_validator"
        assert res["block_reason"] == "EXPLICIT_CONSTRAINT_VIOLATION"
        assert res.get("is_constraint_violation") is True
        assert "unmapped_metric" in res.get("violated_constraint", "")

        # 2. Zero database executions (candidate rejected before executor)
        assert len(env.executed_queries) == 0
        telemetry = res.get("telemetry", {})
        assert telemetry.get("postgres_executor_calls") == 0

        # 3. Zero repair retries attempted
        assert res.get("retry_count", 0) == 0
        assert telemetry.get("repair_count", 0) == 0

        # 4. Memory admission rejected
        assert telemetry.get("memory_admission") == "CONSTRAINT_VIOLATION_NOT_ADMITTED"
        assert vector_store.count() == 0

    def test_test8_regional_revenue_aggregation_repair_workflow(self):
        """Test 8:
        Request: Calculate total revenue by region using column named revenue...
        Initial candidate uses SUM(f.revenue) AS revenue, failing in DB with undefined-column.
        Repaired candidate corrects measure to SUM(f.gross_revenue) AS revenue, succeeding in DB.
        Expected:
        - Initial query passes AST constraint validation (revenue is not extracted as an output constraint).
        - Initial query executes in DB and fails.
        - Repaired query executes in DB and succeeds.
        - Final status is SUCCESS with retry_count == 1 and 2 DB calls.
        - Valid operational memory admitted.
        """
        env = ConstrainedMockEnvironment()
        env.catalog["tables"]["dim_geography"] = {
            "columns": [
                {"name": "geo_key", "type": "integer", "is_pk": True},
                {"name": "region", "type": "varchar", "is_pk": False},
            ]
        }

        initial_sql = (
            "SELECT d.region, SUM(f.revenue) AS revenue\n"
            "FROM fact_sales_performance AS f\n"
            "JOIN dim_geography AS d ON f.geo_key = d.geo_key\n"
            "GROUP BY d.region;"
        )
        repaired_sql = (
            "SELECT d.region, SUM(f.gross_revenue) AS revenue\n"
            "FROM fact_sales_performance AS f\n"
            "JOIN dim_geography AS d ON f.geo_key = d.geo_key\n"
            "GROUP BY d.region;"
        )

        def mock_execute(payload: str) -> ExecutionResult:
            env.executed_queries.append(payload)
            if "f.revenue" in payload:
                return ExecutionResult(
                    status="FAILURE",
                    query=payload,
                    error='column f.revenue does not exist\nLINE 1: SELECT d.region, SUM(f.revenue) AS revenue...',
                    execution_time_ms=2.0,
                )
            return ExecutionResult(
                status="SUCCESS",
                query=payload,
                rows=[("APAC", 7840368.09), ("EMEA", 7389784.84), ("North America", 7481213.85)],
                error=None,
                execution_time_ms=3.5,
                row_count=3,
            )

        env.execute = mock_execute

        user_query = (
            "Calculate total revenue by region using the column named revenue, and group the results by region. "
            "If that column is invalid, use the database error to correct the query and return the regional revenue totals."
        )

        mock_gen = SQLGenerator()
        mock_gen.generate = lambda question, schema_markdown, **kw: GenerationResult(
            raw_response=f"```sql\n{initial_sql}\n```",
            extracted_sql=initial_sql,
        )

        mock_repair = RepairSQLGenerator(
            generator_fn=lambda prompt: GenerationResult(
                raw_response=f"```sql\n{repaired_sql}\n```",
                extracted_sql=repaired_sql,
            )
        )

        vector_store = FAISSMemoryStore()
        wf = ARMGRepairWorkflow(
            environment=env,
            sql_generator=mock_gen,
            repair_generator=mock_repair,
            vector_store=vector_store,
            embed_fn=deterministic_embed_fn,
        )
        graph = wf.build_graph()

        res = graph.invoke({"user_query": user_query, "max_retries": 3})

        # 1. Final status is SUCCESS
        assert res["status"] == STATUS_SUCCESS

        # 2. Exactly 2 database executions (1 failure, 1 success)
        assert len(env.executed_queries) == 2
        assert "revenue" in env.executed_queries[0]
        assert "gross_revenue" in env.executed_queries[1]

        # 3. Exactly 1 repair retry
        assert res["retry_count"] == 1
        telemetry = res.get("telemetry", {})
        assert telemetry.get("repair_count") == 1
        assert telemetry.get("postgres_executor_calls") == 2

        # 4. Traces confirm undefined-column initial failure and successful repaired execution
        attempts = telemetry.get("attempts_trace", [])
        assert len(attempts) == 2
        assert attempts[0]["executed_in_db"] is True
        assert attempts[0]["exec_success"] is False
        assert "column f.revenue does not exist" in attempts[0]["exec_error"]
        assert attempts[1]["executed_in_db"] is True
        assert attempts[1]["exec_success"] is True

        # 5. Governed memory admission
        assert telemetry.get("memory_admission") == "ADMITTED"
        assert vector_store.count() == 1
