from __future__ import annotations
import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Sequence

from adapters.exchanges.binance.market_ws import BinanceMarketDataFeed
from adapters.exchanges.coinbase_adv.market_ws import CoinbaseAdvancedMarketDataFeed
from adapters.exchanges.gateio.market_ws import GateIOMarketDataFeed
from storage.event_store_sqlite import SQLiteEventStore

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _csv(env: str, default: str) -> list[str]:
    v = os.environ.get(env, default)
    return [x.strip() for x in v.split(",") if x.strip()]

def _setup_logging() -> None:
    level = os.environ.get("CBP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)sZ %(levelname)s %(name)s: %(message)s",
    )

async def _run_feed(
    name: str,
    feed,
    symbols: Sequence[str],
    channels: Sequence[str],
    store: SQLiteEventStore,
    stats: Dict[str, Any],
    lock: asyncio.Lock,
) -> None:
    log = logging.getLogger(f"collector.{name}")
    await feed.connect()
    await feed.subscribe(symbols=symbols, channels=channels)
    count = 0
    last_report = time.monotonic()
    async for e in feed.events():
        await store.append(e)
        count += 1
        async with lock:
            s = stats.setdefault(name, {"events": 0, "last_event_ts": None, "errors": 0})
            s["events"] += 1
            s["last_event_ts"] = e.ts.isoformat()
        now = time.monotonic()
        if now - last_report >= 10.0:
            dt = now - last_report
            rate = count / dt if dt > 0 else 0.0
            log.info("events_last_10s=%d rate=%.1f/s", count, rate)
            count = 0
            last_report = now

async def _heartbeat_loop(store: SQLiteEventStore, enable: list[str], channels: list[str], stats: Dict[str, Any], lock: asyncio.Lock) -> None:
    while True:
        await asyncio.sleep(5.0)
        async with lock:
            detail = {"feeds": enable, "channels": channels, "stats": stats}
        await store.heartbeat(ts_iso=utc_now_iso(), service="data_collector", status="running", detail=detail)

async def main() -> None:
    _setup_logging()
    log = logging.getLogger("collector")
    enable = _csv("CBP_FEEDS", "binance,coinbase,gateio")
    channels = _csv("CBP_CHANNELS", "trades,book_l2")
    Path("data").mkdir(exist_ok=True)
    store = SQLiteEventStore(path=Path("data") / "events.sqlite")  # ← Fixed: use Path object
    stats: Dict[str, Any] = {}
    lock = asyncio.Lock()
    tasks: list[asyncio.Task] = []
    hb = asyncio.create_task(_heartbeat_loop(store, enable, channels, stats, lock))
    tasks.append(hb)
    if "binance" in enable:
        symbols = _csv("CBP_BINANCE_SYMBOLS", "btcusdt")
        tasks.append(asyncio.create_task(_run_feed("binance", BinanceMarketDataFeed(), symbols, channels, store, stats, lock)))
    if "coinbase" in enable:
        jwt = os.environ.get("CBP_COINBASE_JWT")
        products = _csv("CBP_COINBASE_PRODUCTS", "BTC-USD")
        tasks.append(asyncio.create_task(_run_feed("coinbase", CoinbaseAdvancedMarketDataFeed(jwt=jwt), products, channels, store, stats, lock)))
    if "gateio" in enable:
        pairs = _csv("CBP_GATEIO_PAIRS", "BTC_USDT")
        tasks.append(asyncio.create_task(_run_feed("gateio", GateIOMarketDataFeed(), pairs, channels, store, stats, lock)))
    if len(tasks) <= 1:
        raise RuntimeError("No feeds enabled. Set CBP_FEEDS (e.g., binance,coinbase,gateio).")
    log.info("started feeds=%s channels=%s", enable, channels)
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        log.warning("keyboard interrupt; shutting down")
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
