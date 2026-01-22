#!/usr/bin/env bash
set -euo pipefail

# Signs the built .app bundle.
# Requires:
#   CODESIGN_IDENTITY (e.g. "Developer ID Application: Your Company (TEAMID)")
#   APP_PATH (default: dist/CryptoBotPro/CryptoBotPro.app)

APP_PATH="${APP_PATH:-dist/CryptoBotPro/CryptoBotPro.app}"
IDENTITY="${CODESIGN_IDENTITY:-}"

if [[ -z "${IDENTITY}" ]]; then
  echo "ERROR: CODESIGN_IDENTITY is required"
  exit 1
fi

if [[ ! -d "${APP_PATH}" ]]; then
  echo "ERROR: App not found at ${APP_PATH}"
  exit 1
fi

echo "[sign] Using identity: ${IDENTITY}"
codesign --force --deep --options runtime --timestamp --sign "${IDENTITY}" "${APP_PATH}"

echo "[sign] Verify:"
codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
echo "[sign] OK"
