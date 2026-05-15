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
import time

from scripts import run_bot_runner as rbr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with_reconcile", action="store_true", help="Also start live reconciler loop")
    args = ap.parse_args()

    cfg = rbr.load_trading_cfg()
    try:
        state = rbr.desired_state(cfg)
    except RuntimeError as exc:
        payload = {
            "ok": False,
            "status": "blocked",
            "error": str(exc),
            "cfg_path": "config/trading.yaml",
            "ts_epoch": time.time(),
        }
        rbr.write_status(payload)
        print(payload)
        return 2

    if args.with_reconcile:
        state = dict(state)
        state["with_reconcile"] = True

    result = rbr.apply_state(state, force_restart=False)
    result.update(
        {
            "ok": True,
            "status": "converged",
            "one_shot": True,
            "state": state,
            "signature": rbr.state_signature(state),
            "ts_epoch": time.time(),
        }
    )
    rbr.write_status(result)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
