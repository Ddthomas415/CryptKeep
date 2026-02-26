from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml
from services.os.app_paths import config_dir, ensure_dirs

ensure_dirs()
_CFG_PATH = config_dir() / "user.yaml"

def load_user_config() -> Dict[str, Any]:
    if not _CFG_PATH.exists():
        return {}
    try:
        return yaml.safe_load(_CFG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
