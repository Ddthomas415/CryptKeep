# Independent R8 Correction GATE

Date: 2026-11-03. Active role: GATE. Risk: HIGH. **ACCEPTED_WITH_RISK for the corrected, sealed paper-buy 120-second TTL/recovery source scope only.** This is independent of the implementation author. No operation or full R8/watchdog acceptance.

Bot relation: BOT_RULES; runtime configuration NOT checked. Paper consumer, evaluator, reconciler and store rules checked in source; actual bot/runtime behavior remains INCOMPLETE.

## Findings And Disposition

**SHOWN:** both original P1 counterexamples are corrected in this seal. The unchanged original eight independent probes pass. No further blocking finding was demonstrated in the bounded correction review. The original rejection and original probe file remain intact; this disposition supersedes that rejection only for the corrected seal below, not retroactively for the rejected candidate.

- Original-age write uncertainty: expiry and fill independently read matching origins from the colocated queue after obtaining the paper ledger write lock. A failed metadata-origin binding cannot remove the older queue origin from the later fill check. The original trigger-induced write-failure probe now passes with no late fill. Author tests also exercise restart/custom clients/reserved and legacy metadata.
- Identity attribution: unresolved buy recovery faults now prevent the ordinary reconciliation loop from processing that intent. A second canonical order/identity check at attribution catches rows absent from the earlier recovery inventory. A filled buy requires one actual full-fill receipt with matching order/quantity and finite positive quantity/price and finite fee. Both original wrong-link and wrong-quantity probes now pass without changing their expectations.
- Additional adversarial checks: twenty-one reviewer-owned cases pass using temporary real stores. These cover old/invalid/future queue origins changed while a ledger writer is waiting, both canonical and custom clients, both expiry and fill paths, missing/unreadable canonical queue evidence without disposal or queue repair, missing canonical order evidence after inventory, partial/zero-price/nonfinite-fee actual receipts, successful custom-client reconciliation, direct noncanonical fallback, and sell independence from an unreadable queue.

The fee/receipt check above is structural attribution evidence, not a check that the economic fee rate, quote provenance or all account-wide cash/holding invariants are correct. Those broader claims are not made.

Failure diagnosis for the rejected candidate remains engineering defect plus integration/verification gaps. Its corrections are demonstrated in this narrow source lane; neither a positive financial result nor operational reliability follows.

## Seal And Delta

**SHOWN:** all twelve current source/test files match the corrected manifest, checked before tests and again after them. All twelve before hashes match the declared saved-production/HEAD-fixture/empty-new-file mapping. Reconstructing the full unified diff from those inputs produces `stage.diff` exactly. The original independent probe hash matches the owner's frozen value.

```text
corrected stage.diff
8939cc2767a10e63169366cf47ae9ffa041e31932b6b71ffbd6a3626a379dbc7
corrected hashes.json
04d83c705c81c7980921edb128232f2d9219158336dec74b3beb1f526afbb5e5
preserved reviewed_candidate.diff
fee2bb69d8b2597823410998985cbb0c1bc730489a3fda8e1eaab40bf5c1f17d
preserved reviewed_hashes.json
2593b0b5af2e54da535ec7015f38eb5087cb1ee0aece77d0eaf5be1e1ebc84ba
unchanged independent_review/test_gate_probes.py
7d01e5f9928442ed2900b2f897fd5f680b76e8477f68ad2824a4d36dd353c715
new independent_review/test_correction_probes.py
aedd0853c5d53012672a0c88b1429c5ba1bea1e45dab3a98b422ec35c34df5b8
```

Compared `reviewed_candidate.diff` with `stage.diff` using `diff -u`, then inspected the actual corrected APIs. Manifest changes are confined to three production files (`services/execution/intent_reconciler.py`, `services/execution/paper_buy_lifecycle.py`, `storage/paper_trading_sqlite.py`) and two tests (`tests/test_paper_buy_fill_expiry.py`, `tests/test_paper_buy_lifecycle.py`). The other seven sealed file hashes are unchanged.

The reconciliation correction consumes faults, validates canonical identity again and validates the full-fill receipt before journal/terminal attribution. Recovery adds durable error events when queue writes permit. The storage correction performs a URI-quoted, read-only lookup of all matching queue origins, with a 0.25-second SQLite lock timeout; known invalid/future origins cannot be hidden by a valid newer origin. Missing canonical evidence or unreadable existing queue evidence blocks the active buy without terminalizing it. Existing terminal/fence precedence, noncanonical unmatched fallback and sell paths are preserved.

Constructor/source layout inspected: both queue and ledger define their database paths under the same `data_dir()`; the ledger lookup resolves `intent_queue.sqlite` beside its own DB. The new independent probes use those actual constructors in isolated state, not only a synthetic three-column queue table. This supports the source-layout dependency; no runtime layout was inspected.

Hash verification used Python hashlib/json/pathlib, the existing seal definitions loaded via `runpy.run_path` without running its main writer, `git show HEAD:<path>` for the two declared original fixture baselines, and difflib to reconstruct the diff. No reviewed artifact was resealed or edited.

