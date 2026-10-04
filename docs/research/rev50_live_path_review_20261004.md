# Rev50 Live-Path Review

Active role: AUDITOR. Scope: independent review of 0037 and 0039. No merge,
deployment, runtime/config/account mutation or production-code repair.

## Finding: P1 - remote order recovery can become local expiry

SHOWN: 0039 excludes an aged intent from expiry when its reason contains a
remote order ID, but recovery occurs after market-quality and symbol-lock
checks. A failed market-quality check overwrites the reason with
`market_quality_block:stale`. On the next turn the remote ID is gone, so the
new TTL branch marks that intent `canceled` and counts it as expired.

The remote exchange order is not canceled by this operation. Local state can
therefore say canceled while a previously submitted order remains outstanding.
This violates the patch's explicit remote-recovery exception. The reason
overwrite is inherited; conversion of this recovery case into a terminal TTL
cancellation is introduced by 0039.

Reproduced on the real ExecutionStore with fake exchange and safety dependencies:
one aged pending intent, reason `remote_id=ord-77`, market quality blocked on
both turns. First turn expired=0; second turn expired=1. Probe expecting no
expiry fails: 1 failed in 0.49s. No real exchange request was made.

Required correction: preserve/recover known remote-order evidence before any
pre-submission block can overwrite it. Confirm both market-quality and
symbol-lock blocked paths and repeated turns. Do not infer that an exchange
order has been canceled from a local TTL disposition.

0039 acceptance state: INCOMPLETE pending this correction and re-review.

## 0037 disposition

No new blocker found in the bounded notional-estimation change. It refuses
unpriceable intents before a daily-cap claim and ignores market-order limit
prices. The purported direct-live-path P1 was overstated: the legacy consumer
has no supported runnable entry point. The canonical consumer already failed
closed downstream on a zero reference price.

Remaining risks: canonical router still receives last/limit rather than the
mid selected for its cap claim; low sell-limit prices can underestimate
realized notional. Neither helper tests nor this review prove venue submission.
This is a bounded review result, not blanket series or deployment approval.

## Verification

VERIFIED_ENV: Python 3.12.10, `/private/tmp/cryptkeep-review48.L67K5O`, rev48
reconstruction with 0038 and 0039 applied. 0038 was applied as a dependency,
not accepted by this review.

Command: `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_consumer_notional_reference_price.py tests/test_live_executor_intent_ttl.py tests/test_live_executor_latency_safety_integration.py tests/test_intent_state_machine_contract.py --tb=short`
Result: 65 passed in 0.97s.

Independent probe stored at
`docs/review_artifacts/shared_submission_review_20261004/rev50_remote_order_probe.py`.
Copy into isolated `tests/test_codex_rev50_review_probe.py`; run the same
interpreter with `-m pytest -q tests/test_codex_rev50_review_probe.py --tb=short`.
Result: 1 failed as above. Full suite, CI, host/process state and live fills
were not checked in this slice. The other seven patches remain unaccepted.
