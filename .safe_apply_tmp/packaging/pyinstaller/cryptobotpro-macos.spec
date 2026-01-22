# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
ROOT = Path(__file__).resolve().parents[2]

datas = [
    (str(ROOT / "dashboard"), "dashboard"),
    (str(ROOT / "services"), "services"),
    (str(ROOT / "docs"), "docs"),
    (str(ROOT / "config"), "config"),
    (str(ROOT / "data"), "data"),
]

a = Analysis(
    [str(ROOT / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# windowed build -> .app bundle on macOS
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CryptoBotPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CryptoBotPro",
)

app = BUNDLE(
    coll,
    name="CryptoBotPro.app",
    icon=None,
    bundle_identifier=None,
)
