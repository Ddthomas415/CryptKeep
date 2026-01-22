# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata

import sys
from pathlib import Path
icon_path = None
assets_dir = Path("assets") / "icons"
if sys.platform.startswith("win"):
    p = assets_dir / "app.ico"
    if p.exists():
        icon_path = str(p)
elif sys.platform == "darwin":
    p = assets_dir / "app.icns"
    if p.exists():
        icon_path = str(p)

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
