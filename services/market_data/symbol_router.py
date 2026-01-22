from __future__ import annotations
from services.admin.config_editor import load_user_yaml

VENUE_ALIASES = {
    "gate.io": "gateio",
    "gate": "gateio",
    "gateio": "gateio",
    "binance": "binance",
    "coinbase": "coinbase",
    "coinbasepro": "coinbase",
}

def normalize_venue(venue: str) -> str:
    v = (venue or "").strip().lower()
    return VENUE_ALIASES.get(v, v)

def normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip()
    if "-" in s and "/" not in s:
        s = s.replace("-", "/")
    parts = s.split("/")
    if len(parts) == 2:
        return f"{parts[0].upper()}/{parts[1].upper()}"
    return s.upper()

def _mapping_cfg() -> dict:
    cfg = load_user_yaml()
    sr = cfg.get("symbol_router") if isinstance(cfg.get("symbol_router"), dict) else {}
    m = sr.get("map") if isinstance(sr.get("map"), dict) else {}
    return m

def map_symbol(venue: str, canonical_symbol: str) -> str:
    v = normalize_venue(venue)
    sym = normalize_symbol(canonical_symbol)
    m = _mapping_cfg()
    per = m.get(sym) if isinstance(m.get(sym), dict) else None
    if isinstance(per, dict):
        mapped = per.get(v)
        if mapped:
            return normalize_symbol(str(mapped))
    return sym
