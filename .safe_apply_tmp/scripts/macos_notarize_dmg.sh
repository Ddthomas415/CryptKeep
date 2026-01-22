#!/usr/bin/env bash
set -euo pipefail

# Notarize and staple a DMG (recommended for distribution).
# Requires Apple credentials via:
#   APPLE_ID, APPLE_TEAM_ID, APPLE_APP_PASSWORD
#
# Output:
#   staples the DMG (and can staple the .app if you pass APP_PATH too)

DMG_PATH="${DMG_PATH:-dist_installers/CryptoBotPro.dmg}"
APP_PATH="${APP_PATH:-dist/CryptoBotPro/CryptoBotPro.app}"

APPLE_ID="${APPLE_ID:-}"
APPLE_TEAM_ID="${APPLE_TEAM_ID:-}"
APPLE_APP_PASSWORD="${APPLE_APP_PASSWORD:-}"

if [[ -z "${APPLE_ID}" || -z "${APPLE_TEAM_ID}" || -z "${APPLE_APP_PASSWORD}" ]]; then
  echo "ERROR: APPLE_ID, APPLE_TEAM_ID, APPLE_APP_PASSWORD are required"
  exit 1
fi

if [[ ! -f "${DMG_PATH}" ]]; then
  echo "ERROR: DMG not found at ${DMG_PATH}"
  exit 1
fi

echo "[notary] Submitting DMG..."
xcrun notarytool submit "${DMG_PATH}" \
  --apple-id "${APPLE_ID}" \
  --team-id "${APPLE_TEAM_ID}" \
  --password "${APPLE_APP_PASSWORD}" \
  --wait

echo "[notary] Stapling DMG..."
xcrun stapler staple "${DMG_PATH}"

# Optional: staple the app too (helpful if you distribute the .app directly)
if [[ -d "${APP_PATH}" ]]; then
  echo "[notary] Stapling APP..."
  xcrun stapler staple "${APP_PATH}" || true
fi

echo "[notary] Validate:"
xcrun stapler validate "${DMG_PATH}" || true
echo "[notary] OK"
