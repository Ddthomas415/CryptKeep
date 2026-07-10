from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import math
import os

from services.os.app_paths import data_dir, runtime_dir

HB_PATH = data_dir() / "bot_heartbeat.json"

# --- named per-loop heartbeats (substrate backlog #6) -----------------------
# The legacy single-file heartbeat above serves the bot-runner/watchdog pair
# and is deliberately untouched. Managed trading loops each need independent
# liveness, so named beats write one file per loop under
# runtime/heartbeats/, atomically, rate-limited, and never raising (a
# heartbeat must not be able to break a trading loop). Liveness is judged
# externally by scripts/check_dead_man.py.

HEARTBEAT_MIN_INTERVAL_S_ENV = "CBP_HEARTBEAT_MIN_INTERVAL_S"
HEARTBEAT_MIN_INTERVAL_S_DEFAULT = 5.0

_NAMED_LAST: dict[str, float] = {}
_NAMED_SEQ: dict[str, int] = {}


def _reset_named() -> None:
    _NAMED_LAST.clear()
    _NAMED_SEQ.clear()


def heartbeat_min_interval_s() -> float:
    raw = os.environ.get(HEARTBEAT_MIN_INTERVAL_S_ENV)
    if raw is None or str(raw).strip() == "":
        return HEARTBEAT_MIN_INTERVAL_S_DEFAULT
    try:
        value = float(raw)
    except Exception as _err:
        return HEARTBEAT_MIN_INTERVAL_S_DEFAULT
    if not math.isfinite(value) or value < 0.0:
        return HEARTBEAT_MIN_INTERVAL_S_DEFAULT
    return value


def named_heartbeat_path(name: str):
    safe = "".join(c if (c.isalnum() or c in "-_") else "_" for c in str(name))
    return runtime_dir() / "heartbeats" / f"{safe}.json"


def write_named_heartbeat(name: str, *, extra: dict | None = None, monotonic=None) -> bool:
    """Record liveness for a managed loop. True when written, False when
    rate-limited or on any error. Never raises."""
    try:
        mono = monotonic or time.monotonic
        now_m = mono()
        last = _NAMED_LAST.get(name)
        if last is not None and (now_m - last) < heartbeat_min_interval_s():
            return False
        _NAMED_SEQ[name] = _NAMED_SEQ.get(name, 0) + 1
        payload = {
            "name": str(name),
            "ts_epoch": time.time(),
            "ts_iso": _iso_now(),
            "pid": os.getpid(),
            "seq": _NAMED_SEQ[name],
        }
        if extra:
            payload["extra"] = extra
        path = named_heartbeat_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        _NAMED_LAST[name] = now_m
        return True
    except Exception as _err:
        return False


def read_named_heartbeat(name: str) -> dict:
    try:
        path = named_heartbeat_path(name)
        if not path.exists():
            return {}
        loaded = json.loads(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except Exception as _err:
        return {}


def named_heartbeat_age_s(name: str, *, now_epoch: float | None = None) -> float | None:
    rec = read_named_heartbeat(name)
    if not rec:
        return None
    try:
        epoch = float(rec.get("ts_epoch"))
    except Exception as _err:
        return None
    if not math.isfinite(epoch) or epoch <= 0.0:
        return None
    now = time.time() if now_epoch is None else float(now_epoch)
    return max(0.0, now - epoch)

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def write_heartbeat(*, status: str = "running", msg: str | None = None) -> dict:
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    obj = {
        "ts_epoch": time.time(),
        "ts_iso": _iso_now(),
        "status": status,
        "msg": msg,
    }
    HB_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"ok": True, "path": str(HB_PATH)}

def write_error(*, err: str, context: dict | None = None) -> dict:
    HB_PATH.parent.mkdir(parents=True, exist_ok=True)
    obj = {
        "ts_epoch": time.time(),
        "ts_iso": _iso_now(),
        "status": "error",
        "error": err,
        "context": (context or {}),
    }
    HB_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)[:2_000_000], encoding="utf-8")
    return {"ok": True, "path": str(HB_PATH)}

def read_heartbeat() -> dict:
    try:
        if not HB_PATH.exists():
            return {}
        return json.loads(HB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
