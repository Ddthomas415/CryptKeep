from __future__ import annotations

import asyncio
import time as _time
from datetime import datetime, timezone
from typing import AsyncIterator, Sequence

import orjson
import websockets

from core.events import BookEvent, BookLevel, EventBase, TradeEvent


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


class GateIOMarketDataFeed:
    """Gate.io Spot WS v4 (public channels).    Channels used:    - spot.trades (public)    - spot.order_book (top-level snapshot)
    """

    venue = "gateio"

    def __init__(self) -> None:
        self._ws = None
        self._pairs: list[str] = []
        self._want_trades = False
        self._want_book = False
        self._closed = asyncio.Event()

    async def connect(self) -> None:
        return

    async def subscribe(self, symbols: Sequence[str], channels: Sequence[str]) -> None:
        self._pairs = list(symbols)  # e.g. BTC_USDT
        ch = set(channels)
        self._want_trades = "trades" in ch
        self._want_book = "book_l2" in ch
        if not (self._want_trades or self._want_book):
            raise ValueError("No valid channels requested. Use channels: trades, book_l2")

    def _url(self) -> str:
        return "wss://api.gateio.ws/ws/v4/"

    async def events(self) -> AsyncIterator[EventBase]:
        backoff = 1.0
        while not self._closed.is_set():
            try:
                async with websockets.connect(self._url(), ping_interval=20, ping_timeout=60) as ws:
                    self._ws = ws
                    backoff = 1.0

                    now = int(_time.time())
                    if self._want_trades:
                        await ws.send(orjson.dumps({
                            "time": now,
                            "channel": "spot.trades",
                            "event": "subscribe",
                            "payload": self._pairs,
                        }).decode("utf-8"))

                    if self._want_book:
                        # payload: [cp, level, interval] 
                        for cp in self._pairs:
                            await ws.send(orjson.dumps({
                                "time": now,
                                "channel": "spot.order_book",
                                "event": "subscribe",
                                "payload": [cp, "5", "100ms"],
                            }).decode("utf-8"))

                    async for raw in ws:
                        msg = orjson.loads(raw)
                        if msg.get("event") != "update":
                            continue
                        channel = msg.get("channel")
                        result = msg.get("result", {})

                        if channel == "spot.trades":
                            # result has taker side, amount, price, currency_pair 
                            yield TradeEvent(
                                venue=self.venue,
                                symbol=result.get("currency_pair", ""),
                                ts=_ms_to_dt(int(msg.get("time_ms") or 0)),
                                price=float(result.get("price")),
                                size=float(result.get("amount")),
                                side=result.get("side"),
                                trade_id=str(result.get("id")) if result.get("id") is not None else None,
                            )

                        elif channel == "spot.order_book":
                            bids = [BookLevel(price=float(p), size=float(q)) for p, q in result.get("bids", [])]
                            asks = [BookLevel(price=float(p), size=float(q)) for p, q in result.get("asks", [])]
                            yield BookEvent(
                                venue=self.venue,
                                symbol=result.get("s", ""),
                                ts=_ms_to_dt(int(result.get("t"))),
                                kind="snapshot",
                                bids=bids,
                                asks=asks,
                                sequence=int(result.get("lastUpdateId")) if result.get("lastUpdateId") is not None else None,
                            )
            except Exception:
                await asyncio.sleep(min(backoff, 30.0))
                backoff *= 2.0

    async def close(self) -> None:
        self._closed.set()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
