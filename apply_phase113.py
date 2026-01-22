# apply_phase113.py - Phase 113 launcher (analytics + drawdown + CSV export + checkpoints)
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) Analytics engine (FIFO PnL from journal fills + drawdown from paper_equity)
write("services/analytics/journal_analytics.py", r'''from __future__ import annotations
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
''')

# 2) Extend TradeJournalSQLite with a larger fetch helper
def patch_trade_journal_db(t: str) -> str:
    if "def list_fills_all" in t:
        return t
    insert = r"""
    def list_fills_all(self, limit: int = 200000) -> list[dict]:
        # Convenience: fetch a large window for analytics/export
        return self.list_fills(limit=int(limit))
"""
    anchor = " def list_fills(self"
    if anchor in t:
        return t.replace(anchor, insert + "\n" + anchor, 1)
    return t + "\n" + insert

patch("storage/trade_journal_sqlite.py", patch_trade_journal_db)

# 3) Dashboard: analytics + export
def patch_dashboard(t: str) -> str:
    if "Analytics v1 (Trade Journal + Equity)" in t and "Download journal CSV" in t:
        return t
    add = r'''
st.divider()
st.header("Analytics v1 (Trade Journal + Equity)")
st.caption("PnL uses FIFO on journal fills (spot-style). Drawdown uses paper_equity snapshots.")
try:
    import pandas as pd
    from storage.trade_journal_sqlite import TradeJournalSQLite
    from storage.paper_trading_sqlite import PaperTradingSQLite
    from services.analytics.journal_analytics import fifo_pnl_from_fills, max_drawdown_from_equity
    jdb = TradeJournalSQLite()
    pdb = PaperTradingSQLite()
    fills = jdb.list_fills_all(limit=200000)
    eq = pdb.list_equity(limit=5000)
    out = fifo_pnl_from_fills(fills)
    dd = max_drawdown_from_equity(eq)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Net realized PnL (FIFO - fees)", f"{out['summary']['net_realized_pnl']:.2f}")
    with c2:
        st.metric("Gross realized PnL (FIFO)", f"{out['summary']['gross_realized_pnl']:.2f}")
    with c3:
        st.metric("Total fees", f"{out['summary']['total_fees']:.2f}")
    with c4:
        st.metric("Win rate", f"{out['summary']['win_rate']*100:.1f}%")
    c5, c6, c7 = st.columns(3)
    with c5:
        st.metric("Closed trades", int(out["summary"]["closed_trades"]))
    with c6:
        st.metric("Max drawdown", f"{dd['max_drawdown']:.2f}")
    with c7:
        st.metric("Max drawdown %", f"{dd['max_drawdown_pct']*100:.2f}%")
    st.subheader("Remaining exposure (unclosed lots)")
    st.json(out["summary"]["remaining_lots_qty_by_symbol"])
    st.subheader("Closed trades (FIFO)")
    closed_df = pd.DataFrame(out["closed_trades"])
    if len(closed_df) > 0:
        st.dataframe(closed_df, use_container_width=True, height=260)
    else:
        st.info("No closed trades yet (need buy then sell).")
    st.subheader("Equity curve (paper_equity)")
    eq_df = pd.DataFrame(eq)
    if len(eq_df) > 0 and "ts" in eq_df.columns and "equity_quote" in eq_df.columns:
        # show oldest->newest
        eq_df2 = eq_df.sort_values("ts")
        st.line_chart(eq_df2.set_index("ts")["equity_quote"])
    else:
        st.info("No equity snapshots yet. Start Paper Engine to generate equity records.")
    st.subheader("Download journal CSV")
    jf_df = pd.DataFrame(fills)
    csv_bytes = jf_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download journal CSV",
        data=csv_bytes,
        file_name="trade_journal_fills.csv",
        mime="text/csv",
    )
except Exception as e:
    st.error(f"Analytics panel failed: {type(e).__name__}: {e}")
'''
    return t + "\n" + add

patch("dashboard/app.py", patch_dashboard)

# 4) CHECKPOINTS
def patch_checkpoints(t: str) -> str:
    if "## DI) Analytics v1 + Export" in t:
        return t
    return t + (
        "\n## DI) Analytics v1 + Export\n"
        "- ✅ DI1: FIFO realized PnL + win rate computed from trade_journal.sqlite journal_fills\n"
        "- ✅ DI2: Max drawdown computed from paper_equity table\n"
        "- ✅ DI3: Dashboard analytics panel (metrics + closed trades table + equity curve)\n"
        "- ✅ DI4: Dashboard Download CSV for journal fills\n"
    )

patch("CHECKPOINTS.md", patch_checkpoints)

print("OK: Phase 113 applied (analytics + drawdown + CSV export + checkpoints).")
print("Next steps:")
print("  1. Check dashboard 'Analytics v1' panel for metrics + equity curve + CSV download")
print("  2. Submit paper orders → fills → journal rows appear in analytics")