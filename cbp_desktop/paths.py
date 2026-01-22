from __future__ import annotations

import os
import sys
from pathlib import Path

from platformdirs import PlatformDirs

APPNAME = "CryptoBotPro"
APPAUTHOR = "CryptoBotPro"


def app_root() -> Path:
    # dev: repo root; PyInstaller: sys._MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def runtime_root() -> Path:
    override = (os.environ.get("CBP_RUNTIME_ROOT") or "").strip()
    if override:
        p = Path(override).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    d = PlatformDirs(APPNAME, APPAUTHOR, ensure_exists=True)
    p = Path(d.user_data_dir) / "runtime"
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_runtime_layout() -> None:
    rr = runtime_root()
    (rr / "data").mkdir(parents=True, exist_ok=True)
    (rr / "logs").mkdir(parents=True, exist_ok=True)
