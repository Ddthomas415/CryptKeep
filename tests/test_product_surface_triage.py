from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

RETAIN_NOW = {
    "paper evidence collection",
    "promotion gates",
    "shadow would-be-fill evidence",
    "archive-first backtesting",
    "crypto-edge data collection",
    "operator status/alerting",
    "backup/restore and recovery proof",
}

DEFER = {
    "cross-platform desktop packaging",
    "public onboarding/product polish",
    "non-operator-critical dashboard pages",
    "broad multi-exchange product claims",
    "automated strategy selection beyond read-only proposal/advisory mode",
}

DECISION_RULE_TERMS = {
    "evidence velocity",
    "profitability discovery",
    "cost measurement",
    "safety",
    "recovery",
    "operator wake-up quality",
}


def test_product_surface_triage_preserves_lab_mode_priority_lists() -> None:
    doc = (REPO / "docs/PRODUCT_SURFACE_TRIAGE.md").read_text(encoding="utf-8")
    assert "CryptKeep remains in lab-mode concentration until expectancy is proven" in doc
    for item in sorted(RETAIN_NOW):
        assert f"- {item}" in doc
    for item in sorted(DEFER):
        assert f"- {item}" in doc


def test_product_surface_triage_preserves_decision_rule_and_identity_link() -> None:
    doc = (REPO / "docs/PRODUCT_SURFACE_TRIAGE.md").read_text(encoding="utf-8")
    normalized = " ".join(doc.split())
    for term in sorted(DECISION_RULE_TERMS):
        assert term in normalized
    assert "`docs/PROJECT_IDENTITY_AND_SCOPE.md`" in doc


def test_root_readme_matches_product_surface_boundary() -> None:
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "profit-measurement and evidence-generation lab" in readme
    assert "not part of the required local production baseline" in readme
    assert "src-tauri" in readme
