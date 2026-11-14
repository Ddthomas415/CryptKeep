# BA-44 / patch 0067: simulation repair and dependency check

Checked 2026-11-13T23:08:34Z against current Git, work log, source and the frozen
simulation specification. Bot relation: BOT_RULES; temporary paper-ledger tests
only. Intended-server configuration was checked at bounded known locations;
effective loaded runtime configuration remains UNVERIFIED.

## Result and boundary

**SHOWN:** existing patch 0067 fixes the demonstrated outcome-path failure. Both
writer and reader now resolve `CBP_STATE_DIR` through `runtime_dir()` on each call.
No strategy, sizing, exit, fee, risk or scheduling rule changed. Source disposition
after separate Nash GATE review: ACCEPTED_WITH_RISK for the path correction only
(2026-11-13T23:07:40Z). Reviewer inspected underlying code/tests and patch blob
identities; did not rerun author tests. See `INDEPENDENT_REVIEW.md`.
Full simulation remains INCOMPLETE. No forward trial or commissioning was started.
Dependency/Group B analysis is self-checked; the separate GATE disposition covers
the source path repair, not all requirements conclusions in this report.

**Correction:** Codex's 22:55Z inference that a generic continuation lifted the
November 12 R10 stop was wrong. It was withdrawn at 22:59:49Z. Pascal was stopped
and reported no source/test/tool changes or operations, only read-only inspection.
Main had changed the log/state only. R10 remains STOPPED, including further backup
development, downloaded-tool execution and cloud access. O-155 records this error.

## Requested items

| Owner item | Disposition and evidence |
| --- | --- |
| 1. Identify outstanding simulation tasks | DONE as requirements reconciliation, not implementation completion. Existing R1-R12 matrix in `../group_a_unit_composition_20261111/README.md` remains applicable, with the dated corrections below. |
| 2. Separate dependencies | DONE. Strategy runner, paper engine, public tick source, isolated account/config, queue/journal and realistic price/fee recording serve the simulation itself. Effective permissions, delivery, lifecycle target, outside monitoring/backups, restore testing and 72-hour commissioning serve the original full deployment's acceptance. R10 remains required for that acceptance, not intrinsically for executing every paper loop. |
| 3. Investigate a paper-only route without R10 | DONE at source level. Existing runner/engine and managed evidence service provide a route; no approved alternative configuration or runtime success is claimed. See below. |
| 4. Complete immediately unblocked work | PARTLY DONE overall: BA-44 source repair and nine synthetic account cases completed; requirements/source investigation completed. Live-price collection, operational provisioning, sizing choice and Group B implementation are not supplied by these tests. |
| 5. Address BA-44 using 0067 | DONE for the demonstrated source defect: production hunks and original tests reused; fail-before/pass-after evidence below; separate source review ACCEPTED_WITH_RISK. Not deployed. |
| 6. Exact remaining blockers | DONE as inventory: sizing/effective profile, evaluation choices, Group B slot/rotation integration, intended-host capacity/permissions/dependency proof, operating tests and separately authorized trial or original commissioning. No backup waiver or deployment authority is inferred. |

## BA-44 evidence

- Preserved before-files: `outcome_logger.py.before`, `outcome_summary.py.before`.
  The original patch is `0067_original.patch`, byte-equal to the rev88 bundle
  member `cryptkeep_series_on_be34a18a_rev88/patches/0067-fix-outcomes-strategy-outcome-log-follows-the-state-.patch`.
  Its SHA256 is `3bd52758a5e2022cad04277078abb124ea319e8ef73c635abcf0f7b7bef2db6e`.
  An initial archival copy lacked the patch trailer's last blank line; that copy
  was corrected and byte equality rechecked. No production hunk changed for this.
- `git apply --reverse --check` restricted to both outcome source files exits 0
  against 0067. The original 0067 test body is byte-equal to the extracted test.
- Before the production fix: the original path tests plus nine new real temporary
  SQLite paper-fill/reconcile cases produced **13 failed, 10 passed**. Four path
  cases and all nine integration cases failed; ten selector checks passed.
- After the fix: the consolidated eight-file selection produced **95 passed,
  1 failed in 2.80 seconds**. All new/original 0067 cases passed. This is not a
  green suite, full-suite run, Linux/systemd proof or live-market simulation.
- Existing failure: `test_reconcile_once_journals_filled_strategy_intent` in
  `tests/test_intent_reconciler.py`. Its FakeQueue lacks
  `list_pending_paper_buys`, so the current reconciler truthfully returns an
  additional `buy_recovery_faults` field. Running that single test with the two
  archived pre-fix modules compiled into their imported module namespaces yields
  the same failure and AttributeError warning. No assertion was weakened and no
  recovery logic was changed to obtain a pass. This establishes it is not caused
  by 0067; it does not establish every full-suite failure is baseline.
- An initial consolidated command named nonexistent
  `tests/test_paper_reconciliation.py`, collected no tests and exited 4. The actual
  selection below uses `tests/test_paper_account_reconciliation.py`.

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_strategy_outcomes_follow_state_dir.py \
  tests/test_simulation_outcome_reconciliation.py \
  tests/test_intent_reconciler.py tests/test_paper_reconciler_recovery.py \
  tests/test_paper_account_reconciliation.py tests/test_paper_runner_lifecycle.py \
  tests/test_outcome_summary.py tests/test_candidate_outcomes.py --tb=short
