# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hiddenimports = []
hiddenimports += collect_submodules('streamlit')

datas = []
datas += collect_data_files('dashboard')
datas += collect_data_files('config')
datas += collect_data_files('docs')

a = Analysis(
    ['apps/desktop_launcher.py'],
    pathex=[os.getcwd()],
    binaries=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CryptoBotPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,   # no console
)
