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


def main() -> int:
    from services.ai_copilot.alert_monitor import (
        list_recent_incidents,
        load_runtime_status,
        process_once,
        request_stop,
        run_forever,
    )

    ap = argparse.ArgumentParser(description="Run the AI alert monitor and incident-report loop.")
    ap.add_argument("--status", action="store_true", help="Show managed AI alert monitor runtime status")
    ap.add_argument("--stop", action="store_true", help="Request stop for the running monitor loop")
    ap.add_argument("--recent", action="store_true", help="List recent persisted AI incident reports")
    ap.add_argument("--limit", type=int, default=5, help="Limit for --recent output")
    ap.add_argument("--once", action="store_true", help="Process one monitor pass and exit")
    ap.add_argument("--interval-sec", type=float, default=30.0, help="Polling interval between monitor passes")
    ap.add_argument("--max-loops", type=int, default=0, help="Optional loop limit for test/manual use")
    args = ap.parse_args()

    if args.stop:
        print(json.dumps(request_stop(), indent=2, default=str))
        return 0
    if args.status:
        print(json.dumps(load_runtime_status(), indent=2, default=str))
        return 0
    if args.recent:
        print(json.dumps(list_recent_incidents(limit=max(1, int(args.limit or 5))), indent=2, default=str))
        return 0
    if args.once:
        print(json.dumps(process_once(), indent=2, default=str))
        return 0

    out = run_forever(
        poll_interval_sec=float(args.interval_sec or 30.0),
        max_loops=(int(args.max_loops) if int(args.max_loops or 0) > 0 else None),
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
