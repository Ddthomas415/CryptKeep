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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.file_utils import atomic_write
from services.os.app_paths import data_dir


def _ohlcv_snapshot_path(venue: str, symbol: str, timeframe: str) -> Path:
    safe_sym = symbol.replace("/", "_").replace(":", "_")
    return data_dir() / "snapshots" / f"ohlcv_{venue}_{safe_sym}_{timeframe}.json"


def _load_local_ohlcv(
    venue: str, symbol: str, *, timeframe: str = "1h", limit: int = 24
) -> list[list]:
    """Load cached OHLCV candles from local snapshot file.

    Returns list of [ts_ms, open, high, low, close, volume] rows,
    newest-first up to `limit` rows.  Returns [] if file absent.
    """
    path = _ohlcv_snapshot_path(venue, symbol, timeframe)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("candles") or []
        return rows[-limit:] if rows else []
    except Exception:
        return []


def write_local_ohlcv_snapshot(
    venue: str,
    symbol: str,
    rows: list[list],
    *,
    timeframe: str = "1h",
    source: str = "unknown",
) -> Path | None:
    """Persist OHLCV rows to the canonical local snapshot path.

    Rows are written as a versioned envelope carrying the actual data source
    (``sample_ohlcv``/``public_ohlcv``/``unknown``) so downstream readers can
    distinguish sample-fed snapshots from public ones (backlog #21 remaining
    work: sample rows must not launder into public provenance through the
    snapshot store). ``_load_local_ohlcv`` already reads both the legacy bare
    list and the ``candles`` envelope, so this is backward compatible.

    Returns the written path, or ``None`` when rows are empty or invalid.
    """
    clean_rows = [list(row) for row in rows if isinstance(row, (list, tuple)) and len(row) >= 6]
    if not clean_rows:
        return None
    path = _ohlcv_snapshot_path(venue, symbol, timeframe)
    source_label = str(source or "unknown").strip() or "unknown"
    try:
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_rows = existing if isinstance(existing, list) else existing.get("candles") or []
            existing_source = (
                "unknown" if isinstance(existing, list) else str(existing.get("source") or "unknown")
            )
            if existing_rows == clean_rows and existing_source == source_label:
                return path
    except Exception:
        pass
    payload = json.dumps(
        {
            "version": 2,
            "source": source_label,
            "written_ts": datetime.now(timezone.utc).isoformat(),
            "candles": clean_rows,
        },
        indent=2,
    )
    atomic_write(path, payload, encoding="utf-8")
    return path


def load_local_ohlcv_snapshot_provenance(
    venue: str, symbol: str, *, timeframe: str = "1h"
) -> dict[str, Any]:
    """Read-only provenance for a local OHLCV snapshot without loading rows
    into the caller's data path.

    ``legacy=True`` marks pre-envelope bare-list snapshots (source unknown).
    Corrupt files report ``exists=True, source="unknown", legacy=True`` so a
    reader asserting public ancestry fails closed rather than assuming.
    """
    path = _ohlcv_snapshot_path(venue, symbol, timeframe)
    out: dict[str, Any] = {
        "path": str(path),
        "exists": False,
        "source": "unknown",
        "legacy": True,
        "written_ts": None,
        "row_count": 0,
    }
    if not path.exists():
        return out
    out["exists"] = True
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return out
    if isinstance(raw, list):
        out["row_count"] = len(raw)
        return out
    if isinstance(raw, dict):
        out["legacy"] = False
        out["source"] = str(raw.get("source") or "unknown").strip() or "unknown"
        out["written_ts"] = raw.get("written_ts")
        candles = raw.get("candles")
        out["row_count"] = len(candles) if isinstance(candles, list) else 0
    return out


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
