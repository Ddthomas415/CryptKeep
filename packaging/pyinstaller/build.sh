#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TARGET_ARCH="${CBP_TARGET_ARCH:-}"
if [ "${TARGET_ARCH}" = "amd64" ]; then
  TARGET_ARCH="x86_64"
fi

X86_BACKUP_PY=""
shopt -s nullglob
x86_candidates=(.venv_x86_backup_*)
shopt -u nullglob
if [ ${#x86_candidates[@]} -gt 0 ]; then
  last_index=$((${#x86_candidates[@]} - 1))
  if [ -x "${x86_candidates[$last_index]}/bin/python" ]; then
    X86_BACKUP_PY="${x86_candidates[$last_index]}/bin/python"
  fi
fi

if [ -n "${PYTHON:-}" ]; then
  PY="${PYTHON}"
elif [ "${TARGET_ARCH}" = "x86_64" ] && [ -n "$X86_BACKUP_PY" ]; then
  PY="$X86_BACKUP_PY"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

if [ -n "$TARGET_ARCH" ] && [ "$TARGET_ARCH" = "x86_64" ] && [ -z "$X86_BACKUP_PY" ] && [ -z "${PYTHON:-}" ]; then
  echo "ERROR: CBP_TARGET_ARCH=x86_64 requires an x86_64 Python environment or PYTHON override."
  exit 2
fi

if [ -z "$TARGET_ARCH" ] && [ "$(uname -s)" = "Darwin" ]; then
  TARGET_ARCH="$("$PY" - <<'PY'
import platform
machine = platform.machine().lower()
print({"amd64": "x86_64"}.get(machine, machine))
PY
)"
fi

if [ -f "requirements/desktop.txt" ]; then
  "$PY" -m pip install -r requirements/desktop.txt
else
  "$PY" -m pip install -r requirements.txt
fi

if [ -n "$TARGET_ARCH" ]; then
  export CBP_TARGET_ARCH="$TARGET_ARCH"
fi
"$PY" packaging/pyinstaller/build.py

echo "Built: dist/CryptoBotPro (set CBP_WINDOWED=1 for a macOS .app build)"
