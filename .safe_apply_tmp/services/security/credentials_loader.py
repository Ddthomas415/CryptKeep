from __future__ import annotations
import os
from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue

def load_exchange_credentials(venue: str) -> dict:
    """
    Safe default: secrets come from ENV ONLY.
    config/user.yaml provides the env var NAMES.
    """
    v = normalize_venue(venue)
    cfg = load_user_yaml()
    ex = cfg.get("exchanges") if isinstance(cfg.get("exchanges"), dict) else {}
    ent = ex.get(v) if isinstance(ex.get(v), dict) else {}
    api_env = str(ent.get("api_key_env", f"{v.upper()}_API_KEY"))
    sec_env = str(ent.get("secret_env", f"{v.upper()}_API_SECRET"))
    pwd_env = str(ent.get("password_env", "")) # optional
    api_key = os.getenv(api_env, "")
    secret = os.getenv(sec_env, "")
    password = os.getenv(pwd_env, "") if pwd_env else ""
    return {
        "venue": v,
        "api_key_present": bool(api_key),
        "secret_present": bool(secret),
        "password_present": bool(password),
        "apiKey": api_key,
        "secret": secret,
        "password": password if password else None,
        "api_env": api_env,
        "secret_env": sec_env,
        "password_env": pwd_env if pwd_env else None,
    }
