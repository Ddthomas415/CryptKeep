from __future__ import annotations
import hashlib
import secrets
import time
import json
from services.os.app_paths import data_dir
STATE_PATH = data_dir() / "live_arming.json"
def _load() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"version": 1, "active": None}
def _save(st: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")
def _sha256(s: str) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()
def issue_token(*, ttl_minutes: int = 30) -> dict:
    token = secrets.token_urlsafe(18)
    now = time.time()
    exp = now + (int(ttl_minutes) * 60)
    st = _load()
    st["active"] = {"hash": _sha256(token), "issued_epoch": now, "expires_epoch": exp, "consumed": False}
    _save(st)
    return {"ok": True, "token": token, "expires_epoch": exp, "path": str(STATE_PATH)}
def status() -> dict:
    st = _load()
    a = st.get("active")
    if not isinstance(a, dict):
        return {"ok": True, "active": None, "path": str(STATE_PATH)}
    return {"ok": True, "active": a, "path": str(STATE_PATH)}
def verify_and_consume(token: str) -> dict:
    st = _load()
    a = st.get("active")
    if not isinstance(a, dict):
        return {"ok": False, "reason": "no_active_token"}
    if bool(a.get("consumed")):
        return {"ok": False, "reason": "token_already_consumed"}
    now = time.time()
    if now > float(a.get("expires_epoch") or 0):
        return {"ok": False, "reason": "token_expired"}
    if _sha256(token) != str(a.get("hash")):
        return {"ok": False, "reason": "token_mismatch"}
    a["consumed"] = True
    a["consumed_epoch"] = now
    st["active"] = a
    _save(st)
    return {"ok": True, "consumed": True}
