from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repo_layout_mentions_phase1_companion_scope() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "phase1_research_copilot/" in txt
    assert "actively referenced from the main README, Makefile, dashboard research fallback, and tests" in txt


def test_repo_layout_mentions_crypto_trading_ai_as_sidecar_workspace() -> None:
    txt = (ROOT / "docs" / "REPO_LAYOUT.md").read_text(encoding="utf-8", errors="replace")
    assert "crypto-trading-ai/" in txt
    assert "treat as sidecar workspace unless a stronger product-scope decision is documented elsewhere" in txt
