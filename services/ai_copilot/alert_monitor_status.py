from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import ensure_dirs, runtime_dir

MONITOR_NAME = "ai_alert_monitor"


def _health_dir() -> Path:
    return runtime_dir() / "health"


def _flags_dir() -> Path:
    return runtime_dir() / "flags"


def _reports_dir() -> Path:
    return runtime_dir() / "ai_reports"


def status_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.json"


def pid_file() -> Path:
    return _health_dir() / f"{MONITOR_NAME}.pid.json"


def stop_file() -> Path:
    return _flags_dir() / f"{MONITOR_NAME}.stop"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def load_runtime_status() -> dict[str, Any]:
    if not status_file().exists():
        return {
            "ok": True,
            "has_status": False,
            "has_pid_file": pid_file().exists(),
            "status": "not_started",
            "reason": "status_missing",
            "summary_text": "AI alert monitor has not written runtime status yet.",
        }

    try:
        payload = _load_json(status_file())
    except Exception as exc:
        return {
            "ok": False,
            "has_status": False,
            "has_pid_file": pid_file().exists(),
            "status": "error",
            "reason": f"status_read_failed:{type(exc).__name__}",
            "summary_text": "AI alert monitor status is unavailable.",
        }

    payload["ok"] = bool(payload.get("ok", True))
    payload["has_status"] = True
    payload["has_pid_file"] = pid_file().exists()
    return payload


def list_recent_incidents(*, limit: int = 5) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(_reports_dir().glob(f"{MONITOR_NAME}_*.json"), reverse=True)[: max(1, int(limit or 5))]:
        try:
            payload = _load_json(path)
        except Exception:
            continue
        out.append(
            {
                "stem": path.stem,
                "severity": payload.get("severity"),
                "summary": payload.get("summary"),
                "generated_at": payload.get("generated_at"),
                "json_path": str(path),
                "markdown_path": str(path.with_suffix(".md")),
            }
        )
    return out


def request_stop() -> dict[str, Any]:
    ensure_dirs()
    _flags_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "requested": True,
        "monitor_name": MONITOR_NAME,
        "stop_file": str(stop_file()),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    stop_file().write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
