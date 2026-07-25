#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.analytics.price_action_forward_return_join import run_price_action_forward_return_join


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Join a research-only price-action label artifact to modeled "
            "forward returns after fee/slippage assumptions. This does not "
            "select strategies, change configs, or create promotion evidence."
        )
    )
    parser.add_argument("--labels", type=Path, required=True, help="JSON artifact from run_price_action_context_labels.py.")
    parser.add_argument("--horizon-bars", type=int, default=1)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--min-label-count", type=int, default=5)
    parser.add_argument("--min-forward-rows", type=int, default=1)
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON artifact path.")
    parser.add_argument("--fail-if-not-ok", action="store_true", help="Exit 2 if the join is not ok.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_price_action_forward_return_join(
        label_artifact_path=args.labels,
        horizon_bars=int(args.horizon_bars),
        fee_bps=float(args.fee_bps),
        slippage_bps=float(args.slippage_bps),
        min_label_count=int(args.min_label_count),
        min_forward_rows=int(args.min_forward_rows),
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
