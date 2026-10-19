# Bounded Specialist Execution Review

Date: 2026-10-06. Active role: AUDITOR. Read-only review; only this requested report was written.

Objective: independently review patches 0047, 0055, 0056, 0058, 0059, 0062, 0065, 0069, 0070, 0071 and 0072, focusing on financial accounting and live fail-open contracts.

Bundle root: `/private/tmp/cryptkeep-rev87-review-20261005/cryptkeep_review_bundle_2026-10-02` (B below).
Assembled source root: `/private/tmp/cryptkeep-rev87-candidate-20261005` (S below).
All source line references below refer to S, not the working repository or historical patch line numbers.

Acceptance state: **REJECTED** for unconditional acceptance of this combined execution slice. The bounded static review is complete, but the findings below need correction or explicit independent risk disposition. This is not a whole-bundle, deployment, or production-readiness verdict.

## Findings

### F1 [P1] Partial trade-list coverage can silently close an under-accounted order (0058)

**SHOWN, static control flow:** `S/services/execution/_executor_reconcile.py:451-452` sets the remainder to zero whenever any matching trade quantity was returned. It does not require that recorded quantity equals the venue's filled quantity before `:507` marks the intent filled. Quantity is added to `trade_filled_qty` at `:361` even for already-known trades or trades without an ID (`:362-364`).

Concrete case: an earlier pass accounted 0.4 BTC; the venue later reports closed/filled=1.0, but a limited, delayed or incomplete trade query returns only the old 0.4 trade. That trade is skipped as known, the remainder is forced to zero, and the intent becomes terminal with 0.6 BTC missing from position/risk accounting. A nonempty incomplete list is enough; no exception is required. The added tests cover a complete list or a completely unavailable list, not this case.

Required proof next: a regression with closed filled=1.0 and only the previously recorded 0.4 trade returned; terminal status must wait for full accounted coverage or a correctly valued remainder.

### F2 [P1] A failed fill on a canceled order is still made terminal (0058)

**SHOWN, static control flow:** `_executor_reconcile.py:399-401` sets `emit_failed` when canonical accounting refuses a trade, but only the closed/filled branch checks it (`:441-445`). The canceled/cancelled/rejected/expired branch at `:513-518` unconditionally makes the intent canceled and the dedupe row terminal.

Concrete case: a limit order partially fills, then is canceled; the trade's sink call fails transiently. No execution fill row is written, yet the intent leaves the tracked statuses (`:237-243`), so subsequent passes cannot retry that fill. The patch's advertised account-before-terminal guarantee does not cover a common terminal order outcome. This is a retained gap in the modified reconciliation contract, not a claim that 0058 introduced cancellation itself.

Required proof next: canceled order with a nonzero trade, first sink refusal, subsequent recovery; the fill must be retried before the intent stops being tracked.

### F3 [P2] Synthetic remainder uses whole-order average and whole-order PnL (0058)

**SHOWN, static arithmetic:** `_executor_reconcile.py:459-477` emits the remaining quantity at the whole-order average and copies the whole order's reported realized PnL. `storage/execution_store_sqlite.py:195-203` returns quantity and raw fee totals, but no recorded execution value or PnL totals.

Concrete price case: 0.4 BTC recorded at $100, final filled=1.0 with average=$160, and no trade rows returned. Actual remaining execution value is $120, giving remainder price=$200. The code emits 0.6 at $160, recording $136 total instead of $160 and understating the buy cost basis by $24. For a sell with earlier trade-level realized PnL, copying total order PnL also counts that earlier PnL again. Tests use a constant price and no reported PnL, hiding both errors. Raw fees are also summed without currency grouping, so subtracting them from an order-level fee requires an unproven same-currency contract.

Required proof next: changing-price partial fill plus fallback, and separately an order-level aggregate realized PnL after trade-level PnL was already applied. Reconcile execution value and PnL deltas, not only quantity.

### F4 [P2] Failure to read recorded totals is treated as no prior fills (0058)

