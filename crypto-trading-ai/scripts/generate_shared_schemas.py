#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "shared" / "schemas"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.schemas.audit import AuditEventListResponse
from backend.app.schemas.connections import ExchangeConnectionListResponse
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.schemas.research import ExplainResponse
from backend.app.schemas.risk import RiskSummary
from backend.app.schemas.settings import SettingsPayload
from backend.app.schemas.terminal import TerminalExecuteResponse
from backend.app.schemas.trading import RecommendationList

SCHEMA_TARGETS = {
    "audit.schema.json": AuditEventListResponse,
    "connections.schema.json": ExchangeConnectionListResponse,
    "dashboard.schema.json": DashboardSummary,
    "research.schema.json": ExplainResponse,
    "risk.schema.json": RiskSummary,
    "settings.schema.json": SettingsPayload,
    "terminal.schema.json": TerminalExecuteResponse,
    "trading.schema.json": RecommendationList,
}


def generate_schema_document(model: type) -> dict[str, Any]:
    document = model.model_json_schema()
    document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return document


def sync_schemas(check_only: bool = False) -> int:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    drifted: list[str] = []

    for filename, model in SCHEMA_TARGETS.items():
        target = SCHEMA_DIR / filename
        generated = generate_schema_document(model)

        if not target.exists():
            if check_only:
                drifted.append(filename)
                continue
            target.write_text(json.dumps(generated, indent=2, sort_keys=False) + "\n", encoding="utf-8")
            print(f"created {filename}")
            continue

        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing != generated:
            if check_only:
                drifted.append(filename)
            else:
                target.write_text(json.dumps(generated, indent=2, sort_keys=False) + "\n", encoding="utf-8")
                print(f"updated {filename}")

    if check_only and drifted:
        print("Shared schemas are out of date:")
        for name in drifted:
            print(f" - {name}")
        print("Run: python scripts/generate_shared_schemas.py")
        return 1

    if check_only:
        print("Shared schemas are in sync.")
    else:
        print("Shared schemas generated.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate shared JSON schemas from backend Pydantic models.")
    parser.add_argument("--check", action="store_true", help="Fail if schemas are not in sync.")
    args = parser.parse_args()
    return sync_schemas(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
