#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$(python3 scripts/get_version.py)"
NAME="CryptoBotPro"
DIST_DIR="dist"

# Expect PyInstaller output at: dist/CryptoBotPro (folder) OR dist/CryptoBotPro.app
# We'll support both:
APP_PATH_APP="$DIST_DIR/$NAME.app"
APP_PATH_DIR="$DIST_DIR/$NAME"

python3 -m venv .venv_pack
source .venv_pack/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements/requirements.packaging.txt
python -m pip install dmgbuild

# Build if not already built
if [ ! -d "$APP_PATH_APP" ] && [ ! -d "$APP_PATH_DIR" ]; then
  CBP_WINDOWED=1 python packaging/pyinstaller/build.py
fi

# If PyInstaller built a folder, we still can DMG it as a folder;
# best user experience is a .app bundle; keep folder DMG for now.
SRC=""
if [ -d "$APP_PATH_APP" ]; then SRC="$APP_PATH_APP"; fi
if [ -z "$SRC" ] && [ -d "$APP_PATH_DIR" ]; then
  echo "WARN: No .app bundle found; DMG will include the dist/$NAME folder."
  SRC="$APP_PATH_DIR"
fi
if [ -z "$SRC" ]; then
  echo "ERROR: no app payload found under dist/"
  exit 1
fi

# Prepare staging
STAGE="packaging/_stage_dmg"
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$SRC" "$STAGE/"

# Build DMG
OUT="release/${NAME}-${VERSION}-macOS.dmg"
mkdir -p release

# dmgbuild requires macOS (uses hdiutil underneath)
dmgbuild -s packaging/dmg/dmgbuild_settings.py "${NAME} ${VERSION}" "$OUT" -D "app=${STAGE}/$(basename "$SRC")"

echo "DONE: $OUT"
