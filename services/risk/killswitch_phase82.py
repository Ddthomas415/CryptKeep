from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml
from services.risk.live_risk_gates_phase82 import LiveGateDB
from services.os.app_paths import data_dir, ensure_dirs

def _exec_db_from_trading_yaml(path: str = "config/trading.yaml") -> str:
    ensure_dirs()
    p = Path(path)
    if not p.exists():
        return str(data_dir() / "execution.sqlite")
    cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    ex_cfg = cfg.get("execution") or {}
    return str(ex_cfg.get("db_path") or (data_dir() / "execution.sqlite"))

@dataclass
class KillSwitch:
    exec_db: str

    @staticmethod
    def from_config() -> "KillSwitch":
        return KillSwitch(exec_db=_exec_db_from_trading_yaml())

    def is_on(self) -> bool:
        return LiveGateDB(self.exec_db).killswitch_on()

    def set(self, on: bool) -> None:
        LiveGateDB(self.exec_db).set_killswitch(on)
