# Explicit remote execution quantity treatment

Active role ENGINEER. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.

## Correction and evidence

Remote filled quantity must be explicitly supplied, numeric, finite and
nonnegative. Missing/None, boolean, empty/malformed, nonfinite and negative
values keep the intent accounting-incomplete. No order becomes terminal from
an assumed zero. Explicit numeric zero (including string zero) remains valid.
Unknown quantity can be retried when affirmative venue evidence arrives.
No quantity is inferred from trade history or order size in this correction.

Reproduced in disposable candidate: 41 new parameterized cases yielded
21 failed / 20 passed before the correction. Expanded seven-file slice after
correction: 107 passed, 16 existing datetime warnings, 1.68 seconds.
VERIFIED_ENV: clean environment, null keyring, sandbox network/operator-home
denial except dependency reads, temporary SQLite and mocked venue responses.
Candidate: /private/tmp/cryptkeep-quantity-treatment-20261007/source.
JUnit: /private/tmp/cryptkeep-quantity-treatment-20261007/quantity_results.xml.

Only services/execution/_executor_reconcile.py and its accounting-delivery
regressions changed. The prior frozen candidate remains preserved; its test
file was briefly copied over during reproduction setup then restored from the
recorded snapshot before the revised candidate was tested. No prior acceptance
or evidence identity is being rewritten.

## Limits and handoff

Independent re-review requested from Hume for quantity finding only.
Distinct-event ordering and competing-writer pass abortion remain unresolved;
the overall financial candidate remains REJECTED. Missing quantities stay
pending even if trade rows exist; no completion inference contract added.
No revised full-suite/CI/host/live integration proof. No account/config/process,
credentials/cohort/orders/publication/deployment changes.
Next policy decision concerns loss/profit event ordering, not this numeric fix.

## Independent disposition

Hume independently inspected the bounded diff and JUnit: quantity finding
ACCEPTED, no new finding in that diff. Reviewer executed no tests/imports;
107-case JUnit inspected, pre-fix reproduction not independently rerun.
Overall candidate remains REJECTED for findings 2 and 3. No release approval.
