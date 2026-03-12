from __future__ import annotations

from dashboard.components.activity import normalize_activity_items


def test_normalize_activity_items_trims_and_limits_values() -> None:
    rows = normalize_activity_items(
        [" Generated explanation for SOL ", "", None, "Health check passed", "Third item"],
        limit=2,
    )
    assert rows == ["Generated explanation for SOL", "Health check passed"]


def test_normalize_activity_items_handles_empty_input() -> None:
    assert normalize_activity_items([], limit=6) == []
    assert normalize_activity_items(None, limit=6) == []
