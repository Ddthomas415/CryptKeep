#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)



import argparse
import json
from services.supervisor.supervisor import start, stop, status

def main():
    ap = argparse.ArgumentParser(description="CryptoBotPro Supervisor (start/stop/status).")
    ap.add_argument("cmd", choices=["start","stop","status"], nargs="?", default="status")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--no-tick", action="store_true")
    ap.add_argument("--no-webhook", action="store_true")
    ap.add_argument("--no-signal-adapter", action="store_true")
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--timeout-sec", type=int, default=6)
    args = ap.parse_args()
    if args.cmd == "status":
        result = status()
        if not result.get("runtime_truth"):
            try:
                from run_bot_runner import status as runner_status
                result["runtime_truth"] = runner_status().get("runtime_truth", {})
            except Exception:
                result["runtime_truth"] = {}
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "start":
        out = start(
            with_dashboard=not args.no_dashboard,
            start_tick=not args.no_tick,
            start_webhook=not args.no_webhook,
            start_signal_adapter=not args.no_signal_adapter,
            start_risk_gate=True,
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 2
    out = stop(
        stop_dashboard=not args.no_dashboard,
        stop_tick=not args.no_tick,
        stop_webhook=not args.no_webhook,
        stop_signal_adapter=not args.no_signal_adapter,
        stop_risk_gate=True,
        timeout_sec=int(args.timeout_sec),
    )
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
