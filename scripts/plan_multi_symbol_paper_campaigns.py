#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.analytics.multi_symbol_paper_campaign_generator import (  # noqa: E402
    build_multi_symbol_paper_campaign_plan,
    write_multi_symbol_paper_campaign_plan,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a symbol universe, rank strategy/symbol candidates, OHLCV-preflight them, "
            "and write paper-only proposed campaign rows. This never starts campaigns or "
            "mutates active manifests."
        )
    )
    parser.add_argument("--host", choices=["laptop", "hetzner", "neither"], default="laptop")
    parser.add_argument("--venue", default="coinbase")
    parser.add_argument("--symbols", nargs="+", default=None, help="Explicit symbols to scan")
    parser.add_argument("--tiers", nargs="+", default=None, help="Universe tiers to scan when --symbols is omitted")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--ohlcv-limit", type=int, default=200)
    parser.add_argument("--min-score", type=float, default=38.0)
    parser.add_argument("--max-candidates", type=int, default=5)
    parser.add_argument("--preflight-probe-limit", type=int, default=50)
    parser.add_argument("--preflight-attempts", type=int, default=1)
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--no-write", action="store_true", help="Do not persist proposal artifacts")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, object]) -> None:
    summary = dict(report.get("summary") or {})
    preflight = dict(report.get("preflight_summary") or {})
    print("=== Multi-Symbol Paper Campaign Plan ===")
    print(f"status={report.get('status')}")
    print(f"read_only={bool(report.get('read_only'))}")
    print(f"symbols_requested={summary.get('symbols_requested')}")
    print(f"symbols_fetched={summary.get('symbols_fetched')}")
    print(f"ranked_candidate_count={summary.get('ranked_candidate_count')}")
    print(f"preflight_passed={preflight.get('passed')}")
    print(f"preflight_failed={preflight.get('failed')}")
    print(f"proposal_count={summary.get('proposal_count')}")
    print(f"rejected_count={summary.get('rejected_count')}")
    paths = report.get("artifact_paths")
    if isinstance(paths, dict) and paths:
        print(f"artifact_latest_json={paths.get('latest_json')}")
        print(f"artifact_latest_markdown={paths.get('latest_markdown')}")


def _exit_code(report: dict[str, object]) -> int:
    status = str(report.get("status") or "")
    if status in {"invalid_manifest", "scan_failed"}:
        return 2
    preflight = dict(report.get("preflight_summary") or {})
    checked = int(preflight.get("checked") or 0)
    passed = int(preflight.get("passed") or 0)
    failed = int(preflight.get("failed") or 0)
    if checked > 0 and failed > 0 and passed == 0:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_multi_symbol_paper_campaign_plan(
        repo_root=ROOT,
        symbols=list(args.symbols or []),
        tiers=list(args.tiers or []) or None,
        venue=str(args.venue),
        timeframe=str(args.timeframe),
        ohlcv_limit=int(args.ohlcv_limit),
        min_score=float(args.min_score),
        max_candidates=int(args.max_candidates),
        proposal_host=str(args.host),
        preflight_probe_limit=int(args.preflight_probe_limit),
        preflight_attempts=int(args.preflight_attempts),
    )
    if not bool(args.no_write):
        report["artifact_paths"] = write_multi_symbol_paper_campaign_plan(report)
    if bool(args.json):
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return _exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
