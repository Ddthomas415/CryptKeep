# CryptKeep — Complete Remediation Plan

**Date:** 2026-05-10 | **Based on:** Passes 1–3J (87 checkpoint commits)
**Verification date:** 2026-05-11 | **Correction date:** 2026-05-11

---

## CORRECTIONS FROM OPERATOR REVIEW (2026-05-11)

### H9 scope correction

Original claim: "supervisor.MANAGED_SERVICES does not include pipeline or executor."

**CORRECTED:** This was based on the wrong supervisor module.

The active paper-soak control path is `scripts/run_bot_runner.py`, which has its own
MANAGED_SERVICES (lines 32–35) including `pipeline`, `executor`, `intent_consumer`,
`ops_signal_adapter`, `ops_risk_gate`, `ai_alert_monitor`.

`bot_status.py` line 14 reads from `services/runtime/process_supervisor`, NOT from
the legacy `services/supervisor/supervisor.py`.

**H9 revised:** The defect in `services/supervisor/supervisor.py` is real but that module
is NOT the active soak supervisor. H9 is a legacy-surface defect, not a current-soak blocker.
Remove from P0. Reclassify as P3 (legacy surface cleanup).

### H6 scope extended

Original claim: only `evidence_cycle.py:_normalize_strategy_name` had the blind spot.

**CORRECTED:** Three files have the same normalization gap:

1. `services/backtest/evidence_cycle.py:110` — _normalize_strategy_name() confirmed
2. `services/analytics/strategy_feedback.py:28` — own _normalize_strategy_name(), same gap
3. `services/backtest/leaderboard.py` — default_strategy_candidates() has no sma_200_trend entry

All three must be fixed for soak evidence to be fully visible to the promotion path.

---

## VERIFICATION STATUS (updated 2026-05-11)

| Fix | Soak branch status | Verified |
|---|---|---|
| P0-1 (H6) evidence_cycle normalization | **NOT APPLIED** | grep empty |
| P0-1 (H6) strategy_feedback normalization | **NOT APPLIED** | grep empty |
| P0-1 (H6) leaderboard candidates | **NOT APPLIED** | sma_200_trend absent |
| H9 supervisor gap | **Scope corrected** | run_bot_runner.py manages pipeline |

---

## Priority 0 — Fix before post-soak evidence evaluation

### P0-1: H6 — soak evidence normalization (THREE FILES)
**Status: OPEN on soak branch — all three files**

**File 1:** `services/backtest/evidence_cycle.py:110` — _normalize_strategy_name()
**File 2:** `services/analytics/strategy_feedback.py:28` — _normalize_strategy_name()
**Fix for both:** Add before `return None`:
```python
if "sma_200" in text or "es_daily_trend" in text or "daily_trend" in text:
    return "sma_200_trend"
```

**File 3:** `services/backtest/leaderboard.py` — default_strategy_candidates()
**Fix:** Add sma_200_trend to the candidates list.

**Why critical:** All 168 hours of fills are filed under "es_daily_trend_v1".
Without normalization, fills route to unmapped_strategy_ids and are invisible
to evidence_cycle, strategy_feedback, and leaderboard queries.

**Delivery:** Create a side branch off the soak branch. Do not touch the running checkout.

---

## Priority 1 — Fix before live deployment

### P1-1: H5 — resume_if_safe disconnected from config (Drill 6 FAIL)
### P1-2: H4 — governance state machine never called in production
### P1-3: H1/H2/H3 — VIEWER role boundary violations (3 pages)
### P1-4: H7 — enforce_direct_origin_block dead code
### P1-5: GateIO client_id_param missing in exchange_client.py
### P1-6: No explicit timeout in fetch_ohlcv (root cause 3 soak incidents)

---

## Priority 2 — Fix before promotion gate evaluation

- P2-1: Consolidate 4 strategy name normalizations -> 1 canonical module
- P2-2: Document canonical intent store
- P2-3: Fix pnl_store NULL fill_id deduplication
- P2-4: Fix autocommit in 5 storage stores

---

## Priority 3 — Systemic debt (not soak blockers)

- P3-1: Consolidate 9 risk threshold sets -> 1 configurable source
- P3-2: Consolidate 3 paper trading implementations
- P3-3: Consolidate 2 market data modules
- P3-4: Fix H8 live_safety_state wrong fail direction (dead code)
- P3-5: Add sma_200_trend to candidate_advisor ALLOWED_STRATEGIES
- P3-6: Wire candidate_advisor output into pipeline runner
- **P3-7: Clean up legacy services/supervisor/supervisor.py MANAGED_SERVICES** (H9 reclassified)

---

## Soak evidence checklist (run when soak completes)

- [ ] Confirm P0-1 applied to all 3 files on side branch and merged
- [ ] Run evidence_cycle for "sma_200_trend" -- verify fill count
- [ ] Run strategy_feedback for "sma_200_trend" -- verify trade count
- [ ] Check leaderboard includes sma_200_trend candidate
- [ ] Check unmapped_strategy_ids is empty
- [ ] Note paper_fee_bps: 0 -- P&L not representative (~60 BPS live Coinbase)

---

## All High findings (corrected)

| # | Finding | Priority | Notes |
|---|---|---|---|
| H6 | Soak evidence: 3 files missing normalization | **P0-1** | Fix before post-soak eval |
| H5 | resume_if_safe disconnected (Drill 6) | P1-1 | Before live |
| H4 | Governance dead code | P1-2 | Before live |
| H1-H3 | VIEWER role boundaries | P1-3 | Before live |
| H7 | enforce_direct_origin_block dead code | P1-4 | Before live |
| H8 | live_safety_state wrong fail direction | P3-4 | Dead code, safe |
| H9 | Legacy supervisor missing pipeline | P3-7 | NOT active soak path |
