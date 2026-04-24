#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from services.market_data.symbol_scanner import scan


def main() -> int:
    ap = argparse.ArgumentParser(description="Run crypto symbol scanner")
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    args = ap.parse_args()

    result = scan(venue=args.venue)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"Scanned: {result.get('scanned', 0)} symbols @ {result.get('ts')}")
    print()

    def _print_bucket(title: str, rows: list[dict], limit: int = 10) -> None:
        print(f"{title} ({len(rows)} found)")
        for r in rows[:limit]:
            print(
                f"  {str(r.get('symbol')):12} "
                f"chg={r.get('change_pct')}%  "
                f"vol_surge={r.get('volume_surge')}x  "
                f"rsi={r.get('rsi')}"
            )
        print()

    _print_bucket("PUMPS", result.get("pumps", []))
    _print_bucket("DUMPS", result.get("dumps", []))
    _print_bucket("VOLUME SURGES", result.get("volume_surges", []))
    _print_bucket("OVERSOLD", result.get("oversold", []))

    errors = result.get("errors", [])
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for r in errors[:10]:
            print(f"  {r.get('symbol')}: {r.get('error')}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
