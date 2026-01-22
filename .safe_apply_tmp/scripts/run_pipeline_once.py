from __future__ import annotations

import yaml
from services.pipeline.pipeline_router import build_pipeline, RouterCfg

def main() -> int:
    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    pipe = cfg.get("pipeline") or {}
    ex = cfg.get("execution") or {}

    symbols = cfg.get("symbols") or ["BTC/USDT"]
    symbol = str(pipe.get("symbol") or symbols[0]).upper()

    p = build_pipeline(RouterCfg(
        exec_db=str(ex.get("db_path") or "data/execution.sqlite"),
        exchange_id=str(pipe.get("exchange_id") or "coinbase").lower(),
        symbol=symbol,
        timeframe=str(pipe.get("timeframe") or "5m"),
        ohlcv_limit=int(pipe.get("ohlcv_limit") or 200),
        mode=str(ex.get("executor_mode") or "paper").lower(),
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
    print(out)
    return 0 if out.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
