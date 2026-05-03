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
from services.runtime.process_supervisor import start_process, status

CORE_SERVICES = ["pipeline", "executor", "intent_consumer", "ops_signal_adapter", "ops_risk_gate"]
ALL_SERVICES = CORE_SERVICES + ["reconciler"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_reconcile", action="store_true", help="Also start live reconciler loop")
    args = ap.parse_args()

    py = sys.executable

    # Start pipeline + paper executor loop, telemetry adapter, and the ops risk-gate service.
    r1 = start_process("pipeline", [py, "scripts/run_pipeline_loop.py"])
    r2 = start_process("executor", [py, "scripts/run_intent_executor_safe.py"])
    r3 = start_process("intent_consumer", [py, "scripts/run_live_intent_consumer.py", "run"])
    r4 = start_process("ops_signal_adapter", [py, "scripts/run_ops_signal_adapter.py", "run"])
    r5 = start_process("ops_risk_gate", [py, "scripts/run_ops_risk_gate_service.py", "run"])

    out = {"pipeline": r1, "executor": r2, "intent_consumer": r3, "ops_signal_adapter": r4, "ops_risk_gate": r5}

    if args.with_reconcile:
        out["reconciler"] = start_process("reconciler", [py, "scripts/run_live_reconciler_safe.py", "run"])

    out["status"] = status(ALL_SERVICES)
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
