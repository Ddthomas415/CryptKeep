from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


# CBP_BOOTSTRAP: ensure repo root on sys.path so `import services` works when running scripts directly
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import json
import yaml

from services.os.app_paths import data_dir, ensure_dirs
from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB
from services.risk.journal_introspection_phase83 import JournalSignals

def main() -> int:
    ensure_dirs()
    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

    limits = LiveRiskLimits.from_trading_yaml("config/trading.yaml")
    db = LiveGateDB(exec_db=exec_db)
    js = JournalSignals(exec_db=exec_db)

    out = {
        "exec_db": exec_db,
        "killswitch": db.killswitch_on(),
        "limits": None if not limits else {
            "max_daily_loss_usd": limits.max_daily_loss_usd,
            "max_notional_per_trade_usd": limits.max_notional_per_trade_usd,
            "max_trades_per_day": limits.max_trades_per_day,
            "max_position_notional_usd": limits.max_position_notional_usd,
        },
        "daily_limits_row": db.day_row(),
        "computed": {
            "realized_pnl_today_usd": js.realized_pnl_today_usd(),
            "trades_today": js.trades_today(),
        },
    }
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
