from __future__ import annotations

import os
# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




from services.config_loader import load_runtime_trading_config
from services.pipeline.pipeline_router import build_pipeline, RouterCfg
from services.os.app_paths import data_dir, ensure_dirs
from services.runtime.managed_symbol_config import resolve_managed_symbols

def main() -> int:
    ensure_dirs()
    cfg = load_runtime_trading_config()
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

    results: list[dict] = []
    all_ok = True
    for symbol in symbols:
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
        ))
        out = p.run_once()
        out = out if isinstance(out, dict) else {"ok": True, "result": out}
        if len(symbols) == 1:
            results = [out]
        else:
            results.append({"symbol": symbol, **out})
        all_ok = all_ok and bool(out.get("ok"))
    out = results[0] if len(results) == 1 else {"ok": all_ok, "note": "multi_symbol_cycle", "results": results}
    print(out)
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
