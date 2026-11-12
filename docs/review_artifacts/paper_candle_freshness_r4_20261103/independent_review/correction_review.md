# Independent Candle-Guard Correction GATE

Disposition: **ACCEPTED_WITH_RISK** for the corrected, sealed hourly-candle source prerequisite only.
Active role: GATE, separate from implementation author. Risk: HIGH. No new blocker found.
Bot relation: BOT_RULES; actual runtime configuration, activation and host state NOT checked.
Latest task-card/work-log and scoped git status checked: **2026-11-04T02:23:32Z**.
Reporting qualification checked against the saved receipt/work log/git: **2026-11-04T02:25:20Z**.
**Invalid-feed decision-archive completeness is INCOMPLETE; acceptance is not certification of it.**

## Correction Disposition

SHOWN: the P1 in the original `independent_review/README.md` is resolved in these corrected bytes.
The unchanged `test_new_diagnostic_write_crossing_ttl_must_not_fill` now passes: successful diagnostic
I/O advancing the injected clock from buy age 119 to 121 seconds produces expiry, not a financial fill.
The original rejection remains a valid record of its earlier candidate; it is not silently rewritten.

SHOWN: `apply_fill` retains the pre-diagnostic canonical age/fence handling. After successful diagnostic
persistence it resamples `_paper_buy_now(clock)` and re-evaluates the same canonical stored origin,
metadata and queue-origin evidence. Expiry/rejection and the terminal receipt precede candle refusal
or accounting. Valid fills use this refreshed time, including guarded calls with `clock=None`.
The pre-diagnostic expiry/write-failure cases and safe unresolved failure behavior still pass.

The production delta is exactly the second age-check block plus the guarded timestamp condition;
only `storage/paper_trading_sqlite.py` and its boundary test differ from the rejected nine-file candidate.
The test delta appends seven cases; all prior boundary-test content is byte-preserved. No sell, default
policy, strategy, cache, capture or other production implementation changed in this correction.

DONE: bounded latency correction, unchanged original behavior probes, strict 119.999/120/121 cases,
expiry-over-candle-refusal precedence, refreshed explicit/default-clock evidence, preserved old checks,
corrected seal/delta verification and separate source GATE. This accepts the corrected hourly-candle
source prerequisite with the previously disclosed limits, not the initial rejected bytes.

PARTLY DONE: broader R4/item 2. NOT DONE: runtime activation, current publisher/coverage evidence,
quote freshness/completeness and per-fill quote provenance, host/cadence/capacity/delivery,
commissioning, economic validation or permission to operate. Policy source default remains false;
actual profile inactivity is not host-verified, and this review performed no activation.

## Independent Evidence

SHOWN: separate read-only verification checked all nine current and nine before hashes and rebuilt
the complete corrected incremental diff byte-for-byte. Before hashes equal the rejected manifest's
before hashes. Comparing manifests proved exactly two changed current entries. The saved rejected
storage bytes match their old hash; the previous boundary test was reconstructed from its old diff,
matched to its old hash, and is an unchanged prefix of the corrected test. The original probe file,
old diff and old manifest all retain their original hashes. No old literal seal assertion was updated.

```text
corrected stage.diff  2378d23335498e035a5d84eeb12a306c4a62b4c633e52ab9e78d333c6cb8e2ea
corrected hashes.json 5f4c5cd56362be5ac9379ddf12f15d2092a099cca93ca344f2d38ef15c86dbfe
original test_probes  336d03bc651df8fd26c7acaad97bd69c8db495e02fd3de5dde13d493f05ef378
```

VERIFIED_ENV: local Python 3.12, scrubbed environment, synthetic data/clock/gates and temporary SQLite,
plugin autoload disabled, no bytecode/pytest-cache writes. Independently ran from repository root:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-candle-correction-independent \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_candle_fill_boundary.py tests/test_hourly_candle_quality.py \
  docs/review_artifacts/paper_candle_freshness_r4_20261103/independent_review/test_probes.py \
  -k 'not test_nine_file_seal' --tb=short
