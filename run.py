#!/usr/bin/env python3
from __future__ import annotations
import argparse
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def _is_windows() -> bool:
    return platform.system().lower().startswith("win")

def _run(cmd: list[str], *, check: bool = True) -> int:
    print(">", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode

def _start_tick_publisher_detached() -> None:
    cmd = [sys.executable, "scripts/run_tick_publisher.py", "run"]
    try:
        if _is_windows():
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(cmd, cwd=str(ROOT), creationflags=DETACHED_PROCESS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(cmd, cwd=str(ROOT), start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[ok] tick publisher started (background)")
    except Exception as e:
        print(f"[warn] could not start tick publisher: {type(e).__name__}: {e}")

def main() -> int:
    ap = argparse.ArgumentParser(description="Run Crypto Bot Pro dashboard.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", default="8501")
    ap.add_argument("--tick-publisher", action="store_true", help="Start tick publisher in background before launching dashboard.")
    args = ap.parse_args()
    if args.tick_publisher:
        _start_tick_publisher_detached()
    app = ROOT / "dashboard" / "app.py"
    if not app.exists():
        raise SystemExit("Missing dashboard/app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app),
        "--server.address", str(args.host),
        "--server.port", str(args.port),
    ]
    return _run(cmd, check=True)

if __name__ == "__main__":
    raise SystemExit(main())
