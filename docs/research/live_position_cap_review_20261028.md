# Live position-cap review: selected gate gap confirmed

2026-10-28. Active role AUDITOR. Finding SHOWN; remediation INCOMPLETE.
Read-only production inspection and synthetic in-memory probe, no live operation.

## Finding

P1: `LiveRiskGates.check_live` does not enforce the declared position cap. The
class parses/stores `max_position_notional_usd` but the decision method never
reads it. The inspected submit caller supplies qty/price/symbol, not side or
existing position. This confirms the narrow central claim of Cowork fix4 against
current local source, not every operational consequence claimed in the handoff.

Source references:
- `services/risk/live_risk_gates.py:23`: position-limit field.
- `services/risk/live_risk_gates.py:40`: loading/parsing that field.
- `services/risk/live_risk_gates.py:167`: gate checks kill, per-order size,
  daily count and realized loss, then returns OK without a position check.
- `services/execution/_executor_submit.py:405`: supplied intent lacks side
  and position evidence at this gate call.

## Reproduction And Exact Scope

Command (VERIFIED_ENV; stdlib-only isolated Python):

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -I -S -B docs/review_artifacts/ed002_live_cap_review_20261028/probe.py
```

The probe parses source AST, executes the unchanged LiveRiskGates class methods
and actual decimal helpers only, removes the dataclass decorator and supplies
invented instance attributes/DB/file-kill state. It does not import production
modules, instantiate a real store, load runtime configs, fetch balances, access
credentials, create an exchange client or submit orders. Source bytes are checked
unchanged before/after. This is selected-method proof, not module/integration proof.

With a synthetic $50 position limit and $25 per-order limit:

- Existing position $40 plus buy $25: gate returns OK; full fill would be $65.
- Existing position $50 plus buy $25: OK; full fill would be $75.
- Unknown existing position plus buy $25: OK; no position-read requirement.
- Existing position $65 minus sell $25: OK under the unchanged other limits.
- Buy $26: correctly blocked by the per-order limit (positive control).
- Synthetic daily counts0-4 each allow a $25 buy; count5 is blocked. Conditional
  on full fills and no other restrictions, five buys would total $125, not $50.
  No such fills occurred in this probe; its sixth proposed buy is blocked.
- Kill-switch positive control blocks. This is not an always-allow stub.

The gate AST contains no position-cap reference; inspected caller keys are
exactly qty/price/symbol. Saved source hashes and results are beside the probe.
The existing live-risk test file was read; the full pytest file was not run or
changed. Its presence is not coverage for an unenforced position rule.

## Limits And Recommended Treatment

UNVERIFIED: remote/live/armed state, actual configured/account holdings, pending
exchange buys, and whether another downstream check prevents a specific order.
No claim that all live protections fail or a real excess/loss occurred. The
ExchangeClient path inspected is labelled legacy/non-preferred; do not infer it
is the currently deployed path. The preferred adapter must be traced before a fix.

Recommended fix scope, not implemented: carry order side and trusted position
evidence into the shared gate; refuse exposure-increasing buys if evidence is
missing or the fee-inclusive/exposure contract would breach the cap, preserving
reducing exits and all existing unrelated limits. Include in-flight reservations,
currency/price/fee valuation and both caller paths in the contract; do not merely
add a caller-provided balance field that could be stale or spoofed. Balance paging
fix1 may affect the trusted source, but neither change is authorized here.

The authoritative position source and reservation/concurrency contract remain
undecided; a production patch must not guess them. No live arming or private probe
is justified by this report. The public ED-002 collector does not use this gate;
reviewing it did not modify any of the pilot's ten pinned source inputs.

Next: scoped treatment design/source trace and explicit code-change authority,
then targeted regression and independent/human high-risk review. Finding SHOWN;
production repair/integration INCOMPLETE. The first scheduled collector slot
remains separately pending, not forced or treated as passed by this audit.
