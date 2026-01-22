# Packaging (Phase 16)

We package the launcher (app_launcher/launcher.py) which starts Streamlit and opens the browser.

Why PyInstaller:
- Common approach for “double-click” local distribution
- Still requires careful handling (Streamlit + multiprocessing + hiddenimports can be finicky). :contentReference[oaicite:4]{index=4}

Build:
- macOS: packaging/pyinstaller/build_macos.sh
- Windows: packaging/pyinstaller/build_windows.ps1

IMPORTANT:
- Build on the target OS. Cross-building is not reliable/typical. :contentReference[oaicite:5]{index=5}

Run output:
- macOS: dist/CryptoBotPro/CryptoBotPro
- Windows: dist\CryptoBotPro\CryptoBotPro.exe
