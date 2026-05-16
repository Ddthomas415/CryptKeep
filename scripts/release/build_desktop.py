from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import os
import sys
import subprocess
import shutil
from pathlib import Path

def _run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)

def main() -> int:
    # Ensure PyInstaller exists
    try:
        import PyInstaller  # noqa
    except Exception:
        print("PyInstaller not found. Install it: python -m pip install pyinstaller")
        return 2

    spec = Path("packaging/desktop.spec")
    if not spec.exists():
        print("Missing packaging/desktop.spec")
        return 2

    # Clean old builds
    for d in ["build", "dist"]:
        if Path(d).exists():
            shutil.rmtree(d, ignore_errors=True)

    _run([sys.executable, "-m", "PyInstaller", str(spec), "--noconfirm"])

    out = Path("dist") / "CryptoBotProDesktop"
    if not out.exists():
        print("Build did not produce dist/CryptoBotProDesktop")
        return 3

    print("OK:", out)
    print("Next:")
    if sys.platform.startswith("win"):
        print("- run: dist\\CryptoBotProDesktop\\CryptoBotProDesktop.exe")
        print("- installer: use packaging/windows/inno_setup.iss with Inno Setup")
    elif sys.platform == "darwin":
        print("- run: dist/CryptoBotProDesktop/CryptoBotProDesktop")
        print("- wrap into .app/.dmg: see docs/PHASE36_INSTALLERS_MAC_WINDOWS.md")
    else:
        print("- run: dist/CryptoBotProDesktop/CryptoBotProDesktop")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
