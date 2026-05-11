# Pass 2U — Execution Layer Batch 4

**Date:** 2026-05-10
**Pass:** 2U
**Status:** COMPLETE for this batch

---

## SHOWN findings

### Finding 1 — retry_policy correct hard stops + exponential backoff (Strength)

Hard stops: InsufficientFunds, InvalidOrder, BadRequest, AuthenticationError,
PermissionDenied, AccountNotFound, OrderNotFound, InvalidNonce.
Retryable: RateLimitExceeded, RequestTimeout, NetworkError, 429/502/503/504.
Backoff: min(cap, base * 2^attempt) + 15% jitter cap. Correct set.

---

### Finding 2 — exchange_client missing GateIO client_id_param case (Medium)

```python
# exchange_client.py
if ex == 'binance': return {'newClientOrderId': client_id}
return {'clientOrderId': client_id}   # GateIO wrong
```

```python
# order_params.py (correct)
if ex_id == 'binance': return {'newClientOrderId': client_id}
elif ex_id in ('gateio', 'gate.io', 'gate'): return {'text': client_id}
else: return {'clientOrderId': client_id}
```

Two implementations of the same mapping. exchange_client.py missing GateIO.
GateIO client OID would be silently ignored via this path.
Comment 'Human Review Required' was on this exact field but fix only applied
in order_params.py, not exchange_client.py.

**Current soak (Coinbase):** not exploitable.

---

### Finding 3 — normalize_ccxt is a passthrough not a normalization (Noted)

```python
def normalize_order(order):
    if isinstance(order, dict): return order
    return {}
```

Returns raw CCXT response unchanged. Not field normalization.

---

### Finding 4 — paper_engine injectable clock + market quality guards (Strength)

Injectable clock for deterministic replay. Cash state persisted, initialized
only on first run (correct resumability). Market quality and staleness checks
before each paper fill. Same guards as live path.

---

### Finding 5 — reconciliation validates credentials before API call (Strength)

Missing apiKey or secret returns structured error before CCXT call.

---

### Finding 6 — Coinbase has no idempotency window in venue_capabilities (Shown)

Binance and GateIO: 1800s. Coinbase: None.
retry_is_safe_after_ambiguous_ack depends on remote order ID for Coinbase.

---

## Summary

| Finding | Severity |
|---|---|
| retry_policy correct hard stops and backoff | **Strength** |
| exchange_client missing GateIO client_id_param | Medium |
| normalize_ccxt passthrough | Noted |
| paper_engine injectable clock + market quality | **Strength** |
| reconciliation validates credentials | **Strength** |
| Coinbase no idempotency window | Shown |

---

## services/execution/ coverage: ~35 of 80 files reviewed

Remaining ~45 files. Next priority:
ccxt_fills.py, intent_reconciler.py, order_reconciliation.py,
live_event_executor.py, live_trader_loop.py, sizing.py, position_math.py

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2U
**Next:** Continue services/execution/ remaining 45 files
