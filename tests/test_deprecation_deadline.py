"""tests/test_deprecation_deadline.py

Enforces the 2026-08-01 deprecation deadline for transitional service families.

If this test fails, it means the deadline has passed and the deprecated code
must be removed from the listed transitional families.

If the deadline needs to be extended, update the date here AND add a decision
record in docs/strategies/ explaining why.
"""
from __future__ import annotations

import pytest
from datetime import date
from pathlib import Path


DEPRECATION_DEADLINE = date(2026, 8, 1)
DEPRECATED_FAMILIES = []
RETIRED_FAMILIES = [
    "services/paper",
    "services/marketdata",
    "services/strategy",
    "services/strategy_runner",
]


def _tracked_family_python_files(family: str) -> list[str]:
    root = Path(family)
    if not root.exists():
        return []
    return [
        str(path)
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    ]


def test_retired_families_stay_removed():
    """Prevent retired compatibility packages from being reintroduced."""
    present = {
        family: files
        for family in RETIRED_FAMILIES
        if (files := _tracked_family_python_files(family))
    }

    assert not present, (
        "Retired compatibility families must not contain Python files. "
        f"Found: {present}\n"
        "Use docs/architecture/transitional_service_families.md for canonical replacements."
    )


def test_deprecation_deadline_not_passed():
    """Fail loudly if the deprecation deadline has passed without removal."""
    today = date.today()
    if today < DEPRECATION_DEADLINE:
        pytest.skip(f"Deadline not yet reached ({today} < {DEPRECATION_DEADLINE})")

    still_present = [
        d for d in DEPRECATED_FAMILIES
        if (Path(d)).exists() and list(Path(d).glob("*.py"))
    ]

    assert not still_present, (
        f"Deprecation deadline {DEPRECATION_DEADLINE} has passed. "
        f"These families must be removed: {still_present}\n"
        f"See docs/architecture/transitional_service_families.md for migration guidance."
    )


def test_deprecated_families_have_deprecation_warnings():
    """Each deprecated family must have a DeprecationWarning in __init__.py."""
    today = date.today()
    if today >= DEPRECATION_DEADLINE:
        pytest.skip("Past deadline — handled by test_deprecation_deadline_not_passed")

    for family in DEPRECATED_FAMILIES:
        init = Path(family) / "__init__.py"
        if not init.exists():
            continue
        content = init.read_text()
        assert "DeprecationWarning" in content or "deprecated" in content.lower(), (
            f"{init} missing DeprecationWarning — all deprecated families must "
            f"warn on import so callers know to migrate"
        )
