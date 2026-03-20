from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict

from services.fills.user_stream_router import route_ccxt_trade
from services.os.app_paths import data_dir


def _normalize_exchange_id(exchange_id: str) -> str:
    ex = str(exchange_id or "").lower().strip()
    return {"gate": "gateio", "gate.io": "gateio", "coinbase_adv": "coinbase"}.get(ex, ex)


def _safe_close(client: Any) -> None:
    try:
        maybe = getattr(client, "close", None)
        if callable(maybe):
            out = maybe()
            if asyncio.iscoroutine(out):
                # fire-and-forget close in best effort mode
                asyncio.create_task(out)
    except Exception:
        pass


@dataclass
class UserStreamWSConfig:
    exchange_id: str
    exec_db: str = str(data_dir() / "execution.sqlite")
    symbol: str | None = None
    sandbox: bool = False
    route_via_live_executor_hook: bool = True
    retry_sleep_sec: float = 2.0


class UserStreamFillService:
    """
    Optional user-stream fills service.
    - Reads authenticated user trade updates from WS adapters (ccxt.pro)
    - Routes every trade through route_ccxt_trade(...), which enforces the FillSink choke point
      and optionally the live executor _on_fill hook.
    """

    def __init__(self, cfg: UserStreamWSConfig):
        self.cfg = cfg
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    def _build_ws_client(self) -> Any | None:
        ex_id = _normalize_exchange_id(self.cfg.exchange_id)
        try:
            import ccxt.pro as ccxtpro  # type: ignore
        except Exception:
            return None

        ex_cls = getattr(ccxtpro, ex_id, None)
        if ex_cls is None:
            return None

        try:
            from services.execution.exchange_client import credentials_from_env

            params: Dict[str, Any] = {"enableRateLimit": True}
            params.update(credentials_from_env(ex_id))
            client = ex_cls(params)
            if hasattr(client, "set_sandbox_mode"):
                try:
                    client.set_sandbox_mode(bool(self.cfg.sandbox))
                except Exception:
                    pass
            return client
        except Exception:
            return None

    async def run_once(self, *, client: Any | None = None) -> Dict[str, Any]:
        ex = client if client is not None else self._build_ws_client()
        if ex is None:
            return {"ok": False, "reason": "ws_client_unavailable", "processed": 0}

        watch = getattr(ex, "watch_my_trades", None)
        if not callable(watch):
            watch = getattr(ex, "watchMyTrades", None)
        if not callable(watch):
            return {"ok": False, "reason": "watch_my_trades_not_supported", "processed": 0}

        if self.cfg.symbol:
            trades = await watch(str(self.cfg.symbol))
        else:
            trades = await watch()

        processed = 0
        for trade in list(trades or []):
            out = route_ccxt_trade(
                self.cfg.exchange_id,
                dict(trade or {}),
                exec_db=self.cfg.exec_db,
                prefer_live_executor_hook=bool(self.cfg.route_via_live_executor_hook),
            )
            if bool(out.get("ok")):
                processed += 1

        return {"ok": True, "processed": processed}

    async def run_forever(self) -> Dict[str, Any]:
        ex = self._build_ws_client()
        if ex is None:
            return {"ok": False, "reason": "ws_client_unavailable"}

        loops = 0
        last_error = ""
        try:
            while not self._stop.is_set():
                loops += 1
                try:
                    await self.run_once(client=ex)
                    last_error = ""
                    # Cooperative yield so stop() and other tasks can run.
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    last_error = f"{type(e).__name__}:{e}"
                    await asyncio.sleep(max(0.1, float(self.cfg.retry_sleep_sec)))
        finally:
            _safe_close(ex)
        return {"ok": True, "loops": loops, "last_error": last_error}

