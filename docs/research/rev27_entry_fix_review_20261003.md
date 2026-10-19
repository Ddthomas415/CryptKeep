# Rev27 bounded entry-fix review

AUDITOR / VERIFIED_ENV. 0016: ACCEPTED_WITH_RISK for the bounded entry fix.
Whole-series acceptance remains INCOMPLETE; 0011 remains held.

SHOWN: numbered-patch hash comparison with rev26 adds only 0016.
Inspected production diff, tests and folder23 README. Built isolated tree
/tmp/cryptkeep-rev27.1IcaWx from 97c24c8e4 plus 0001-0010,0012-0016.

No new blocking defect found in 0016. Buy-only direct lookup precedes entry
price/bar/scale/risk-counter writes, covers all four in-flight statuses without
pagination, and refuses unknown storage state. Existing sells follow the old
path. This closes the rev26 four-status entry reproduction.

Correction to handoff wording: a refused buy is not free of all strategy-state
changes. last_action/signal-history writes precede the new check. It writes no
new entry bookkeeping or emitted-buy marker; this distinction explains why
clearing the blocker does not retry the entry until another signal change.
No automatic retry is introduced or authorized by this review.

Not counting an already-in-flight intent as a new risk refusal is appropriate
for this duplicate-prevention gate. Existing risk counters are preserved, not
reset. Blocking buys behind any in-flight strategy sell prevents conflicting
exposure-increasing intent; it does not block the protective sell itself.

## Verification

Python 3.12, PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1:

```sh
python -m pytest -q -p no:cacheprovider tests/test_runner_entry_open_intent.py tests/test_review_pending_statuses.py tests/test_runner_multi_symbol.py tests/test_runner_pending_entry_exposure.py tests/test_runner_exposure_pct.py
```

115 passed in 7.51s, including the unchanged four-status reproduction and
targeted exit cases. Delivered single-symbol differential harness: 76 passed;
compare_traces.py versus supplied trace_0001-0003.json: 75 identical, zero
different, 132 baseline orders. This is not exhaustive exit equivalence: the
external 900-cell matrix was not rerun, nor the full suite or host integration.
External full-suite and mutation counts remain CLAIMED.

## Residual risks and next action

- The normal sell path still uses the truncated queued/submitted scan; the
  new buy lookup is not a duplicate-sell repair or atomic reservation.
- Code inspection confirms exit performance bookkeeping runs before the sell
  scan. External repeated-loss/50-loop-kill figures have not been independently
  reproduced in this pass. Treat that as the next bounded reproduction, not
  already-verified numeric evidence or a reason to change protective exits now.
- A submitted intent is not a reconciled fill. Simply moving loss bookkeeping
  after enqueue would avoid some repeats but would not establish realized PnL.
  The follow-on must identify the intended performance-counter contract and
  ensure one event cannot be counted repeatedly, without losing exit retries.
- Stuck submitting-row recovery, multi-component interleaving and account
  provenance remain unverified. Do not clear historical rows on this approval.

No main production source, configuration, account, service, campaign, GitHub
or deployment changed. Next: reproduce blocked-exit bookkeeping in isolation,
then scope an idempotent correction with separate review.
