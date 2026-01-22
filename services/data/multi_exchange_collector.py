from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import ccxt
import yaml

from storage.market_store_sqlite import MarketStore

def _safe_load_yaml(path: str = "config/trading.yaml") -> Dict[str, Any]:
    try:
        return yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}
    except Exception:
        return {}

@dataclass
class VenueCfg:
    exchange_id: str
    sandbox: bool = True
    symbols: List[str] = None  # type: ignore
    timeframe: str = "1m"
    ohlcv_limit: int = 200

@dataclass
class MultiCollectorCfg:
    venues: List[VenueCfg]
    poll_sec: float = 5.0
    db_path: str = "data/market_raw.sqlite"

def _build_ex(exchange_id: str, sandbox: bool) -> Any:
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"ccxt has no exchange id '{exchange_id}'")
    ex_cls = getattr(ccxt, exchange_id)
    ex = ex_cls({"enableRateLimit": True})
    if hasattr(ex, "set_sandbox_mode"):
        try:
            ex.set_sandbox_mode(bool(sandbox))
        except Exception:
            pass
    try:
        ex.load_markets()
    except Exception:
        pass
    return ex

def collect_venue_once(store: MarketStore, v: VenueCfg) -> Dict[str, Any]:
    out = {"exchange": v.exchange_id, "tickers": 0, "ohlcv": 0, "errors": 0}
    ex = None
    try:
        ex = _build_ex(v.exchange_id, v.sandbox)
        for sym in (v.symbols or []):
            # ticker
            try:
                t = ex.fetch_ticker(sym)
                ts = int(t.get("timestamp") or int(time.time() * 1000))
                store.upsert_ticker(
                    ts_ms=ts,
                    exchange=v.exchange_id,
                    symbol=sym,
                    bid=(float(t["bid"]) if t.get("bid") is not None else None),
                    ask=(float(t["ask"]) if t.get("ask") is not None else None),
                    last=(float(t["last"]) if t.get("last") is not None else None),
                    base_vol=(float(t.get("baseVolume")) if t.get("baseVolume") is not None else None),
                    quote_vol=(float(t.get("quoteVolume")) if t.get("quoteVolume") is not None else None),
                )
                out["tickers"] += 1
            except Exception:
                out["errors"] += 1

            # ohlcv
            try:
                bars = ex.fetch_ohlcv(sym, timeframe=v.timeframe, limit=int(v.ohlcv_limit))
                for b in bars or []:
                    store.upsert_ohlcv(
                        ts_ms=int(b[0]),
                        exchange=v.exchange_id,
                        symbol=sym,
                        timeframe=v.timeframe,
                        o=float(b[1]), h=float(b[2]), l=float(b[3]), cl=float(b[4]),
                        v=(float(b[5]) if len(b) > 5 and b[5] is not None else None),
                    )
                    out["ohlcv"] += 1
            except Exception:
                out["errors"] += 1
    finally:
        if ex is not None:
            try: ex.close()
            except Exception: pass
    return out

def run_once(cfg: MultiCollectorCfg) -> Dict[str, Any]:
    store = MarketStore(path=cfg.db_path)
    results = []
    for v in cfg.venues:
        try:
            results.append(collect_venue_once(store, v))
        except Exception as e:
            results.append({"exchange": v.exchange_id, "tickers": 0, "ohlcv": 0, "errors": 1, "fatal": str(e)})
    return {"venues": results}

def run_loop(cfg: MultiCollectorCfg) -> None:
    while True:
        out = run_once(cfg)
        print("[multi-collector]", out)
        time.sleep(float(cfg.poll_sec))

def cfg_from_yaml(path: str = "config/trading.yaml") -> MultiCollectorCfg:
    cfg = _safe_load_yaml(path)
    multi = cfg.get("multi_exchanges") or {}

    venues_cfg = multi.get("venues")
    venues: List[VenueCfg] = []

    # Default requested venues (user can override fully in config)
    defaults = [
        {"exchange_id": "coinbase", "sandbox": True, "symbols": cfg.get("symbols") or ["BTC/USDT"]},
        {"exchange_id": "binance", "sandbox": True, "symbols": cfg.get("symbols") or ["BTC/USDT"]},
        {"exchange_id": "gateio",  "sandbox": True, "symbols": cfg.get("symbols") or ["BTC/USDT"]},
    ]

    use_list = venues_cfg if isinstance(venues_cfg, list) and venues_cfg else defaults

    timeframe = str((cfg.get("collector") or {}).get("timeframe") or "1m")
    ohlcv_limit = int((cfg.get("collector") or {}).get("ohlcv_limit") or 200)

    for v in use_list:
        venues.append(VenueCfg(
            exchange_id=str(v.get("exchange_id")).lower(),
            sandbox=bool(v.get("sandbox", True)),
            symbols=list(v.get("symbols") or []),
            timeframe=str(v.get("timeframe") or timeframe),
            ohlcv_limit=int(v.get("ohlcv_limit") or ohlcv_limit),
        ))

    poll_sec = float(multi.get("poll_sec") or (cfg.get("collector") or {}).get("poll_sec") or 5.0)
    db_path = str(multi.get("db_path") or (cfg.get("collector") or {}).get("db_path") or "data/market_raw.sqlite")

    return MultiCollectorCfg(venues=venues, poll_sec=poll_sec, db_path=db_path)
