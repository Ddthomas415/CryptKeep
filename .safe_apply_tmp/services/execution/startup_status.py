from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir

STATUS_PATH = data_dir() / "startup_status.json"

def _day_key_utc(ts: float | None = None) -> str:
    ts = float(ts if ts is not None else time.time())
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"

def _load() -> dict:
    try:
        if not STATUS_PATH.exists():
            return {}
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save(obj: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)[:2_000_000], encoding="utf-8")

def record_success(*, venue: str, symbols: list[str], report: dict | None = None) -> dict:
    v = str(venue).strip().lower()
    now = time.time()
    st = _load()
    st.setdefault("venues", {})
    st["venues"][v] = {
        "ok": True,
        "ts_epoch": now,
        "ts_iso": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "day_utc": _day_key_utc(now),
        "symbols": list(symbols or []),
        "report_summary": {
            "open_orders_total": (report or {}).get("open_orders_total"),
            "lookback_hours": (report or {}).get("lookback_hours"),
        } if isinstance(report, dict) else {},
    }
    _save(st)
    return {"ok": True, "path": str(STATUS_PATH), "venue": v, "ts_epoch": now}

def record_failure(*, venue: str, reason: str, detail: dict | None = None) -> dict:
    v = str(venue).strip().lower()
    now = time.time()
    st = _load()
    st.setdefault("venues", {})
    st["venues"][v] = {
        "ok": False,
        "ts_epoch": now,
        "ts_iso": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "day_utc": _day_key_utc(now),
        "reason": str(reason),
        "detail": (detail or {}),
    }
    _save(st)
    return {"ok": True, "path": str(STATUS_PATH), "venue": v, "ts_epoch": now}

def get_status(*, venue: str | None = None) -> dict:
    st = _load()
    if venue:
        v = str(venue).strip().lower()
        return {"path": str(STATUS_PATH), "venue": v, "status": (st.get("venues", {}) or {}).get(v)}
    return {"path": str(STATUS_PATH), "status": st}

def is_fresh(*, venue: str, within_hours: int = 24) -> dict:
    v = str(venue).strip().lower()
    within_hours = int(within_hours)
    if within_hours <= 0:
        within_hours = 24
    st = _load()
    vs = (st.get("venues", {}) or {}).get(v)
    if not isinstance(vs, dict):
        return {"ok": True, "fresh": False, "reason": "no_status"}
    if not bool(vs.get("ok", False)):
        return {"ok": True, "fresh": False, "reason": "last_status_not_ok", "status": vs}
    ts = vs.get("ts_epoch")
    if ts is None:
        return {"ok": True, "fresh": False, "reason": "missing_timestamp", "status": vs}
    age = time.time() - float(ts)
    return {"ok": True, "fresh": (age <= within_hours * 3600.0), "age_sec": float(age), "within_hours": within_hours, "status": vs}
