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

from services.ops.risk_gate_service import (
    RiskGateServiceCfg,
    process_latest_raw_signal,
    request_stop,
    run_forever,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop", "once"], nargs="?", default="run")
    ap.add_argument("--db", default="", help="override ops sqlite path")
    ap.add_argument("--poll-sec", type=float, default=1.0)
    ap.add_argument("--max-loops", type=int, default=None)
    ap.add_argument("--write-if-unchanged", action="store_true")
    args = ap.parse_args()

    if args.cmd == "stop":
        print(json.dumps(request_stop(), sort_keys=True))
        return 0

    if args.cmd == "once":
        from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite

        out = process_latest_raw_signal(
            store=OpsSignalStoreSQLite(path=str(args.db or "")),
            write_if_unchanged=bool(args.write_if_unchanged),
        )
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") else 2

    out = run_forever(
        RiskGateServiceCfg(
            store_path=str(args.db or ""),
            poll_interval_sec=float(args.poll_sec),
            write_if_unchanged=bool(args.write_if_unchanged),
        ),
        max_loops=args.max_loops,
    )
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
