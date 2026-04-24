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

from services.execution.live_event_executor import request_stop, run_forever, status


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop", "status"], nargs="?", default="run")
    ap.add_argument("--config", default="config/trading.yaml")
    ap.add_argument("--poll-sec", type=float, default=0.2)
    ap.add_argument("--min-trigger-ms", type=int, default=200)
    args = ap.parse_args()

    if args.cmd == "stop":
        print(json.dumps(request_stop(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "status":
        print(json.dumps(status(), indent=2, sort_keys=True))
        return 0

    out = run_forever(
        cfg_path=str(args.config),
        poll_sec=float(args.poll_sec),
        min_trigger_interval_ms=int(args.min_trigger_ms),
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
