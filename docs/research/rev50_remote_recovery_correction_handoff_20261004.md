# Remote Recovery Correction Handoff

Active role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.

Human acceptance, subsequent conversation: the operator replied "approved"
after this correction's handoff. The bounded correction is ACCEPTED. This
supersedes its pending-review state, not the original 0039 defect or whole-series
integration status. Merge, deployment and runtime changes remain unauthorized.

Base: isolated rev48 file tree plus 0038/0039; correction is not applied to the
main checkout. Patch artifact:
`docs/review_artifacts/shared_submission_review_20261004/rev50_remote_recovery_correction.patch`.

Change: move existing remote-ID recovery ahead of TTL, market-quality and
symbol-lock checks. A known-sent intent is marked submitted without a new
exchange call. Those gates still apply to intents with no remote-ID evidence.
This prevents a refusal from erasing remote evidence followed by local expiry.

SHOWN: original failing review probe now passes. Six new fresh/aged cases cover
market-quality refusal, quote-check exceptions and real-store symbol locks,
two turns each, retained remote ID and zero new submissions.

VERIFIED_ENV: isolated temporary candidate; local Python 3.12.10. Command:
`/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_codex_rev50_review_probe.py tests/test_live_executor_intent_ttl.py tests/test_live_executor_latency_safety_integration.py tests/test_intent_state_machine_contract.py --tb=short`
Result: 40 passed in 1.04 seconds. The original probe is stored separately as
`rev50_remote_order_probe.py` alongside the patch; copy it into isolated tests
under the command's probe filename. Do not run against a live state directory.

Required independent proof: inspect the recovery-before-gates ordering,
confirm no new submission or TTL bypass for unsent intents, rerun the probes,
and verify local status-write failure behavior retains recoverable evidence.
The existing remote-ID parser is reused; this correction does not authenticate
remote-ID strings or prove that the exchange accepted/filled an order.

UNVERIFIED: full suite, CI, host/process state, exchange reconciliation.
No push, merge, deployment, config/account change or collector start.
