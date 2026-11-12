# Independent R8 Source GATE

Date: 2026-11-03. Active role: GATE. Risk: HIGH. Disposition: **REJECTED** for the submitted paper-buy TTL/recovery source scope. Independent reviewer did not produce the sealed changes.

Bot relation: BOT_RULES; runtime configuration was NOT checked. Runner consumer/reconciler/evaluation source rules were checked; actual running-bot behavior is INCOMPLETE.

## Blocking Findings

### P1: A failed legacy-origin persistence write permits a late fill

**SHOWN** by `test_gate_legacy_origin_write_failure_must_not_allow_late_fill` in `test_gate_probes.py`.

An existing `paper_intent_buy` order has no reserved origin and has a recent ledger creation time. Its queue origin is already 110 seconds old. A real SQLite trigger aborts only the metadata update that would preserve the older queue origin. `expire_buy_order` rolls back; `recover_paper_buys` reports `IntegrityError`, but does not prevent further evaluation of that order. Remove the trigger (writes have recovered), advance 11 seconds, and `evaluate_open_orders` expires/checks/fills against the newer ledger creation time. Observed result: **one fill, cash 899.5 rather than 1000, at queue age 121 seconds**.

Relevant paths: `storage/paper_trading_sqlite.py:464-474` (origin update/rollback); `services/execution/paper_buy_lifecycle.py:68-99` (failure only recorded); `services/execution/paper_runner.py:363-365` (consume, then engine evaluation). The engine's own age check does not know the unpersisted queue origin. This is a failure of the submitted original-age/recovery boundary, not a request for a full account watchdog.

Smallest correction proposal: make unsuccessful original-age binding prevent that buy from reaching a fill-capable path until the binding has succeeded, including the evaluator/restart boundary. Do not terminalize uncertain fills or mutate unrelated orders, and do not weaken sell recovery. Reviewer is not prescribing a new watcher or governance system.

### P1: Identity recovery faults do not fence the regular reconciliation path

**SHOWN** by `test_gate_identity_fault_must_block_reconciliation[wrong_link]` and `[wrong_qty]`.

Both real-SQLite cases first produce the exact recovery fault `paper_buy_order_identity_mismatch`. In the same `reconcile_once` call, the normal submitted-row loop ignores that fault, reads the linked order, inserts a journal fill, and marks the buy filled. Observed `(queue status, journal count)` is **('filled', 1)** instead of unresolved with no attributed journal fill. The wrong-link case attributes a BTC/USD order to an ADA/USD intent; the quantity case attributes a two-unit order to a one-unit intent.

Relevant path: `services/execution/intent_reconciler.py:151-164`, then `:210-267`. New recovery detects the contradiction, but its integration does not enforce it downstream. The older linked-order trust path already existed; this review does NOT claim the patch invented that older behavior. It establishes that the new bounded identity guard is ineffective end-to-end for the submitted rows explicitly covered by this review. This is distinct from the separately open R4 quote-symbol fallback.

Smallest correction proposal: require a valid canonical buy receipt before journal/terminal mutation; unresolved identity or missing-canonical evidence must remain unresolved and alerted. Preserve the normal journal-before-terminal success path and existing R12 sell receipt handling.

Cause classification: engineering defect, with a verification/integration gap. The source-completion claims about original-age durability and canonical recovery must remain unaccepted until corrected and independently re-reviewed. No economic conclusion follows.

## Evidence And Commands

Environment: **VERIFIED_ENV** for these repository-local Python/temporary SQLite commands. Tests use isolated temporary state, synthetic prices/router results and mocked alert configuration/dispatch. No network/services/schedules/market-data operations were requested or run. No runtime account or credential inspection was performed.

