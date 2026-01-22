#!/usr/bin/env bash
set -euo pipefail

# Runs: python3 scripts/monitor_and_maybe_rollback.py every 5 minutes (default)
# Installs LaunchAgent at: ~/Library/LaunchAgents/com.cryptobotpro.monitor.plist

INTERVAL_SECONDS="${1:-300}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.cryptobotpro.monitor.plist"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.cryptobotpro.monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>bash</string>
    <string>-lc</string>
    <string>cd "$REPO_ROOT" && python3 scripts/monitor_and_maybe_rollback.py</string>
  </array>
  <key>StartInterval</key><integer>${INTERVAL_SECONDS}</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>${REPO_ROOT}/data/logs/monitor.out.log</string>
  <key>StandardErrorPath</key><string>${REPO_ROOT}/data/logs/monitor.err.log</string>
</dict>
</plist>
EOF

mkdir -p "$REPO_ROOT/data/logs"

# (Re)load agent
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"

echo "OK: Installed macOS monitor LaunchAgent."
echo "Plist: $PLIST"
echo "Interval seconds: ${INTERVAL_SECONDS}"
