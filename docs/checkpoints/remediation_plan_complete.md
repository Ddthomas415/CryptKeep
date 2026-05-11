# CryptKeep — Complete Remediation Plan

**Date:** 2026-05-10 | **Based on:** Passes 1–3J (87 checkpoint commits)
**Verification date:** 2026-05-11

---

## VERIFICATION STATUS

Both P0 fixes were verified against the soak branch on 2026-05-11.

| Fix | Soak branch status | Verified |
|---|---|---|
| P0-1 (H6) evidence_cycle normalization | **NOT APPLIED** | grep returns empty |
| P0-2 (H9) supervisor MANAGED_SERVICES | **NOT APPLIED** | line 24 unchanged |

Neither fix is present on `codex/runtime-hardening-ai-alert-monitor`.
Both must be applied before the soak completes.

---

## Priority 0 — Fix before soak completes (~97h remaining at audit close)

### P0-1: H6 — soak evidence invisible to promotion gate
**Status: OPEN — NOT applied to soak branch**

**File:** `services/backtest/evidence_cycle.py` line 110
**Function:** `_normalize_strategy_name`
**Verified missing:** grep for "es_daily_trend" returns nothing on soak branch.

**Add:**
```python
if "sma_200" in text or "es_daily_trend" in text or "daily_trend" in text:
    return "sma_200_trend"
```

**Why critical:** When soak completes, promotion gate will show insufficient
evidence. All 168 hours of fills are filed under "es_daily_trend_v1" which
_normalize_strategy_name maps to None -> unmapped_strategy_ids -> invisible.

**Risk:** Zero. No restart needed. Apply to soak branch immediately.

---

### P0-2: H9 — supervisor missing pipeline and executor
**Status: OPEN — NOT applied to soak branch**

**File:** `services/supervisor/supervisor.py` line 24
**Verified missing:** MANAGED_SERVICES does not contain "pipeline" or "intent_executor".

**Change to:**
```python
MANAGED_SERVICES = (
    "dashboard", "tick_publisher", "market_ws", "evidence_webhook",
    "ops_signal_adapter", "ops_risk_gate", "intent_consumer", "reconciler",
    "pipeline",         # ADD
    "intent_executor",  # ADD
)
```

**Why urgent:** Dead-process gap. If pipeline crashes, no automated detection
or restart fires. The soak could silently lose signal coverage.

**Risk:** Low. Requires supervisor restart (safe during soak).

---

## Priority 1 — Fix before live deployment

### P1-1: H5 — resume_if_safe disconnected from config (Drill 6 FAIL)
resume_if_safe() sets arming signal but not config live_enabled flag.
live_enabled_and_armed() requires both. Fix: add resume bypass flag or
have resume_if_safe() update config.

### P1-2: H4 — governance state machine never called in production
can_transition(), decide(), should_invalidate() implemented but never invoked.
Fix: call can_transition() before campaign-level transitions and in
force_safe_degraded().

### P1-3: H1/H2/H3 — VIEWER role boundary violations
50_Automation.py (arming), 70_Settings.py (API keys), 44_Paper_Reconciliation.py.
Fix: add require_role("OPERATOR") at top of each affected action handler.

### P1-4: H7 — enforce_direct_origin_block dead code
Implemented and tested but never called in production HTTP handler.
Fix: call in HTTP request handler when auth_scope == "remote_public_candidate".

### P1-5: GateIO client_id_param missing in exchange_client.py
Fix: add elif ex in ("gateio", "gate.io", "gate"): return {"text": client_id}

### P1-6: No explicit timeout in fetch_ohlcv (root cause all 3 soak incidents)
Fix: pass timeout=8000 in make_exchange config for OHLCV fetches.
Add retry with backoff before propagating to pipeline.

---

## Priority 2 — Fix before promotion gate evaluation

- P2-1: Consolidate 4 strategy name normalizations -> 1 canonical module
- P2-2: Document canonical intent store (execution_store_sqlite is canonical)
- P2-3: Fix pnl_store NULL fill_id deduplication
- P2-4: Fix autocommit in 5 storage stores (use explicit transactions)

---

## Priority 3 — Systemic debt

- P3-1: Consolidate 9 risk threshold sets -> 1 configurable source
- P3-2: Consolidate 3 paper trading implementations
- P3-3: Consolidate 2 market data modules (label marketdata/ deprecated)
- P3-4: Fix H8 live_safety_state wrong fail direction (dead code, safe)
- P3-5: Add sma_200_trend to candidate_advisor ALLOWED_STRATEGIES
- P3-6: Wire candidate_advisor output into pipeline runner

---

## Soak evidence checklist (run when soak completes)

- [ ] Confirm P0-1 applied on soak branch
- [ ] Run evidence_cycle for "sma_200_trend" -- verify fill count
- [ ] Check unmapped_strategy_ids is empty in evidence report
- [ ] Note paper_fee_bps: 0 -- P&L not representative (~60 BPS live Coinbase)

---

## All High findings with verification status

| # | Finding | Soak branch | Priority |
|---|---|---|---|
| H6 | Soak evidence invisible to promotion gate | **OPEN** | P0-1 |
| H9 | Supervisor missing pipeline/executor | **OPEN** | P0-2 |
| H5 | resume_if_safe disconnected (Drill 6) | OPEN | P1-1 |
| H4 | Governance dead code | OPEN | P1-2 |
| H1 | VIEWER partial arming state | OPEN | P1-3 |
| H2 | VIEWER writes API keys | OPEN | P1-3 |
| H3 | VIEWER corrupts paper state | OPEN | P1-3 |
| H7 | enforce_direct_origin_block dead code | OPEN | P1-4 |
| H8 | live_safety_state wrong fail direction | OPEN (dead code) | P3-4 |
