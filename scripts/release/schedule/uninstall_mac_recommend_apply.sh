#!/usr/bin/env bash
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.cryptobotpro.recommend_apply.plist"
if [ -f "$PLIST" ]; then
  launchctl unload "$PLIST" >/dev/null 2>&1 || true
  rm -f "$PLIST"
  echo "OK: Uninstalled macOS recommend+apply LaunchAgent."
else
  echo "No plist found at $PLIST"
fi
