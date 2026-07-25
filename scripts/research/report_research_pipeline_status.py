#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH

try:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parents[1])

from services.analytics.research_pipeline_status import build_research_pipeline_status  # noqa: E402


def _print_report(payload: dict[str, Any]) -> None:
    print("=== Research Pipeline Status ===")
    print(f"ok={payload.get('ok')} pipelines={payload.get('pipeline_count')}")
    summary = dict(payload.get("summary") or {})
    print(
        "summary: "
        f"wired={summary.get('wired', 0)} "
        f"latest_ok={summary.get('latest_ok', 0)} "
        f"not_run={summary.get('not_run', 0)} "
        f"latest_not_ok={summary.get('latest_not_ok', 0)}"
    )
    for row in list(payload.get("pipelines") or []):
        if not isinstance(row, dict):
            continue
        print(
            "- "
            f"{row.get('pipeline_id')}: "
            f"wiring_ok={row.get('wiring_ok')} "
            f"latest_status={row.get('latest_status')} "
            f"make={row.get('make_target')} "
            f"latest={row.get('latest_summary_path') or '-'}"
        )
        reasons = [str(item) for item in list(row.get("reasons") or []) if str(item)]
        if reasons:
            print(f"  reasons={','.join(reasons)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only status report for accepted research pipeline wrappers"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)

    payload = build_research_pipeline_status(repo_root=ROOT)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(payload)
    return 0 if bool(payload.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
