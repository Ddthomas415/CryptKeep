#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_archive_walk_forward import parse_utc_ms
from services.backtest.ohlcv_archive import load_archived_ohlcv
from services.backtest.price_action_context import build_price_action_context_artifact


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Emit research-only price-action context labels from archived OHLCV rows. "
            "This writes an optional JSON artifact only; it does not modify campaigns, "
            "strategies, gates, or execution policy."
        )
    )
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--since", default=None)
    parser.add_argument("--archive-db", type=Path, default=None)
    parser.add_argument("--swing-lookback", type=int, default=5)
    parser.add_argument("--range-lookback", type=int, default=5)
    parser.add_argument("--displacement-lookback", type=int, default=10)
    parser.add_argument("--displacement-range-multiple", type=float, default=1.5)
    parser.add_argument("--displacement-min-body-fraction", type=float, default=0.6)
    parser.add_argument("--rejection-wick-body-multiple", type=float, default=2.0)
    parser.add_argument("--rejection-wick-range-fraction", type=float, default=0.45)
    parser.add_argument("--opening-range-bars", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if archive rows are unavailable.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    loaded = load_archived_ohlcv(
        str(args.venue),
        str(args.symbol),
        timeframe=str(args.timeframe),
        limit=int(args.limit),
        since_ms=parse_utc_ms(args.since),
        db_path=str(args.archive_db) if args.archive_db is not None else None,
    )
    generated_at = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
    if not bool(loaded.get("ok")):
        payload = {
            "ok": False,
            "artifact_type": "price_action_context_labels_v1",
            "research_only": True,
            "reason": str(loaded.get("reason") or "archive_unavailable"),
            "archive": {k: v for k, v in dict(loaded).items() if k != "rows"},
            "generated_at": generated_at,
            "limitations": [
                "research_only",
                "not_strategy_config",
                "not_campaign_evidence",
                "not_promotion_evidence",
                "not_profitability_evidence",
            ],
        }
    else:
        payload = build_price_action_context_artifact(
            list(loaded.get("rows") or []),
            venue=str(loaded.get("exchange") or args.venue),
            symbol=str(loaded.get("symbol") or args.symbol),
            timeframe=str(loaded.get("timeframe") or args.timeframe),
            source=str(loaded.get("source") or "market_ohlcv_archive"),
            dataset_hash=str(loaded.get("dataset_hash") or ""),
            archive_path=str(loaded.get("archive_path") or ""),
            generated_at=generated_at,
            swing_lookback=int(args.swing_lookback),
            range_lookback=int(args.range_lookback),
            displacement_lookback=int(args.displacement_lookback),
            displacement_range_multiple=float(args.displacement_range_multiple),
            displacement_min_body_fraction=float(args.displacement_min_body_fraction),
            rejection_wick_body_multiple=float(args.rejection_wick_body_multiple),
            rejection_wick_range_fraction=float(args.rejection_wick_range_fraction),
            opening_range_bars=int(args.opening_range_bars),
        )
        payload["archive"] = {k: v for k, v in dict(loaded).items() if k != "rows"}

    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_if_not_ok and not bool(payload.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
