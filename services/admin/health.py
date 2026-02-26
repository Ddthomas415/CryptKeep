from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import runtime_dir, ensure_dirs
from services.logging.app_logger import get_logger

ensure_dirs()
HEALTH_DIR = runtime_dir() / "health"
logger = get_logger("admin_health")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_health(service: str, status: str, pid: int | None = None, details: dict | None = None) -> None:
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    path = HEALTH_DIR / f"{service}.json"

    payload = {
        "service": service,
        "status": status,
        "pid": pid,
        "ts": _now(),
        "details": details or {},
    }

    try:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except Exception:
        logger.exception("admin_health: failed to write health file path=%s", path)


def read_health(service: str) -> dict:
    path = HEALTH_DIR / f"{service}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        logger.exception("admin_health: failed to read health file path=%s", path)
        return {}


def list_health() -> list[dict]:
    if not HEALTH_DIR.exists():
        return []

    rows = []
    for f in HEALTH_DIR.glob("*.json"):
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            logger.exception("admin_health: failed to parse health file path=%s", f)
    return rows
