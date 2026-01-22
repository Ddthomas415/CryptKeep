from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_CONFIG = ROOT / "packaging" / "config" / "app.json"

def run(cmd: list[str]) -> int:
    print(">", " ".join(cmd))
    return subprocess.call(cmd)  # noqa: S603

def _load_cfg() -> dict:
    if APP_CONFIG.exists():
        try:
            return json.loads(APP_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"name": "CryptoBotPro", "version": "0.1.0", "entry": "desktop/run_desktop.py", "windowed_default": False, "icons": {}, "pyinstaller": {}}

def _looks_real_icon(p: Path) -> bool:
    try:
        return p.exists() and p.is_file() and p.stat().st_size > 1000
    except Exception:
        return False

def main() -> int:
    os.chdir(str(ROOT))

    try:
        import PyInstaller  # noqa: F401
    except Exception:
        print("PyInstaller not installed. Run: pip install -r requirements-dev.txt")
        return 2

    cfg = _load_cfg()
    name = str(cfg.get("name", "CryptoBotPro"))
    entry = ROOT / str(cfg.get("entry", "desktop/run_desktop.py"))
    version = str(cfg.get("version", "0.1.0"))
    icons = cfg.get("icons", {}) if isinstance(cfg.get("icons"), dict) else {}
    pyi = cfg.get("pyinstaller", {}) if isinstance(cfg.get("pyinstaller"), dict) else {}

    if not entry.exists():
        print(f"Missing entry: {entry}")
        return 3

    windowed = bool(cfg.get("windowed_default", False))
    if os.environ.get("CBP_WINDOWED", "").strip().lower() in ("1", "true", "yes", "on"):
        windowed = True
    if os.environ.get("CBP_CONSOLE", "").strip().lower() in ("1", "true", "yes", "on"):
        windowed = False

    # Clean outputs
    for p in [DIST, BUILD, ROOT / f"{name}.spec"]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()

    hidden = pyi.get("hidden_imports", ["streamlit", "ccxt"])
    if not isinstance(hidden, list):
        hidden = ["streamlit", "ccxt"]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", name,
        "--onedir",
        "--noconfirm",
        "--clean",
        "--windowed" if windowed else "--console",
        "--add-data", f"dashboard{os.pathsep}dashboard",
        "--add-data", f"services{os.pathsep}services",
        "--add-data", f"docs{os.pathsep}docs",
        "--add-data", f"config{os.pathsep}config",
        "--add-data", f"scripts{os.pathsep}scripts",
    ]

    # Optional icons
    if os.name == "nt":
        ico = ROOT / str(icons.get("windows_ico", ""))
        if _looks_real_icon(ico):
            cmd += ["--icon", str(ico)]
        ver = ROOT / "packaging" / "windows" / "version_info.txt"
        if ver.exists():
            cmd += ["--version-file", str(ver)]
    else:
        # macOS icon option (only if real icns exists)
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

    out = DIST / name
    print("\nOK: Build complete.")
    print(f"Version: {version}")
    print(f"Output folder: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
