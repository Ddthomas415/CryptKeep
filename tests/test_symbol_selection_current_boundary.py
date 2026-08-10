from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/strategies/symbol_selection_current_boundary.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_symbol_selection_boundary_preserves_current_rule() -> None:
    text = _normalized(DOC)

    assert "canonical paper campaigns do not automatically choose new trade symbols at runtime" in text
    assert "Current campaign symbols come from explicit configuration and manifests" in text
    assert "Automatic symbol selection is not allowed to become promotion evidence" in text
    assert "paper campaign authority, or live execution authority" in text


def test_symbol_selection_boundary_classifies_existing_surfaces() -> None:
    text = _text(DOC)

    for surface in (
        "services/signals/universe_loader.py",
        "scripts/data/run_candidate_scan.py",
        "scripts/plan_multi_symbol_paper_campaigns.py",
        "services/runtime/dynamic_symbol_selector.py",
        "services/analytics/multi_symbol_paper_campaign_generator.py",
    ):
        assert surface in text

    assert "Research/planning input only" in text
    assert "Does not mutate active manifests or start campaigns" in text
    assert "Not current canonical promotion authority" in text


def test_symbol_selection_boundary_answers_btc_and_auto_selection_questions() -> None:
    text = _normalized(DOC)

    assert "not proof that the repo can only use BTC" in text
    assert "It does not automatically select canonical promotion or live-trading symbols." in text
    assert "Current campaigns trade configured symbols." in text
    assert "read-only candidate" in text
    assert "multi-symbol planning tools" in text
    assert "proposals can change active campaigns" in text
    assert "count toward promotion" in text


def test_symbol_selection_boundary_is_linked_from_current_diagram_and_roadmap() -> None:
    for rel in ("docs/CURRENT_SYSTEM_DIAGRAM.md", "docs/ROADMAP_TRACKING_CHECKLIST.md"):
        assert DOC in _text(rel), rel
