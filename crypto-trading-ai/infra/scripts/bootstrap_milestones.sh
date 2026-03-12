#!/usr/bin/env bash
set -euo pipefail

gh api repos/:owner/:repo/milestones -f title="M1 — Research MVP" -f description="Dashboard, Research, Connections, Settings" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="M2 — Paper Trading" -f description="State machines, policy engine, paper trading" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="M3 — Live Approval" -f description="Live approval + reconciliation + kill switch" 2>/dev/null || true
gh api repos/:owner/:repo/milestones -f title="M4 — Automation and Ops" -f description="Event bus, terminal, hardening" 2>/dev/null || true
