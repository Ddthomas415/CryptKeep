"""
services/market_data/local_data_reader.py

Canonical location for reading local market data snapshots and OHLCV files.

Previously these functions lived in dashboard/services/views/_shared_market.py
and were imported by service-layer code, creating an illegal services→dashboard
dependency. They now live here in the service layer.

Dashboard code imports from here via dashboard/services/views/_shared_market.py
which re-exports these names.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir


def _load_local_ohlcv(
    venue: str, symbol: str, *, timeframe: str = "1h", limit: int = 24
) -> list[list]:
    """Load cached OHLCV candles from local snapshot file.

    Returns list of [ts_ms, open, high, low, close, volume] rows,
    newest-first up to `limit` rows.  Returns [] if file absent.
    """
    safe_sym = symbol.replace("/", "_").replace(":", "_")
    path = data_dir() / "snapshots" / f"ohlcv_{venue}_{safe_sym}_{timeframe}.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("candles") or []
        return rows[-limit:] if rows else []
    except Exception:
        return []


def _get_market_snapshot(
    asset: str, *, exchange: str = "coinbase"
) -> dict[str, Any] | None:
    """Load the latest market snapshot for an asset from local file."""
    safe_asset = asset.replace("/", "_").replace(":", "_")
    path = data_dir() / "snapshots" / f"market_{exchange}_{safe_asset}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_settings_view() -> dict[str, Any]:
    """Load the latest settings snapshot from local file.

    Returns an empty dict if no snapshot is available.
    This is the canonical service-layer path for reading settings state.
    Dashboard-layer callers should use dashboard/services/views/settings_view.py.
    """
    path = data_dir() / "snapshots" / "settings.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
