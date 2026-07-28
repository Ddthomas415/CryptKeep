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

from services.analytics.operator_status_bundle import build_operator_status_bundle  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    summary = dict(payload.get("summary") or {})
    print("=== Operator Status Bundle ===")
    print(f"ok={bool(payload.get('ok'))}")
    print(
        "backlog: "
        f"passive={summary.get('passive_operator_items', 0)} "
        f"low={summary.get('low_risk_docs_tests', 0)} "
        f"medium={summary.get('medium_risk_runtime_read_only', 0)} "
        f"high={summary.get('high_risk_gate_execution_deploy', 0)}"
    )
    print(
        "research: "
        f"wired={summary.get('research_pipelines_wired', 0)} "
        f"latest_ok={summary.get('research_pipelines_latest_ok', 0)} "
        f"not_run={summary.get('research_pipelines_not_run', 0)}"
    )
    print(
        "proofs: "
        f"remaining={summary.get('remaining_proof_or_coverage_markers', 0)} "
        f"host_side={summary.get('host_side_markers', 0)} "
        f"proof_ready={summary.get('proof_ready_markers', 0)}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only bundle of operator backlog, research, and proof status reports."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args(argv)

    payload = build_operator_status_bundle(repo_root=ROOT)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