```

SHOWN: **101 passed, 1 deselected in 1.70s**. This comprises 53 corrected boundary cases, 44 assessor/
cache/engine/pending-sell/archive cases and all four unchanged independent behavior probes. The sole
deselection is the old test pinning literal rejected-candidate hashes; corrected sealing was independently
verified separately, not exempted. No test failure, error or skip was hidden by that explicit selection.

SHOWN: scoped `git diff --check -- storage/paper_trading_sqlite.py` exited 0. Final shell SHA checks
matched corrected diff/manifest, unchanged original probes and both changed files after test execution.

Receipt inspection, not additional independent runs: `rejected_delay_cases.txt` records six failures/
one pass/46 deselected on saved rejected source; `worker_corrected_boundary.txt` records 53 passes;
`corrected_affected.txt` records 480 passes/one deselected in 10.84s. These worker/main receipts remain
attributed self-checks. Their overlapping cases are not added to the independent 101 count. Neither
the 480-case selection, the earlier rejected 839-case selection nor a broad suite was repeated.

## Limits And Closure

Evidence needed: preservation of pre-diagnostic expiry and failure safety, a final canonical logical
fill-time verdict after the newly introduced diagnostic I/O, accurate refreshed evidence time, intact
seal and independent regression proof. The above inspection and passing counterexample satisfy this
bounded correction question. No additional implementation or hardening loop is requested or started.

Inspected: current artifact README qualification, current PROJECT_STATE item 2/O-56/O-57 and latest
task-card additions; corrected/rejected manifests and diffs; saved rejected storage; actual corrected
storage delta and appended boundary tests; unchanged original probes; corrected test execution and
saved worker/main receipts. Seven unchanged candidate files retain the earlier GATE's inspected bytes;
they were hash-compared, not subjected to another broad historical review. The initial independent
report and failing-before evidence remain preserved. Existing dirty-worktree changes were not reverted.

Not inspected: actual runtime/private config, credentials/accounts, live cache/status, host processes,
services, schedules, network/exchange responses, actual I/O latency, delivery or financial outcomes.
This is source/synthetic integration evidence, not a current-bot, host or economic certificate.
Current operation and economic readiness remain **UNVERIFIED / INCOMPLETE**. Prior R8 account-stage
human acceptance was neither reopened nor upgraded to independent technical verification.

Residual limits: the preserved contract is a logical fill-time check, not a guaranteed wall-clock
deadline for physical SQLite commit under arbitrary later I/O stalls. This correction specifically
closes the demonstrated new diagnostic-write interval; it is not a redesign of all accounting/commit
timing. Cache labels remain producer assertions, reads have a size budget rather than an interruptible
deadline, and no cross-filesystem transaction certifies subsequent external cache rewrites. Default-off
policy requires separate approved setup, whose actual state was not inspected.

## Dated Diagnostic Qualification

2026-11-04T02:25:20Z: new main-reported synthetic evidence narrows the earlier capture/diagnostic
claim. SHOWN in the saved public `invalid_input_recording_check.txt`: `quality_ok=false`, while
`capture_result` has `ok=false`, `status=failed`, `error_type=ValueError`, and `synthetic_only=true`.
The receipt was inspected, not independently rerun. Main attributes the input to raw NaN OHLCV and
the failure to the pre-existing strict bar-layout/number validation; the compact receipt does not
itself contain that input or a traceback, so those details remain CLAIMED by main for this supplement.

The buy guard's invalid-candle refusal remains supported by the independent source/tests. However,
whitelisted candle-quality metadata is retained only when the rest of the decision record is valid
and serializable. A rejected raw feed can cause the entire decision archive event to fail, so a
successful assessor verdict/refusal is not proof that its diagnostic event was archived. Complete
R4 invalid-feed diagnostic archiving is **NOT DONE / INCOMPLETE**, not closed by source acceptance.

The bounded guard/TTL correction retains ACCEPTED_WITH_RISK; if acceptance were instead defined as
complete invalid-feed diagnostic-event retention, that broader criterion is INCOMPLETE. No strict
sanitizer is weakened, no R6 redesign is approved, and no new review/implementation loop is opened.
No further test was run for this reporting supplement. Main will record the gap and propose separate
bounded work; this report does not authorize or start it. The prior report's general capture wording
must be read with this dated limitation, not as all-input diagnostic-completeness certification.

Assumptions: disposition applies only to these corrected sealed bytes and the existing logical
fill-time contract. No assumption about actual deployment, account state or measured execution is used.
What could overturn it: changed source/seal or a new concrete within-scope failure of canonical age,
preserved expiry/failure precedence, sell isolation or guarded fill timestamps. Operational acceptance
still requires its separately approved evidence; passing this review does not supply it.

Only this correction report was written. Original report/probes, rejected artifacts, reviewed source,
shared work log and PROJECT_STATE were not edited. The one post-correction source GATE is complete.

What do I know that could change the owner's decision that I have not yet said?

Answer: nothing material from this bounded re-review is withheld. The reproduced late-fill blocker is
resolved at the logical fill boundary, but raw invalid OHLCV can prevent the entire diagnostic archive
event from being recorded. Default-off source acceptance is not diagnostic completeness, activation,
full R4, commissioning, current host safety or evidence of economic advantage.
