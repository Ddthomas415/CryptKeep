# Rev56 Submission Review

Active role: AUDITOR. Scope: new pasted handoffs and initial rev56 review,
prioritizing live retry/TTL safety. Overall acceptance state: INCOMPLETE.

## P1 - created dedupe rows are not proof of an unsent order

SHOWN: 0045 `_submit_may_have_reached_venue` returns false for a dedupe row
marked `created` without a remote order ID. However, `ExchangeClient.submit_order`
persists its claim before calling the venue, and marks submitted only after
receiving a response. An interruption between venue acceptance and that update
leaves the row `created`. The new helper therefore makes a possibly-live order
eligible for local TTL cancellation. A local cancellation does not cancel the
exchange order.

Independent probe uses the supplied fake venue and real ExchangeClient/dedupe
store. It records one accepted request, then raises KeyboardInterrupt to model
interruption outside the Exception handler. The persisted row remains created;
the helper returns false. Probe expecting protection fails. This simulates an
interruption; it is not a demonstrated real exchange incident or a process-kill
test. The underlying crash window is inherited, but 0045's assertion that
created means never sent is unsafe for its new TTL exemption.

Required correction: distinguish proven pre-send/definitively rejected states
from an unresolved created claim. Unknown submission must remain recoverable;
do not infer absence at the venue from this local row. Add interruption and
restart probes. Existing created-row retry behavior also needs disposition,
not merely the TTL check.

0045: INCOMPLETE. No repair implemented in this review.

## Stale handoff claims

- The assertion that all 0031-0045 are unreviewed is superseded by the bounded
  0031-0039 dispositions and human acceptance of the separate remote-ID recovery
  correction. New 0040-0045 are not accepted by those earlier reviews.
- The supplied rev56 series applies original numbered patches; the separate
  accepted recovery correction is not automatically incorporated. 0045 does
  not relocate remote-ID recovery before refusal checks. Integration must
  reconcile that correction explicitly rather than silently omit it.
- Stored disabled live flags are not proof that every running process and
  host is disabled. No fresh process/environment/Hetzner check was performed.
- Full-suite counts in the handoffs remain CLAIMED, not reproduced by this slice.

## Economic decision brief

The three substantive operator choices remain configuration/cohort decisions:
whether obsolete trailing-stop trades qualify for the current candidate,
which current account fee schedule to charge, and whether to apply the strict
campaign market-quality template and observe its cycle. Neither pasted
recommendations nor historical review approval authorizes those mutations.

Do not equate historical recorded 50-bps fees with a newly queried tier, 16-month
trade-frequency arithmetic with a forecast, or fixed-dollar paper seeds with
the user's monthly funding limit. Do not erase historical fills. The obsolete
cohort trades should remain visibly diagnostic pending the scope decision.
No cohort reset, fee change, strict config change or live-path selection made.

## Verification and coverage

VERIFIED_ENV: Python 3.12.10, isolated `/private/tmp/cryptkeep-rev56.3fTGQR`.
All 43 numbered rev56 patches apply to 97c24c8e4, excluding held 0011 and
superseded 0019. This establishes applicability, not tree identity/acceptance.

`python -m pytest -q tests/test_live_submit_ambiguous_classification.py tests/test_live_executor_intent_ttl.py tests/test_codex_rev56_review_probe.py --tb=short`
using the main checkout's absolute venv interpreter: 33 passed, independent
probe failed in 1.12s. Probe preserved at
`docs/review_artifacts/shared_submission_review_20261004/rev56_created_submit_probe.py`.
Copy only into the isolated test tree under the command's probe filename.

Both new pasted attachments read in full; 0045 diff/tests inspected. Earlier
revision families were not exhaustively re-read. New paper/dead-man/crash
patches have targeted verification only, not independent acceptance here.
Targeted five-file slice covering cost-config validation, ledger validation,
fill-quote freshness, collector dead-man and evidence backfill: 72 passed in
1.89s. These tests do not establish scheduling, uninterrupted operation or
correct retirement PnL for recovered evidence.
No full suite, CI, real exchange, scheduler, collector or host proof in this
slice. No main source/config/account mutation, merge, push or deployment.
