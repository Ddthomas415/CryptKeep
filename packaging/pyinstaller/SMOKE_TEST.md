# Smoke Test Checklist (PyInstaller)

Goal: verify the packaged app runs without Python installed.

## Common expectations
- App starts by double-click.
- Dashboard opens at http://127.0.0.1:8501
- Runtime folder is created in the OS user data dir and shown on the dashboard.
- Logs appear in <runtime>/logs/

## macOS
1) Build using packaging/pyinstaller/README.md
2) Run: dist/CryptoBotPro.app
3) Verify:
   - runtime folder created
   - dashboard loads
   - start/stop "collector" works
4) If it fails:
   - run from Terminal to capture logs:
     open -a "CryptoBotPro" --args --no-browser

## Windows
1) Build using packaging/pyinstaller/README.md
2) Run: dist/CryptoBotPro.exe
3) Verify:
   - runtime folder created
   - dashboard loads
   - start/stop "collector" works
4) If it fails:
   - build a console variant (remove --noconsole) to see stdout
