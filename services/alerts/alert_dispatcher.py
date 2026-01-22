from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from services.logging.app_logger import get_logger
from services.os.app_paths import data_dir

logger = get_logger("alert_dispatcher")

LAST_PATH = data_dir() / "alerts_last.json"

def _persist_last(obj: dict) -> None:
    try:
        LAST_PATH.parent.mkdir(parents=True, exist_ok=True)
        LAST_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str)[:2_000_000], encoding="utf-8")
    except Exception:
        pass

def read_last_send() -> dict:
    try:
        if not LAST_PATH.exists():
            return {}
        return json.loads(LAST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _cfg_alerts(cfg: dict) -> dict:
    a = cfg.get("alerts") if isinstance(cfg.get("alerts"), dict) else {}
    a.setdefault("enabled", False)
    a.setdefault("slack_webhook_url", "")
    a.setdefault("min_level", "error")  # info|warn|error
    return a

_LEVELS = {"info": 10, "warn": 20, "error": 30}

def _lvl(x: str) -> int:
    return _LEVELS.get((x or "error").strip().lower(), 30)

def send_alert(*, cfg: dict, level: str, message: str, payload: dict | None = None) -> dict:
    a = _cfg_alerts(cfg)
    if not bool(a.get("enabled", False)):
        out = {"ok": True, "skipped": True, "reason": "alerts_disabled"}
        _persist_last(out)
        return out

    if _lvl(level) < _lvl(str(a.get("min_level", "error"))):
        out = {"ok": True, "skipped": True, "reason": "below_min_level"}
        _persist_last(out)
        return out

    url = str(a.get("slack_webhook_url") or "").strip()
    if not url:
        out = {"ok": False, "reason": "missing_slack_webhook_url"}
        _persist_last(out)
        return out

    body = {"text": f"[{level.upper()}] {message}"}
    if payload:
        body["text"] += "\n```" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)[:3000] + "\n```"

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            out = {"ok": True, "status": int(getattr(resp, "status", 200))}
            _persist_last(out)
            return out
    except Exception as e:
        logger.exception("alert send failed")
        out = {"ok": False, "reason": f"{type(e).__name__}:{e}"}
        _persist_last(out)
        return out
