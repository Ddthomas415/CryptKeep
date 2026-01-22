#!/usr/bin/env bash
set -euo pipefail

if ! command -v pbpaste >/dev/null 2>&1; then
  echo "ERROR: pbpaste not found (macOS only)."
  exit 1
fi

echo "Watching clipboard…"
echo "Only prompts when clipboard contains a COMPLETE python3 heredoc patch:"
echo "  python3 - <<'PY'   ...   PY"
echo "Press Ctrl+C to stop."

last_hash=""

hash_clip() {
  python3 - <<'PY'
import hashlib, sys
s = sys.stdin.read().encode("utf-8", "replace")
print(hashlib.sha256(s).hexdigest())
PY
}

is_complete_py_heredoc() {
  local s="$1"
  # must contain heredoc header
  if ! grep -Eq "python3[[:space:]]*-[[:space:]]*<<[[:space:]]*['\\\"]?PY['\\\"]?" <<<"$s"; then
    return 1
  fi
  # must end with a terminator line "PY" (last non-empty line)
  local last_nonempty
  last_nonempty="$(printf "%s" "$s" | awk 'NF{line=$0} END{print line}')"
  if [ "$(printf "%s" "$last_nonempty" | tr -d "\r" | xargs)" != "PY" ]; then
    return 1
  fi
  return 0
}

while true; do
  clip="$(pbpaste || true)"

  if [ "${#clip}" -lt 200 ]; then
    sleep 0.8
    continue
  fi

  if ! is_complete_py_heredoc "$clip"; then
    sleep 0.8
    continue
  fi

  hash="$(printf "%s" "$clip" | hash_clip)"
  if [ "$hash" != "$last_hash" ]; then
    last_hash="$hash"
    echo ""
    echo "Clipboard contains a COMPLETE python3-heredoc patch (len=${#clip}). Apply it? (y/N)"
    read -r ans
    if [[ "${ans:-N}" =~ ^[Yy]$ ]]; then
      printf "%s" "$clip" > patch.txt
      python3 tools/safe_apply.py --patch-file patch.txt --run-pytest --apply --run-docker-tests
      echo "Applied."
    else
      echo "Skipped."
    fi
  fi

  sleep 0.8
done
