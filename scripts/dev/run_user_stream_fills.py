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
import asyncio
import json
import signal

from services.fills.user_stream_ws import UserStreamFillService, UserStreamWSConfig


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run authenticated user-stream fills router (optional).")
    ap.add_argument("--exchange", default="coinbase", help="Exchange id (coinbase/binance/gateio)")
    ap.add_argument("--exec-db", default=".cbp_state/data/execution.sqlite", help="Execution DB path")
    ap.add_argument("--symbol", default="", help="Optional symbol filter (e.g. BTC/USD)")
    ap.add_argument("--sandbox", action="store_true", help="Enable sandbox mode")
    ap.add_argument("--no-live-hook", action="store_true", help="Disable live_executor._on_fill hook preference")
    ap.add_argument("--retry-sleep-sec", type=float, default=2.0, help="Retry sleep on ws errors")
    return ap


async def _main_async() -> int:
    args = _build_arg_parser().parse_args()
    cfg = UserStreamWSConfig(
        exchange_id=str(args.exchange),
        exec_db=str(args.exec_db),
        symbol=(str(args.symbol).strip() or None),
        sandbox=bool(args.sandbox),
        route_via_live_executor_hook=not bool(args.no_live_hook),
        retry_sleep_sec=float(args.retry_sleep_sec),
    )
    svc = UserStreamFillService(cfg)
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, svc.stop)
        except Exception:
            pass
    print(json.dumps({"ok": True, "service": "user_stream_fills", "cfg": cfg.__dict__}, indent=2))
    out = await svc.run_forever()
    print(json.dumps(out, indent=2))
    return 0 if bool(out.get("ok")) else 2


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    raise SystemExit(main())
