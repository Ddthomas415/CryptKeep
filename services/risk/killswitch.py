from __future__ import annotations

import logging
_LOG = logging.getLogger(__name__)

# CBP_OPTIONAL_YAML_V1

from dataclasses import dataclass
from pathlib import Path
import os
# yaml is optional (PyYAML)

from services.os.app_paths import data_dir, ensure_dirs
from services.risk.live_risk_gates import LiveGateDB  # canonical


def _admin_armed() -> bool:
    """
    Treat the canonical admin/runtime kill switch as part of the effective
    execution safety boundary.
    """
    try:
        from services.admin.kill_switch import get_state as get_admin_kill_switch_state

        state = get_admin_kill_switch_state()
        if isinstance(state, dict):
            return bool(state.get("armed", True))
    except Exception as exc:
        _LOG.debug("killswitch_admin_read_failed: %s", exc)
    return True

def _exec_db_from_trading_yaml(path: str = "config/trading.yaml") -> str:
    # Prefer env override
    env_db = os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH")
    if env_db:
        return str(env_db)

    p = Path(path)
    if not p.exists():
        ensure_dirs()
        return str(data_dir() / "execution.sqlite")

    # PyYAML optional
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        ex_cfg = (cfg.get("execution") or {})
        if isinstance(ex_cfg, dict) and ex_cfg.get("db_path"):
            return str(ex_cfg.get("db_path"))
    except Exception as _err:
        pass  # suppressed: see _LOG.debug below

    ensure_dirs()
    return str(data_dir() / "execution.sqlite")

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
# CBP_KILLSWITCH_MODULE_HELPERS_V1
def is_on() -> bool:
    """
    Module-level convenience: return True if kill switch is ON.
    """
    if _admin_armed():
        return True
    try:
        return bool(KillSwitch.from_config().is_on())
    except Exception:
        return False

def snapshot() -> dict:
    """
    Best-effort snapshot API used by chokepoints.
    """
    return {"kill_switch": bool(is_on()), "cooldown_until": 0.0}
