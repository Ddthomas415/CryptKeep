#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="${APP_NAME:-CryptoBotPro}"
DIST_DIR="${DIST_DIR:-$ROOT/dist/$APP_NAME}"
APPDIR="${APPDIR:-$ROOT/build/${APP_NAME}.AppDir}"
OUT_DIR="${OUT_DIR:-$ROOT/dist}"
DESKTOP_FILE="$ROOT/packaging/appimage/CryptoBotPro.desktop"
ICON_CANDIDATES=(
  "$ROOT/assets/icons/app.png"
  "$ROOT/packaging/assets/icon.png"
)

echo "[appimage] ROOT=$ROOT"
echo "[appimage] DIST_DIR=$DIST_DIR"
echo "[appimage] APPDIR=$APPDIR"

if [[ ! -d "$DIST_DIR" ]]; then
  echo "[appimage] dist payload not found: $DIST_DIR" >&2
  echo "[appimage] build desktop bundle first (example: python3 scripts/build_desktop.py)." >&2
  exit 2
fi

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "[appimage] appimagetool not found in PATH." >&2
  echo "[appimage] install AppImageKit (https://github.com/AppImage/AppImageKit) and retry." >&2
  exit 2
fi

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$DESKTOP_FILE" "$APPDIR/$APP_NAME.desktop"
cp "$DESKTOP_FILE" "$APPDIR/usr/share/applications/$APP_NAME.desktop"

icon_path=""
for c in "${ICON_CANDIDATES[@]}"; do
  if [[ -f "$c" ]]; then
    icon_path="$c"
    break
  fi
done

if [[ -n "$icon_path" ]]; then
  cp "$icon_path" "$APPDIR/$APP_NAME.png"
  cp "$icon_path" "$APPDIR/usr/share/icons/hicolor/256x256/apps/cryptobotpro.png"
else
  echo "[appimage] warning: no icon found; AppImage will use default icon."
fi

cp -R "$DIST_DIR" "$APPDIR/usr/bin/$APP_NAME"

cat >"$APPDIR/usr/bin/cryptobotpro" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BUNDLE="$HERE/CryptoBotPro"
if [[ -x "$BUNDLE/CryptoBotPro" ]]; then
  exec "$BUNDLE/CryptoBotPro" "$@"
fi

# Fallback: first executable in bundle root.
bin="$(find "$BUNDLE" -maxdepth 1 -type f -perm -111 | head -n 1 || true)"
if [[ -n "$bin" ]]; then
  exec "$bin" "$@"
fi

echo "No executable found inside $BUNDLE" >&2
exit 2
SH
chmod +x "$APPDIR/usr/bin/cryptobotpro"

cat >"$APPDIR/AppRun" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/cryptobotpro" "$@"
SH
chmod +x "$APPDIR/AppRun"

mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/${APP_NAME}-linux-x86_64.AppImage"
appimagetool "$APPDIR" "$OUT_FILE"
chmod +x "$OUT_FILE"
echo "[appimage] wrote: $OUT_FILE"
