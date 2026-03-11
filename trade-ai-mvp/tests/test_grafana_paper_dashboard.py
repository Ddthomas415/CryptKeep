from __future__ import annotations

import json
from pathlib import Path


def test_grafana_dashboard_has_paper_trading_panels():
    path = Path(__file__).resolve().parents[1] / "infra" / "grafana" / "dashboards" / "trade_ai_overview.json"
    payload = json.loads(path.read_text())
    titles = {panel.get("title") for panel in payload.get("panels", [])}
    assert "Paper Trading" in titles
    assert "Paper Positions" in titles
    assert "Recent Paper Fills" in titles
    assert "Paper Risk State" in titles
    assert "Paper Readiness" in titles
