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

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_reconcile", action="store_true", help="Also start live reconciler loop")
    args = ap.parse_args()

    py = sys.executable

    # Start pipeline + executor loops
    r1 = start_process("pipeline", [py, "scripts/run_pipeline_loop.py"])
    r2 = start_process("executor", [py, "scripts/run_intent_executor_safe.py"])

    out = {"pipeline": r1, "executor": r2}

    if args.with_reconcile:
        out["reconciler"] = start_process("reconciler", [py, "scripts/run_intent_reconciler_safe.py"])

    out["status"] = status(["pipeline","executor","reconciler"])
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
