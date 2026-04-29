from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict

from services.market_data.ws_common import normalize_ticker_message
from services.monitoring.ws_health_logger import log_ws_health
from services.market_data import ws_feature_blacklist as blacklist


def _watch_ticker_supported(exchange: Any) -> bool:
    has = getattr(exchange, "has", None)
    if isinstance(has, dict):
        return bool(has.get("watchTicker") or has.get("watch_ticker"))
    return callable(getattr(exchange, "watch_ticker", None)) or callable(getattr(exchange, "watchTicker", None))


def _watch_ticker_fn(exchange: Any):
    fn = getattr(exchange, "watch_ticker", None)
    if callable(fn):
        return fn
    fn = getattr(exchange, "watchTicker", None)
    if callable(fn):
        return fn
    return None


@dataclass(frozen=True)
class WSTickerFeedCfg:
    max_errors_before_disable: int = 10
    disable_cooldown_sec: int = 1800
    error_sleep_sec: float = 0.5


class WSTickerFeed:
    """
    Small watchTicker wrapper with the same auto-disable behavior used by
    WS feature blacklist flows.
    """

    FEATURE = "watchTicker"

    def __init__(self, *, exchange: Any, venue: str, symbol: str, cfg: WSTickerFeedCfg | None = None):
        self.exchange = exchange
        self.venue = str(venue).lower().strip()
        self.symbol = str(symbol).strip()
        self.cfg = cfg or WSTickerFeedCfg()
        self._errors = 0

    def is_disabled(self) -> Dict[str, Any]:
        return blacklist.is_disabled(venue=self.venue, symbol=self.symbol, feature=self.FEATURE)

    def _disable(self, reason: str) -> Dict[str, Any]:
        self._errors = 0
        return blacklist.disable(
            venue=self.venue,
            symbol=self.symbol,
            feature=self.FEATURE,
            reason=str(reason)[:500],
            cooldown_sec=int(self.cfg.disable_cooldown_sec),
        )

    async def next_ticker(self) -> Dict[str, Any]:
        disabled = self.is_disabled()
        if bool(disabled.get("disabled")):
            return {"ok": False, "reason": "feature_disabled", "disabled": True, "key": disabled.get("key")}

        if not _watch_ticker_supported(self.exchange):
            d = self._disable("unsupported_watchTicker")
            return {"ok": False, "reason": "unsupported_watchTicker", "disabled": True, "blacklist": d}

        fn = _watch_ticker_fn(self.exchange)
        if not callable(fn):
            d = self._disable("watchTicker_method_missing")
            return {"ok": False, "reason": "watchTicker_method_missing", "disabled": True, "blacklist": d}

        try:
            raw = await fn(self.symbol)
            self._errors = 0
            q = normalize_ticker_message(raw if isinstance(raw, dict) else {}, venue=self.venue, symbol=self.symbol)
            # Persist only successful quotes so freshness never treats a transport
            # error as a fresh market-data heartbeat.
            try:
                log_ws_health(
                    exchange=self.venue,
                    symbol=str(q.get("symbol") or self.symbol),
                    connected=True,
                    recv_ts_ms=int(q.get("ts_ms") or 0),
                    meta={"feature": self.FEATURE},
                )
            except Exception:
                pass
            return {"ok": True, "quote": q}
        except Exception as e:
            self._errors += 1
            out: Dict[str, Any] = {
                "ok": False,
                "reason": "watch_ticker_error",
                "error": f"{type(e).__name__}:{e}",
                "errors": int(self._errors),
            }
            if self._errors >= int(self.cfg.max_errors_before_disable):
                out["blacklist"] = self._disable(out["error"])
                out["disabled"] = True
            return out

    async def stream(self, *, stop_event: asyncio.Event | None = None) -> AsyncIterator[Dict[str, Any]]:
        stop = stop_event or asyncio.Event()
        while not stop.is_set():
            out = await self.next_ticker()
            if bool(out.get("ok")):
                yield out["quote"]
                continue
            await asyncio.sleep(max(0.05, float(self.cfg.error_sleep_sec)))
