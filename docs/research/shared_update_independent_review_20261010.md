# Shared update review

Role: AUDITOR. Status: INCOMPLETE for newly submitted live-fill/position-truth code.
Source: user attachment 7b34c444-7e45-4963-9406-d17ec2697613/Pasted text.txt. Original preserved.

## Findings

1. HIGH: live_reconciler._validated_trade_values validates finite Decimal values then converts to float without validating representability. Probe amount and USD fee `1e1000` returns infinite qty/fee. Thus the finite-output claim is false and invalid numeric accounting evidence can still reach the insertion/emission path. Check converted outputs before returning, or preserve Decimal through a separately reviewed storage contract. This slice is not an end-to-end Decimal migration.
2. MEDIUM: PositionTruthPolicy.from_env permits min_obs1 and min_persist_ms0, below the operator's accepted three-check/15-minute contract. Probe both environment settings yields immediate one-observation policy. Preserve the agreed minimum or explicitly seek a policy-change decision; reject/validate direct policy construction consistently too.
3. MEDIUM evidence overstatement: a USD-like fee with missing cost is still replaced by zero, and absent/non-USD fees are not validated by this helper. The shared statement that every missing/invalid fee is refused is broader than the implementation. Missing fee evidence must not silently become verified zero-cost evidence. A fee-asset conversion contract remains separate.

Verification: `./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_live_reconciler_trade_value_validation.py tests/test_position_truth.py tests/test_position_truth_authority.py`:27 passed. Additional finite-output and policy-override probes reproduced findings1/2. No fixes, orders, runtime policy or scheduling changes in this review.

## Reconciliation with later work

- The pasted quote-policy implementation was subsequently reviewed, corrected and independently accepted with risk for the three bounded fixes; do not rebuild it.
- Warm-up is independently verified, research-only activation is separately recorded/accepted, and the first completed evaluation hour is archived. The pasted 'not started' status is historical.
- V3 synthetic confirmation subsequently failed15/18 null scenarios, with negative aggregation independently verified. No primary statistical scoring gate is certified.
- November8 is the earliest potential first-appearance cohort day under30-day coverage, not an unconditional scoring unlock. Coverage, endpoint maturity and statistical validity still matter.
- 'Only external work remains' is inaccurate: the newly submitted high-risk slices have these local review gaps, remaining Decimal/storage integration is not complete, and final integrated research evidence remains open.
- The reported1034 tests are the author's claimed VM result; this reviewer reproduced27 targeted tests, not that full selection or full repository suite.

Recommendation: treat the local numeric-output and drift-policy gaps as bounded corrective work, preserve paper accounting/campaign state, and do not schedule/deploy these high-risk components until separately reviewed after correction. Continue approved research collection independently. No new blanket hardening lane is authorized by this review.

## Correction handoff

Bounded correction now refuses Decimal-to-float overflow/nonzero underflow and missing cost on explicitly reported USD-like fees. Position policy enforces at least3 observations and900000ms through environment parsing and direct construction.41 targeted tests passed. Separate review requested; READY_FOR_INDEPENDENT_REVIEW. Absent/non-USD fee evidence and end-to-end Decimal migration remain outside this correction, not silently closed.
