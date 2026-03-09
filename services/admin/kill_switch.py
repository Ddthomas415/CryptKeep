from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from services.os.app_paths import runtime_dir, ensure_dirs

ensure_dirs()
KILL_PATH = runtime_dir() / "kill_switch.json"
_LOG = logging.getLogger(__name__)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _default_payload(note: str = "default") -> dict:
    return {"armed": True, "ts": _now(), "note": str(note)}


def _read_state() -> dict:
    return json.loads(KILL_PATH.read_text(encoding="utf-8"))


def ensure_default():
    if not KILL_PATH.exists():
        KILL_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = _default_payload()
        KILL_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload
    return _read_state()

def set_armed(state: bool, note: str = "") -> dict:
    payload = {"armed": bool(state), "ts": _now(), "note": str(note or "manual")}
    KILL_PATH.parent.mkdir(parents=True, exist_ok=True)
    KILL_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def get_state():
    try:
        if not KILL_PATH.exists():
            return ensure_default()
        return _read_state()
    except Exception as e:
        _LOG.warning("kill switch state read failed: %s: %s", type(e).__name__, e)
        return _default_payload("fallback")
