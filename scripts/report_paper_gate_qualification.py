#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH

try:
    from _bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.control.paper_gate_qualification_report import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    build_paper_gate_qualification_report,
)


def _row_reason(row: dict[str, Any]) -> str:
    reasons = [str(item) for item in list(row.get("rejection_reasons") or []) if str(item)]
    if reasons:
        return ",".join(reasons)
    if row.get("status") == "incomplete":
        return "qualified_fill_not_part_of_complete_round_trip"
    return "counts_toward_qualified_round_trip"


def print_report(payload: dict[str, Any]) -> None:
    summary = dict(payload.get("summary") or {})
    expected = dict(payload.get("expected_contract") or {})

    print("=== Paper Gate Qualification Report ===")
    print(f"Strategy: {payload.get('strategy_id')} target={payload.get('target_strategy')}")
    print(f"Evidence: {payload.get('evidence_dir')}")
    print(f"Journal: {payload.get('journal_path')}")
    print(
        "Expected provenance: "
        f"source={expected.get('market_data_source') or '-'} "
        f"timeframe={expected.get('ohlcv_timeframe') or '-'} "
        f"venue={expected.get('ohlcv_venue') or '-'} "
        f"symbol={expected.get('ohlcv_symbol') or '-'}"
    )
    print(
        "Round trips: "
        f"qualified={summary.get('qualified_round_trips', 0)} "
        f"all_history={summary.get('all_history_round_trips', 0)}"
    )
    print(
        "Evidence fills: "
        f"counted={summary.get('counted_evidence_fills', 0)} "
        f"incomplete={summary.get('incomplete_evidence_fills', 0)} "
        f"rejected={summary.get('rejected_evidence_fills', 0)} "
        f"total={summary.get('evidence_fills', 0)}"
    )
    reason_counts = dict(summary.get("unqualified_reason_counts") or {})
    if reason_counts:
        print(
            "Rejected reasons: "
            + ", ".join(
                f"{reason}={count}" for reason, count in sorted(reason_counts.items())
            )
        )
    print("")
    print("Fills:")
    for row in list(payload.get("fills") or []):
        print(
            f"- #{row.get('index')} {row.get('timestamp') or '-'} "
            f"{row.get('side') or '-'} order_id={row.get('order_id') or '-'} "
            f"status={row.get('status')} reason={_row_reason(dict(row))}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only fill-level diagnostic for paper gate provenance qualification"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--filter",
        choices=("all", "counted", "incomplete", "rejected"),
        default="all",
        help="Filter fill rows by qualification status",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit returned fill rows")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Strategy config path",
    )
    args = parser.parse_args(argv)

    payload = build_paper_gate_qualification_report(
        config_path=args.config,
        row_filter=str(args.filter or "all"),
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
