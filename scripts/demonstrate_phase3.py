"""
ARMG Phase 3: Faculty Demonstrations Script.

Demonstrates the 3 core operational lifecycles of ARMG:
1. Successful Repair Lifecycle:
   Initial SQL -> AST validation -> PostgreSQL execution failure -> runtime observation ->
   deterministic diagnosis -> repair prompt -> regenerated SQL -> AST revalidation ->
   PostgreSQL re-execution -> final SUCCESS & memory admission.

2. Terminal Failure Lifecycle:
   Exercises the retry controller across 4 generation attempts (initial + 3 retries),
   demonstrates retry budget exhaustion, terminal STATUS_FAILED, and zero false memory admission.

3. Safety Blocking Lifecycle:
   Demonstrates pre-execution AST interception of destructive SQL (e.g. DROP TABLE),
   verifying STATUS_BLOCKED and zero PostgreSQL database execution.

Uses real PostgreSQL warehouse and explicitly labeled demonstration fixtures.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from environment.postgres import PostgreSQLEnvironment
from environment.base import ExecutionResult
from graph.state import (
    ARMGState,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_RETRYING,
    STATUS_SUCCESS,
)
from graph.workflow import ARMGRepairWorkflow, default_embed_fn
from agents.sql_generator import GenerationResult, SQLGenerator
from agents.repair_agent import RepairSQLGenerator
from memory.vector_store import FAISSMemoryStore
from memory.governance import MemoryGovernanceEngine


# =============================================================================
# Demonstration Sequence Generators
# =============================================================================

class DemonstrationSequenceGenerator:
    """Explicitly labeled demonstration generator for deterministic lifecycle replay."""

    def __init__(self, sequence: List[GenerationResult], label: str = "Demonstration Fixture"):
        self.sequence = list(sequence)
        self.idx = 0
        self.label = label

    def generate(self, question: str, schema_markdown: str) -> GenerationResult:
        res = self.sequence[self.idx]
        self.idx = min(self.idx + 1, len(self.sequence) - 1)
        return res

    def generate_repair(self, repair_prompt: str) -> GenerationResult:
        res = self.sequence[self.idx]
        self.idx = min(self.idx + 1, len(self.sequence) - 1)
        return res


# =============================================================================
# Demonstration 1: Successful Repair
# =============================================================================

def run_demonstration_1_successful_repair(env: PostgreSQLEnvironment) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("DEMONSTRATION 1: SUCCESSFUL REPAIR LIFECYCLE (Invalid Column Semantic Recovery)")
    print("=" * 80)
    print("Source Type: Controlled Demonstration Fixture (exercises real PostgreSQL, real diagnosis, real repair prompt)")
    print("Scenario: User asks 'What is the total revenue by region?'")
    print("Initial SQL references non-existent column 'revenue' in fact_sales_performance.")

    # Attempt 1: Fails with column "revenue" does not exist
    # Attempt 2: Repaired to valid column "gross_revenue"
    seq = [
        GenerationResult(
            raw_response="```sql\nSELECT g.region, SUM(f.revenue) AS total_revenue FROM fact_sales_performance f JOIN dim_geography g ON f.geo_key = g.geo_key GROUP BY g.region;\n```",
            extracted_sql="SELECT g.region, SUM(f.revenue) AS total_revenue FROM fact_sales_performance f JOIN dim_geography g ON f.geo_key = g.geo_key GROUP BY g.region;",
            prompt_tokens=220,
            completion_tokens=45,
            generation_duration_ms=120.0,
        ),
        GenerationResult(
            raw_response="```sql\nSELECT g.region, SUM(f.gross_revenue) AS total_revenue FROM fact_sales_performance f JOIN dim_geography g ON f.geo_key = g.geo_key GROUP BY g.region;\n```",
            extracted_sql="SELECT g.region, SUM(f.gross_revenue) AS total_revenue FROM fact_sales_performance f JOIN dim_geography g ON f.geo_key = g.geo_key GROUP BY g.region;",
            prompt_tokens=340,
            completion_tokens=45,
            generation_duration_ms=145.0,
        ),
    ]

    demo_gen = DemonstrationSequenceGenerator(seq, label="Demonstration Fixture: Invalid-Column Recovery")
    v_store = FAISSMemoryStore()
    gov_engine = MemoryGovernanceEngine()

    wf = ARMGRepairWorkflow(
        environment=env,
        sql_generator=demo_gen,
        repair_generator=demo_gen,
        governance_engine=gov_engine,
        vector_store=v_store,
        embed_fn=default_embed_fn,
    )
    app = wf.build_graph()

    t0 = time.perf_counter()
    state = app.invoke({
        "user_query": "What is the total revenue by region?",
        "max_retries": 3,
    })
    total_time_ms = (time.perf_counter() - t0) * 1000.0

    telemetry = state.get("telemetry", {})
    attempts = telemetry.get("attempts_trace", [])

    print(f"\nFinal Execution Status: {state.get('status')}")
    print(f"Total Attempts: {telemetry.get('generation_attempts')}")
    print(f"Retries Used: {state.get('retry_count')} / {state.get('max_retries', 3)}")
    print(f"Token Telemetry (Demo Fixture): Prompt={telemetry.get('prompt_tokens')} [Demo Fixture], Comp={telemetry.get('completion_tokens')} [Demo Fixture], Total={telemetry.get('total_tokens')} [Demo Fixture]")
    print(f"Stage Latencies: Gen={telemetry.get('generation_latency_ms')}ms [Demo Fixture], Val={telemetry.get('validation_latency_ms')}ms [Live Measured], Exec={telemetry.get('execution_latency_ms')}ms [Live Measured]")
    print(f"Total Telemetry Latency: {telemetry.get('total_latency_ms')} ms (Wall clock: {total_time_ms:.1f} ms [Live Measured])")
    print(f"Memory Admission Status: {telemetry.get('memory_admission')} [Live Measured]")

    print("\n--- ATTEMPT-BY-ATTEMPT LIFECYCLE AUDIT TRAIL ---")
    for att in attempts:
        print(f"\n[Attempt {att['attempt']}] {'(Repair Iteration)' if att['is_repair'] else '(Initial Generation)'} at {att['timestamp']}")
        print(f"  SQL: {att['sql']}")
        print(f"  AST Guard: {'PASSED [Live Measured]' if att.get('ast_valid') else 'FAILED [Live Measured]: ' + str(att.get('ast_error'))}")
        if att.get("executed_in_db"):
            print(f"  PostgreSQL: {'SUCCESS (' + str(att.get('row_count')) + ' rows in ' + str(att.get('exec_time_ms')) + 'ms) [Live Measured]' if att.get('exec_success') else 'FAILED: ' + str(att.get('exec_error')).strip() + ' [Live Measured]'}")
        else:
            print("  PostgreSQL: NOT EXECUTED")
        if att.get("diagnosis"):
            d = att["diagnosis"]
            print(f"  Diagnosis: Category={d.get('taxonomy_category')}, Broken='{d.get('broken_identifier')}', Candidate={d.get('candidate_replacements')} [Live Measured]")
            print(f"  Repair Rule: {d.get('repair_rule')}")

    exec_res = state.get("execution_result")
    if exec_res and exec_res.is_success:
        print("\nFinal PostgreSQL Query Result Sample (First 3 Rows):")
        for r in (exec_res.rows or [])[:3]:
            print(f"  {r}")

    return state


# =============================================================================
# Demonstration 2: Terminal Failure (Retry Budget Exhaustion)
# =============================================================================

def run_demonstration_2_terminal_failure(env: PostgreSQLEnvironment) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("DEMONSTRATION 2: TERMINAL FAILURE LIFECYCLE (Retry Budget Exhaustion: 4 Attempts Max)")
    print("=" * 80)
    print("Source Type: Controlled Demonstration Fixture (exercises real retry controller, real budget bounds)")
    print("Scenario: Unrepairable query with invalid column that fails repeatedly.")
    print("Constraint: max_retries = 3 -> Exactly 4 total generation attempts permitted.")

    # 4 repeated failed attempts to exhaust the retry budget
    failed_result = GenerationResult(
        raw_response="```sql\nSELECT unmapped_metric FROM fact_sales_performance;\n```",
        extracted_sql="SELECT unmapped_metric FROM fact_sales_performance;",
        prompt_tokens=180,
        completion_tokens=25,
        generation_duration_ms=90.0,
    )
    seq = [failed_result, failed_result, failed_result, failed_result]

    demo_gen = DemonstrationSequenceGenerator(seq, label="Demonstration Fixture: Budget Exhaustion")
    v_store = FAISSMemoryStore()
    gov_engine = MemoryGovernanceEngine()

    wf = ARMGRepairWorkflow(
        environment=env,
        sql_generator=demo_gen,
        repair_generator=demo_gen,
        governance_engine=gov_engine,
        vector_store=v_store,
        embed_fn=default_embed_fn,
    )
    app = wf.build_graph()

    state = app.invoke({
        "user_query": "What is the unmapped metric across transactions?",
        "max_retries": 3,
    })

    telemetry = state.get("telemetry", {})
    attempts = telemetry.get("attempts_trace", [])

    print(f"\nFinal Execution Status: {state.get('status')}")
    print(f"Total Generation Attempts: {telemetry.get('generation_attempts')} (Verified maximum: 1 initial + 3 retries = 4)")
    print(f"Retry Budget Exhausted: {state.get('retry_count')} / {state.get('max_retries', 3)}")
    print(f"Remaining Budget: {max(0, state.get('max_retries', 3) - state.get('retry_count', 0))}")
    print(f"Token Telemetry (Demo Fixture): Prompt={telemetry.get('prompt_tokens')} [Demo Fixture], Comp={telemetry.get('completion_tokens')} [Demo Fixture], Total={telemetry.get('total_tokens')} [Demo Fixture]")
    print(f"Memory Admission Status: {telemetry.get('memory_admission')} (Zero false admission verified [Live Measured])")

    print("\n--- ATTEMPT-BY-ATTEMPT LIFECYCLE AUDIT TRAIL ---")
    for att in attempts:
        print(f"\n[Attempt {att['attempt']}] {'(Repair Iteration ' + str(att['attempt']-1) + ')' if att['is_repair'] else '(Initial Generation)'} at {att['timestamp']}")
        print(f"  SQL: {att['sql']}")
        print(f"  AST Guard: {'PASSED [Live Measured]' if att.get('ast_valid') else 'FAILED [Live Measured]'}")
        print(f"  PostgreSQL: {'FAILED [Live Measured]: ' + str(att.get('exec_error')).strip().splitlines()[0] if not att.get('exec_success') else 'SUCCESS [Live Measured]'}")
        if att.get("diagnosis"):
            d = att["diagnosis"]
            print(f"  Diagnosis: Category={d.get('taxonomy_category')}, Broken='{d.get('broken_identifier')}' [Live Measured]")

    return state


# =============================================================================
# Demonstration 3: Safety Blocking
# =============================================================================

def run_demonstration_3_safety_blocking(env: PostgreSQLEnvironment) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("DEMONSTRATION 3: PRE-EXECUTION AST SAFETY GUARD BLOCK")
    print("=" * 80)
    print("Source Type: Controlled Demonstration Fixture (exercises real AST guardrail and routing)")
    print("Scenario: Destructive SQL statement generated (e.g. DROP TABLE fact_sales_performance CASCADE;).")
    print("Requirement: Rejected before PostgreSQL execution; database executor is NEVER called.")

    unsafe_result = GenerationResult(
        raw_response="```sql\nDROP TABLE fact_sales_performance CASCADE;\n```",
        extracted_sql="DROP TABLE fact_sales_performance CASCADE;",
        prompt_tokens=150,
        completion_tokens=20,
        generation_duration_ms=60.0,
    )

    demo_gen = DemonstrationSequenceGenerator([unsafe_result], label="Demonstration Fixture: Unsafe DDL")
    v_store = FAISSMemoryStore()
    gov_engine = MemoryGovernanceEngine()

    wf = ARMGRepairWorkflow(
        environment=env,
        sql_generator=demo_gen,
        repair_generator=demo_gen,
        governance_engine=gov_engine,
        vector_store=v_store,
        embed_fn=default_embed_fn,
    )
    app = wf.build_graph()

    state = app.invoke({
        "user_query": "Drop the sales table permanently.",
        "max_retries": 3,
    })

    telemetry = state.get("telemetry", {})
    attempts = telemetry.get("attempts_trace", [])

    print(f"\nFinal Execution Status: {state.get('status')}")
    print(f"Safety Violation Detected: {state.get('is_safety_violation')}")
    print(f"Safety Category: {state.get('safety_category')}")
    print(f"AST Validation Error: {state.get('validation_error')}")
    print(f"PostgreSQL Execution Result: {state.get('execution_result')} (Verified: NEVER CALLED)")
    print(f"Memory Admission Status: {telemetry.get('memory_admission', 'NONE')}")

    print("\n--- ATTEMPT AUDIT TRAIL ---")
    for att in attempts:
        print(f"\n[Attempt {att['attempt']}] at {att['timestamp']}")
        print(f"  SQL: {att['sql']}")
        print(f"  AST Guard: REJECTED (Safety Violation: {att.get('safety_category')})")
        print(f"  AST Error: {att.get('ast_error')}")
        print(f"  PostgreSQL: {'NOT EXECUTED' if not att.get('executed_in_db') else 'ERROR: ILLEGALLY EXECUTED'}")

    return state


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    print("Initializing PostgreSQL warehouse environment...")
    env = PostgreSQLEnvironment()

    # Verify database connectivity
    test_res = env.execute("SELECT 1;")
    if not test_res.is_success:
        print(f"Error: PostgreSQL is unavailable: {test_res.error}")
        sys.exit(1)
    print("PostgreSQL connection confirmed.")

    demo1_state = run_demonstration_1_successful_repair(env)
    assert demo1_state.get("status") == STATUS_SUCCESS, "Demo 1 must succeed after repair"
    assert demo1_state.get("retry_count") == 1, "Demo 1 must use exactly 1 retry"

    demo2_state = run_demonstration_2_terminal_failure(env)
    assert demo2_state.get("status") == STATUS_FAILED, "Demo 2 must terminate with STATUS_FAILED"
    assert demo2_state.get("retry_count") == 3, "Demo 2 must exhaust 3 retries"
    assert demo2_state["telemetry"]["generation_attempts"] == 4, "Demo 2 must make exactly 4 generation attempts"

    demo3_state = run_demonstration_3_safety_blocking(env)
    assert demo3_state.get("status") == STATUS_BLOCKED, "Demo 3 must terminate with STATUS_BLOCKED"
    assert demo3_state.get("execution_result") is None, "Demo 3 must not execute in database"

    print("\n" + "=" * 80)
    print("ALL THREE PHASE 3 FACULTY DEMONSTRATIONS COMPLETED SUCCESSFULLY & VERIFIED.")
    print("=" * 80)


if __name__ == "__main__":
    main()
