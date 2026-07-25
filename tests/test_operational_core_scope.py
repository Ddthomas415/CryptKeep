from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

CORE_SURFACES = {
    "services/control/",
    "services/strategies/",
    "services/execution/",
    "services/analytics/",
    "services/risk/",
    "services/admin/",
    "services/security/",
    "services/signals/",
    "services/market_data/",
    "storage/",
    "scripts/",
    "dashboard/",
    "configs/",
    "config/",
}

QUARANTINE_STATES = {
    "core",
    "research_only",
    "advisory_only",
    "compatibility",
    "retired",
    "sidecar",
}

CORE_PRIORITIES = {
    "evidence velocity",
    "profitability discovery",
    "cost measurement",
    "safety",
    "recovery",
    "operator wake-up quality",
}

CLASSIFICATION_RECORDS = {
    "docs/architecture/paper_execution_surfaces.md",
    "docs/architecture/safety_surface_classification.md",
    "docs/architecture/storage_surface_classification.md",
    "docs/architecture/websocket_surface_classification.md",
    "docs/research/signal_discovery_classification.md",
    "docs/BACKLOG_EXECUTION_LANES.md",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_operational_core_doc_preserves_current_core_surfaces() -> None:
    text = _text("docs/CORE.md")

    for surface in CORE_SURFACES:
        assert f"`{surface}`" in text


def test_operational_core_doc_preserves_quarantine_policy() -> None:
    text = _text("docs/CORE.md")

    assert "Do not delete or move broad surfaces in one sweep." in text
    for state in QUARANTINE_STATES:
        assert f"`{state}`" in text


def test_operational_core_doc_preserves_priority_rule() -> None:
    text = _text("docs/CORE.md")

    assert "New functionality should land in the core only when it directly improves one of:" in text
    for priority in CORE_PRIORITIES:
        assert priority in text
    assert "Otherwise it belongs in research/advisory scope or should be deferred." in text


def test_operational_core_classification_records_exist_and_are_linked() -> None:
    text = _text("docs/CORE.md")

    for rel in CLASSIFICATION_RECORDS:
        assert f"`{rel}`" in text
        assert (REPO / rel).is_file(), rel
