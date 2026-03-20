from __future__ import annotations

import os
import json
import time
from typing import Any, Dict, Iterable, List

from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import map_symbol, normalize_symbol, normalize_venue
from services.os.app_paths import ensure_dirs, runtime_dir
from services.security.exchange_factory import make_exchange

FLAGS = runtime_dir() / "flags"
SNAPSHOTS = runtime_dir() / "snapshots"
STOP_FILE = FLAGS / "market_data_poller.stop"


def build_required_pairs(
    symbols: Iterable[str],
    *,
    include_symbols: bool = True,
    extra_pairs: Iterable[str] | None = None,
) -> list[str]:
    out: List[str] = []

    def _add(sym: str) -> None:
        s = normalize_symbol(sym)
        if s and s not in out:
            out.append(s)

    if include_symbols:
        for s in symbols:
            _add(str(s))
    if extra_pairs:
        for s in extra_pairs:
            _add(str(s))
    return out


async def fetch_tickers_once(venue: str, pairs: Iterable[str]) -> dict:
    v = normalize_venue(venue)
    pairs_list = [normalize_symbol(p) for p in pairs]
    ticks: List[Dict[str, Any]] = []
    errors: Dict[str, str] = {}
    ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        for p in pairs_list:
            sym = map_symbol(v, p)
            try:
                t = ex.fetch_ticker(sym)
                fetch_ts_ms = int(time.time() * 1000)
                ticks.append(
                    {
                        "venue": v,
                        "symbol": p,
                        "symbol_mapped": sym,
                        "bid": t.get("bid"),
                        "ask": t.get("ask"),
                        "last": t.get("last"),
                        "ts_ms": fetch_ts_ms,
                        "exchange_ts_ms": int(t.get("timestamp") or 0),
                    }
                )
            except Exception as e:
                errors[p] = f"{type(e).__name__}:{e}"
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

    return {
        "ok": len(errors) == 0,
        "venue": v,
        "pairs": pairs_list,
        "ticks": ticks,
        "errors": errors,
    }


def load_poller_cfg() -> dict:
    cfg = load_user_yaml()
    md = cfg.get("market_data_poller") if isinstance(cfg.get("market_data_poller"), dict) else {}
    pf = cfg.get("preflight") if isinstance(cfg.get("preflight"), dict) else {}
    symbols = md.get("symbols") or pf.get("symbols") or ["BTC/USD"]
    # Prefer explicit symbols from env (CBP_SYMBOLS)
    env_syms = (os.environ.get('CBP_SYMBOLS') or '').strip()
    if env_syms:
        symbols = [x.strip() for x in env_syms.split(',') if x.strip()]
    return {
        "venue": str(md.get("venue") or (os.environ.get("CBP_VENUE") or "coinbase")).lower().strip(),
        "symbols": [str(s).strip() for s in symbols],
        "interval_sec": float(md.get("interval_sec", 15.0) or 15.0),
        "include_symbols": bool(md.get("include_symbols", True)),
        "extra_pairs": md.get("extra_pairs") or [],
    }


def request_stop() -> dict:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(str(time.time()) + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}
