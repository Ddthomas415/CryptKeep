from __future__ import annotations

import json
import os
# CBP_BOOTSTRAP_SYS_PATH
import sys
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

FLAGS = runtime_dir() / "flags"
STATUS_FILE = FLAGS / "pipeline.status.json"


def _write_status(obj: dict) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(obj, indent=2, sort_keys=True) + "\n")

def main() -> int:
    ensure_dirs()
    cfg = load_runtime_trading_config()
    pipe = cfg.get("pipeline") or {}
    ex = cfg.get("execution") or {}

    poll = float(pipe.get("poll_sec") or 10.0)

    symbols = cfg.get("symbols") or []

    _env_syms = (os.environ.get("CBP_SYMBOLS") or "").strip()

    if _env_syms:
        symbols = [x.strip() for x in _env_syms.split(",") if x.strip()]

    if not symbols:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:symbols[0]")

    symbol = str(pipe.get("symbol") or symbols[0]).upper()

    exchange_id = str(pipe.get("exchange_id") or "").strip().lower()
    if not exchange_id:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:pipeline.exchange_id")

    mode = str(ex.get("executor_mode") or "").strip().lower()
    if not mode:
        raise RuntimeError("CBP_CONFIG_REQUIRED:missing_config:execution.executor_mode")

    p = build_pipeline(RouterCfg(
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
    ))

    print({"ok": True, "note": "pipeline_loop_start", "poll_sec": poll, "strategy": str(pipe.get("strategy") or "ema"), "exchange": p.cfg.exchange_id if hasattr(p, "cfg") else None, "symbol": symbol})
    loops = 0
    _write_status(
        {
            "ok": True,
            "status": "running",
            "pid": os.getpid(),
            "poll_sec": poll,
            "exchange": p.cfg.exchange_id if hasattr(p, "cfg") else None,
            "symbol": symbol,
            "ts_epoch": time.time(),
            "loops": loops,
        }
    )
    try:
        while True:
            out = p.run_once()
            print(out)
            loops += 1
            _write_status(
                {
                    "ok": True,
                    "status": "running",
                    "pid": os.getpid(),
                    "poll_sec": poll,
                    "exchange": p.cfg.exchange_id if hasattr(p, "cfg") else None,
                    "symbol": symbol,
                    "ts_epoch": time.time(),
                    "loops": loops,
                    "last_result": out,
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
                "exchange": p.cfg.exchange_id if hasattr(p, "cfg") else None,
                "symbol": symbol,
                "ts_epoch": time.time(),
                "loops": loops,
            }
        )
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
