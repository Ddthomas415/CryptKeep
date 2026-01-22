#!/usr/bin/env bash
set -euo pipefail

# Codesign all .app bundles found under dist/ and build/ (bounded depth) with hardened runtime + timestamp.
# Usage:
#   bash packaging/signing/macos_ci_codesign_apps.sh --identity "$MAC_SIGN_IDENTITY"

IDENTITY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --identity) IDENTITY="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$IDENTITY" ]]; then
  echo "Missing --identity"
  exit 2
fi

echo "[macOS] Searching for .app bundles..."
APPS=$( (ls dist/*.app 2>/dev/null || true) ; (find build -maxdepth 7 -name "*.app" -type d 2>/dev/null || true) )
if [[ -z "${APPS}" ]]; then
  echo "No .app bundles found to codesign."
  exit 2
fi

for app in $APPS; do
  echo "[macOS] codesign: $app"
  codesign --force --options runtime --timestamp --deep --sign "$IDENTITY" "$app"
  codesign --verify --deep --strict --verbose=2 "$app"
done

echo "[macOS] Done codesigning apps."
