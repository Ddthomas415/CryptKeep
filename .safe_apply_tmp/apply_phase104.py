# apply_phase104.py - Phase 104 launcher (PyInstaller packaging + frozen-safe paths)
from pathlib import Path
import re

def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"Written/Updated: {path}")

def patch(path: str, fn):
    p = Path(path)
    if not p.exists():
        print(f"Skipping patch - file missing: {path}")
        return
    t = p.read_text(encoding="utf-8")
    nt = fn(t)
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        print(f"Patched: {path}")
    else:
        print(f"No changes needed: {path}")

# 1) App paths helper (frozen vs dev)
write("services/os/app_paths.py", r'''from __future__ import annotations
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
''')

# 2) Patch modules to use app_paths (replace hardcoded "data"/"runtime")
def patch_daily_limits_sqlite(t: str) -> str:
    if "from services.os.app_paths import data_dir" in t:
        return t
    t = t.replace("from pathlib import Path\n", "from pathlib import Path\nfrom services.os.app_paths import data_dir\n", 1)
    t = t.replace('DB_PATH = Path("data") / "daily_limits.sqlite"', 'DB_PATH = data_dir() / "daily_limits.sqlite"')
    return t

patch("storage/daily_limits_sqlite.py", patch_daily_limits_sqlite)

def patch_evidence_sqlite(t: str) -> str:
    if "from services.os.app_paths import data_dir" in t:
        return t
    t = t.replace("from pathlib import Path\n", "from pathlib import Path\nfrom services.os.app_paths import data_dir\n", 1)
    t = t.replace('DB_PATH = Path("data") / "evidence_signals.sqlite"', 'DB_PATH = data_dir() / "evidence_signals.sqlite"')
    return t

patch("storage/evidence_signals_sqlite.py", patch_evidence_sqlite)

def patch_quarantine_review(t: str) -> str:
    if "from services.os.app_paths import data_dir" in t:
        return t
    t = t.replace("from storage.evidence_signals_sqlite import EvidenceSignalsSQLite\n", "from storage.evidence_signals_sqlite import EvidenceSignalsSQLite\nfrom services.os.app_paths import data_dir\n", 1)
    t = t.replace('db = Path("data") / "evidence_signals.sqlite"', 'db = data_dir() / "evidence_signals.sqlite"')
    return t

patch("services/evidence/quarantine_review.py", patch_quarantine_review)

def patch_pnl_harvester(t: str) -> str:
    if "from services.os.app_paths import state_root" in t:
        return t
    t = t.replace("from pathlib import Path\n", "from pathlib import Path\nfrom services.os.app_paths import state_root\n", 1)
    t = re.sub(
        r"LOCAL_DB_DIRS\s*=\s*\[[^\]]*\]",
        'LOCAL_DB_DIRS = [\n    state_root() / "data",\n    state_root() / "runtime",\n    state_root() / "runtime" / "db",\n    state_root() / "runtime" / "data",\n    Path("data"),\n    Path("runtime"),\n    Path("runtime") / "db",\n    Path("runtime") / "data",\n]',
        t,
        flags=re.S
    )
    return t

patch("services/risk/pnl_harvester.py", patch_pnl_harvester)

def patch_tick_publisher(t: str) -> str:
    if "from services.os.app_paths import runtime_dir, ensure_dirs" in t:
        return t
    t = t.replace("from pathlib import Path\n", "from pathlib import Path\nfrom services.os.app_paths import runtime_dir, ensure_dirs\n", 1)
    t = t.replace('SNAPSHOT_DIR = Path("runtime") / "snapshots"', 'SNAPSHOT_DIR = runtime_dir() / "snapshots"')
    t = t.replace('FLAGS_DIR = Path("runtime") / "flags"', 'FLAGS_DIR = runtime_dir() / "flags"')
    t = t.replace('LOCKS_DIR = Path("runtime") / "locks"', 'LOCKS_DIR = runtime_dir() / "locks"')
    if "ensure_dirs()" not in t:
        t = t.replace("c = _cfg()\n", "ensure_dirs()\n    c = _cfg()\n", 1)
    return t

patch("services/market_data/system_status_publisher.py", patch_tick_publisher)

