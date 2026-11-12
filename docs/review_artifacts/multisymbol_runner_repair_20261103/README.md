# Multi-symbol runner repair - 2026-11-03

Bot relation: BOT_RULES; runtime trading configuration was not inspected in this task. Synthetic test configuration only.

Role: AUDITOR (handoff records the separate review). Risk: HIGH. Author implementation ended READY_FOR_INDEPENDENT_REVIEW; separate focused source GATE: ACCEPTED. Operational readiness: INCOMPLETE.

Final disposition 2026-11-03: separate reviewer Poincare accepted the corrected hash-bound code, reran 28 integration cases and three additional failure probes, and reproduced the five new regression failures on the initial submission. See independent_review.md. The 197-case combined receipt is author self-checked, not rerun by the reviewer. No deployment or campaign start follows from this acceptance.

## Dated correction - 2026-11-03 05:10Z

The first independent GATE rejected the initial code scope for two demonstrated omissions: repeated all-symbol venue resolution outside the local error boundary, and overwriting saved prices after a failed price-state read. The earlier 22-pass receipt below did not establish those two paths. Initial source/test snapshots and their hashes are retained as strategy_runner.after.py and integration_test.snapshot.py, not silently replaced.

Both findings are corrected: initial all-symbol startup validation runs once, subsequent venue resolution is symbol-local, and a newly selected venue's StartupGuardError still fails closed. Price-read validity now gates both periodic and final checkpoints, so an unread fallback cannot replace saved history. Six new regression cases cover later venue failures, quote/no-quote price-read failures in both data branches through the periodic-save turn, and newly selected unknown-venue refusal.

SHOWN: final new harness **28 passed in 3.21s**. The six new cases against the initial review snapshot produce **5 failed, 1 passed, 22 deselected in 1.05s** (the unknown-venue fail-closed case also passed before). The final combined new-plus-existing command, using the same environment and test-file list below with the new harness added, produces **197 passed in 7.04s**. These are targeted offline results, not a full suite or deployment.

Final source SHA256: 9fb545d0a105e25a7d595a3c0518d11084764d4e454d3c80cacc36a0689ff153.
Final tests SHA256: b1509eead2b0ea315afc17710ad87fc7988cc1878f13ae672b701fd915f1d888.
Final whitespace-insensitive source diff: 64 additions / 5 deletions. Focused independent re-review subsequently ACCEPTED (record above). The original before-repair 19-failure/3-pass receipt below is explicitly the first 22 cases, not a claim about all 28.

Initial submission findings, their causes and affected completion statements are recorded in PROJECT_STATE omission rows O-38/O-39 and the work log. The author has not independently certified these corrections.

## Outcome and scope

SHOWN: rebased the existing rev88 patch 0004 approach onto the current runner, rather than applying the unrelated October series. One symbol is serviced per outer turn, round-robin. Each serviced symbol now reaches position, decision, protective-exit and queue handling using its own freshly fetched price. A missing quote skips that symbol without borrowing another quote. Fresh quotes remain available to protective exits during signal warm-up.

The rebase additionally isolates ordinary multi-symbol turn exceptions and checkpoints loaded price/action state under the current symbol's keys. Partial state reads cannot flush previous-symbol latches under new keys. Single-symbol exception propagation and the all-symbol startup fail-closed guard are retained. A failure in that startup guard intentionally stops startup; it is not treated as an ignorable runtime symbol error.

Inspected: original patch 0004, current full run_forever control flow, relevant helper/storage interfaces, focused existing runner/exit tests and the new real-loop integration harness. Earlier work: PROJECT_STATE engineering item 1; exit_parity_audit_20261031; rev88 patch member and hashes in baseline.json. Saved original source and original patch are unchanged.

Not inspected or exercised: live configuration, real accounts, processes, servers, exchange connectivity, actual consumer lifecycle, deployment or profitability. No operational permission follows from this source repair. All 25 supported symbols remain supported; BTC/ETH/SOL are synthetic test cases, not a reduced universe.

## Requirement evidence

| Queue requirement | Implementation proof | Status |
| --- | --- | --- |
| Reuse earlier fix and independently reproduce defect | Original 0004 saved; identical new harness against original source: 19 failures, 3 passes | Done, self-checked |
| Three independent entries, positions and exit checks | Both tick/public-candle branches; real queue/state/position SQLite and real exit stack | Done, self-checked |
| Simultaneous holdings | Three real temporary paper position rows held together | Done, self-checked |
| Rejected exit isolation | Synthetic test driver records a rejected first-symbol sell; another symbol's sell fills | Done, self-checked |
| Restart and recovery | New runner module and SQLite handles recover own entry/trailing/action state; stop and trailing exits remain symbol-specific | Done, self-checked |
| Missing quote/error/order-write failure isolation | Tick/public branches; injected fetch, position and queue-write failures; fresh-warm-up coverage | Done, self-checked |
| State persistence isolation | Middle-symbol partial read, failed checkpoint, stop mid-round | Done, self-checked |
| Preserve safety boundaries | Unknown/open startup state fails closed before any symbol fetch; single-symbol errors still propagate | Done, self-checked |
| Independent review | Separate GATE ACCEPTED; 28 cases and three reviewer probes pass on final hashes | Done for source scope |
| Multi-symbol operational readiness | Not attempted or authorized by this task | Not done |

