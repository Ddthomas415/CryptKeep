from __future__ import annotations

from typing import Any, Dict

def make_exchange(exchange_id: str, creds: dict, *, enable_rate_limit: bool = True) -> Any:
    import ccxt  # type: ignore

    ex_id = str(exchange_id).lower().strip()
    klass = getattr(ccxt, ex_id)

    cfg: dict = {
        "enableRateLimit": bool(enable_rate_limit),
        "apiKey": creds.get("apiKey"),
        "secret": creds.get("secret"),
    }

    # Some exchanges (notably Coinbase Exchange style) use a passphrase.
    # CCXT commonly calls that field "password".
    if creds.get("passphrase"):
        cfg["password"] = creds.get("passphrase")

    # Binance reliability: allow time difference adjustment
    if ex_id.startswith("binance"):
        cfg.setdefault("options", {})
        if isinstance(cfg["options"], dict):
            cfg["options"].setdefault("adjustForTimeDifference", True)

    return klass(cfg)
