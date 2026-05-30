"""
scripts/candidate_trade_summary.py

Summarise closed paper trades, broken down by candidate layer features.

Answers:
  - Which score buckets produced the best outcomes?
  - Which trade types worked?
  - Which preferred strategies from the candidate layer performed best?

Usage:
    python scripts/candidate_trade_summary.py
    python scripts/candidate_trade_summary.py --json
    python scripts/candidate_trade_summary.py --min-trades 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.os.app_paths import data_dir
from services.signals.candidate_store import load_history


# ---------------------------------------------------------------------------
# Journal helpers
# ---------------------------------------------------------------------------

def _load_closed_trades() -> list[dict]:
    """Load closed fills from the paper trade journal."""
    db = data_dir() / "trade_journal.sqlite"
    if not db.exists():
        return []
    try:
        import sqlite3
        con = sqlite3.connect(str(db), check_same_thread=False, timeout=5)
        con.row_factory = sqlite3.Row
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        trades = []
        for tbl in ("fills", "journal", "trades"):
            if tbl not in tables:
                continue
            rows = con.execute(f'SELECT * FROM "{tbl}"').fetchall()
            for r in rows:
                d = dict(r)
                pnl = float(d.get("realized_pnl") or d.get("pnl") or 0)
                side = str(d.get("side") or "").lower()
                status = str(d.get("status") or "").lower()
                if side == "sell" or status in ("closed", "filled"):
                    d["_pnl"] = pnl
                    trades.append(d)
        con.close()
        return trades
    except Exception:
        return []


def _score_bucket(score: float) -> str:
    if score >= 70:   return "high(70+)"
    if score >= 55:   return "medium(55-70)"
    if score >= 40:   return "low(40-55)"
    return "below_threshold(<40)"


def _stats(pnls: list[float]) -> dict:
    if not pnls:
        return {"count": 0, "net_pnl": 0, "win_rate": None, "avg_pnl": None}
    wins = sum(1 for p in pnls if p > 0)
    net = sum(pnls)
    return {
        "count": len(pnls),
        "net_pnl": round(net, 4),
        "win_rate_pct": round(wins / len(pnls) * 100, 1),
        "avg_pnl": round(net / len(pnls), 4),
    }


# ---------------------------------------------------------------------------
# Attribution: match trades to candidate snapshots
# ---------------------------------------------------------------------------

def _build_attribution(
    trades: list[dict],
    history: list[dict],
) -> list[dict]:
    """For each trade, find the nearest-prior candidate snapshot and attach it."""
    attributed = []
    for trade in trades:
        symbol = str(trade.get("symbol") or trade.get("pair") or "").upper()
        trade_ts = float(trade.get("timestamp") or trade.get("ts_epoch") or 0)
        pnl = float(trade.get("_pnl") or 0)

        # Find latest snapshot before the trade
        best_snap = None
        best_snap_ts = 0.0
        for snap in history:
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(str(snap.get("ts") or "").replace("Z", "+00:00"))
                snap_ts = dt.timestamp()
            except Exception:
                continue
            if snap_ts <= trade_ts and snap_ts > best_snap_ts:
                for cand in snap.get("candidates") or []:
                    if str(cand.get("symbol") or "").upper() == symbol:
                        best_snap = cand
                        best_snap_ts = snap_ts
                        break

        attributed.append({
            "symbol": symbol,
            "pnl": pnl,
            "candidate": best_snap,
        })
    return attributed


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def build_summaries(attributed: list[dict], *, min_trades: int = 1) -> dict:
    by_bucket: dict[str, list[float]]   = defaultdict(list)
    by_type:   dict[str, list[float]]   = defaultdict(list)
    by_strat:  dict[str, list[float]]   = defaultdict(list)
    by_conf:   dict[str, list[float]]   = defaultdict(list)
    no_candidate: list[float]           = []

    for row in attributed:
        pnl  = float(row.get("pnl") or 0)
        cand = row.get("candidate")

        if cand is None:
            no_candidate.append(pnl)
            continue

        score  = float(cand.get("composite_score") or 0)
        ttype  = str(cand.get("trade_type")         or "unknown")
        strat  = str(cand.get("preferred_strategy") or "unknown")
        conf   = str(cand.get("confidence")         or "unknown")

        by_bucket[_score_bucket(score)].append(pnl)
        by_type[ttype].append(pnl)
        by_strat[strat].append(pnl)
        by_conf[conf].append(pnl)

    def _filtered(d: dict) -> dict:
        return {k: _stats(v) for k, v in d.items() if len(v) >= min_trades}

    return {
        "by_score_bucket":       _filtered(by_bucket),
        "by_trade_type":         _filtered(by_type),
        "by_preferred_strategy": _filtered(by_strat),
        "by_confidence":         _filtered(by_conf),
        "no_candidate_match":    _stats(no_candidate) if len(no_candidate) >= min_trades else None,
        "total_trades":          len(attributed),
        "attributed_trades":     sum(1 for r in attributed if r.get("candidate")),
    }


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _print_section(title: str, data: dict | None) -> None:
    if not data:
        print(f"\n{title}: (no data)\n")
        return
    print(f"\n{title}")
    print("-" * 50)
    header = f"  {'KEY':<28} {'N':>4}  {'NET PNL':>9}  {'WIN%':>6}  {'AVG PNL':>9}"
    print(header)
    for key, stats in sorted(data.items(), key=lambda x: -(x[1].get("net_pnl") or 0)):
        n   = stats.get("count", 0)
        net = f"{stats['net_pnl']:+.4f}" if stats.get("net_pnl") is not None else "—"
        wr  = f"{stats['win_rate_pct']:.0f}%" if stats.get("win_rate_pct") is not None else "—"
        avg = f"{stats['avg_pnl']:+.4f}" if stats.get("avg_pnl") is not None else "—"
        print(f"  {key:<28} {n:>4}  {net:>9}  {wr:>6}  {avg:>9}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Candidate layer closed-trade summary")
    ap.add_argument("--min-trades", type=int, default=1,
                    help="Minimum trades per bucket to include in summary")
    ap.add_argument("--history-limit", type=int, default=200,
                    help="Max candidate history snapshots to search")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    trades = _load_closed_trades()
    history = load_history(limit=args.history_limit)

    if not trades:
        print("No closed trades found in paper journal.")
        if not history:
            print("No candidate history found either. Run a scan first.")
        sys.exit(0)

    attributed = _build_attribution(trades, history)
    summaries  = build_summaries(attributed, min_trades=args.min_trades)

    if args.json:
        print(json.dumps(summaries, indent=2, default=str))
        return

    print(f"=== Candidate Trade Attribution Summary ===")
    print(f"Total trades: {summaries['total_trades']} | "
          f"With candidate match: {summaries['attributed_trades']}")

    _print_section("By score bucket", summaries.get("by_score_bucket"))
    _print_section("By trade type",   summaries.get("by_trade_type"))
    _print_section("By preferred strategy", summaries.get("by_preferred_strategy"))
    _print_section("By confidence",   summaries.get("by_confidence"))

    no_cand = summaries.get("no_candidate_match")
    if no_cand:
        print(f"\nTrades with no candidate match: {no_cand}")


if __name__ == "__main__":
    main()
