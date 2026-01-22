# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

project_root = os.path.abspath(os.getcwd())

# include our code + configs + docs needed at runtime
datas = []
for folder in ["dashboard", "services", "storage", "scripts", "config", "docs"]:
    p = os.path.join(project_root, folder)
    if os.path.isdir(p):
        datas.append((p, folder))

# streamlit + friends hidden imports
streamlit_datas, streamlit_binaries, streamlit_hidden = collect_all('streamlit')
ccxt_datas, ccxt_binaries, ccxt_hidden = collect_all('ccxt')

datas += streamlit_datas + ccxt_datas
binaries = streamlit_binaries + ccxt_binaries
hiddenimports = list(set(streamlit_hidden + ccxt_hidden))

block_cipher = None

a = Analysis(
    ['packaging/desktop_launcher.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CryptoBotProDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='CryptoBotProDesktop',
)
