"""
review_candidate_outcomes.py
-----------------------------
Cross-references the candidate history log against the paper trade journal
to answer: did the top-ranked candidates actually perform well?

Output columns (--json for machine-readable):
  scan_ts | symbol | cand_rank | cand_score | preferred_strategy |
  trades_found | closed_trades | net_pnl | win_rate | verdict

Usage:
    python scripts/review_candidate_outcomes.py
    python scripts/review_candidate_outcomes.py --limit 20 --json
    python scripts/review_candidate_outcomes.py --since 2026-04-01
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.os.app_paths import data_dir
from services.signals.candidate_store import load_history

# ---------------------------------------------------------------------------
# Journal helpers
# ---------------------------------------------------------------------------

def _load_journal_fills() -> list[dict]:
    """Load all fills from the paper trade journal SQLite."""
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
        fills = []
        for tbl in ("fills", "journal", "trades"):
            if tbl in tables:
                rows = con.execute(f'SELECT * FROM "{tbl}"').fetchall()
                fills.extend([dict(r) for r in rows])
        con.close()
        return fills
    except Exception:
        return []


def _fills_for_symbol(fills: list[dict], symbol: str) -> list[dict]:
    sym = str(symbol).strip().upper()
    return [
        f for f in fills
        if str(f.get("symbol") or f.get("pair") or "").strip().upper() == sym
    ]


def _pnl_stats(fills: list[dict]) -> dict:
    closed = [f for f in fills if str(f.get("side") or "").lower() == "sell"
              or str(f.get("status") or "").lower() in ("closed", "filled")]
    net = sum(float(f.get("realized_pnl") or f.get("pnl") or 0) for f in closed)
    wins = sum(1 for f in closed if float(f.get("realized_pnl") or f.get("pnl") or 0) > 0)
    win_rate = (wins / len(closed) * 100) if closed else None
    return {
        "total_fills": len(fills),
        "closed_trades": len(closed),
        "net_pnl": round(net, 4),
        "win_rate_pct": round(win_rate, 1) if win_rate is not None else None,
    }


def _verdict(stats: dict, cand_rank: int) -> str:
    closed = int(stats.get("closed_trades") or 0)
    net = float(stats.get("net_pnl") or 0)
    wr = stats.get("win_rate_pct")
    if closed == 0:
        return "no_data"
    if net > 0 and (wr or 0) >= 50:
        return "positive" if cand_rank == 0 else "positive_non_top"
    if net < 0:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_report(
    *,
    limit: int = 30,
    since_ts: str | None = None,
    top_n: int = 3,
) -> list[dict]:
    history = load_history(limit=limit, since_ts=since_ts)
    fills = _load_journal_fills()

    rows = []
    for snap in history:
        ts = str(snap.get("ts") or "")
        scan_id = str(snap.get("scan_id") or "")
        candidates = list(snap.get("candidates") or [])[:top_n]

        for rank, cand in enumerate(candidates):
            symbol = str(cand.get("symbol") or "")
            score = cand.get("score") or cand.get("composite_score") or 0
            strategy = str(cand.get("preferred_strategy") or cand.get("strategy") or "")
            trade_type = str(cand.get("trade_type") or "")
            sym_fills = _fills_for_symbol(fills, symbol)
            stats = _pnl_stats(sym_fills)
            rows.append({
                "scan_ts": ts,
                "scan_id": scan_id,
                "symbol": symbol,
                "cand_rank": rank + 1,
                "cand_score": round(float(score), 3),
                "preferred_strategy": strategy,
                "trade_type": trade_type,
                **stats,
                "verdict": _verdict(stats, rank),
            })

    return rows


def _print_table(rows: list[dict]) -> None:
    if not rows:
        print("No history entries found. Run a candidate scan first.")
        return
    headers = [
        "scan_ts", "symbol", "rank", "score",
        "strategy", "closed", "net_pnl", "win%", "verdict",
    ]
    col_w = [19, 12, 4, 7, 22, 6, 8, 5, 14]
    header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_w))
    print(header_row)
    print("-" * len(header_row))
    for r in rows:
        win = f"{r['win_rate_pct']:.0f}" if r["win_rate_pct"] is not None else "—"
        pnl = f"{r['net_pnl']:+.4f}" if r["net_pnl"] else "0.0000"
        ts = str(r["scan_ts"] or "")[:19]
        cols = [
            ts, r["symbol"], str(r["cand_rank"]),
            f"{r['cand_score']:.3f}", r["preferred_strategy"],
            str(r["closed_trades"]), pnl, win, r["verdict"],
        ]
        print("  ".join(str(c).ljust(w) for c, w in zip(cols, col_w)))


def main() -> None:
    ap = argparse.ArgumentParser(description="Review candidate-vs-outcome alignment")
    ap.add_argument("--limit", type=int, default=30, help="Max history snapshots to scan")
    ap.add_argument("--since", type=str, default=None, help="ISO date lower bound e.g. 2026-04-01")
    ap.add_argument("--top-n", type=int, default=3, help="How many top candidates per scan to include")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of table")
    args = ap.parse_args()

    rows = build_report(limit=args.limit, since_ts=args.since, top_n=args.top_n)

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        _print_table(rows)

        # Summary
        if rows:
            with_data = [r for r in rows if r["closed_trades"] > 0]
            positive = [r for r in with_data if r["verdict"] == "positive"]
            negative = [r for r in with_data if r["verdict"] == "negative"]
            print(f"\n{len(rows)} rows | {len(with_data)} with trade data | "
                  f"{len(positive)} positive | {len(negative)} negative | "
                  f"{len(rows)-len(with_data)} no data yet")


if __name__ == "__main__":
    main()
