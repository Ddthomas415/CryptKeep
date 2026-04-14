from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from dashboard.services.intelligence import build_opportunity_snapshot
from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml
from services.execution.live_arming import set_live_enabled
from services.setup.config_manager import DEFAULT_CFG, deep_merge

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
PHASE1_ORCHESTRATOR_URL = os.environ.get("CK_PHASE1_ORCHESTRATOR_URL", "http://localhost:8002").rstrip("/")
PHASE1_SERVICE_TOKEN = (
    os.environ.get("CK_PHASE1_SERVICE_TOKEN")
    or os.environ.get("SERVICE_TOKEN")
    or ""
).strip()
API_TIMEOUT_SECONDS = float(os.environ.get("CK_API_TIMEOUT_SECONDS", "0.6"))


def _attach_data_provenance(
    payload: dict[str, Any],
    *,
    source: str,
    fallback: bool,
    message: str,
) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["data_provenance"] = {
        "source": str(source),
        "fallback": bool(fallback),
        "message": str(message).strip(),
    }
    return enriched


def _derive_volume_trend(change_24h_pct: float) -> str:
    magnitude = abs(change_24h_pct)
    if magnitude >= 5.0:
        return "high"
    if magnitude >= 2.0:
        return "elevated"
    return "steady"


def _normalize_asset_symbol(value: Any) -> str:
    symbol = str(value or "").strip().upper()
    if not symbol:
        return ""
    if "/" in symbol:
        return symbol.split("/", 1)[0]
    if "-" in symbol:
        return symbol.split("-", 1)[0]
    for suffix in ("USDT", "USDC", "USD", "PERP"):
        if symbol.endswith(suffix) and len(symbol) > len(suffix):
            return symbol[: -len(suffix)]
    return symbol


def _extract_close_series(rows: Any) -> list[float]:
    if not isinstance(rows, list):
        return []

    series: list[float] = []
    for row in rows:
        close_value: Any | None = None
        if isinstance(row, dict):
            close_value = row.get("close")
        elif isinstance(row, (list, tuple)) and len(row) >= 5:
            close_value = row[4]

        try:
            close_price = round(float(close_value), 2)
        except (TypeError, ValueError):
            continue

        if close_price > 0:
            series.append(close_price)
    return series


