# R8 paper-buy lifecycle source handoff

Date: 2026-11-03. Active role: ENGINEER. Bot relation: BOT_RULES; runtime configuration, processes and host state not checked. HIGH risk. Author disposition: READY_FOR_INDEPENDENT_REVIEW, self-checked source/synthetic scope only.

**Dated qualification, 2026-11-03:** independent GATE REJECTED the originally sealed candidate.
Three reviewer probes demonstrated two P1 defects: a failed older-origin persistence write allowed a late
fill, and recovery identity faults did not prevent ordinary reconciliation from journaling the wrong order.
The original report/probes are preserved in `independent_review/`; `reviewed_candidate.diff` and
`reviewed_hashes.json` identify that rejected source. The implementation/completion statements below describe
the submitted design, not independent proof. The single bounded correction is now sealed for re-review. The 625-pass
receipt predates it and must not be presented as verification of the corrected source.

**Final separate disposition, 2026-11-03:** correction GATE **ACCEPTED_WITH_RISK**, source only.
The independent reviewer verified all twelve sealed files, passed 356 narrow cases including the eight
unchanged original probes, and passed 21 additional adversarial cases. See
`independent_review/correction_review.md` and `independent_review/test_correction_probes.py`.
Both original P1s are resolved for the corrected seal; the initial rejection remains part of the record.
The author's READY_FOR_INDEPENDENT_REVIEW is not self-approval. No operation or full R8 acceptance follows.

## Outcome And Boundaries

The approved paper buy lifetime is fixed at **120 seconds from intent creation**. The live/shadow default of 300 seconds and its environment override do not widen this paper policy. A stale buy is fenced before disposal, and its original age is retained through routing, resting orders and recovery. Sells remain non-expiring under the existing R12 rules. This is not deployment, an observed paper session, a full R8 watchdog, or proof of trading profitability.

The full failure matrix and task card are in the existing work log; this is an evidence handoff, not another queue. The interrupted part-2 conversation audit did not authorize this implementation. The owner's subsequent "carry out the next steps" resumed the already accepted engineering item 2.

## Implementation

- **DONE, source:** `paper_buy_policy.py` reuses the timestamp parser but enforces age strictly below 120 seconds; invalid/future creation or clock values fail closed. Historical decision `ts` is not a fresh creation timestamp.
- **DONE, source:** the engine passes the queue's immutable origin explicitly. Storage reads canonical order metadata and time after acquiring its write lock. Checks cannot be bypassed with a caller's stale side/metadata, old fill timestamp or wider live TTL setting.
- **DONE, source:** missing-order expiry writes a durable client-identity fence before the queue terminal transition. A concurrent late insertion cannot then fill, even with a refreshed origin. A previously committed fill remains authoritative. Existing-order identity is checked under the ledger lock before any expiry mutation.
- **DONE, source:** recovery persists an older valid queue origin into a legacy resting order, only shortening its lifetime. A restart does not reset the clock. Fresh legacy `open` buys remain supported alongside `new`; their expired fills are blocked too.
- **DONE, corrected source, self-checked:** expiry and fill also read matching creation evidence from the colocated `intent_queue.sqlite` under the paper write lock, via a path-quoted read-only connection with a 0.25-second SQLite lock timeout. All matching origins are checked; an older origin shortens the lifetime and invalid/future evidence cannot be hidden. Failed metadata binding therefore does not remove original-age protection. This explicit store-layout dependency is tested, not inferred from caller metadata alone.
- **DONE, corrected source, self-checked:** missing canonical queue evidence or an unreadable existing queue leaves active buys unresolved, without a fill or terminal disposal. Direct noncanonical paper orders retain their own creation-time fallback when no matching evidence exists. Existing terminal/fence precedence and sells do not depend on queue readability. Canonical means the existing `paper_intent_` namespace; custom legacy client matches are checked too.
- **DONE, corrected source, self-checked:** recovery faults prevent ordinary buy reconciliation. The point of attribution independently requires a matching canonical order and one valid full-fill receipt, including intents arriving after the recovery inventory. A contradictory link/quantity or a filled flag without its actual receipt cannot journal a fill or complete the buy. Recovery faults also retain reason events when the queue permits writing.
- **DONE, source:** a submit exception is treated as commit-uncertain, not proof of refusal. Recovery re-links a durable order and uses normal fill-journal-before-terminal reconciliation. An unwritten submitting buy expires at its deadline; after one minute from pickup it requests an alert, not early disposal.
- **DONE, source:** queue creation, pickup and transition events are append-only. Terminal buys cannot be resurrected by ordinary queue updates. Existing pre-feature history is not reconstructed as observed history.
- **DONE, source:** refusal/expiry reasons and alert dispatch outcomes are retained. Failed/skipped terminal alerts remain eligible for throttled retry. A skipped alert is not external delivery. Old unrelated legacy terminal rows without lifecycle events are not retroactively bulk-alerted.
- **PARTLY DONE, R8 overall:** this closes the buy-age/disposal boundaries being submitted, not all order reconciliation. Account-wide cash/position/fill/fee invariants, deleted-row detection, full daily reporting and host watchdog commissioning remain separate before-start requirements. Existing paper reconciliation/monitor components were inspected for reuse; no second background watcher was created.
- **NOT DONE, operations:** no server/configuration/account/provider/scheduler/collector/trading change, live submission, external alert test, deployment or commissioning. All 25 supported symbols and frozen research rules remain intact.