# 3) Desktop launcher (for frozen app)
write("desktop_launcher.py", r'''from __future__ import annotations
import os
import sys
import webbrowser
from pathlib import Path
from services.os.app_paths import code_root, ensure_dirs

def _app_path() -> str:
    # dashboard/app.py is bundled as data into the frozen app
    return str((code_root() / "dashboard" / "app.py").resolve())

def main():
    ensure_dirs()
    host = os.getenv("CBP_HOST", "127.0.0.1")
    port = os.getenv("CBP_PORT", "8501")
    # Open browser to local URL (best-effort)
    try:
        webbrowser.open(f"http://{host}:{port}", new=1)
    except Exception:
        pass
    # Start Streamlit (bootstrap)
    import streamlit.web.bootstrap as bootstrap
    bootstrap.run(_app_path(), "streamlit run", [], {"server.address": host, "server.port": int(port), "browser.gatherUsageStats": False})

if __name__ == "__main__":
    main()
''')

# 4) PyInstaller spec
write("packaging/crypto_bot_pro.spec", r'''# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata
block_cipher = None

st_datas, st_bins, st_hidden = collect_all("streamlit", include_py_files=False)
metas = []
for pkg in ("streamlit", "altair", "protobuf", "validators", "click"):
    try:
        metas += copy_metadata(pkg)
    except Exception:
        pass

a = Analysis(
    ["desktop_launcher.py"],
    pathex=["."],
    binaries=[] + st_bins,
    datas=[] + st_datas + metas + [
        ("dashboard", "dashboard"),
        ("services", "services"),
        ("storage", "storage"),
        ("scripts", "scripts"),
        ("docs", "docs"),
    ],
    hiddenimports=[] + st_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CryptoBotPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CryptoBotPro",
)
''')

# 5) Build script
write("scripts/build_desktop.py", r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packaging" / "crypto_bot_pro.spec"

def run(cmd: list[str]) -> int:
    print(">", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(ROOT))

def main() -> int:
    ap = argparse.ArgumentParser(description="Build desktop app using PyInstaller (onedir).")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--noconfirm", action="store_true")
    args = ap.parse_args()
    try:
        import PyInstaller
    except Exception:
        print("[info] PyInstaller not found. Installing...")
        rc = run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        if rc != 0:
            return rc
    cmd = [sys.executable, "-m", "PyInstaller", str(SPEC)]
    if args.clean:
        cmd.append("--clean")
    if args.noconfirm:
        cmd.append("--noconfirm")
    rc = run(cmd)
    if rc == 0:
        dist = ROOT / "dist" / "CryptoBotPro"
        print(f"[ok] build complete: {dist}")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
''')

# 6) Patch checkpoints
def patch_checkpoints():
    p = Path("CHECKPOINTS.md")
    if not p.exists():
        print("CHECKPOINTS.md missing - skipping patch")
        return
    t = p.read_text(encoding="utf-8")
    if "## CZ) Desktop App Build (PyInstaller)" in t:
        print("Already patched checkpoints")
        return
    t += (
        "\n## CZ) Desktop App Build (PyInstaller)\n"
        "- ✅ CZ1: desktop_launcher.py starts Streamlit via bootstrap and opens local browser\n"
        "- ✅ CZ2: services/os/app_paths.py routes runtime/data to user-writable dir when frozen\n"
        "- ✅ CZ3: packaging/crypto_bot_pro.spec bundles dashboard + modules + Streamlit data/metadata\n"
        "- ✅ CZ4: scripts/build_desktop.py builds an OS-native distributable folder (dist/CryptoBotPro)\n"
        "- ✅ CZ5: No secrets bundled; keyring/env remains the only secret path\n"
    )
    p.write_text(t, encoding="utf-8")
    print("Patched: CHECKPOINTS.md")

patch_checkpoints()

print("OK: Phase 104 applied (PyInstaller packaging + frozen-safe paths + build script + checkpoints).")
print("Next steps:")
print("  1. Install PyInstaller (if not already): pip install pyinstaller")
print("  2. Build the app: python3 scripts/build_desktop.py")
print("  3. Run the bundled app: dist/CryptoBotPro/CryptoBotPro (or .exe on Windows)")