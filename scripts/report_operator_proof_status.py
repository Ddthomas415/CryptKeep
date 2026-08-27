#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scripts._bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[1])

from services.analytics.operator_proof_status import build_operator_proof_status  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Operator Proof Status ===")
    print(
        f"ok={bool(payload.get('ok'))} "
        f"passive_items={payload.get('passive_operator_item_count')} "
        f"proof_markers={payload.get('proof_marker_count')}"
    )
    if payload.get("proof_marker_scope") == "suppressed_by_passive_ordinal":
        print(f"proof_marker_scope=suppressed_by_passive_ordinal source={payload.get('source_proof_marker_count')}")
    if payload.get("category_filter"):
        print(f"category_filter={payload.get('category_filter')}")
    if payload.get("line_filter"):
        print(f"line_filter={payload.get('line_filter')}")
    if payload.get("passive_operator_ordinal_filter"):
        print(f"passive_operator_ordinal_filter={payload.get('passive_operator_ordinal_filter')}")
    if payload.get("passive_operator_scope") and payload.get("passive_operator_scope") != "all":
        print(f"passive_operator_scope={payload.get('passive_operator_scope')}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    if payload.get("reason") == "invalid_category":
        print("available_categories=" + ",".join(str(item) for item in list(payload.get("available_categories") or [])))
    summary = dict(payload.get("summary") or {})
    print(
        "summary: "
        f"remaining={summary.get('remaining_proof_or_coverage_markers', 0)} "
        f"host_side={summary.get('host_side_markers', 0)} "
        f"proof_ready={summary.get('proof_ready_markers', 0)} "
        f"satisfied={summary.get('proof_markers_satisfied', 0)} "
        f"context_only={summary.get('proof_markers_context_only', 0)} "
        f"actions_required={summary.get('proof_marker_actions_required', payload.get('proof_marker_count', 0))}"
    )
    print("passive_operator_evidence:")
    for row in list(payload.get("passive_operator_items") or []):
        if not isinstance(row, dict):
            continue
        print(f"- {row.get('ordinal')}. {row.get('text')}")
        if row.get("next_action") and row.get("next_action") != "none":
            print(f"  next_action={row.get('next_action')}")

    markers = [row for row in list(payload.get("proof_markers") or []) if isinstance(row, dict)]
    if markers:
        print("proof_marker_lines:")
        for row in markers[:20]:
            print(f"- L{row.get('line')} {row.get('category')}: {row.get('text')}")
            if row.get("next_action") and row.get("next_action") != "none":
                print(f"  next_action={row.get('next_action')}")
        if len(markers) > 20:
            print(f"... {len(markers) - 20} more markers; use --json for all")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only report of operator-side proof/evidence items from backlog docs."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument("--category", default=None, help="Limit proof markers to one category")
    parser.add_argument("--line", default=None, help="Limit proof markers to one REMAINING_TASKS.md line")
    parser.add_argument(
        "--passive-ordinal",
        default=None,
        help="Limit passive operator-evidence items to one 1-based ordinal",
    )
    args = parser.parse_args(argv)

    payload = build_operator_proof_status(
        repo_root=ROOT,
        category=args.category,
        line=args.line,
        passive_ordinal=args.passive_ordinal,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
