from __future__ import annotations
import os
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue
from services.security.credential_store import get_exchange_credentials

def load_exchange_credentials(venue: str) -> dict:
    """
    Preferred order:
      1) OS keyring via credential_store
      2) Environment variables named in config/user.yaml
    """
    v = normalize_venue(venue)
    cfg = load_user_yaml()
    ex = cfg.get("exchanges") if isinstance(cfg.get("exchanges"), dict) else {}
    ent = ex.get(v) if isinstance(ex.get(v), dict) else {}
    api_env = str(ent.get("api_key_env", f"{v.upper()}_API_KEY"))
    sec_env = str(ent.get("secret_env", f"{v.upper()}_API_SECRET"))
    pwd_env = str(ent.get("password_env", ""))  # optional

    keyring_creds = None
    keyring_error = None
    try:
        keyring_creds = get_exchange_credentials(v)
    except Exception as exc:
        keyring_error = f"{type(exc).__name__}: {exc}"

    if isinstance(keyring_creds, dict) and keyring_creds.get("apiKey") and keyring_creds.get("secret"):
        passphrase = keyring_creds.get("password") or keyring_creds.get("passphrase")
        return {
            "venue": v,
            "source": "keyring",
            "api_key_present": True,
            "secret_present": True,
            "password_present": bool(passphrase),
            "apiKey": str(keyring_creds.get("apiKey") or ""),
            "secret": str(keyring_creds.get("secret") or ""),
            "password": str(passphrase) if passphrase else None,
            "api_env": api_env,
            "secret_env": sec_env,
            "password_env": pwd_env if pwd_env else None,
            "keyring_error": keyring_error,
        }

    api_key = os.getenv(api_env, "")
    secret = os.getenv(sec_env, "")
    password = os.getenv(pwd_env, "") if pwd_env else ""
    return {
        "venue": v,
        "source": "env",
        "api_key_present": bool(api_key),
        "secret_present": bool(secret),
        "password_present": bool(password),
        "apiKey": api_key,
        "secret": secret,
        "password": password if password else None,
        "api_env": api_env,
        "secret_env": sec_env,
        "password_env": pwd_env if pwd_env else None,
        "keyring_error": keyring_error,
    }
