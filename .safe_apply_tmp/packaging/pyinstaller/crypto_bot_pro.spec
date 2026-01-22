# NOTE:
# Build ON the target OS. PyInstaller doesn't reliably cross-compile.
# This spec builds a launcher that runs Streamlit.
#
# Build:
#   pyinstaller packaging/pyinstaller/crypto_bot_pro.spec

from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = str(ROOT / "scripts" / "run_desktop.py")

# Collect data from streamlit (often required)
datas, binaries, hiddenimports = [], [], []

# best-effort collections
for pkg in ["streamlit", "altair", "pandas", "numpy"]:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    [ENTRY],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="CryptoBotPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="CryptoBotPro",
)
