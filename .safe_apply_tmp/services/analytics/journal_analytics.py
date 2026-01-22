from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math

@dataclass
class Lot:
    qty: float
    price: float  # entry price
    ts: str

@dataclass
class ClosedTrade:
    symbol: str
    side: str  # "long" only for now (spot-style)
    entry_ts: str
    exit_ts: str
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    fees: float

def _f(x) -> float:
    try:
        v = float(x)
        if not math.isfinite(v):
            return 0.0
        return v
    except Exception:
        return 0.0

def fifo_pnl_from_fills(journal_fills: List[dict]) -> dict:
    """
    Compute realized PnL using FIFO lots per symbol.
    Assumes spot-style: buys add lots; sells close FIFO lots.
    Returns summary + list of ClosedTrade dicts.
    """
    # oldest -> newest
    fills = sorted(journal_fills, key=lambda r: str(r.get("fill_ts") or r.get("journal_ts") or ""))
    lots: Dict[str, List[Lot]] = {}
    closed: List[ClosedTrade] = []
    total_fees = 0.0
    gross_realized = 0.0
    for f in fills:
        sym = str(f.get("symbol") or "").strip()
        side = str(f.get("side") or "").lower().strip()
        qty = _f(f.get("qty"))
        px = _f(f.get("price"))
        fee = _f(f.get("fee"))
        ts = str(f.get("fill_ts") or f.get("journal_ts") or "")
        if not sym or qty <= 0 or px <= 0:
            continue
        total_fees += fee
        lots.setdefault(sym, [])
        if side == "buy":
            lots[sym].append(Lot(qty=qty, price=px, ts=ts))
            continue
        if side == "sell":
            remaining = qty
            while remaining > 1e-12 and lots[sym]:
                lot = lots[sym][0]
                close_qty = min(lot.qty, remaining)
                pnl = (px - lot.price) * close_qty
                gross_realized += pnl
                closed.append(ClosedTrade(
                    symbol=sym,
                    side="long",
                    entry_ts=lot.ts,
                    exit_ts=ts,
                    entry_price=lot.price,
                    exit_price=px,
                    qty=close_qty,
                    pnl=pnl,
                    fees=0.0,  # fees handled separately; we keep total fees in summary
                ))
                lot.qty -= close_qty
                remaining -= close_qty
                if lot.qty <= 1e-12:
                    lots[sym].pop(0)
            # If user sells more than position, we ignore excess for PnL calc
            continue
    # win rate from closed trades
    wins = sum(1 for t in closed if t.pnl > 0)
    losses = sum(1 for t in closed if t.pnl < 0)
    n_closed = len(closed)
    win_rate = (wins / n_closed) if n_closed else 0.0
    avg_win = (sum(t.pnl for t in closed if t.pnl > 0) / wins) if wins else 0.0
    avg_loss = (sum(t.pnl for t in closed if t.pnl < 0) / losses) if losses else 0.0
    net_realized = gross_realized - total_fees
    # exposure: remaining lots market value unknown here; just report remaining qty
    remaining_by_symbol = {s: sum(l.qty for l in ls) for s, ls in lots.items() if ls}
    return {
        "summary": {
            "fills": len(fills),
            "closed_trades": n_closed,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "gross_realized_pnl": gross_realized,
            "total_fees": total_fees,
            "net_realized_pnl": net_realized,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "remaining_lots_qty_by_symbol": remaining_by_symbol,
        },
        "closed_trades": [t.__dict__ for t in closed],
    }

def max_drawdown_from_equity(equity_rows: List[dict]) -> dict:
    """
    Compute max drawdown from paper_equity rows.
    Expects rows with keys: ts, equity_quote.
    """
    if not equity_rows:
        return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}
    # oldest -> newest
    rows = sorted(equity_rows, key=lambda r: str(r.get("ts") or ""))
    peak = None
    max_dd = 0.0
    max_dd_pct = 0.0
    peak_ts = None
    trough_ts = None
    for r in rows:
        eq = _f(r.get("equity_quote"))
        ts = str(r.get("ts") or "")
        if peak is None or eq > peak:
            peak = eq
            peak_ts = ts
        if peak and peak > 0:
            dd = peak - eq
            dd_pct = dd / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct
                trough_ts = ts
    return {
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "peak_ts": peak_ts,
        "trough_ts": trough_ts,
    }
