from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import math
import time
from services.security.exchange_factory import make_exchange
from services.market_data.symbol_router import normalize_venue, map_symbol, normalize_symbol

def _f(x, default=0.0):
    try:
        v = float(x)
        if not math.isfinite(v):
            return default
        return v
    except Exception:
        return default

def fetch_ohlcv(
    venue: str,
    canonical_symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
) -> list[list]:
    v = normalize_venue(venue)
    sym = map_symbol(v, normalize_symbol(canonical_symbol))
    ex = make_exchange(v, {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        kwargs = {"timeframe": timeframe, "limit": int(limit)}
        if since_ms is not None:
            kwargs["since"] = int(since_ms)
        return ex.fetch_ohlcv(sym, **kwargs)
    finally:
        try:
            if hasattr(ex, "close"):
                ex.close()
        except Exception:
            pass

def replay_signals_on_ohlcv(
    ohlcv: list[list],
    signals: list[dict],
    *,
    fee_bps: float = 10.0,  # 0.10%
    slippage_bps: float = 5.0,  # 0.05%
    initial_cash: float = 10000.0,
) -> dict:
    sigs = []
    for s in signals:
        ts_ms = s.get("ts_ms")
        if ts_ms is None:
            try:
                ts_ms = int(float(s.get("ts")) * 1000.0)
            except Exception:
                ts_ms = 0
        sigs.append({**s, "ts_ms": int(ts_ms)})
    sigs.sort(key=lambda r: int(r.get("ts_ms") or 0))
    cash = float(initial_cash)
    pos_qty = 0.0
    pos_entry_px = None
    equity = []
    trades = []
    def find_next_idx(ts_ms: int) -> int:
        for i, row in enumerate(ohlcv):
            if int(row[0]) >= ts_ms:
                return i
        return len(ohlcv) - 1
    sig_i = 0
    for i, row in enumerate(ohlcv):
        t_ms = int(row[0])
        o = _f(row[1]); c = _f(row[4])
        while sig_i < len(sigs) and find_next_idx(sigs[sig_i]["ts_ms"]) == i:
            s = sigs[sig_i]
            act = str(s.get("action") or "").lower().strip()
            px = o
            slip = px * (slippage_bps / 10000.0)
            fee = 0.0
            if act == "buy" and pos_qty <= 1e-12:
                exec_px = px + slip
                qty = cash / exec_px if exec_px > 0 else 0.0
                notional = qty * exec_px
                fee = notional * (fee_bps / 10000.0)
                if qty > 0 and cash >= fee:
                    cash = cash - notional - fee
                    pos_qty = qty
                    pos_entry_px = exec_px
                    trades.append({"ts_ms": t_ms, "action": "buy", "qty": qty, "px": exec_px, "fee": fee})
            elif act == "sell" and pos_qty > 1e-12:
                exec_px = max(px - slip, 0.0)
                notional = pos_qty * exec_px
                fee = notional * (fee_bps / 10000.0)
                cash = cash + notional - fee
                trades.append({"ts_ms": t_ms, "action": "sell", "qty": pos_qty, "px": exec_px, "fee": fee})
                pos_qty = 0.0
                pos_entry_px = None
            sig_i += 1
        mtm = cash + pos_qty * c
        equity.append({"ts_ms": t_ms, "equity": mtm, "cash": cash, "pos_qty": pos_qty, "close": c})
    realized = 0.0
    last_buy = None
    for tr in trades:
        if tr["action"] == "buy":
            last_buy = tr
        elif tr["action"] == "sell" and last_buy:
            realized += (tr["px"] - last_buy["px"]) * last_buy["qty"] - (tr["fee"] + last_buy["fee"])
            last_buy = None
    return {
        "initial_cash": initial_cash,
        "final_equity": equity[-1]["equity"] if equity else initial_cash,
        "realized_pnl_est": realized,
        "trades": trades,
        "equity": equity,
        "signals_used": len(sigs),
    }
