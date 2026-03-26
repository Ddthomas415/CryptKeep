import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError


SERVICE_NAME = "crypto-bot-pro-auth"
INDEX_ACCOUNT = "__users_index__"
ROLE_VALUES = {"VIEWER", "OPERATOR", "ADMIN"}
MFA_ISSUER = "Crypto Bot Pro"
MFA_DIGITS = 6
MFA_PERIOD_SECONDS = 30
MFA_ALLOWED_DRIFT_WINDOWS = 1
MFA_BACKUP_CODE_COUNT = 6
PASSWORD_ALGO_ARGON2ID = "argon2id"
PASSWORD_ALGO_PBKDF2 = "pbkdf2_sha256"
DEFAULT_PBKDF2_ITERATIONS = 390_000

_MFA_RECORD_KEYS = {
    "mfa_enabled",
    "mfa_secret_b32",
    "mfa_issuer",
    "mfa_backup_code_hashes",
    "mfa_enrollment_started_ts",
    "mfa_enabled_ts",
}


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


def _argon2_hasher() -> PasswordHasher:
    return PasswordHasher()


def _build_argon2_password_record(password: str) -> dict[str, Any]:
    return {
        "password_algo": PASSWORD_ALGO_ARGON2ID,
        "password_hash": _argon2_hasher().hash(str(password or "")),
    }


