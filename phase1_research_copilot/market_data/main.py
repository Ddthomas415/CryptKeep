from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

import ccxt
import websockets
from fastapi import FastAPI, Query

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.db import Database
from shared.logging import configure_logging
from shared.retry import retry_sync

settings = get_settings()
logger = configure_logging(settings.service_name or "market-data", settings.log_level)
db = Database(settings.database_url)

app = FastAPI(title="market-data", version="0.1.0")


class State:
    rest_last_ingest: str | None = None
    ws_last_ingest: str | None = None
    errors: int = 0


state = State()
_stop = asyncio.Event()
_rest_task: asyncio.Task | None = None
_ws_task: asyncio.Task | None = None


def _exchange() -> Any:
    exchange_id = settings.exchange_id.lower().strip()
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"unsupported_exchange:{exchange_id}")
    ex_cls = getattr(ccxt, exchange_id)
    return ex_cls({"enableRateLimit": True})


def _normalize_ws_symbol(symbol: str) -> str:
    return symbol.replace("/", "").lower()


def _insert_tick(
    *,
    ts: datetime,
    exchange: str,
    symbol: str,
    source: str,
    price: float | None,
    bid: float | None,
    ask: float | None,
    volume: float | None,
    raw_payload: dict[str, Any],
) -> None:
    db.execute(
        """
        INSERT INTO market_ticks (event_ts, exchange, symbol, source, price, bid, ask, volume, raw_payload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            ts,
            exchange,
            symbol,
            source,
            price,
            bid,
            ask,
            volume,
            json.dumps(raw_payload),
        ),
    )


async def _rest_loop() -> None:
    ex = _exchange()
    symbols = settings.exchange_symbols_list
    exchange_name = settings.exchange_id.lower().strip()

    while not _stop.is_set():
        for symbol in symbols:
            try:
                ticker = retry_sync(lambda: ex.fetch_ticker(symbol), retries=2, base_delay=0.4)
                ts_ms = int(ticker.get("timestamp") or (datetime.now(timezone.utc).timestamp() * 1000))
                ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                _insert_tick(
                    ts=ts,
                    exchange=exchange_name,
                    symbol=symbol,
                    source="rest",
                    price=float(ticker.get("last") or 0.0),
                    bid=float(ticker.get("bid") or 0.0),
                    ask=float(ticker.get("ask") or 0.0),
                    volume=float(ticker.get("baseVolume") or 0.0),
                    raw_payload=ticker,
                )
                state.rest_last_ingest = datetime.now(timezone.utc).isoformat()
            except Exception as exc:
                state.errors += 1
                logger.error(
                    "rest_ingest_failed",
                    extra={"context": {"symbol": symbol, "error": str(exc)}},
                )
                await emit_audit_event(
                    "market-data",
                    "rest_ingest_failed",
                    status="error",
                    payload={"symbol": symbol, "error": str(exc)},
                )

        await emit_audit_event(
            "market-data",
            "rest_ingest_cycle",
            payload={"symbols": symbols, "last_ingest": state.rest_last_ingest},
        )
        await asyncio.sleep(max(1.0, settings.market_rest_poll_seconds))


async def _binance_ws_loop() -> None:
    symbols = settings.exchange_symbols_list
    streams = "/".join(f"{_normalize_ws_symbol(s)}@ticker" for s in symbols)
    ws_url = f"wss://stream.binance.com:9443/stream?streams={streams}"

    while not _stop.is_set():
        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                while not _stop.is_set():
                    raw = await ws.recv()
                    payload = json.loads(raw)
                    data = payload.get("data") if isinstance(payload, dict) else None
                    if not isinstance(data, dict):
                        continue

                    symbol = str(data.get("s") or "").upper()
                    if not symbol:
                        continue

                    ts_ms = int(data.get("E") or int(datetime.now(timezone.utc).timestamp() * 1000))
                    ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                    normalized_symbol = f"{symbol[:-4]}/{symbol[-4:]}" if symbol.endswith("USDT") else symbol

                    _insert_tick(
                        ts=ts,
                        exchange="binance",
                        symbol=normalized_symbol,
                        source="ws",
                        price=float(data.get("c") or 0.0),
                        bid=float(data.get("b") or 0.0),
                        ask=float(data.get("a") or 0.0),
                        volume=float(data.get("v") or 0.0),
                        raw_payload=data,
                    )
                    state.ws_last_ingest = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            state.errors += 1
            logger.error("ws_ingest_failed", extra={"context": {"error": str(exc)}})
            await emit_audit_event(
                "market-data",
                "ws_ingest_failed",
                status="error",
                payload={"error": str(exc)},
            )
            await asyncio.sleep(2.0)


async def _noop_ws_loop() -> None:
    while not _stop.is_set():
        await asyncio.sleep(30.0)


@app.on_event("startup")
async def startup() -> None:
    global _rest_task, _ws_task
    _stop.clear()
    _rest_task = asyncio.create_task(_rest_loop())

    if settings.market_ws_enabled and settings.exchange_id.lower().strip() == "binance":
        _ws_task = asyncio.create_task(_binance_ws_loop())
    else:
        _ws_task = asyncio.create_task(_noop_ws_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    _stop.set()
    for task in (_rest_task, _ws_task):
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "service": "market-data",
        "ok": bool(db.health().get("ok")),
        "rest_last_ingest": state.rest_last_ingest,
        "ws_last_ingest": state.ws_last_ingest,
        "errors": state.errors,
        "exchange": settings.exchange_id,
        "symbols": settings.exchange_symbols_list,
    }


@app.get("/v1/market/latest")
async def latest(symbol: str = Query(..., description="Symbol like SOL/USDT")) -> dict[str, Any]:
    row = db.fetch_one(
        """
        SELECT event_ts, exchange, symbol, source, price, bid, ask, volume, raw_payload
        FROM market_ticks
        WHERE symbol = %s
        ORDER BY event_ts DESC
        LIMIT 1
        """,
        (symbol,),
    )
    return {"ok": row is not None, "tick": row}
