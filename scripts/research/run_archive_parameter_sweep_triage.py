#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.archive_parameter_sweep_triage import (
    run_archive_parameter_sweep_triage,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only triage report over an existing "
            "archive_backed_parameter_sweep_v1 artifact. This ranks sweep "
            "variants for manual review only; it does not rerun backtests, "
            "change strategy config, start campaigns, or produce promotion "
            "evidence."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="archive_backed_parameter_sweep_v1 JSON artifact.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--min-successful-variants", type=int, default=1)
    parser.add_argument("--min-window-count", type=int, default=2)
    parser.add_argument("--min-closed-trades", type=int, default=1)
    parser.add_argument("--min-non-negative-window-ratio", type=float, default=0.50)
    parser.add_argument("--min-avg-test-return-pct", type=float, default=0.0)
    parser.add_argument("--max-avg-test-drawdown-pct", type=float, default=100.0)
    parser.add_argument("--fail-if-not-ok", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_archive_parameter_sweep_triage(
        input_path=args.input,
        min_successful_variants=int(args.min_successful_variants),
        min_window_count=int(args.min_window_count),
        min_closed_trades=int(args.min_closed_trades),
        min_non_negative_window_ratio=float(args.min_non_negative_window_ratio),
        min_avg_test_return_pct=float(args.min_avg_test_return_pct),
        max_avg_test_drawdown_pct=float(args.max_avg_test_drawdown_pct),
    )
    result["script"] = "scripts/research/run_archive_parameter_sweep_triage.py"
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
