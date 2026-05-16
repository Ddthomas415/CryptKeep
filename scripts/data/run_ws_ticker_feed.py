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
import os
import signal
from typing import Any

from services.market_data.ws_ticker_feed import WSTickerFeed, WSTickerFeedCfg


def _normalize_exchange_id(exchange_id: str) -> str:
    v = str(exchange_id or "").lower().strip()
    return {"gate": "gateio", "gate.io": "gateio", "coinbase_adv": "coinbase"}.get(v, v)


def _credentials_from_env(exchange_id: str) -> dict[str, str]:
    ex = str(exchange_id).upper().replace(".", "_")
    key = os.environ.get(f"{ex}_API_KEY") or os.environ.get("CBP_API_KEY")
    sec = os.environ.get(f"{ex}_API_SECRET") or os.environ.get("CBP_API_SECRET")
    pwd = (
        os.environ.get(f"{ex}_API_PASSPHRASE")
        or os.environ.get(f"{ex}_API_PASSWORD")
        or os.environ.get("CBP_API_PASSPHRASE")
    )
    out: dict[str, str] = {}
    if key:
        out["apiKey"] = key
    if sec:
        out["secret"] = sec
    if pwd:
        out["password"] = pwd
    return out


def _build_exchange(exchange_id: str, *, sandbox: bool = False) -> Any:
    ex_id = _normalize_exchange_id(exchange_id)
    import ccxt.pro as ccxtpro  # type: ignore

    ex_cls = getattr(ccxtpro, ex_id, None)
    if ex_cls is None:
        raise RuntimeError(f"unsupported_exchange:{ex_id}")
    params: dict[str, Any] = {"enableRateLimit": True}
    params.update(_credentials_from_env(ex_id))
    ex = ex_cls(params)
    if hasattr(ex, "set_sandbox_mode"):
        try:
            ex.set_sandbox_mode(bool(sandbox))
        except Exception:
            pass
    return ex


async def _safe_close(ex: Any) -> None:
    try:
        fn = getattr(ex, "close", None)
        if callable(fn):
            out = fn()
            if asyncio.iscoroutine(out):
                await out
    except Exception:
        pass


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run watchTicker WS feed with auto-disable blacklist behavior.")
    ap.add_argument("--venue", default="coinbase")
    ap.add_argument("--symbol", default="BTC/USD")
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--max-errors-before-disable", type=int, default=10)
    ap.add_argument("--disable-cooldown-sec", type=int, default=1800)
    ap.add_argument("--max-events", type=int, default=0, help="0 means run forever")
    return ap


async def _main_async() -> int:
    args = _build_parser().parse_args()
    try:
        ex = _build_exchange(args.venue, sandbox=bool(args.sandbox))
    except Exception as e:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "exchange_init_failed",
                    "error": f"{type(e).__name__}:{e}",
                    "venue": str(args.venue),
                }
            )
        )
        return 2
    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except Exception:
            pass
    cfg = WSTickerFeedCfg(
        max_errors_before_disable=max(1, int(args.max_errors_before_disable)),
        disable_cooldown_sec=max(1, int(args.disable_cooldown_sec)),
    )
    feed = WSTickerFeed(exchange=ex, venue=str(args.venue), symbol=str(args.symbol), cfg=cfg)
    print(json.dumps({"ok": True, "service": "ws_ticker_feed", "venue": args.venue, "symbol": args.symbol, "cfg": cfg.__dict__}))
    seen = 0
    try:
        async for q in feed.stream(stop_event=stop):
            print(json.dumps({"ok": True, "ticker": q}))
            seen += 1
            if int(args.max_events) > 0 and seen >= int(args.max_events):
                stop.set()
                break
    finally:
        await _safe_close(ex)
    return 0


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    raise SystemExit(main())
