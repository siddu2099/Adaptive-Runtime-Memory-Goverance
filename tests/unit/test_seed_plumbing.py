"""
Unit tests for deterministic seed plumbing in LLM generation requests.
Per Audit 1 Remediation Item REM-P0-03.
"""

from unittest.mock import MagicMock, patch
import pytest
from agents.sql_generator import SQLGenerator
from agents.repair_agent import RepairSQLGenerator


def test_sql_generator_seed_plumbing_when_specified():
    """Verify that when seed is provided, options['seed'] is included in Ollama payload."""
    generator = SQLGenerator(seed=42)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT 1;\n```",
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = generator.generate("What is total revenue?", "## fact_sales_performance")

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "options" in payload
        assert payload["options"]["temperature"] == 0.0
        assert payload["options"]["seed"] == 42
        assert res.extracted_sql == "SELECT 1;"


def test_sql_generator_no_seed_when_unspecified():
    """Verify that when seed is None, options['seed'] is omitted from Ollama payload."""
    generator = SQLGenerator(seed=None)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT 1;\n```",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        generator.generate("What is total revenue?", "## fact_sales_performance")

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "options" in payload
        assert "seed" not in payload["options"]


def test_repair_generator_seed_plumbing_when_specified():
    """Verify that when seed is provided to RepairSQLGenerator, options['seed'] is included."""
    repair_gen = RepairSQLGenerator(seed=999)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT repaired_col FROM fact_sales_performance;\n```",
            "prompt_eval_count": 20,
            "eval_count": 8,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        res = repair_gen.generate_repair("[STRICT REPAIR CONSTRAINTS]\nUse repaired_col")

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "options" in payload
        assert payload["options"]["temperature"] == 0.0
        assert payload["options"]["seed"] == 999
        assert "repaired_col" in res.extracted_sql


def test_repair_generator_no_seed_when_unspecified():
    """Verify that when seed is None, options['seed'] is omitted in RepairSQLGenerator."""
    repair_gen = RepairSQLGenerator(seed=None)

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "```sql\nSELECT 1;\n```",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        repair_gen.generate_repair("prompt")

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]

        assert "options" in payload
        assert "seed" not in payload["options"]