**SHOWN, static control flow:** `_executor_reconcile.py:149-157` returns `(0.0, 0.0)` for a totals read exception. The caller at `:451-465` then emits the entire filled quantity with a new synthetic fill ID, although previous trade IDs may already have been accounted.

Concrete case: a transient SQLite read failure after a prior partial fill, followed by a successful sink/store write, adds the whole order on top of the prior partial fill. Canonical idempotency cannot deduplicate the new `order:<id>:closed` against the prior trade ID. Unknown accounting state must not mean zero accounting state.

Required proof next: inject a totals read failure after a recorded partial fill; no synthetic fill or terminal transition may occur until totals are readable.

### F5 [P1] Symbol-loss update failure becomes permanently non-retryable (0059, 0070)

**SHOWN, static commit ordering:** `services/journal/fill_sink.py:148-155` applies daily risk before attempting the symbol-loss update. The new condition at `:183` permits that update only when daily risk was applied in this invocation. Exceptions from constructing the execution store, reading lock settings or writing the lock are logged and swallowed at `:206-209`; the sink returns success and writes no order-block flag for this failure.

Concrete case: the third losing close commits daily risk, then `increment_symbol_loss` fails. The symbol remains below the lock threshold and the reconciler treats the fill as accounted. Offering the same fill again returns daily-risk already-applied, so the new guard permanently skips its missing loss-count update. The boundary added by 0070 reads the successfully readable but missing/old lock (`place_order.py:621-627`) and permits another buy. A process interruption between the two commits has the same missing-update issue.

Required proof next: fail the loss-counter write after daily-risk commit, restore storage, replay the fill; either an independently idempotent lock update completes or new entries remain blocked. Daily-risk application is not sufficient proof of symbol-lock application.

### F6 [P1] Risk repair bypasses the consecutive-loss control before clearing its block (0065 with 0059/0070)

**SHOWN, cross-patch control flow:** `scripts/repair_risk_sink_failed.py:81-104` repairs a missing fill by calling `RiskDailyDB.apply_fill_once` directly. It never performs the symbol-loss update. Once the ledger is complete, `:241-260` can clear the flag. Later delivery through the sink cannot repair the loss count because `fill_sink.py:183` requires a newly applied daily-risk row.

Concrete case: two losing closes have been counted. A third close is journaled and its position updated, but its daily-risk write fails and raises the block. Running the repair successfully records that third loss in daily risk and clears the block without incrementing the symbol count. A subsequent buy passes the loss-lock boundary. This is a normal supported repair path, not misuse of `--force-clear`.

Required proof next: a real sink/repair/boundary test with two counted losses and a third daily-risk write failure; repair must leave the third-loss lock enforced before lifting the block.

### F7 [P1] Verified repair can delete a newer, unverified failure flag (0065)

**SHOWN, static interleaving:** `repair_risk_sink_failed.py:206` reads the flag once; `:241` verifies that captured payload; `:260` unlinks the current pathname without checking its generation or excluding concurrent writers. The sink atomically replaces that pathname when a new failure occurs (`fill_sink.py:30-39`).

Concrete interleaving: repair verifies old fill A and completes its final missing-fill query; a reconciler then replaces the flag with an unjournaled fill B failure; repair writes its A-clear event and deletes B's flag. B need not appear in the missing-fill join because it never reached the journal. New orders are now unblocked although the newest cause was never verified. This is a retained concurrency gap in the newly strengthened clear contract. No evidence was obtained that operational tooling enforces writer quiescence.

Required proof next: coordinate a replacement between verification and removal and prove the new flag survives. Use a shared exclusion/generation-aware protocol, or an enforced and documented quiescent repair precondition; a simple unchecked reread is not atomic exclusion.

### F8 [P2] Disarm permits orders before its required audit event succeeds (0062)

**SHOWN, static publication ordering:** `scripts/killswitch.py:81` publishes `armed=False`; only afterward does `:82-88` write the required event. It rearms on failure at `:91`. `services/admin/kill_switch.py:43-47` writes the state directly; `place_order.py:653-656` reads the kill gate before submission.

