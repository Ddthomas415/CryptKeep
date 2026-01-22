from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.process.heartbeat import read_heartbeat
from services.logging.app_logger import log_path as app_log_path

CRASH_PATH = data_dir() / "crash_snapshot.json"
BOT_LOG = data_dir() / "logs" / "bot.log"

def _iso_now() -> str:
    return datetime.utcfromtimestamp(time.time()).isoformat() + "Z"

def _tail_bytes(p: Path, max_bytes: int = 200_000) -> str:
    try:
        if not p.exists():
            return ""
        b = p.read_bytes()
        if len(b) > max_bytes:
            b = b[-max_bytes:]
        return b.decode("utf-8", errors="replace")
    except Exception:
        return ""

def write_crash_snapshot(
    *,
    reason: str,
    pid: int | None = None,
    proc_state: dict | None = None,
    extra: dict | None = None,
) -> dict:
    CRASH_PATH.parent.mkdir(parents=True, exist_ok=True)
    obj: dict[str, Any] = {
        "ts_epoch": time.time(),
        "ts_iso": _iso_now(),
        "reason": reason,
        "pid": int(pid) if pid else None,
        "proc_state": (proc_state or {}),
        "heartbeat_last": read_heartbeat(),
        "bot_log_tail": _tail_bytes(BOT_LOG),
        "app_log_tail": _tail_bytes(app_log_path()),
        "extra": (extra or {}),
    }
    CRASH_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)[:2_000_000], encoding="utf-8")
    return {"ok": True, "path": str(CRASH_PATH)}

def read_crash_snapshot() -> dict:
    try:
        if not CRASH_PATH.exists():
            return {}
        return json.loads(CRASH_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
