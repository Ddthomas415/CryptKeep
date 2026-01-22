# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

block_cipher = None

# Include project folders needed at runtime
datas = [
    (str(ROOT / "dashboard"), "dashboard"),
    (str(ROOT / "services"), "services"),
    (str(ROOT / "storage"), "storage"),
    (str(ROOT / "scripts"), "scripts"),
    (str(ROOT / "docs"), "docs"),
    (str(ROOT / "config"), "config"),
]

# Optional: include user_config.yaml if present (generated after install.py)
uc = ROOT / "user_config.yaml"
if uc.exists():
    datas.append((str(uc), "."))

a = Analysis(
    [str(ROOT / "app_entry.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Console=True is safer for diagnostics; you can flip to False later
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="CryptoBotPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)

# For macOS .app, PyInstaller will create an app bundle when building on macOS.
