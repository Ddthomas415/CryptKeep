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


def test_stock_options_requirements_doc_preserves_execution_boundary() -> None:
    text = (REPO_ROOT / "docs/research/stock_options_requirements.md").read_text(encoding="utf-8")
    compact = " ".join(text.split())

    assert "requirements boundary only" in text
    assert "No equities/options data integration" in text
    assert "Can stock/options research run in parallel with crypto? | Yes, only as an isolated read-only research lane." in text
    assert "Can stock/options execution run in parallel with crypto? | No" in text
    assert "Can stock/options evidence count toward the crypto paper gate? | No." in text
    assert "OPRA or vendor data entitlement" in text
    assert "OSI/OCC option symbology parser" in text
    assert "Assignment, exercise, early-exercise, expiration, pin risk" in text
    assert "No stock/options order routing." in text
    assert "No shared risk budget with crypto." in text
    assert "not_campaign_evidence" in compact