## Independent Commands And Results

Environment: **VERIFIED_ENV** for repository-local Python and isolated temporary SQLite. Working directory: `/Users/baitus/Downloads/crypto-bot-pro`. Prices, router permissions and alert configuration/dispatch were synthetic or mocked. No network, service, schedule, account, credential, private runtime configuration or market-data operation was performed.

Exact narrow command:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-r8-correction-gate \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  docs/review_artifacts/paper_buy_lifecycle_r8_20261103/independent_review/test_gate_probes.py \
  tests/test_paper_buy_fill_expiry.py tests/test_paper_buy_lifecycle.py \
  tests/test_paper_buy_before_boundary.py tests/test_paper_exit_atomicity.py --tb=short
```

**SHOWN: 356 passed in 6.97s**, exit 0, zero failures/errors/skips. Includes all eight unchanged original GATE cases, current buy policy/storage/lifecycle tests, original current-source before-boundary regressions, and the R12 atomicity file. Covers real SQLite expiry/fill races and ledger-first fences, terminal permanence, fresh/expired legacy `open`, failed writes, response loss and preserved sells. No full-suite inference.

Exact additional independent command:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-r8-correction-independent-probes \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  docs/review_artifacts/paper_buy_lifecycle_r8_20261103/independent_review/test_correction_probes.py --tb=short
```

**SHOWN: 21 passed in 0.89s**, exit 0, zero failures/errors/skips. No harness correction or test assertion change was needed. The lock-wait cases change queue evidence before releasing the paper writer, then verify that expiry/fill observes that evidence and preserves cash/fills.

Inspected author evidence: `corrected_affected.txt` records **485 passed in 18.78s**, not independently rerun here. The earlier eighteen-file **625 passed in 33.90s** receipt predates this correction. Neither receipt is a repository full suite, and overlapping counts are not added.

## Scope, Risks And Handoff

Decision served: accept or reject the single bounded correction against the original two P1s. Acceptance proof required: unchanged original counterexamples pass, correction delta/seal match, narrow buy/R12 regressions pass, and independent checks find no blocker in queue-origin or attribution boundaries. Done: those source checks. Budget: one bounded re-review; no new architecture or broad suite. Prior evidence searched/read: PROJECT_STATE O-51/O-52/O-53 and its dated correction; handoff qualification; preserved rejected diff/hashes; initial independent report/probes; exact R8 spec. Memory registry search had no matching R8 entry and was not used as evidence.

**Done:** corrected source disposition, immutable-probe reproduction, seal verification, independent adversarial checks and this report. **Partly done:** overall R8, because only the buy TTL/recovery boundary is accepted. **Not done:** runtime or operational commissioning, full watchdog/account reconciliation/deletion checks, intended-host performance, full suite or external alert delivery.

Residual risks and limits:

- Active canonical buy fills now require readable matching queue-origin evidence. Missing/unreadable evidence leaves them unresolved rather than guessing, and may require operational attention. The measured tests do not establish intended-host latency/capacity; read-only queue lock waits occur while holding the paper write lock.
- Queue and ledger reads are not a cross-database transaction. Supported queue upserts preserve original creation time; arbitrary external rewrites/deletion after a read, manual corruption, forged provenance and full deleted-row detection are not certified by this correction. The lock-wait probes establish read placement and failure behavior, not protection against every external database writer.
- Noncanonical direct orders intentionally retain their own-age fallback when there is no matching queue evidence. An unreadable existing queue blocks their active buys conservatively; sells have no new queue-origin dependency. Terminal/fence precedence remains earlier than lookup. These are source policies, not current-process observations.
- Alert evidence remains throttled dispatch-attempt/result retention and retry eligibility, not exactly-once external delivery. Response-loss notifications can repeat. Full watcher cadence/daily reports/account invariants, R4 wrong-symbol quote fallback, ordinary paper fill-model limits and other before-start requirements remain open, not new blockers inside this patch.

What was not inspected: current runtime configuration, processes, server layout/logs, private accounts, credentials, live data or real fills. These omissions prevent any claim that an operating bot uses this code correctly, that alerts reach the owner, that the full simulation is commissioned, or that a strategy is worth running live. No configuration, source, sell policy, shared tracker or original review artifact was changed by this reviewer.

What could overturn this disposition: a concrete counterexample against the corrected sealed source within the accepted boundaries; a different deployed store layout or unsupported writer violating the source assumptions; or a source/hash change. The original failed case names remain unchanged for any bounded subsequent regression check:

```text
test_gate_legacy_origin_write_failure_must_not_allow_late_fill
test_gate_identity_fault_must_block_reconciliation[wrong_link]
test_gate_identity_fault_must_block_reconciliation[wrong_qty]
```

Current objective ends at this narrow independent source GATE. The implementation author's READY_FOR_INDEPENDENT_REVIEW is not self-approval; the source disposition above is the separate review result. Owner/author may record it in the existing shared state/work log; this review was restricted to its own directory and does not authorize operation or further work.

What do I know that could change the owner's decision that I have not yet said?
