# Independent quote-policy review

Role: AUDITOR. Environment: VERIFIED_ENV. Acceptance: INCOMPLETE.
Scope: the separate session's cmc_quote_qualification.py and run_cmc_qualified_report.py; no implementation edits.

## Findings

1. High: entry capacity is checked for a different quantity than the registered outcome. The registered view uses the ticker ask, while qualify_capture derives quantity from the later book ask and the qualified wrapper retains the unchanged ticker outcome. Probe: ticker ask 100, book ask 200, displayed ask size 0.75 qualifies using 0.5 units, although the reported $100 ticker entry requires 1 unit. Qualify the same position quantity represented by the outcome, or explicitly model a separate book-price outcome; do not combine the two silently.
2. Medium: caller-supplied exit quantity is not required to be finite and positive. Probe quantity -1 returns QUALIFIED. Reject invalid, zero, negative and boolean quantities without aborting the whole report.
3. Medium: all_ranges_above_zero checks whatever sensitivity entries happen to exist, not the required 7/14/28-day set. Probe with positive registered interval and an empty sensitivity map returns True. Require every named interval and valid finite numeric bounds before reporting the descriptive condition satisfied.

## Verification

`./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_cmc_quote_qualification.py`: 10 passed.
Additional read-only probes reproduced all three findings. No scoring, collection, campaign or original artifact changes.

The wrapper still explicitly blocks primary scoring on the uncertified statistical method. Findings concern trustworthy qualification/reporting, not demonstrated order submission. Repair these bounded cases and add regressions before acceptance; preserve original registered results and accepted thresholds.

## Correction disposition

The three findings above are preserved as historical findings and are superseded for the corrected implementation by separate GATE reviewer Hooke's ACCEPTED_WITH_RISK disposition. Reviewer reported 58 targeted tests and additional mismatch/13-invalid-value probes passing, no blockers. User explicitly supplied INDEPENDENTLY REVIEWED ACCEPTED. Acceptance applies only to these three corrections, not the entire research system. Displayed capacity is not fill proof; statistical certification and profitability remain unverified and primary scoring stays blocked.
