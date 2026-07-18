#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json

from services.analytics.paper_campaign_recovery import (
    DEFAULT_CONFIG_PATH,
    load_campaign_specs,
    manage_campaigns,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check or idempotently restore configured paper evidence campaigns."
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="Check configured campaign processes without starting them")
    mode.add_argument("--restore", action="store_true", help="Start only configured campaigns whose collectors are not alive")
    ap.add_argument(
        "--campaign",
        action="append",
        default=[],
        help="Limit the operation to a configured campaign name; may be repeated",
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Paper campaign manifest path")
    ap.add_argument(
        "--preflight-ohlcv",
        action="store_true",
        help="Before --restore starts a dead collector, verify its configured public-OHLCV source is reachable",
    )
    ap.add_argument(
        "--restart-unhealthy",
        action="store_true",
        help="With --restore --preflight-ohlcv, stop and replace alive unhealthy collectors after preflight passes",
    )
    ap.add_argument(
        "--restart-wait-sec",
        type=float,
        default=5.0,
        help="Seconds to wait after requesting an unhealthy collector stop before sending SIGTERM",
    )
    ap.add_argument(
        "--ohlcv-preflight-probe-limit",
        type=int,
        default=400,
        help="Rows to request for --preflight-ohlcv checks; default matches strategy_runner max_bars fallback",
    )
    ap.add_argument(
        "--ohlcv-preflight-attempts",
        type=int,
        default=1,
        help="Attempts for --preflight-ohlcv reachability checks",
    )
    ap.add_argument(
        "--ohlcv-preflight-attempt-delay-sec",
        type=float,
        default=0.0,
        help="Delay between --preflight-ohlcv attempts",
    )
    args = ap.parse_args(argv)
    if args.restart_unhealthy and (not args.restore or not args.preflight_ohlcv):
        ap.error("--restart-unhealthy requires --restore --preflight-ohlcv")

    try:
        specs = load_campaign_specs(args.config, repo_root=ROOT)
        payload = manage_campaigns(
            specs,
            restore=bool(args.restore),
            selected_names=args.campaign,
            restart_unhealthy=bool(args.restart_unhealthy),
            restart_wait_sec=float(args.restart_wait_sec),
            preflight_ohlcv=bool(args.restore and args.preflight_ohlcv),
            preflight_probe_limit=args.ohlcv_preflight_probe_limit,
            preflight_attempts=args.ohlcv_preflight_attempts,
            preflight_attempt_delay_sec=args.ohlcv_preflight_attempt_delay_sec,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "ok": False,
            "action": "restore" if args.restore else "status",
            "reason": f"invalid_campaign_config:{type(exc).__name__}",
        }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
