from __future__ import annotations

from dataclasses import asdict
from dataclasses import is_dataclass
from typing import Any, Dict

from services.release.local_build import (
    build_macos_app_and_dmg,
    build_windows_installer_inno,
    build_windows_pyinstaller,
)


TARGETS = {
    "windows_pyinstaller": build_windows_pyinstaller,
    "windows_inno": build_windows_installer_inno,
    "macos_app_dmg": build_macos_app_and_dmg,
}


def list_targets() -> list[str]:
    return sorted(TARGETS.keys())


def run_build_target(target: str) -> Dict[str, Any]:
    key = str(target).strip().lower()
    fn = TARGETS.get(key)
    if fn is None:
        return {"ok": False, "reason": "unknown_target", "target": key, "available": list_targets()}
    res = fn()
    if is_dataclass(res):
        payload = asdict(res)
    elif isinstance(res, dict):
        payload = dict(res)
    else:
        payload = {
            "ok": bool(getattr(res, "ok", False)),
            "code": int(getattr(res, "code", 1)),
            "cmd": list(getattr(res, "cmd", [])),
            "out": str(getattr(res, "out", "")),
            "err": str(getattr(res, "err", "")),
        }
    payload["target"] = key
    return payload
