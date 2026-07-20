#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_archive_walk_forward import load_strategy_config
from services.analytics.funding_context_price_join import run_funding_context_price_join


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only funding_extreme forward-return report by joining "
            "stored crypto-edge funding snapshots to archived OHLCV rows. This is "
            "not portfolio PnL, expectancy, promotion, or campaign evidence."
        )
    )
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON/YAML funding_extreme config.")
    parser.add_argument("--edge-db", type=Path, default=None, help="Optional crypto-edge sqlite path.")
    parser.add_argument("--archive-db", type=Path, default=None, help="Optional market OHLCV archive sqlite path.")
    parser.add_argument("--context-source", default="live_public")
    parser.add_argument("--context-venue", default="okx")
    parser.add_argument("--context-symbol", default="BTC/USDT:USDT")
    parser.add_argument("--price-venue", default="okx")
    parser.add_argument("--price-symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--funding-limit", type=int, default=500)
    parser.add_argument("--ohlcv-limit", type=int, default=500)
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--min-joined-rows", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 when the report is not ok.")
    return parser.parse_args(argv)


def _load_cfg(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"strategy": {"name": "funding_extreme"}}
    return load_strategy_config(path)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    with contextlib.redirect_stdout(sys.stderr):
        result = run_funding_context_price_join(
            cfg=_load_cfg(args.config),
            edge_db_path=str(args.edge_db) if args.edge_db is not None else None,
            archive_db_path=str(args.archive_db) if args.archive_db is not None else None,
            context_source=str(args.context_source),
            context_venue=str(args.context_venue),
            context_symbol=str(args.context_symbol),
            price_venue=str(args.price_venue),
            price_symbol=str(args.price_symbol),
            timeframe=str(args.timeframe),
            funding_limit=int(args.funding_limit),
            ohlcv_limit=int(args.ohlcv_limit),
            horizon_bars=int(args.horizon_bars),
            min_joined_rows=int(args.min_joined_rows),
            fee_bps=float(args.fee_bps),
            slippage_bps=float(args.slippage_bps),
        )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_if_not_ok and not bool(result.get("ok")):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
