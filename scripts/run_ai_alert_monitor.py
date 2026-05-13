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

from services.ai_copilot.alert_monitor_status import (
    list_recent_incidents,
    load_runtime_status,
    request_stop,
)


def _unsupported(action: str) -> dict[str, object]:
    return {
        "ok": False,
        "status": "unsupported",
        "reason": "monitor_control_loop_unavailable_on_branch",
        "action": action,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect AI alert monitor runtime status and persisted incidents.")
    ap.add_argument("--status", action="store_true", help="Show managed AI alert monitor runtime status")
    ap.add_argument("--stop", action="store_true", help="Request stop for the running monitor loop")
    ap.add_argument("--recent", action="store_true", help="List recent persisted AI incident reports")
    ap.add_argument("--limit", type=int, default=5, help="Limit for --recent output")
    ap.add_argument("--once", action="store_true", help="Unsupported on this branch; status only")
    ap.add_argument("--interval-sec", type=float, default=30.0, help="Unsupported on this branch; status only")
    ap.add_argument("--max-loops", type=int, default=0, help="Unsupported on this branch; status only")
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

    print(json.dumps(_unsupported("run"), indent=2, default=str))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
