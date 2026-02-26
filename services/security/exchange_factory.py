from __future__ import annotations

import os
from typing import Any

from services.security.binance_guard import require_binance_allowed


def make_exchange(exchange_id: str, creds: dict, *, enable_rate_limit: bool = True) -> Any:
    import ccxt  # type: ignore

    ex_id = str(os.environ.get("CBP_VENUE") or exchange_id or "coinbase").lower().strip()
    require_binance_allowed(ex_id)

    klass = getattr(ccxt, ex_id)

    cfg: dict = {
        "enableRateLimit": bool(enable_rate_limit),
        "apiKey": creds.get("apiKey"),
        "secret": creds.get("secret"),
    }

    # Some exchanges use a passphrase; CCXT calls it "password".
    if creds.get("passphrase"):
        cfg["password"] = creds.get("passphrase")

    # Binance reliability: allow time difference adjustment
    if ex_id.startswith("binance"):
        cfg.setdefault("options", {})
        if isinstance(cfg["options"], dict):
            cfg["options"].setdefault("adjustForTimeDifference", True)

    return klass(cfg)


def _cbp_guard_binance(ex_id) -> None:
    # legacy shim kept for compatibility with old call sites
    require_binance_allowed(str(ex_id))
