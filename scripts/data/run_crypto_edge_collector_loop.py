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
import hashlib
import json
import math

from services.analytics.okx_funding_pair_batch import validate_okx_pair_plan
from services.analytics.okx_funding_contract import _finite_json_float, _object, _reject_nonfinite

from services.analytics.crypto_edge_collector_service import (
    CryptoEdgeCollectorServiceCfg,
    load_runtime_status,
    request_stop,
    run_forever,
)


def _read_object(path):
    body = Path(path).read_bytes()
    value = json.loads(body, object_pairs_hook=_object, parse_constant=_reject_nonfinite,
                       parse_float=_finite_json_float)
    if type(value) is not dict:
        raise ValueError("configuration_object_required")
    return value, hashlib.sha256(body).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the read-only live crypto structural edge collector loop.")
    ap.add_argument("--plan-file", default="sample_data/crypto_edges/live_collector_plan.json", help="JSON collection plan")
    ap.add_argument("--db-path", default="", help="Optional sqlite path override")
    ap.add_argument("--source", default="live_public", help="Snapshot source label")
    ap.add_argument("--interval-sec", type=float, default=300.0, help="Polling interval between collections")
    ap.add_argument("--max-loops", type=int, default=0, help="Optional loop limit for test/manual use")
    ap.add_argument("--stop", action="store_true", help="Request stop for the running collector loop")
    ap.add_argument("--status", action="store_true", help="Show managed collector runtime status")
    ap.add_argument("--okx-pairs", action="store_true", help="Opt into raw paired OKX funding; requires explicit settings")
    ap.add_argument("--okx-pair-options-file", help="JSON file with the four funding batch limits")
    ap.add_argument("--raw-funding-max-rows", type=int, help="Explicit journal row budget per cycle")
    ap.add_argument("--raw-funding-max-bytes", type=int, help="Explicit encoded journal byte budget per cycle")
    ap.add_argument("--check-config", action="store_true", help="Validate paired configuration and print a no-start preview")
    args = ap.parse_args(argv)

    paired_arguments = (args.okx_pair_options_file is not None
                        or args.raw_funding_max_rows is not None or args.raw_funding_max_bytes is not None)
    if (args.okx_pairs or args.check_config or paired_arguments) and (args.stop or args.status):
        ap.error("paired configuration cannot be combined with stop/status")
    if (args.check_config or paired_arguments) and not args.okx_pairs:
        ap.error("paired options/check-config require --okx-pairs")
    pair_options, preview = None, None
    if args.okx_pairs:
        if (not args.okx_pair_options_file or not args.db_path.strip()
                or not args.source or args.source != args.source.strip()
                or args.raw_funding_max_rows is None or args.raw_funding_max_rows <= 0
                or args.raw_funding_max_bytes is None or args.raw_funding_max_bytes <= 0
                or not math.isfinite(args.interval_sec) or args.interval_sec <= 0
                or args.max_loops < 0):
            ap.error("paired mode requires explicit plan/options/store/source and positive budgets/interval")
        stage = "plan_file"
        try:
            plan, plan_hash = _read_object(args.plan_file)
            stage = "pair_options_file"
            pair_options, options_hash = _read_object(args.okx_pair_options_file)
            stage = "pair_plan_limits"
            rows, pair_options = validate_okx_pair_plan(plan.get("funding"), pair_options)
            if len(rows) > args.raw_funding_max_rows:
                raise ValueError("pair_plan_exceeds_row_budget")
            stage = "other_stream_lists"
            counts = {}
            for name in ("open_interest", "basis", "quotes", "order_books"):
                items = plan.get(name, [])
                if type(items) is not list or any(type(item) is not dict for item in items):
                    raise ValueError("nonfunding_plan_list_required")
                counts[name] = len(items)
        except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            ap.error("invalid paired configuration at " + stage + ": " + type(exc).__name__)
        preview = {
            "ok": True, "configuration_valid": True, "will_start": False,
            "funding_pairs": [{"venue": row["venue"], "symbol": row["symbol"], "inst_id": row["inst_id"]}
                              for row in rows],
            "funding_capture_limits": pair_options, "other_stream_row_counts": counts,
            "other_streams_outside_funding_budget": True,
            "raw_journal_limits": {"rows": args.raw_funding_max_rows, "bytes": args.raw_funding_max_bytes},
            "plan_sha256": plan_hash, "options_sha256": options_hash,
            "database_path_explicit": True, "database_ownership": "UNVERIFIED",
            "runtime_state": "UNVERIFIED", "execution_enabled": False,
        }

    if args.check_config:
        print(json.dumps(preview, indent=2))
        return 0

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
        raw_funding_only=args.okx_pairs,
        raw_funding_max_rows=args.raw_funding_max_rows,
        raw_funding_max_bytes=args.raw_funding_max_bytes,
        okx_pair_options=pair_options,
    )
    out = run_forever(cfg, max_loops=(int(args.max_loops) if int(args.max_loops or 0) > 0 else None))
    if args.okx_pairs:
        last = out.get("last_result")
        succeeded = (out.get("ok") is True and out.get("reason") != "already_running"
                     and out.get("errors") == 0 and isinstance(last, dict) and last.get("ok") is True)
        out = {**out, "ok": succeeded, "paired_run_succeeded": succeeded}
    print(json.dumps(out, indent=2, default=str))
    return 0 if not args.okx_pairs or succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
