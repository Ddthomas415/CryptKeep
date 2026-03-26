from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from services.preflight.preflight import run_preflight


def _pf_get(payload: Any, key: str, default: Any = None) -> Any:
    if isinstance(payload, dict):
        return payload.get(key, default)
    return getattr(payload, key, default)


def _invoke_preflight(*, venue: str, symbols: list[str]) -> Any:
    sig = inspect.signature(run_preflight)
    kwargs: dict[str, Any] = {}
    if "venue" in sig.parameters:
        kwargs["venue"] = venue
    elif "exchange" in sig.parameters:
        kwargs["exchange"] = venue
    elif "name" in sig.parameters:
        kwargs["name"] = venue

    if "symbols" in sig.parameters:
        kwargs["symbols"] = symbols
    elif "pairs" in sig.parameters:
        kwargs["pairs"] = symbols
    elif "symbol" in sig.parameters:
        kwargs["symbol"] = symbols[0] if symbols else ""

    try:
        return run_preflight(**kwargs)
    except TypeError:
        args_list: list[Any] = []
        for param_name in sig.parameters:
            if param_name in kwargs:
                args_list.append(kwargs[param_name])
        return run_preflight(*args_list)


def _start_strategy_runner() -> int:
    from services.strategy_runner import ema_crossover_runner as strategy_runner

    if hasattr(strategy_runner, "main") and callable(strategy_runner.main):
        return int(strategy_runner.main())
    if hasattr(strategy_runner, "run") and callable(strategy_runner.run):
        return int(strategy_runner.run())
    if hasattr(strategy_runner, "run_forever") and callable(strategy_runner.run_forever):
        strategy_runner.run_forever()
        return 0
    raise SystemExit(
        "strategy runner has no runnable entrypoint (expected main/run/run_forever in "
        "services.strategy_runner.ema_crossover_runner)"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--symbols", default="BTC/USD", help="Comma-separated symbol list")
    ap.add_argument("--force", action="store_true", help="Run even if preflight fails")
    args = ap.parse_args(argv)

    symbols = [item.strip().upper().replace("-", "/") for item in str(args.symbols or "").split(",") if item.strip()]
    os.environ.setdefault("CBP_VENUE", str(args.venue or ""))
    os.environ.setdefault("CBP_SYMBOLS", ",".join(symbols))

    preflight = _invoke_preflight(venue=str(args.venue or "coinbase"), symbols=symbols)
    print(
        {
            "preflight_ok": _pf_get(preflight, "ok"),
            "dry_run": _pf_get(preflight, "dry_run"),
            "checks": _pf_get(preflight, "checks"),
        }
    )

    if not bool(_pf_get(preflight, "ok")) and not bool(args.force):
        try:
            from services.execution.kill_switch import set_kill_switch

            set_kill_switch(True, reason="preflight_failed")
        except Exception:
            pass
        raise SystemExit(2)

    return _start_strategy_runner()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback

        traceback.print_exc()
        raise
