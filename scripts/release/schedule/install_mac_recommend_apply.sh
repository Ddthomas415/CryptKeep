#!/usr/bin/env bash
set -euo pipefail

# Runs (safe):
# 1) recommend (writes data/learning/recommended_model.json)
# 2) apply pending switch ONLY if explicit approval file exists (and matches)
#
# Installs LaunchAgent at: ~/Library/LaunchAgents/com.cryptobotpro.recommend_apply.plist

INTERVAL_SECONDS="${1:-1800}"  # default 30 min
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.cryptobotpro.recommend_apply.plist"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$REPO_ROOT/data/logs"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.cryptobotpro.recommend_apply</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>bash</string>
    <string>-lc</string>
    <string>cd "$REPO_ROOT" && python3 scripts/recommend_model_switch.py && python3 scripts/apply_pending_model_switch.py</string>
  </array>
  <key>StartInterval</key><integer>${INTERVAL_SECONDS}</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>${REPO_ROOT}/data/logs/recommend_apply.out.log</string>
  <key>StandardErrorPath</key><string>${REPO_ROOT}/data/logs/recommend_apply.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "OK: Installed macOS recommend+apply LaunchAgent (approval required to actually switch)."
echo "Plist: $PLIST"
echo "Interval seconds: ${INTERVAL_SECONDS}"
