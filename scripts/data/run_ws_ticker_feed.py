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
from datetime import datetime, timezone
from typing import Any

from services.config_loader import load_runtime_trading_config, runtime_trading_config_available
from services.market_data.ws_ticker_feed import WSTickerFeed, WSTickerFeedCfg
from services.os.app_paths import ensure_dirs, runtime_dir
from services.os.file_utils import atomic_write


FLAGS = runtime_dir() / "flags"
HEALTH = runtime_dir() / "health"
STOP_FILE = FLAGS / "market_ws.stop"
STATUS_FILE = HEALTH / "market_ws.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_status(payload: dict[str, Any]) -> None:
    ensure_dirs()
    HEALTH.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(payload, indent=2, sort_keys=True) + "\n")


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


def _default_venue() -> str:
    raw = str(os.environ.get("CBP_VENUE") or "").strip()
    if raw:
        return _normalize_exchange_id(raw.split(",")[0])
    if runtime_trading_config_available():
        try:
            cfg = load_runtime_trading_config()
            live = cfg.get("live") if isinstance(cfg.get("live"), dict) else {}
            pipeline = cfg.get("pipeline") if isinstance(cfg.get("pipeline"), dict) else {}
            candidate = live.get("exchange_id") or pipeline.get("exchange_id") or cfg.get("venue")
            if candidate:
                return _normalize_exchange_id(str(candidate))
        except Exception:
            pass
    return "coinbase"


def _default_symbol() -> str:
    raw = str(os.environ.get("CBP_SYMBOLS") or "").strip()
    if raw:
        symbols = [item.strip() for item in raw.split(",") if item.strip()]
        if symbols:
            return symbols[0]
    if runtime_trading_config_available():
        try:
            cfg = load_runtime_trading_config()
            symbols = cfg.get("symbols") or []
            if isinstance(symbols, list):
                for symbol in symbols:
                    if str(symbol).strip():
                        return str(symbol).strip()
        except Exception:
            pass
    return "BTC/USD"


def request_stop() -> dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text("stop\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}


async def _watch_stop_file(stop: asyncio.Event) -> None:
    while not stop.is_set():
        if STOP_FILE.exists():
            stop.set()
            return
        await asyncio.sleep(0.2)


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run watchTicker WS feed with auto-disable blacklist behavior.")
    ap.add_argument("cmd", nargs="?", choices=["run", "stop"], default="run")
    ap.add_argument("--venue", default=_default_venue())
    ap.add_argument("--symbol", default=_default_symbol())
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--max-errors-before-disable", type=int, default=10)
    ap.add_argument("--disable-cooldown-sec", type=int, default=1800)
    ap.add_argument("--max-events", type=int, default=0, help="0 means run forever")
    return ap


async def _main_async(args: argparse.Namespace) -> int:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass
    _write_status(
        {
            "ok": True,
            "status": "starting",
            "ts": _now(),
            "venue": str(args.venue),
            "symbol": str(args.symbol),
            "events": 0,
        }
    )
    try:
        ex = _build_exchange(args.venue, sandbox=bool(args.sandbox))
    except Exception as e:
        _write_status(
            {
                "ok": False,
                "status": "error",
                "reason": "exchange_init_failed",
                "error": f"{type(e).__name__}:{e}",
                "ts": _now(),
                "venue": str(args.venue),
                "symbol": str(args.symbol),
                "events": 0,
            }
        )
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
    stop_task = asyncio.create_task(_watch_stop_file(stop))
    cfg = WSTickerFeedCfg(
        max_errors_before_disable=max(1, int(args.max_errors_before_disable)),
        disable_cooldown_sec=max(1, int(args.disable_cooldown_sec)),
    )
    feed = WSTickerFeed(exchange=ex, venue=str(args.venue), symbol=str(args.symbol), cfg=cfg)
    print(json.dumps({"ok": True, "service": "ws_ticker_feed", "venue": args.venue, "symbol": args.symbol, "cfg": cfg.__dict__}))
    seen = 0
    stop_reason = "stream_exited"
    try:
        async for q in feed.stream(stop_event=stop):
            print(json.dumps({"ok": True, "ticker": q}))
            seen += 1
            _write_status(
                {
                    "ok": True,
                    "status": "running",
                    "ts": _now(),
                    "venue": str(args.venue),
                    "symbol": str(args.symbol),
                    "events": seen,
                    "last_quote_ts_ms": int(q.get("ts_ms") or 0),
                }
            )
            if int(args.max_events) > 0 and seen >= int(args.max_events):
                stop_reason = "max_events"
                stop.set()
                break
        if stop_reason != "max_events":
            stop_reason = "stop_requested" if stop.is_set() else "stream_exited"
        _write_status(
            {
                "ok": True,
                "status": "stopped",
                "reason": stop_reason,
                "ts": _now(),
                "venue": str(args.venue),
                "symbol": str(args.symbol),
                "events": seen,
            }
        )
    except Exception as e:
        _write_status(
            {
                "ok": False,
                "status": "error",
                "reason": "ws_feed_runtime_error",
                "error": f"{type(e).__name__}:{e}",
                "ts": _now(),
                "venue": str(args.venue),
                "symbol": str(args.symbol),
                "events": seen,
            }
        )
        raise
    finally:
        stop_task.cancel()
        await _safe_close(ex)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "stop":
        print(json.dumps(request_stop()))
        return 0
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
