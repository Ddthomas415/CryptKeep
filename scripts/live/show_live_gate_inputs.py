from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)




import json

from services.admin.kill_switch import get_state as get_admin_kill_switch_state
from services.config_loader import load_runtime_trading_config
from services.os.app_paths import data_dir, ensure_dirs
from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB
from services.risk.journal_introspection_phase83 import JournalSignals

def main() -> int:
    ensure_dirs()
    cfg = load_runtime_trading_config()
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

    limits = LiveRiskLimits.from_dict(cfg)
    db = LiveGateDB(exec_db=exec_db)
    js = JournalSignals(exec_db=exec_db)
    admin_state = get_admin_kill_switch_state()
    admin_armed = bool((admin_state or {}).get("armed", True))
    db_armed = db.killswitch_on()

    out = {
        "exec_db": exec_db,
        "killswitch": bool(admin_armed or db_armed),
        "killswitch_admin": admin_armed,
        "killswitch_db": db_armed,
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
