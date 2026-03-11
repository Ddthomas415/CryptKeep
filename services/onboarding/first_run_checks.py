from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from services.admin.config_editor import CONFIG_PATH, ensure_user_yaml_exists, validate_user_yaml
from services.admin.kill_switch import ensure_default as ensure_kill_switch_default
from services.os.app_paths import ensure_dirs, runtime_dir


def run_first_run_checks() -> Dict[str, Any]:
    ensure_dirs()
    cfg_ok = ensure_user_yaml_exists()
    ks = ensure_kill_switch_default()
    cfg = {}
    if Path(CONFIG_PATH).exists():
        try:
            import yaml  # type: ignore

            cfg = yaml.safe_load(Path(CONFIG_PATH).read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}
    valid, errors, warnings = validate_user_yaml(cfg)
    return {
        "ok": bool(cfg_ok and valid),
        "config_path": str(CONFIG_PATH),
        "config_exists": Path(CONFIG_PATH).exists(),
        "config_valid": bool(valid),
        "config_errors": errors,
        "config_warnings": warnings,
        "kill_switch": ks,
        "runtime_dir": str(runtime_dir()),
    }
