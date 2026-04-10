from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml
from services.os.app_paths import code_root, config_dir, ensure_dirs

ensure_dirs()
_CFG_PATH = config_dir() / "user.yaml"
DEFAULT_TRADING_CFG_PATH = "config/trading.yaml"

def load_user_config() -> Dict[str, Any]:
    if not _CFG_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_yaml_file(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _merge_dicts(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(current, value)
        else:
            merged[key] = value
    return merged


def _normalize_runtime_trading_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(cfg)
    live = dict(out.get("live") or {})
    execution = dict(out.get("execution") or {})
    preflight = dict(out.get("preflight") or {})

    if "live_enabled" in execution:
        live["enabled"] = execution.get("live_enabled")
    elif "enabled" in live:
        execution["live_enabled"] = live.get("enabled")

    if not out.get("symbols") and isinstance(preflight.get("symbols"), list):
        out["symbols"] = list(preflight.get("symbols") or [])

    if not live.get("exchange_id"):
        venues = preflight.get("venues")
        if isinstance(venues, list) and venues:
            live["exchange_id"] = venues[0]

    out["live"] = live
    out["execution"] = execution
    return out


def _is_default_trading_cfg_path(path: str | Path) -> bool:
    if Path(path) == Path(DEFAULT_TRADING_CFG_PATH):
        return True
    try:
        return Path(path).resolve() == (code_root() / DEFAULT_TRADING_CFG_PATH).resolve()
    except Exception:
        return False


def runtime_trading_config_available(path: str = DEFAULT_TRADING_CFG_PATH) -> bool:
    p = Path(path)
    if _is_default_trading_cfg_path(p):
        return (code_root() / DEFAULT_TRADING_CFG_PATH).exists() or _CFG_PATH.exists()
    return p.exists()


def load_runtime_trading_config(path: str = DEFAULT_TRADING_CFG_PATH) -> Dict[str, Any]:
    if not _is_default_trading_cfg_path(path):
        return _normalize_runtime_trading_config(_load_yaml_file(path))

    legacy_cfg = _load_yaml_file(code_root() / DEFAULT_TRADING_CFG_PATH)
    runtime_cfg = load_user_config()
    return _normalize_runtime_trading_config(_merge_dicts(legacy_cfg, runtime_cfg))
