# Pass 2A Audit — Critical Pre-Live Surfaces

**Date:** 2026-05-10  
**Pass:** 2A — must-read before live deployment  
**Status:** COMPLETE

---

## Surfaces covered

1. `services/execution/live_exchange_adapter.py`
2. `services/execution/lifecycle_boundary.py`
3. `services/execution/order_params.py` (prepare_ccxt_params)
4. `services/risk/risk_daily.py`
5. `services/journal/canonical_execdb.py`
6. `storage/order_dedupe_store_sqlite.py`
7. `services/security/auth_runtime_guard.py`
8. `services/risk/risk_gate.py` (risk limit loading)

---

## SHOWN findings

### Finding 1 — `find_order_by_client_oid` silently swallows all exchange exceptions (Medium)

```python
try:
    found = _find(self.ex.fetch_open_orders(sym) or [])
    if found:
        return found
except Exception:
    pass   # silent
```

If both `fetch_open_orders` and `fetch_closed_orders` raise, the method
returns `None`. The caller (`intent_executor.py:59`) uses this as a dup-guard:
if it returns `None` due to a transient API failure (not because the order
doesn’t exist), the executor may re-submit an order already placed.

**Mitigation:** `prepare_ccxt_params` injects `client_order_id` at the
exchange level (venue-specific). Duplicate submissions are rejected by most
exchanges. Residual risk: not all exchanges enforce client order ID uniqueness.

---

### Finding 2 — `find_order_by_client_oid` not behind lifecycle boundary (Low)

`cancel_order` and `fetch_order` route through `lifecycle_boundary` which
logs every request and result. `find_order_by_client_oid` calls
`ex.fetch_open_orders()` directly. No event is logged for dup-guard lookups.
An operator cannot tell from the event log whether a dup-guard check was
attempted before a resubmission.

---

### Finding 3 — `apply_fill_once` is correctly idempotent (Strength)

```sql
PRIMARY KEY(venue, fill_id)
```

`IntegrityError` on duplicate skips the fill without updating counters.
Empty `fill_id` is explicitly logged and skipped. WAL mode + `busy_timeout=15000ms`.

---

### Finding 4 — Canonical fills use INSERT OR IGNORE on PRIMARY KEY (Strength)

```sql
INSERT OR IGNORE INTO canonical_fills(venue, fill_id, ...) VALUES (...)
```

Replay-safe. Comment in source confirms intent.

---

### Finding 5 — Order dedup two UNIQUE constraints, fails closed (Strength)

```sql
UNIQUE INDEX uq_od_intent ON order_dedupe(exchange_id, intent_id)
UNIQUE INDEX uq_od_client ON order_dedupe(exchange_id, client_order_id)
```

`claim()` raises `RuntimeError("order_dedupe claim failed")` if the
`INSERT OR IGNORE` returns 0 rows. Caller must handle explicitly.
Two independent UNIQUE constraints: either blocks a duplicate.

---

### Finding 6 — Risk limits have permissive hardcoded defaults (Noted)

```python
mdl = float(risk_cfg.get("max_daily_loss_usd", 500.0))
mnt = float(risk_cfg.get("max_notional_per_trade_usd", 10000.0))
mpn = float(risk_cfg.get("max_position_notional_usd", 50000.0))
```

Missing `risk:` config section activates these defaults rather than failing
closed. `$10,000` per trade and `$50,000` position notional could be
significant on a live account. `LAUNCH_CHECKLIST.md` Section 2 requires
these to be set explicitly — close if checklist is followed.

---

### Finding 7 — `auth_runtime_guard` detects bypass and remote violations (Strength)

Three violations detected and surfaced:
- `BYPASS_DASHBOARD_AUTH` set outside `APP_ENV=dev`
- `CBP_ALLOW_ENV_LOGIN` set outside `APP_ENV=dev`
- `remote_public_candidate` without outer access-control layer

All surfaced in dashboard sidebar via `auth_capabilities.py`.

**One gap:** if `get_settings_view` import fails, it is suppressed silently
and `auth_scope` defaults to `"local_private_only"`. The remote/public
candidate violation would not fire if settings view is unavailable.

---

### Finding 8 — `submit_order` routes through all 7 safety gates (Strength)

`live_exchange_adapter.submit_order()` → `place_order()` → 7 sequential gates:
risk_sink_failed flag, system health, kill switch, arming check, ops risk gate,
daily limits, market rules. All fail-closed.

---

### Finding 9 — `close()` suppresses all exceptions (Low)

```python
except Exception as _err:
    pass  # suppressed
```

Connection close failures are never logged. Could leave a WebSocket connection
open generating fills after the system believes it has disconnected.

---

## Summary

| Finding | Surface | Severity |
|---|---|---|
| `find_order_by_client_oid` swallows exceptions | `live_exchange_adapter.py` | Medium |
| `find_order_by_client_oid` not behind lifecycle boundary | `live_exchange_adapter.py` | Low |
| `apply_fill_once` idempotent on (venue, fill_id) | `risk_daily.py` | **Strength** |
| Canonical fills INSERT OR IGNORE on PRIMARY KEY | `canonical_execdb.py` | **Strength** |
| Order dedup two UNIQUE constraints, fails closed | `order_dedupe_store_sqlite.py` | **Strength** |
| Risk limits permissive hardcoded defaults | `risk_gate.py` | Noted |
| Auth guard detects bypass and remote violations | `auth_runtime_guard.py` | **Strength** |
| `get_settings_view` failure suppressed in auth guard | `auth_runtime_guard.py` | Low |
| `submit_order` through all 7 safety gates | `live_exchange_adapter.py` | **Strength** |
| `close()` suppresses all exceptions | `live_exchange_adapter.py` | Low |

---

## Updated depth labels for audit map

| File | Depth |
|---|---|
| `services/execution/live_exchange_adapter.py` | REVIEWED |
| `services/execution/lifecycle_boundary.py` | REVIEWED |
| `services/execution/order_params.py` | SAMPLED |
| `services/risk/risk_daily.py` | REVIEWED |
| `services/journal/canonical_execdb.py` | REVIEWED |
| `storage/order_dedupe_store_sqlite.py` | REVIEWED |
| `services/security/auth_runtime_guard.py` | REVIEWED |
| `services/risk/risk_gate.py` | SAMPLED |

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Pass 2A  
**Next:** Pass 2B — adversarial verification of H1/H2 (VIEWER arming path)
or Pass 2C — unread dashboard pages
