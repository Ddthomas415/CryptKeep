from __future__ import annotations

import json
import os
# CBP_BOOTSTRAP_SYS_PATH
import sys
import traceback
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




import time
from services.config_loader import load_runtime_trading_config
from services.pipeline.pipeline_router import build_pipeline, RouterCfg
from services.os.app_paths import data_dir, ensure_dirs, runtime_dir
from services.os.file_utils import atomic_write
from services.runtime.managed_symbol_config import resolve_managed_symbols

FLAGS = runtime_dir() / "flags"
STATUS_FILE = FLAGS / "pipeline.status.json"


def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _coerce_result(out: object) -> dict:
    return out if isinstance(out, dict) else {"ok": True, "result": out}


def _build_pipelines(cfg: dict) -> tuple[list[str], list[tuple[str, object]], dict, dict, str, str]:
    pipe = cfg.get("pipeline") or {}
    ex = cfg.get("execution") or {}

    symbols = resolve_managed_symbols(cfg)
    if not symbols:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:symbols[0]")

    exchange_id = str(pipe.get("exchange_id") or "").strip().lower()
    if not exchange_id:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id")

    mode = str(ex.get("executor_mode") or "").strip().lower()
    if not mode:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:execution.executor_mode")

    pipelines: list[tuple[str, object]] = []
    for symbol in symbols:
        pipelines.append(
            (
                symbol,
                build_pipeline(
                    RouterCfg(
                        exec_db=str(ex.get("db_path") or (data_dir() / "execution.sqlite")),
                        exchange_id=exchange_id,
                        symbol=symbol,
                        timeframe=str(pipe.get("timeframe") or "5m"),
                        ohlcv_limit=int(pipe.get("ohlcv_limit") or 200),
                        mode=mode,
                        fixed_qty=float(pipe.get("fixed_qty") or 0.0),
                        quote_notional=float(pipe.get("quote_notional") or 0.0),
                        only_on_new_bar=bool(pipe.get("only_on_new_bar", True)),
                        strategy=str(pipe.get("strategy") or "ema").lower(),
                        ema_fast=int(pipe.get("ema_fast") or 12),
                        ema_slow=int(pipe.get("ema_slow") or 26),
                        bb_window=int(pipe.get("bb_window") or 20),
                        bb_k=float(pipe.get("bb_k") or 2.0),
                        sma_period=int(pipe.get("sma_period") or 200),
                        atr_period=int(pipe.get("atr_period") or 20),
                    )
                ),
            )
        )
    return symbols, pipelines, pipe, ex, exchange_id, mode


def _run_cycle(pipelines: list[tuple[str, object]]) -> dict:
    if len(pipelines) == 1:
        _symbol, pipeline = pipelines[0]
        return _coerce_result(pipeline.run_once())

    results: list[dict] = []
    all_ok = True
    for symbol, pipeline in pipelines:
        out = _coerce_result(pipeline.run_once())
        results.append({"symbol": symbol, **out})
        all_ok = all_ok and bool(out.get("ok"))
    return {
        "ok": all_ok,
        "note": "multi_symbol_cycle",
        "results": results,
    }

def main() -> int:
    ensure_dirs()
    cfg = load_runtime_trading_config()
    symbols, pipelines, pipe, _ex, exchange_id, _mode = _build_pipelines(cfg)

    poll = float(pipe.get("poll_sec") or 10.0)
    first_symbol = symbols[0] if symbols else ""
    print({"ok": True, "note": "pipeline_loop_start", "poll_sec": poll, "strategy": str(pipe.get("strategy") or "ema"), "exchange": exchange_id, "symbol": first_symbol, "symbols": symbols})
    loops = 0
    errors = 0
    last_result: dict = {}
    _write_status(
        {
            "ok": True,
            "status": "running",
            "pid": os.getpid(),
            "poll_sec": poll,
            "exchange": exchange_id,
            "symbol": first_symbol,
            "symbols": symbols,
            "ts_epoch": time.time(),
            "loops": loops,
            "errors": errors,
        }
    )
    try:
        while True:
            try:
                last_result = _run_cycle(pipelines)
                print(last_result)
                loops += 1
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                errors += 1
                last_result = {
                    "ok": False,
                    "note": "run_once_failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                print(last_result)
                traceback.print_exc()
            _write_status(
                {
                    "ok": True,
                    "status": "running",
                    "pid": os.getpid(),
                    "poll_sec": poll,
                    "exchange": exchange_id,
                    "symbol": first_symbol,
                    "symbols": symbols,
                    "ts_epoch": time.time(),
                    "loops": loops,
                    "errors": errors,
                    "last_ok": bool(last_result.get("ok")),
                    "last_reason": str(last_result.get("note") or ""),
                    "last_result": last_result,
                }
            )
            time.sleep(poll)
    except KeyboardInterrupt:
        _write_status(
            {
                "ok": True,
                "status": "stopped",
                "pid": os.getpid(),
                "poll_sec": poll,
                "exchange": exchange_id,
                "symbol": first_symbol,
                "symbols": symbols,
                "ts_epoch": time.time(),
                "loops": loops,
                "errors": errors,
                "last_ok": bool(last_result.get("ok", True)),
                "last_reason": str(last_result.get("note") or ""),
                "last_result": last_result,
            }
        )
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