```

The nine new cases use three strategy labels x BTC/ETH/SOL, synthetic prices,
temporary real queues/paper engines/journals, simulated read-only source failure,
and reconciler reload. They verify fill reconciliation and no duplicate on a
clean restart, not strategy signal correctness, simultaneous process isolation,
OS read-only enforcement, power loss, profitability or the $1,000 sizing rule.
Submission gates are stubbed only in these tests; production gates are unchanged.
Historical mixed logs are neither migrated, deleted nor silently used as a
fallback. Outcome append failure/crash atomicity remains outside this path fix.

## Existing route without R10; no new controller

**SHOWN source:** `scripts/run_strategy_runner.py` calls the existing strategy
runner; `scripts/run_paper_engine.py` calls the existing paper runner. The latter
consumes queued intents, evaluates paper orders, reconciles fills and marks
positions to market. Neither entrypoint nor those inspected loop bodies invokes
the Group A compositor or backup service. No global import-closure or operating
claim is implied by that observation.

`services/analytics/paper_strategy_evidence_service.py` already starts the public
tick publisher and paper engine and runs strategy windows. This is a genuine bot
path, not a substitute historical backtest. It is nevertheless NOT a drop-in
nine-account 26-week experiment: strategy windows are sequential, child processes
inherit ambient environment, runtime components can be reused, and effective
configuration/ownership must be established before any run. Do not bypass kernel
checks or weaken trading gates to launch it.

**Recommended separately approvable route:** a bounded, supervised diagnostic
using these existing entrypoints and new isolated paper state/config, explicit
live-disabled settings, public data, stated duration and owned cleanup. No new
backup role or controller is needed to propose it. This would test software/data
behavior only; it would not start the original official clock, close R10, satisfy
72-hour commissioning or become registered strategy-performance evidence.
No profile was written or applied. Full-position sizing still needs a decision:
`strategy_runner._cfg()` reads fixed base-unit `qty`; spec section 3 says roughly
$1,000 per position, without choosing fixed-dollar versus changing-cash behavior
or fee/precision handling. Guessing that rule would change financial semantics.

**SHOWN:** the unchanged full-spec compositor includes the backup entrypoint and
refuses a complete target when it is absent. Existing unit composition and
commissioning requirements remain untouched. The earlier statement that no
unblocked source correction remained is narrowed by today's BA-44 reproduction;
the compositor's refusal must not be reported as universal paper impossibility.

## Group B / U-07

**SHOWN:** spec section 4 requires weekly Monday 00:05 UTC selection from the
declared 25-symbol universe, last 200 completed hourly candles, three highest
scores >=38, cash for empty slots, stable slot ownership and fee-charged exit on
rotation. Its ranker stays outside the runner. Group B follows Group A capacity
approval; U-07 is not closed by a static ranking or the nine BA-44 tests.

Existing `multi_symbol_paper_campaign_generator.py` ranks and writes proposals;
`scripts/plan_multi_symbol_paper_campaigns.py` explicitly does not start campaigns
or mutate active manifests. Defaults are 5m / five candidates, not the frozen
hourly / three-slot experiment. Source searches across services/scripts/tests and
Group A artifacts found no Group B weekly slot-file/rotation implementation.
The fetch helper also does not itself trim still-forming candles. Reuse its
ranking primitives, but do not run the default planner and call it Group B.
Missing integration: point-in-time input capture/filtering and Coinbase identity
eligibility; dated slot artifact and stable assignments; runner slot consumption;
exit-before-switch accounting/restart behavior; capacity and same-date evaluation.
No new ranking rule, schedule, collection or rotation logic was invented here.

## Current server inspection and evidence limits

One bounded read-only SSH projection succeeded (exit 0), without credentials,
environment dumps, database access, file/config changes or service actions. Both
documented paths were absent:
`/srv/cryptkeep/app/config/user.yaml` and
`/srv/cryptkeep/app/.cbp_state/runtime/config/user.yaml`. A bounded lookup of
Group A release configuration paths returned no further matching paths.
This is NOT proof that no configuration exists elsewhere or no service runs.
Loaded process config, active services, mount policy, actual source release and
current capacity remain UNVERIFIED. No second connection was made.

Inspected: current instructions/queue/log/Git, frozen spec, source candidate and
composition evidence, original 0067, writer/reader/app_paths, reconciliation and
paper loops, managed service and ranking proposal code, selected tests, bounded
host file projection. Not inspected: credentials, private account state, actual
fills, full runtime process/unit graph or complete host filesystem. No market
backtest, downloaded backup binary, cloud operation, deployment, schedule or
trading/configuration change was performed. Existing source/test evidence was
reused rather than repeating 1,616 tests or the completed Linux test.

Open questions that could change conclusions: actual intended runtime profile and
namespace; sizing semantics; evaluation-rule approvals; Group B implementation
outside the searched paths; independently reviewed source regressions; operating
acceptance and explicit authority for a diagnostic trial versus full commissioning.

What do I know that could change the owner's decision that I have not yet said?
The paper code can be exercised without backups, but that alone does not supply
an approved, correctly sized nine-account experiment. BA-44 is a real repair;
R10's stop and original commissioning criteria can both remain intact while a
separate diagnostic is considered. This report does not make that decision.