## Verification And Corrections

Environment: VERIFIED_ENV for isolated Python 3.12/local SQLite test commands. Tests use temporary databases, synthetic router/price/safety inputs and mocked alert delivery; no private trading configuration or market data is evidence here.

- Original interrupted selection: **286 passed / 4 failed**. Three fixtures used January creation times while asserting fresh-buy behavior; one fake engine had no durable ledger. Recovery also terminalized before the older transition counter ran. Creation inputs and durable fixtures were corrected without removing cash/fill/link assertions; actual recovery transitions are counted.
- Resumed focused consumer/recovery selection: **31 passed in 2.25 seconds**, including both response-loss boundaries and new failure cases. A new probe file initially had an import-path collection error; the package-qualified import fixed it before execution. This was not a behavior-test failure or proof of correctness.
- Preserved pre-feature source, same two behavioral probes: **2 failed in 0.42 seconds**, for actual late-fill success and actual premature queue rejection. No production source swapping was used. Set `CBP_BUY_BEFORE_ROOT=docs/review_artifacts/paper_buy_lifecycle_r8_20261103/before` only for that expected-failure check.
- First expanded 18-file selection: **554 passed / 34 failed / 33 errors in 30.11 seconds**. The dominant common cause was the draft storage guard rejecting legacy `open` buys, breaking real-ledger holding setup. That source compatibility defect was corrected, with direct fresh/expired-open cases; the multi-symbol and pending-exit harness assertions were not weakened.
- Corrected consolidated result: **625 passed in 33.90 seconds**, eighteen files, zero failures/errors/skips (`consolidated.txt`). Do not add separate run counts or call the repository suite green.
- The storage worker's earlier 290-case slice and 134-case policy matrix are self-checked predecessor receipts, not substitutes for the final consolidated or independent gate.
- Independent initial GATE: **306 existing cases passed; three reviewer probes failed and five passed**. The actual late fill and wrong attribution supersede the earlier source-completion claims. This rejection is retained in `independent_review/final_review.md`.
- Bounded correction: **485 passed in 18.78 seconds**, fourteen affected test files plus the eight unchanged GATE probes; zero failures/errors/skips, saved in `corrected_affected.txt`. This is the current-source author receipt, not a rerun of all eighteen files or the full suite. The 178 storage cases preserve the previous 138 and add 40. The two added reconciliation cases check inventory-to-attribution identity and missing actual fill receipts. The earlier reconciliation-only 26 and worker 179 counts are overlapping diagnostics, not additional cases.

