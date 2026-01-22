from __future__ import annotations

import json
import yaml

from services.risk.live_risk_gates_phase82 import LiveRiskLimits, LiveGateDB
from services.risk.journal_introspection_phase83 import JournalSignals

def main() -> int:
    cfg = yaml.safe_load(open("config/trading.yaml","r",encoding="utf-8").read()) or {}
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or "data/execution.sqlite")

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