Concrete case: otherwise-enabled/armed consumer observes the disarmed file while the journal write is blocked or before it fails and sends an order. Rearming cannot undo that order. A process interruption after publishing disarm also leaves the switch released with no required record. The new test verifies only final state after a synchronous event failure, not the live observer window. The previous CLI already lacked auditing; this is a gap in the new required-record guarantee, not a newly introduced release capability.

Required proof next: block/fail audit publication while a second observer checks order permission. Release must not become effective until a durable authorization record exists, with appropriate transition/completion event semantics.

## Other Scoped Results And Limits

- **SHOWN:** 0047 changes cache quality but still intentionally returns `ok=True` for unmeasured or unconfirmed time (`clock_sanity.py:165-202`); the consumer gates only on `ok` (`live_intent_consumer.py:409-410`). Its new tests explicitly pin this. This is a disclosed fail-open policy limitation requiring operator risk disposition, not a new cache regression.
- **SHOWN:** 0055 rejects explicit contract notation and negative market metadata, but missing metadata passes (`place_order.py:585-588`). This is deny-known-nonspot, not positive spot attestation. No current reachable derivatives route was established in this bounded review.
- **SHOWN:** 0056 refuses missing/unreadable models and non-finite score/probability/threshold cases; router exception handling also refuses when enabled. Model schema completeness and finite-but-out-of-range thresholds remain outside the demonstrated validation contract. No additional independently substantiated live-path finding is asserted here.
- **SHOWN:** 0069 restores a snapshot on an audited-save failure and distinguishes incomplete rollback. Its snapshot reader conflates read failure and absence (`config_editor.py:98-103`), and restoring `None` deletes the file (`:85-90`). Abort on unavailable snapshots is advisable; reachability of a transient read failure followed by writable restoration was not executed here. Concurrent config edits and save/restore atomicity were not proven.
- **SHOWN:** 0070 permits sells while refusing locked/unreadable-lock buys. The operator's approval of that policy, string-key consistency across all venue symbol mappings, and legacy-path exit behavior remain **UNVERIFIED**.
- **SHOWN:** 0071/0072 distinguish the explicit boundary refusal and unbuilt adapter from submit ambiguity and return the consumer claim. Market-rule errors are prefixed in the assembled boundary (`place_order.py:736-758`), so the superseded 0071 README statement is not a current defect. Claim release is a separate aggregate-counter transaction, not an intent-keyed durable refund; failures after terminal-state publication can retain budget. No recovery guarantee was established.
- **CLAIMED:** README/guide test counts and previous-code failure counts. Earlier README baseline-failure assertions are corrected by the guide. None was adopted as this review's test result.
- **UNVERIFIED:** current live enablement, deployed path ownership, actual venue error/fee/trade pagination semantics, persistent operator config, production integration, economic validity, and full-suite status.

## Exact Reading Coverage

Every file in the following table was fully read, including all test and documentation hunks in the full patches. Prefix every table path with B. Truncated combined command outputs were supplemented by rereads; they were not treated as complete reads on their own. The guide was fully read at `B/REVIEW_GUIDE_0031_0075.md`. No root README exists in the supplied root listing; the requested per-patch READMEs are listed here.

