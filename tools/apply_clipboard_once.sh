#!/usr/bin/env bash
set -euo pipefail

clip="$(pbpaste || true)"

if ! grep -q "python3 - <<'PY'" <<<"$clip"; then
  echo "Clipboard does not contain a python heredoc patch."
  exit 1
fi

printf "%s" "$clip" > patch.txt
python3 tools/safe_apply.py --patch-file patch.txt
