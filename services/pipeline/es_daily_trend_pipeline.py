"""Supervised pipeline adapter for ES Daily Trend."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from services.execution.intent_writer import IntentWriter, IntentWriterCfg
from services.market_data.ccxt_market_data import CCXTMarketData, MarketDataCfg
from services.os.app_paths import data_dir, ensure_dirs
from services.strategies.es_daily_trend import signal_from_ohlcv
from storage.ops_event_store_sqlite import OpsEventStore
from storage.strategy_state_store_sqlite import StrategyStateStore

ensure_dirs()

STRATEGY_ID = "es_daily_trend_v1"
MIN_OHLCV_BARS = 220


@dataclass
class ESDailyTrendCfg:
    exec_db: str = str(data_dir() / "execution.sqlite")
    exchange_id: str = ""
    symbol: str = ""
    timeframe: str = "1d"
    ohlcv_limit: int = 220
    sma_period: int = 200
    atr_period: int = 20
    mode: str = ""
    fixed_qty: float = 0.0
    quote_notional: float = 0.0
    only_on_new_bar: bool = True


class ESDailyTrendPipeline:
    STRATEGY_ID = STRATEGY_ID

    def __init__(self, cfg: ESDailyTrendCfg) -> None:
        self.cfg = cfg
        self.state = StrategyStateStore(exec_db=cfg.exec_db)
        self.ops = OpsEventStore(exec_db=cfg.exec_db)
        self.md = CCXTMarketData(MarketDataCfg(exchange_id=cfg.exchange_id, default_type="spot", sandbox=False))
        self.writer = IntentWriter(IntentWriterCfg(exec_db=cfg.exec_db, cfg_path="config/trading.yaml"))

    def _calc_qty(self, last_price: float) -> float:
        if self.cfg.fixed_qty and self.cfg.fixed_qty > 0:
            return float(self.cfg.fixed_qty)
        if self.cfg.quote_notional and self.cfg.quote_notional > 0 and last_price > 0:
            return float(self.cfg.quote_notional) / float(last_price)
        return 0.0

    def run_once(self) -> dict[str, Any]:
        ex = self.cfg.exchange_id.lower().strip()
        sym = self.cfg.symbol.upper().strip()
        tf = "1d"

        limit = max(int(self.cfg.ohlcv_limit), MIN_OHLCV_BARS)
        ohlcv = self.md.ohlcv(sym, tf, limit=limit)
        if not ohlcv or len(ohlcv) < MIN_OHLCV_BARS:
            return {"ok": False, "note": "not_enough_data", "rows": len(ohlcv) if ohlcv else 0, "required": MIN_OHLCV_BARS}

        last_bar_ts = int(ohlcv[-1][0])
        last_px = float(ohlcv[-1][4])

        st = self.state.get(strategy_id=self.STRATEGY_ID, exchange=ex, symbol=sym, timeframe=tf) or {}

        if self.cfg.only_on_new_bar and st.get("last_bar_ts_ms") is not None and int(st["last_bar_ts_ms"]) == last_bar_ts:
            return {"ok": True, "note": "no_new_bar", "last_bar_ts_ms": last_bar_ts}

        sig = signal_from_ohlcv(ohlcv, sma_period=int(self.cfg.sma_period), atr_period=int(self.cfg.atr_period))
        action = str(sig.get("action") or "hold").lower().strip()

        if not bool(sig.get("ok", False)) or action == "hold":
            self.state.upsert(
                strategy_id=self.STRATEGY_ID,
                exchange=ex,
                symbol=sym,
                timeframe=tf,
                last_bar_ts_ms=last_bar_ts,
                last_signal=None,
                last_intent_id=st.get("last_intent_id"),
                meta_json=json.dumps(sig, sort_keys=True),
            )
            return {"ok": True, "note": sig.get("reason") or "no_signal", "last_bar_ts_ms": last_bar_ts, "regime": sig.get("regime")}

        qty = self._calc_qty(last_px)
        if qty <= 0:
            self.ops.add(
                severity="WARN",
                event_type="pipeline_no_qty",
                message="ES Daily Trend signal produced but sizing returned qty<=0",
                meta={"exchange": ex, "symbol": sym, "timeframe": tf, "signal": action, "last_price": last_px},
            )
            return {"ok": False, "note": "qty_zero", "signal": action}

        meta = {
            "strategy": self.STRATEGY_ID,
            "timeframe": tf,
            "bar_ts_ms": last_bar_ts,
            "close": last_px,
            "sma_period": int(self.cfg.sma_period),
            "atr_period": int(self.cfg.atr_period),
            "signal": action,
            "regime": sig.get("regime"),
            "sma_200": sig.get("sma_200"),
            "atr_ratio": sig.get("atr_ratio"),
            "entry_allowed": sig.get("entry_allowed"),
        }

        intent_id = self.writer.create_intent(
            exchange=ex,
            symbol=sym,
            mode=self.cfg.mode,
            side=action,
            qty=float(qty),
            order_type="market",
            price=None,
            meta=meta,
            status="pending",
            strategy_id=self.STRATEGY_ID,
            source="pipeline",
            enqueue_execution=True,
        )

        self.state.upsert(
            strategy_id=self.STRATEGY_ID,
            exchange=ex,
            symbol=sym,
            timeframe=tf,
            last_bar_ts_ms=last_bar_ts,
            last_signal=action,
            last_intent_id=intent_id,
            meta_json=json.dumps(meta, sort_keys=True),
        )

        self.ops.add(
            severity="INFO",
            event_type="pipeline_intent_created",
            message="ES Daily Trend created intent",
            meta={"intent_id": intent_id, **meta},
        )

        return {"ok": True, "note": "intent_created", "intent_id": intent_id, "signal": action, "qty": qty, "last_bar_ts_ms": last_bar_ts}
