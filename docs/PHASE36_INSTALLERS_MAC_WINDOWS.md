# Phase 36 — Installable Desktop App (macOS + Windows) using PyInstaller

Why this approach:
- Streamlit runs a local server. A lightweight launcher can manage lifecycle (start/stop) and open the UI.
- PyInstaller can bundle Python + deps into an executable, but **must be built on each OS**. (Win build on Win, mac build on mac.)

## 1) Test locally (dev)
- python scripts/run_desktop_launcher.py

## 2) Build (per OS)
- python -m pip install pyinstaller
- python scripts/build_desktop.py

Outputs:
- dist/CryptoBotProDesktop/...

## 3) Windows installer (recommended)
Use Inno Setup:
- Open packaging/windows/inno_setup.iss
- Compile → produces an installer EXE

## 4) macOS distribution
You can ship the PyInstaller output as-is, or wrap into an .app + .dmg.
A simple dmg can be created with `hdiutil` (manual step) once you have a folder you want to distribute.

## Security / Keys
Installers should **not** bundle secrets. Use environment variables or an OS key store.
(Current live keys are read from env vars; a later phase can add keyring-based storage.)

## Non-goals
This phase does not change trading logic. It only adds packaging + a launcher.
