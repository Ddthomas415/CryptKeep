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
from pathlib import Path
import yaml

from services.os.app_paths import data_dir, ensure_dirs
from services.risk.risk_daily import RiskDailyDB

def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--pnl", type=float, default=0.0)
    ap.add_argument("--fee", type=float, default=0.0)
    ap.add_argument("--trades", type=int, default=0)
    args = ap.parse_args()

    cfg_path = Path("config/trading.yaml")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    ex_cfg = (cfg.get("execution") or {})
    exec_db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

    db = RiskDailyDB(exec_db)
    if args.trades:
        db.incr_trades(args.trades)
    if args.pnl or args.fee:
        db.add_pnl(realized_pnl_usd=args.pnl, fee_usd=args.fee)

    print(json.dumps({"ok": True, "risk_daily_today": db.get()}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
