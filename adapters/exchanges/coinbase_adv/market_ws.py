from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, Sequence

import orjson
import websockets

from core.events import BookEvent, BookLevel, EventBase, TradeEvent


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


class CoinbaseAdvancedMarketDataFeed:
    """Coinbase Advanced Trade Market Data WS (read-only).

    Endpoint: wss://advanced-trade-ws.coinbase.com 
    Notes:
    - Server disconnects if no subscribe is received quickly after connect. 
    - Heartbeats are recommended because many channels close after 60–90s of inactivity. 
    - Most channels are available without auth, but authenticating is recommended for reliability. 
    """

    venue = "coinbase"

    def __init__(self, jwt: Optional[str] = None) -> None:
        self._ws = None
        self._products: list[str] = []
        self._channels: list[str] = []
        self._jwt = jwt
        self._closed = asyncio.Event()

    async def connect(self) -> None:
        return

    async def subscribe(self, symbols: Sequence[str], channels: Sequence[str]) -> None:
        self._products = list(symbols)
        ch = set(channels)
        self._channels = []
        if "trades" in ch:
            self._channels.append("market_trades")
        if "book_l2" in ch:
            self._channels.append("level2")
        # Keep connections open for sparse symbols.
        if "heartbeats" not in self._channels:
            self._channels.append("heartbeats")

    def _url(self) -> str:
        return "wss://advanced-trade-ws.coinbase.com"

    async def events(self) -> AsyncIterator[EventBase]:
        backoff = 1.0
        while not self._closed.is_set():
            try:
                async with websockets.connect(self._url(), ping_interval=20, ping_timeout=60) as ws:
                    self._ws = ws
                    backoff = 1.0

                    # Subscribe (must happen shortly after connect) 
                    for ch in self._channels:
                        sub = {"type": "subscribe", "product_ids": self._products, "channel": ch}
                        if self._jwt:
                            sub["jwt"] = self._jwt
                        await ws.send(orjson.dumps(sub).decode("utf-8"))

                    async for raw in ws:
                        msg = orjson.loads(raw)
                        channel = msg.get("channel")

                        # Market trades format 
                        if channel == "market_trades":
                            for ev in msg.get("events", []):
                                for t in ev.get("trades", []):
                                    yield TradeEvent(
                                        venue=self.venue,
                                        symbol=t["product_id"],
                                        ts=_iso(t["time"]),
                                        price=float(t["price"]),
                                        size=float(t["size"]),
                                        side=("buy" if t.get("side") == "BUY" else "sell"),
                                        trade_id=str(t.get("trade_id")) if t.get("trade_id") is not None else None,
                                    )

                        # Level2 order book format (note: response channel can be "l2_data") 
                        elif channel in ("level2", "l2_data"):
                            outer_ts = msg.get("timestamp")
                            ts = _iso(outer_ts) if outer_ts else datetime.now(timezone.utc)
                            seq = msg.get("sequence_num")
                            for ev in msg.get("events", []):
                                kind = "snapshot" if ev.get("type") == "snapshot" else "delta"
                                bids: list[BookLevel] = []
                                asks: list[BookLevel] = []
                                product = ev.get("product_id", "")
                                for u in ev.get("updates", []):
                                    side = u.get("side")
                                    px = float(u.get("price_level"))
                                    qty = float(u.get("new_quantity"))
                                    lvl = BookLevel(price=px, size=qty)
                                    if side == "bid":
                                        bids.append(lvl)
                                    elif side == "ask":
                                        asks.append(lvl)
                                if bids or asks:
                                    yield BookEvent(
                                        venue=self.venue,
                                        symbol=product,
                                        ts=ts,
                                        kind=kind,
                                        bids=bids,
                                        asks=asks,
                                        sequence=int(seq) if seq is not None else None,
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
