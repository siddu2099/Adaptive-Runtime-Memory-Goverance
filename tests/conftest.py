"""
Pytest configuration for ARMG test suite.
Phase 3 Test Architecture Implementation.

Enforces:
1. Repository root on sys.path.
2. Explicit marker tagging:
   - tests/unit/ -> @pytest.mark.unit (hermetic, offline, zero services)
   - tests/integration/ -> @pytest.mark.integration (requires live services)
   - tests/test_env.py -> @pytest.mark.environment (diagnostic verification)
"""

import sys
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def pytest_collection_modifyitems(config, items):
    """Automatically tag tests with unit, integration, or environment markers based on location."""
    for item in items:
        fspath = str(item.fspath).replace("\\", "/")
        if "/tests/unit/" in fspath:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in fspath:
            item.add_marker(pytest.mark.integration)
        elif "test_env.py" in fspath:
            item.add_marker(pytest.mark.environment)
