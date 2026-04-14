#!/usr/bin/env python3
"""scripts/run_strategy_runner.py — Strategy runner entrypoint.

Wraps run_forever() with a control kernel pre-check.
If the deployment stage is safe_degraded, the runner does not start.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import json
import os

from services.strategy_runner.ema_crossover_runner import run_forever, request_stop
from services.logging.app_logger import get_logger

_LOG = get_logger("run_strategy_runner")


def _kernel_pre_check(strategy_id: str) -> tuple[bool, str]:
    """Return (allowed, reason) based on deployment stage."""
    try:
        from services.control.deployment_stage import get_current_stage, Stage
        stage = get_current_stage(strategy_id)
        if stage == Stage.SAFE_DEGRADED:
            return False, f"stage:safe_degraded — strategy {strategy_id} is in safe_degraded mode; promote before running"
        return True, f"stage:{stage.value}"
    except Exception as e:
        # If control kernel is unavailable, allow (fail-open for runner start;
        # execution safety is enforced by place_order, not here).
        _LOG.warning("kernel pre-check unavailable: %s — allowing runner start", e)
        return True, "kernel_unavailable:fail_open"


def main() -> int:
    ap = argparse.ArgumentParser(description="Strategy runner with kernel pre-check")
    ap.add_argument("cmd", choices=["run", "stop"], nargs="?", default="run")
    ap.add_argument("--strategy-id", type=str,
                    default=os.environ.get("CBP_STRATEGY_ID", ""),
                    help="Strategy ID for deployment stage check")
    ap.add_argument("--skip-kernel-check", action="store_true",
                    help="Bypass deployment stage gate (for paper/testing only)")
    args = ap.parse_args()

    if args.cmd == "stop":
        print(json.dumps(request_stop()))
        return 0

    # Kernel pre-check before starting the loop
    if not args.skip_kernel_check and args.strategy_id:
        allowed, reason = _kernel_pre_check(args.strategy_id)
        if not allowed:
            _LOG.error("runner blocked by kernel: %s", reason)
            print(f"BLOCKED: {reason}", file=sys.stderr)
            return 1
        _LOG.info("kernel pre-check passed: %s", reason)

    run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
