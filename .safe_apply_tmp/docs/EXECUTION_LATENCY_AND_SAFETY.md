# Phase 333 — Execution Latency + Safety Gates

Adds:
- Execution latency tracker:
  - order_submit_ms (marker)
  - submit_to_ack_ms
  - ack_to_fill_ms
- Safety gates (intended for live mode):
  - require WS market data freshness before sending orders

DB:
- Uses `data/market_ws.sqlite` latency_events table (category=execution)

Config (config/trading.yaml):
- execution_safety:
  - require_ws_fresh_for_live
  - max_ws_recv_age_ms
  - max_ack_ms
  - pause_seconds_on_breach
  - latency_db_path

Operational rule:
- There is no “no-delay trading”.
- We minimize + measure latency and fail-closed if data/execution becomes unsafe.
