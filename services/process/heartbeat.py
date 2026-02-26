from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from services.os.app_paths import data_dir

HB_PATH = data_dir() / "bot_heartbeat.json"

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
