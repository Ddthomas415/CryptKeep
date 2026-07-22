#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.funding_threshold_window_stability import (
    run_funding_threshold_window_stability,
)


def _csv_floats(value: str) -> list[float]:
    out: list[float] = []
    for part in str(value or "").split(","):
        item = part.strip()
        if item:
            out.append(float(item))
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a research-only funding-threshold window-stability report over "
            "an existing funding context price-join artifact. This does not "
            "fetch data, change strategy config, start campaigns, or produce "
            "promotion evidence."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="funding_context_price_join_v1 JSON artifact.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--long-thresholds-pct", default="0.005,0.01,0.02,0.05")
    parser.add_argument("--short-thresholds-pct", default="-0.005,-0.01,-0.02,-0.05")
    parser.add_argument("--window-rows", type=int, default=100)
    parser.add_argument("--step-rows", type=int, default=None)
    parser.add_argument("--min-windows", type=int, default=2)
    parser.add_argument("--fail-if-not-ok", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_funding_threshold_window_stability(
        input_path=args.input,
        long_thresholds_pct=_csv_floats(args.long_thresholds_pct),
        short_thresholds_pct=_csv_floats(args.short_thresholds_pct),
        window_rows=int(args.window_rows),
        step_rows=int(args.step_rows) if args.step_rows is not None else None,
        min_windows=int(args.min_windows),
    )
    result["script"] = "scripts/research/run_funding_threshold_window_stability.py"
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
