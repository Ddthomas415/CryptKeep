# Pass 2D — Zero-Coverage Services

**Date:** 2026-05-10  
**Pass:** 2D — services with zero prior coverage  
**Status:** COMPLETE

---

## Surfaces covered

- `services/fills/fills_poller.py`, `user_stream_router.py`
- `services/reconciliation/exchange_reconciler.py`
- `services/governance/campaign_state_machine.py`
- `services/governance/invalidation.py`
- `services/governance/claims_guard.py`
- `services/analytics/paper_strategy_evidence_service.py`

---

## SHOWN findings

### Finding 1 — Fills route through CanonicalFillSink; synthetic fill IDs are deterministic (Strength)

`user_stream_router._stable_synth_fill_id` generates a deterministic synthetic
fill ID for exchanges that don’t provide one, using `sha256` of
`exchange_id:trade_id:ts:side:qty:price`. Same fill always produces the same
ID. Replays are safe. Downstream `CanonicalFillSink` INSERT OR IGNORE ensures
idempotency.

---

### Finding 2 — Campaign state machine blocks INVALID transitions but has one rule only (Shown)

```python
def can_transition(current_state, next_state):
    if str(current_state) == "INVALID" and str(next_state) != "INVALID":
        return False
    return True
```

Six lines. One rule. Correctly blocks `INVALID → non-INVALID`.

Does not define valid states, valid inter-state transitions, or log failed
transitions. Returns `False` silently — the caller must check. The governance
signoff’s "end-to-end proof" requires verifying every caller handles the
`False` return. Not confirmed in this pass.

---

### Finding 3 — `claims_guard.validate_claim` is effectively a passthrough (Shown)

Only rejects "guaranteed profit" in claim text. All other claims return
`"ALLOWED"`. The middle block always falls through. Not a meaningful
governance gate for most claim types (consistent returns, low risk, etc).

---

### Finding 4 — `invalidation.py` uses exact-match triggers (Shown)

```python
TERMINAL_INVALIDATION_REASONS = {
    "fingerprint_mismatch", "drift", "contamination"
}
```

Case-insensitive after strip. Exact match only. A reason like `"strategy_drift"`
or `"data_drift"` would NOT match `"drift"`. Callers must use precise strings.

---

### Finding 5 — Reconciler in-memory dedup; downstream is persistent (Strength)

In-memory `seen: set[str]` prevents double-processing within one
`reconcile_once` call. Not persistent across calls. But `CanonicalFillSink`
and `risk_daily.apply_fill_once` both have persistent idempotency, so
double-processing at the reconciler level produces no duplicate accounting.

---

### Finding 6 — Status files use `write_text` not `atomic_write` (Low)

`paper_strategy_evidence_service.py` lines 89, 93. Same inconsistency as
PID files and safety_auditor. Low risk for advisory artifacts.

---

### Finding 7 — DEFAULT_STRATEGIES missing `es_daily_trend_v1` (Noted)

`DEFAULT_STRATEGIES = ("ema_cross", "breakout_donchian", "mean_reversion_rsi")`

Active soak strategy is `es_daily_trend_v1`. Evidence service invoked with
defaults would collect evidence for the wrong strategies. Mitigated by
explicit `cfg.signal_source` and strategy ID config at runtime.

---

### Finding 8 — Evidence service correctly uses `start_new_session=True` (Strength)

`kwargs["start_new_session"] = True` on line 426. Correct session detach.
Note: `process_supervisor.py` uses `os.setsid` instead. Inconsistency
between the two launchers is noted.

---

## Summary

| Finding | Severity |
|---|---|
| Fills → CanonicalFillSink; synthetic IDs deterministic | **Strength** |
| State machine: one rule, INVALID block only | Shown |
| `claims_guard` passthrough | Shown |
| Invalidation triggers exact match only | Shown |
| Reconciler in-memory dedup; downstream persistent | **Strength** |
| Status files write_text not atomic_write | Low |
| DEFAULT_STRATEGIES missing es_daily_trend_v1 | Noted |
| Evidence service start_new_session=True correct | **Strength** |

---

## Still NOT_AUDITED in governance/

`campaign_fingerprint.py`, `campaign_validation.py`, `decision_engine.py`,
`deployment_truth.py`, `operator_overrides.py` — these close the governance
signoff Blocking:Yes items if their call sites are verified. Priority for Pass 2E.

`services/strategies/` — all files including `es_daily_trend.py` (active soak strategy).

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Pass 2D  
**Next:** Pass 2E — test audit and remaining governance modules
