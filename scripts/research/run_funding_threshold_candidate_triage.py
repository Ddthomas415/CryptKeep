#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.funding_threshold_candidate_triage import (
    run_funding_threshold_candidate_triage,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only funding threshold candidate triage report over "
            "an existing funding-threshold sensitivity artifact. This ranks "
            "threshold pairs for manual review only; it does not change strategy "
            "config, campaigns, gates, promotion evidence, or execution."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="funding_threshold_sensitivity_v1 JSON artifact.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--min-input-rows", type=int, default=100)
    parser.add_argument("--min-actionable-rows", type=int, default=5)
    parser.add_argument("--min-actionable-share", type=float, default=0.01)
    parser.add_argument("--min-positive-ratio", type=float, default=0.50)
    parser.add_argument("--min-avg-net-forward-return-pct", type=float, default=0.0)
    parser.add_argument("--fail-if-not-ok", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_funding_threshold_candidate_triage(
        input_path=args.input,
        min_input_rows=int(args.min_input_rows),
        min_actionable_rows=int(args.min_actionable_rows),
        min_actionable_share=float(args.min_actionable_share),
        min_positive_ratio=float(args.min_positive_ratio),
        min_avg_net_forward_return_pct=float(args.min_avg_net_forward_return_pct),
    )
    result["script"] = "scripts/research/run_funding_threshold_candidate_triage.py"
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
