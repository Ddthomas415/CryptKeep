#!/usr/bin/env bash
set -euo pipefail

# Notarize + staple a file artifact (dmg/pkg/zip) using a stored keychain profile.
# Usage:
#   bash packaging/signing/macos_notarize_file.sh --file dist/MyApp.dmg --profile NotaryProfile

FILE=""
PROFILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file) FILE="$2"; shift 2;;
    --profile) PROFILE="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$FILE" || -z "$PROFILE" ]]; then
  echo "Missing args."
  exit 2
fi

if [[ ! -f "$FILE" ]]; then
  echo "File not found: $FILE"
  exit 2
fi

echo "[macOS] Submitting to Apple notary service: $FILE"
xcrun notarytool submit "$FILE" --keychain-profile "$PROFILE" --wait

echo "[macOS] Stapling ticket..."
xcrun stapler staple "$FILE"

echo "[macOS] Done notarizing+stapling: $FILE"
