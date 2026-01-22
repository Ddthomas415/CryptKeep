from __future__ import annotations
import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence
import orjson
import websockets
from adapters.exchanges.binance.depth_snapshot import DepthSnapshot, fetch_depth_snapshot
from core.events import BookEvent, BookLevel, EventBase, TradeEvent

log = logging.getLogger(__name__)

def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)

@dataclass
class _DepthState:
    symbol_key: str
    rest_symbol: str
    initialized: bool = False
    last_update_id: Optional[int] = None
    buffer: List[Dict[str, Any]] = field(default_factory=list)
    snapshot_task: Optional[asyncio.Task] = None

class BinanceMarketDataFeed:
    venue = "binance"

    def __init__(self) -> None:
        self._ws = None
        self._streams: list[str] = []
        self._symbols: list[str] = []
        self._want_trades = False
        self._want_book = False
        self._closed = asyncio.Event()
        self._q: asyncio.Queue = asyncio.Queue(maxsize=10000)

    async def connect(self) -> None:
        return

    async def subscribe(self, symbols: Sequence[str], channels: Sequence[str]) -> None:
        ch = set(channels)
        self._want_trades = "trades" in ch
        self._want_book = "book_l2" in ch
        streams: list[str] = []
        sym_clean: list[str] = []
        for sym in symbols:
            s = str(sym).lower().replace("-", "").replace("_", "")
            if not s:
                continue
            sym_clean.append(s)
            if self._want_trades:
                streams.append(f"{s}@trade")
            if self._want_book:
                streams.append(f"{s}@depth@100ms")
        if not streams:
            raise ValueError("No valid channels. Use: trades, book_l2")
        self._streams = streams
        self._symbols = sym_clean

    def _url(self) -> str:
        return "wss://stream.binance.com:9443/stream?streams=" + "/".join(self._streams)

    async def _reader(self, ws) -> None:
        async for msg in ws:
            try:
                data = orjson.loads(msg)
                payload = data.get("data", data)
                await self._q.put(payload)
            except Exception:
                continue

    def _start_snapshot_if_needed(self, st: _DepthState, limit: int) -> None:
        if st.snapshot_task is None or st.snapshot_task.done():
            st.snapshot_task = asyncio.create_task(fetch_depth_snapshot(st.rest_symbol, limit=limit))

    def _emit_snapshot_event(self, st: _DepthState, snap: DepthSnapshot) -> BookEvent:
        bids = [BookLevel(price=p, size=q) for p, q in snap.bids]
        asks = [BookLevel(price=p, size=q) for p, q in snap.asks]
        return BookEvent(
            venue=self.venue,
            symbol=st.symbol_key,
            ts=datetime.now(timezone.utc),
            kind="snapshot",
            bids=bids,
            asks=asks,
            sequence=snap.last_update_id,
        )

    def _apply_delta_check(self, st: _DepthState, upd: Dict[str, Any]) -> Optional[BookEvent]:
        U = int(upd.get("U", 0))
        u = int(upd.get("u", 0))
        event_time = int(upd.get("E", 0))
        if st.last_update_id is None:
            return None
        if u <= st.last_update_id:
            return None
        if not st.initialized:
            target = st.last_update_id + 1
            if U <= target <= u:
                st.initialized = True
                st.last_update_id = u
            else:
                return None
        else:
            if U != st.last_update_id + 1:
                return None
            st.last_update_id = u
        bids = [BookLevel(price=float(p), size=float(q)) for p, q in upd.get("b", [])]
        asks = [BookLevel(price=float(p), size=float(q)) for p, q in upd.get("a", [])]
        return BookEvent(
            venue=self.venue,
            symbol=st.symbol_key,
            ts=_ms_to_dt(event_time),
            kind="delta",
            bids=bids,
            asks=asks,
            sequence=u,
        )

    async def events(self) -> AsyncIterator[EventBase]:
        backoff = 1.0
        depth_limit = int(os.environ.get("CBP_BINANCE_DEPTH_LIMIT", "1000"))
        states: Dict[str, _DepthState] = {}
        if self._want_book:
            for s in self._symbols:
                states[s] = _DepthState(symbol_key=s, rest_symbol=s.upper())
        while not self._closed.is_set():
            try:
                async with websockets.connect(self._url(), ping_interval=20, ping_timeout=60) as ws:
                    self._ws = ws
                    backoff = 1.0
                    reader = asyncio.create_task(self._reader(ws))
                    if self._want_book:
                        for st in states.values():
                            st.initialized = False
                            st.last_update_id = None
                            st.buffer.clear()
                            self._start_snapshot_if_needed(st, depth_limit)
                    try:
                        while True:
                            if self._want_book:
                                for st in states.values():
                                    if st.snapshot_task and st.snapshot_task.done() and st.last_update_id is None:
                                        snap = st.snapshot_task.result()
                                        st.last_update_id = snap.last_update_id
                                        yield self._emit_snapshot_event(st, snap)
                                        new_buf = []
                                        for upd in st.buffer:
                                            ev = self._apply_delta_check(st, upd)
                                            if ev is None:
                                                new_buf.append(upd)
                                                continue
                                            yield ev
                                        st.buffer = new_buf
                            try:
                                payload = await asyncio.wait_for(self._q.get(), timeout=0.2)
                            except asyncio.TimeoutError:
                                continue
                            et = payload.get("e")
                            if et == "trade":
                                yield TradeEvent(
                                    venue=self.venue,
                                    symbol=str(payload["s"]).lower(),
                                    ts=_ms_to_dt(int(payload["T"])),
                                    price=float(payload["p"]),
                                    size=float(payload["q"]),
                                    side=("sell" if payload.get("m") else "buy"),
                                    trade_id=str(payload.get("t")) if payload.get("t") is not None else None,
                                )
                                continue
                            if et == "depthUpdate" and self._want_book:
                                sym = str(payload.get("s", "")).lower().replace("-", "").replace("_", "")
                                st = states.get(sym)
                                if st is None:
                                    continue
                                if st.last_update_id is None:
                                    st.buffer.append(payload)
                                    if len(st.buffer) > 5000:
                                        st.buffer = st.buffer[-2000:]
                                    continue
                                ev = self._apply_delta_check(st, payload)
                                if ev is None:
                                    log.warning("binance book gap for %s; resyncing", sym)
                                    st.initialized = False
                                    st.last_update_id = None
                                    st.buffer.clear()
                                    self._start_snapshot_if_needed(st, depth_limit)
                                    continue
                                yield ev
                    finally:
                        reader.cancel()
                        await asyncio.gather(reader, return_exceptions=True)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("binance ws error; reconnecting in %.1fs: %s", min(backoff, 30.0), e)
                await asyncio.sleep(min(backoff, 30.0))
                backoff *= 2.0

    async def close(self) -> None:
        self._closed.set()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
