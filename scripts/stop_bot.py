from __future__ import annotations

import argparse
from services.runtime.process_supervisor import stop_process, status

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Stop pipeline, executor, reconciler")
    ap.add_argument("--pipeline", action="store_true")
    ap.add_argument("--executor", action="store_true")
    ap.add_argument("--reconciler", action="store_true")
    args = ap.parse_args()

    targets = []
    if args.all or (not any([args.pipeline, args.executor, args.reconciler])):
        targets = ["pipeline","executor","reconciler"]
    else:
        if args.pipeline: targets.append("pipeline")
        if args.executor: targets.append("executor")
        if args.reconciler: targets.append("reconciler")

    out = {t: stop_process(t) for t in targets}
    out["status"] = status(["pipeline","executor","reconciler"])
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
