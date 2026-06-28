#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import argparse
import json
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.runtime.startup_hardening_audit import (  # noqa: E402
    build_startup_hardening_audit,
    write_startup_hardening_audit,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only startup hardening audit report.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist report artifacts")
    return parser.parse_args(argv)


def _print_summary(report: dict) -> None:
    print("=== Startup Hardening Audit ===")
    print(f"gap_status={report.get('gap_status')}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"machine_summary={report.get('machine_summary')}")
    for item in list(report.get("action_items") or []):
        if not isinstance(item, dict):
            continue
        print(
            "action="
            f"{item.get('id')} severity={item.get('severity')} "
            f"summary={item.get('summary')}"
        )
    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest_json={paths.get('latest_json')}")
        print(f"artifact_latest_markdown={paths.get('latest_markdown')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_startup_hardening_audit()
    if not bool(args.no_write):
        report["artifact_paths"] = write_startup_hardening_audit(report)

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
