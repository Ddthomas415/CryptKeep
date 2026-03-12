from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict


SERVICE_NAME = "crypto-bot-pro-auth"
INDEX_ACCOUNT = "__users_index__"
ROLE_VALUES = {"VIEWER", "OPERATOR", "ADMIN"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_keyring_module():
    import keyring  # type: ignore

    return keyring


def _keyring_get(account: str) -> str | None:
    kr = _get_keyring_module()
    return kr.get_password(SERVICE_NAME, str(account))


def _keyring_set(account: str, value: str) -> None:
    kr = _get_keyring_module()
    kr.set_password(SERVICE_NAME, str(account), str(value))


def _account_name(username: str) -> str:
    return f"user:{_norm_username(username)}"


def _norm_username(username: str) -> str:
    return str(username or "").strip().lower()


def _norm_role(role: str | None) -> str:
    r = str(role or "VIEWER").strip().upper()
    return r if r in ROLE_VALUES else "VIEWER"


def _pbkdf2_hash(password: str, salt: bytes, iterations: int) -> str:
    raw = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, int(iterations))
    return raw.hex()


def keychain_available() -> tuple[bool, str | None]:
    try:
        _ = _keyring_get("__probe__")
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _load_users_index() -> list[str]:
    raw = _keyring_get(INDEX_ACCOUNT)
    if not raw:
        return []
    try:
        rows = json.loads(raw)
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    out = []
    for item in rows:
        name = _norm_username(str(item))
        if name:
            out.append(name)
    return sorted(set(out))


def _save_users_index(usernames: list[str]) -> None:
    names = sorted(set(_norm_username(x) for x in usernames if _norm_username(x)))
    _keyring_set(INDEX_ACCOUNT, json.dumps(names, sort_keys=True))


def get_user(username: str) -> dict[str, Any] | None:
    name = _norm_username(username)
    if not name:
        return None
    raw = _keyring_get(_account_name(name))
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    if _norm_username(obj.get("username") or name) != name:
        return None
    out = dict(obj)
    out["username"] = name
    out["role"] = _norm_role(out.get("role"))
    out["enabled"] = bool(out.get("enabled", True))
    return out


def list_users() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name in _load_users_index():
        row = get_user(name)
        if not row:
            continue
        out.append(
            {
                "username": str(row.get("username") or ""),
                "role": _norm_role(row.get("role")),
                "enabled": bool(row.get("enabled", True)),
                "created_ts": row.get("created_ts"),
                "updated_ts": row.get("updated_ts"),
            }
        )
    return out


def upsert_user(*, username: str, password: str, role: str = "VIEWER", enabled: bool = True) -> dict[str, Any]:
    name = _norm_username(username)
    if not name:
        return {"ok": False, "reason": "username_required"}
    pwd = str(password or "")
    if not pwd:
        return {"ok": False, "reason": "password_required"}

    existing = get_user(name) or {}
    salt = secrets.token_bytes(16)
    iterations = int(existing.get("iterations") or 390_000)
    record = {
        "username": name,
        "role": _norm_role(role),
        "enabled": bool(enabled),
        "iterations": int(iterations),
        "password_salt_b64": base64.b64encode(salt).decode("utf-8"),
        "password_hash_hex": _pbkdf2_hash(pwd, salt, iterations),
        "created_ts": str(existing.get("created_ts") or _now_iso()),
        "updated_ts": _now_iso(),
    }
    _keyring_set(_account_name(name), json.dumps(record, sort_keys=True))
    names = _load_users_index()
    names.append(name)
    _save_users_index(names)
    return {"ok": True, "username": name, "role": record["role"], "enabled": bool(record["enabled"])}


def verify_login(*, username: str, password: str) -> dict[str, Any]:
    name = _norm_username(username)
    pwd = str(password or "")
    if not name:
        return {"ok": False, "reason": "username_required"}
    if not pwd:
        return {"ok": False, "reason": "password_required"}

    # Controlled fallback for environments where keychain is unavailable.
    env_user = _norm_username(os.environ.get("CBP_AUTH_USERNAME") or "")
    env_pass = str(os.environ.get("CBP_AUTH_PASSWORD") or "")
    if env_user and env_pass and name == env_user:
        if hmac.compare_digest(pwd, env_pass):
            return {
                "ok": True,
                "source": "env",
                "username": name,
                "role": _norm_role(os.environ.get("CBP_AUTH_ROLE") or "ADMIN"),
            }
        return {"ok": False, "reason": "invalid_credentials"}

    row = get_user(name)
    if not row:
        return {"ok": False, "reason": "unknown_user"}
    if not bool(row.get("enabled", True)):
        return {"ok": False, "reason": "user_disabled"}
    try:
        salt = base64.b64decode(str(row.get("password_salt_b64") or "").encode("utf-8"))
        iterations = int(row.get("iterations") or 390_000)
        expected = str(row.get("password_hash_hex") or "")
    except Exception:
        return {"ok": False, "reason": "invalid_user_record"}
    actual = _pbkdf2_hash(pwd, salt, iterations)
    if not hmac.compare_digest(actual, expected):
        return {"ok": False, "reason": "invalid_credentials"}
    return {"ok": True, "source": "keychain", "username": name, "role": _norm_role(row.get("role"))}


def ensure_bootstrap_user_from_env() -> dict[str, Any]:
    user = _norm_username(os.environ.get("CBP_AUTH_BOOTSTRAP_USER") or "")
    pwd = str(os.environ.get("CBP_AUTH_BOOTSTRAP_PASSWORD") or "")
    role = _norm_role(os.environ.get("CBP_AUTH_BOOTSTRAP_ROLE") or "ADMIN")
    if not user or not pwd:
        return {"ok": True, "skipped": True, "reason": "bootstrap_env_missing"}

    existing = get_user(user)
    if existing:
        return {"ok": True, "skipped": True, "reason": "bootstrap_user_exists", "username": user}

    out = upsert_user(username=user, password=pwd, role=role, enabled=True)
    out["bootstrapped"] = bool(out.get("ok"))
    return out