def _build_pbkdf2_password_record(password: str, *, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> dict[str, Any]:
    salt = secrets.token_bytes(16)
    return {
        "password_algo": PASSWORD_ALGO_PBKDF2,
        "iterations": int(iterations),
        "password_salt_b64": base64.b64encode(salt).decode("utf-8"),
        "password_hash_hex": _pbkdf2_hash(str(password or ""), salt, int(iterations)),
    }


def _save_user_record(username: str, record: dict[str, Any]) -> None:
    name = _norm_username(username)
    payload = dict(record or {})
    payload["username"] = name
    payload["role"] = _norm_role(payload.get("role"))
    payload["enabled"] = bool(payload.get("enabled", True))
    payload["updated_ts"] = str(payload.get("updated_ts") or _now_iso())
    _keyring_set(_account_name(name), json.dumps(payload, sort_keys=True))


def _totp_secret_bytes(secret_b32: str) -> bytes:
    text = str(secret_b32 or "").strip().replace(" ", "").upper()
    pad = "=" * ((8 - (len(text) % 8)) % 8)
    return base64.b32decode(text + pad, casefold=True)


def _totp_hotp(secret_b32: str, counter: int) -> str:
    secret = _totp_secret_bytes(secret_b32)
    digest = hmac.new(secret, int(counter).to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return str(code % (10**MFA_DIGITS)).zfill(MFA_DIGITS)


def _current_totp_code(secret_b32: str, *, for_time: int | None = None) -> str:
    ts = int(time.time() if for_time is None else for_time)
    counter = ts // MFA_PERIOD_SECONDS
    return _totp_hotp(secret_b32, counter)


def _verify_totp_code(secret_b32: str, code: str, *, for_time: int | None = None) -> bool:
    normalized = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(normalized) != MFA_DIGITS:
        return False
    ts = int(time.time() if for_time is None else for_time)
    base_counter = ts // MFA_PERIOD_SECONDS
    for delta in range(-MFA_ALLOWED_DRIFT_WINDOWS, MFA_ALLOWED_DRIFT_WINDOWS + 1):
        if hmac.compare_digest(normalized, _totp_hotp(secret_b32, base_counter + delta)):
            return True
    return False


def _generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _backup_code_hash(code: str) -> str:
    normalized = "".join(ch for ch in str(code or "").strip().upper() if ch.isalnum())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _generate_backup_codes(*, count: int = MFA_BACKUP_CODE_COUNT) -> list[str]:
    out: list[str] = []
    for _ in range(max(1, int(count))):
        token = secrets.token_hex(4).upper()
        out.append(f"{token[:4]}-{token[4:]}")
    return out


def _otpauth_uri(*, username: str, secret_b32: str, issuer: str = MFA_ISSUER) -> str:
    label = quote(f"{issuer}:{_norm_username(username)}", safe="")
    issuer_q = quote(str(issuer or MFA_ISSUER), safe="")
    secret_q = quote(str(secret_b32 or ""), safe="")
    return f"otpauth://totp/{label}?secret={secret_q}&issuer={issuer_q}&digits={MFA_DIGITS}&period={MFA_PERIOD_SECONDS}"


def _env_login_allowed() -> bool:
    app_env = str(os.environ.get("APP_ENV") or "").strip().lower()
    explicit = str(os.environ.get("CBP_ALLOW_ENV_LOGIN") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return app_env == "dev" and explicit


def keychain_available() -> tuple[bool, str | None]:
    try:
        _ = _keyring_get("__probe__")
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _load_users_index() -> list[str]:
    try:
        raw = _keyring_get(INDEX_ACCOUNT)
    except Exception:
        return []
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
    try:
        raw = _keyring_get(_account_name(name))
    except Exception:
        return None
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
    out["mfa_enabled"] = bool(out.get("mfa_enabled", False) and str(out.get("mfa_secret_b32") or "").strip())
    out["mfa_backup_code_hashes"] = [
        str(item)
        for item in list(out.get("mfa_backup_code_hashes") or [])
        if str(item).strip()
    ]
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
                "mfa_enabled": bool(row.get("mfa_enabled", False)),
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
    record = {
        "username": name,
        "role": _norm_role(role),
        "enabled": bool(enabled),
        "created_ts": str(existing.get("created_ts") or _now_iso()),
        "updated_ts": _now_iso(),
    }
    record.update(_build_argon2_password_record(pwd))
    for key in _MFA_RECORD_KEYS:
        if key in existing:
            record[key] = existing.get(key)
    _save_user_record(name, record)
    names = _load_users_index()
    names.append(name)
    _save_users_index(names)
    return {"ok": True, "username": name, "role": record["role"], "enabled": bool(record["enabled"])}


def get_user_mfa_status(username: str) -> dict[str, Any]:
    row = get_user(username)
    if not row:
        return {"ok": False, "reason": "invalid_credentials"}
    backup_hashes = [str(item) for item in list(row.get("mfa_backup_code_hashes") or []) if str(item).strip()]
    return {
        "ok": True,
        "username": str(row.get("username") or ""),
        "enabled": bool(row.get("mfa_enabled", False)),
        "configured": bool(str(row.get("mfa_secret_b32") or "").strip()),
        "issuer": str(row.get("mfa_issuer") or MFA_ISSUER),
        "backup_codes_remaining": int(len(backup_hashes)),
        "enabled_ts": row.get("mfa_enabled_ts"),
        "enrollment_started_ts": row.get("mfa_enrollment_started_ts"),
    }


def begin_mfa_enrollment(*, username: str, issuer: str = MFA_ISSUER) -> dict[str, Any]:
    row = get_user(username)
    if not row:
        return {"ok": False, "reason": "invalid_credentials"}
    secret_b32 = _generate_totp_secret()
    backup_codes = _generate_backup_codes()
    row["mfa_enabled"] = False
    row["mfa_secret_b32"] = secret_b32
    row["mfa_issuer"] = str(issuer or MFA_ISSUER)
    row["mfa_backup_code_hashes"] = [_backup_code_hash(item) for item in backup_codes]
    row["mfa_enrollment_started_ts"] = _now_iso()
    row.pop("mfa_enabled_ts", None)
    row["updated_ts"] = _now_iso()
    _save_user_record(str(row.get("username") or ""), row)
    return {
        "ok": True,
        "username": str(row.get("username") or ""),
        "secret_b32": secret_b32,
        "issuer": str(row.get("mfa_issuer") or MFA_ISSUER),
        "backup_codes": backup_codes,
        "otpauth_uri": _otpauth_uri(username=str(row.get("username") or ""), secret_b32=secret_b32, issuer=str(row.get("mfa_issuer") or MFA_ISSUER)),
    }


def confirm_mfa_enrollment(*, username: str, code: str) -> dict[str, Any]:
    row = get_user(username)
    if not row:
        return {"ok": False, "reason": "invalid_credentials"}
    secret_b32 = str(row.get("mfa_secret_b32") or "").strip()
    if not secret_b32:
        return {"ok": False, "reason": "mfa_not_configured"}
    if not _verify_totp_code(secret_b32, code):
        return {"ok": False, "reason": "invalid_mfa_code"}
    row["mfa_enabled"] = True
    row["mfa_enabled_ts"] = _now_iso()
    row["updated_ts"] = _now_iso()
    _save_user_record(str(row.get("username") or ""), row)
    return {
        "ok": True,
        "username": str(row.get("username") or ""),
        "backup_codes_remaining": int(len(list(row.get("mfa_backup_code_hashes") or []))),
    }


def disable_mfa_for_user(*, username: str) -> dict[str, Any]:
    row = get_user(username)
    if not row:
        return {"ok": False, "reason": "invalid_credentials"}
    for key in _MFA_RECORD_KEYS:
        row.pop(key, None)
    row["updated_ts"] = _now_iso()
    _save_user_record(str(row.get("username") or ""), row)
    return {"ok": True, "username": str(row.get("username") or ""), "mfa_enabled": False}


def verify_mfa_code(*, username: str, code: str) -> dict[str, Any]:
    row = get_user(username)
    if not row:
        return {"ok": False, "reason": "invalid_credentials"}
    if not bool(row.get("mfa_enabled", False)):
        return {"ok": False, "reason": "mfa_not_enabled"}
    secret_b32 = str(row.get("mfa_secret_b32") or "").strip()
    if secret_b32 and _verify_totp_code(secret_b32, code):
        return {"ok": True, "method": "totp", "username": str(row.get("username") or "")}

    backup_hash = _backup_code_hash(code)
    hashes = [str(item) for item in list(row.get("mfa_backup_code_hashes") or []) if str(item).strip()]
    if backup_hash in hashes:
        remaining = [item for item in hashes if item != backup_hash]
        row["mfa_backup_code_hashes"] = remaining
        row["updated_ts"] = _now_iso()
        _save_user_record(str(row.get("username") or ""), row)
        return {
            "ok": True,
            "method": "backup_code",
            "username": str(row.get("username") or ""),
            "backup_codes_remaining": int(len(remaining)),
        }
    return {"ok": False, "reason": "invalid_mfa_code"}


def verify_login(*, username: str, password: str) -> dict[str, Any]:
    name = _norm_username(username)
    pwd = str(password or "")
    if not name:
        return {"ok": False, "reason": "username_required"}
    if not pwd:
        return {"ok": False, "reason": "password_required"}

    # Controlled fallback for environments where keychain is unavailable.
    # Disabled by default. Only allowed in explicit dev mode with:
    #   APP_ENV=dev
    #   CBP_ALLOW_ENV_LOGIN=1
    env_user = _norm_username(os.environ.get("CBP_AUTH_USERNAME") or "")
    env_pass = str(os.environ.get("CBP_AUTH_PASSWORD") or "")
    if _env_login_allowed() and env_user and env_pass and name == env_user:
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
        return {"ok": False, "reason": "invalid_credentials"}
    if not bool(row.get("enabled", True)):
        return {"ok": False, "reason": "invalid_credentials"}
    algo = str(row.get("password_algo") or "").strip().lower()
    verified = False
    needs_rehash = False
    if algo in {"", PASSWORD_ALGO_PBKDF2}:
        try:
            salt = base64.b64decode(str(row.get("password_salt_b64") or "").encode("utf-8"))
            iterations = int(row.get("iterations") or DEFAULT_PBKDF2_ITERATIONS)
            expected = str(row.get("password_hash_hex") or "")
        except Exception:
            return {"ok": False, "reason": "invalid_credentials"}
        actual = _pbkdf2_hash(pwd, salt, iterations)
        verified = hmac.compare_digest(actual, expected)
        needs_rehash = verified
    elif algo == PASSWORD_ALGO_ARGON2ID:
        encoded = str(row.get("password_hash") or "").strip()
        try:
            verified = _argon2_hasher().verify(encoded, pwd)
            needs_rehash = _argon2_hasher().check_needs_rehash(encoded)
        except (VerifyMismatchError, InvalidHashError):
            verified = False
        except Exception:
            return {"ok": False, "reason": "invalid_credentials"}
    else:
        return {"ok": False, "reason": "invalid_credentials"}
    if not verified:
        return {"ok": False, "reason": "invalid_credentials"}
    if needs_rehash:
        row.update(_build_argon2_password_record(pwd))
        row.pop("iterations", None)
        row.pop("password_salt_b64", None)
        row.pop("password_hash_hex", None)
        row["updated_ts"] = _now_iso()
        _save_user_record(name, row)
    mfa_enabled = bool(row.get("mfa_enabled", False) and str(row.get("mfa_secret_b32") or "").strip())
    return {
        "ok": True,
        "source": "keychain",
        "username": name,
        "role": _norm_role(row.get("role")),
        "mfa_required": mfa_enabled,
    }


def ensure_bootstrap_user_from_env() -> dict[str, Any]:
    app_env = str(os.environ.get("APP_ENV") or "").strip().lower()
    explicit = str(os.environ.get("CBP_ALLOW_BOOTSTRAP_USER") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not (app_env == "dev" and explicit):
        return {"ok": True, "skipped": True, "reason": "bootstrap_not_allowed"}

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
