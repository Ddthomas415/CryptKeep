# Pass 2S — Execution Layer Batch 2

**Date:** 2026-05-10
**Pass:** 2S
**Status:** COMPLETE for this batch

---

## SHOWN findings

### Finding 1 — live_arming uses atomic_write + Drill 6 fix documented (Strength)

Arming state uses atomic_write. live_armed_signal() precedence:
1. CBP_EXECUTION_ARMED env var
2. CBP_LIVE_ENABLED env var
3. CBP_EXECUTION_LIVE_ENABLED env var
4. Persisted live_arming.json (300s max age)

Comment explicitly says: 'This fixes Drill 6: sibling processes that do not
inherit resume_gate.py in-process env var can still read the persisted arming state.'

H5 status: still open. live_enabled_and_armed() checks is_live_enabled(cfg) first.
If config doesn't have live_enabled=True, still fails regardless of arming file.

---

### Finding 2 — issue_token + verify_and_consume one-time token (Strength)

SHA-256 hashed, TTL 30min, consumed flag prevents replay. Token not stored in
plaintext. Well-implemented one-time confirmation token for live arming.

---

### Finding 3 — Corrupted arming file fails closed (Strength)

Corrupted live_arming.json: get_live_armed_state() raises -> caught ->
returns armed=False. Correct fail-safe direction.

---

### Finding 4 — Persisted arming state 300s max age (Strength)

Arming file older than 300s (configurable via CBP_LIVE_ARMING_MAX_AGE_S)
treated as disarmed. Prevents stale arming file from keeping crashed system armed.

---

### Finding 5 — require_ws_fresh_for_live=True blocks on no WS data (Shown)

SafetyConfig default: require_ws_fresh_for_live=True, max_ws_recv_age_ms=1500.
No WS data -> ok=False -> blocks live submission. Current soak doesn't run
market_ws, so live would be blocked by this gate as well.

---

### Finding 6 — startup_guard blocks unknown position state (Strength)

On startup: no position record -> blocks unless CBP_STARTUP_CONFIRM_FLAT=true.
Open position -> blocks unless CBP_STARTUP_ALLOW_OPEN_POSITION=true.
Prevents starting into unknown position state.

---

### Finding 7 — idempotency.py is a near-empty stub (Noted)

client_oid(intent_id) = f'intent-{intent_id}'. Two lines.
Actual idempotency handled by order_dedupe_store_sqlite (Pass 2A REVIEWED).

---

### Finding 8 — order_manager time-bucketed idempotency (Strength)

sha256(venue|symbol|side|qty|price|5s-bucket). Two identical orders within
same 5-second window deduplicated. Secondary layer on top of order_dedupe_store.

---

### Finding 9 — latency_slippage_guard P95 defaults active (Shown)

Default: P95 ack_ms=2500, P95 slippage=25bps, window=200 orders.
guard_enabled=True. Configurable via user.yaml.

---

## Still NOT_AUDITED in services/execution/ (59 of 80 files)

Critical remaining: _executor_shared.py, _executor_reconcile.py,
intent_writer.py, live_executor.py, risk_gates.py, safety.py,
intent_reconciler.py, order_reconciliation.py, live_fill_mapper.py,
live_event_executor.py, live_trader_loop.py, funnel.py, and ~47 others.

---

## Summary

| Finding | Severity |
|---|---|
| live_arming atomic_write + Drill 6 fix | **Strength** |
| One-time token correct | **Strength** |
| Corrupted arming fails closed | **Strength** |
| Persisted arming 300s max age | **Strength** |
| require_ws_fresh blocks on no WS | Shown |
| startup_guard blocks unknown position | **Strength** |
| idempotency.py near-empty stub | Noted |
| order_manager time-bucket dedup | **Strength** |
| latency_slippage_guard P95 defaults active | Shown |

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2S
**Next:** services/execution/ remaining 59 files
