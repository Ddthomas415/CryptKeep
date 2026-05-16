#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.ai_copilot.sim_runner import run_simulation_job, write_simulation_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an approved read-only paper/replay simulation job.")
    parser.add_argument("job", choices=["paper_diagnostics", "paper_loss_replay"])
    parser.add_argument("--strategy-id", default="", help="Required for paper_loss_replay.")
    parser.add_argument("--symbol", default="", help="Optional symbol filter, e.g. ETH/USD")
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows or replay records to emit")
    parser.add_argument("--timeframe", default="", help="Optional OHLCV timeframe for paper_loss_replay")
    parser.add_argument("--context-bars", type=int, default=3, help="Bars before/after entry/exit for paper_loss_replay")
    parser.add_argument("--journal-path", default="", help="Optional trade journal path override for paper_loss_replay")
    parser.add_argument("--timeout-sec", type=int, default=30, help="Subprocess timeout")
    parser.add_argument("--stem", default="", help="Optional report filename stem")
    args = parser.parse_args()

    report = run_simulation_job(
        args.job,
        strategy_id=str(args.strategy_id or ""),
        symbol=str(args.symbol or ""),
        limit=int(args.limit or 10),
        timeframe=str(args.timeframe or ""),
        context_bars=int(args.context_bars or 3),
        journal_path=str(args.journal_path or ""),
        timeout_sec=int(args.timeout_sec or 30),
    )
    paths = write_simulation_report(report, stem=str(args.stem or "").strip() or None)
    payload = dict(report)
    payload["report_paths"] = paths
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
