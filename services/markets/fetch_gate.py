from __future__ import annotations
from services.markets.models import MarketRules
from services.markets.symbols import canonicalize, gate_native
from services.markets.http_json import get_json

def fetch_rules(canonical_symbol: str) -> MarketRules:
    cs = canonicalize(canonical_symbol)
    native = gate_native(cs)
    url = f"https://api.gateio.ws/api/v4/spot/currency_pairs/{native}"
    data = get_json(url, timeout_s=10.0)

    tradable = str(data.get("trade_status") or "").lower() != "untradable"
    active = bool(data.get("id")) and tradable

    min_qty = float(data.get("min_base_amount")) if data.get("min_base_amount") is not None else None
    min_notional = float(data.get("min_quote_amount")) if data.get("min_quote_amount") is not None else None

    qty_step = None
    ap = data.get("amount_precision")
    try:
        if ap is not None:
            qty_step = 10.0 ** (-int(ap))
    except Exception:
        pass

    return MarketRules("gate", cs, native, bool(active), min_notional=min_notional, min_qty=min_qty, qty_step=qty_step, meta={"trade_status": data.get("trade_status")})
