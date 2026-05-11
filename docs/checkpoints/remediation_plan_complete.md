# CryptKeep — Complete Remediation Plan

**Date:** 2026-05-10 | **Based on:** Passes 1–3J (86 checkpoint commits)

---

## Priority 0 — Fix NOW (before soak ends)

### P0-1: H6 — soak evidence invisible to promotion gate

**File:** services/backtest/evidence_cycle.py:110
**Add to _normalize_strategy_name:**
```python
if 'sma_200' in text or 'es_daily_trend' in text:
    return 'sma_200_trend'
```
**Risk:** Zero. No restart needed. Fix before promotion gate evaluation.

### P0-2: H9 — supervisor missing pipeline and executor

**File:** services/supervisor/supervisor.py
**Add to MANAGED_SERVICES:**
```python
'pipeline', 'intent_executor'
```
**Risk:** Low. Requires supervisor restart (safe during soak).

---

## Priority 1 — Fix before live deployment

### P1-1: H5 — resume_if_safe disconnected from config (Drill 6)

resume_if_safe() sets arming signal but not config.
live_enabled_and_armed() requires BOTH.
**Fix:** Add resume bypass flag OR have resume_if_safe set config.

### P1-2: H4 — wire governance state machine into production

can_transition(), decide(), should_invalidate() never called.
**Fix:** Call can_transition() before every campaign-level transition.
Call before force_safe_degraded() demotion.

### P1-3: H1/H2/H3 — VIEWER role boundary violations

50_Automation.py (partial arming), 70_Settings.py (API key write),
44_Paper_Reconciliation.py (paper state corruption).
**Fix:** Add require_role('OPERATOR') at top of each affected handler.

### P1-4: H7 — enforce_direct_origin_block dead code

**Fix:** Call enforce_direct_origin_block() in HTTP request handler
when auth_scope == 'remote_public_candidate'.

### P1-5: M — GateIO client_id_param missing in exchange_client.py

**Fix:** Add GateIO branch: return {'text': client_id}

### P1-6: M — No explicit timeout in fetch_ohlcv (root cause of 3 incidents)

**Fix:** Pass timeout=8000 in make_exchange config for OHLCV fetches.

---

## Priority 2 — Fix before promotion

- P2-1: Consolidate 4 strategy name normalizations -> 1 canonical module
- P2-2: Document canonical intent store (execution_store_sqlite is canonical)
- P2-3: Fix pnl_store NULL fill_id deduplication gap
- P2-4: Fix autocommit in 5 storage stores (use explicit transactions)

---

## Priority 3 — Systemic debt

- P3-1: Consolidate 9 risk threshold sets -> 1 configurable source
- P3-2: Consolidate 3 paper trading implementations
- P3-3: Consolidate 2 market data modules (label marketdata/ deprecated)
- P3-4: Fix H8 live_safety_state wrong fail direction (dead code)
- P3-5: Add sma_200_trend to candidate_advisor ALLOWED_STRATEGIES
- P3-6: Wire candidate_advisor output into pipeline runner

---

## Soak evidence checklist (run when soak completes)

- [ ] Confirm P0-1 applied
- [ ] Run evidence_cycle for 'sma_200_trend' -- verify fill count matches soak
- [ ] Check unmapped_strategy_ids is empty
- [ ] Note paper fee is 0 BPS -- P&L not representative of live (~60 BPS Coinbase)

---

## All High findings

| # | Finding | Priority |
|---|---|---|
| H6 | Soak evidence invisible to promotion gate | P0-1 FIX FIRST |
| H9 | Supervisor missing pipeline/executor | P0-2 FIX NOW |
| H5 | resume_if_safe disconnected (Drill 6) | P1-1 |
| H4 | Governance dead code | P1-2 |
| H1-H3 | VIEWER role boundaries | P1-3 |
| H7 | enforce_direct_origin_block dead code | P1-4 |
| H8 | live_safety_state wrong fail direction | P3-4 dead code |
