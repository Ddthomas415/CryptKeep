# Pass 2E — Test Audit and Remaining Governance

**Date:** 2026-05-10  
**Pass:** 2E  
**Status:** COMPLETE — Pass 2 fully done

---

## Governance remaining modules

### Finding 1 — Governance modules minimal but correct for stated scope (Shown)

`campaign_validation.py`:
```python
def validate_campaign_payload(payload):
    if not isinstance(payload, dict): return False
    return bool(payload.get("strategy") or payload.get("strategies"))
```
Only checks for strategy key presence. Source comment: "Minimal canonical validation."
Directly confirms governance signoff Blocking:Yes item 1.

`decision_engine.py`:
```python
def decide(state): return "BLOCK" if str(state) == "INVALID" else "ALLOW"
```
4 lines. Correct for the state machine’s one rule. Callers must honor `"BLOCK"`.

`campaign_fingerprint.py`:
`sha256(json.dumps(sorted))`. Deterministic, stable. Correct.

`deployment_truth.py`:
Thin wrapper over `auth_runtime_guard_status()`. Correct.

`operator_overrides.py`:
Hard cap: `max_order_quote > 1,000,000` raises `ValueError`. One concrete safety bound.

---

### Finding 2 — Governance signoff Blocking:Yes items — final status (Shown)

| Item | Status |
|---|---|
| Campaign validation depth minimal | **Still open** |
| Terminal invalidation enforcement | **Partially addressed** |
| End-to-end proof invalid → continuation blocked | **Still open** |

Individual functions are correct. End-to-end proof requires tracing every caller
of `can_transition` / `decision_engine.decide` and confirming `BLOCK` is
honored. Not done.

---

## Active strategy

### Finding 3 — `signal_from_ohlcv` correctly returns `action="buy"` (Strength)

```python
action = "buy" if (signal == "long" and reg["entry_allowed"]) else "hold"
```

`action: "buy"` only when SMA long AND ATR regime filter passes. Matches
`ESDailyTrendPipeline.run_once()` which reads `sig.get("action")`. Semantically
aligned.

`entry_allowed=True` only when ATR ratio is within configured threshold.
Conservative entry filter — high-volatility conditions are skipped.

---

## Test audit

### Finding 4 — Critical-path tests cover failure modes (Strength)

| Test file | Coverage |
|---|---|
| `test_fill_sink_logging.py` | Schema, risk_daily, record failure |
| `test_p0_live_accounting_fail_closed.py` | executor_shared, CompositeFillSink, health detection |
| `test_live_arming_env_sources.py` | Canonical arming env acceptance/rejection |
| `test_live_arming_contract.py` | Canonical arming shape |
| `test_paper_adapter_interface.py` | Paper adapter method contracts |
| `test_live_intent_consumer_orphan_fix.py` | MQ block + risk write orphan fixes |

Critical-path tests are present and cover failure cases.

---

### Finding 5 — 7 near-identical formatting tests inflate test count (Shown)

`test_checkpoints_recent_firstline_no_double_asterisk.py` exists in 7 variants
(again, third, fourth, fifth, sixth, seventh). One formatting constraint,
seven files. Inflates test pass count without adding logic coverage.

---

### Finding 6 — No tests for H1, H2, H3 or key Pass 2 findings (Shown)

No tests found for:
- VIEWER arming via Automation save (H1)
- VIEWER API key write via Settings save (H2)
- VIEWER paper reconciliation (H3)
- `find_order_by_client_oid` exception swallowing
- Safe wrapper IDLE-on-crash
- `run_intent_consumer_safe` routing to paper-era consumer

Findings confirmed by code inspection only. Tests must be written before fix PRs.

---

## Pass 2 cumulative findings

| # | Finding | Severity |
|---|---|---|
| 2A-1 | `find_order_by_client_oid` swallows exceptions | Medium |
| 2A-6 | Risk limits permissive hardcoded defaults | Noted |
| H3 | VIEWER can corrupt paper state via reconciliation | Medium |
| 2D-2 | Campaign state machine has one rule only | Shown |
| 2D-3 | `claims_guard` effectively a passthrough | Shown |
| 2E-5 | 7 formatting tests inflate test count | Shown |
| 2E-6 | No tests for H1, H2, H3 | Shown |

---

## Next actions (priority order)

1. Write tests for H1, H2, H3 before fix PRs
2. Fix H1, H2, H3 (one-line page auth changes)
3. Fix Pass 2A Finding 1 (`find_order_by_client_oid`)
4. Close governance signoff items 1 and 3
5. Pass 3 — governance lifecycle call site verification

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Pass 2E and full Pass 2
