from __future__ import annotations

from typing import Any, Optional, Dict

from services.security.exchange_factory import resolve_exchange_id

def get_adapter(venue: str, *, sandbox: Optional[bool] = None, **kwargs: Any):
    """Return a CCXT exchange instance for `venue`.

    Compatibility shim for legacy imports:
        from services.execution.adapters.factory import get_adapter
    """
    mode = str(kwargs.pop("mode", "") or "").lower().strip()
    if mode == "paper":
        from services.execution.adapters.paper import PaperEngineAdapter
        return PaperEngineAdapter(venue=venue)

    import ccxt  # type: ignore  # live path only
    venue = resolve_exchange_id(venue)

    raw = venue.strip()
    ccxt_id = raw.lower().replace(" ", "").replace("-", "").replace("_", "")

    cls = getattr(ccxt, ccxt_id, None) or getattr(ccxt, raw.lower(), None)
    if cls is None:
        raise KeyError(f"Unknown ccxt venue: {venue!r} (normalized={ccxt_id!r})")

    cfg: Dict[str, Any] = {}
    # allow callers to pass config/params dicts
    if isinstance(kwargs.get("config"), dict):
        cfg.update(kwargs.pop("config"))
    if isinstance(kwargs.get("params"), dict):
        cfg.update(kwargs.pop("params"))

    # allow credentials if provided (optional)
    for k in ("apiKey", "secret", "password"):
        v = kwargs.pop(k, None)
        if v:
            cfg[k] = v

    ex = cls(cfg)

    if sandbox is True and hasattr(ex, "set_sandbox_mode"):
        ex.set_sandbox_mode(True)

    return ex
