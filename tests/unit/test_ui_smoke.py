"""
Headless UI smoke test for ARMG Phase 8: Streamlit Inspection Dashboard.

Uses streamlit.testing.v1.AppTest to verify:
- Dashboard imports and loads cleanly headlessly without uncaught exceptions.
- All three major tabs render (Query Trace, Memory Bank, Governance Visualizer).
- Major headers and titles are present.
- Query input text area, sample selectbox, and execution button exist.
- Memory filter selectbox exists and explicitly includes DECAYING.
- Decay-sweep controls exist (days input + trigger button).
- Governance mathematics section and line charts render.
- No live network, Ollama, or PostgreSQL query dependencies required for rendering contract.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DASHBOARD_PATH = str(ROOT_DIR / "ui" / "dashboard.py")
RENDER_TIMEOUT = 15  # generous timeout for cold imports in test runners


@pytest.fixture
def app_test() -> AppTest:
    """Fixture providing an initialized, headlessly rendered AppTest instance."""
    at = AppTest.from_file(DASHBOARD_PATH).run(timeout=RENDER_TIMEOUT)
    return at


def test_dashboard_renders_without_exceptions(app_test: AppTest):
    """Verify initial headless render produces zero uncaught Streamlit exceptions."""
    assert len(app_test.exception) == 0, f"Uncaught exceptions: {[e.value for e in app_test.exception]}"


def test_all_three_tabs_render(app_test: AppTest):
    """Verify all 3 tabs are created and rendered in the dashboard."""
    assert len(app_test.tabs) == 3


def test_major_headers_present(app_test: AppTest):
    """Verify major headers and system title are present."""
    assert len(app_test.title) >= 1
    title_text = app_test.title[0].value
    assert "Adaptive Runtime Memory Governance" in title_text

    header_values = [h.value for h in app_test.header]
    assert any("Live Query Execution & Runtime Trace" in h for h in header_values)
    assert any("Governed Memory Bank Inspector" in h for h in header_values)
    assert any("Governance Mathematics & Control Engine Visualizer" in h for h in header_values)


def test_query_input_and_controls_exist(app_test: AppTest):
    """Verify analytical query inputs, pre-populated samples, and execute button exist in Tab 1."""
    # Sample selection selectbox
    sample_selects = [s for s in app_test.selectbox if "Analytical Query Example" in s.label]
    assert len(sample_selects) == 1
    options = sample_selects[0].options
    assert any("revenue" in opt.lower() for opt in options)

    # Text area query input
    query_inputs = [t for t in app_test.text_area if "Query Input" in t.label]
    assert len(query_inputs) == 1

    # Execute button
    exec_buttons = [b for b in app_test.button if "Execute Query" in b.label]
    assert len(exec_buttons) == 1


def test_memory_filter_exists_with_decaying_state(app_test: AppTest):
    """Verify lifecycle state filter exists and strictly includes DECAYING state."""
    filter_selects = [s for s in app_test.selectbox if "Filter by Lifecycle State" in s.label]
    assert len(filter_selects) == 1
    options = filter_selects[0].options
    # Locked lifecycle requires all states including DECAYING
    assert "ALL" in options
    assert "NEW" in options
    assert "ACTIVE" in options
    assert "STABLE" in options
    assert "DECAYING" in options  # Critical invariant: must NOT omit DECAYING
    assert "ARCHIVED" in options


def test_decay_sweep_control_exists(app_test: AppTest):
    """Verify simulated epoch advance control and decay sweep trigger button exist in Tab 2."""
    advance_inputs = [n for n in app_test.number_input if "Advance" in n.label]
    assert len(advance_inputs) >= 1

    sweep_buttons = [b for b in app_test.button if "Decay Sweep" in b.label]
    assert len(sweep_buttons) == 1


def test_governance_visualization_section_exists(app_test: AppTest):
    """Verify mathematical governance sections and line charts render in Tab 3."""
    subheaders = [s.value for s in app_test.subheader]
    assert any("Confidence Decay" in s for s in subheaders)
    assert any("Escalation" in s for s in subheaders)
    assert any("Penalty" in s for s in subheaders)
    assert any("Utility" in s for s in subheaders)

    # Verify mathematical sliders (C_0, lambda, alpha, beta) and LaTeX formulas render
    assert len(app_test.slider) >= 6
    assert len(app_test.latex) >= 4


def test_simulated_decay_sweep_interaction(app_test: AppTest):
    """Verify triggering simulated epoch decay sweep executes without exception."""
    sweep_btn = [b for b in app_test.button if "Decay Sweep" in b.label][0]
    sweep_btn.click()
    app_test.run(timeout=RENDER_TIMEOUT)
    assert len(app_test.exception) == 0


def test_dashboard_renders_blocked_state_correctly():
    """Verify BLOCKED execution state renders blocked SQL label, NOT EXECUTED, and NOT INVOKED."""
    at = AppTest.from_file(DASHBOARD_PATH)
    # Set simulated last execution state with STATUS_BLOCKED
    at.session_state["last_execution_state"] = {
        "status": "BLOCKED",
        "user_query": "Delete all records from the sales table.",
        "retry_count": 1,
        "max_retries": 3,
        "generated_sql": "DELETE FROM fact_sales_performance;",
        "previous_sql": "SELECT revenue FROM fact_sales_performance;",
        "previous_execution_error": 'column "revenue" does not exist',
        "validation_passed": False,
        "validation_error": "Destructive mutation 'Delete' is strictly rejected.",
        "is_safety_violation": True,
        "safety_category": "destructive_mutation",
        "execution_result": None,
        "diagnosis": None,
        "runtime_knowledge": None,
        "telemetry": {
            "generation_attempts": 2,
            "repair_count": 1,
            "memory_admission": "SAFETY_VIOLATION_BLOCKED",
            "terminal_reason": "destructive_mutation",
            "previous_execution_error": 'column "revenue" does not exist',
        },
    }
    at.run(timeout=RENDER_TIMEOUT)
    assert len(at.exception) == 0

    markdown_texts = [m.value for m in at.markdown]
    info_texts = [i.value for i in at.info]
    error_texts = [e.value for e in at.error]

    # Verify Blocked SQL Label
    assert any("Generated SQL — BLOCKED:" in m for m in markdown_texts)
    assert not any("Final Executed SQL Query:" in m for m in markdown_texts)

    # Verify PostgreSQL: NOT EXECUTED
    assert any("PostgreSQL**: NOT EXECUTED" in i for i in info_texts)
    assert not any("PostgreSQL Execution Error" in e for e in error_texts)

    # Verify Diagnosis & Repair: NOT INVOKED
    assert any("Diagnosis & Repair**: NOT INVOKED" in i for i in info_texts)

    # Verify Previous Failed SQL section displays previous error
    assert any("Prior Attempt Failure:" in c.value for c in at.caption)

