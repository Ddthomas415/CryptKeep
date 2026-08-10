from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DOC = "docs/CURRENT_SYSTEM_DIAGRAM.md"


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_current_system_diagram_preserves_identity_and_authority_boundary() -> None:
    text = _normalized(DOC)

    required = {
        "evidence-first crypto trading research and operations system",
        "profitability and live capital reliability are not proven",
        "BTC/USDT paper gate is one validation track",
        "not the full project identity",
        "deterministic trading/risk engine is the only authority allowed to move capital",
        "AI, research, archive, dashboard, and roadmap layers are advisory",
    }

    for phrase in required:
        assert phrase in text


def test_current_system_diagram_names_major_repo_layers() -> None:
    text = _text(DOC)

    for layer in (
        "Operator / User Layer",
        "AI / Research Advisory Layer",
        "Crypto Market Data",
        "Normalization / Provenance Layer",
        "State And Evidence Stores",
        "Research And Analytics Layer",
        "Strategy Runtime Layer",
        "Paper Execution Layer",
        "Shadow / Would-Be-Fill Layer",
        "Deterministic Risk Engine",
        "Execution Boundary",
    ):
        assert layer in text


def test_current_system_diagram_keeps_multi_asset_scope_bounded() -> None:
    text = _normalized(DOC)

    assert "Not the project identity and not proof that only BTC can be used" in text
    assert "Stocks/options" in text
    assert "Read-only research only until requirements" in text
    assert "no governed broker/data/execution scope is active" in text
    assert "new asset classes as isolated read-only research" in text


def test_current_system_diagram_is_linked_from_architecture_and_roadmap() -> None:
    for rel in ("docs/ARCHITECTURE.md", "docs/ROADMAP_TRACKING_CHECKLIST.md"):
        assert DOC in _text(rel), rel
