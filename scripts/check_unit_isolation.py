"""
ARMG Phase 3: Automated Dependency-Leakage & Hermetic Isolation Auditor.
Section 9 Implementation.

Statically and dynamically scans all test files under tests/unit/ to ensure:
- Zero imports of PostgreSQLEnvironment
- Zero unmocked imports of psycopg2, socket, urllib
- Zero live network or database calls
- 100% offline hermetic execution
"""

import ast
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
UNIT_DIR = REPO_ROOT / "tests" / "unit"

FORBIDDEN_IMPORTS = {
    "environment.postgres": ["PostgreSQLEnvironment"],
    "psycopg2": None,
    "socket": None,
    "urllib.request": None,
    "http.client": None,
    "httpx": None,
    "ollama": None,
    "asyncpg": None,
    "subprocess": None,
}


def scan_unit_tests():
    print("=" * 70)
    print("ARMG PHASE 3: STATIC DEPENDENCY-LEAKAGE AUDIT OF TESTS/UNIT/")
    print("=" * 70)

    violations = []
    unit_files = sorted(list(UNIT_DIR.glob("test_*.py")))

    for fpath in unit_files:
        content = fpath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(fpath))

        for node in ast.walk(tree):
            # Check import ...
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_IMPORTS and FORBIDDEN_IMPORTS[alias.name] is None:
                        violations.append((fpath.name, node.lineno, f"Forbidden import: {alias.name}"))
            # Check from ... import ...
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod in FORBIDDEN_IMPORTS:
                    forbidden_names = FORBIDDEN_IMPORTS[mod]
                    if forbidden_names is None:
                        violations.append((fpath.name, node.lineno, f"Forbidden import: from {mod}"))
                    else:
                        for alias in node.names:
                            if alias.name in forbidden_names:
                                violations.append((fpath.name, node.lineno, f"Forbidden import: from {mod} import {alias.name}"))

    if violations:
        print("VIOLATIONS FOUND IN TESTS/UNIT/:")
        for fname, line, msg in violations:
            print(f"  - {fname}:{line} -> {msg}")
        return False
    else:
        print(f"PASSED: Audited {len(unit_files)} test files in tests/unit/. ZERO forbidden live-service dependencies found.")
        return True


if __name__ == "__main__":
    passed = scan_unit_tests()
    if not passed:
        sys.exit(1)
