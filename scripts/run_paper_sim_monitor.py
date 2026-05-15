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

from services.analytics.paper_sim_monitor import (
    PaperSimMonitorCfg,
    collect_once,
    delete_watch,
    load_runtime_status,
    list_watches,
    register_watch,
    request_stop,
    run_forever,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Monitor paper simulation strategy, fills, PnL, and evidence progress.")
    ap.add_argument("--status", action="store_true", help="Show paper sim monitor runtime status")
    ap.add_argument("--stop", action="store_true", help="Request stop for the running paper sim monitor")
    ap.add_argument("--once", action="store_true", help="Collect one paper sim snapshot without starting the loop")
    ap.add_argument("--list-watches", action="store_true", help="List persisted paper sim watches")
    ap.add_argument("--register-watch", default="", help="Persist a named watch")
    ap.add_argument("--watch-trigger", default="", help="Watch trigger for --register-watch")
    ap.add_argument("--delete-watch", default="", help="Delete a named watch")
    ap.add_argument("--interval-sec", type=float, default=300.0, help="Polling interval for monitor loop")
    ap.add_argument(
        "--min-closed-trades",
        type=int,
        default=1,
        help="Closed trade threshold used to report enough_evidence",
    )
    ap.add_argument("--max-loops", type=int, default=0, help="Optional loop cap for tests/manual use")
    args = ap.parse_args()

    if args.stop:
        print(json.dumps(request_stop(), indent=2, default=str))
        return 0
    if args.delete_watch:
        print(json.dumps(delete_watch(name=str(args.delete_watch)), indent=2, default=str))
        return 0
    if args.register_watch:
        print(
            json.dumps(
                register_watch(name=str(args.register_watch), trigger=str(args.watch_trigger)),
                indent=2,
                default=str,
            )
        )
        return 0
    if args.list_watches:
        print(json.dumps({"ok": True, "watches": list_watches()}, indent=2, default=str))
        return 0
    if args.status:
        print(json.dumps(load_runtime_status(), indent=2, default=str))
        return 0

    cfg = PaperSimMonitorCfg(
        poll_interval_sec=float(args.interval_sec or 300.0),
        min_closed_trades_for_enough_evidence=int(args.min_closed_trades or 1),
    )
    if args.once:
        print(json.dumps(collect_once(cfg), indent=2, default=str))
        return 0

    out = run_forever(
        cfg,
        max_loops=(int(args.max_loops) if int(args.max_loops or 0) > 0 else None),
    )
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
