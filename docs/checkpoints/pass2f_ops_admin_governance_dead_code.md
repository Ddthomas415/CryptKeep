# Pass 2F — Ops, Admin, and Governance Dead Code

**Date:** 2026-05-10
**Pass:** 2F
**Status:** COMPLETE

## Status update — 2026-05-11

- Historical finding `H4` remains valid as evidence of the wiring gap at audit time.
- Independently accepted remediation now exists on:
  - `codex/governance-enforcement-wiring` @ `8601aafae`
- That remediation has **not** been landed into the active soak checkout.
- Current blocker status is tracked in:
  - [audit_findings_status_2026_05_11.md](./audit_findings_status_2026_05_11.md)

---

## Critical finding

### Finding 1 — Governance enforcement functions are dead code (High)

Verified by grep across all of services/:

- `can_transition` — only defined in campaign_state_machine.py, zero callers
- `decision_engine.decide` — zero callers in services/
- `should_invalidate` — zero callers in services/

All three are only imported in one test file.

A campaign in INVALID state can transition to any other state without hitting the `can_transition` check because nothing calls it.

**Governance signoff Blocking:Yes item 3 upgraded from 'unverified' to CONFIRMED NOT WIRED.**
The state machine exists but is never consulted in any campaign lifecycle path.

---

## Other findings

### Finding 2 — Kill switch defaults to ARMED (Strength)

Missing kill switch file creates it as `{armed: True}`. Trading cannot start from an absent kill switch file. Correct fail-safe default.

### Finding 3 — Kill switch has 5 files, 1 owner (Noted)

Five files documented in source comment. `services/admin/kill_switch.py` is canonical; others delegate. Technical debt, not a safety issue.

### Finding 4 — `live_guard.live_allowed()` chains 3 gates correctly (Strength)

System guard -> kill switch -> `is_live_enabled()`. All fail-closed. `ks.get('armed', True)` defaults to ON when state is absent.

### Finding 5 — `risk_gate_engine` has 4-level graduated response (Strength)

exchange_api_down -> FULL_STOP
block hazard -> HALT_NEW_POSITIONS
warn hazard -> ALLOW_ONLY_REDUCTIONS
no hazard -> ALLOW_TRADING

Well-designed. Exchange API down is hardest stop.

### Finding 6 — `risk_gate_service._write_status` uses write_text (Low)

Same inconsistency as elsewhere. Low risk.

---

## Governance signoff updated status

| Item | Status |
|---|---|
| Campaign validation depth minimal | Still open |
| Terminal invalidation enforcement | Dead code — not wired |
| End-to-end proof invalid blocked | Cannot be proven — never called |

---

## Updated audit map

| File | Depth |
|---|---|
| `services/governance/campaign_state_machine.py` | REVIEWED + caller verified |
| `services/governance/decision_engine.py` | REVIEWED + caller verified |
| `services/governance/invalidation.py` | REVIEWED + caller verified |
| `services/ops/risk_gate_engine.py` | REVIEWED |
| `services/ops/risk_gate_service.py` | SAMPLED |
| `services/admin/kill_switch.py` | REVIEWED |
| `services/admin/live_guard.py` | REVIEWED |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2F
**New High finding:** Governance enforcement dead code
**Next:** Continue auditing services/admin/ or pivot to fix H1/H2/H3/governance wiring
