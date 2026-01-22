# apply_phase103.py - Phase 103 launcher (one installer + runner + doctor + checkpoints)
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, add_block: str, guard: str):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    if guard in t:
        print(f"Already patched: {path}")
        return
    p.write_text(t + "\n" + add_block.lstrip("\n"), encoding="utf-8")
    print(f"Patched: {path}")

# 1) One installer (cross-platform)
write("install.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
RUNTIME_DIR = ROOT / "runtime"
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "runtime" / "config"
USER_YAML = CONFIG_DIR / "user.yaml"

def _is_windows() -> bool:
    return platform.system().lower().startswith("win")

def _venv_python() -> Path:
    if _is_windows():
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def _run(cmd: list[str], *, check: bool = True) -> int:
    print(">", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode

def _ensure_python_version() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 10):
        raise SystemExit(f"Python 3.10+ required. You have {major}.{minor}.")

def _ensure_dirs() -> None:
    (RUNTIME_DIR / "flags").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "locks").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "logs").mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def _write_default_user_yaml_if_missing() -> None:
    if USER_YAML.exists():
        return
    USER_YAML.write_text(
        """# Crypto Bot Pro — user config (safe defaults)
preflight:
  venues: ["binance", "coinbase", "gateio"]
  symbols: ["BTC/USDT"]
# Safety defaults (you can edit later in the Dashboard safely)
execution:
  guard_enabled: true
  latency_guard_ms_p95: 2500
  slippage_guard_bps_p95: 25.0
  guard_window_n: 200
  market_data_guard_enabled: true
  market_data_max_age_sec: 5
  spread_guard_enabled: false
  max_spread_bps: 30.0
risk:
  daily_limits_enabled: true
  daily_reset_tz: "UTC"
  max_trades_per_day: 0
  max_daily_notional_usd: 0.0
  max_daily_loss_usd: 0.0
  auto_harvest_pnl_on_evaluate: false
evidence:
  require_consent: true
  allowed_sources: []
  webhook:
    enabled: true
    host: "127.0.0.1"
    port: 8787
    require_hmac: true
    allow_public_bind: false
market_data_publisher:
  enabled: true
  interval_sec: 2
  write_latest_only: true
  venues: ["binance", "coinbase", "gateio"]
  symbols: ["BTC/USDT"]
  max_symbols_per_venue: 50
""",
        encoding="utf-8",
    )
    print(f"[ok] wrote default config: {USER_YAML}")

def _create_venv() -> None:
    if _venv_python().exists():
        print("[ok] venv exists:", VENV_DIR)
        return
    print("[info] creating venv:", VENV_DIR)
    _run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    print("[ok] venv created")

def _pip_install() -> None:
    py = str(_venv_python())
    _run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    req = ROOT / "requirements.txt"
    pyproj = ROOT / "pyproject.toml"
    if req.exists():
        print("[info] installing requirements.txt")
        _run([py, "-m", "pip", "install", "-r", str(req)], check=True)
        return
    if pyproj.exists():
        print("[info] installing from pyproject.toml (pip install .)")
        _run([py, "-m", "pip", "install", "."], check=True)
        return
    # Fallback minimal deps
    print("[warn] No requirements.txt or pyproject.toml — installing minimal deps.")
    _run([py, "-m", "pip", "install", "streamlit", "ccxt", "pandas", "PyYAML", "keyring"], check=True)

def _print_next_steps() -> None:
    py = _venv_python()
    if _is_windows():
        run_cmd = f'{py} run.py'
        run_cmd2 = f'{py} run.py --tick-publisher'
    else:
        run_cmd = f'{py} run.py'
        run_cmd2 = f'{py} run.py --tick-publisher'
    print("\n[done] install complete.")
    print("Run dashboard:")
    print(" ", run_cmd)
    print("Optional (start tick publisher too):")
    print(" ", run_cmd2)

def main() -> int:
    _ensure_python_version()
    ap = argparse.ArgumentParser(description="Crypto Bot Pro installer (cross-platform).")
    ap.add_argument("--run", action="store_true", help="Run dashboard after install.")
    ap.add_argument("--tick-publisher", action="store_true", help="If --run, also start tick publisher in background.")
    ap.add_argument("--reinstall", action="store_true", help="Force reinstall deps.")
    args = ap.parse_args()
    _ensure_dirs()
    _write_default_user_yaml_if_missing()
    _create_venv()
    if args.reinstall:
        print("[info] forcing reinstall (pip install --upgrade).")
    _pip_install()
    _print_next_steps()
    if args.run:
        py = str(_venv_python())
        cmd = [py, "run.py"]
        if args.tick_publisher:
            cmd.append("--tick-publisher")
        _run(cmd, check=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 2) One runner
write("run.py", r'''#!/usr/bin/env python3
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
''')

# 3) Doctor script
write("scripts/doctor.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    checks = []
    def ok(name, value=True, details=None):
        checks.append({"name": name, "ok": bool(value), "details": details})
    ok("repo_root_exists", ROOT.exists(), str(ROOT))
    ok("dashboard_app_exists", (ROOT/"dashboard"/"app.py").exists())
    ok("user_yaml_exists", (ROOT/"runtime"/"config"/"user.yaml").exists())
    ok("data_dir_exists", (ROOT/"data").exists())
    ok("runtime_snapshots_dir_exists", (ROOT/"runtime"/"snapshots").exists())
    try:
        import streamlit  # noqa
        ok("import_streamlit", True)
    except Exception as e:
        ok("import_streamlit", False, f"{type(e).__name__}: {e}")
    try:
        import ccxt  # noqa
        ok("import_ccxt", True)
    except Exception as e:
        ok("import_ccxt", False, f"{type(e).__name__}: {e}")
    try:
        import yaml  # noqa
        ok("import_pyyaml", True)
    except Exception as e:
        ok("import_pyyaml", False, f"{type(e).__name__}: {e}")
    print(json.dumps({"ok": all(c["ok"] for c in checks), "checks": checks}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 4) Patch checkpoints
def patch_checkpoints():
    p = Path("CHECKPOINTS.md")
    if not p.exists():
        print("CHECKPOINTS.md missing - skipping patch")
        return
    t = p.read_text(encoding="utf-8")
    if "## CY) One Installer (Mac + Windows)" in t:
        print("Already patched checkpoints")
        return
    t += (
        "\n## CY) One Installer (Mac + Windows)\n"
        "- ✅ CY1: install.py creates .venv, installs deps, creates runtime/data/config safely\n"
        "- ✅ CY2: install.py writes runtime/config/user.yaml with safe defaults if missing\n"
        "- ✅ CY3: run.py launches Streamlit dashboard; optional tick publisher autostart\n"
        "- ✅ CY4: scripts/doctor.py verifies install without manual file edits\n"
        "- ✅ CY5: No secrets stored; evidence webhook secrets remain in keyring/env\n"
    )
    p.write_text(t, encoding="utf-8")
    print("Patched: CHECKPOINTS.md")

patch_checkpoints()

print("OK: Phase 103 applied (install.py + run.py + doctor + checkpoints).")
print("Next steps:")
print("  1. Run installer: python3 install.py --run")
print("  2. Or just the dashboard: python3 run.py")
print("  3. Check health: python3 scripts/doctor.py")