# ES journal transfer of fill-time cost evidence + report-only gate counts (2026-10-09)

ENGINEER: Claude (cloud session), per Damian's decisions (~23:00 UTC). HIGH risk area; READY_FOR_INDEPENDENT_REVIEW.
No campaign restart, config/account change, trading-rule change, deployment, commit or push.

## Changes
1. services/execution/intent_reconciler.py (+60 lines; pre-edit copy kept outside the repo for diffing):
   - _stored_fill_evidence(pdb, fill_id): reads PaperTradingSQLite.get_fill_execution_identity(fill_id); missing
     getter -> missing; read exception -> invalid_storage.
   - _fill_evidence_verdict(): fill_cost_policy_verified becomes True ONLY when the stored evidence status is
     "cost_policy_verified" AND its execution_identity + sha256 equal the order's validated identity. Otherwise
     fill_evidence_status = missing_fill_evidence | invalid_storage | invalid_fill_evidence |
     fill_evidence_identity_mismatch and the flag stays False. An invalid ORDER identity is never rescued.
   - Journal insert remains first-write-wins: a row journaled unverified is never upgraded later.
2. services/control/paper_gate_qualification_report.py: new "fill_cost_verification_report_only" block
   (affects_gate False) with verified/invalid/no-evidence counts for all and for counted evidence fills.
   Summary/counting is unchanged (test asserts identical summary with and without tags).

## Tests (isolated temp SQLite; system python3 3.10)
- tests/test_journal_fill_cost_verification.py (10): verified, missing, sha mismatch, invalid, unknown status,
  corrupt paper storage, invalid order identity, store without getter, engine-produced evidence round trip to a
  verified journal row, engine cost mismatch round trip to unverified.
- tests/test_paper_gate_fill_cost_report_only.py (1).
- Broad selection of every test touching reconciler/paper engine/journal identity/fill identity/gate report:
  393 passed, 1 collection error in tests/test_consumer_locking_and_paths.py (unchanged file; imports datetime.UTC,
  unavailable in the VM's Python 3.10 - environment, not this change). Full suite not run.

## Limits
Verified = agreement with declared paper fee/slippage policy at fill time, not real costs or slippage.
The gate report reads the best-effort fill evidence log; the durable flag lives in the journal. No historical
backfill: fills made before the durable storage slice stay missing_fill_evidence.

## October 16 bounded canonical-evidence correction

Independent GATE review found dictionary equality insufficient: `True == 1`
and `200.0 == 200` let altered stored fill payloads pass while retaining the
original digest. Both cases reproduced through isolated SQLite stores and
persisted a false verified flag. The original transfer slice remained INCOMPLETE.

The reconciler now additionally calls the existing canonical identity validator
on stored fill evidence before setting verification. Two regression cases fail
before this four-line source correction and pass afterward. The five-file
identity/transfer/report selection passed52 tests in0.91s under Python3.12,
using temporary state and databases. No full-suite or running-campaign test.

No historical journal row is upgraded or rewritten; first-write-wins and
report-only gate behavior remain unchanged. Cost-policy agreement is not actual
execution-cost validation, real fill proof or end-to-end Decimal accounting.
No deployment, service restart, trading/config/account or schedule change.
Bounded correction: READY_FOR_INDEPENDENT_REVIEW.

Separate Avicenna GATE re-review October16: ACCEPTED_WITH_RISK for the bounded
local transfer slice; exact canonical-validation P2 closed. Reviewer independently
reproduced52 passing tests in0.81s and both rejection regressions. No material
findings remain in that scope. This does not approve the broader patch series,
running integration, real costs/fills, historical backfill or deployment.
