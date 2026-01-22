from __future__ import annotations
import os
import platform
import sys
from pathlib import Path

APP_NAME = "CryptoBotPro"

def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")

def code_root() -> Path:
    """
    Path to bundled code root (PyInstaller _MEIPASS) or repo root (dev).
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    # repo root: services/os/app_paths.py -> services/os -> services -> repo
    return Path(__file__).resolve().parents[2]

def user_data_root() -> Path:
    """
    Cross-platform per-user writable data directory.
    Windows: %APPDATA%/CryptoBotPro
    macOS: ~/Library/Application Support/CryptoBotPro
    Linux: ~/.local/share/CryptoBotPro
    """
    override = os.getenv("CBP_STATE_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    home = Path.home()
    sysname = platform.system().lower()
    if sysname.startswith("win"):
        base = os.getenv("APPDATA", str(home / "AppData" / "Roaming"))
        return Path(base) / APP_NAME
    if sysname == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    # linux + others
    xdg = os.getenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    return Path(xdg) / APP_NAME

def state_root() -> Path:
    """
    Where runtime/data/config live.
    - Dev: repo root (keeps existing behavior)
    - Frozen: user_data_root()
    """
    if is_frozen():
        return user_data_root()
    return code_root()

def runtime_dir() -> Path:
    return state_root() / "runtime"

def data_dir() -> Path:
    return state_root() / "data"

def config_dir() -> Path:
    return runtime_dir() / "config"

def ensure_dirs() -> None:
    (runtime_dir() / "flags").mkdir(parents=True, exist_ok=True)
    (runtime_dir() / "locks").mkdir(parents=True, exist_ok=True)
    (runtime_dir() / "snapshots").mkdir(parents=True, exist_ok=True)
    (runtime_dir() / "logs").mkdir(parents=True, exist_ok=True)
    data_dir().mkdir(parents=True, exist_ok=True)
    config_dir().mkdir(parents=True, exist_ok=True)
