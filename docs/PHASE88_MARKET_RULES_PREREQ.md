# Phase 88 - LIVE prereq: market rules cache must be fresh (fail-closed)

Adds:
- services/markets/prereq.py (check_market_rules_prereq)
- scripts/market_rules_health.py (CLI PASS/FAIL)
- best-effort patch to services/ops/live_prereqs.py to block LIVE unless rules cache is fresh
- dashboard/app.py panel showing status

Usage:
  python3 scripts/market_rules_health.py --ttl-hours 6
