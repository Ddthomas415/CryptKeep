from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stock_options_backlog_preserves_research_only_boundary() -> None:
    text = (REPO_ROOT / "REMAINING_TASKS.md").read_text(encoding="utf-8")
    compact = " ".join(text.split())

    assert "Define stock-options requirements before any equities/options data" in text
    assert "OCC/ODD disclosure" in text
    assert "OPRA" in text
    assert "assignment/exercise" in text
    assert "read-only research artifact generation" in text
    assert "no stock/options\n    order routing" in text
    assert "can run in parallel with crypto only as an isolated read-only lane" in compact
