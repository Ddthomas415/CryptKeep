"""
services/alerts/alert_dispatcher.py

Alert dispatch with guaranteed local fallback.

Channels (tried in order when configured):
  1. Slack webhook (if slack_webhook_url set)
  2. SMTP email     (if SMTP env vars set — via email_notifier)
  3. Local alert file (ALWAYS written for error-level alerts)

The local fallback ensures critical alerts are never silently dropped
even when no external channel is configured.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.logging.app_logger import get_logger
from services.os.app_paths import data_dir, runtime_dir
from services.os.file_utils import atomic_write

logger = get_logger("alert_dispatcher")

# Where the last sent alert is persisted (existing behaviour)
LAST_PATH = data_dir() / "alerts_last.json"

# Local alert log — written for every error-level alert regardless of channel config
ALERT_LOG_PATH = runtime_dir() / "alerts" / "critical_alerts.jsonl"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist_last(obj: dict) -> None:
    try:
        LAST_PATH.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(
            LAST_PATH,
            json.dumps({**obj, "ts": _now_iso()}, ensure_ascii=False, indent=2, default=str)[:2_000_000],
        )
    except Exception as _silent_err:
        _LOG.debug("suppressed: %s", _silent_err)


def _write_local_alert(level: str, message: str, payload: dict | None) -> None:
    """Append a JSONL entry to the local alert log — always available, no config needed."""
    try:
        ALERT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "ts": _now_iso(),
            "level": level,
            "message": str(message),
            "payload": payload or {},
        }, ensure_ascii=False, default=str)
        # JSONL append — not atomic (append is atomic enough for a log)
        with open(ALERT_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(entry + "\n")
    except Exception as _silent_err:
        _LOG.debug("suppressed: %s", _silent_err)


def _cfg_alerts(cfg: dict) -> dict:
    a = cfg.get("alerts") if isinstance(cfg.get("alerts"), dict) else {}
    a.setdefault("enabled", False)
    a.setdefault("slack_webhook_url", "")
    a.setdefault("min_level", "error")
    return a


_LEVELS = {"info": 10, "warn": 20, "error": 30}


def _lvl(x: str) -> int:
    return _LEVELS.get((x or "error").strip().lower(), 30)


# ---------------------------------------------------------------------------
# Channel implementations
# ---------------------------------------------------------------------------

def _try_slack(url: str, level: str, message: str, payload: dict | None) -> dict:
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
            return {"channel": "slack", "ok": True, "status": int(getattr(resp, "status", 200))}
    except Exception as e:
        logger.warning("slack alert failed: %s", e)
        return {"channel": "slack", "ok": False, "reason": f"{type(e).__name__}:{e}"}


def _try_email(level: str, message: str, payload: dict | None) -> dict:
    try:
        import os
        from services.alerts.email_notifier import send_email
        to_raw = os.environ.get("CBP_ALERT_EMAIL_TO", "").strip()
        if not to_raw:
            return {"channel": "email", "ok": False, "reason": "CBP_ALERT_EMAIL_TO_not_set"}
        recipients = [r.strip() for r in to_raw.split(",") if r.strip()]
        body = f"[{level.upper()}] {message}"
        if payload:
            body += "\n\n" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)[:3000]
        return {
            "channel": "email",
            **send_email(to=recipients, subject=f"CryptKeep alert: [{level.upper()}]", body=body),
        }
    except Exception as e:
        return {"channel": "email", "ok": False, "reason": f"{type(e).__name__}:{e}"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_last_send() -> dict:
    try:
        if not LAST_PATH.exists():
            return {}
        return json.loads(LAST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_alert_log(*, limit: int = 50) -> list[dict]:
    """Return recent local alert log entries, newest first."""
    if not ALERT_LOG_PATH.exists():
        return []
    try:
        lines = ALERT_LOG_PATH.read_text(encoding="utf-8").splitlines()
        entries = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception as _silent_err:
                _LOG.debug("suppressed: %s", _silent_err)
            if len(entries) >= limit:
                break
        return entries
    except Exception:
        return []


def send_alert(
    *,
    cfg: dict,
    level: str,
    message: str,
    payload: dict | None = None,
) -> dict:
    """Dispatch an alert through configured channels with local file fallback.

    Local alert file is ALWAYS written for error-level events, regardless of
    whether any external channel is configured or succeeds.
    """
    lvl_str = str(level or "error").strip().lower()

    # Local fallback: write to file for all error-level alerts unconditionally
    if _lvl(lvl_str) >= _lvl("error"):
        _write_local_alert(lvl_str, message, payload)

    a = _cfg_alerts(cfg)
    if not bool(a.get("enabled", False)):
        out = {"ok": True, "skipped": True, "reason": "alerts_disabled",
               "local_written": _lvl(lvl_str) >= _lvl("error")}
        _persist_last(out)
        return out

    if _lvl(lvl_str) < _lvl(str(a.get("min_level", "error"))):
        out = {"ok": True, "skipped": True, "reason": "below_min_level",
               "local_written": _lvl(lvl_str) >= _lvl("error")}
        _persist_last(out)
        return out

    results = []

    # Channel 1: Slack
    slack_url = str(a.get("slack_webhook_url") or "").strip()
    if slack_url:
        results.append(_try_slack(slack_url, lvl_str, message, payload))

    # Channel 2: Email (if Slack failed or not configured)
    if not any(r.get("ok") for r in results):
        email_result = _try_email(lvl_str, message, payload)
        if email_result.get("ok") or "not_set" not in str(email_result.get("reason", "")):
            results.append(email_result)

    any_ok = any(r.get("ok") for r in results)
    out = {
        "ok": any_ok,
        "channels": results,
        "local_written": _lvl(lvl_str) >= _lvl("error"),
        "reason": None if any_ok else "all_channels_failed",
    }
    _persist_last(out)
    return out
