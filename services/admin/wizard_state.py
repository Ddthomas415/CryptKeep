from __future__ import annotations

import json
import time
from typing import Any
from services.os.app_paths import data_dir

PATH = data_dir() / "wizard_reconcile.json"

DEFAULT = {
    "version": 1,
    "updated_ts": 0.0,
    "step": 1,  # 1..6
    "last_reconcile": None,
    "last_export_path": None,
    "last_cancel_unknown": None,
    "last_reconcile_after_cancel": None,
    "last_resolve": None,
    "last_resume": None,
}

def load() -> dict[str, Any]:
    try:
        if not PATH.exists():
            return dict(DEFAULT)
        d = json.loads(PATH.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return dict(DEFAULT)
        out = dict(DEFAULT)
        out.update(d)
        return out
    except Exception:
        return dict(DEFAULT)

def save(st: dict[str, Any]) -> dict[str, Any]:
    st = dict(st or {})
    st["updated_ts"] = float(time.time())
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {"ok": True, "path": str(PATH), "updated_ts": st["updated_ts"]}

def reset() -> dict[str, Any]:
    st = dict(DEFAULT)
    save(st)
    return st

def advance(st: dict[str, Any], step: int) -> dict[str, Any]:
    st["step"] = int(step)
    save(st)
    return st
