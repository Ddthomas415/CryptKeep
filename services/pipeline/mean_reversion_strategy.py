from __future__ import annotations

from services.markets.symbols import env_symbol
import os
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.market_data.ccxt_market_data import CCXTMarketData, MarketDataCfg
from services.execution.intent_writer import IntentWriter, IntentWriterCfg
from services.os.app_paths import data_dir, ensure_dirs
from storage.strategy_state_store_sqlite import StrategyStateStore
from storage.ops_event_store_sqlite import OpsEventStore

ensure_dirs()

def _sma(values: List[float], n: int) -> float:
    if n <= 0 or len(values) < n:
        return float("nan")
    return sum(values[-n:]) / float(n)

def _std(values: List[float], n: int) -> float:
    if n <= 1 or len(values) < n:
        return float("nan")
    mu = _sma(values, n)
    var = sum((x - mu) ** 2 for x in values[-n:]) / float(n)
    return var ** 0.5

@dataclass
class MeanReversionCfg:
    exec_db: str = str(data_dir() / "execution.sqlite")
    exchange_id: str = "coinbase"
    symbol: str = env_symbol(venue=os.environ.get("CBP_VENUE") or "coinbase")
    timeframe: str = "5m"
    ohlcv_limit: int = 300

    # bollinger
    bb_window: int = 20
    bb_k: float = 2.0

    # sizing
    mode: str = "paper"
    fixed_qty: float = 0.0
    quote_notional: float = 0.0

    # behavior
    only_on_new_bar: bool = True
    # optional: avoid trading when inside bands
    trade_only_outside_bands: bool = True

class MeanReversionBBPipeline:
    STRATEGY_ID = "mean_reversion_bb_v1"

    def __init__(self, cfg: MeanReversionCfg):
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

    def run_once(self) -> Dict[str, Any]:
        ex = self.cfg.exchange_id.lower().strip()
        sym = self.cfg.symbol.upper().strip()
        tf = self.cfg.timeframe

        ohlcv = self.md.ohlcv(sym, tf, limit=int(self.cfg.ohlcv_limit))
        if not ohlcv or len(ohlcv) < (int(self.cfg.bb_window) + 5):
            return {"ok": False, "note": "not_enough_data", "rows": len(ohlcv) if ohlcv else 0}

        closes = [float(r[4]) for r in ohlcv]
        times = [int(r[0]) for r in ohlcv]
        last_bar_ts = times[-1]
        last_px = closes[-1]

        st = self.state.get(strategy_id=self.STRATEGY_ID, exchange=ex, symbol=sym, timeframe=tf) or {}
        prev_seen_ts = st.get("last_bar_ts_ms")

        if self.cfg.only_on_new_bar and prev_seen_ts is not None and int(prev_seen_ts) == int(last_bar_ts):
            return {"ok": True, "note": "no_new_bar", "last_bar_ts_ms": last_bar_ts}

        w = int(self.cfg.bb_window)
        k = float(self.cfg.bb_k)

        mid = _sma(closes, w)
        sd = _std(closes, w)
        if sd != sd:  # NaN
            return {"ok": False, "note": "bb_failed"}

        upper = mid + k * sd
        lower = mid - k * sd

        signal = None
        # Mean reversion: buy below lower band, sell above upper band
        if last_px < lower:
            signal = "buy"
        elif last_px > upper:
            signal = "sell"

        # update state even if no signal (prevents repeats)
        self.state.upsert(
            strategy_id=self.STRATEGY_ID,
            exchange=ex,
            symbol=sym,
            timeframe=tf,
            last_bar_ts_ms=last_bar_ts,
            last_signal=signal,
            last_intent_id=st.get("last_intent_id"),
            meta_json=json.dumps({"bb_window": w, "bb_k": k, "mid": mid, "upper": upper, "lower": lower, "close": last_px}, sort_keys=True),
        )

        if not signal:
            return {"ok": True, "note": "no_signal", "last_bar_ts_ms": last_bar_ts, "close": last_px, "mid": mid, "upper": upper, "lower": lower}

        # duplicate guard: same bar + same signal => skip
        if st and st.get("last_bar_ts_ms") is not None and int(st.get("last_bar_ts_ms")) == int(last_bar_ts) and (st.get("last_signal") == signal):
            return {"ok": True, "note": "duplicate_guard_hit", "signal": signal, "last_bar_ts_ms": last_bar_ts}

        qty = self._calc_qty(last_px)
        if qty <= 0:
            self.ops.add(
                severity="WARN",
                event_type="pipeline_no_qty",
                message="Mean reversion signal produced but sizing returned qty<=0",
                meta={"exchange": ex, "symbol": sym, "timeframe": tf, "signal": signal, "last_price": last_px, "fixed_qty": self.cfg.fixed_qty, "quote_notional": self.cfg.quote_notional},
            )
            return {"ok": False, "note": "qty_zero", "signal": signal}

        meta = {
            "strategy": self.STRATEGY_ID,
            "timeframe": tf,
            "bar_ts_ms": last_bar_ts,
            "close": last_px,
            "bb_window": w,
            "bb_k": k,
            "bb_mid": mid,
            "bb_upper": upper,
            "bb_lower": lower,
        }

        try:
            intent_id = self.writer.create_intent(
                exchange=ex,
                symbol=sym,
                mode=self.cfg.mode,
                side=signal,
                qty=float(qty),
                order_type="market",
                price=None,
                meta=meta,
                status="pending",
                strategy_id=self.STRATEGY_ID,
                source="pipeline",
                enqueue_execution=True,
            )
        except Exception as e:
            self.ops.add(
                severity="ERROR",
                event_type="pipeline_intent_rejected",
                message="IntentWriter rejected or failed to create intent",
                meta={"error": f"{type(e).__name__}: {e}", "meta": meta},
            )
            return {"ok": False, "note": "intent_create_failed", "error": f"{type(e).__name__}: {e}", "signal": signal}

        self.state.upsert(
            strategy_id=self.STRATEGY_ID,
            exchange=ex,
            symbol=sym,
            timeframe=tf,
            last_bar_ts_ms=last_bar_ts,
            last_signal=signal,
            last_intent_id=intent_id,
            meta_json=json.dumps(meta, sort_keys=True),
        )

        self.ops.add(
            severity="INFO",
            event_type="pipeline_intent_created",
            message="Mean reversion created intent",
            meta={"intent_id": intent_id, **meta},
        )
        return {"ok": True, "note": "intent_created", "intent_id": intent_id, "signal": signal, "qty": qty, "last_bar_ts_ms": last_bar_ts}
