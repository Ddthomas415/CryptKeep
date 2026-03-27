#!/usr/bin/env python3
"""
Crypto Bot Pro — installer (clean, idempotent)

- Ensures .venv exists
- Installs root baseline dependencies from requirements.txt
- Does NOT write secrets
- Supports the root repo Python platform only
"""
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
import venv

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"

def _run(cmd: list[str], *, env=None) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, env=env)

def _venv_python() -> Path:
    if platform.system().lower().startswith("win"):
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def ensure_venv() -> Path:
    if not VENV_DIR.exists():
        print(f"[install] creating venv at {VENV_DIR}")
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))
    py = _venv_python()
    if not py.exists():
        raise RuntimeError(f"venv python missing: {py}")
    return py

def main() -> int:
    # warn about very-new python if needed
    try:
        import sys as _sys
        if _sys.version_info >= (3, 13):
            print("[warn] You are using Python 3.13. If packaging/PyInstaller gets weird later, switch to 3.11.")
    except Exception:
        pass

    py = ensure_venv()
    _run([str(py), "-m", "pip", "install", "-U", "pip"])

    req = ROOT / "requirements.txt"

    if req.exists():
        _run([str(py), "-m", "pip", "install", "-r", str(req)])
    else:
        print("[install] requirements.txt is required for the root baseline install path.")
        return 2

    print("\n[ok] install complete.")
    print("[note] This installer provisions the root repo Python platform only.")
    print("[note] requirements.txt is the dependency source of truth for this baseline.")
    print("[note] Sidecar workspaces such as crypto-trading-ai/, src-tauri/, and packaging flows are not part of this baseline install path.")
    if platform.system().lower().startswith("win"):
        print(r"Activate: .\.venv\Scripts\activate")
    else:
        print("Activate: source .venv/bin/activate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
