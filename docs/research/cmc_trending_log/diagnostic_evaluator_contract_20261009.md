# Diagnostic evaluator contract

The separate evaluator composes reviewed structural quote checks, UTC endpoint
selection and registered 1.2% per-side cost arithmetic. It does not alter the
logger, snapshots or collection schedule.

Inputs must identify an already classified daily cohort and capture-time asset
identity. Only PRIMARY_COHORT_CANDIDATE with explicit identity eligibility can
produce a diagnostic return. Missing/invalid endpoints remain missing. Actual
coin and BTC receipt-time offsets are reported, not silently treated as equal.

Operator acknowledged the recommended 60-second maximum absolute coin/BTC
receipt offset at entry and exit. Entry mismatch is explicitly excluded; unmatched
exit observations cannot supply an endpoint. Boundary is inclusive. This capture
alignment policy does not verify underlying quote age or fills.

Every return remains diagnostic, freshness UNVERIFIED and scoring_authorized
false. Structurally valid bid/ask is not proven executable size or fill evidence.
No missing history may be reconstructed from later lists or price similarity.

Outstanding integration: validated raw-snapshot adapter, daily canonicalization,
complete cohort and maturity reporting, explicit capture/provenance qualification,
dependent statistical evaluation, and unattended schedule evidence. Do not call
this a completed primary evaluator or use its returns for promotion.

Verification: 39 focused CMC tests passed. Independent review pending.
Acceptance: READY_FOR_INDEPENDENT_REVIEW.
