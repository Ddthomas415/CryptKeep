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

from services.analytics.crypto_edge_collector_service import (
    CryptoEdgeCollectorServiceCfg,
    load_runtime_status,
    request_stop,
    run_forever,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the read-only live crypto structural edge collector loop.")
    ap.add_argument("--plan-file", default="sample_data/crypto_edges/live_collector_plan.json", help="JSON collection plan")
    ap.add_argument("--db-path", default="", help="Optional sqlite path override")
    ap.add_argument("--source", default="live_public", help="Snapshot source label")
    ap.add_argument("--interval-sec", type=float, default=300.0, help="Polling interval between collections")
    ap.add_argument("--max-loops", type=int, default=0, help="Optional loop limit for test/manual use")
    ap.add_argument("--stop", action="store_true", help="Request stop for the running collector loop")
    ap.add_argument("--status", action="store_true", help="Show managed collector runtime status")
    args = ap.parse_args()

    if args.stop:
        print(json.dumps(request_stop(), indent=2, default=str))
        return 0
    if args.status:
        print(json.dumps(load_runtime_status(), indent=2, default=str))
        return 0

    cfg = CryptoEdgeCollectorServiceCfg(
        plan_file=str(args.plan_file),
        poll_interval_sec=float(args.interval_sec or 300.0),
        db_path=str(args.db_path or ""),
        source=str(args.source or "live_public"),
    )
    out = run_forever(cfg, max_loops=(int(args.max_loops) if int(args.max_loops or 0) > 0 else None))
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
