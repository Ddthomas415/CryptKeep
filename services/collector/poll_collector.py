from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir


@dataclass(frozen=True)
class CollectorConfig:
    config_path: str = "config/trading.yaml"
    events_db_path: str = str(data_dir() / "events.sqlite")
    poll_sec: float = 1.0


def _parse_ts(ts: Any) -> float | None:
    try:
        text = str(ts or "").strip()
        if not text:
            return None
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _parse_detail(raw: Any) -> dict[str, Any] | None:
    if raw in (None, b"", ""):
        return None
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        obj = json.loads(str(raw))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


class PollCollectorHandle:
    def __init__(self, cfg: CollectorConfig) -> None:
        self.cfg = cfg

    def status(self) -> dict[str, Any]:
        db_path = Path(str(self.cfg.events_db_path))
        threshold_sec = max(30.0, float(self.cfg.poll_sec or 1.0) * 10.0)
        base = {
            "ok": True,
            "running": False,
            "service": "data_collector",
            "config_path": str(self.cfg.config_path),
            "events_db_path": str(db_path),
            "poll_sec": float(self.cfg.poll_sec),
            "threshold_sec": threshold_sec,
        }
        if not db_path.exists():
            return {**base, "reason": "events_db_missing"}

        con = sqlite3.connect(str(db_path))
        try:
            row = con.execute(
                "SELECT ts, status, detail FROM health WHERE service=? ORDER BY id DESC LIMIT 1",
                ("data_collector",),
            ).fetchone()
        except sqlite3.Error as e:
            return {**base, "ok": False, "reason": f"db_error:{type(e).__name__}:{e}"}
        finally:
            con.close()

        if not row:
            return {**base, "reason": "heartbeat_missing"}

        ts_epoch = _parse_ts(row[0])
        age_sec = (time.time() - ts_epoch) if ts_epoch is not None else None
        last_status = str(row[1] or "")
        running = bool(last_status == "running" and age_sec is not None and age_sec <= threshold_sec)
        out = {
            **base,
            "running": running,
            "last_ts": row[0],
            "age_sec": age_sec,
            "status": last_status,
            "detail": _parse_detail(row[2]),
        }
        if not running:
            out["reason"] = "stale" if age_sec is not None else "unparseable_heartbeat_ts"
        return out


_HANDLES: dict[CollectorConfig, PollCollectorHandle] = {}


def get_or_create(cfg: CollectorConfig) -> PollCollectorHandle:
    handle = _HANDLES.get(cfg)
    if handle is None:
        handle = PollCollectorHandle(cfg)
        _HANDLES[cfg] = handle
    return handle
