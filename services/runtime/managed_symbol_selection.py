from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from services.os.app_paths import runtime_dir
from services.os.file_utils import atomic_write
from services.runtime.dynamic_symbol_selector import select_symbols
from services.runtime.managed_symbol_config import normalize_symbols, resolve_managed_symbols

_TERMINAL_INTENT_STATUSES = {"filled", "cancelled", "canceled", "rejected", "closed", "error"}
_DEFAULT_PRESERVE_INTENT_STATUSES = ("queued", "submitting", "submitted")
_DEFAULT_POSITION_MAX_AGE_SEC = 7 * 24 * 60 * 60
_DEFAULT_INTENT_MAX_AGE_SEC = 24 * 60 * 60


def _unique_symbols(symbols: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in symbols:
        sym = str(item or "").strip().upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        out.append(sym)
    return out


def _iso_to_epoch(ts: Any) -> float | None:
    txt = str(ts or "").strip()
    if not txt:
        return None
    try:
        return datetime.fromisoformat(txt.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _age_sec(ts: Any, *, now_epoch: float) -> float | None:
    epoch = _iso_to_epoch(ts)
    if epoch is None:
        return None
    return max(0.0, float(now_epoch) - float(epoch))


def _age_allowed(age_sec: float | None, *, max_age_sec: float) -> bool:
    if max_age_sec <= 0:
        return True
    if age_sec is None:
        return False
    return age_sec <= max_age_sec


def _preserve_intent_statuses(managed: dict[str, Any]) -> set[str]:
    raw = managed.get("preserve_intent_statuses")
    if isinstance(raw, (list, tuple, set)):
        values = [str(x or "").strip().lower() for x in raw]
    else:
        values = list(_DEFAULT_PRESERVE_INTENT_STATUSES)
    return {v for v in values if v}


def _protected_symbol_details(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}
    for row in details:
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        entry = index.get(symbol)
        if entry is None:
            entry = {"symbol": symbol, "reasons": []}
            index[symbol] = entry
            merged.append(entry)
        reason = {k: v for k, v in row.items() if k != "symbol"}
        entry["reasons"].append(reason)
    return merged


def _busy_paper_symbol_details(*, venue: str, managed: dict[str, Any]) -> list[dict[str, Any]]:
    from storage.intent_queue_sqlite import IntentQueueSQLite
    from storage.paper_trading_sqlite import PaperTradingSQLite

    details: list[dict[str, Any]] = []
    now_epoch = time.time()
    position_max_age_sec = float(managed.get("preserve_position_max_age_sec", _DEFAULT_POSITION_MAX_AGE_SEC) or _DEFAULT_POSITION_MAX_AGE_SEC)
    intent_max_age_sec = float(managed.get("preserve_intent_max_age_sec", _DEFAULT_INTENT_MAX_AGE_SEC) or _DEFAULT_INTENT_MAX_AGE_SEC)
    intent_statuses = _preserve_intent_statuses(managed)
    venue_norm = str(venue or "").strip().lower()

    try:
        positions = PaperTradingSQLite().list_positions(limit=500)
        for row in positions:
            try:
                qty = float(row.get("qty") or 0.0)
            except Exception:
                continue
            if abs(qty) <= 0.0:
                continue
            age_sec = _age_sec(row.get("updated_ts"), now_epoch=now_epoch)
            if not _age_allowed(age_sec, max_age_sec=position_max_age_sec):
                continue
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            detail = {
                "symbol": symbol,
                "source": "paper_position",
                "qty": qty,
                "updated_ts": row.get("updated_ts"),
            }
            if age_sec is not None:
                detail["age_sec"] = round(age_sec, 3)
            details.append(detail)
    except Exception:
        pass

    try:
        intents = IntentQueueSQLite().list_intents(limit=1000)
        for row in intents:
            status = str(row.get("status") or "").strip().lower()
            if status in _TERMINAL_INTENT_STATUSES or status not in intent_statuses:
                continue
            row_venue = str(row.get("venue") or "").strip().lower()
            if venue_norm and row_venue and row_venue != venue_norm:
                continue
            ts = row.get("updated_ts") or row.get("created_ts") or row.get("ts")
            age_sec = _age_sec(ts, now_epoch=now_epoch)
            if not _age_allowed(age_sec, max_age_sec=intent_max_age_sec):
                continue
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            detail = {
                "symbol": symbol,
                "source": "intent_queue",
                "status": status,
                "intent_id": row.get("intent_id"),
                "updated_ts": row.get("updated_ts"),
            }
            if row.get("created_ts"):
                detail["created_ts"] = row.get("created_ts")
            if age_sec is not None:
                detail["age_sec"] = round(age_sec, 3)
            details.append(detail)
    except Exception:
        pass

    return details


def _scan_cache_path():
    return runtime_dir() / "health" / "managed_symbol_selection.json"


def _scan_criteria(managed: dict[str, Any]) -> dict[str, float | int]:
    return {
        "top_n": int(managed.get("top_n", 2) or 2),
        "min_hot_score": float(managed.get("min_hot_score", 25.0) or 25.0),
        "min_change_pct": float(managed.get("min_change_pct", 2.5) or 2.5),
        "min_volume_24h": float(managed.get("min_volume_24h", 100000.0) or 100000.0),
    }


def _read_scan_cache(*, venue: str, criteria: dict[str, float | int], refresh_sec: float) -> dict[str, Any] | None:
    if refresh_sec <= 0:
        return None
    path = _scan_cache_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        age = time.time() - float(payload.get("ts_epoch") or 0.0)
    except Exception:
        return None
    if age < 0 or age > refresh_sec:
        return None
    if str(payload.get("venue") or "").strip().lower() != str(venue or "").strip().lower():
        return None
    if payload.get("criteria") != criteria:
        return None
    return payload


def _write_scan_cache(payload: dict[str, Any]) -> None:
    path = _scan_cache_path()
    try:
        atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except Exception:
        pass


def _scan_symbol_candidates(*, venue: str, managed: dict[str, Any]) -> dict[str, Any]:
    criteria = _scan_criteria(managed)
    refresh_sec = float(managed.get("refresh_sec", 300.0) or 300.0)
    cached = _read_scan_cache(venue=venue, criteria=criteria, refresh_sec=refresh_sec)
    if cached is not None:
        return {
            "ok": bool(cached.get("ok")),
            "selected": _unique_symbols(normalize_symbols(cached.get("selected") or [])),
            "source": cached.get("source"),
            "ts": cached.get("scan_ts"),
            "errors": list(cached.get("errors") or []),
            "cached": True,
        }

    scan = select_symbols(venue=str(venue), **criteria)
    payload = {
        "venue": str(venue),
        "criteria": criteria,
        "ts_epoch": time.time(),
        "ok": bool(scan.get("ok")),
        "selected": _unique_symbols(normalize_symbols(scan.get("selected") or [])),
        "source": scan.get("source"),
        "scan_ts": scan.get("ts"),
        "errors": list(scan.get("errors") or []),
    }
    _write_scan_cache(payload)
    return {
        "ok": payload["ok"],
        "selected": list(payload["selected"]),
        "source": payload.get("source"),
        "ts": payload.get("scan_ts"),
        "errors": list(payload.get("errors") or []),
        "cached": False,
    }


def resolve_managed_symbol_selection(
    cfg: dict[str, Any],
    *,
    venue: str,
    mode: str,
    live_enabled: bool,
) -> dict[str, Any]:
    base_symbols = resolve_managed_symbols(cfg)
    managed = cfg.get("managed_symbols") if isinstance(cfg.get("managed_symbols"), dict) else {}
    source = str(managed.get("source") or "static").strip().lower() or "static"

    out: dict[str, Any] = {
        "source": source,
        "symbols": list(base_symbols),
        "base_symbols": list(base_symbols),
        "selected_symbols": list(base_symbols),
        "protected_symbols": [],
        "protected_symbol_details": [],
        "scan_ok": None,
        "scan_cached": None,
        "reason": "static_config",
    }

    if source != "scanner":
        return out

    if mode != "paper" or live_enabled:
        out["source"] = "static"
        out["reason"] = "scanner_source_live_unsupported"
        return out

    scan = _scan_symbol_candidates(venue=str(venue), managed=managed)
    selected_symbols = _unique_symbols(normalize_symbols(scan.get("selected") or []))
    protected_details = _busy_paper_symbol_details(venue=str(venue), managed=managed) if bool(managed.get("preserve_active", True)) else []
    protected_symbol_details = _protected_symbol_details(protected_details)
    protected_symbols = [str(item.get("symbol") or "").strip().upper() for item in protected_symbol_details if str(item.get("symbol") or "").strip()]

    out["scan_ok"] = bool(scan.get("ok"))
    out["scan_cached"] = bool(scan.get("cached"))
    out["selected_symbols"] = list(selected_symbols)
    out["protected_symbols"] = list(protected_symbols)
    out["protected_symbol_details"] = list(protected_symbol_details)
    out["scan_source"] = scan.get("source")
    out["scan_ts"] = scan.get("ts")
    out["scan_errors"] = list(scan.get("errors") or [])

    if bool(scan.get("ok")) and selected_symbols:
        out["symbols"] = _unique_symbols(selected_symbols + protected_symbols)
        out["reason"] = "scanner_selected_cached" if bool(scan.get("cached")) else "scanner_selected"
        return out

    out["symbols"] = _unique_symbols(base_symbols + protected_symbols)
    out["reason"] = "scanner_fallback_to_base_cached" if bool(scan.get("cached")) else "scanner_fallback_to_base"
    return out