## Verification receipts

VERIFIED_ENV: repository venv; env -i; HOME=/private/tmp; PYTHONDONTWRITEBYTECODE=1; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1. New harness relocates state/config/log paths to pytest temporary directories, prevents socket/subprocess access, disables context capture and substitutes quote/signal inputs. It executes real run_forever, exit controls and SQLite accounting. Its minimal test consumer advances queued intents to submitted before recording filled/rejected results; it does not prove production consumer behavior. Fees are zero in this engineering harness, not a financial model.

Commands use the prefix:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```

SHOWN final new harness command (with the prefix above):

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_runner_multi_symbol_integration.py --tb=short
```

Result: **22 passed in 2.83 seconds**. Identical command with CBP_MULTISYMBOL_BEFORE_SOURCE set to the absolute path of strategy_runner.before.py and --tb=no: **19 failed, 3 passed in 1.99 seconds**. The three baseline passes preserve single-symbol exception propagation. Initial harness development failures were not production fixes: queued-to-filled violated the queue transition contract, and first-held-bar counting was asserted incorrectly. Both harness errors were corrected before the reported before/after comparison.

SHOWN existing regression command (same prefix, plus CBP_CAPTURE_MARKET_CONTEXT=0 and CBP_CAPTURE_EXECUTION_IDENTITY=0):

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_runner_public_client_reuse.py tests/test_strategy_runner_lock.py tests/test_ema_runner_risk_defaults.py tests/test_daily_trend_exit_translation.py tests/test_exit_control_stack.py tests/test_managed_exit_policy.py tests/test_exit_deferral.py tests/test_exit_deferral_persistence_boundary.py tests/test_paper_runner_lifecycle.py --tb=short
```

Result: **169 passed in 4.86 seconds**. This is a focused suite, not the full repository suite. git diff --check on changed source/test paths passed. Whitespace-insensitive source diff is 55 additions / 4 deletions; the larger physical diff primarily indents the existing decision tail into the exception boundary.

Initial review hashes (SHA256; superseded for current source/tests by the dated correction above):

- Runner: 0eb457fcf565a8a49b61d7dd89cd6ea1bb44533f25d81afb78ab3647b9fea684
- New tests: da9d67d7d4b4fa2db54dd03ef742008a158d98584c35780186d60c8e4634b572
- Original runner: 7006466dcec981e20b853c26314045a7d8b346b80b2559f46d7ad880f47356ba
- Original patch: 1fab115dcf0bbfb8c8ca1b3fa3a5087f6d9e4d8fbf300a85f3f3269e72ff6348

## Limits that could change acceptance

1. Round-robin cadence is deliberately inherited from 0004: with N symbols each is visited once per N outer turns. This is not all-symbols-every-turn service or a wall-clock latency guarantee. Restart begins the traversal at the first configured symbol. No sampling/cooldown retuning is authorized.
2. Missing/unreadable prices still prevent management of that same symbol; other symbols continue. Total storage failure, process death, blocked network calls and full consumer crash/reconciliation are not established by these injected turn-failure tests.
3. Existing global kill/cooldown, 200-row open-intent scan/status coverage, bookkeeping before successful queue write, rejected-exit retry and aggregate exposure defects are NOT repaired here. Rejection testing demonstrates isolation, not eventual recovery of the rejected holding. These remain the existing paper-simulation/live-safety dependencies in PROJECT_STATE; passing this fix is not permission to run them with money.
4. Startup position uncertainty remains fail-closed for the whole runner. Dynamic venue selection, credential/configuration failures and service operation were not validated here. Historical source acceptance is not current operational proof.
5. Tests inject deterministic signals rather than establishing alpha, and use one venue/quote currency. Existing single-symbol regressions pass, not an exhaustive all-configuration equivalence proof.

No source/settings/services were deployed, no account or credential was accessed, no collector/schedule was started or changed, and no market-data experiment ran. Independent review or a counterexample to state/price isolation could overturn this narrow completion claim. Strategic review remains separate from code tests.

What do I know that could change the owner's decision that I have not yet said?
