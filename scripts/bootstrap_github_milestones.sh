#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required (https://cli.github.com/)" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh auth is required. Run: gh auth login" >&2
  exit 1
fi

create_milestone() {
  local title="$1"
  local description="$2"

  if gh api repos/:owner/:repo/milestones --paginate -q ".[] | select(.title == \"$title\") | .title" 2>/dev/null | grep -qx "$title"; then
    echo "exists: $title"
    return 0
  fi

  gh api repos/:owner/:repo/milestones \
    -X POST \
    -f title="$title" \
    -f description="$description" >/dev/null
  echo "created: $title"
}

create_milestone "M1 — Research MVP" "Dashboard, Research, Connections, Settings, audit/health/metrics baseline"
create_milestone "M2 — Paper Trading" "State machines, policy engine, recommendations, paper approvals, paper orders/positions, risk page"
create_milestone "M3 — Live Approval" "One live exchange, approval-based execution, kill switch, reconciliation"
create_milestone "M4 — Automation and Ops" "Event bus, workers, terminal, projections, replay/debug, advanced hardening"

echo "milestone bootstrap complete"
