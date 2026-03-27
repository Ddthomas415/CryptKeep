from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_CONFIG = ROOT / "packaging" / "config" / "app.json"


def run(cmd: list[str]) -> int:
    print(">", " ".join(cmd))
    return subprocess.call(cmd)  # noqa: S603


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _target_arch() -> str | None:
    if sys.platform != "darwin":
        return None

    raw = os.environ.get("CBP_TARGET_ARCH", "").strip().lower()
    if not raw:
        return {"amd64": "x86_64"}.get(platform.machine().lower(), platform.machine().lower())

    target = {"amd64": "x86_64"}.get(raw, raw)
    if target not in {"x86_64", "arm64", "universal2"}:
        raise ValueError(f"Unsupported CBP_TARGET_ARCH={raw!r}; expected arm64, x86_64, or universal2.")

    return target


def _load_cfg() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "name": "CryptoBotPro",
        "version": "0.1.0",
        "entry": "scripts/run_desktop.py",
        "windowed_default": False,
        "icons": {},
        "pyinstaller": {
            "hidden_imports": ["streamlit", "ccxt", "yaml"],
            "data_dirs": ["dashboard", "services", "storage", "docs", "config", "scripts"],
        },
    }
    if not APP_CONFIG.exists():
        return defaults
    try:
        loaded = json.loads(APP_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return defaults
    if not isinstance(loaded, dict):
        return defaults
    out = defaults.copy()
    out.update(loaded)
    if isinstance(defaults.get("icons"), dict) and isinstance(loaded.get("icons"), dict):
        merged_icons = dict(defaults["icons"])
        merged_icons.update(loaded["icons"])
        out["icons"] = merged_icons
    if isinstance(defaults.get("pyinstaller"), dict) and isinstance(loaded.get("pyinstaller"), dict):
        merged_pyi = dict(defaults["pyinstaller"])
        merged_pyi.update(loaded["pyinstaller"])
        out["pyinstaller"] = merged_pyi
    return out


def _looks_real_icon(p: Path) -> bool:
    try:
        return p.exists() and p.is_file() and p.stat().st_size > 1000
    except Exception:
        return False


def _resolve_entry(cfg: dict[str, Any]) -> Path:
    entry = ROOT / str(cfg.get("entry", "scripts/run_desktop.py"))
    if entry.exists():
        return entry
    fallback = ROOT / "scripts" / "run_desktop.py"
    return fallback


def _add_data_args(cmd: list[str], pyi_cfg: dict[str, Any]) -> None:
    data_dirs = pyi_cfg.get("data_dirs", ["dashboard", "services", "storage", "docs", "config", "scripts"])
    if not isinstance(data_dirs, list):
        data_dirs = ["dashboard", "services", "storage", "docs", "config", "scripts"]
    for rel in data_dirs:
        src = ROOT / str(rel)
        if src.exists():
            cmd += ["--add-data", f"{src}{os.pathsep}{rel}"]


def main() -> int:
    os.chdir(str(ROOT))

    try:
        import PyInstaller  # noqa: F401
    except Exception:
        print("PyInstaller not installed. Run: pip install -r requirements/desktop.txt")
        return 2

    cfg = _load_cfg()
    name = str(cfg.get("name", "CryptoBotPro"))
    entry = _resolve_entry(cfg)
    version = str(cfg.get("version", "0.1.0"))
    icons = cfg.get("icons", {}) if isinstance(cfg.get("icons"), dict) else {}
    pyi = cfg.get("pyinstaller", {}) if isinstance(cfg.get("pyinstaller"), dict) else {}
    try:
        target_arch = _target_arch()
    except ValueError as exc:
        print(str(exc))
        return 4

    if not entry.exists():
        print(f"Missing entry: {entry}")
        return 3

    windowed = bool(cfg.get("windowed_default", False))
    if _truthy("CBP_WINDOWED"):
        windowed = True
    if _truthy("CBP_CONSOLE"):
        windowed = False

    for p in [DIST, BUILD, ROOT / f"{name}.spec"]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()

    hidden = pyi.get("hidden_imports", ["streamlit", "ccxt", "yaml"])
    if not isinstance(hidden, list):
        hidden = ["streamlit", "ccxt", "yaml"]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        name,
        "--onedir",
        "--noconfirm",
        "--clean",
        "--windowed" if windowed else "--console",
    ]
    if target_arch:
        cmd += ["--target-arch", target_arch]
    _add_data_args(cmd, pyi)

    if os.name == "nt":
        ico = ROOT / str(icons.get("windows_ico", ""))
        if _looks_real_icon(ico):
            cmd += ["--icon", str(ico)]
        ver = ROOT / "packaging" / "windows" / "version_info.txt"
        if ver.exists():
            cmd += ["--version-file", str(ver)]
    elif sys.platform == "darwin":
        icns = ROOT / str(icons.get("mac_icns", ""))
        if _looks_real_icon(icns):
            cmd += ["--icon", str(icns)]

    for h in hidden:
        cmd += ["--hidden-import", str(h)]
    cmd += [str(entry)]

    rc = run(cmd)
    if rc != 0:
        print("Build failed.")
        return int(rc)

    app_bundle = DIST / f"{name}.app"
    out = app_bundle if windowed and app_bundle.exists() else DIST / name
    print("\nOK: Build complete.")
    print(f"Version: {version}")
    print(f"Output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