Corrected seal: `stage.diff` SHA256 `8939cc2767a10e63169366cf47ae9ffa041e31932b6b71ffbd6a3626a379dbc7`;
`hashes.json` SHA256 `04d83c705c81c7980921edb128232f2d9219158336dec74b3beb1f526afbb5e5`.
The unchanged reviewer probe SHA256 is `7d01e5f9928442ed2900b2f897fd5f680b76e8477f68ad2824a4d36dd353c715`.
Source remained frozen through separate correction GATE. Its ACCEPTED_WITH_RISK applies to this seal only;
the author cannot independently approve a changed seal.

The incremental public-source diff and exact twelve source/test hashes are generated by `seal.py` into `stage.diff` and `hashes.json`. `initial_candidate.diff` / `initial_hashes.json` preserve the rejected legacy-status candidate. Production baselines are preserved in `before/`; existing test-fixture baselines come from HEAD, as the seal declares. These do not include runtime state, secrets or the unrelated dirty worktree.

The exact corrected consolidated command was:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-buy-r8-consolidated \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_buy_fill_expiry.py tests/test_paper_buy_lifecycle.py \
  tests/test_paper_buy_before_boundary.py tests/test_paper_runner_decide_order.py \
  tests/test_paper_reconciler_recovery.py tests/test_paper_engine_integration.py \
  tests/test_paper_engine_limit_and_status.py tests/test_paper_runner_lifecycle.py \
  tests/test_paper_exit_atomicity.py tests/test_pending_paper_exit_integration.py \
  tests/test_paper_exit_accounting.py tests/test_paper_trading_sqlite_invariants.py \
  tests/test_paper_fill_identity_durability.py tests/test_intent_queue_integrity.py \
  tests/test_strategy_runtime_runner.py tests/test_runner_multi_symbol_integration.py \
  tests/test_runner_decision_capture.py tests/test_runner_decision_kernel.py --tb=short
```

The focused before/after command is:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-buy-r8-check \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_buy_before_boundary.py --tb=short
```

The current correction command uses the same isolated environment prefix as the eighteen-file command,
but selects its first fourteen files (through `tests/test_intent_queue_integrity.py`) plus
`docs/review_artifacts/paper_buy_lifecycle_r8_20261103/independent_review/test_gate_probes.py`.
Its complete result is preserved in `corrected_affected.txt`; no counts are combined across runs.

## Risks And Required Review

Separate reviewer must work from the source/diff/tests and actual SQLite boundaries: expiry/fill serialization, missing-order fences, original-age durability, committed-response loss, canonical identity, permanent terminal states, reason/alert evidence, preserved sells and unchanged runner accounting. Passing local tests is not acceptance by the author.

No independent financial conclusion is made. The fill model remains full-fill paper accounting with configured costs, not exchange execution. Expiry recognition occurs on service/reconciliation visits; the atomic deadline prevents late fills but is not a wall-clock alert daemon. External alerts can be disabled or fail; synchronous dispatch can delay a consumer, so actual delivery/cadence remain operational evidence. Generic malformed queue records, manual deletion/corruption and other allocation-specific position writers are not certified by this bounded path. WAL/NORMAL durability does not guarantee all power-loss cases.

Open questions that could change the conclusion: a new concrete counterexample against the corrected seal; intended-host latency/capacity and deployed store layout; actual alert configuration/delivery; full R8 watchdog/delete checks; R4 symbol/freshness guards; and the remaining provider/evaluation/start decisions. Queue and ledger are not one cross-database transaction; arbitrary external origin rewrites/deletion after a read are not certified. The known R4 wrong-symbol fallback is not repaired here; no market-valid fill is claimed.

No material capital/risk assumption is needed for this source correction. Applicable timestamps use the existing UTC parser convention; changes to clock/queue provenance or stored evidence can invalidate a recovery and leave it unresolved rather than justify inventing a fill.

What do I know that could change the owner's decision that I have not yet said?

Answer: the initial 625 passing tests missed two real P1 boundary defects. Independent review found them before acceptance, and the corrected 485-case receipt includes its unchanged counterexamples. The fix also makes canonical buy filling depend on readable colocated queue-origin evidence; unavailable evidence now leaves the buy unresolved, which may require operational attention. No operational acceptance follows, and no other material inspected finding is withheld.
