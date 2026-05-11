# Pass 2Y — Execution Layer Final Files

**Date:** 2026-05-10
**Pass:** 2Y
**Status:** COMPLETE — services/execution/ safety-critical surfaces fully covered

---

## SHOWN findings

### Finding 1 — Three separate intent tracking stores (Medium)

- intent_store.py -> data/intents.sqlite (intents table)
- order_intents.py -> data/execution.sqlite (order_intents table)
- IntentQueueSQLite -> data/live_intent_queue.sqlite

Three concurrent stores with different schemas. No canonical store documented.
An intent processed in one store is not visible to another.

---

### Finding 2 — ccxt_private_factory validates credentials before exchange creation (Strength)

```python
if not creds.get('apiKey') or not creds.get('secret'):
    raise RuntimeError(f'missing_credentials:{ex}:{source}')
```

Raises before creating exchange object. Correct fix for the gap identified
in Pass 2A Finding 7 (make_exchange doesn't validate first). Use
make_private_exchange for all authenticated operations.

---

### Finding 3 — strategy_runner deprecated, raises on every call (Strength)

```python
run_once = _raise_placeholder_error
run_forever = _raise_placeholder_error
run = main = _raise_placeholder_error
```

No code can accidentally use the old strategy runner path.

---

### Finding 4 — compute_slippage_bps correct formula, None on missing data (Strength)

abs((fill - intended) / intended) * 10000. Returns None not 0 when prices
are missing. Correct distinction between no-data and zero slippage.

---

### Finding 5 — audit_monitor severity thresholds reasonable (Strength)

25% fail rate >= 8 events -> high. 10% fail rate >= 5 events -> warn.
Minimum event counts prevent false positives from small samples.

---

## Cumulative execution layer findings (Passes 2S-2Y)

| # | Finding | Severity |
|---|---|---|
| M1 | GateIO client_id_param missing in exchange_client.py | Medium |
| M2 | Three separate intent tracking stores, no canonical documented | Medium |
| L1 | paper_fees defaults 0 BPS | Low |
| L2 | outcome_logger non-atomic JSONL | Low |
| L3 | idempotency.py stub only | Low |
| L4 | live_fill_mapper stub returns [] | Low |

---

## services/execution/ effectively complete for safety-critical surfaces

All safety-critical files reviewed: arming, gating, fill accounting,
intent lifecycle, authority enforcement, retry policy, exchange client,
order deduplication, state machine, kill switch.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2Y
**Next:** Compile complete findings list or continue into remaining
NOT_AUDITED service directories
