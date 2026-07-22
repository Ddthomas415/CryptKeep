from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

OPERATOR_CRITICAL_SURFACES = {
    "gate status": [
        "dashboard/services/promotion_ladder.py",
        "dashboard/services/strategy_evidence_runtime.py",
    ],
    "paper reconciliation": [
        "dashboard/pages/44_Paper_Reconciliation.py",
        "services/execution/paper_reconciliation.py",
    ],
    "campaign health": [
        "dashboard/pages/60_Operations.py",
        "scripts/report_paper_campaign_status.py",
    ],
    "market movers / candidate context": [
        "dashboard/pages/37_Coinbase_Movers.py",
        "dashboard/pages/36_Symbol_Scanner.py",
    ],
    "AI/copilot advisory reports": [
        "dashboard/pages/65_Copilot_Reports.py",
        "dashboard/services/copilot_reports.py",
    ],
    "kill switch and halted-state visibility": [
        "dashboard/pages/60_Operations.py",
        "dashboard/services/operator.py",
    ],
}


def test_dashboard_data_page_backlog_maps_operator_critical_surfaces() -> None:
    doc = (REPO / "docs/dashboard/DATA_PAGE_BACKLOG.md").read_text(encoding="utf-8")
    for label, paths in OPERATOR_CRITICAL_SURFACES.items():
        assert label in doc
        for rel in paths:
            assert (REPO / rel).exists(), rel
            assert f"`{rel}`" in doc


def test_dashboard_data_page_backlog_preserves_mutation_boundary() -> None:
    doc = (REPO / "docs/dashboard/DATA_PAGE_BACKLOG.md").read_text(encoding="utf-8")
    assert "Any dashboard page that can mutate state must keep explicit role guards" in doc
    assert "must not bypass accepted CLI/runbook ceremonies for high-risk actions" in doc
