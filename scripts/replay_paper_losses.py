#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.analytics.paper_loss_replay import build_loss_replay


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay losing closed trades from persisted paper journal fills.")
    ap.add_argument("--strategy-id", required=True, help="Canonical strategy_id to inspect, e.g. mean_reversion_rsi")
    ap.add_argument("--symbol", default="", help="Optional symbol filter, e.g. ETH/USD")
    ap.add_argument("--journal-path", default="", help="Optional trade_journal.sqlite path override")
    ap.add_argument("--limit", type=int, default=10, help="Maximum number of losing replays to emit")
    args = ap.parse_args()

    out = build_loss_replay(
        strategy_id=str(args.strategy_id or "").strip(),
        symbol=str(args.symbol or "").strip(),
        journal_path=str(args.journal_path or ""),
        limit=int(args.limit or 10),
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
