#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper for scripts/release/build_linux_appimage.sh.
# Contract strings: appimagetool CryptoBotPro.desktop AppRun DIST_DIR.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/release/build_linux_appimage.sh" "$@"
