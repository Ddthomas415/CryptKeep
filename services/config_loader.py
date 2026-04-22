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
    import logging
    import json
    from services.os.app_paths import config_dir
    _LOG = logging.getLogger(__name__)
    out = dict(cfg)
    live = dict(out.get("live") or {})
    execution = dict(out.get("execution") or {})
    preflight = dict(out.get("preflight") or {})

    if "live_enabled" in execution:
        new_val = execution.get("live_enabled")
        if live.get("enabled") != new_val:
            _LOG.debug("[CONFIG AUTHORITY] live.enabled <- execution.live_enabled = %s", new_val)
        live["enabled"] = new_val
    elif "enabled" in live:
        new_val = live.get("enabled")
        if execution.get("live_enabled") != new_val:
            _LOG.debug("[CONFIG AUTHORITY] execution.live_enabled <- live.enabled = %s", new_val)
        execution["live_enabled"] = new_val

    if not out.get("symbols") and isinstance(preflight.get("symbols"), list):
        _LOG.debug("[CONFIG AUTHORITY] symbols injected from preflight: %s", preflight.get("symbols"))
        out["symbols"] = list(preflight.get("symbols") or [])

    if not live.get("exchange_id"):
        venues = preflight.get("venues")
        if isinstance(venues, list) and venues:
            _LOG.debug("[CONFIG AUTHORITY] exchange_id injected from preflight.venues[0]: %s", venues[0])
            live["exchange_id"] = venues[0]

    out["live"] = live
    out["execution"] = execution

    # Write canonical snapshot for audit and single source of truth
    try:
        canonical_path = config_dir() / "canonical_runtime.json"
        canonical_path.write_text(json.dumps(out, indent=2, default=str))
        _LOG.debug("[CONFIG AUTHORITY] Canonical config written to %s", canonical_path)
    except Exception as e:
        _LOG.warning("[CONFIG AUTHORITY] Could not write canonical snapshot: %s", e)

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
