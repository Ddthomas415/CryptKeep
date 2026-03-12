#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.schemas.connections import ExchangeConnectionListResponse
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.schemas.research import ExplainResponse
from backend.app.schemas.risk import RiskSummary
from backend.app.schemas.settings import SettingsPayload

MOCK_DIR = ROOT / "shared" / "mock-data"

MOCK_TARGETS = {
    "dashboard.json": DashboardSummary,
    "explain-sol.json": ExplainResponse,
    "exchanges.json": ExchangeConnectionListResponse,
    "settings.json": SettingsPayload,
    "risk-summary.json": RiskSummary,
}


def validate_mock_payload(filename: str, model: type) -> None:
    path = MOCK_DIR / filename
    payload = json.loads(path.read_text(encoding="utf-8"))

    required_top = {"request_id", "status", "data", "error", "meta"}
    if not required_top.issubset(payload.keys()):
        missing = sorted(required_top - set(payload.keys()))
        raise ValueError(f"{filename}: missing envelope keys {missing}")

    if payload["status"] != "success":
        raise ValueError(f"{filename}: expected status=success, got {payload['status']!r}")
    if payload["error"] is not None:
        raise ValueError(f"{filename}: expected error=None, got {payload['error']!r}")
    if not isinstance(payload["meta"], dict):
        raise ValueError(f"{filename}: expected meta to be an object")

    model.model_validate(payload["data"])


def main() -> int:
    for filename, model in MOCK_TARGETS.items():
        validate_mock_payload(filename, model)
        print(f"validated {filename}")
    print("All shared mock-data files are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
