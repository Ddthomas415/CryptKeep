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

from services.analytics.paper_strategy_evidence_service import (
    PaperStrategyEvidenceServiceCfg,
    load_runtime_status,
    request_stop,
    run_campaign,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a managed paper strategy evidence collection campaign.")
    ap.add_argument(
        "--strategies",
        default="ema_cross,breakout_donchian,mean_reversion_rsi",
        help="Comma-separated canonical strategy IDs to run sequentially.",
    )
    ap.add_argument("--runtime-sec", type=float, default=900.0, help="Per-strategy runtime window in seconds")
    ap.add_argument("--strategy-drain-sec", type=float, default=2.0, help="Wait after each strategy stop for fills to settle")
    ap.add_argument("--symbol", default="BTC/USD", help="Runtime symbol for tick publisher, runner, and paper engine")
    ap.add_argument("--venue", default="coinbase", help="Runtime venue for tick publisher, runner, and paper engine")
    ap.add_argument("--tick-interval-sec", type=float, default=2.0, help="Tick publisher interval while the campaign is active")
    ap.add_argument("--evidence-symbol", default="", help="Optional symbol override for the synthetic evidence cycle")
    ap.add_argument("--paper-history-path", default="", help="Optional trade_journal.sqlite path override")
    ap.add_argument("--max-strategies", type=int, default=0, help="Optional cap for test/manual runs")
    ap.add_argument("--stop", action="store_true", help="Request stop for the active managed campaign")
    ap.add_argument("--status", action="store_true", help="Show managed campaign runtime status")
    args = ap.parse_args()

    if args.stop:
        print(json.dumps(request_stop(), indent=2, default=str))
        return 0
    if args.status:
        print(json.dumps(load_runtime_status(), indent=2, default=str))
        return 0

    cfg = PaperStrategyEvidenceServiceCfg(
        strategies=tuple(item.strip() for item in str(args.strategies or "").split(",") if item.strip()),
        per_strategy_runtime_sec=float(args.runtime_sec or 900.0),
        strategy_drain_sec=float(args.strategy_drain_sec or 2.0),
        symbol=str(args.symbol or "BTC/USD"),
        venue=str(args.venue or "coinbase"),
        tick_publish_interval_sec=float(args.tick_interval_sec or 2.0),
        evidence_symbol=str(args.evidence_symbol or ""),
        paper_history_path=str(args.paper_history_path or ""),
    )
    out = run_campaign(
        cfg,
        max_strategies=(int(args.max_strategies) if int(args.max_strategies or 0) > 0 else None),
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
