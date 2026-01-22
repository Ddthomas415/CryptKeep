from __future__ import annotations

import argparse
import sys
from services.runtime.process_supervisor import start_process, status

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_reconcile", action="store_true", help="Also start live reconciler loop")
    args = ap.parse_args()

    py = sys.executable

    # Start pipeline + executor loops
    r1 = start_process("pipeline", [py, "scripts/run_pipeline_loop.py"])
    r2 = start_process("executor", [py, "scripts/run_executor_loop.py"])

    out = {"pipeline": r1, "executor": r2}

    if args.with_reconcile:
        out["reconciler"] = start_process("reconciler", [py, "scripts/run_live_reconcile_loop.py"])

    out["status"] = status(["pipeline","executor","reconciler"])
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
