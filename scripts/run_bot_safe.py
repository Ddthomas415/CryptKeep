from __future__ import annotations

import os
import inspect
# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import argparse
import sys

from services.preflight.preflight import run_preflight
from services.strategies.base import MarketContext, PositionContext
from services.strategies.registry import get_strategy
from services.strategies.strategy_registry import compute_signal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--symbols", default="BTC/USD", help="Comma list")
    ap.add_argument("--force", action="store_true", help="Run even if preflight fails (NOT recommended)")
    args = ap.parse_args()

    syms = [s.strip().upper().replace("-", "/") for s in str(args.symbols).split(",") if s.strip()]
        # Signature-safe preflight call (compat across versions)
    os.environ.setdefault("CBP_VENUE", str(getattr(args, "venue", "") or ""))
    os.environ.setdefault("CBP_SYMBOLS", ",".join(syms))
    sig = inspect.signature(run_preflight)
    kw = {}
    if "venue" in sig.parameters:
        kw["venue"] = args.venue
    elif "exchange" in sig.parameters:
        kw["exchange"] = args.venue
    elif "name" in sig.parameters:
        kw["name"] = args.venue

    if "symbols" in sig.parameters:
        kw["symbols"] = syms
    elif "pairs" in sig.parameters:
        kw["pairs"] = syms
    elif "symbol" in sig.parameters:
        kw["symbol"] = syms[0] if syms else ""

    try:
        pf = run_preflight(**kw)
    except TypeError:
        # fallback to positional args in declared order
        args_list = []
        for p in sig.parameters:
            if p in kw:
                args_list.append(kw[p])
        pf = run_preflight(*args_list)

    print({"preflight_ok": _pf_get(pf, "ok"), "dry_run": _pf_get(pf, "dry_run"), "checks": _pf_get(pf, "checks")})

    if (not _pf_get(pf, "ok")) and (not args.force):
        # turn kill switch ON to be explicit
        try:
            from services.execution.kill_switch import set_kill_switch
            set_kill_switch(True, reason="preflight_failed")
        except Exception:
            pass
        raise SystemExit(2)

    # If passes, start runner
    from services.execution import strategy_runner  # type: ignore
    if hasattr(strategy_runner, "main"):
        return strategy_runner.main()
    if hasattr(strategy_runner, "run"):
        return strategy_runner.run()
    print("strategy_runner has no main/run; start it via your existing entrypoint.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        raise
