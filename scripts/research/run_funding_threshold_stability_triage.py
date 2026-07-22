#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.funding_threshold_stability_triage import (
    run_funding_threshold_stability_triage,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only funding threshold stability-triage report over "
            "an existing funding_threshold_window_stability_v1 artifact. This "
            "ranks threshold pairs for manual review only and does not change "
            "strategy config, campaigns, gates, promotion evidence, or execution."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="funding_threshold_window_stability_v1 JSON artifact.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--min-window-count", type=int, default=2)
    parser.add_argument("--min-actionable-window-ratio", type=float, default=0.50)
    parser.add_argument("--min-positive-actionable-window-ratio", type=float, default=0.50)
    parser.add_argument("--min-avg-net-forward-return-pct", type=float, default=0.0)
    parser.add_argument("--min-worst-window-avg-net-forward-return-pct", type=float, default=0.0)
    parser.add_argument("--fail-if-not-ok", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_funding_threshold_stability_triage(
        input_path=args.input,
        min_window_count=int(args.min_window_count),
        min_actionable_window_ratio=float(args.min_actionable_window_ratio),
        min_positive_actionable_window_ratio=float(args.min_positive_actionable_window_ratio),
        min_avg_net_forward_return_pct=float(args.min_avg_net_forward_return_pct),
        min_worst_window_avg_net_forward_return_pct=float(args.min_worst_window_avg_net_forward_return_pct),
    )
    result["script"] = "scripts/research/run_funding_threshold_stability_triage.py"
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
