#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="${ROOT_DIR}/.githooks"
GIT_TOPLEVEL="$(git -C "${ROOT_DIR}" rev-parse --show-toplevel)"
HOOKS_RELATIVE_TO_GIT_TOPLEVEL="$(python3 - <<'PY' "${GIT_TOPLEVEL}" "${HOOKS_DIR}"
import os
import sys

git_root = os.path.realpath(sys.argv[1])
hooks_dir = os.path.realpath(sys.argv[2])
print(os.path.relpath(hooks_dir, git_root))
PY
)"

if [[ ! -d "${HOOKS_DIR}" ]]; then
  echo "Missing hooks directory: ${HOOKS_DIR}" >&2
  exit 1
fi

chmod +x "${HOOKS_DIR}/"*

git -C "${GIT_TOPLEVEL}" config core.hooksPath "${HOOKS_RELATIVE_TO_GIT_TOPLEVEL}"
echo "Installed git hooks path: ${HOOKS_RELATIVE_TO_GIT_TOPLEVEL}"
