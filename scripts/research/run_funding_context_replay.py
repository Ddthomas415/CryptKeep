#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.research.run_archive_walk_forward import load_strategy_config
from services.analytics.funding_context_replay import run_funding_context_replay


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only funding_extreme signal replay over stored "
            "crypto-edge funding snapshots. This emits signal distribution only, "
            "not PnL, expectancy, or promotion evidence."
        )
    )
    parser.add_argument("--config", type=Path, default=None, help="Optional JSON/YAML strategy config.")
    parser.add_argument("--edge-db", type=Path, default=None, help="Optional crypto-edge sqlite path.")
    parser.add_argument("--source", default="live_public")
    parser.add_argument("--venue", default="okx")
    parser.add_argument("--symbol", default="BTC/USDT:USDT")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 when insufficient funding rows are available.")
    return parser.parse_args(argv)


def _load_cfg(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"strategy": {"name": "funding_extreme"}}
    return load_strategy_config(path)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_funding_context_replay(
        cfg=_load_cfg(args.config),
        db_path=str(args.edge_db) if args.edge_db is not None else None,
        source=str(args.source),
        venue=str(args.venue),
        symbol=str(args.symbol),
        limit=int(args.limit),
        min_rows=int(args.min_rows),
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
