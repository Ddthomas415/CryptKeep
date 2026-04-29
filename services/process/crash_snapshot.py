from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir, runtime_dir
from services.process.bot_runtime_truth import read_heartbeat
from services.logging.app_logger import log_path as app_log_path

CRASH_PATH = data_dir() / "crash_snapshot.json"
BOT_LOG = data_dir() / "logs" / "bot.log"


def _managed_service_logs() -> dict[str, Path]:
    logs = runtime_dir() / "logs"
    return {
        "market_ws": logs / "market_ws.log",
        "intent_consumer": logs / "intent_consumer.log",
        "reconciler": logs / "reconciler.log",
    }

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

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


def _managed_service_log_tails() -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": str(path),
            "tail": _tail_bytes(path),
        }
        for name, path in _managed_service_logs().items()
    }

def write_crash_snapshot(
    *,
    reason: str,
    pid: int | None = None,
    proc_state: dict | None = None,
    extra: dict | None = None,
) -> dict:
    CRASH_PATH.parent.mkdir(parents=True, exist_ok=True)
    app_log = Path(app_log_path())
    obj: dict[str, Any] = {
        "ts_epoch": time.time(),
        "ts_iso": _iso_now(),
        "reason": reason,
        "pid": int(pid) if pid else None,
        "proc_state": (proc_state or {}),
        "heartbeat_last": read_heartbeat(),
        "bot_log_path": str(BOT_LOG),
        "bot_log_tail": _tail_bytes(BOT_LOG),
        "app_log_path": str(app_log),
        "app_log_tail": _tail_bytes(app_log),
        "managed_service_log_tails": _managed_service_log_tails(),
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
