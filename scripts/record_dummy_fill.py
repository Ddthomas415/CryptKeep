from __future__ import annotations

import argparse
import json
from pathlib import Path
import yaml

from services.risk.fill_hook import record_fill
from services.risk.risk_daily import RiskDailyDB

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTC-USD")
    ap.add_argument("--pnl", type=float, default=0.0)
    ap.add_argument("--fee", type=float, default=0.0)
    args = ap.parse_args()

    cfg_path = Path("config/trading.yaml")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    ex_cfg = (cfg.get("execution") or {})
    exec_db = str(ex_cfg.get("db_path") or "data/execution.sqlite")

    cf = record_fill(exec_db, {"symbol": args.symbol, "realized_pnl_usd": args.pnl, "fee_usd": args.fee})
    snap = RiskDailyDB(exec_db).get()
    print(json.dumps({"ok": True, "fill": cf.__dict__, "risk_daily_today": snap}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
