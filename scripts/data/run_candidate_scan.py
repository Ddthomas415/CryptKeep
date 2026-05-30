"""
scripts/run_candidate_scan.py

Run a candidate scan over the configured universe.

Usage:
    python scripts/run_candidate_scan.py
    python scripts/run_candidate_scan.py --tiers tier1 tier2
    python scripts/run_candidate_scan.py --symbols BTC/USDT ETH/USDT
    python scripts/run_candidate_scan.py --exchange coinbase --tiers coinbase_pairs
    python scripts/run_candidate_scan.py --min-score 45 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.security.exchange_factory import make_exchange
from services.signals.candidate_engine import build_candidate_list
from services.signals.candidate_store import write_candidates, diff_snapshots, load_previous_snapshot
from services.signals.universe_loader import load_universe, load_scan_defaults, all_tier_names


def _parse_args() -> argparse.Namespace:
    defaults = load_scan_defaults()
    p = argparse.ArgumentParser(
        description="CryptKeep candidate scan",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available tiers: {', '.join(all_tier_names())}",
    )
    p.add_argument("--symbols", nargs="+", default=None,
                   help="Override symbol list (space-separated). Bypasses universe config.")
    p.add_argument("--tiers", nargs="+", default=None,
                   help="Universe tiers to scan (default: standard_scan_tiers from config)")
    p.add_argument("--exchange", type=str, default="coinbase",
                   help="Exchange ID (default: coinbase)")
    p.add_argument("--timeframe", type=str, default=defaults.get("timeframe", "1h"),
                   help=f"OHLCV timeframe (default: {defaults.get('timeframe', '1h')})")
    p.add_argument("--limit", type=int, default=int(defaults.get("limit", 200)),
                   help="OHLCV bar limit per symbol")
    p.add_argument("--min-score", type=float,
                   default=float(defaults.get("min_composite_score", 38.0)),
                   help="Minimum composite score to include in output")
    p.add_argument("--json", action="store_true", help="Output JSON instead of table")
    p.add_argument("--no-save", action="store_true", help="Skip saving to candidate store")
    p.add_argument("--diff", action="store_true", help="Show diff vs previous scan")
    return p.parse_args()


def _fetch_symbol(ex, symbol: str, timeframe: str, limit: int) -> dict | None:
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        ticker = ex.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "symbol_return_pct": float(ticker.get("percentage") or 0.0),
            "ohlcv": ohlcv,
        }
    except Exception as e:
        print(f"  SKIP {symbol}: {type(e).__name__}", file=sys.stderr)
        return None


def _print_table(candidates: list[dict]) -> None:
    if not candidates:
        print("No candidates above score threshold.")
        return
    hdr = f"{'SYMBOL':<14} {'SCORE':>6}  {'TYPE':<14} {'STRATEGY':<22} {'CONF':<8} {'REASON'}"
    print(hdr)
    print("-" * len(hdr))
    for c in candidates:
        sym    = str(c.get("symbol") or "")[:13]
        score  = f"{float(c.get('composite_score') or 0):.2f}"
        ttype  = str(c.get("trade_type") or "")[:13]
        strat  = str(c.get("preferred_strategy") or "—")[:21]
        conf   = str(c.get("confidence") or "")[:7]
        reason = str(c.get("mapping_reason") or "")[:40]
        print(f"{sym:<14} {score:>6}  {ttype:<14} {strat:<22} {conf:<8} {reason}")


def main() -> None:
    args = _parse_args()

    # Resolve symbol list
    if args.symbols:
        symbols = [s.strip() for s in args.symbols if s.strip()]
        print(f"Scanning {len(symbols)} symbols (explicit list)", file=sys.stderr)
    else:
        symbols = load_universe(tiers=args.tiers)
        tier_label = ", ".join(args.tiers) if args.tiers else "standard_scan_tiers"
        print(f"Scanning {len(symbols)} symbols from tiers: {tier_label}", file=sys.stderr)

    if not symbols:
        print("ERROR: no symbols to scan", file=sys.stderr)
        sys.exit(1)

    # Fetch market data
    ex = make_exchange(args.exchange, {"apiKey": None, "secret": None}, enable_rate_limit=True)
    try:
        print(f"Fetching {args.timeframe} OHLCV (limit={args.limit})...", file=sys.stderr)
        symbols_data = []
        for sym in symbols:
            row = _fetch_symbol(ex, sym, args.timeframe, args.limit)
            if row:
                symbols_data.append(row)
    finally:
        if hasattr(ex, "close"):
            ex.close()

    if not symbols_data:
        print("ERROR: no market data fetched", file=sys.stderr)
        sys.exit(1)

    # Build candidates
    candidates = build_candidate_list(
        symbols_data=symbols_data,
        min_composite_score=args.min_score,
    )

    # Save
    if not args.no_save:
        path = write_candidates(candidates)
        print(f"Saved {len(candidates)} candidates → {path}", file=sys.stderr)

    # Diff
    if args.diff:
        prev = load_previous_snapshot()
        if prev.get("candidates"):
            from services.signals.candidate_store import diff_snapshots
            d = diff_snapshots(candidates, prev["candidates"])
            print(f"\nDiff vs {prev.get('ts', 'previous')}:", file=sys.stderr)
            if d["new"]:      print(f"  New:      {[r['symbol'] for r in d['new']]}", file=sys.stderr)
            if d["dropped"]:  print(f"  Dropped:  {[r['symbol'] for r in d['dropped']]}", file=sys.stderr)
            if d["moved_up"]: print(f"  Moved up: {[r['symbol'] for r in d['moved_up']]}", file=sys.stderr)
            if d["moved_dn"]: print(f"  Moved dn: {[r['symbol'] for r in d['moved_dn']]}", file=sys.stderr)

    # Output
    if args.json:
        print(json.dumps(candidates, indent=2, default=str))
    else:
        _print_table(candidates)
        print(f"\n{len(candidates)} candidates | {len(symbols_data)}/{len(symbols)} symbols fetched")


if __name__ == "__main__":
    main()
