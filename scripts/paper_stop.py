#!/usr/bin/env python3
"""Graceful paper campaign shutdown."""
from __future__ import annotations
import argparse
import pathlib
import subprocess
import sys
import time

FLAGS_DIR = pathlib.Path(".cbp_state/runtime/flags")

STOP_FLAGS = [
    "paper_strategy_evidence.stop",
    "strategy_runner.stop",
    "paper_engine.stop",
    "tick_publisher.stop",
]
PROC_PATTERNS = [
    "run_es_daily_trend_paper",
    "run_strategy_runner",
    "run_paper_engine",
    "run_tick_publisher",
]

def alive() -> list[str]:
    return [p for p in PROC_PATTERNS
            if subprocess.run(["pgrep", "-f", f"{p}.py"], capture_output=True).returncode == 0]

def write_flags() -> None:
    FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    for flag in STOP_FLAGS:
        (FLAGS_DIR / flag).write_text("stop\n", encoding="utf-8")

def kill(patterns: list[str]) -> None:
    for pat in patterns:
        subprocess.run(["pkill", "-f", f"{pat}.py"], capture_output=True)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force-now", action="store_true")
    args = ap.parse_args()

    write_flags()

    if args.force_now:
        print("Stop flags written. Force stopping immediately...")
        kill(PROC_PATTERNS)
        time.sleep(1)
        remaining = alive()
        if not remaining:
            print("Teardown: clean — all child processes stopped")
            return 0
        print(f"Teardown: timeout — still running: {remaining}")
        print("Run: make paper-clean-locks")
        return 1

    print("Stop flags written. Waiting for graceful shutdown...")
    for _ in range(5):
        time.sleep(1)
        if not alive():
            print("Teardown: clean — all child processes stopped")
            return 0

    still_alive = alive()
    print(f"Graceful stop timed out — force stopping: {still_alive}")
    kill(still_alive)

    for _ in range(10):
        time.sleep(1)
        if not alive():
            print("Teardown: clean — all child processes stopped after force stop")
            return 0

    remaining = alive()
    print(f"Teardown: timeout — still running: {remaining}")
    print("Run: make paper-clean-locks")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
