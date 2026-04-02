from __future__ import annotations

import os
from typing import Any

from services.security.binance_guard import require_binance_allowed


class VenueResolutionError(ValueError):
    pass


def resolve_exchange_id(exchange_id: str | None) -> str:
    explicit = str(exchange_id or "").lower().strip()
    env_v = str(os.environ.get("CBP_VENUE") or "").lower().strip()
    if explicit and env_v and explicit != env_v:
        raise VenueResolutionError(f"CBP_VENUE conflict: explicit={explicit!r} env={env_v!r}")
    resolved = explicit or env_v
    if not resolved:
        raise VenueResolutionError("venue is required: pass exchange_id or set CBP_VENUE")
    return resolved


def make_exchange(
    exchange_id: str,
    creds: dict,
    *,
    enable_rate_limit: bool = True,
    sandbox: bool = False,
    require_sandbox: bool = False,
) -> Any:
    import ccxt  # type: ignore

    ex_id = resolve_exchange_id(exchange_id)
    require_binance_allowed(ex_id)

    klass = getattr(ccxt, ex_id)

    cfg: dict = {
        "enableRateLimit": bool(enable_rate_limit),
        "apiKey": creds.get("apiKey"),
        "secret": creds.get("secret"),
    }

    # Some exchanges use a passphrase; CCXT calls it "password".
    password = creds.get("password") or creds.get("passphrase")
    if password:
        cfg["password"] = password

    # Binance reliability: allow time difference adjustment
    if ex_id.startswith("binance"):
        cfg.setdefault("options", {})
        if isinstance(cfg["options"], dict):
            cfg["options"].setdefault("adjustForTimeDifference", True)

    ex = klass(cfg)
    if bool(sandbox) and not hasattr(ex, "set_sandbox_mode"):
        if require_sandbox:
            raise RuntimeError(f"sandbox_not_supported:{ex_id}")
        return ex
    if hasattr(ex, "set_sandbox_mode"):
        try:
            ex.set_sandbox_mode(bool(sandbox))
        except Exception as exc:
            if require_sandbox and bool(sandbox):
                raise RuntimeError(f"sandbox_enable_failed:{type(exc).__name__}:{exc}") from exc
    return ex


def _cbp_guard_binance(ex_id) -> None:
    # legacy shim kept for compatibility with old call sites
    require_binance_allowed(str(ex_id))
