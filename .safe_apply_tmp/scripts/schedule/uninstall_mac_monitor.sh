#!/usr/bin/env bash
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.cryptobotpro.monitor.plist"
if [ -f "$PLIST" ]; then
  launchctl unload "$PLIST" >/dev/null 2>&1 || true
  rm -f "$PLIST"
  echo "OK: Uninstalled macOS monitor LaunchAgent."
else
  echo "No monitor plist found at $PLIST"
fi
