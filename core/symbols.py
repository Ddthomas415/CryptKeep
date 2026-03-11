from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from services.os.app_paths import data_dir, ensure_dirs

_CACHE: Tuple[Optional[float], Dict[str, Dict[str, str]]] = (None, {})

ensure_dirs()
DEFAULT_MAP_PATH = data_dir() / "symbol_map.json"

def _load_symbol_map(path: Path = DEFAULT_MAP_PATH) -> Dict[str, Dict[str, str]]:
    global _CACHE
    try:
        if not path.exists():
            return {}
        mtime = path.stat().st_mtime
        cached_mtime, cached_map = _CACHE
        if cached_mtime == mtime and cached_map:
            return cached_map
        data = json.loads(path.read_text(encoding="utf-8"))
        out: Dict[str, Dict[str, str]] = {}
        for venue, mp in (data or {}).items():
            if isinstance(mp, dict):
                out[str(venue).lower()] = {str(k): str(v) for k, v in mp.items()}
        _CACHE = (mtime, out)
        return out
    except Exception:
        return {}

def normalize_symbol(venue: str, symbol: str) -> str:
    v = (venue or "").lower().strip()
    s = (symbol or "").strip()
    if not s:
        return s
    mp = _load_symbol_map()
    vmap = mp.get(v, {})
    if s in vmap:
        return vmap[s]
    candidates = {s, s.upper(), s.lower()}
    if v == "binance":
        candidates |= {s.replace("-", "").replace("_", ""), s.replace("-", "").replace("_", "").lower(), s.replace("-", "").replace("_", "").upper()}
    for c in candidates:
        if c in vmap:
            return vmap[c]
    if "/" in s:
        a, b = s.split("/", 1)
        return f"{a.upper()}-{b.upper()}"
    if "-" in s:
        a, b = s.split("-", 1)
        return f"{a.upper()}-{b.upper()}"
    if "_" in s:
        a, b = s.split("_", 1)
        return f"{a.upper()}-{b.upper()}"
    u = s.upper()
    common_quotes = ["USDT", "USDC", "FDUSD", "TUSD", "BUSD", "USD", "BTC", "ETH", "EUR"]
    for q in common_quotes:
        if u.endswith(q) and len(u) > len(q):
            base = u[: -len(q)]
            return f"{base}-{q}"
    return u

def ensure_default_symbol_map(path: Path = DEFAULT_MAP_PATH) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    def csv(env: str, default: str) -> list[str]:
        v = os.environ.get(env, default)
        return [x.strip() for x in v.split(",") if x.strip()]
    bin_syms = csv("CBP_BINANCE_SYMBOLS", "btcusdt")
    cb_syms = csv("CBP_COINBASE_PRODUCTS", "BTC-USD")
    gt_syms = csv("CBP_GATEIO_PAIRS", "BTC_USDT")
    m = {
        "binance": {s: normalize_symbol("binance", s) for s in bin_syms},
        "coinbase": {s: normalize_symbol("coinbase", s) for s in cb_syms},
        "gateio": {s: normalize_symbol("gateio", s) for s in gt_syms},
    }
    path.write_text(json.dumps(m, indent=2, sort_keys=True), encoding="utf-8")
