# Phase 275 — Intent Executor Wiring (paper-first)

Adds:
- services/execution/intent_store.py (created if missing): SQLite intent queue
- services/journal/order_event_store.py (created if missing): SQLite order event journal
- services/execution/intent_executor.py:
  - claims READY -> SENDING
  - duplicate guards (order_id exists; open-order found by client_oid)
  - places order via adapter
  - journals events
  - reconciles SENT/OPEN using open-orders and fetch_order

- scripts/run_intent_executor.py: background loop
- services/execution/intent_executor_supervisor.py: start/stop/status via PID file
- Streamlit panel: Execution Loop

Live safety:
- live orders only when execution.live_enabled=true
- optional kill/cooldown enforced if services.risk.live_safety_state exists
