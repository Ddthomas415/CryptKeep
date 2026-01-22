#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# 1) Build PyInstaller output (also produces .app on macOS when --windowed is used)
bash scripts/build_macos.sh

APP_PATH="dist/CryptoBotPro/CryptoBotPro.app"
OUT_DIR="dist_installers"
DMG_PATH="${OUT_DIR}/CryptoBotPro.dmg"

mkdir -p "${OUT_DIR}"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "ERROR: .app not found at ${APP_PATH}"
  echo "PyInstaller should create .app on macOS with --windowed."
  exit 1
fi

# 2) Create DMG
if command -v create-dmg >/dev/null 2>&1; then
  # create-dmg tool
  create-dmg \
    --volname "CryptoBotPro" \
    --app-drop-link 450 185 \
    "${DMG_PATH}" \
    "${APP_PATH}"
  echo "DMG built at ${DMG_PATH}"
else
  # Fallback: simple DMG via hdiutil (no fancy layout)
  TMP_DIR="$(mktemp -d)"
  cp -R "${APP_PATH}" "${TMP_DIR}/"
  hdiutil create -volname "CryptoBotPro" -srcfolder "${TMP_DIR}" -ov -format UDZO "${DMG_PATH}"
  rm -rf "${TMP_DIR}"
  echo "DMG built (basic) at ${DMG_PATH}"

# OPTIONAL_SIGN_NOTARY_v1
# Optional signing/notarization (CI sets secrets; local users can set env vars)
if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
  echo "[optional] Signing .app..."
  CODESIGN_IDENTITY="${CODESIGN_IDENTITY}" APP_PATH="${APP_PATH}" bash scripts/macos_codesign_app.sh
fi

if [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "${APPLE_APP_PASSWORD:-}" ]]; then
  echo "[optional] Notarizing DMG..."
  APPLE_ID="${APPLE_ID}" APPLE_TEAM_ID="${APPLE_TEAM_ID}" APPLE_APP_PASSWORD="${APPLE_APP_PASSWORD}" DMG_PATH="${DMG_PATH}" APP_PATH="${APP_PATH}" bash scripts/macos_notarize_dmg.sh
fi

  echo "Tip: install create-dmg for nicer DMG layout."
fi
