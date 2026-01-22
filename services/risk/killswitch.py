from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import yaml

from services.risk.live_risk_gates import LiveGateDB

def _exec_db_from_trading_yaml(path: str = "config/trading.yaml") -> str:
    p = Path(path)
    if not p.exists():
        return "data/execution.sqlite"
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    ex_cfg = (cfg.get("execution") or {})
    return str(ex_cfg.get("db_path") or "data/execution.sqlite")

@dataclass
class KillSwitch:
    exec_db: str

    @staticmethod
    def from_config() -> "KillSwitch":
        return KillSwitch(exec_db=_exec_db_from_trading_yaml())

    def _db(self) -> LiveGateDB:
        return LiveGateDB(self.exec_db)

    def is_on(self) -> bool:
        return self._db().killswitch_on()

    def set(self, on: bool) -> None:
        self._db().set_killswitch(bool(on))