All pytest invocations used this prefix (run at repository root):

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-r8-independent-20261103 \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider
```

1. Narrow existing current tests: append `tests/test_paper_buy_fill_expiry.py tests/test_paper_buy_lifecycle.py tests/test_paper_buy_before_boundary.py tests/test_paper_exit_atomicity.py --tb=short`. **SHOWN: 306 passed in 4.57s**, exit 0. Includes real SQLite lock-wait clock sampling, both expiry/fill winners, missing-order fence/late insertion, older-origin restart, malformed stored evidence, canonical identity mutation guards, permanent terminals, fresh/expired legacy-open compatibility and R12 atomicity. This is NOT the full repository suite.
2. Preserved before-source: same prefix with `CBP_STATE_DIR=/private/tmp/cbp-r8-independent-before` and additional `CBP_BUY_BEFORE_ROOT=docs/review_artifacts/paper_buy_lifecycle_r8_20261103/before`; append `tests/test_paper_buy_before_boundary.py --tb=short`. **SHOWN: 2 failed in 0.98s**, exit 1, expected counterfactual failures: `test_old_buy_cannot_commit_a_late_fill` actually commits a late fill; `test_committed_order_response_loss_is_not_reported_as_refused` actually produces rejected rather than submitted. Baseline modules loaded from preserved files, no source swapping.
3. Reviewer probes: same prefix with `CBP_STATE_DIR=/private/tmp/cbp-r8-independent-probes`; append `docs/review_artifacts/paper_buy_lifecycle_r8_20261103/independent_review/test_gate_probes.py --tb=short`. **SHOWN final run: 3 failed, 5 passed in 0.48s**, exit 1. Failures are the three stable probe cases above. Passing probes cover pickup age over 60 seconds without premature disposal, queue-read failure without ledger mutation, malformed origin with durable fence, held-row terminal-update refusal with safe ledger fence, and alert-dispatch response-loss remaining throttled/retryable rather than called delivered.

Probe-development disclosure: the first legacy-origin setup used the wall-clock insertion timestamp against an earlier injected clock, so it exercised future-origin rejection rather than the desired update failure. The fixture was corrected to explicitly set a recent, non-future ledger creation time; no production source or existing assertions were changed. The final failure is at the late-fill/accounting assertion after the intended SQLite write failure has been demonstrated. Repeated probe runs are not additive test counts.

The author's `consolidated.txt`/README records **625 passed in 33.90s across eighteen files**. This is an inspected author receipt, not independently rerun and not a full-suite claim. Earlier predecessor receipts are not added to it.

### Seal Verification

**SHOWN:** current twelve source/test hashes match `hashes.json` **12/12**. Before hashes match **12/12**, using the declared flattened `before/` map, HEAD for the two pre-existing fixture files and empty bytes for newly introduced files. Reconstructed unified diff equals `stage.diff` byte-for-byte. Reviewed production source was not edited.

```text
hashes.json sha256 2593b0b5af2e54da535ec7015f38eb5087cb1ee0aece77d0eaf5be1e1ebc84ba
stage.diff  sha256 fee2bb69d8b2597823410998985cbb0c1bc730489a3fda8e1eaab40bf5c1f17d
```

Hash verification used Python `hashlib`/`json`/`pathlib`, loaded seal.py definitions with `runpy.run_path` (not its main writer), read preserved before bytes, read the two fixture baselines with `git show HEAD:<path>`, and rebuilt the diff with `difflib.unified_diff`. No sealing artifacts were regenerated.

## Scope And Handoff

Decision served: whether this frozen R8 paper-buy TTL/recovery patch can be accepted as source, preserving R12. Done when: inspect exact R8 spec and changed APIs, hash-check the seal, test the narrow failure matrix and save independent findings. Budget: one bounded review pass; stop on blocking proof. Earlier-work searches: PROJECT_STATE item 2/omissions; work log R8/R12 entries; artifact README/diff/baselines; branch names. Memory registry search had no matching R8 entry and was not used as evidence.

Inspected: exact R8/R12 specification; artifact README, hashes, seal mapping and full changed hunks; the seven actual production files (`paper_engine`, `paper_runner`, `intent_reconciler`, `paper_buy_policy`, `paper_buy_lifecycle`, both SQLite stores); changed/new test bodies and focused test receipt. Changed APIs inspected include submit's intent origin, fill's injected clock, expiry's expected-order/missing fence contract, queue transitions/events/alert inventory, recovery faults and reconciliation consumption.

- Done: independent narrow source inspection, seal checking, targeted SQLite tests, before-source failure reproduction, new blocking counterexamples and stable re-review probes.
- Partly done: buy lifecycle source acceptance. Happy-path/atomic fence coverage passes, but origin-write uncertainty and identity-fault integration block acceptance.
- Not done: full R8 five-minute account watchdog, deleted-row detection, daily reporting, runtime configuration/state/process/log verification, intended-host cadence/capacity, external alert delivery, deployment/commissioning or full suite. Those were not authorized here and are not certified.

Alert evidence is a dispatch-attempt/result journal plus retry inventory, not an exactly-once external-delivery outbox. Delivery response loss can duplicate external notifications after the throttle; a skipped dispatch is not delivery. No new alert-provider requirement is proposed. Generic queue corruption and arbitrary manual database damage remain outside the proven malformed-origin/read-error cases. Normal paper-fill model limits, R4 and full account watchdog remain open; they are not new blockers asserted by this review.

No sell source was changed by the reviewer. Narrow sell/atomicity regressions passed; this is not a claim that all possible sell behavior was exhaustively proven unchanged.

Assumptions relevant to the probes: a legacy order may exist with later ledger creation than its durable queue origin (the supported compatibility case); a SQLite metadata update may fail and a subsequent call may succeed. The identity probes explicitly introduce contradictory stored order/link evidence rather than claiming such evidence was observed in operation.

Open questions that could change the disposition: can the bounded correction enforce canonical receipts on every buy journal/terminal path; can unresolved original-age persistence block fill paths through recovery and restart; do the three original independent failure cases pass without weakening their assertions or the sell/atomicity tests? New contrary evidence or corrected sealed source would warrant bounded re-review, not a broad restart.

Required re-review names, unchanged:

```text
test_gate_legacy_origin_write_failure_must_not_allow_late_fill
test_gate_identity_fault_must_block_reconciliation[wrong_link]
test_gate_identity_fault_must_block_reconciliation[wrong_qty]
```

Owner/author follow-through: record these two omissions and review disposition in PROJECT_STATE and the existing work log when authorized outside this review-only directory; date corrections to affected completion claims. This GATE wrote only its probe file and this report under `independent_review/`, per explicit ownership restriction, and did not modify shared trackers or reviewed artifacts. No source correction, acceptance by the author, priority change or trading authorization is inferred.

What do I know that could change the owner's decision that I have not yet said?
