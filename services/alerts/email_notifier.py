from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Iterable


def _smtp_cfg() -> Dict[str, Any]:
    return {
        "host": str(os.environ.get("CBP_SMTP_HOST") or "").strip(),
        "port": int(os.environ.get("CBP_SMTP_PORT") or "587"),
        "username": str(os.environ.get("CBP_SMTP_USERNAME") or "").strip(),
        "password": str(os.environ.get("CBP_SMTP_PASSWORD") or "").strip(),
        "from_email": str(os.environ.get("CBP_SMTP_FROM") or "").strip(),
        "use_tls": str(os.environ.get("CBP_SMTP_USE_TLS") or "1").strip().lower() in {"1", "true", "yes", "on"},
    }


def send_email(
    *,
    to: Iterable[str],
    subject: str,
    body: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    cfg = _smtp_cfg()
    rcpts = [str(x).strip() for x in (to or []) if str(x).strip()]
    if not rcpts:
        return {"ok": False, "reason": "no_recipients"}
    missing = [k for k in ("host", "from_email") if not cfg.get(k)]
    if missing:
        return {"ok": False, "reason": "smtp_not_configured", "missing": missing}
    if dry_run:
        return {"ok": True, "dry_run": True, "to": rcpts, "subject": str(subject)}

    msg = EmailMessage()
    msg["From"] = cfg["from_email"]
    msg["To"] = ", ".join(rcpts)
    msg["Subject"] = str(subject)
    msg.set_content(str(body))

    try:
        with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=20) as s:
            if cfg["use_tls"]:
                s.starttls()
            if cfg["username"]:
                s.login(cfg["username"], cfg["password"])
            s.send_message(msg)
        return {"ok": True, "sent": True, "to_count": len(rcpts)}
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}: {e}"}
