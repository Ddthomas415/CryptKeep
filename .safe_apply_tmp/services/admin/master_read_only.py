from __future__ import annotations
from datetime import datetime, timezone
from services.config_loader import load_user_config

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def is_master_read_only() -> tuple[bool, dict]:
    cfg = load_user_config()
    safety = cfg.get("safety") if isinstance(cfg.get("safety"), dict) else {}
    ro = bool(safety.get("read_only_mode", False))
    return ro, {"ts": _now(), "read_only_mode": ro}

def details() -> dict:
    ro, det = is_master_read_only()
    return det
