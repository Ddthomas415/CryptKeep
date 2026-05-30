#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper for scripts/release/build_desktop_mac.sh.
# Uses requirements/desktop.txt in the release wrapper.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/release/build_desktop_mac.sh" "$@"
