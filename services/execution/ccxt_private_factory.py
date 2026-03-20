from __future__ import annotations

from typing import Any

from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange


def make_private_exchange(exchange: str, *, enable_rate_limit: bool = True) -> Any:
    ex = str(exchange).lower().strip()
    creds = load_exchange_credentials(ex)
    if not creds.get("apiKey") or not creds.get("secret"):
        raise RuntimeError(f"missing_credentials:{ex}:{str(creds.get('source') or 'unknown')}")
    return make_exchange(ex, creds, enable_rate_limit=enable_rate_limit)
