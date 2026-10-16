# ARMG Architecture & Safety Changelog

This document records architectural, safety, and governance additions to Adaptive Runtime Memory Governance (ARMG).

> **Provenance & Baseline Integrity Note**:  
> The canonical experimental benchmark results and artifacts reported in `benchmark/` and the frozen evidence package reflect the **ARMG v1.0 evaluation baseline** ($n=3$ multi-seed benchmark across 25 queries over the synthetic Star Schema warehouse). The enhancements documented below represent post-v1.0 architectural safety and constraint-preservation layers implemented in the working tree. They operate as pre-execution and repair guardrails without altering the historical benchmark provenance or the frozen v1.0 baseline measurements.

---

## [Unreleased Working Tree] — Post-v1.0 Safety & Governance Enhancements

### 1. Natural-Language Intent Safety Gate (Phase 12)
- **Module Added**: `validation/intent_classifier.py`
- **Workflow Node Added**: `intent_gate_node` (Node 1 in LangGraph `StateGraph`)
- **Key Capabilities**:
  - Deterministic, zero-token pre-generation classification of natural-language analytical requests prior to language model or database invocations.
  - Multi-tier cascading evaluation: fast-path keyword filtering, ambiguity/contradiction detection, educational/negation whitelisting, imperative destructive command detection (`DROP`, `TRUNCATE`, `DELETE`, `ALTER TABLE ... DROP`), standalone direct SQL command detection, and non-destructive vocabulary fallback.
  - Controlled decision outcomes: `BLOCK`, `ALLOW`, `ALLOW_EXPLANATION`, `AMBIGUOUS`.
  - Immediate short-circuit routing upon `BLOCK` or `AMBIGUOUS` directly to `memory_governance_node`, guaranteeing 0 Ollama tokens, 0 SQL generations, 0 schema introspection queries, 0 vector store lookups, 0 PostgreSQL calls, and 0 repair retries.
  - Terminal state attribution: `status = STATUS_BLOCKED`, `decision_source = "natural_language_intent_gate"`, `block_reason = "DESTRUCTIVE_INTENT_DETECTED"` (or `"AMBIGUOUS_INTENT_CLARIFICATION_REQUIRED"`), and `memory_admission = "SAFETY_VIOLATION_BLOCKED"`.
- **Test Evidence**:
  - `tests/unit/test_phase12_intent_gate.py` (37 automated tests verifying standalone classifier rules, execution short-circuiting, benign prompt whitelisting, ambiguity handling, error isolation, and manual SQL override precedence).

### 2. Explicit User-Constraint Preservation & Projection Validation (Phase 13)
- **Module Added**: `validation/constraint_validator.py`
- **Integration Points**: `agents/schema_introspector.py` (extraction), `graph/workflow.py` (`introspect_and_prune_node`, `ast_guard_node`, `observation_node`, `memory_retrieval_node`), `agents/error_diagnosis.py` (constraint-aware diagnosis).
- **Key Capabilities**:
  - Extraction and tracking of `ExplicitConstraints`: required exact tables (`required_tables`), prohibited tables (`prohibited_tables`), table substitution policy (`allow_table_substitution`), and required output columns (`required_columns`).
  - AST-level projection validation: verifies that explicitly demanded output columns are represented in `SELECT` projection expressions (as direct columns, qualified identifiers, aliases, or within aggregations), rejecting candidates where required columns appear only in `WHERE`, `JOIN`, or `GROUP BY` clauses.
  - Wildcard projection rejection: strictly rejects `SELECT *` when an explicit output column is mandated, as column presence cannot be verified statically from the wildcard alone.
  - Autonomous repair constraint bounding: prevents the self-repair generator from silently substituting a prohibited table when an exact requested relation does not exist in the database (Case A).
  - Memory retrieval filtering: candidate memories that recommend prohibited table substitutions are excluded from retrieval for constrained queries.
- **Test Evidence**:
  - `tests/unit/test_constraint_preservation.py` (23 automated tests verifying exact table substitution blocking, output-column projection validation, Test 4A vs 4B differentiation, Test 8 regional revenue aggregation repair, and authorized governance quarantine).
  - `tests/integration/test_repair_integration.py` (5 live PostgreSQL integration tests validating constraint preservation and semantic repair against active database instances).

### 3. Authorized Memory Quarantine API
- **Module Enhanced**: `graph/workflow.py` (`quarantine_memory_by_id`) and `memory/governance.py` (`archive_memory`)
- **Key Capabilities**:
  - Exposes an authorized operational method to inspect and quarantine invalid historical memories from active retrieval.
  - Transitions the target memory to `MemoryState.ARCHIVED` with structured quarantine metadata (`reason`), permanently excluding it from FAISS nearest-neighbor searches while maintaining audit trail history.

### 4. Interactive Streamlit UI Modernization (Phase 8 UI)
- **Module Enhanced**: `ui/dashboard.py`
- **Key Capabilities**:
  - Real-time display of Intent Gate decisions (`STATUS: BLOCKED`, `STATUS: CLARIFICATION REQUIRED`) with zero-Ollama / zero-PostgreSQL telemetry attribution.
  - Dedicated display of explicit constraint violations (`STATUS: FAILED (EXPLICIT CONSTRAINT VIOLATION)`).
  - Clear attribution of execution source mode (`🤖 Ollama Generation` vs `⚡ Manual SQL Override`).
  - Session state isolation: ensures fresh form submissions initialize clean state payloads, preventing cross-run telemetry contamination.

---

## [ARMG v1.0 Baseline] — Canonical Research Benchmark Release (Frozen)

- **Initial Pipeline & Baseline**: Single-pass Text-to-SQL generation over PostgreSQL analytical warehouse using local `qwen2.5:7b-instruct` and `nomic-embed-text`.
- **Pre-Execution Safety**: Static SQLGlot AST guardrail (`validation/execution_validator.py`) enforcing single-statement execution, read-only `SELECT` root statements, and destructive DDL/DML rejection.
- **Diagnostic Taxonomy**: 7-tier deterministic exception taxonomy (`Validation`, `Syntax`, `Semantic`, `Planning`, `Permission`, `Resource`, `Execution`).
- **Autonomic Memory Engine**: Multi-factor utility formulation ($U = C \times \text{SuccessRate} \times \text{ContextSimilarity} \times \text{Recency}$), asymptotic confidence escalation ($\alpha=0.10$), failure penalty ($\beta=0.15$), continuous exponential decay ($\lambda=0.05$), and 6-stage lifecycle machine (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`).
- **Evaluation Suite**: 450 total benchmark evaluations ($n=3$ repeated runs over 25 queries across 6 experimental modes: Zero-Shot, Stateless Repair, Unmanaged RAG, Governed ARMG, No-Negative Ablation, No-Decay Ablation).
