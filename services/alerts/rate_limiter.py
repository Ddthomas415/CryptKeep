from __future__ import annotations

import json
import time
from typing import Any

from services.os.app_paths import data_dir

STATE_PATH = data_dir() / "alert_rate_limit.json"


def _read_state() -> dict[str, float]:
    try:
        if not STATE_PATH.exists():
            return {}
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict[str, float] = {}
        for k, v in raw.items():
            try:
                out[str(k)] = float(v)
            except Exception:
                continue
        return out
    except Exception:
        return {}


def _write_state(state: dict[str, float]) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    except Exception:
        return


def allow(*, key: str, min_interval_sec: int = 60, now_ts: float | None = None) -> dict[str, Any]:
    now = float(now_ts if now_ts is not None else time.time())
    interval = max(0.0, float(min_interval_sec or 0))
    state = _read_state()
    last_ts = float(state.get(str(key), 0.0) or 0.0)
    age_sec = (now - last_ts) if last_ts else None

    if interval <= 0.0 or age_sec is None or age_sec >= interval:
        state[str(key)] = now
        _write_state(state)
        return {
            "allowed": True,
            "key": str(key),
            "min_interval_sec": interval,
            "last_ts": last_ts or None,
            "age_sec": age_sec,
        }

    return {
        "allowed": False,
        "key": str(key),
        "min_interval_sec": interval,
        "last_ts": last_ts,
        "age_sec": age_sec,
        "retry_after_sec": max(0.0, interval - age_sec),
    }
