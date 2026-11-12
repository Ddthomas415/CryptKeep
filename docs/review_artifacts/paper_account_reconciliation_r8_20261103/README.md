# R8 account reconciliation source handoff

Date: 2026-11-03. Active role: ENGINEER, HIGH risk. Author: READY_FOR_INDEPENDENT_REVIEW, self-checked.
Bot relation: BOT_RULES; runtime configuration, processes, deployment and host state NOT checked.

Independent-review handoff: the separate reviewer returned a usage-limit error before providing a review
disposition. No independent acceptance is available for this stage. The seven-file source seal and 546-case
author receipt remain preserved; no substitute self-approval, automatic retry, operation or new task follows.
Required next proof remains a separate review of this exact seal and its underlying source/test boundaries.

Owner disposition, recorded 2026-11-04 UTC after checking current work log, git and all seven hashes at
2026-11-04T01:13:24Z: the owner's subsequent **"approve"** accepts the submitted source with its disclosed
risks through the human-acceptance route: **ACCEPTED_WITH_RISK, source only**. This is not a completed
independent technical review or a claim that the owner inspected underlying files. Technical proof remains
author self-checked; the reviewer usage-limit failure is retained. No startup, deployment, trading or
configuration permission follows. Further contrary source evidence can reopen this narrow acceptance.

## Outcome

Add account-wide evidence checks to the existing paper monitor. No balance repair, intent transition,
order submission, service startup, scheduled job, account access or strategy change is performed.
This stage follows the independently accepted R8 buy lifecycle and provisional written-sell accounting;
it does not reopen those changes or certify the whole simulation.

- DONE, source/self-checked: atomic fresh-ledger cash initialization retains an opening-cash/common-quote receipt.
  Existing balances ignore unused initialization defaults and are not re-baselined. Existing cash/holdings/history
  without origin evidence yields an alertable incomplete check, not an invented starting balance.
- DONE, source/self-checked: capture all account orders/fills/positions and whitelisted queue/state evidence
  while holding the ledger writer lock. Queue reads are URI-quoted/read-only and use a 0.25-second lock timeout;
  missing/corrupt stores are not treated as empty healthy accounts. Financial writes are not made by auditing.
- DONE, source/self-checked: replay actual fill insertion order with fee-inclusive average basis, compare cash,
  holdings, average basis and realized P&L; inspect 50-bps fill fees and common quote units. All symbols are included,
  not only the primary configured symbol. These are internal paper consistency checks, not exchange-fill proof.
- DONE, source/self-checked: report malformed/overdue intents, missing orders/fills, contradictory identity and
  final states, multiple full-fill receipts, late buy fills and delayed sells. Sells are reported, not expired.
  Retain a union of observed intent IDs and surviving buy/exit event evidence to detect deleted queue rows.
- DONE, source/self-checked: append/fsync a dated JSONL report, preserve known issues when receipt writing fails,
  and dispatch faults through the existing alert interface. Skipped alerts are not delivered. Reporting/alert
  failures remain visible in the returned result; no exactly-once external delivery guarantee.
- DONE, source/self-checked: explicit `--account-reconcile` mode reuses the existing monitor's loop/stop/status
  mechanism independently of the paper runner and campaign analytics. It requires a finite interval in (0,300]
  seconds and subtracts check elapsed time from sleep. Ordinary monitor defaults are unchanged; a status read
  of a stopped account monitor does not repeat the audit or send alerts.
- PARTLY DONE: full R8. Intended-host cadence/capacity, runtime commissioning, actual alert delivery and the
  required bid/ask/mid/age/source at each fill are not certified; quote provenance belongs to the queued R4 work.
- NOT DONE: operations, deployment, full repository suite or profitability evidence. No frozen market experiment
  or 25-symbol scope changed. This is not authorization to run the new mode against real state.

## Evidence

