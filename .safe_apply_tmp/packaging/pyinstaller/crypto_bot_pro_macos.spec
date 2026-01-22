# macOS-focused PyInstaller spec that produces a .app bundle using BUNDLE.
# Build on macOS.

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in ["streamlit", "altair", "pandas", "numpy", "ccxt", "yaml"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

datas += [
  ("dashboard", "dashboard"),
  ("services", "services"),
  ("storage", "storage"),
  ("config", "config"),
  ("docs", "docs"),
  ("scripts", "scripts"),
]

a = Analysis(
    ["app_launcher/launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    a.zipfiles,
    a.resources,
    name="CryptoBotPro",
    console=True,
)

app = BUNDLE(
    exe,
    name="CryptoBotPro.app",
    bundle_identifier="com.cryptobotpro.app",
)
