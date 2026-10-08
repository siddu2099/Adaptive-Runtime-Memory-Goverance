"""
ARMG Phase 1C: SQL Extraction Correctness & Validation Test Suite.

Tests the boundary between LLM responses, SQL extraction, and downstream SQLGlot validation:
- Deterministic extraction on valid plain SQL and fenced SQL.
- Strict rejection of natural-language refusals, non-SQL explanations, and non-SQL markdown blocks.
- Distinction between extraction failure, syntax parsing failure, and safety policy violation.
- Full SQLGlot security barrier verification (SELECT, syntax, DDL/DML, multi-statement, transactions).
"""

import pytest
from agents.sql_generator import extract_sql_from_response
from validation.execution_validator import ExecutionValidator, SafetyViolationCategory, validate_sql


# ==============================================================================
# 1. Core Extraction Boundary Tests (Cases A - H, Empty, Whitespace)
# ==============================================================================

def test_case_a_valid_plain_sql():
    """Case A: Valid plain SQL without fences should be extracted directly."""
    raw = "SELECT COUNT(*) FROM orders;"
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT COUNT(*) FROM orders;"
    is_valid, err = validate_sql(extracted)
    assert is_valid is True
    assert err is None


def test_case_b_valid_fenced_sql():
    """Case B: Valid fenced SQL should have code fences removed and content extracted."""
    raw = "```sql\nSELECT COUNT(*) FROM orders;\n```"
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT COUNT(*) FROM orders;"
    is_valid, err = validate_sql(extracted)
    assert is_valid is True


def test_case_c_natural_language_refusal_must_not_be_sql():
    """Case C: Natural-language refusal must NOT be returned as an extracted SQL candidate."""
    raw = "I cannot answer this query because the requested information is unavailable."
    extracted = extract_sql_from_response(raw)
    # Critical invariant: arbitrary non-SQL text must never be returned as extracted SQL
    assert extracted == "", f"Refusal was incorrectly extracted as SQL: {extracted!r}"


def test_case_d_explanation_followed_by_sql():
    """Case D: Natural-language explanation followed by plain SQL should extract only the SQL."""
    raw = "Here is the query you requested:\n\nSELECT COUNT(*) FROM orders;"
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT COUNT(*) FROM orders;"
    is_valid, err = validate_sql(extracted)
    assert is_valid is True


def test_case_e_explanation_with_no_sql_must_not_be_sql():
    """Case E: Natural-language explanation without any SQL must NOT be accepted as SQL."""
    raw = "The query requires information that is not available in the database."
    extracted = extract_sql_from_response(raw)
    assert extracted == "", f"Explanation without SQL was incorrectly extracted as SQL: {extracted!r}"


def test_case_f_invalid_sql_syntax_handling():
    """Case F: Invalid SQL-like text must be rejected by SQLGlot validation."""
    raw = "SELEC COUNT(*) FROM orders;"
    extracted = extract_sql_from_response(raw)
    # Whether extracted or rejected at boundary, downstream validator must reject it
    if extracted:
        is_valid, err = validate_sql(extracted)
        assert is_valid is False
        assert err is not None


def test_case_g_markdown_without_sql_must_not_be_sql():
    """Case G: Markdown fence with 'text' or non-SQL tag must NOT be accepted as SQL."""
    raw = "```text\nI cannot generate the requested query.\n```"
    extracted = extract_sql_from_response(raw)
    assert extracted == "", f"Non-SQL markdown block was incorrectly extracted as SQL: {extracted!r}"


def test_case_h_multiple_fenced_blocks():
    """Case H: Multiple fenced blocks with explanation/result should extract only the SQL block."""
    raw = (
        "Here is the query:\n\n"
        "```sql\n"
        "SELECT COUNT(*) FROM orders;\n"
        "```\n\n"
        "The result should be:\n\n"
        "```text\n"
        "count\n"
        "```"
    )
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT COUNT(*) FROM orders;"
    is_valid, err = validate_sql(extracted)
    assert is_valid is True


def test_empty_response():
    """Empty string response must yield empty extraction."""
    assert extract_sql_from_response("") == ""


def test_none_response():
    """None response must yield empty extraction."""
    assert extract_sql_from_response(None) == ""


def test_whitespace_only_response():
    """Whitespace-only response must yield empty extraction."""
    assert extract_sql_from_response("   \n\t  \n  ") == ""


def test_fenced_sql_with_surrounding_commentary():
    """Fenced SQL surrounded by conversational text before and after."""
    raw = (
        "Sure, I can help with that!\n\n"
        "```sql\n"
        "SELECT user_id, email FROM users WHERE is_active = true;\n"
        "```\n\n"
        "Let me know if you need any further modifications."
    )
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT user_id, email FROM users WHERE is_active = true;"
    is_valid, _ = validate_sql(extracted)
    assert is_valid is True


