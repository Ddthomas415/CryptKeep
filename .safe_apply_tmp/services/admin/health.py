from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HEALTH_DIR = Path("runtime") / "health"


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
        pass


def list_health() -> list[dict]:
    if not HEALTH_DIR.exists():
        return []

    rows = []
    for f in HEALTH_DIR.glob("*.json"):
        try:
            rows.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return rows

