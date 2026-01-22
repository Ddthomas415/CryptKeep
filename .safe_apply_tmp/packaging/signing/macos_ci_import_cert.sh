#!/usr/bin/env bash
set -euo pipefail

# Imports a base64-encoded .p12 into a temporary keychain and configures access for codesign.
# Usage:
#   bash packaging/signing/macos_ci_import_cert.sh \
#     --p12-base64 "$MAC_CERT_P12_BASE64" \
#     --p12-password "$MAC_CERT_PASSWORD" \
#     --keychain-password "$MAC_KEYCHAIN_PASSWORD"

P12_B64=""
P12_PASS=""
KC_PASS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --p12-base64) P12_B64="$2"; shift 2;;
    --p12-password) P12_PASS="$2"; shift 2;;
    --keychain-password) KC_PASS="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 2;;
  esac
done

if [[ -z "$P12_B64" || -z "$P12_PASS" || -z "$KC_PASS" ]]; then
  echo "Missing args."
  exit 2
fi

KC="build-signing.keychain-db"
P12="cert.p12"

echo "$P12_B64" | base64 --decode > "$P12"

security create-keychain -p "$KC_PASS" "$KC"
security set-keychain-settings -lut 21600 "$KC"
security unlock-keychain -p "$KC_PASS" "$KC"

# Make it the default (so codesign can find identities)
security list-keychains -d user -s "$KC" login.keychain-db
security default-keychain -s "$KC"

# Import cert
security import "$P12" -k "$KC" -P "$P12_PASS" -T /usr/bin/codesign -T /usr/bin/security

# Allow codesign to access the key without prompts
security set-key-partition-list -S apple-tool:,apple: -s -k "$KC_PASS" "$KC"

echo "[macOS] Imported cert into keychain: $KC"
security find-identity -p codesigning -v "$KC" || true