def test_cte_with_statement_plain():
    """Plain SQL starting with WITH clause (Common Table Expression)."""
    raw = (
        "WITH regional_sales AS (\n"
        "    SELECT region, SUM(amount) AS total FROM sales GROUP BY region\n"
        ")\n"
        "SELECT region, total FROM regional_sales WHERE total > 1000;"
    )
    extracted = extract_sql_from_response(raw)
    assert extracted.startswith("WITH regional_sales AS")
    is_valid, _ = validate_sql(extracted)
    assert is_valid is True


def test_generic_fence_with_valid_sql():
    """Generic ``` fence (no language tag) containing valid SQL should be extracted."""
    raw = "```\nSELECT product_id, product_name FROM dim_product;\n```"
    extracted = extract_sql_from_response(raw)
    assert extracted == "SELECT product_id, product_name FROM dim_product;"
    is_valid, _ = validate_sql(extracted)
    assert is_valid is True


def test_generic_fence_with_natural_language_refusal():
    """Generic ``` fence containing natural language refusal must NOT be extracted as SQL."""
    raw = "```\nSorry, I could not find the relevant tables.\n```"
    extracted = extract_sql_from_response(raw)
    assert extracted == "", f"Refusal in generic fence was extracted as SQL: {extracted!r}"


# ==============================================================================
# 2. Distinction Between Failure Classes (Section 6 & 8)
# ==============================================================================

def test_distinction_extraction_failure_vs_syntax_failure_vs_safety_failure():
    """Verify that extraction failure, syntax error, and safety violation are distinct."""
    # 1. Extraction Failure: Natural language output yields empty string
    refusal = "I am unable to answer this question from the given schema."
    extracted_refusal = extract_sql_from_response(refusal)
    assert extracted_refusal == ""
    # Validator rejects empty payload
    is_valid_empty, err_empty = validate_sql(extracted_refusal)
    assert is_valid_empty is False
    assert "empty" in err_empty.lower()
    is_safety_empty, cat_empty = ExecutionValidator.classify_safety_violation(extracted_refusal)
    assert is_safety_empty is False  # NOT a safety attack
    assert cat_empty is None

    # 2. SQL Syntax Parsing Failure: Candidate extracted, but malformed grammar
    bad_syntax = "SELECT FROM WHERE;"
    is_valid_syn, err_syn = validate_sql(bad_syntax)
    assert is_valid_syn is False
    assert err_syn is not None
    is_safety_syn, cat_syn = ExecutionValidator.classify_safety_violation(bad_syntax)
    # Bad syntax is NOT classified as a destructive safety violation
    assert is_safety_syn is False

    # 3. SQL Safety Failure: Candidate extracted, but contains destructive DDL/DML
    destructive = "DROP TABLE dim_product;"
    is_valid_safe, err_safe = validate_sql(destructive)
    assert is_valid_safe is False
    assert "drop" in err_safe.lower() or "destructive" in err_safe.lower()
    is_safety_safe, cat_safe = ExecutionValidator.classify_safety_violation(destructive)
    assert is_safety_safe is True
    assert cat_safe == SafetyViolationCategory.DESTRUCTIVE_MUTATION


# ==============================================================================
# 3. Comprehensive SQLGlot Security Barrier Verification (Section 7)
# ==============================================================================

@pytest.mark.parametrize("query,expected_valid,expected_safety", [
    # Valid queries
    ("SELECT id, name FROM users;", True, False),
    ("SELECT COUNT(*), AVG(price) FROM products GROUP BY category;", True, False),
    ("WITH cte AS (SELECT * FROM t) SELECT * FROM cte;", True, False),
    ("SELECT a FROM t1 UNION SELECT a FROM t2;", True, False),

    # Invalid Syntax
    ("SELEC id FROM users;", False, False),
    ("SELECT FROM WHERE;", False, False),

    # Destructive DDL / DML Mutations (Must be BLOCKED as safety violations)
    ("DELETE FROM users WHERE id = 1;", False, True),
    ("UPDATE users SET name = 'bad' WHERE id = 1;", False, True),
    ("INSERT INTO users (id, name) VALUES (1, 'bad');", False, True),
    ("DROP TABLE users;", False, True),
    ("ALTER TABLE users ADD COLUMN bad int;", False, True),
    ("TRUNCATE TABLE users;", False, True),
    ("CREATE TABLE bad (id int);", False, True),

    # Multi-statement injection
    ("SELECT 1; SELECT 2;", False, True),
    ("SELECT 1; DROP TABLE users;", False, True),

    # Transaction / Control statements
    ("BEGIN; SELECT 1; COMMIT;", False, True),
    ("ROLLBACK;", False, True),
])
def test_sqlglot_security_barrier(query, expected_valid, expected_safety):
    """Verify that SQLGlot validation and safety classification correctly handle all statement types."""
    is_valid, err = validate_sql(query)
    assert is_valid is expected_valid, f"Validity mismatch for: {query} (err: {err})"

    is_safety, cat = ExecutionValidator.classify_safety_violation(query)
    assert is_safety is expected_safety, f"Safety mismatch for: {query} (cat: {cat})"
