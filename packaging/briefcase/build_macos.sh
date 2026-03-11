#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
source ".venv/bin/activate"
briefcase create macOS
briefcase build macOS
briefcase package macOS
echo "Done. Check build/cryptobotpro/macos/ (or briefcase output paths)."
