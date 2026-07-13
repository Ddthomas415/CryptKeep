from __future__ import annotations
from datetime import datetime, timezone
from services.config_loader import ConfigLoadError, load_user_config

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def is_master_read_only() -> tuple[bool, dict]:
    try:
        cfg = load_user_config(strict=True)
    except ConfigLoadError as exc:
        return True, {
            "ts": _now(),
            "read_only_mode": True,
            "reason": "config_unreadable",
            "error": str(exc),
        }
    except Exception as exc:
        return True, {
            "ts": _now(),
            "read_only_mode": True,
            "reason": "config_unreadable",
            "error": f"{type(exc).__name__}: {exc}",
        }

    safety = cfg.get("safety") if isinstance(cfg.get("safety"), dict) else {}
    ro = bool(safety.get("read_only_mode", False))
    return ro, {
        "ts": _now(),
        "read_only_mode": ro,
        "reason": "config" if ro else "not_read_only",
    }

def details() -> dict:
    ro, det = is_master_read_only()
    return det
