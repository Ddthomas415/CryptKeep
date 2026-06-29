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

from services.analytics.pullback_stage0_readiness import (  # noqa: E402
    DEFAULT_HETZNER_MANIFEST,
    DEFAULT_LAPTOP_MANIFEST,
    build_pullback_stage0_readiness,
    write_pullback_stage0_readiness,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a read-only readiness report for the pullback Stage 0 proof.",
    )
    parser.add_argument("--laptop-config", type=Path, default=DEFAULT_LAPTOP_MANIFEST)
    parser.add_argument("--hetzner-config", type=Path, default=DEFAULT_HETZNER_MANIFEST)
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist report artifacts")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    print("=== Pullback Stage 0 Readiness ===")
    print(f"status={report.get('status')}")
    print(f"ready={bool(report.get('ready'))}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"strategy={report.get('strategy')}")
    print(f"session_strategy_id={report.get('session_strategy_id')}")
    print(f"state_dir={report.get('state_dir')}")
    blocking = report.get("blocking_checks")
    print(f"blocking_checks={len(blocking) if isinstance(blocking, list) else 0}")
    proof = report.get("proof_command")
    if isinstance(proof, dict):
        print(f"stage0_command={proof.get('shell')}")
    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest_json={paths.get('latest_json')}")
        print(f"artifact_latest_markdown={paths.get('latest_markdown')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_pullback_stage0_readiness(
        repo_root=ROOT,
        laptop_manifest=args.laptop_config,
        hetzner_manifest=args.hetzner_config,
    )
    if not bool(args.no_write):
        report["artifact_paths"] = write_pullback_stage0_readiness(report)

    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 0 if bool(report.get("ready")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
