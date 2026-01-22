#!/usr/bin/env bash
set -euo pipefail

# Creates a notarytool keychain profile in the current default keychain.
# Typical CI usage:
#   bash packaging/signing/macos_ci_prepare_notary_profile.sh \
#     --profile "NotaryProfile" \
#     --apple-id "$APPLE_ID" \
#     --password "$APP_SPECIFIC_PASSWORD" \
#     --team-id "$TEAM_ID"

PROFILE=""
APPLE_ID=""
PASSWORD=""
TEAM_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2;;
    --apple-id) APPLE_ID="$2"; shift 2;;
    --password) PASSWORD="$2"; shift 2;;
    --team-id) TEAM_ID="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$PROFILE" || -z "$APPLE_ID" || -z "$PASSWORD" || -z "$TEAM_ID" ]]; then
  echo "Missing args."
  exit 2
fi

echo "[macOS] Storing notarytool credentials as keychain profile: $PROFILE"
# notarytool will validate credentials by default
xcrun notarytool store-credentials "$PROFILE" --apple-id "$APPLE_ID" --password "$PASSWORD" --team-id "$TEAM_ID"
echo "[macOS] OK: profile stored."
