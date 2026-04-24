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
import json

from services.config_loader import load_runtime_trading_config
from services.os.app_paths import data_dir, ensure_dirs
from services.risk.fill_hook import record_fill
from services.risk.risk_daily import RiskDailyDB

def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTC-USD")
    ap.add_argument("--pnl", type=float, default=0.0)
    ap.add_argument("--fee", type=float, default=0.0)
    args = ap.parse_args()

    cfg = load_runtime_trading_config()
    ex_cfg = (cfg.get("execution") or {})
    exec_db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

    cf = record_fill(exec_db, {"symbol": args.symbol, "realized_pnl_usd": args.pnl, "fee_usd": args.fee})
    snap = RiskDailyDB(exec_db).get()
    print(json.dumps({"ok": True, "fill": cf.__dict__, "risk_daily_today": snap}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
