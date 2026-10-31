# Account-wide cap: synthetic transaction prototype

2026-10-28. Active role ENGINEER. Risk HIGH (financial/concurrency logic).
Current acceptance ACCEPTED_WITH_RISK for the corrected synthetic prototype,
after separate GATE review. Production repair INCOMPLETE. Original submission
and rejection are preserved below and in the archivedv1 artifacts.

Operator approved the stated next step after the separate design review:
synthetic implementation/proof only, not live order-path integration.

## Changed Files

- `scripts/research/synthetic_live_position_cap.py`: isolated callable prototype,
  stdlib only; no production imports, exchange calls, CLI, order routing or DDL.
- `tests/test_synthetic_live_position_cap.py`: invented identities, holdings,
  prices and clocks in disposable SQLite databases. No account inspection.

Reuses the existing live_consumer_state(k,v) table shape and BEGIN IMMEDIATE
pattern. Tests explicitly create/seed their own databases; the prototype never
creates/migrates tables, locates application state or resets a missing row.
No services/storage code imports this new module. Runtime financial gates,
cap value, authenticated clients and collectors are unchanged.

## Model Contract

All figures use exact Fraction/Decimal conversion; bool/float/nonfinite/negative
quantities are refused. Venue/account/base identity defines one shared bucket
across quote pairs. Identity, complete total holdings (not free funds), complete
buy obligations, USD/FX/order bounds and included-fill baselines are explicit
synthetic input assertions, not independently authenticated account evidence.

Within one local transaction the model validates input ages/skew/generation,
reconciles retained obligations, computes conservative held-plus-pending-plus-new
USD exposure and durably reserves an allowed increase. Dynamic clock callbacks
are sampled after acquiring the transaction; fixed invented clocks are permitted
for deterministic fixtures, not claimed to be live clock verification.

Local and observed manual buy obligations survive absent later order rows,
unknown submission/cancellation, reconnection and restart. A coherent explicit
terminal observation is required for release. Matching cumulative fill evidence
prevents counting the same units as both held and pending. Durable tombstones
refuse intent-ID reuse; corrupt/missing state refuses increases, not reset-to-zero.

A validated observation/reconciliation is retained even when the proposed buy is
refused. The refused proposal itself receives no reservation. Invalid evidence
or failed transaction rolls back. This distinction keeps manual obligations
from disappearing just because their first observation accompanied a denied buy.

The reducing-sell branch does not depend on cap/increase evidence or cap-store
availability. It requires separate declared spot/reduction/pending-sell evidence
and adds no over-cap refusal. It does not reserve sells, independently certify
ownership, enforce other gates or promise global no-oversell serialization.
Every answer has execution_authority=false and other_gates_required=true.

Base units are conservatively valued at the larger of the current USD mark and
declared order bound. No stablecoin peg, cost-basis mark or fee savings is inferred.
Cash affordability, fee currency/provider verification and actual order-envelope
enforcement remain external requirements, not new live defaults in this model.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_synthetic_live_position_cap.py
```

Final author run:47passed in0.64seconds. No full-suite result is claimed.
Tests cover the $40+$25vs$50 refusal and exact-cap case, manual pending buys,
cross-pair/account isolation, incomplete pages/FX/identities, invalid numbers,
freshness/future/skew, same-source regressions, partial fills, confirmed/unknown
cancellation, missing/corrupt state, mixed sync/async real transactions, async
wait cancellation, hard process exit before/after commit and failed commit.

Two owned disposable Python child processes use os._exit to exercise SQLite
crash boundaries. Tests never start/stop services or use production databases.
Test-body socket guards are not system-wide network attestation. Cancelling an
async wait can leave its worker completing a durable reservation; it does not
grant submission authority or silently release that reservation.

Initial39cases passed; extending manual-obligation retention exposed a fixture
that reused a generation for changed data (43passed/1failed). The fixture was
corrected to advance explicit generations, not weaken the regression rule.
Expanded44cases then passed1.15s; final47cases include malformed collections and
clock sampling after a real local lock. Source is frozen at the final proof.

`../review_artifacts/synthetic_live_cap_20261028_01/` preserves source.diff and
BINDINGS.json with command/result and reviewed contract/source hashes.
All10public-pilot pins, policy and installed job were verified unchanged.

## Remaining Boundaries

This is not a repaired live cap. Production integration still needs trusted
complete account/order evidence, provider identity/FX/price bounds, durable
submission/fill lifecycle wiring, existing gate compatibility and separate review.
Input completeness assertions cannot certify actual pagination or snapshot
coherence. External manual trades/transfers and market moves remain uncontrolled.

JSON obligations/tombstones have no retention/operator-release tooling here and
can conservatively refuse increases indefinitely. It is a prototype over an
existing table shape, not authorization to create its rows in a live database.
Store damage, remote operational behavior and all possible crash/failure paths
are not certified by these focused cases. No funds, accounts, risk settings,
services/schedules, market experiments, package installs or trading changed.

## Subsequent Separate Review And Correction

V1 was independently REJECTED for SYNTHETIC-CAP-01: missing order rows bypassed
known cumulative-fill baseline validation. The47-test pass above did not detect
that defect. Rejected source/bindings are preserved, not rewritten. See
`synthetic_live_cap_review_20261028.md` for the reproducer, two-line correction,
six new regression cases and current53passed0.66s result. Corrected code remains
READY_FOR_INDEPENDENT_REVIEW pending a focused separate closure disposition.

That separate closure subsequently returned ACCEPTED_WITH_RISK,53passed0.62s,
exactsource/testhashes verified and SYNTHETIC-CAP-01 closed. See the review note's
Actual Separate Closure section. This supersedes the pending-code-review status,
not the production-evidence/integration limits.
