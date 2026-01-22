# Order Intents (Phase 239)

Goal:
- Prevent duplicate order submissions across restarts and loop retries.

Mechanism:
- Create deterministic intent_id:
  venue::SYMBOL::side::timeframe::bar_ts_ms

Storage:
- data/execution.sqlite table order_intents

Statuses (initial):
- NEW (created this bar; not yet executed)
- STALE (NEW older than max_new_age_sec)
Later phases will add SENT/FILLED/FAILED with reconciliation to exchange order IDs.

Bot integration:
- Before executing BUY/SELL, create_if_new(...)
- If created=False => skip executing (idempotent behavior)
