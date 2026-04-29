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
import logging
from services.admin.live_disable_wizard import disable_live_now
from services.runtime.process_supervisor import stop_process, status

logger = logging.getLogger(__name__)

ALL_SERVICES = ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate", "reconciler"]


def main() -> int:
    try:
        disable_live_now(note="stop_bot")
    except Exception as exc:
        logger.warning("disable_live_now failed during stop_bot: %s", exc)

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--all",
        action="store_true",
        help="Stop pipeline, executor, intent_consumer, ops_signal_adapter, ops_risk_gate, reconciler",
    )
    ap.add_argument("--pipeline", action="store_true")
    ap.add_argument("--executor", action="store_true")
    ap.add_argument("--intent_consumer", action="store_true")
    ap.add_argument("--ops_signal_adapter", action="store_true")
    ap.add_argument("--ops_risk_gate", action="store_true")
    ap.add_argument("--reconciler", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.all or (
        not any(
            [
                args.pipeline,
                args.executor,
                args.intent_consumer,
                args.ops_signal_adapter,
                args.ops_risk_gate,
                args.reconciler,
            ]
        )
    ):
        targets = list(ALL_SERVICES)
    else:
        if args.pipeline:
            targets.append("pipeline")
        if args.executor:
            targets.append("executor")
        if args.intent_consumer:
            targets.append("intent_consumer")
        if args.ops_signal_adapter:
            targets.append("ops_signal_adapter")
        if args.ops_risk_gate:
            targets.append("ops_risk_gate")
        if args.reconciler:
            targets.append("reconciler")

    out = {t: stop_process(t) for t in targets}
    out["status"] = status(ALL_SERVICES)
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
