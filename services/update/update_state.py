from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DEFAULT_PATH = str(data_dir() / "update_state.json")

def load_state(path: str = DEFAULT_PATH) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

def save_state(state: Dict[str, Any], path: str = DEFAULT_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state or {}, indent=2, sort_keys=True), encoding="utf-8")

def get_last_accepted_version(path: str = DEFAULT_PATH) -> str | None:
    st = load_state(path)
    v = st.get("last_accepted_version")
    return str(v) if v else None

def set_last_accepted_version(version: str, path: str = DEFAULT_PATH) -> None:
    st = load_state(path)
    st["last_accepted_version"] = str(version)
    save_state(st, path)

def get_last_manifest_sha256(path: str = DEFAULT_PATH) -> str | None:
    st = load_state(path)
    v = st.get("last_manifest_sha256")
    return str(v) if v else None

def set_last_manifest_sha256(sha256_hex: str, path: str = DEFAULT_PATH) -> None:
    st = load_state(path)
    st["last_manifest_sha256"] = str(sha256_hex)
    save_state(st, path)
