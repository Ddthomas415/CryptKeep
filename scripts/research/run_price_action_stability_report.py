#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.price_action_stability_report import run_price_action_stability_report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a research-only window-stability report from a saved "
            "price-action forward-return artifact. This does not select "
            "strategies or authorize confirmation filters."
        )
    )
    parser.add_argument("--forward-returns", type=Path, required=True, help="JSON artifact from run_price_action_forward_return_join.py.")
    parser.add_argument("--window-size-rows", type=int, default=100)
    parser.add_argument("--min-windows", type=int, default=3)
    parser.add_argument("--min-label-count", type=int, default=5)
    parser.add_argument("--consistency-threshold", type=float, default=0.6)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if the stability report is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_price_action_stability_report(
        forward_return_artifact_path=args.forward_returns,
        window_size_rows=int(args.window_size_rows),
        min_windows=int(args.min_windows),
        min_label_count=int(args.min_label_count),
        consistency_threshold=float(args.consistency_threshold),
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
