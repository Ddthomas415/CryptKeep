from __future__ import annotations
import os

def allow_binance() -> bool:
    """Binance allowed only if CBP_VENUE is binance* AND CBP_ALLOW_BINANCE=1."""
    env = (os.environ.get("CBP_VENUE") or "").lower().strip()
    allow = (os.environ.get("CBP_ALLOW_BINANCE") or "").strip() == "1"
    return env.startswith("binance") and allow

def require_binance_allowed(ex_id: str) -> None:
    ex = str(ex_id or "").lower().strip()
    if ex.startswith("binance") and not allow_binance():
        env = (os.environ.get("CBP_VENUE") or "").lower().strip()
        allow = (os.environ.get("CBP_ALLOW_BINANCE") or "").strip()
        raise RuntimeError(
            f"Refusing Binance ex_id={ex_id!r} because CBP_VENUE={env!r} and/or CBP_ALLOW_BINANCE={allow!r} != '1'"
        )
