#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.ai_copilot.strategy_lab import build_strategy_lab_report, write_strategy_lab_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only strategy lab report from persisted evidence.")
    parser.add_argument("--strategy-id", default="", help="Optional explicit strategy to analyze; defaults to current top strategy.")
    parser.add_argument("--symbol", default="", help="Optional symbol filter for replay rows.")
    parser.add_argument("--replay-limit", type=int, default=3, help="Maximum losing replay rows to include.")
    parser.add_argument("--journal-path", default="", help="Optional trade journal path override.")
    parser.add_argument("--no-loss-replay", action="store_true", help="Skip losing-trade replay attachment.")
    parser.add_argument("--stem", default="", help="Optional report filename stem.")
    args = parser.parse_args()

    report = build_strategy_lab_report(
        strategy_id=str(args.strategy_id or ""),
        symbol=str(args.symbol or ""),
        replay_limit=int(args.replay_limit or 3),
        include_loss_replay=not bool(args.no_loss_replay),
        journal_path=str(args.journal_path or ""),
    )
    paths = write_strategy_lab_report(report, stem=str(args.stem or "").strip() or None)
    payload = dict(report)
    payload["report_paths"] = paths
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
