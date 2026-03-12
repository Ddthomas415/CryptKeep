from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.schemas.connections import ConnectionRecord
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.schemas.settings import SettingsPayload

ROOT = Path(__file__).resolve().parents[3] / "shared" / "mock-data"


def _load(name: str) -> Any:
    return json.loads((ROOT / name).read_text())


def load_dashboard() -> DashboardSummary:
    return DashboardSummary(**_load("dashboard.json"))


def load_exchanges() -> list[ConnectionRecord]:
    payload = _load("exchanges.json")
    return [ConnectionRecord(**x) for x in payload["items"]]


def load_settings() -> SettingsPayload:
    return SettingsPayload(**_load("settings.json"))


def load_risk_summary() -> dict[str, Any]:
    return _load("risk-summary.json")


def load_explain_template() -> dict[str, Any]:
    return _load("explain-sol.json")


def load_audit_events() -> list[dict[str, Any]]:
    return [
        {
            "id": "audit_1",
            "timestamp": "2026-03-11T13:00:12Z",
            "service": "orchestrator",
            "action": "explain_asset",
            "result": "success",
            "request_id": "req_123",
            "details": "Generated explanation for SOL",
        },
        {
            "id": "audit_2",
            "timestamp": "2026-03-11T13:02:12Z",
            "service": "risk_engine",
            "action": "evaluate_trade",
            "result": "blocked",
            "request_id": "req_124",
            "details": "Execution disabled in research mode",
        },
    ]


SETTINGS_STATE = load_settings()
EXCHANGES_STATE = load_exchanges()