| Patch | Directory | Fully Read Files In That Directory |
|---|---|---|
| 0047 | 55_clock_measurement_quality | README.txt; production_files_only.diff; 0047-fix-a-clock-measurement-is-cached-as-OK-only-when-it.patch |
| 0055 | 63_spot_only_order_boundary | README.txt; production_files_only.diff; 0055-fix-execution-order-boundary-refuses-non-spot-markets.patch |
| 0056 | 64_order_gates_cannot_pass_blind | README.txt; production_files_only.diff; 0056-fix-router-enabled-ai-and-probability-gates-refuse.patch |
| 0058 | 66_executor_reconcile_partial_fills | README.txt; production_files_only.diff; 0058-fix-executor-reconcile-partially-filled-orders-to-completion.patch |
| 0059 | 67_fill_sink_loss_lock_and_risk_write | README.txt; production_files_only.diff; 0059-fix-fill-sink-loss-lock-counts-closing-fills-once.patch |
| 0062 | 70_killswitch_cli_records | README.txt; production_files_only.diff; 0062-fix-killswitch-the-kill-switch-command-records-its-changes.patch |
| 0065 | 73_risk_sink_flag_clear | README.txt; production_files_only.diff; 0065-fix-repair-clear-the-risk-sink-order-block-only-for-.patch |
| 0069 | 77_live_enable_rollback | README.txt; production_files_only.diff; 0069-fix-live-enable-a-failed-enable-really-restores-the-.patch |
| 0070 | 78_symbol_lock_at_order_boundary | README.txt; production_files_only.diff; 0070-fix-place-order-the-live-order-boundary-refuses-buys.patch |
| 0071 | 79_boundary_refusal_in_consumer | README.txt; production_files_only.diff; 0071-fix-live-consumer-an-order-the-boundary-declined-is-.patch |
| 0072 | 80_adapter_unavailable_in_consumer | README.txt; production_files_only.diff; 0072-fix-live-consumer-an-intent-whose-exchange-adapter-c.patch |

Additional assembled-source reads, all prefixed with S:

| File | Coverage |
|---|---|
| services/journal/fill_sink.py | Full file, lines 1-252 |
| services/execution/_executor_reconcile.py | Full file, lines 1-636 |
| scripts/repair_risk_sink_failed.py | Full file, lines 1-265 |
| services/execution/clock_sanity.py | Full file, lines 1-204 |
| services/admin/kill_switch.py | Full file, lines 1-57 |
| services/execution/live_enable.py | Full file, lines 1-125 |
| services/admin/live_enable_wizard.py | Full file, lines 1-213 |
| scripts/killswitch.py | Full file, lines 1-108 |
| services/ai_engine/model.py | Full file |
| services/ai_engine/signal_service.py | Full file |
| services/feature_gate.py | Full file |
| services/markets/fetch_coinbase_ccxt.py | Full file |
| services/admin/config_editor.py | Lines 1-240 only |
| storage/execution_store_sqlite.py | Lines 190-335 only |
| services/risk/risk_daily.py | Lines 200-330 only |
| services/execution/place_order.py | Lines 550-816 only |
| services/execution/live_intent_consumer.py | Lines 115-182 and 300-705 only |
| storage/live_intent_queue_sqlite.py | Lines 450-611 only |
| services/execution/live_exchange_adapter.py | Lines 1-140 only; symbol mapping, constructor and submit path |
| services/live_router/router.py | Lines 90-178 only; AI/probability gate and exception handling |

The selected patches' test hunks were fully read; entire pre-existing test files, unmodified fixture dependencies, unrelated patches, MANIFEST.txt, REVIEW_HANDOFF.md, embedded documents and deployment/runtime artifacts were not fully read. Directory/path inventories and a memory keyword search were discovery only, not review evidence. No relevant prior-memory finding was used.

## Verification And Handoff

Command confidence: **VERIFIED_ENV** for local read-only file inspection and the requested report path, which were observed directly. No runtime imports, tests, builds, simulations, order operations, external calls or persistent configuration changes were performed. **Tests were not run**, including the full suite. Static examples above are logical counterexamples, not executed reproductions; actual production occurrence is **UNVERIFIED**.

Assumptions: at most two material assumptions, both explicit scenario preconditions rather than claims about deployment: (1) the reviewed live paths may be used with live otherwise authorized; (2) storage/venue calls may fail or yield partial history, as their existing error handling already anticipates. Operational writer quiescence was not assumed.

Highest-leverage next action: correct and independently verify the cross-patch fill-accounting completion contract, including loss-lock application and repair. Preserve the entry blocks until all required accounting effects are durably proven; do not solve these findings by disabling the controls. The implementer should add focused regressions described above and obtain separate high-risk review. No source change or acceptance was performed by this auditor.
