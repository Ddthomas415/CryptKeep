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

from services.analytics.signal_quality import (
    DEFAULT_HORIZON_BARS,
    DEFAULT_LATE_THRESHOLD_SHARE,
    DEFAULT_LOOKBACK_BARS,
    DEFAULT_TARGET_MOVE_PCT,
    build_signal_quality_report,
    write_signal_quality_artifacts,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy-id", default="es_daily_trend_v1")
    ap.add_argument("--symbol", default=None)
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--timeframe", default="1d")
    ap.add_argument("--ohlcv-path", default=None)
    ap.add_argument("--evidence-dir", default=None)
    ap.add_argument("--target-move-pct", type=float, default=DEFAULT_TARGET_MOVE_PCT)
    ap.add_argument("--horizon-bars", type=int, default=DEFAULT_HORIZON_BARS)
    ap.add_argument("--late-threshold-share", type=float, default=DEFAULT_LATE_THRESHOLD_SHARE)
    ap.add_argument("--lookback-bars", type=int, default=DEFAULT_LOOKBACK_BARS)
    ap.add_argument(
        "--allow-unqualified-evidence",
        action="store_true",
        help="Research-only: include non-sample signals without matching public-OHLCV provenance.",
    )
    ap.add_argument("--no-persist", action="store_true")
    args = ap.parse_args()

    report = build_signal_quality_report(
        strategy_id=args.strategy_id,
        symbol=(args.symbol.strip() or None) if isinstance(args.symbol, str) else None,
        venue=args.venue,
        timeframe=args.timeframe,
        ohlcv_path=args.ohlcv_path,
        evidence_dir=args.evidence_dir,
        target_move_pct=float(args.target_move_pct),
        horizon_bars=int(args.horizon_bars),
        late_threshold_share=float(args.late_threshold_share),
        lookback_bars=int(args.lookback_bars),
        require_matching_provenance=not bool(args.allow_unqualified_evidence),
    )
    if not args.no_persist:
        report["artifacts"] = write_signal_quality_artifacts(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
