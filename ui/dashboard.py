"""
ARMG Phase 8: Live Streamlit Inspection Dashboard.

Provides an interactive observability and inspection interface over the ARMG engine:
1. Tab 1: Live Query Execution & Runtime Trace (Schema, Generation, AST Guard, Execution, Diagnosis, Repair, Telemetry).
2. Tab 2: Governed Runtime Memory Bank Inspector (FAISS memory status, filtering including DECAYING, epoch decay sweep).
3. Tab 3: Governance Mathematics & Decay Visualizer (Confidence decay, escalation, penalty, and utility curves).
"""

import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import streamlit as st

# Ensure repository root is in sys.path when executed via 'streamlit run ui/dashboard.py'
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from environment.postgres import PostgreSQLEnvironment

from graph.state import STATUS_BLOCKED, STATUS_FAILED, STATUS_RETRYING, STATUS_RUNNING, STATUS_SUCCESS
from graph.workflow import ARMGRepairWorkflow
from memory.governance import MemoryGovernanceEngine
from memory.models import MemoryState, RuntimeMemory
from memory.vector_store import FAISSMemoryStore


# =============================================================================
# Page Configuration & Styling
# =============================================================================

st.set_page_config(
    page_title="ARMG — Adaptive Runtime Memory Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# State Management & Engine Initialization (Section 4)
# =============================================================================

def get_engine_components():
    """Retrieve or initialize persistent session components without modifying ARMG engine."""
    if "governance_engine" not in st.session_state:
        st.session_state.governance_engine = MemoryGovernanceEngine()

    if "vector_store" not in st.session_state:
        st.session_state.vector_store = FAISSMemoryStore()

    if "simulated_epoch" not in st.session_state:
        st.session_state.simulated_epoch = 0

    if "environment" not in st.session_state:
        try:
            st.session_state.environment = PostgreSQLEnvironment()
        except Exception:
            st.session_state.environment = None

    if "workflow" not in st.session_state:
        if st.session_state.environment is not None:
            st.session_state.workflow = ARMGRepairWorkflow(
                environment=st.session_state.environment,
                governance_engine=st.session_state.governance_engine,
                vector_store=st.session_state.vector_store,
            )
        else:
            st.session_state.workflow = None

    return (
        st.session_state.workflow,
        st.session_state.governance_engine,
        st.session_state.vector_store,
        st.session_state.environment,
    )


workflow, governance_engine, vector_store, environment = get_engine_components()


# =============================================================================
# Header & Overview
# =============================================================================

st.title("🛡️ Adaptive Runtime Memory Governance (ARMG)")
st.caption(
    "Operational Knowledge Framework Validated in Text-to-SQL — "
    "Autonomous Observation, Deterministic Diagnosis, Governed Memory, and Runtime Repair"
)

tab1, tab2, tab3 = st.tabs([
    "🚀 Live Query Execution & Runtime Trace",
    "🧠 Governed Memory Bank Inspector",
    "📐 Governance Mathematics & Decay Visualizer",
])


# =============================================================================
# Tab 1: Live Query Execution & Runtime Trace
# =============================================================================

with tab1:
    st.header("Live Query Execution & Runtime Trace")
    st.markdown(
        "Execute analytical queries through the compiled **LangGraph repair workflow**. "
        "Observe deterministic schema pruning, AST guardrails, PostgreSQL execution, "
        "passive runtime observation, error diagnosis, and bounded self-repair."
    )

    SAMPLE_QUERIES = [
        "What is the total gross revenue?",
        "Show total gross revenue by region.",
        "What is the total revenue by region?",  # Exercising semantic repair: revenue -> gross_revenue
        "What is the total discount applied and net profit by product category?",
        "Show units sold and net profit for each zone.",
        "Custom Query...",
    ]

    col_q1, col_q2 = st.columns([2, 1])
    with col_q1:
        selected_sample = st.selectbox(
            "Select an Analytical Query Example:",
            SAMPLE_QUERIES,
            index=2,  # Default to revenue repair example
            key="sample_query_select",
        )

    with col_q2:
        max_retries_input = st.number_input(
            "Max Repair Retries:",
            min_value=1,
            max_value=5,
            value=3,
            help="Maximum repair retries (locked default: 3 retries = 4 total generation attempts).",
            key="max_retries_input",
        )

    initial_text = "" if selected_sample == "Custom Query..." else selected_sample
    user_query = st.text_area(
        "Query Input:",
        value=initial_text,
        height=70,
        placeholder="Type a natural language question (e.g., 'What is the total revenue by region?')...",
        key="query_input_text",
    )

    run_btn = st.button("⚡ Execute Query", type="primary", key="execute_query_button")

    if run_btn:
        if not user_query.strip():
            st.warning("Please enter a query before executing.")
        elif workflow is None or environment is None:
            st.error(
                "Runtime Environment is unavailable. Ensure PostgreSQL service is running on port 5432."
            )
        else:
            with st.spinner("Executing through ARMG Workflow..."):
                try:
                    app_graph = workflow.build_graph()
                    exec_state = app_graph.invoke({
                        "user_query": user_query.strip(),
                        "max_retries": int(max_retries_input),
                    })
                    st.session_state["last_execution_state"] = exec_state
                except Exception as ex:
                    st.error(f"Execution failed with runtime exception: {ex}")

    # Display Last Execution Results if available
    last_state: Optional[Dict[str, Any]] = st.session_state.get("last_execution_state")
    if last_state:
        status = last_state.get("status", STATUS_FAILED)
        retries = last_state.get("retry_count", 0)
        telemetry = last_state.get("telemetry", {})

        st.divider()

        # Status Banner
        if status == STATUS_SUCCESS:
            if retries > 0:
                st.success(f"**STATUS: SUCCESS (REPAIRED)** — Resolved after {retries} repair retry attempt(s)")
            else:
                st.success("**STATUS: SUCCESS** — Resolved on initial generation attempt (0 retries)")
        elif status == STATUS_BLOCKED:
            sec_cat = last_state.get("safety_category", "explicit safety policy")
            st.error(f"🛡️ **STATUS: BLOCKED** — Execution permanently prevented by AST safety guardrail ({sec_cat}). Destructive mutations and non-read-only operations are strictly prohibited.")
        elif status == STATUS_RETRYING:
            st.warning(f"**STATUS: RETRYING** — Currently in repair iteration {retries}")
        else:
            st.error(f"**STATUS: FAILED** — Exhausted all {retries} repair retry attempts without resolution")

        # Telemetry metrics cards
        t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
        t_col1.metric("Status", status)
        t_col2.metric("Retry Count", f"{retries} / {last_state.get('max_retries', 3)}")
        t_col3.metric("Generation Attempts", telemetry.get("generation_attempts", 1))
        t_col4.metric("Total Latency", f"{telemetry.get('total_latency_ms', 0.0):.1f} ms")
        t_col5.metric("Total Tokens", telemetry.get("total_tokens", 0))

        # Trace Section 1: Schema Context
        with st.expander("1. Pruned Schema Context", expanded=False):
            st.markdown(last_state.get("pruned_schema_markdown", "No schema available"))

        # Trace Section 2: Memory Retrieval
        retrieved = last_state.get("retrieved_memories", [])
        with st.expander(f"2. Governed Memory Retrieval ({len(retrieved)} retrieved)", expanded=bool(retrieved)):
            if retrieved:
                for idx, mem in enumerate(retrieved, start=1):
                    st.markdown(
                        f"**Memory {idx}** (`{mem.memory_id}`) | Status: `{mem.status.value}` | "
                        f"Confidence: `{mem.confidence:.2f}` | Utility: `{mem.utility:.3f}`"
                    )
                    st.markdown(f"- **Rule:** {mem.repair_strategy}")
                    st.markdown(f"- **Root Cause:** {mem.root_cause}")
            else:
                st.info("No prior governed memories retrieved for this query context.")

        # Trace Section 3: SQL Generation & AST Guard
        st.subheader("Generated SQL & Validation")
        col_sql1, col_sql2 = st.columns(2)

        with col_sql1:
            if status == STATUS_BLOCKED:
                st.markdown("**Generated SQL — BLOCKED:**")
            elif not last_state.get("validation_passed", True):
                st.markdown("**Generated SQL (Validation Failed):**")
            elif status == STATUS_SUCCESS:
                st.markdown("**Final Executed SQL Query:**")
            else:
                st.markdown("**Final Generated SQL Query:**")

            final_sql = last_state.get("generated_sql", "-- No SQL generated --")
            st.code(final_sql, language="sql")

            if last_state.get("previous_sql"):
                st.warning(f"Previous Failed SQL (Attempt {retries}):")
                st.code(last_state["previous_sql"], language="sql")
                prev_err = last_state.get("previous_execution_error") or telemetry.get("previous_execution_error")
                if prev_err:
                    st.caption(f"Prior Attempt Failure: {prev_err}")

        with col_sql2:
            st.markdown("**AST Guardrail Inspection:**")
            if last_state.get("validation_passed", False):
                st.info("🛡️ **AST VALIDATION PASSED** — Single safe read-only SELECT verified.")
            else:
                val_err = last_state.get("validation_error", "Unknown validation rejection")
                st.error(f"🚫 **AST VALIDATION FAILED**: {val_err}")

            if status == STATUS_BLOCKED:
                st.info("⚡ **PostgreSQL**: NOT EXECUTED (Operation permanently blocked by safety guardrail)")
            elif not last_state.get("validation_passed", True):
                st.info("⚡ **PostgreSQL**: NOT EXECUTED (AST validation failed before execution)")
            else:
                exec_res = last_state.get("execution_result")
                if exec_res:
                    if exec_res.is_success:
                        st.success(f"⚡ **PostgreSQL Execution Success** ({exec_res.execution_time_ms:.1f} ms)")
                    else:
                        st.error(f"❌ **PostgreSQL Execution Error**: {exec_res.error}")
                else:
                    st.info("⚡ **PostgreSQL**: NOT EXECUTED")

        # Trace Section 4: Query Results Table
        exec_res = last_state.get("execution_result")
        if exec_res and exec_res.is_success and exec_res.rows:
            st.subheader("Query Result Set")
            st.dataframe(pd.DataFrame(exec_res.rows), use_container_width=True)
            st.caption(f"Retrieved {exec_res.row_count} row(s) in {exec_res.execution_time_ms:.2f} ms")

        # Trace Section 5: Diagnosis & Strict Repair Constraints (if failure occurred)
        if status == STATUS_BLOCKED:
            st.subheader("Deterministic Error Diagnosis & Strict Repair Constraints")
            st.info("🛡️ **Diagnosis & Repair**: NOT INVOKED (Safety guardrail rejections are terminal and non-repairable)")
        else:
            diag = last_state.get("diagnosis")
            if diag:
                st.subheader("Deterministic Error Diagnosis & Strict Repair Constraints")
                d_col1, d_col2 = st.columns([1, 1])
                with d_col1:
                    st.markdown(f"**Taxonomy Category:** `{diag.taxonomy_category.value}`")
                    st.markdown(f"**Broken Identifier:** `{diag.broken_identifier or 'None'}`")
                    st.markdown(f"**Root Cause:** {diag.root_cause}")
                    st.markdown(f"**Candidate Replacements:** `{diag.candidate_replacements}`")
                    st.markdown(f"**Negative Constraints:** `{diag.negative_constraints}`")
                    st.markdown(f"**Repair Rule:** {diag.repair_rule}")

                with d_col2:
                    repair_prompt = last_state.get("repair_prompt")
                    if repair_prompt and "[STRICT REPAIR CONSTRAINTS]" in repair_prompt:
                        st.markdown("**Actual Generated Strict Repair Block:**")
                        # Extract the strict constraints section
                        start_idx = repair_prompt.find("[STRICT REPAIR CONSTRAINTS]")
                        end_idx = repair_prompt.find("### REPAIRED SQL QUERY:")
                        if end_idx != -1:
                            constraints_text = repair_prompt[start_idx:end_idx].strip()
                        else:
                            constraints_text = repair_prompt[start_idx:].strip()
                        st.code(constraints_text, language="text")

        # Trace Section 6: Governance Telemetry
        st.subheader("Post-Execution Governance Telemetry")
        st.markdown(f"- **Memory Admission Status:** `{telemetry.get('memory_admission', 'NONE')}`")
        if telemetry.get("admitted_memory_id"):
            st.markdown(f"- **Admitted Memory ID:** `{telemetry['admitted_memory_id']}`")
        if telemetry.get("reinforced_memory_id"):
            st.markdown(f"- **Reinforced Memory ID:** `{telemetry['reinforced_memory_id']}`")
        if telemetry.get("penalized_memory_id"):
            st.markdown(f"- **Penalized Memory ID:** `{telemetry['penalized_memory_id']}`")


# =============================================================================
# Tab 2: Governed Memory Bank Inspector
# =============================================================================

with tab2:
    st.header("Governed Memory Bank Inspector")
    st.markdown(
        "Inspect the contents of the **FAISS CPU Vector Store** and decoupled metadata registry. "
        "Filter memories across the six-stage lifecycle (`NEW`, `ACTIVE`, `STABLE`, `DECAYING`, `ARCHIVED`, `DELETED`)."
    )

    memories: List[RuntimeMemory] = vector_store.all_memories()

    # Filter row
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    with f_col1:
        state_filter = st.selectbox(
            "Filter by Lifecycle State:",
            ["ALL", "NEW", "ACTIVE", "STABLE", "DECAYING", "ARCHIVED"],
            index=0,
            key="memory_state_filter",
        )

    with f_col2:
        st.metric("Total Governed Memories", len(memories))

    with f_col3:
        st.metric("Simulated Epoch / Day", st.session_state.simulated_epoch)

    # Filter memories
    if state_filter != "ALL":
        filtered_memories = [m for m in memories if m.status.value == state_filter]
    else:
        filtered_memories = memories

    # Display Memory Table
    if filtered_memories:
        table_rows = []
        for m in filtered_memories:
            forbid_str = ", ".join(m.negative_constraints) if m.negative_constraints else "None"
            table_rows.append({
                "Memory ID": m.memory_id,
                "Failure Type": m.failure_type.value if hasattr(m.failure_type, "value") else str(m.failure_type),
                "Root Cause": m.root_cause,
                "Repair Strategy / Rule": m.repair_strategy,
                "Forbidden Tokens": forbid_str,
                "Status": m.status.value,
                "Confidence": f"{m.confidence:.3f}",
                "Utility": f"{m.utility:.3f}",
                "Total Uses": m.total_uses,
                "Successful Uses": m.successful_uses,
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    else:
        st.info(
            f"No governed memories found with status '{state_filter}'. "
            "Execute an analytical query with a repair attempt in Tab 1 to populate governed memory."
        )

    st.divider()

    # Simulated Epoch Decay Sweep
    st.subheader("Simulated Epoch Decay Sweep")
    st.markdown(
        "Simulate the passage of time without altering wall-clock time. "
        "Applies Phase 6 continuous exponential decay: $C(t) = C_{\\text{ref}} \\cdot e^{-\\lambda \\cdot \\Delta t}$."
    )

    s_col1, s_col2, s_col3 = st.columns([1, 1, 2])
    with s_col1:
        advance_days = st.number_input(
            "Days / Epochs to Advance:",
            min_value=1,
            max_value=90,
            value=10,
            step=1,
            key="advance_days_input",
        )

    with s_col2:
        decay_btn = st.button("⏳ Trigger Simulated Epoch Decay Sweep", key="trigger_decay_button")

    if decay_btn:
        new_epoch = st.session_state.simulated_epoch + int(advance_days)
        st.session_state.simulated_epoch = new_epoch
        # Execute Phase 6 decay sweep across all registered memories
        current_mems = vector_store.all_memories()
        updated_mems = governance_engine.apply_decay_sweep(current_mems, current_epoch=new_epoch)
        # Update vector store metadata
        for updated in updated_mems:
            if updated.embedding:
                vector_store.add(updated, updated.embedding)
        st.success(
            f"Simulated epoch advanced to **Epoch {new_epoch}** (+{advance_days} days). "
            f"Decay sweep evaluated for {len(updated_mems)} memory artifact(s)."
        )
        st.rerun()

    st.warning(
        "🔒 **Governance Safety Rule**: Manual editing of confidence, utility, use counts, "
        "or lifecycle states is strictly prohibited. State transitions are governed exclusively "
        "by the deterministic Phase 6 governance engine."
    )


# =============================================================================
# Tab 3: Governance Mathematics & Decay Visualizer
# =============================================================================

with tab3:
    st.header("Governance Mathematics & Control Engine Visualizer")
    st.markdown(
        "Interactive mathematical visualization of the locked **Phase 6 Governance equations** "
        "governing operational memory utility, confidence escalation, failure penalty, and exponential decay."
    )

    # Section A: Continuous Exponential Decay
    st.subheader("A. Continuous Exponential Confidence Decay")
    st.latex(r"C(t) = C_0 \cdot e^{-\lambda \cdot \Delta t} \quad \text{with } \lambda = 0.05 \text{ day}^{-1}")

    decay_col1, decay_col2 = st.columns([1, 2])
    with decay_col1:
        decay_c0 = st.slider("Starting Confidence ($C_0$):", min_value=0.20, max_value=1.0, value=0.80, step=0.05)
        decay_lambda = st.slider(r"Decay Rate ($\lambda$ per day):", min_value=0.01, max_value=0.20, value=0.05, step=0.01)

    epochs = np.arange(0, 61, 1)
    decay_curve = [round(decay_c0 * math.exp(-decay_lambda * t), 4) for t in epochs]

    decay_df = pd.DataFrame({
        "Simulated Epoch (Days)": epochs,
        "Decayed Confidence": decay_curve,
        "Stable Threshold (0.80)": [0.80] * len(epochs),
        "Archive Threshold (0.20)": [0.20] * len(epochs),
    }).set_index("Simulated Epoch (Days)")

    with decay_col2:
        st.line_chart(decay_df)

    st.divider()

    # Section B: Asymptotic Successful-Use Escalation
    st.subheader("B. Asymptotic Successful-Use Confidence Escalation")
    st.latex(r"C_{\text{new}} = C_{\text{old}} + \alpha \cdot (1 - C_{\text{old}}) \quad \text{with } \alpha = 0.10")

    esc_col1, esc_col2 = st.columns([1, 2])
    with esc_col1:
        esc_c0 = st.slider("Initial Prior Confidence ($C_0$):", min_value=0.10, max_value=0.90, value=0.50, step=0.05)
        esc_alpha = st.slider("Escalation Rate ($\alpha$):", min_value=0.05, max_value=0.30, value=0.10, step=0.01)

    succ_counts = list(range(11))
    esc_values = [esc_c0]
    curr_c = esc_c0
    for _ in range(10):
        curr_c = curr_c + esc_alpha * (1.0 - curr_c)
        esc_values.append(round(curr_c, 4))

    esc_df = pd.DataFrame({
        "Successful Uses": succ_counts,
        "Escalated Confidence": esc_values,
        "Stable Threshold (0.80)": [0.80] * len(succ_counts),
    }).set_index("Successful Uses")

    with esc_col2:
        st.line_chart(esc_df)

    st.divider()

    # Section C: Failure Penalty Reduction
    st.subheader("C. Multiplicative Failure Penalty Reduction")
    st.latex(r"C_{\text{new}} = \max(0, \, C_{\text{old}} \cdot (1 - \beta)) \quad \text{with } \beta = 0.15")

    pen_col1, pen_col2 = st.columns([1, 2])
    with pen_col1:
        pen_c0 = st.slider("Current Confidence ($C_0$):", min_value=0.30, max_value=1.0, value=0.85, step=0.05)
        pen_beta = st.slider("Penalty Rate ($\beta$):", min_value=0.05, max_value=0.40, value=0.15, step=0.01)

    fail_counts = list(range(11))
    pen_values = [pen_c0]
    curr_p = pen_c0
    for _ in range(10):
        curr_p = max(0.0, curr_p * (1.0 - pen_beta))
        pen_values.append(round(curr_p, 4))

    pen_df = pd.DataFrame({
        "Consecutive Failures": fail_counts,
        "Penalized Confidence": pen_values,
        "Archive Threshold (0.20)": [0.20] * len(fail_counts),
    }).set_index("Consecutive Failures")

    with pen_col2:
        st.line_chart(pen_df)

    st.divider()

    # Section D: Multi-Factor Utility Heuristic
    st.subheader("D. Multi-Factor Utility Heuristic Calculator")
    st.latex(
        r"\text{Utility} = \text{Confidence} \times \text{SuccessRate} \times \text{ContextSimilarity} \times \text{Recency}"
    )
    st.latex(r"\text{where } \text{SuccessRate} = \frac{\text{successful}}{\text{total}} \quad \text{and} \quad \text{Recency} = \frac{1}{1 + \Delta t}")

    u_col1, u_col2, u_col3, u_col4 = st.columns(4)
    with u_col1:
        u_conf = st.number_input("Confidence ($C$):", min_value=0.0, max_value=1.0, value=0.80, step=0.05)
    with u_col2:
        u_succ = st.number_input("Successful Uses:", min_value=0, max_value=50, value=8, step=1)
        u_tot = st.number_input("Total Uses:", min_value=1, max_value=50, value=10, step=1)
    with u_col3:
        u_sim = st.number_input("Context Similarity:", min_value=0.0, max_value=1.0, value=0.90, step=0.05)
    with u_col4:
        u_dt = st.number_input(r"Elapsed Time ($\Delta t$ days):", min_value=0.0, max_value=100.0, value=2.0, step=1.0)

    calculated_u = governance_engine.calculate_utility(
        confidence=float(u_conf),
        successful_uses=int(u_succ),
        total_uses=int(u_tot),
        context_similarity=float(u_sim),
        delta_t=float(u_dt),
    )

    admission_qualified = calculated_u >= governance_engine.admission_threshold
    st.info(
        f"**Calculated Operational Utility:** `{calculated_u:.4f}` | "
        f"**Admission Threshold ($\theta = 0.25$):** "
        f"{'✅ ADMITTED' if admission_qualified else '❌ REJECTED'}"
    )