Environment VERIFIED_ENV for isolated Python/SQLite commands. Prices, router gates, account state and alerts
are synthetic/mocked. Work-log task card records prior searches, acceptance criteria, failure matrix and budget.
Public before-source bytes are preserved in `before/`; `seal.py` emits seven exact hashes and an incremental diff.
No unrelated dirty checkout, secrets, configuration or runtime state is bundled.

- First pure checks: 48 passed / one failed. The partial-sale fixture incorrectly expected 4.725 instead of
  4.475 after fee-inclusive basis; its cash expectation was already correct. Arithmetic was corrected, not the
  implementation weakened. Intermediate counts are not added to the consolidated total.
- Current focused fourteen-file selection: **546 passed in 14.77s**, zero failures/errors/skips (`consolidated.txt`).
  Includes new pure/real SQLite/account snapshot cases, existing monitor cases and accepted buy/exit boundaries.
- Preserved original initializer, one boundary probe: **one expected failure in 0.36s** (`before_probe.txt`),
  because initialized cash had no evidenced opening-balance receipt. Only the original initializer method is
  injected from the saved engine using AST; no source swapping, import error or whole-old-tree claim.

Exact consolidated command, from repository root:

```sh
env PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=/private/tmp/cbp-r8-account-consolidated \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_account_reconciliation.py tests/test_paper_account_snapshot.py \
  tests/test_paper_sim_monitor.py tests/test_paper_buy_fill_expiry.py \
  tests/test_paper_buy_lifecycle.py tests/test_paper_buy_before_boundary.py \
  tests/test_paper_engine_integration.py tests/test_paper_engine_honesty.py \
  tests/test_paper_engine_limit_and_status.py tests/test_paper_reconciler_recovery.py \
  tests/test_paper_runner_lifecycle.py tests/test_paper_exit_atomicity.py \
  tests/test_pending_paper_exit_integration.py tests/test_paper_trading_sqlite_invariants.py --tb=short
```

Before-boundary command uses the same prefix, adds
`CBP_ACCOUNT_BEFORE_ROOT=docs/review_artifacts/paper_account_reconciliation_r8_20261103/before`,
and selects `tests/test_paper_account_reconciliation.py::test_pristine_cash_has_durable_origin` only.

## Limits And Required Review

Separate review must challenge opening-baseline provenance/atomicity, snapshot lock placement and queue errors,
replay/accounting/fee/identity checks, deletion evidence, failures during persistence/alerts, existing-monitor
compatibility and source-only scope. Do not turn a passing report or local test into operational acceptance.

The intended account must be isolated in its own state directory with one common quote currency; no current
deployment was inspected. Other allocation writers/direct balance changes are reported as inconsistencies,
not automatically repaired. Supported ledger writers use its lock; queue/ledger are not one cross-database
transaction against arbitrary external writers. A deleted intent with no order, event or prior observation
cannot be reconstructed; deletion of all evidence is not certified as detectable. Manual forging of opening
receipts is not authenticated. Reports describe observed stored data, not an immutable external audit trail.

The source interval is not a wall-clock guarantee if the process, filesystem or alert provider stalls.
Full-history snapshots/replay and growing observed-ID receipts have not been sized on the intended host.
Daily reports are per-UTC-day JSONL check/alert receipts, not a replacement trading ledger or a statistical
performance report. An unavailable filesystem can prevent durable reporting; the returned fault/alert remains
best-effort. Alerts mean channel acceptance, not proof a human received them. No report pruning is introduced.

Open questions: independent counterexamples, actual store/writer compatibility, host cadence/capacity, alert
configuration and the remaining R4/commissioning/evaluation/provider decisions. Source/default configuration,
current configuration, runtime state, backtests/paper economics and deployment remain separate evidence lanes.

What do I know that could change the owner's decision that I have not yet said?

Answer: this makes discrepancies observable, not repaired. An old account may remain INCOMPLETE because its
opening balance was never evidenced; silently adopting its current cash would conceal the very problem being
checked. Actual host startup and full simulation readiness still require their existing separate gates.
