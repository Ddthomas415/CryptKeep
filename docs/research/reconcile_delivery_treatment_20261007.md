# Durable reconciliation accounting delivery

Active role: ENGINEER. Risk HIGH. State READY_FOR_INDEPENDENT_REVIEW.

## Objective and dependency

Continue the approved accounting treatment after human acceptance of the
symbol-loss cutover. Prevent a failed accounting delivery from disappearing
behind a local fill record or terminal order status. No deployment authorized.

## Changes

- Local fill and canonical delivery payload are persisted atomically. Delivery
  evidence is retained after completion, with identity/conflict constraints.
- Retry pending deliveries before fetching new exchange evidence. A successful
  sink response is required before recording completion; failure of either
  delivery or its completion marker retains the pending record.
- Terminal filled/canceled status requires completed delivery records and
  recorded quantity matching the exchange's cumulative filled quantity.
  Unknown local coverage is not treated as zero.
- Continue polling partially_filled intents. Incomplete trade history cannot
  terminalize a partially accounted order. A whole-order synthetic fill is
  allowed only when no quantity is already recorded; otherwise the gap stays
  explicit rather than double-counting the entire cumulative quantity.
- Reconciliation returns ok=false and accounting_incomplete intent IDs where
  completion is unresolved. It does not pretend a failed sink was successful.

## Verification

VERIFIED_ENV: isolated pytest outside repository conftest, clean environment,
temporary SQLite and state paths, fake exchange/session, no network or order
submission. Final slice: 31 passed in 0.61 seconds; existing datetime warnings.
Nine reconciliation tests plus the 22 prerequisite/regression tests cover:
failed closed/canceled delivery, restart without trade history, partial-order
continuation and missing history, synthetic retry, legacy unknown coverage,
completion-marker failure, transactional rollback, coverage-read failure,
and real canonical sink retry without duplicate symbol-loss count.

Command: .venv/bin/python -B -m pytest -q --confcutdir TEMP_ROOT followed by
the four copied test files (test_reconcile_accounting_delivery.py,
test_symbol_loss_fill_once.py, test_fill_sink_live_position_integration.py,
test_fill_sink_logging.py). Clean subprocess runner used explicit temporary
CBP_STATE_DIR, EXEC_DB_PATH and CBP_DB_PATH; no inherited operator settings.

## Remaining risks and scope

- No full suite, public-facade compatibility suite, CI, host deployment or
  genuine exchange fault/crash/power-loss proof. Existing reconcile doubles
  without the new storage contract require compatibility verification.
- Legacy local fills without durable completion evidence remain incomplete;
  the approved counter cutover does not certify their full accounting.
- Missing partial history is held, not reconstructed. Incremental cumulative
  VWAP/fee fallback and fee-asset conversion are not repaired by this patch.
- This path does not resolve ambiguous submission/acknowledgement defects,
  independent live queue/reconciler implementations, flag-clear concurrency,
  loss-event chronological ordering across intents or bounded polling limits.
- An add-fill/storage failure can still interrupt the reconciliation call;
  no successful completion or terminal transition is inferred from it.
- Storage migration and stopping old-version writers need explicit deployment
  authorization. Operator databases/configs/accounts/processes were untouched.

Independent review must inspect the combined storage/reconciler diff and
failure tests before release. The prior reviewer returned a usage-limit error;
no completed independent review is claimed for this new change.

## Human acceptance and public-interface compatibility checkpoint

The user approved the 31-test implementation handoff. Bounded human disposition:
ACCEPTED_WITH_RISK; not deployment authorization or independent-review proof.

The existing four-test shadow/trade reconciliation file initially produced
3 passed / 1 failed because its fake store lacked durable delivery methods.
Its partial-fill fixture now uses a real temporary SQLite-backed tracking store
and asserts completed coverage with no pending delivery. No production check
was relaxed. Combined execution exposed module mocks left behind by facade
synchronization; direct fault-test fixtures now explicitly reset their store
and clock dependency, preventing a facade clock wrapper from re-synchronizing
stale dependencies during a test.

Final combined isolated run: 35 passed in 0.65 seconds (same four previous
files plus test_live_executor_shadow_and_trade_reconcile.py). This covers
that public-interface slice, not every public-facade test or the full suite.
No production changes in this checkpoint. Host, CI, historical repair and
deployment boundaries above remain unchanged.
