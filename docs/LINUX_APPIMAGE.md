# Linux AppImage (Optional)

This repo includes an optional Linux packaging helper:

- `scripts/build_linux_appimage.sh`

It packages an existing PyInstaller onedir bundle (`dist/CryptoBotPro`) into:

- `dist/CryptoBotPro-linux-x86_64.AppImage`

## Prerequisites

1. Build desktop bundle first:
   - `python3 scripts/build_desktop.py`
2. Install `appimagetool` (from AppImageKit) and ensure it is in `PATH`.

## Build

```bash
bash scripts/build_linux_appimage.sh
```

Optional overrides:

- `APP_NAME` (default `CryptoBotPro`)
- `DIST_DIR` (default `dist/CryptoBotPro`)
- `APPDIR` (default `build/CryptoBotPro.AppDir`)
- `OUT_DIR` (default `dist`)

Example:

```bash
APP_NAME=CryptoBotPro DIST_DIR=dist/CryptoBotPro bash scripts/build_linux_appimage.sh
```
