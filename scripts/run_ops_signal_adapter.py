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

from services.ops.signal_adapter_service import (
    SignalAdapterServiceCfg,
    publish_once,
    request_stop,
    run_forever,
)
from services.ops.telemetry_snapshot_builder import TelemetrySnapshotCfg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "stop", "once"], nargs="?", default="run")
    ap.add_argument("--db", default="", help="override ops sqlite path")
    ap.add_argument("--poll-sec", type=float, default=1.0)
    ap.add_argument("--max-loops", type=int, default=None)
    ap.add_argument("--symbol", default="BTC/USD")
    args = ap.parse_args()

    if args.cmd == "stop":
        print(json.dumps(request_stop(), sort_keys=True))
        return 0

    telemetry = TelemetrySnapshotCfg(
        ops_db_path=str(args.db or ""),
        symbol=str(args.symbol or "BTC/USD"),
    )
    cfg = SignalAdapterServiceCfg(
        poll_interval_sec=float(args.poll_sec),
        telemetry=telemetry,
    )

    if args.cmd == "once":
        out = publish_once(cfg)
        print(json.dumps(out, sort_keys=True))
        return 0 if out.get("ok") else 2

    out = run_forever(cfg, max_loops=args.max_loops)
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

