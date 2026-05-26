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

from services.admin.reconcile_safe_steps import run_all_safe_steps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--symbols", default="BTC/USD")
    ap.add_argument("--mode", default="spot", choices=["spot", "derivatives"])
    ap.add_argument("--require-exchange-ok", action="store_true")
    args = ap.parse_args()

    symbols = [x.strip() for x in str(args.symbols).split(",") if x.strip()]
    out = run_all_safe_steps(
        venue=str(args.venue),
        symbols=symbols,
        mode=str(args.mode),
        require_exchange_ok=bool(args.require_exchange_ok),
    )
    print(json.dumps(out, ensure_ascii=False))
    return 0 if bool(out.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
