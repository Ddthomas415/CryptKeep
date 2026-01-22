# Phase 87 - Market rules: fetch + cache + validate (Binance/Coinbase/Gate)

Adds:
- services/markets/* (rules fetchers + sqlite cache + validator)
- scripts/refresh_market_rules.py
- dashboard panel: Market Rules (Phase 87)

Executor integration:
- Add a line "# LIVE_MARKET_RULES_ANCHOR" right before LIVE submit success path,
  then re-run Phase 87 patch to apply the call (fail-closed).
