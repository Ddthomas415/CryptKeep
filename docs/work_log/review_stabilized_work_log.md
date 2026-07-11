# Review Stabilized Work Log

This file is the durable Codex work log for `review-stabilized`.

Purpose: make engineering/audit work visible in git, including what was found,
what changed, why that change was chosen, expected outcome, verification, and
remaining risk.

## Logging Rule

Every future Codex change that affects code, docs, tests, runtime policy,
operator workflow, or gate behavior must add or update an entry here before
handoff.

Minimum entry fields:
- date/time or commit SHA
- active role and objective
- what was found
- what changed
- why that change was chosen
- expected outcome
- verification run, or why verification was not run
- remaining risk and acceptance state

High-risk work must end at `READY_FOR_INDEPENDENT_REVIEW` in this log until a
separate reviewer or human accepts it.

## Retrospective Scope

SHOWN:
- The current branch is `review-stabilized`.
- Recent visible commit history is available through `git log --oneline`.
- Recent verification results were captured in this thread for the latest gate
  and monitor changes.

UNVERIFIED:
- Older commit intent can only be reconstructed from commit messages and visible
  repo artifacts unless a decision record or command output is present.
- This retrospective is therefore a best-effort reconstruction, not a substitute
  for the original review transcript.

## 2026-07-01 - Add Hetzner Canonical State Migration Template

Date: 2026-07-01

Active role: `ENGINEER`

Objective: add a docs-only canonical `.cbp_state` migration packet template so
future Hetzner migration work has a reviewed evidence structure before any
state is stopped, copied, verified, or started.

What was found:
- SHOWN: `configs/paper_evidence_campaigns.hetzner.example.json` owns only
  `ema_cross_default`.
- SHOWN: `configs/paper_evidence_campaigns.laptop.json` owns canonical
  `es_daily_trend_v1` at `.cbp_state`.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` had Stage 3 requirements but no dated
  canonical migration packet template.

What changed:
- Added
  `docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md`.
- Updated `docs/HETZNER_PAPER_HOST.md` to require the template before any
  canonical migration runtime action.
- Updated `REMAINING_TASKS.md` to name the reviewed Hetzner canonical campaign
  manifest as a blocker.
- Added
  `docs/checkpoints/hetzner_canonical_state_migration_template_2026_07_01.md`.

Why this change:
- The isolated EMA proof does not authorize canonical `.cbp_state` migration.
  The future migration needs a packet that captures baseline gate state, fresh
  ownership payloads, laptop stop proof, manifest/backup/restore proof,
  Hetzner start proof, post-migration gate comparison, and rollback readiness.

Expected outcome:
- Future canonical migration work cannot reasonably proceed from ad hoc shell
  memory; it has an explicit evidence packet and stop conditions.

Verification:
- SHOWN: template/reference grep passed:
  ```bash
  rg -n 'hetzner_canonical_state_migration_TEMPLATE|reviewed Hetzner canonical campaign manifest|Reviewed Hetzner Canonical Manifest|READY_FOR_INDEPENDENT_REVIEW|stop-copy-verify-start' docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md docs/HETZNER_PAPER_HOST.md REMAINING_TASKS.md docs/checkpoints/hetzner_canonical_state_migration_template_2026_07_01.md docs/work_log/review_stabilized_work_log.md
  ```
- SHOWN: manifest ownership grep passed and showed the current split:
  ```bash
  rg -n 'es_daily_trend_v1|\.cbp_state|ema_cross_default' configs/paper_evidence_campaigns.hetzner.example.json configs/paper_evidence_campaigns.laptop.json
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- HIGH: this is a workflow template for a future migration of persistent
  financial-evidence state.
- UNVERIFIED: current Hetzner host runtime state, future reviewed canonical
  manifest, and future canonical migration readiness.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01 after PR #161 checks passed.

## 2026-07-01 - Align Hetzner Follow-Through Backlog

Date: 2026-07-01

Active role: `ENGINEER`

Objective: remove stale Hetzner backlog/runbook language that still described
the isolated challenger UTC-cycle and backup restore rehearsal as open blockers
after the dated deployment record had accepted proof.

What was found:
- SHOWN: `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  is marked `FIRST_UTC_CYCLE_ACCEPTED`.
- SHOWN: the same deployment record contains an `ACCEPTED` backup restore
  rehearsal section with isolated restore path, manifest verification,
  evidence counts, and active-collector non-interference proof.
- SHOWN: `REMAINING_TASKS.md`, `docs/HETZNER_PAPER_HOST.md`, and
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` still
  described restore rehearsal or first UTC-cycle proof as open.

What changed:
- Updated `docs/HETZNER_PAPER_HOST.md` to point at the accepted dated
  deployment record and to keep only canonical `.cbp_state` migration and
  future scheduler/external-alert policy proof as blockers.
- Updated `REMAINING_TASKS.md` to mark the isolated EMA backup restore
  rehearsal, storage-health preflight, and host-health alerting wrapper as
  accepted, while preserving the canonical migration blocker.
- Updated `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` so
  the older checkpoint does not contradict the current accepted deployment
  record.

Why this change:
- The backlog should not send future agents to redo already-accepted high-risk
  operational proof. The correct remaining work is the fresh canonical
  stop-copy-verify-start migration packet, not another isolated EMA restore
  rehearsal.

Expected outcome:
- Future Hetzner work starts from the current accepted proof boundary and does
  not reopen closed isolated-challenger evidence.

Verification:
- SHOWN: stale open-blocker grep returned no matches:
  ```bash
  rg -n "No isolated challenger has completed|No backup/restore rehearsal has been performed|backup restore rehearsal remains open|Storage-health preflight tooling is ready for independent review|host-health alerting wrapper is ready for independent review|Campaign deployment remains blocked pending current-host runtime proof" REMAINING_TASKS.md docs/HETZNER_PAPER_HOST.md docs/checkpoints/review_stabilized_next_actions_2026_05_28.md
  ```
- SHOWN: accepted-proof/current-blocker grep returned the dated deployment
  record and updated backlog/checkpoint references:
  ```bash
  rg -n 'FIRST_UTC_CYCLE_ACCEPTED|Backup Restore Rehearsal|backup/restore rehearsal is accepted|Hetzner isolated EMA backup restore rehearsal is accepted|Canonical `\\.cbp_state` migration remains blocked' REMAINING_TASKS.md docs/HETZNER_PAPER_HOST.md docs/checkpoints/review_stabilized_next_actions_2026_05_28.md docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- LOW: docs-only alignment to existing accepted deployment record.
- UNVERIFIED: current live Hetzner host state and future canonical migration
  readiness.
- Acceptance state: `ACCEPTED`.
- Review reference: same-thread low-risk closure based on visible accepted
  deployment record evidence.

## 2026-07-01 - Hetzner Paper Host Health Alerting Wrapper

Date: 2026-07-01

Active role: `ENGINEER`

Objective: add a scheduled-safe, read-only health wrapper for the Hetzner paper
host so host-preflight failures produce a durable latest artifact and local
critical-alert fallback.

What was found:
- SHOWN: `scripts/hetzner_paper_host_preflight.py` already reports the accepted
  host-readiness checks, including storage health.
- SHOWN: `services/alerts/alert_dispatcher.py` already writes a local
  critical-alert JSONL fallback for error-level alerts, even when external
  alert channels are disabled.
- SHOWN: `services/alerts/alert_dispatcher.py` had three suppressed-error paths
  that referenced undefined `_LOG` instead of the module `logger`.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` listed persistent health alerting as a
  remaining blocker separate from backup restore rehearsal.

What changed:
- Added `scripts/check_hetzner_paper_host_health.py`.
- Added focused tests in `tests/test_check_hetzner_paper_host_health.py`.
- Fixed the alert dispatcher suppressed-error logger references.
- Added alert-dispatcher fallback regression tests in
  `tests/test_alert_dispatcher_fallback.py`.
- Added `make check-hetzner-paper-host-health`.
- Updated `docs/HETZNER_PAPER_HOST.md`, `scripts/SCRIPTS.md`,
  `REMAINING_TASKS.md`, and
  `docs/checkpoints/hetzner_paper_host_health_alerting_proof_2026_07_01.md`.

Why this change:
- The smallest useful fix was to wrap the accepted preflight rather than build
  a second host-health implementation. That keeps the health source of truth in
  one place and uses the already accepted local alert fallback.
- The `_LOG` fix was required because the new wrapper depends on alert fallback
  robustness; leaving it unfixed could turn an alert-write failure into a
  `NameError`.

Expected outcome:
- A host-local scheduler can run one command and leave
  `.cbp_state/runtime/snapshots/hetzner_paper_host_health.latest.json`.
- Failed preflight checks are visible in `failed_checks` and create a local
  critical-alert fallback without requiring Slack, email, SSH, restore, stop,
  start, or campaign mutation.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile services/alerts/alert_dispatcher.py scripts/check_hetzner_paper_host_health.py tests/test_alert_dispatcher_fallback.py tests/test_check_hetzner_paper_host_health.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_alert_dispatcher_fallback.py tests/test_check_hetzner_paper_host_health.py
  ```
  Result: `7 passed in 0.18s`.
- SHOWN: root-script bootstrap slice passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py tests/test_alert_dispatcher_fallback.py tests/test_check_hetzner_paper_host_health.py
  ```
  Result: `20 passed in 0.61s`.

Remaining risk:
- HIGH: this is deployment-adjacent host health alerting for persistent paper
  evidence jobs.
- UNVERIFIED: actual Hetzner host health, scheduler installation, external
  alert delivery, backup age checks, backup restore rehearsal, and canonical
  `.cbp_state` migration.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01 after PR #159 checks passed.

## 2026-07-01 - Close Transitional Family Migration Docs

Date: 2026-07-01

Active role: `ENGINEER`

Objective: align architecture docs with the completed compatibility-family
retirement state after `services/storage` and `services/strategy_runner` were
added to the retired-family guard.

What was found:
- SHOWN: `docs/ARCHITECTURE.md` still described transitional families as frozen
  and scheduled for removal by 2026-08-01.
- SHOWN: `docs/architecture/transitional_service_families.md` and
  `docs/architecture/transitional_family_migration_next_steps.md` did not list
  `services/storage` in the retired family set.
- SHOWN: `tests/test_deprecation_deadline.py` now guards retired families,
  including `services/storage` and `services/strategy_runner`.

What changed:
- Updated `docs/ARCHITECTURE.md` to describe retired service families rather
  than active transitional families.
- Added `services/storage` to the canonical transitional-family docs' retired
  set.
- Added a status update to the 2026-07-01 deadline decision record indicating
  the extended deadline was satisfied early.

Why this change:
- The architectural docs should match the current guarded source state. Leaving
  deadline language active after the migration was complete would send future
  agents toward already-closed cleanup work.

Expected outcome:
- Future contributors see canonical families and retired-family rules without
  stale instructions to migrate no-longer-tracked packages.

Verification:
- SHOWN: targeted retired-family test passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_deprecation_deadline.py
  ```
  Result: `2 passed, 1 skipped in 0.07s`.
- SHOWN: stale-transition wording grep returned no matches:
  ```bash
  rg -n 'frozen compatibility|scheduled for removal|No new code should be added to transitional|Migration target|wrapper-only|future cleanup candidate|remains a frozen' docs/ARCHITECTURE.md docs/architecture docs/checkpoints/storage_retirement_readiness.md docs/checkpoints/overlap_cleanup_plan.md docs/checkpoints/repo_hygiene_overlap_status.md REMAINING_TASKS.md
  ```
- SHOWN: retired-family reference grep showed only expected retired-family and
  guard references:
  ```bash
  rg -n 'services/storage|services/storage/|services\.storage|services/strategy_runner|services/strategy_runner/|services\.strategy_runner' docs/ARCHITECTURE.md docs/architecture docs/checkpoints/storage_retirement_readiness.md docs/checkpoints/overlap_cleanup_plan.md docs/checkpoints/repo_hygiene_overlap_status.md REMAINING_TASKS.md tests/test_deprecation_deadline.py
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- LOW: docs-only alignment with already-merged retired-family guard state.
- Acceptance state: `ACCEPTED`.
- Review reference: same-thread low-risk closure based on targeted proof.

## 2026-07-01 - Mark `services/storage` Retired

Date: 2026-07-01

Active role: `ENGINEER`

Objective: reconcile the storage overlap docs and retired-family guard after
`services/storage` was already absent from tracked source.

What was found:
- SHOWN: `git ls-files services/storage` returned no tracked files.
- SHOWN: active import grep returned no `services.storage` imports from tracked
  source/test paths.
- SHOWN: no non-cache files remained under `services/storage`.
- SHOWN: overlap docs still described `services/storage` as a future cleanup
  candidate instead of a retired family.

What changed:
- Added `services/storage` to `RETIRED_FAMILIES` in
  `tests/test_deprecation_deadline.py`.
- Updated storage overlap/checkpoint/backlog docs to mark `services/storage`
  retired and top-level `storage/` canonical.

Why this change:
- The source tree had already reached the retired state. The guard and docs
  should match the visible repo state so future work does not reopen a removed
  compatibility package.

Expected outcome:
- Any future tracked Python file under `services/storage` fails the
  retired-family regression guard.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted deprecation test passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_deprecation_deadline.py
  ```
  Result: `2 passed, 1 skipped in 0.08s`.
- SHOWN: no tracked files remain under `services/storage`:
  ```bash
  git ls-files services/storage
  ```
- SHOWN: active import grep returned no matches:
  ```bash
  rg -n 'from services\.storage|import services\.storage' services scripts tests dashboard tools --glob '*.py'
  ```
- SHOWN: no non-cache files remain under `services/storage`:
  ```bash
  find services/storage -type f -not -path '*/__pycache__/*' -print | sort
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- LOW: no tracked source files are removed in this change; it is docs/test
  governance alignment.
- Acceptance state: `ACCEPTED`.
- Review reference: same-thread low-risk closure based on targeted proof.

## 2026-07-01 - Retire `services/strategy_runner`

Date: 2026-07-01

Active role: `ENGINEER`

Objective: retire the remaining `services/strategy_runner` compatibility
package after runtime ownership moved to `services/execution/strategy_runner.py`
and active internal callers were migrated.

What was found:
- SHOWN: `services/strategy_runner` contained only compatibility wrapper files.
- SHOWN: active import grep returned no `services.strategy_runner` imports from
  tracked `services/`, `scripts/`, or `tests/` Python files.
- SHOWN: canonical strategy runtime now lives at
  `services/execution/strategy_runner.py`.

What changed:
- Deleted the remaining tracked `services/strategy_runner` Python files.
- Moved `services/strategy_runner` from `DEPRECATED_FAMILIES` to
  `RETIRED_FAMILIES` in `tests/test_deprecation_deadline.py`.
- Updated architecture, checkpoint, and backlog docs to mark
  `services/strategy_runner` retired.

Why this change:
- Keeping a wrapper-only compatibility package after active callers had been
  migrated preserved overlap debt with no internal runtime benefit. Retiring it
  completes the transitional-family migration and lets the retired-family guard
  prevent reintroduction.

Expected outcome:
- No tracked source files remain under `services/strategy_runner`.
- New code cannot reintroduce `services/strategy_runner` without failing the
  retired-family regression test.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    tests/test_deprecation_deadline.py \
    tests/test_execution_strategy_runner_placeholder.py \
    services/execution/strategy_runner.py
  ```
- SHOWN: targeted retirement/runtime guard tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_deprecation_deadline.py \
    tests/test_execution_strategy_runner_placeholder.py \
    tests/test_startup_guard_regression.py \
    tests/test_ema_runner_risk_defaults.py \
    tests/test_ema_unification_regression.py
  ```
  Result: `10 passed, 1 skipped in 1.49s`.
- SHOWN: canonical runtime import does not trigger deprecated-wrapper warnings:
  ```bash
  ./.venv/bin/python -c 'import warnings; warnings.simplefilter("error", DeprecationWarning); import services.execution.strategy_runner as runner; print(callable(runner.run_forever), callable(runner.request_stop))'
  ```
  Result: `True True`.
- SHOWN: active import grep returned no matches:
  ```bash
  rg -n 'from services\.strategy_runner|import services\.strategy_runner' services scripts tests --glob '*.py'
  ```
- SHOWN: no non-cache files remain under `services/strategy_runner`:
  ```bash
  find services/strategy_runner -type f -not -path '*/__pycache__/*' -print | sort
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- MEDIUM: external untracked callers importing `services.strategy_runner` would
  need to move to `services.execution.strategy_runner` or canonical strategy
  modules.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Broaden Strategy Runner Import Guard

Date: 2026-07-01

Active role: `ENGINEER`

Objective: prevent active internal code from reintroducing imports from the
frozen `services.strategy_runner` compatibility package after runtime ownership
moved to `services.execution.strategy_runner`.

What was found:
- SHOWN: `tests/test_execution_strategy_runner_placeholder.py` blocked imports
  of `services.strategy_runner.ema_crossover_runner`.
- SHOWN: the guard did not block other transitional imports such as
  `services.strategy_runner.strategies.ema_crossover`.
- SHOWN: current `rg` output showed no active `services/` or `scripts/` import
  from the transitional package after PR #154.

What changed:
- Broadened the AST import guard to reject any `services.strategy_runner` import
  from active `services/` and `scripts/` code outside the compatibility package
  itself.

Why this change:
- The remaining `services/strategy_runner` files are compatibility wrappers.
  Active code should not grow new dependencies on that package while it is
  frozen for retirement.

Expected outcome:
- Any future internal reintroduction of `services.strategy_runner` imports fails
  targeted regression tests immediately.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    tests/test_execution_strategy_runner_placeholder.py \
    tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_execution_strategy_runner_placeholder.py \
    tests/test_deprecation_deadline.py
  ```
  Result: `5 passed, 1 skipped in 1.29s`.
- SHOWN: active-code import grep returned no matches:
  ```bash
  rg -n 'from services\.strategy_runner|import services\.strategy_runner' services scripts --glob '*.py'
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- LOW: this is test-only governance hardening.
- Acceptance state: `ACCEPTED`.
- Review reference: same-thread low-risk closure based on targeted proof.

## 2026-07-01 - Move Strategy Runtime To Execution Package

Date: 2026-07-01

Active role: `ENGINEER`

Objective: continue retiring the frozen `services/strategy_runner`
compatibility family by moving the runtime runner module to the canonical
execution package.

What was found:
- SHOWN: current architecture docs marked `services/strategy_runner` as frozen
  transitional code, but `services/execution/strategy_runner.py` was still a
  placeholder that told callers to use the transitional module.
- SHOWN: active runtime callers imported
  `services.strategy_runner.ema_crossover_runner` directly.
- SHOWN: the earlier ADR still described `services/strategy_runner` as the
  canonical runtime package, which conflicted with the migration deadline docs.

What changed:
- Moved the runner implementation from
  `services/strategy_runner/ema_crossover_runner.py` to
  `services/execution/strategy_runner.py`.
- Replaced the old transitional module with a compatibility re-export wrapper.
- Migrated active internal runtime imports to `services.execution.strategy_runner`.
- Updated current architecture/operator docs and regression tests to use the
  execution runtime path.

Why this change:
- The strategy runtime is execution behavior. Keeping the real implementation
  under a frozen compatibility family made the 2026-08-01 retirement deadline
  unenforceable without a later risky move. This change preserves the runtime
  API while moving canonical ownership to the execution package.

Expected outcome:
- New internal code has a canonical runtime path that does not import the
  transitional package.
- The remaining `services/strategy_runner` package can be retired later once
  external/reference proof shows no callers require the compatibility wrapper.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    services/execution/strategy_runner.py \
    services/strategy_runner/ema_crossover_runner.py \
    scripts/run_strategy_runner.py \
    scripts/compat/run_strategy_runner.py \
    scripts/run_bot_safe.py \
    services/analytics/paper_strategy_evidence_service.py \
    services/execution/live_trader_loop.py \
    tests/test_execution_strategy_runner_placeholder.py \
    tests/test_strategy_runtime_runner.py \
    tests/test_intent_emission_gate.py \
    tests/test_startup_guard_regression.py \
    tests/test_ema_runner_risk_defaults.py \
    tests/test_ema_unification_regression.py \
    tests/test_es_signal_regression.py \
    tests/test_campaign_summary.py
  ```
- SHOWN: focused ownership/import tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_execution_strategy_runner_placeholder.py \
    tests/test_startup_guard_regression.py \
    tests/test_ema_runner_risk_defaults.py \
    tests/test_ema_unification_regression.py \
    tests/test_intent_emission_gate.py
  ```
  Result: `9 passed in 1.58s`.
- SHOWN: strategy runtime regression tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_strategy_runtime_runner.py \
    tests/test_es_signal_regression.py \
    tests/test_campaign_summary.py
  ```
  Result: `47 passed in 1.19s`.
- SHOWN: canonical import does not trigger the deprecated wrapper warning:
  ```bash
  ./.venv/bin/python -c 'import warnings; warnings.simplefilter("error", DeprecationWarning); import services.execution.strategy_runner as runner; print(callable(runner.run_forever), callable(runner.request_stop))'
  ```
  Result: `True True`.
- SHOWN: no active `services/` or `scripts/` source imports remain from the
  transitional runner module:
  ```bash
  rg -n 'from services\.strategy_runner\.ema_crossover_runner|import services\.strategy_runner\.ema_crossover_runner|from services\.strategy_runner import ema_crossover_runner' services scripts --glob '*.py'
  ```
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- HIGH: this changes runtime module ownership for paper/live strategy runner
  code, even though the implementation body is preserved and callers are
  migrated mechanically.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Track `services/strategy_runner` Deadline

Date: 2026-07-01

Active role: `ENGINEER`

Objective: restore deadline enforcement for the remaining frozen
`services/strategy_runner` transitional family after the paper, marketdata, and
strategy compatibility families were retired.

What was found:
- SHOWN: architecture and backlog docs still identify
  `services/strategy_runner` as frozen transitional code with a 2026-08-01
  target.
- SHOWN: `tests/test_deprecation_deadline.py` had `DEPRECATED_FAMILIES = []`,
  so the deadline test no longer enforced removal for the still-frozen family.
- SHOWN: `services/strategy_runner/__init__.py` was empty, so re-adding the
  family to `DEPRECATED_FAMILIES` also required the existing deprecation-warning
  test to be satisfied.

What changed:
- Added `services/strategy_runner` back to `DEPRECATED_FAMILIES`.
- Added an import-time `DeprecationWarning` to
  `services/strategy_runner/__init__.py`.

Why this change:
- The deprecation test should keep enforcing the one transitional family that
  remains frozen, while the retired-family guard separately prevents the already
  retired families from being reintroduced.

Expected outcome:
- The repository will fail the deadline test after 2026-08-01 if
  `services/strategy_runner` remains present.
- Imports of `services.strategy_runner` expose an explicit deprecation warning
  before the deadline.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    tests/test_deprecation_deadline.py \
    services/strategy_runner/__init__.py
  ```
- SHOWN: targeted deadline test passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_deprecation_deadline.py
  ```
  Result: `2 passed, 1 skipped in 0.07s`.
- SHOWN: whitespace check passed:
  ```bash
  git diff --check
  ```

Remaining risk:
- LOW: this is a governance/test coherence fix plus a package-level
  deprecation warning.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Move EMA Helper Ownership To Canonical Strategy

Date: 2026-07-01

Active role: `ENGINEER`

Objective: prevent canonical EMA strategy imports from depending on the
deprecated `services.strategy_runner` compatibility package after package-level
deprecation warnings were added.

What was found:
- SHOWN: `services/strategies/ema_cross.py` imported `EMACfg`, `EMAState`,
  `update_ema_state`, and `compute_signal` from
  `services.strategy_runner.strategies.ema_crossover`.
- SHOWN: adding a package-level deprecation warning to `services.strategy_runner`
  would therefore warn even when callers used the canonical
  `services.strategies.ema_cross` path.

What changed:
- Moved the EMA helper dataclasses and pure helper functions into
  `services/strategies/ema_cross.py`.
- Replaced `services/strategy_runner/strategies/ema_crossover.py` with a
  compatibility re-export from the canonical strategy module.
- Migrated active internal callers in `services/strategy_ema.py` and
  `services/trading_runner/run_trader.py` to the canonical helper path.
- Added a regression assertion that canonical EMA code does not import
  `services.strategy_runner`.

Why this change:
- The canonical strategy package should own reusable strategy logic. The frozen
  strategy-runner package should remain a temporary runtime/compatibility
  surface, not the source of reusable strategy helpers.

Expected outcome:
- Canonical EMA strategy imports no longer trigger the deprecated package
  warning.
- Existing deprecated imports continue to resolve through the compatibility
  re-export until the full `services/strategy_runner` retirement.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    services/strategies/ema_cross.py \
    services/strategy_runner/strategies/ema_crossover.py \
    services/strategy_ema.py \
    services/trading_runner/run_trader.py \
    tests/test_ema_unification_regression.py
  ```
- SHOWN: targeted EMA/deprecation tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_ema_unification_regression.py \
    tests/test_ema_parity_regression.py \
    tests/test_deprecation_deadline.py
  ```
  Result: `9 passed, 1 skipped in 1.21s`.
- SHOWN: canonical imports do not trigger the deprecated package warning:
  ```bash
  ./.venv/bin/python -c 'import warnings; warnings.simplefilter("error", DeprecationWarning); import services.strategies.ema_cross; import services.strategy_ema; print("canonical_imports_ok")'
  ```
- SHOWN: no active source imports remain from the deprecated EMA helper module:
  ```bash
  rg -n 'from services\.strategy_runner\.strategies\.ema_crossover|import services\.strategy_runner\.strategies\.ema_crossover' services scripts --glob '*.py'
  ```

Remaining risk:
- MEDIUM: this moves pure EMA helper ownership but preserves function names and
  behavior through targeted regression tests.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Retired Family Regression Guard

Date: 2026-07-01

Active role: `ENGINEER`

Objective: prevent retired compatibility families from being silently
reintroduced after `services/paper`, `services/marketdata`, and
`services/strategy` were retired.

What was found:
- SHOWN: `tests/test_deprecation_deadline.py` had no active deprecated family
  entries after the retirements.
- SHOWN: without a separate retired-family guard, a future Python file under a
  retired family could reappear without failing the deprecation test before the
  2026-08-01 deadline.

What changed:
- Added `RETIRED_FAMILIES` to `tests/test_deprecation_deadline.py`.
- Added `test_retired_families_stay_removed`, which fails if any retired family
  contains non-cache Python files.

Why this change:
- The deprecation gate should distinguish between families still pending
  migration and families already retired. Retired families need a permanent
  no-reintroduction check.

Expected outcome:
- `services/paper`, `services/marketdata`, and `services/strategy` cannot be
  reintroduced with Python files without an explicit test failure.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted test passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_deprecation_deadline.py
  ```
  Result: `2 passed, 1 skipped in 0.07s`.

Remaining risk:
- LOW: this is a test-only governance guard.
- Acceptance state: `ACCEPTED`.

## 2026-07-01 - Retire `services/strategy`

Date: 2026-07-01

Active role: `ENGINEER`

Objective: retire the final `services/strategy` compatibility shim and route
startup-guard proof to the canonical execution package.

What was found:
- SHOWN: `services/strategy` had one tracked source file:
  `services/strategy/startup_guard.py`.
- SHOWN: `services/execution/startup_guard.py` contains the canonical
  `require_known_flat_or_override` implementation.
- SHOWN: active runtime code imports the canonical startup guard from
  `services.execution.startup_guard`, not `services.strategy.startup_guard`.
- SHOWN: `tests/test_startup_guard_regression.py` read the deprecated file
  directly, keeping the retired family alive as test scaffolding.

What changed:
- Deleted `services/strategy/startup_guard.py`.
- Updated `tests/test_startup_guard_regression.py` to check
  `services/execution/startup_guard.py`.
- Removed `services/strategy` from `tests/test_deprecation_deadline.py`.
- Updated architecture, transitional-family, overlap, ownership, and backlog
  docs to mark `services/strategy` retired.

Why this change:
- The remaining `services/strategy` file was a compatibility shim over a
  canonical execution guard with active tests. Deleting the shim removes false
  transitional-family debt without changing the active runtime import path.

Expected outcome:
- No tracked Python files remain under `services/strategy`.
- Startup-guard tests and runtime wiring stay anchored to
  `services/execution/startup_guard.py`.
- The only remaining transitional runtime family is
  `services/strategy_runner`.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    services/execution/startup_guard.py \
    tests/test_startup_guard_regression.py \
    tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_startup_guard_behavior.py \
    tests/test_startup_guard_regression.py \
    tests/test_deprecation_deadline.py
  ```
  Result: `6 passed, 1 skipped in 0.21s`.
- SHOWN: source-only reference check found no active `services.strategy`
  imports:
  ```bash
  rg --pcre2 -n "services\.strategy(?!_)" \
    services scripts tests dashboard storage tools --glob '*.py'
  ```
- SHOWN: no non-cache files remain under `services/strategy` in the working
  tree:
  ```bash
  find services/strategy -maxdepth 2 -type f -not -path '*/__pycache__/*'
  ```
- SHOWN: the final tracked shim is deleted in the working tree:
  ```bash
  git ls-files -d services/strategy
  ```

Remaining risk:
- MEDIUM: external untracked callers importing `services.strategy.startup_guard`
  would need to move to `services.execution.startup_guard`.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Mark `services/marketdata` Retired

Date: 2026-07-01

Active role: `ENGINEER`

Objective: reconcile the transitional-family docs and deprecation test after
`services/marketdata` was already absent from tracked source.

What was found:
- SHOWN: `git ls-files services/marketdata` returned no tracked source files.
- SHOWN: strict import grep found no active `services.marketdata` imports in
  source, scripts, or tests.
- SHOWN: docs still described `services/marketdata` as a pending
  compatibility wrapper.
- SHOWN: `tests/test_deprecation_deadline.py` still listed
  `services/marketdata` even though no tracked Python files remained under that
  family.

What changed:
- Removed `services/marketdata` from `tests/test_deprecation_deadline.py`.
- Updated architecture, transitional-family, overlap, and backlog docs to mark
  `services/marketdata` retired.
- Updated the marketdata retirement/deprecation checkpoints to record completed
  retirement instead of future-retirement planning.

Why this change:
- The compatibility family had already reached the removal state; leaving docs
  and deadline tests in a pending state created false backlog noise and could
  cause future agents to reopen retired work.

Expected outcome:
- Remaining transitional-family work narrows to `services/strategy` and
  `services/strategy_runner`.
- New market-data work stays routed to `services/market_data`.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_deprecation_deadline.py \
    tests/test_ws_ticker_feed.py \
    tests/test_marketdata_ohlcv_fetcher.py \
    tests/test_repo_layout_scope_doc.py
  ```
  Result: `15 passed, 1 skipped in 0.30s`.
- SHOWN: source-only reference check found no active `services.marketdata`
  imports:
  ```bash
  rg -n -P "services\.marketdata(?!_)" \
    tests services scripts dashboard storage tools --glob '*.py'
  ```
- SHOWN: no tracked files remain under `services/marketdata`:
  ```bash
  git ls-files services/marketdata
  ```

Remaining risk:
- LOW: no tracked `services/marketdata` source files were removed in this
  change; the main risk is stale docs elsewhere.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Retire `services/paper`

Date: 2026-07-01

Active role: `ENGINEER`

Objective: retire the `services/paper` transitional compatibility package after
PR #149 extended the transitional-family deadline.

What was found:
- SHOWN: `rg` found only test callers for `services.paper`.
- SHOWN: `services.paper.paper_state.PaperState` duplicated the canonical
  `services.paper_trader.paper_state.PaperState`.
- SHOWN: `services.paper.paper_broker` was a thin compatibility wrapper over
  `services.execution.paper_engine.PaperEngine` with no active runtime caller.
- SHOWN: `services.paper.main` was covered only by a legacy mode-gate test.

What changed:
- Deleted the tracked `services/paper` package files.
- Deleted `tests/test_paper_main_mode_gate.py`, which existed only for the
  retired package.
- Migrated `test_paper_state_snapshot` to
  `services.paper_trader.paper_state`.
- Removed the shim-only paper broker compatibility test.
- Removed `services/paper` from `tests/test_deprecation_deadline.py`.
- Updated architecture, overlap, ownership, and backlog docs to mark
  `services/paper` retired.

Why this change:
- `services/paper` was the safest transitional-family retirement target because
  it had no active runtime imports and only test coverage remained.
- Retiring one family reduces the August deprecation deadline risk without
  touching active paper campaigns.

Expected outcome:
- No tracked Python files remain under `services/paper`.
- Future paper work routes to `services/paper_trader` or
  `services/execution/paper_engine.py`.
- The remaining transitional-family work narrows to `services/marketdata`,
  `services/strategy`, and `services/strategy_runner`.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    tests/test_placeholder_recovery_phase3.py \
    tests/test_deprecation_deadline.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_placeholder_recovery_phase3.py \
    tests/test_deprecation_deadline.py
  ```
  Result: `9 passed, 1 skipped in 0.23s`.
- SHOWN: strict source/reference check found no remaining `services.paper`
  imports:
  ```bash
  rg -n -P "services\.paper(?!_)" \
    tests services scripts dashboard storage tools docs/architecture \
    docs/checkpoints docs/ARCHITECTURE.md REMAINING_TASKS.md \
    --glob '*.py' --glob '*.md'
  ```
- SHOWN: tracked files under `services/paper` are deleted in the working tree:
  ```bash
  git ls-files -d services/paper tests/test_paper_main_mode_gate.py
  ```

Remaining risk:
- MEDIUM: compatibility package removal can break any untracked external caller
  that still imports `services.paper`.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Transitional Family Deadline Extension

Date: 2026-07-01

Active role: `ENGINEER`

Objective: unblock PR #149 CI after the transitional-family deprecation
deadline elapsed on 2026-07-01.

What was found:
- SHOWN: `CI sanity` and `CI validate` both failed only at
  `tests/test_deprecation_deadline.py::test_deprecation_deadline_not_passed`.
- SHOWN: the failure reported `services/strategy` and `services/paper` still
  present after the 2026-07-01 deadline.
- SHOWN: `docs/architecture/transitional_service_families.md` records
  `services/paper` as a frozen compatibility layer and `services/strategy` as a
  frozen internal compatibility island.
- SHOWN: tests still cover `services/paper` and
  `services/strategy/startup_guard.py`.

What changed:
- Extended the transitional-family removal deadline to 2026-08-01 in
  `tests/test_deprecation_deadline.py`.
- Aligned deadline text in `docs/ARCHITECTURE.md`, `docs/CONTROL_KERNEL.md`,
  `services/paper/*`, and `services/strategy/startup_guard.py`.
- Added
  `docs/strategies/decision_record_2026-07-01_transitional_family_deadline.md`.
- Updated `REMAINING_TASKS.md` and
  `docs/architecture/transitional_family_migration_next_steps.md` so the
  extended deadline remains visible in the backlog.

Why this change:
- Removing the compatibility families inside the Hetzner storage-preflight PR
  would mix unrelated migration work into a host-readiness change and risk
  deleting covered behavior without focused migration proof.
- The deprecation test explicitly allows extending the deadline if the date is
  updated and a decision record explains why.

Expected outcome:
- CI can run again while preserving the removal pressure.
- Transitional families remain frozen; no new imports or feature work should
  target them.

Verification:
- SHOWN: GitHub Actions logs for PR #149 showed the date-triggered failure.
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    tests/test_deprecation_deadline.py \
    services/paper/__init__.py \
    services/paper/main.py \
    services/paper/paper_broker.py \
    services/paper/paper_state.py \
    services/strategy/startup_guard.py
  ```
- SHOWN: targeted deadline/compatibility slice passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_deprecation_deadline.py \
    tests/test_paper_main_mode_gate.py \
    tests/test_placeholder_recovery_phase3.py \
    tests/test_startup_guard_regression.py
  ```
  Result: `13 passed, 1 skipped, 5 warnings in 1.34s`.
- UNVERIFIED: GitHub CI rerun on 2026-07-01 after the deadline extension.

Remaining risk:
- MEDIUM: the compatibility-family migration is deferred, not resolved.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01.

## 2026-07-01 - Hetzner Storage Preflight

Date: 2026-07-01

Active role: `ENGINEER`

Objective: add read-only backup-directory, free-space, and free-inode checks to
the accepted Hetzner paper-host preflight.

What was found:
- SHOWN: the accepted Hetzner preflight checked repo files, venv, collector
  imports, Git checkout, NTP, Tailscale, and campaign config.
- SHOWN: it did not check backup directory presence, free disk space, or free
  inode availability.
- SHOWN: persistent alerting and backup restore rehearsal remain separate
  Priority 16 blockers.

What changed:
- Added `storage_health` to `scripts/hetzner_paper_host_preflight.py`.
- Added CLI thresholds: `--backup-dir`, `--min-free-gb`, and
  `--min-free-inodes`.
- Added targeted tests for accepted storage, missing backup directory, low
  space, and low inodes.
- Updated `docs/HETZNER_PAPER_HOST.md`, `scripts/SCRIPTS.md`,
  `REMAINING_TASKS.md`, Priority 16 checkpoint, and added
  `docs/checkpoints/hetzner_storage_preflight_proof_2026_07_01.md`.

Why this change:
- Storage health is a minimum precondition for persistent paper evidence jobs.
  Adding it to the existing read-only preflight is the smallest safe step
  before any restore/start or state-transfer operation.

Expected outcome:
- Operators get a fail-closed storage readiness signal before Hetzner restore
  or state transfer.
- The remaining blockers stay explicit: current-host proof, persistent
  alerting, backup restore rehearsal, and reviewed migration procedure.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    scripts/hetzner_paper_host_preflight.py \
    tests/test_hetzner_paper_host_preflight.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q tests/test_hetzner_paper_host_preflight.py
  ```
  Result: `12 passed in 0.10s`.
- SHOWN: root-script bootstrap slice passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_bootstrap_helper_adoption.py \
  tests/test_no_duplicate_script_bootstrap.py \
  tests/test_hetzner_paper_host_preflight.py
  ```
  Result: `25 passed in 0.57s`.

Remaining risk:
- HIGH: host storage health affects persistent financial-evidence background
  jobs and state migration safety.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-01 before the CI deadline follow-up.

## 2026-06-30 - Record PR147 Merge Status

Date: 2026-06-30

Active role: `ENGINEER`

Objective: align backlog and Priority 16 checkpoint language after PR #147 was
independently accepted and merged.

What was found:
- SHOWN: PR #147 merged as `8d75486e`.
- SHOWN: `REMAINING_TASKS.md` and the Priority 16 checkpoint still described
  runtime duplicate-process proof tooling as ready for independent review.
- SHOWN: current-host runtime proof still requires fresh laptop and Hetzner
  status payloads.

What changed:
- Updated `REMAINING_TASKS.md` to mark runtime duplicate-process proof tooling
  accepted and merged by PR #147.
- Updated
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`
  to keep only the current-host runtime proof and other operational blockers
  open.

Why this change:
- Completed high-risk review states should not remain in the active backlog as
  pending review work. The repo needs to distinguish accepted tooling from the
  still-unperformed fresh-host runtime proof.

Expected outcome:
- Future check-ins see the correct Hetzner state: runtime ownership tooling is
  accepted, while current-host status payload proof remains required.

Verification:
- SHOWN: `git diff --check` passed.
- SHOWN: `rg` confirmed no remaining "runtime duplicate-process proof tooling
  is ready for independent review" wording in the touched backlog surfaces.
- Tests were not run because this is docs/status alignment only.

Remaining risk:
- LOW: documentation/status alignment only.
- Acceptance state: `ACCEPTED`.

## 2026-06-30 - Paper Runtime Ownership Proof Tooling

Date: 2026-06-30

Active role: `ENGINEER`

Objective: add a read-only runtime duplicate-process checker for already
captured laptop and Hetzner paper-campaign status JSON payloads.

What was found:
- SHOWN: manifest ownership proof is accepted, but it does not prove current
  process ownership.
- SHOWN: `restore_paper_campaigns.py --status` emits campaign `name`,
  `session_strategy_id`, `state_dir`, `running`, and `pid`.
- SHOWN: the remaining Hetzner blocker needs current-host duplicate-process
  proof before any state transfer or restore/start operation.

What changed:
- Added `services/analytics/paper_campaign_runtime_ownership.py`.
- Added `scripts/check_paper_campaign_runtime_ownership.py`.
- Added targeted service and CLI tests.
- Updated `scripts/SCRIPTS.md`, `REMAINING_TASKS.md`, Priority 16 checkpoint,
  and added
  `docs/checkpoints/hetzner_paper_runtime_ownership_proof_2026_06_30.md`.

Why this change:
- Comparing fresh status payloads is the smallest safe runtime proof before
  stop-copy-verify-start planning. The checker does not SSH, restore, start,
  stop, copy state, or migrate `.cbp_state`.

Expected outcome:
- Operators can detect duplicate running campaign ownership across laptop and
  Hetzner from captured status JSON before migration work.
- Actual host/process proof remains explicit and time-bound to the captured
  payloads.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    services/analytics/paper_campaign_runtime_ownership.py \
    scripts/check_paper_campaign_runtime_ownership.py \
    tests/test_paper_campaign_runtime_ownership.py \
    tests/test_check_paper_campaign_runtime_ownership_script.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_paper_campaign_runtime_ownership.py \
    tests/test_check_paper_campaign_runtime_ownership_script.py
  ```
  Result: `5 passed in 0.15s`.
- SHOWN: root-script bootstrap slice passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_bootstrap_helper_adoption.py \
    tests/test_no_duplicate_script_bootstrap.py \
    tests/test_paper_campaign_runtime_ownership.py \
    tests/test_check_paper_campaign_runtime_ownership_script.py
  ```
  Result: `18 passed in 0.64s`.

Remaining risk:
- HIGH: runtime ownership affects persistent financial-evidence background jobs
  and state migration safety.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by human operator on
  2026-06-30 before PR #147 merge.

## 2026-06-30 - Record PR145 Merge Status

Date: 2026-06-30

Active role: `ENGINEER`

Objective: align backlog and Priority 16 checkpoint language after PR #145 was
independently accepted and merged.

What was found:
- SHOWN: PR #145 merged as `6d9f8af66`.
- SHOWN: `REMAINING_TASKS.md` and the Priority 16 checkpoint still described
  the Hetzner manifest ownership proof as ready for independent review.
- SHOWN: runtime duplicate-process proof, backup restore rehearsal,
  disk/health alerting, and reviewed stop-copy-verify-start remain open.

What changed:
- Updated `REMAINING_TASKS.md` to mark manifest-level ownership proof accepted
  and merged by PR #145.
- Updated
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`
  to keep only the remaining Hetzner operational blockers open.

Why this change:
- Completed high-risk review states should not remain in the active backlog as
  pending review work. Stale status text causes duplicate audits and confuses
  the next operator action.

Expected outcome:
- Future check-ins see the correct Hetzner state: manifest ownership is
  accepted, while runtime host/process and restore proofs remain required.

Verification:
- SHOWN: `git diff --check` passed.
- SHOWN: `rg` confirmed no remaining "manifest ownership proof is ready for
  independent review" wording in the touched backlog surfaces.
- Tests were not run because this is docs/status alignment only.

Remaining risk:
- LOW: documentation/status alignment only.
- Acceptance state: `ACCEPTED`.

## 2026-06-30 - Paper Campaign Ownership Proof

Date: 2026-06-30

Active role: `ENGINEER`

Objective: add a local read-only manifest ownership proof for laptop and
Hetzner paper campaign configs before any state transfer or canonical
`.cbp_state` migration.

What was found:
- SHOWN: the laptop manifest owns `es_daily_trend_v1` and `breakout_default`.
- SHOWN: the Hetzner manifest owns `ema_cross_default`.
- SHOWN: the Hetzner follow-through backlog requires one owner per campaign,
  but runtime host checks, backup restore rehearsal, and canonical migration
  remain separate high-risk work.

What changed:
- Added `services/analytics/paper_campaign_ownership.py`.
- Added `scripts/check_paper_campaign_ownership.py`.
- Added targeted service and CLI tests.
- Added `make check-paper-campaign-ownership`.
- Updated `scripts/SCRIPTS.md`, `REMAINING_TASKS.md`, Priority 16 checkpoint,
  and added
  `docs/checkpoints/hetzner_paper_campaign_ownership_proof_2026_06_30.md`.

Why this change:
- A manifest-level ownership check is the smallest safe proof before any
  stop-copy-verify-start operation. It prevents duplicate campaign/session/state
  claims across the combined manifests without SSH, restore, start, stop, or
  state-copy behavior.

Expected outcome:
- Operators can verify laptop/Hetzner manifest ownership before migration work.
- The remaining Hetzner blockers are clearer: runtime duplicate-process proof,
  backup restore rehearsal, disk/health alerting, and reviewed migration steps.

Verification:
- SHOWN: compile check passed:
  ```bash
  ./.venv/bin/python -m py_compile \
    services/analytics/paper_campaign_ownership.py \
    scripts/check_paper_campaign_ownership.py \
    tests/test_paper_campaign_ownership.py \
    tests/test_check_paper_campaign_ownership_script.py
  ```
- SHOWN: targeted tests passed:
  ```bash
  ./.venv/bin/python -m pytest -q \
    tests/test_paper_campaign_ownership.py \
    tests/test_check_paper_campaign_ownership_script.py
  ```
  Result: `5 passed in 0.15s`.

Remaining risk:
- HIGH: campaign ownership affects persistent financial-evidence background
  jobs and state migration safety.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by human operator on
  2026-06-30 before PR #145 merge.

## 2026-06-29 - Short Context Readiness Report

Date: 2026-06-29

Active role: `ENGINEER`

Objective: add a fail-closed read-only readiness report for short/context data
so future replay work can tell whether stored crypto-edge evidence is
`live_public` ready or fixture-only.

What was found:
- SHOWN: the crypto-edge store already persists funding, open-interest, basis,
  quote, and order-book rows with a source label.
- SHOWN: the accepted short/context audit still blocks Binance derivatives
  public-data rows because exchange open failed with `NetworkError`.
- SHOWN: there was no compact operator command that classified whether required
  `live_public` row families were present before replay.

What changed:
- Added `services/analytics/short_context_readiness.py`.
- Added `scripts/check_short_context_readiness.py`.
- Added targeted service and CLI tests.
- Added `make check-short-context-readiness`.
- Updated `scripts/SCRIPTS.md`, `REMAINING_TASKS.md`, the short-context audit,
  the next-actions checkpoint, and added
  `docs/checkpoints/short_context_readiness_report_2026_06_29.md`.

Why this change:
- A read-only store check is the narrowest useful step before replay. It avoids
  contacting exchanges, starting collectors, or changing strategy/runtime
  behavior, while preventing accidental reliance on partial live-public
  derivatives context.

Expected outcome:
- Operators can run one short command before any short/context replay prototype.
- Replay remains fixture-only unless required `live_public` funding,
  open-interest, basis, and order-book row families are present.

Verification:
- `./.venv/bin/python -m py_compile services/analytics/short_context_readiness.py scripts/check_short_context_readiness.py tests/test_short_context_readiness.py tests/test_check_short_context_readiness_script.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_short_context_readiness.py tests/test_check_short_context_readiness_script.py`
  - SHOWN: `6 passed in 0.18s`.

Remaining risk:
- HIGH: this is short/derivatives research-governance logic and can affect
  whether future replay work relies on live-public context evidence.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-30 after PR #144 was opened for review.

## 2026-06-29 - Composite Hybrid Long Window Variants

Date: 2026-06-29

Active role: `ENGINEER`

Objective: add research-only long-window variants so the accepted
`composite_hybrid_v1_breakout_sma200_research` candidate can be evaluated
across at least three realized synthetic windows without enabling paper,
runtime, promotion, or order-routing behavior.

What was found:
- SHOWN: the prior accepted long-window proof gave the composite candidate one
  realized synthetic round trip.
- SHOWN: the active backlog required at least three realized synthetic windows
  before any paper decision is revisited.
- SHOWN: the composite remains unregistered from runtime strategy dispatch.

What changed:
- Added `long_trend_breakout_retest` and
  `long_trend_failed_extension` to both `services/backtest/evidence_cycle.py`
  and `services/backtest/evidence_windows.py`.
- Updated `tests/test_backtest_evidence_cycle.py` to require all three long
  SMA confirmation windows and prove each produces a closed composite trade.
- Added
  `docs/checkpoints/composite_hybrid_long_window_variant_proof_2026_06_29.md`.
- Updated `REMAINING_TASKS.md` and the composite/hybrid design checkpoint to
  show the accepted proof does not authorize paper advancement.

Why this change:
- Adding two deterministic research windows is the smallest way to close the
  synthetic participation coverage gap while preserving the existing safety
  boundary around paper and runtime paths.

Expected outcome:
- Composite research comparison has three realized synthetic windows available.
- The candidate can be reviewed with better synthetic participation evidence
  while remaining blocked from persistent paper campaigns until a separate
  accepted decision changes that boundary.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_evidence_cycle.py tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py`
  - SHOWN: `26 passed in 5.07s`.
- Read-only aggregate comparison:
  - SHOWN: composite row `rank=2`, `decision=improve`,
    `evidence_status=synthetic_only`, `confidence_label=low`,
    `closed_trades=3`, `closed_trade_window_count=3`,
    `active_window_count=3`, and `research_acceptance.accepted=false`.

Remaining risk:
- HIGH: financial strategy research evidence can affect future candidate
  ranking and campaign selection.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-29 after PR #143 was opened for review.

## 2026-06-29 - Pullback Stage 0 Make Targets

Date: 2026-06-29

Active role: `ENGINEER`

Objective: add short operator Make targets for the accepted pullback Stage 0
readiness and proof-verifier steps without adding a target that runs the
15-minute proof.

What was found:
- SHOWN: `scripts/check_pullback_stage0_readiness.py` and
  `scripts/verify_pullback_stage0_proof.py` exist and are read-only helper
  surfaces.
- SHOWN: `Makefile` exposed daily paper and candidate helper targets, but no
  pullback Stage 0 helper targets.
- SHOWN: the long proof remains an explicit operator-run command and should not
  be hidden behind a Make target.

What changed:
- Added `make pullback-stage0-readiness`.
- Added `make pullback-stage0-baseline`.
- Added `make pullback-stage0-verify`.
- Updated `make script-index`, `scripts/SCRIPTS.md`,
  `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md`,
  `REMAINING_TASKS.md`, and this work log.

Why this change:
- Make targets reduce copy/paste risk for the short baseline and verification
  steps while preserving explicit operator control over the long proof run.

Expected outcome:
- The operator can run the accepted short proof helpers through stable Make
  commands and still must explicitly choose when to run the 15-minute isolated
  Stage 0 proof.

Verification:
- `make -n pullback-stage0-readiness`
  - SHOWN: expands to `./.venv/bin/python scripts/check_pullback_stage0_readiness.py`.
- `make -n pullback-stage0-baseline`
  - SHOWN: expands to
    `./.venv/bin/python scripts/verify_pullback_stage0_proof.py --record-baseline`.
- `make -n pullback-stage0-verify`
  - SHOWN: expands to `./.venv/bin/python scripts/verify_pullback_stage0_proof.py`.
- `make script-index`
  - SHOWN: lists all three pullback Stage 0 helper targets.

Remaining risk:
- LOW: Makefile/docs wrapper only; no collector start, restore, manifest,
  campaign, or order-routing behavior changes.
- Acceptance state: `ACCEPTED`.

## 2026-06-29 - Pullback Stage 0 Proof Verifier

Date: 2026-06-29

Active role: `ENGINEER`

Objective: add a read-only baseline and verifier for the pending
`pullback_recovery_default` Stage 0 proof, without running the 15-minute proof.

What was found:
- SHOWN: the first pullback Stage 0 state directory still contains pre-fix
  session evidence and cannot be accepted as the post-fix proof.
- SHOWN: the checkpoint requires canonical fill-count isolation, public-OHLCV
  provenance, clean completion, and no persistent campaign conversion.
- SHOWN: canonical fill-count isolation cannot be proven after the fact without
  a before-count baseline.

What changed:
- Added `services/analytics/pullback_stage0_proof_verifier.py` with
  `build_pullback_stage0_baseline()` and
  `build_pullback_stage0_verification()`.
- Added `scripts/verify_pullback_stage0_proof.py`:
  - `--record-baseline` captures canonical and challenger fill counts before
    the long proof.
  - default verification checks post-baseline completion, expected commit,
    public-OHLCV provenance, strategy attribution, runtime status, and canonical
    fill-count isolation.
- Added targeted service and CLI tests.
- Updated `scripts/SCRIPTS.md`, the pullback checkpoint, `REMAINING_TASKS.md`,
  and this work log.

Why this change:
- The long proof remains operator-run, but the repo now carries the proof
  validation workflow instead of relying on manual inspection of JSONL,
  runtime status, and SQLite counts.
- Capturing the baseline immediately before the long command is the narrowest
  way to prove canonical paper history was not contaminated.

Expected outcome:
- The operator can run a short baseline command, then the 15-minute isolated
  proof, then a short verifier command that returns pass/fail evidence.
- Persistent `pullback_recovery_default` campaigns remain blocked until the
  verifier passes and the proof is independently accepted.

Verification:
- `awk 'length($0)>100 {print FILENAME ":" FNR ":" length($0) ":" $0}' services/analytics/pullback_stage0_proof_verifier.py scripts/verify_pullback_stage0_proof.py tests/test_pullback_stage0_proof_verifier.py tests/test_verify_pullback_stage0_proof_script.py`
  - SHOWN: no over-100-column lines after formatting.
- `./.venv/bin/python -m py_compile services/analytics/pullback_stage0_proof_verifier.py scripts/verify_pullback_stage0_proof.py tests/test_pullback_stage0_proof_verifier.py tests/test_verify_pullback_stage0_proof_script.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_pullback_stage0_proof_verifier.py tests/test_verify_pullback_stage0_proof_script.py`
  - SHOWN: `6 passed in 0.22s`.
- `./.venv/bin/python scripts/verify_pullback_stage0_proof.py --record-baseline --json --no-write`
  - SHOWN: produced a read-only baseline with canonical fill count `174`,
    challenger fill count `0`, and expected commit `9924f0c77`.
- `CBP_STATE_DIR=/private/tmp/cbp-pullback-stage0-verifier ./.venv/bin/python scripts/verify_pullback_stage0_proof.py --record-baseline --json`
  - SHOWN: wrote only verifier baseline artifacts under
    `/private/tmp/cbp-pullback-stage0-verifier/data/pullback_stage0_verification/`.
- `git diff --check`
  - SHOWN: passed.
- `find scripts -maxdepth 1 -type f -name '*.py' | wc -l`
  - SHOWN: root `scripts/` currently contains `105` Python entrypoints.

Remaining risk:
- HIGH: strategy campaign proof workflow and future evidence acceptance path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-29 for PR #141.

## 2026-06-29 - Pullback Stage 0 Backlog Alignment

Date: 2026-06-29

Active role: `ENGINEER`

Objective: align the active backlog and pullback checkpoint after PR #139
merged, so operators do not re-review an already accepted readiness report.

What was found:
- SHOWN: PR #139 merged as `f26dd965e`.
- SHOWN: `REMAINING_TASKS.md` and the pullback checkpoint still described the
  readiness report review as part of the next action.
- SHOWN: the actual remaining pullback step is the operator-run 15-minute
  isolated Stage 0 proof.

What changed:
- Updated `REMAINING_TASKS.md` to mark the pullback readiness report as
  recently completed and keep the full Stage 0 run as the active remaining
  task.
- Updated `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md` to
  record PR #139 acceptance and remove the stale review step from `Next Action`.

Why this change:
- The backlog should reflect the current operator decision point. Leaving the
  completed readiness review in the next action creates avoidable workflow
  ambiguity.

Expected outcome:
- Future check-ins point directly at the full post-fix Stage 0 proof command
  and preserve the rule that persistent pullback campaigns remain blocked until
  that proof is accepted.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "Review and accept the read-only Stage 0 readiness|then run the full post-fix isolated Stage 0 proof|readiness report review" REMAINING_TASKS.md docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: no active stale next-action wording remains; the only remaining
    `readiness report review` hit is this work-log entry describing the
    corrected stale state.

Remaining risk:
- LOW: docs-only accepted-state alignment.
- Acceptance state: `ACCEPTED`.

## 2026-06-29 - Pullback Stage 0 Readiness Report

Date: 2026-06-29

Active role: `ENGINEER`

Objective: add a short, read-only readiness report for the accepted
`pullback_recovery_default` Stage 0 proof without running the 15-minute
collector command or enabling a persistent campaign.

What was found:
- SHOWN: `pullback_recovery` is supported by strategy validation and the
  strategy registry.
- SHOWN: `pullback_recovery_default` exists as a preset.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py` maps
  `pullback_recovery` to `pullback_recovery_default` by default and supports
  the explicit one-shot proof flags.
- SHOWN: the checkpoint still requires the full post-fix isolated Stage 0 run,
  but the operator requested no long-running commands unless handed off.

What changed:
- Added `services/analytics/pullback_stage0_readiness.py`, a read-only report
  builder that validates strategy wiring, preset validation, collector session
  attribution, challenger-state isolation, and active campaign-manifest
  ownership conflicts.
- Added `scripts/check_pullback_stage0_readiness.py`, a root CLI that writes
  readiness artifacts by default or prints JSON with `--no-write`.
- Added targeted tests for the report builder and CLI wrapper.
- Updated `scripts/SCRIPTS.md`, the pullback campaign checkpoint,
  `REMAINING_TASKS.md`, and this work log.

Why this change:
- The full Stage 0 proof is intentionally a 15-minute operator-run command.
  A short readiness report removes avoidable wiring/state-isolation ambiguity
  before that command is run, without contaminating canonical paper evidence.
- The change is smaller and safer than adding a persistent campaign or starting
  another collector from automation.

Expected outcome:
- Operators can run a fast readiness check, inspect the exact Stage 0 command,
  and confirm no manifest/state conflict exists before starting the isolated
  proof manually.
- The actual Stage 0 campaign proof remains pending until the operator runs the
  printed long command.

Verification:
- `./.venv/bin/python -m py_compile services/analytics/pullback_stage0_readiness.py scripts/check_pullback_stage0_readiness.py tests/test_pullback_stage0_readiness.py tests/test_check_pullback_stage0_readiness_script.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_pullback_stage0_readiness.py tests/test_check_pullback_stage0_readiness_script.py`
  - SHOWN: `5 passed in 0.19s`.
- `./.venv/bin/python scripts/check_pullback_stage0_readiness.py --json --no-write`
  - SHOWN: `status=ready_for_operator_stage0`, `blocking_checks=[]`, and all
    safety mutation flags false.
- `CBP_STATE_DIR=/private/tmp/cbp-pullback-stage0-readiness ./.venv/bin/python scripts/check_pullback_stage0_readiness.py --json`
  - SHOWN: wrote only pullback readiness report artifacts under
    `/private/tmp/cbp-pullback-stage0-readiness/data/pullback_stage0_readiness/`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: strategy campaign workflow and future evidence collection path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-29 for PR #139 after all 9 GitHub checks passed.

## 2026-05-28 - Master Integration Branch Refresh With Shadow Evidence

Date: 2026-05-28

Active role: `ENGINEER`

Objective: refresh draft PR #44 with the latest accepted `review-stabilized`
tip after the shadow spread evidence fix and acceptance-log update.

What was found:
- SHOWN: main `review-stabilized` was clean and synced at
  `4c414b256 docs: accept shadow spread evidence fix`.
- SHOWN: the existing PR #44 branch
  `codex/master-review-stabilized-integration` did not contain `4c414b256`.
- SHOWN: merging latest `review-stabilized` into the integration branch merged
  source changes cleanly and produced one content conflict in
  `docs/work_log/review_stabilized_work_log.md`.

What changed:
- Resolved the work-log conflict by preserving the prior master-integration
  entry plus the newer PR #10 and shadow-spread evidence entries.
- Refreshed the integration branch with the accepted shadow-gate evidence
  changes from `review-stabilized`.
- Left `master` unchanged.

Why this change:
- PR #44 is the current review surface for moving `review-stabilized` toward
  `master`; it must carry the latest accepted work or reviewers will audit a
  stale integration branch.
- Keeping the integration conflict resolution on the PR branch avoids repeating
  temp-worktree recovery work.

Expected outcome:
- PR #44 remains the single reviewable master-integration branch and now
  includes the latest accepted shadow evidence work.
- Future master merge review can focus on PR #44 instead of chasing branch
  drift between `review-stabilized` and the integration branch.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_check_promotion_gates.py tests/test_service_control_path.py tests/test_service_ctl_smoke.py tests/test_safe_wrapper_import_side_effects.py tests/test_intent_services_safe_import.py tests/test_hardening_smoke.py tests/test_run_bot_runner.py tests/test_intent_services_safe_runtime_config.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `102 passed in 1.68s`.

Remaining risk:
- HIGH: master integration branch and promotion evidence behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `4ce4d083e`.

## 2026-05-28 - Master Integration Branch Refresh

Date: 2026-05-28

Active role: `ENGINEER`

Objective: update the existing `codex/master-review-stabilized-integration`
worktree with the latest accepted `review-stabilized` tip without changing
`master`.

What was found:
- SHOWN: `review-stabilized` was clean and synced at
  `507d9f05d docs: fix work log audit trail`.
- SHOWN: local `master...review-stabilized` comparison reported `64 / 84`.
- SHOWN: the existing integration worktree at
  `/private/tmp/cryptkeep-master-review-stabilized-integration` was on
  `codex/master-review-stabilized-integration`.
- SHOWN: merging latest `review-stabilized` into that integration branch
  produced four add/add conflicts:
  - `scripts/run_bot_runner.py`
  - `scripts/run_intent_executor_safe.py`
  - `scripts/run_intent_reconciler_safe.py`
  - `scripts/service_ctl.py`

What changed:
- Resolved the four conflicts by taking the `review-stabilized`
  executable-wrapper shape.
- Preserved executable bits on the four wrapper files.
- Left `master` and the main `review-stabilized` worktree unchanged.

Why this change:
- The integration branch is the correct place to absorb master/review branch
  conflicts before any canonical `master` update.
- The `review-stabilized` wrapper shape preserves direct script execution,
  avoids import-time side effects, and matches the service-control text test.
- Pushing the integration branch prevents the resolved worktree from being lost
  if the temporary worktree is removed.

Expected outcome:
- `codex/master-review-stabilized-integration` contains the latest accepted
  `review-stabilized` work plus the existing master integration resolution.
- Reviewers can inspect one branch for the master update instead of recovering
  temp-state conflict work.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_service_control_path.py tests/test_service_ctl_smoke.py tests/test_safe_wrapper_import_side_effects.py tests/test_intent_services_safe_import.py tests/test_hardening_smoke.py tests/test_run_bot_runner.py tests/test_intent_services_safe_runtime_config.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `50 passed in 1.00s`.

Remaining risk:
- HIGH: master integration and script entrypoint behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after PR #44 was created.

## 2026-05-28 - Paper Campaign Check and Shadow Signal Spread Evidence

Date: 2026-05-28

Active role: `ENGINEER`

Objective: verify the paper evidence campaign is still progressing and close
the immediate shadow-gate spread/depth logging gap before the paper gate clears.

What was found:
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py --status` reported
  the collector `pid_alive=true`, `status=idle`, `reason=waiting_for_next_day`,
  and `last_completed_day=2026-05-28`.
- SHOWN: `scripts/check_promotion_gates.py --json` reported `23/30` days and
  `7/10` round trips, with manual review still required.
- SHOWN: `scripts/run_paper_sim_monitor.py --status` reported monitor
  `status=stopped`, `recommendation=continue`, and active watches. This is
  expected after the daily collector stops run components.
- SHOWN: `scripts/check_promotion_gates.py --stage shadow --json` reported
  `All signals logged with spread/depth data` as failed across `33251`
  historical signal records.
- SHOWN: historical `es_daily_trend_v1` signal records had no spread/depth keys.

What changed:
- Added `_market_quality_evidence_extra(...)` in
  `services/strategy_runner/ema_crossover_runner.py`.
- Public-OHLCV signal evidence now merges local market-quality fields into
  `evidence_extra`, including `spread_bps` when fresh bid/ask data is present.
- Updated the shadow gate to recognize `spread_bps` and explicit depth keys.
- Added tests for the market-quality evidence helper and shadow gate
  spread/depth recognition.
- Updated the next-actions checkpoint with campaign status and shadow-gate
  implementation proof.

Why this change:
- The shadow checklist requires contemporaneous spread/depth data before
  paper -> shadow/sandbox review.
- Existing historical signals could never satisfy that gate because the runner
  did not attach market-quality fields to signal evidence.
- Using the local tick snapshot path avoids adding network calls to the signal
  path and aligns with the existing market-quality guard.

Expected outcome:
- Future public-OHLCV signal records include `spread_bps` when the tick
  publisher has fresh bid/ask data.
- The shadow gate can distinguish new market-quality-stamped signal evidence
  from legacy unstamped evidence.
- Existing historical signal evidence remains honestly failing until replaced
  or supplemented by fresh stamped runs.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_check_promotion_gates.py`
  - SHOWN: `52 passed in 0.80s`.
- `python3 -c "... _market_quality_evidence_extra('coinbase','BTC/USDT') ..."`
  - SHOWN: current idle tick data was stale, returning `market_quality_reason:
    stale_tick`; no `spread_bps` was emitted during idle.

Remaining risk:
- HIGH: promotion evidence and shadow-gate behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `9f0dd8b0c`.

## 2026-05-28 - PR #10 Supersession Closure and Checkpoint Refresh

Date: 2026-05-28

Active role: `ENGINEER`

Objective: close the stale PR #10 audit-noise item after verifying the fix is
already present on `review-stabilized`, and update the visible checkpoint.

What was found:
- SHOWN: PR #10 was open against `review-stabilized` from
  `audit/defect-05-null-overwrite`.
- SHOWN: PR #10 contained commit
  `5858dcc1969ec68763a11dc85fe589ca7de5a755`.
- SHOWN: that exact commit is not an ancestor of `review-stabilized`.
- SHOWN: `6cc95f678 fix: preserve queue ids on guarded status updates` is an
  ancestor of `review-stabilized`.
- SHOWN: current paper/live queue code preserves existing client, linked, and
  exchange order ids with `COALESCE`.

What changed:
- Closed PR #10 with an audit comment referencing `6cc95f678`.
- Updated `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  mark PR #10 complete and record PR #44 as the preserved master-integration
  draft PR.
- Updated this work log so the repository records the GitHub housekeeping work.

Why this change:
- Leaving a superseded PR open creates false audit noise and makes it look like
  a queue-id preservation defect is still unresolved.
- The checkpoint should reflect current repository state instead of stale
  pending work.

Expected outcome:
- Reviewers can see that PR #10 is closed because the accepted equivalent fix is
  already on `review-stabilized`.
- The remaining highest structural item is review/merge decision for PR #44,
  not recovery of the old temp integration worktree.

Verification:
- `gh pr view 10 --json ...`
  - SHOWN: PR #10 was open before closure.
- `gh pr view 10 --json number,state,url,title`
  - SHOWN: PR #10 state is `CLOSED` after closure.
- `git merge-base --is-ancestor 6cc95f678 review-stabilized`
  - SHOWN: passed.
- `rg -n "COALESCE\\(\\?, client_order_id\\)|COALESCE\\(\\?, linked_order_id\\)|COALESCE\\(\\?, exchange_order_id\\)" storage/intent_queue_sqlite.py storage/live_intent_queue_sqlite.py`
  - SHOWN: matched current queue preservation paths.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_queue_update_status_preserves_ids.py`
  - SHOWN: `2 passed in 0.08s`.

Remaining risk:
- LOW: GitHub PR hygiene and checkpoint accuracy.
- Acceptance state: `ACCEPTED`.

## 2026-05-28 - Work Log Audit Corrections and Next-Actions Checkpoint

Date: 2026-05-28

Active role: `ENGINEER`

Objective: correct work-log acceptance states, add the missing high-risk
promotion-ladder entry, and make the broader next-action list visible in git.

What was found:
- SHOWN: the auditor identified four work-log accuracy issues:
  - `84aa49113` still showed `READY_FOR_INDEPENDENT_REVIEW`.
  - `e06d49371` had no entry.
  - several entries used vague "accepted by later review" wording.
  - `9f90a8d2e` had ambiguous acceptance wording.
- SHOWN: `git show e06d49371` changed promotion ladder code, docs, digest
  wiring, and tests.
- SHOWN: local `master...review-stabilized` comparison reports `64 / 83`.
- SHOWN: `REMAINING_TASKS.md` documents the master integration conflict list.

What changed:
- Updated `84aa49113` and `9f90a8d2e` acceptance states to `ACCEPTED` with
  auditor/session references.
- Added a full entry for `e06d49371`.
- Replaced "accepted by later review" with reviewer/date/session references.
- Added `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` with
  the prioritized task list and SHOWN/CLAIMED/UNVERIFIED evidence labels.

Why this change:
- The work log is now a governed artifact under `AGENTS.md`.
- Incorrect or vague acceptance states weaken the audit trail.
- The broader next-action list needs to be visible in git instead of existing
  only in chat.

Expected outcome:
- Future readers can trace accepted high-risk changes to an auditor/date/session
  reference.
- The promotion-ladder coupling fix is represented in the governed work log.
- Master integration, PR cleanup, paper campaign monitoring, shadow prep,
  safety wiring, and CI-fixture work are tracked as visible pending actions.

Verification:
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- MEDIUM: documentation accuracy and governance traceability.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator in
  the 2026-05-28 audit session after commit `507d9f05d`.

## 2026-05-27 - Paper Gate Threshold and Manual Review

Commit: `84aa49113 fix: align paper gate threshold with slow turnover`

Active role: `ENGINEER` then `GATE`

Objective: make the paper-stage round-trip threshold coherent for a daily
slow-turnover strategy without implying profitability.

What was found:
- SHOWN: `check_promotion_gates.py` reported `7/50, 43 remaining`.
- SHOWN: `docs/DECISION_FRAMEWORK.md` and
  `docs/strategies/es_daily_trend_v1.md` used a 50+ paper round-trip gate.
- SHOWN: the strategy spec says the holding period is days to months, making
  50 paper round trips an impractical paper-to-sandbox blocker.
- SHOWN: the machine gate checked positive average PnL but did not machine-check
  win rate and avg win/loss against backtest expectations.

What changed:
- Paper-stage round-trip threshold changed from `50` to `10` in
  `services/control/promotion_thresholds.py`.
- Gate label and progress output changed to `10+ completed round trips`.
- `50+` was retained in docs as a later research/live-capital confidence floor.
- `check_promotion_gates.py` now emits:
  - `machine_ready`
  - `manual_review_required`
  - `manual_review`
- The manual-review block surfaces the outstanding win-rate and avg win/loss vs
  backtest comparison and includes observed paper-history metrics.
- Docs now state that 10+ round trips validates the paper execution path and
  does not prove profitability.

Why this change:
- A slow daily strategy cannot reasonably be blocked from sandbox/shadow review
  by a threshold that may require months or years.
- Lowering the paper threshold without surfacing manual review would create a
  false readiness signal.
- Keeping `50+` as a later confidence floor preserves the stronger evidence bar
  for larger live-capital decisions.

Expected outcome:
- The machine gate reports current progress as `7/10, 3 remaining`.
- Even after machine thresholds pass, `ready=false` while manual review remains
  outstanding.
- Operators see that sandbox/shadow review is path validation, not a
  profitability endorsement.

Verification:
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `7/10, 3 remaining`
  - SHOWN: `manual_review_required=true`
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `67 passed`
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `1907 passed, 33 skipped`

Remaining risk:
- HIGH: promotion-gate policy and financial/operator decision logic.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor in the 2026-05-28 audit session
  after the `manual_review_required` clarification, targeted tests, and full
  suite proof (`1907 passed, 33 skipped`).

## 2026-05-27 - Paper Promotion Progress in Monitor

Commit: `9f90a8d2e feat: surface paper promotion progress in monitor`

Active role: `ENGINEER` then `GATE`

Objective: make promotion-gate progress visible in the paper sim monitor and
Operations dashboard so the operator does not have to poll CLI output manually.

What was found:
- SHOWN: `check_promotion_gates.py --json` exposed remaining day and round-trip
  thresholds.
- SHOWN: paper sim monitor status exposed current campaign state and watches but
  did not include authoritative promotion threshold progress.
- SHOWN: stopped monitor status could preserve a stale PID and report
  `pid_alive=true` after the PID file disappeared.

What changed:
- Added service-layer promotion threshold helpers:
  - `services/control/promotion_thresholds.py`
  - `services/control/paper_promotion_progress.py`
- Paper sim monitor now includes `promotion_progress`,
  `promotion_thresholds_ready`, and `promotion_progress_summary`.
- Operations dashboard table now shows promotion threshold readiness and
  progress.
- Stopped monitor status no longer trusts stale status PIDs unless the monitor is
  running or starting.
- `docs/GOLDEN_PATH.md` documents that the monitor surfaces promotion progress.

Why this change:
- Operator-facing monitor output should distinguish current campaign evidence
  from promotion readiness.
- The service-layer helper preserves the repo rule against services importing
  scripts.
- Stale PID correction prevents reused OS PIDs from making a stopped monitor look
  alive.

Expected outcome:
- Monitor and dashboard show threshold progress directly.
- A local monitor recommendation cannot be mistaken for promotion readiness.
- Stopped monitor status reconciles correctly.

Verification:
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: promotion progress appeared in status.
  - SHOWN: stopped monitor reported `pid=null`, `pid_alive=false`.
- Targeted monitor/dashboard/gate tests:
  - SHOWN: `66 passed`
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `1906 passed, 33 skipped`

Remaining risk:
- HIGH: background-job/operator gate visibility.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor in the 2026-05-28 audit session as
  part of the paired monitor/gate-policy review.

## 2026-05-18 - Target-Strategy Paper Promotion Gating

Commit: `e06d49371 fix: scope paper promotion gating to target strategy`

Active role: `ENGINEER` then `GATE`

Objective: decouple paper -> sandbox promotion readiness from the global
leaderboard top row and evaluate the named target strategy's own evidence row.

What was found:
- SHOWN by the audit finding: `breakout_donchian` could block
  `es_daily_trend_v1` paper -> sandbox review because the ladder evaluated the
  global top row.
- SHOWN by commit diff: `dashboard/services/promotion_ladder.py` used top-row
  helpers and was changed to accept and normalize a target `strategy_id`.
- SHOWN by commit diff: paper -> sandbox criteria changed from "Top strategy"
  wording to "Target strategy" wording.
- SHOWN by commit diff: sandbox -> tiny-live kept the top-strategy policy.

What changed:
- Added target-strategy normalization and lookup in
  `dashboard/services/promotion_ladder.py`.
- `build_promotion_readiness(...)` now accepts `strategy_id` for paper ->
  sandbox review.
- Paper -> sandbox blockers now evaluate the target row's recommendation,
  closed trades, evidence status, confidence, and post-cost return.
- Sandbox -> tiny-live review remains portfolio/top-strategy based.
- `docs/safety/strategy_promotion_ladder.md` documents the policy split.
- Tests were added for target-strategy paper gating and digest wiring.

Why this change:
- Paper -> sandbox answers whether a specific strategy has enough controlled
  behavior to shadow with real infrastructure.
- A different strategy with synthetic-only or weak evidence should not block a
  target strategy's paper-stage review.
- Portfolio-wide/top-strategy gating is still appropriate before real-capital
  exposure at the later sandbox -> tiny-live stage.

Expected outcome:
- `es_daily_trend_v1` paper -> sandbox readiness is judged from the
  `sma_200_trend` / target strategy evidence row.
- A synthetic-only global top strategy no longer creates an incoherent paper
  promotion blocker.
- Later live-capital review still requires the strongest portfolio candidate to
  be acceptable.

Verification:
- SHOWN by audit record supplied in this session: `34 tests pass`.
- SHOWN by commit diff: tests added in `tests/test_promotion_ladder.py` and
  `tests/test_dashboard_home_digest.py`.

Remaining risk:
- HIGH: promotion policy and operator gate behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: auditor sign-off on `e06d49371` in the 2026-05 audit
  session: "policy fix is correct, scoped correctly, and tested."

## 2026-05-27 - Promotion Gate Output Clarity

Commits:
- `183ac148e fix: suppress passed gate hints`
- `4354ca665 fix: show remaining paper gate thresholds`

Active role: `ENGINEER`

Objective: make gate output more actionable and reduce operator confusion.

What was found:
- SHOWN: passed gates could still include remediation hints.
- SHOWN: threshold gates did not clearly show remaining days/trips.

What changed:
- Passed gates now suppress hints.
- Paper days and round-trip gates now include observed/required counts and
  remaining counts.

Why this change:
- Passed gate hints make status output look degraded when it is not.
- Remaining counts are the operator's next-action data.

Expected outcome:
- Gate output should focus attention on actual blockers.
- Operators can see exactly how many days/trips remain.

Verification:
- SHOWN from prior handoff: targeted tests passed.
- SHOWN from later full-suite runs: full suite passed after these changes.

Remaining risk:
- LOW to MEDIUM: reporting-only, but promotion-gate output influences operator
  decisions.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` in the 2026-05 review-stabilized audit
  session after targeted gate-output verification.

## 2026-05-27 - No-Trade Evidence Windows and Script Compatibility

Commits:
- `7bf129bd5 fix: allow no-trade evidence windows`
- `108cbc403 fix: restore root script compatibility`

Active role: `ENGINEER`

Objective: prevent valid no-trade daily sessions and root script entrypoints
from blocking the evidence campaign.

What was found:
- SHOWN: daily paper runs can validly produce signal/session evidence without
  orders or fills.
- SHOWN: root script compatibility wrappers had regressed.

What changed:
- Promotion evidence presence allows no-trade windows when signal and session
  logs exist and no order/fill was expected.
- Root `scripts.*` compatibility wrappers were restored.

Why this change:
- A slow strategy often produces no trade on a valid day; treating that as an
  evidence failure makes the campaign unusable.
- Root script compatibility keeps documented operator commands runnable.

Expected outcome:
- No-trade daily sessions count as valid operational evidence.
- Existing script invocation paths continue to work.

Verification:
- SHOWN from prior handoff:
  - no-trade change full suite: `1902 passed, 33 skipped`
  - script compatibility full suite: `1900 passed, 33 skipped`

Remaining risk:
- MEDIUM: evidence semantics affect gate outcomes.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` in the 2026-05 review-stabilized audit
  session after full-suite proof (`1902 passed, 33 skipped` and `1900 passed,
  33 skipped` for the grouped changes).

## 2026-05-26 - Evidence Provenance and Gate Trust

Visible commits:
- `49c4570b7 fix: skip unattributed signal evidence`
- `2f44b97ad fix: report unknown provenance sources`
- `074856eb2 fix: report latest evidence log window in promotion gate`
- `b47bc3fed fix: require recent kill switch test in promotion gate`
- `705c6a10b fix: keep backtests out of runtime evidence`
- `6520636ad fix: align promotion gate paper history counts`
- `836cb42b7 fix: preserve paper evidence provenance`
- `f461a131c fix: require promotion evidence provenance`
- `1de9a3513 fix: stamp signal evidence provenance`

Active role: `ENGINEER`

Objective: make promotion evidence attributable, current-window based, and
separate from synthetic/backtest evidence.

What was found:
- SHOWN by commit history: the branch had repeated fixes around provenance,
  latest-window reporting, kill-switch recency, and paper-history counts.
- SHOWN by current gate output: current-window provenance is reported separately
  from all-time historical provenance diagnostics.

What changed:
- Signal evidence gained market-data provenance stamping.
- Unattributed signal evidence is skipped for promotion use.
- Promotion gates require non-sample provenance.
- Unknown provenance sources are reported.
- Latest-window evidence log status is reported.
- Kill-switch gate checks recency.
- Runtime evidence excludes backtest-derived evidence.
- Paper-history counts align with the trade journal.

Why this change:
- Promotion gates must not pass on synthetic, stale, or unattributed evidence.
- Latest-window checks prevent old bad/missing evidence from blocking a valid
  current evidence cycle while preserving diagnostics.

Expected outcome:
- Gate readiness is based on current, attributable paper evidence.
- Historical unknown/missing provenance remains visible as a diagnostic without
  automatically blocking the latest valid window.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for each individual commit is not in
  this retrospective.

Remaining risk:
- HIGH: promotion evidence logic.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later gate/full-suite verification remained
  clean after these commits.

## 2026-05-18 to 2026-05-26 - Paper Campaign Monitor and Operator Workflow

Visible commits:
- `92c2c35d7 feat: show paper sim monitor in home digest`
- `6f7482623 feat: add paper sim desktop alert setting`
- `6fcf705f8 fix: surface paper sim notification truth`
- `c3f61c15b feat: add dashboard paper sim watch controls`
- `b6ade1c66 feat: add paper sim watch notifications`
- `ada32aa7d fix: break digest monitor import cycle`
- `215fe908d fix: tighten home digest paper sim monitor wiring`
- `9f8efe2c2 Update test_dashboard_home_digest.py`
- `92626d032 feat: surface paper_sim_monitor in home digest builder`
- `6dc87550c fix: reconcile stopped paper sim monitor summary`
- `b1a470534 fix: surface paper evidence persistence phase`
- `c965f9786 fix: name evidence persistence in monitor summary`
- `73bb81d4c fix: supervise paper evidence collection daily`
- `08793e700 fix: surface idle paper evidence collector state`

Active role: `ENGINEER`

Objective: reduce manual polling by making paper evidence collection and monitor
state visible through runtime status, dashboard, home digest, watches, and
notifications.

What was found:
- SHOWN by commit history and current runtime status: the repo has a managed
  daily paper evidence collector and a paper sim monitor.
- SHOWN by current status: collector can be idle while waiting for the next UTC
  day and still be healthy.

What changed:
- Home digest surfaces paper sim monitor state.
- Dashboard Operations exposes monitor watch controls.
- Paper sim monitor can write watch reports and local desktop notification
  status.
- Paper evidence collector runs in a managed daily-loop path.
- Runtime summaries distinguish idle, persisting evidence, completed, stopped,
  and notification states.

Why this change:
- The operator should not have to remember files or manually poll low-level
  artifacts to know whether the campaign is working.
- Watch reports and notifications turn important state changes into durable
  artifacts.

Expected outcome:
- Operator can see campaign and monitor status from dashboard/home surfaces.
- Meaningful events such as fills, position closes, campaign completion, and
  investigate recommendations are visible.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for every listed commit is not in
  this retrospective.

Remaining risk:
- HIGH: background job/operator workflow.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later monitor/gate full-suite verification
  remained clean after these commits.

## 2026-05-18 to 2026-05-26 - Evidence Artifacts and Decision Records

Visible commits:
- `c1fbd6372 docs: add 2026-05-26 strategy decision record`
- `5ab5f3cee docs: refresh 2026-05-18 decision record`
- `27f6b8ab5 docs: add 2026-05-18 strategy decision record`
- `f73a3d069 docs: track master integration blocker`
- `89ee99159 fix: scope runtime ignore rules`
- `e3248ffff fix: restore script alignment wrappers`
- `ff2e3fba1 fix: bootstrap nested script entrypoints`
- `30d465ea7 fix: tolerate missing parity strategy config`

Active role: `ENGINEER`

Objective: keep evidence artifacts, decision records, ignore rules, and script
entrypoints aligned with the active branch state.

What was found:
- SHOWN by current docs: strategy decision records exist for 2026-05-18 and
  2026-05-26.
- SHOWN by commit history: runtime ignore rules, script wrappers, nested
  bootstraps, and missing parity strategy config were addressed.

What changed:
- Added/refreshed strategy decision records.
- Documented a master integration blocker.
- Scoped runtime ignore behavior.
- Restored alignment wrappers and nested script bootstrap paths.
- Tolerated missing parity strategy config.

Why this change:
- Decision records need to match canonical evidence, not temp proof artifacts.
- Script entrypoints and ignores must not create recurring git dirt or broken
  operator commands.

Expected outcome:
- Audit artifacts are tracked where appropriate.
- Temp/runtime artifacts do not recur as untracked git noise.
- Script paths remain runnable from documented entrypoints.

Verification:
- SHOWN from later full-suite runs: full suite passed after these commits.
- UNVERIFIED: exact targeted command output for every listed commit is not in
  this retrospective.

Remaining risk:
- LOW to MEDIUM: mostly documentation and compatibility, with some operational
  workflow impact.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: accepted by auditor through the 2026-05
  review-stabilized audit cycle; later branch verification remained clean after
  these commits.

## 2026-05-30 - PR #44 Integration Suite Repair

Active role: `ENGINEER`

Objective: repair the PR #44 `codex/master-review-stabilized-integration`
branch after the master integration full suite exposed regressions.

What was found:
- SHOWN: the original temporary integration worktree became prunable and no
  longer had a `.git` directory.
- SHOWN: the prunable directory still contained the interrupted repair edits,
  so it was treated as a recovery copy rather than deleted.
- SHOWN: `scripts.run_intent_executor` was missing at the root import path even
  though tests and runtime status writers import that canonical path.
- SHOWN: `scripts.run_ws_ticker_feed` used a star-import wrapper, so callers
  monkeypatching the root module did not affect the relocated implementation.
- SHOWN: `test_place_order_fail_closed.py` could read a repo-local
  `risk_sink_failed.flag`, masking the intended fail-closed assertions.
- SHOWN: older live-arming tests conflicted with the hardened policy: fresh
  persisted arming is valid, stale persisted arming is blocked.
- SHOWN: `LiveIntentQueueSQLite.upsert_intent` still mutated existing queued
  rows, conflicting with insert-only queue-authority expectations.
- SHOWN: paper reconciliation marked an intent filled before journal inserts,
  which could hide a fill-journal failure.

What changed:
- Recreated a clean integration worktree at
  `/private/tmp/cryptkeep-master-review-stabilized-integration-v2`.
- Added `scripts.run_intent_executor` compatibility aliasing to the relocated
  compat implementation.
- Converted the root `scripts.run_ws_ticker_feed` wrapper into an implementation
  module alias so CLI and imported behavior share one module object.
- Made live intent upsert insert-only for existing intent IDs; lifecycle changes
  remain under `update_status`.
- Reordered paper reconciliation so fills are journaled before an intent is
  marked filled.
- Isolated order fail-closed tests with per-test `CBP_STATE_DIR`.
- Updated older tests to the accepted live-arming persisted-state policy and to
  explicitly pass ticker symbol when environment defaults are irrelevant.

Why this change:
- The smallest safe repair was to preserve production fail-closed behavior and
  fix compatibility/test isolation around it.
- Deleting or bypassing `risk_sink_failed.flag` would have weakened a safety
  control; isolating tests proves the intended behavior without mutating
  operator state.
- Insert-only intent creation and journal-before-filled ordering keep state
  authority coherent in order/fill lifecycle paths.

Expected outcome:
- PR #44 can advance with the full suite green.
- Runtime import paths remain backward compatible after script relocation.
- Live/order fail-closed protections remain intact while tests no longer depend
  on repo-local runtime state.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_canonical_runtime_status_writers.py tests/test_intent_reconciler_fill_journal_order.py tests/test_live_arming_contract.py tests/test_live_arming_state_fallback.py tests/test_live_intent_upsert_insert_only.py tests/test_live_intent_queue_integrity.py tests/test_live_reconciler.py tests/test_place_order_fail_closed.py tests/test_run_ws_ticker_feed.py`
  was run from the integration worktree using the repository venv path and
  passed: `55 passed, 1 warning`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  was run from the integration worktree and passed:
  `2085 passed, 33 skipped, 13 warnings in 202.46s`.

Remaining risk:
- HIGH: master integration touches live/order/risk-adjacent lifecycle behavior
  and compatibility entrypoints.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported all checks passing and merge state
  `CLEAN`.

## 2026-05-30 - PR #44 Release Checklist Entrypoint Repair

Active role: `ENGINEER`

Objective: repair the PR #44 macOS PyInstaller CI failure after the integration
suite repair was pushed.

What was found:
- SHOWN: GitHub Actions macOS build failed before packaging work could run.
- SHOWN: the failing command was
  `python scripts/release_checklist.py --sync-requires --pyinstaller`.
- SHOWN: the repository had `scripts/release/release_checklist.py` but no root
  `scripts/release_checklist.py` compatibility entrypoint.
- SHOWN: after adding the root wrapper, dry-run exposed a relocated-script root
  bug: `scripts/release/release_checklist.py` resolved `ROOT` to `scripts/`,
  so it could not find repo-root `pyproject.toml`.

What changed:
- Added `scripts/release_checklist.py` as a root compatibility entrypoint.
- The wrapper executes `scripts.release.release_checklist` as `__main__` via
  `runpy` so the relocated script keeps its CLI behavior.
- Corrected `scripts/release/release_checklist.py` root calculation from
  `parent.parent` to `parents[2]`.
- Added a regression test that runs
  `scripts/release_checklist.py --dry-run` in a subprocess.

Why this change:
- The documented workflows and release docs all call the root
  `scripts/release_checklist.py` path.
- Fixing the entrypoint and underlying root calculation is smaller and safer
  than editing every workflow and doc path.
- `runpy` avoids importing and calling `main()` in a way that would bypass the
  relocated script's `__main__` setup.

Expected outcome:
- GitHub Actions can resolve the documented root release checklist command.
- The relocated release checklist can find repo-root release metadata.
- PyInstaller CI proceeds past the missing-file/root-resolution failure.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_remaining_compat_wrappers.py::test_release_checklist_root_wrapper_dry_run`
  passed: `1 passed`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/release_checklist.py --dry-run`
  passed and returned `ok=true`, `manifest_written=null`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/release/release_checklist.py --dry-run`
  passed and returned `ok=true`, `manifest_written=null`.
- UNVERIFIED: full PyInstaller packaging was not run locally because
  `--pyinstaller` writes build/release artifacts; GitHub CI remains the
  intended verification surface for that build.

Remaining risk:
- HIGH: release/desktop packaging CI path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported macOS and Windows desktop builds passing.

## 2026-05-30 - PR #44 Paper Runner Entrypoint Repair

Active role: `ENGINEER`

Objective: repair the remaining PR #44 CI failure in the main `validate`
workflow after desktop builds, sanity, ruff, mypy, and core pytest passed.

What was found:
- SHOWN: GitHub Actions main `validate` failed after the core pytest step
  passed with `1967 passed, 62 skipped`.
- SHOWN: the failing command was
  `python scripts/run_es_daily_trend_paper.py --dry-run`.
- SHOWN: the implementation exists at
  `scripts/dev/run_es_daily_trend_paper.py`, while CI and docs still call the
  historical root path.
- SHOWN: the CI workflow reads the root script source directly to assert the
  ManagedComponent contract marker `lock_dir=runtime_dir()`.

What changed:
- Added `scripts/run_es_daily_trend_paper.py` as a root compatibility
  entrypoint that delegates to `scripts.dev.run_es_daily_trend_paper`.
- Preserved the visible ManagedComponent contract marker in the root wrapper
  because the workflow intentionally checks the historical entrypoint source.
- Added a subprocess regression test for
  `scripts/run_es_daily_trend_paper.py --dry-run`.

Why this change:
- The CI and documentation contract is the root runner path.
- Restoring a compatibility wrapper is smaller and safer than editing multiple
  workflows and docs during master integration.
- Delegating with `runpy` avoids duplicating runner behavior.

Expected outcome:
- The main CI `Paper runner dry-run` step can resolve and execute the
  historical root runner path.
- The following workflow source-contract step still sees the expected
  ManagedComponent marker.

Verification:
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_remaining_compat_wrappers.py::test_es_daily_trend_paper_root_wrapper_dry_run`
  passed: `1 passed`.
- `CBP_STATE_DIR=/tmp/cbp_ci_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/run_es_daily_trend_paper.py --dry-run`
  passed and printed `DRY RUN: pre-flight passed. Stage=paper, kernel=allow`.
- Local reproduction of the CI ManagedComponent source-contract check passed:
  `ManagedComponent API contract: OK`.

Remaining risk:
- HIGH: paper-runner/operator workflow and CI integration path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-30 after PR #44 CI reported the main `validate` workflow passing.

## 2026-05-31 - Paper Gate Backtest Baseline Contract

Active role: `ENGINEER`

Objective: remove the ambiguity around the paper-gate checklist item requiring
observed win rate and average win/loss to be compared against backtest
expectations before `es_daily_trend_v1` can advance.

What was found:
- SHOWN: `scripts/check_promotion_gates.py --json` already surfaced
  `manual_review_required=true`.
- SHOWN: the gate included observed paper-history metrics for
  `sma_200_trend`: 7 closed trades, 14 fills, 28.6% win rate, +35.75 net
  realized PnL, +5.11 expectancy per closed trade.
- SHOWN: no machine-readable backtest baseline for `win_rate`, `avg_win`, and
  `avg_loss` existed in the strategy config, so the gate could only ask for
  manual comparison.

What changed:
- Added `promotion.paper.backtest_expectations` to
  `configs/strategies/es_daily_trend_v1.yaml` with `source`, `tolerance_pct`,
  `win_rate`, `avg_win`, and `avg_loss` fields.
- Updated `scripts/check_promotion_gates.py` so the paper gate reads those
  configured expectations, compares observed paper metrics against the
  configured tolerance, and marks the item as `machine_checked`,
  `machine_blocking`, or `manual_required`.
- Kept the current config values unset because no accepted closed-trade
  backtest baseline has been identified for `sma_200_trend`.
- Updated `docs/strategies/es_daily_trend_v1.md` and
  `docs/DECISION_FRAMEWORK.md` to document the config-backed baseline contract.
- Added tests for matching configured metrics, out-of-tolerance configured
  metrics, and the config contract existing before a baseline is accepted.

Why this change:
- The smallest safe fix is to create the machine-readable contract without
  inventing baseline numbers.
- A missing baseline must remain visible as `manual_review_required=true`;
  otherwise the gate can appear ready while the spec's performance-comparison
  item is still unresolved.

Expected outcome:
- When an accepted backtest baseline exists, the paper gate can compare
  observed paper metrics automatically.
- Until then, the gate remains blocked with explicit missing baseline fields
  and current observed paper metrics in JSON output.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `68 passed in 0.85s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `manual_review_required=true`.
  - SHOWN: missing baseline metrics are `win_rate`, `avg_win`, and `avg_loss`.
  - SHOWN: observed metrics include 7 closed trades, 14 fills, 28.6% win rate,
    +35.75 net realized PnL, and +5.11 expectancy per closed trade.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2095 passed, 33 skipped, 13 warnings in 382.38s`.

Remaining risk:
- HIGH: promotion-gate behavior for a financial strategy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-31 after targeted and full-suite verification.

## 2026-05-31 - Live Risk Limits Fail Closed From Runtime Config

Active role: `ENGINEER`

Objective: harden the live daily-loss risk-limit source of truth while
investigating the `daily_loss_halt_pct` wiring discrepancy.

What was found:
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` declares
  `daily_loss_halt_pct` as a percentage target.
- SHOWN: the live risk gate enforces absolute USD limits via
  `services/risk/live_risk_gates.py`.
- SHOWN: `LiveRiskLimits.from_trading_yaml()` read
  `canonical_runtime.json` directly and substituted broad hardcoded defaults
  when `risk.live.*` was absent.
- SHOWN: docs and a Phase 82 helper still referenced the removed
  `services/risk/live_risk_gates_phase82.py` path.

What changed:
- Changed `LiveRiskLimits.from_trading_yaml()` to load the canonical runtime
  trading config through `load_runtime_trading_config(path)`.
- Removed hardcoded fallback live-risk limits from that loader.
- Made missing or invalid `risk.live.*` return `None`, preserving fail-closed
  behavior in callers that block when limits are unavailable.
- Added regression tests proving the loader uses runtime config and fails
  closed when live risk limits are missing.
- Updated stale Phase 82 and strategy docs to point at
  `services/risk/live_risk_gates.py`.

Why this change:
- The percentage-to-USD translation still needs a separate accepted equity
  source; inventing that translation now would be unsafe.
- The smallest safety hardening is to prevent live risk gates from silently
  inventing default dollar limits when the canonical runtime config lacks
  explicit `risk.live.*` values.

Expected outcome:
- Live risk evaluation remains blocked when live dollar limits are missing or
  malformed.
- Operators see the current v1 contract clearly: strategy
  `daily_loss_halt_pct` is declarative, while live enforcement uses explicit
  `risk.live.max_daily_loss_usd`.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_risk_gates.py tests/test_placeholder_recovery_phase2.py tests/test_phase82_apply_safe_import.py tests/test_show_live_gate_inputs.py tests/test_live_executor_latency_safety_integration.py`
  - SHOWN: `43 passed in 0.90s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2097 passed, 33 skipped, 13 warnings in 355.48s`.

Remaining risk:
- HIGH: live risk-gate behavior and daily-loss safety control.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-05-31 after targeted and full-suite verification.

## 2026-06-01T09:19:28Z - SMA Backtest Parity Flat Exit

Active role: `ENGINEER`

Objective: make the parity backtest able to close `sma_200_trend` round trips
when the documented SMA rule flips from long to flat, without adding a new live
paper exit path.

What was found:
- SHOWN: `sma_200_trend` signal logic returns `flat` when price is below the
  SMA, but `signal_from_ohlcv()` keeps runtime `action=hold`.
- SHOWN: the paper runner owns position state and can emit sells from signal
  changes or the strategy-aware exit stack.
- SHOWN: historical paper orders include `sma_200_trend` sells with
  `signal_reason=sma200:long:...`, so not every closed paper trade was caused
  by the SMA flat signal.
- SHOWN: the 2026-05-26 `sma_200_trend` sell had
  `signal_reason=sma200:flat:regime:trending` and no persisted `exit_reason`,
  so the runtime path already has distinct exit behavior from the parity
  backtest simulator.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d.json` still produces 1 buy, 0 sells,
  and 0 closed trades for the default SMA path, so it is not a valid
  closed-trade baseline fixture.

What changed:
- Left `services/strategies/es_daily_trend.py::signal_from_ohlcv()` runtime
  behavior unchanged: a flat SMA signal still returns `action=hold`.
- Added a backtest-only translation in
  `services/backtest/parity_engine.py`: when the simulated strategy is already
  long, the strategy is `sma_200_trend`, and the computed signal is `flat`, the
  simulator treats that bar as a sell.
- Added a regression test proving `run_parity_backtest()` can close an SMA
  round trip on a flat signal.
- Added a regression test proving the runtime adapter still returns `hold` for
  flat, preserving live paper signal semantics.

Why this change:
- Changing the registry adapter to emit `sell` would alter live paper behavior
  and potentially introduce a second exit path.
- The smallest safe change is to fix the simulator's position-aware
  interpretation of the documented flat/exit condition while leaving runtime
  exit ownership unchanged.

Expected outcome:
- Backtest parity can now produce closed-trade metrics for `sma_200_trend`
  when the input OHLCV window contains both above-SMA entry and below-SMA exit
  participation.
- Live paper behavior is unchanged by this patch.
- The existing sample OHLCV remains insufficient as a closed-trade baseline;
  a deterministic SMA CI fixture is still required as separate work.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_backtest_parity_engine.py tests/test_strategy_registry.py`
  - SHOWN: `50 passed in 0.54s`.
- `./.venv/bin/python -m pytest -q tests/test_campaign_summary.py tests/test_es_signal_regression.py tests/test_paper_engine_integration.py tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_strategy_evaluation.py`
  - SHOWN: `46 passed in 0.98s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2099 passed, 33 skipped, 13 warnings in 388.18s`.
- Sample OHLCV proof:
  - SHOWN: `ok=true`, `bars=230`, `buy_count=1`, `sell_count=0`,
    `closed_trades=0`.

Remaining risk:
- HIGH: financial backtest semantics for a promoted paper strategy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-01 after targeted verification and fresh full-suite verification
  reported `2099 passed, 33 skipped, 13 warnings in 372.93s`.

## 2026-06-01T09:35:12Z - SMA 200 CI Round-Trip Fixture

Active role: `ENGINEER`

Objective: add a deterministic CI-only OHLCV fixture that proves the default
`sma_200_trend` parity path can produce a buy-to-sell round trip.

What was found:
- SHOWN: the previous parity fix made flat SMA exits possible in the backtest
  simulator, but the existing sample OHLCV still produced 1 buy, 0 sells, and
  0 closed trades for the default SMA path.
- SHOWN: there was no dedicated `sma_200_trend` fixture under
  `sample_data/ohlcv/` that intentionally crossed back below SMA-200 after
  entry.

What changed:
- Added `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`, a synthetic
  220-bar OHLCV sequence with 200 warmup bars, an above-SMA entry window, and a
  below-SMA exit window.
- Added a parity-engine regression test that loads the fixture and asserts one
  buy, one sell, one closed trade, an SMA long entry reason, an SMA flat exit
  reason, and scorecard fields needed by the manual review gate.

Why this change:
- A dedicated fixture is the smallest way to make the CI proof deterministic
  without treating synthetic data as promotion evidence.
- Keeping the fixture in `sample_data/ohlcv/` makes its purpose explicit and
  avoids changing live paper runtime behavior or strategy configuration.

Expected outcome:
- CI can prove `sma_200_trend` backtest mechanics for both entry and exit under
  default SMA parameters.
- The fixture remains a synthetic mechanics check only; it does not prove
  profitability, live readiness, or paper-promotion eligibility.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_signal_regression.py`
  - SHOWN: `14 passed in 0.29s`.
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_daily_trend.py tests/test_strategy_registry.py`
  - SHOWN: `51 passed in 0.45s`.

Remaining risk:
- LOW: synthetic fixture and test coverage only; no runtime strategy, order
  routing, evidence-gate, or live execution behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: same-thread low-risk closure after targeted regression
  verification.

## 2026-06-01T09:39:51Z - Post-Integration Master Catch-Up PR

Active role: `GATE`

Objective: preserve the accepted post-PR44 `review-stabilized` work in a
reviewable master catch-up PR without merging high-risk gate/risk changes
directly.

What was found:
- SHOWN: `origin/master` is an ancestor of `review-stabilized`.
- SHOWN: `git rev-list --left-right --count origin/master...review-stabilized`
  reported `0 5`, meaning `review-stabilized` is 5 commits ahead of
  `origin/master` with no new master-only commits.
- SHOWN: the ahead commits are `f6a67ef68`, `c9cd496b8`, `706e9468e`,
  `a3235229a`, and `e4ad5d99c`.
- SHOWN: `gh pr list --base master --head review-stabilized --state open`
  returned no existing open PR for this delta.

What changed:
- Created draft PR #45:
  `https://github.com/Ddthomas415/CryptKeep/pull/45`.
- Verified PR #45 is open, draft, targets `master`, uses
  `review-stabilized` as head, and reports `mergeable=MERGEABLE`.

Why this change:
- The old master-integration conflict debt was already resolved by PR #44, but
  five later accepted commits were still only on `review-stabilized`.
- A draft PR is the smallest safe handoff surface: it makes the delta visible
  without bypassing independent review or CI for high-risk financial gate and
  risk-control changes.

Expected outcome:
- Reviewers can evaluate the exact post-integration delta before master moves
  again.
- Master remains unchanged until PR #45 receives independent review and fresh
  CI/full-suite confirmation.

Verification:
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2100 passed, 33 skipped, 13 warnings in 367.83s`.
- Final PR-head gate run after pushing the acceptance record:
  `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2100 passed, 33 skipped, 13 warnings in 370.35s`.
- `gh pr view 45 --json number,title,state,isDraft,headRefName,baseRefName,url,mergeable`
  - SHOWN: PR #45 is `OPEN`, `isDraft=true`, `baseRefName=master`,
    `headRefName=review-stabilized`, and `mergeable=MERGEABLE`.
- `git status --short --branch`
  - SHOWN: `review-stabilized...origin/review-stabilized` before this
    work-log entry.

Remaining risk:
- HIGH: PR #45 contains promotion-gate, live risk-gate, and financial backtest
  semantics changes.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-01, with full-suite verification shown above.
- Gate outcome: PR #45 is ready to mark non-draft and merge after the final
  PR-head full-suite result shown above. This line is a docs-only proof update;
  no code or runtime behavior changed after the final suite run.

## 2026-06-03T00:34:50Z - Master Branch Protection Runbook

Active role: `ENGINEER`

Objective: remove ambiguous GitHub check names and document the required
`master` branch-protection settings after PR #45 proved the branch was
unprotected.

What was found:
- SHOWN: PR #45 merged into `master` while one GitHub `validate` workflow was
  still pending.
- SHOWN: the pending workflow later passed, but merge ordering showed that
  GitHub was not enforcing all expected checks before master updates.
- SHOWN: `gh api repos/Ddthomas415/CryptKeep/branches/master/protection`
  returned `Branch not protected`.
- SHOWN: two workflows exposed a job named `validate`, making a required-check
  rule ambiguous.

What changed:
- Added explicit check names for the always-on CI jobs:
  `CI validate`, `CI sanity`, and `Governance smoke`.
- Renamed the path-filtered script integrity job from generic `validate` to
  `script-path-integrity`.
- Added `docs/GITHUB_BRANCH_PROTECTION.md` with the required `master`
  protection settings and the exact status checks that should be required.

Why this change:
- Branch protection itself is external GitHub configuration, not repository
  code.
- The smallest safe repo-side fix is to make required check names unambiguous
  and document the external setting needed to prevent another pending-check
  merge.
- The path-filtered check is documented as non-global because requiring it for
  every PR would block unrelated changes where that workflow does not run.

Expected outcome:
- Future branch-protection setup can require the main CI jobs without confusing
  the main CI `validate` job with the path-filtered script integrity job.
- A reviewer or admin can audit `master` protection against a visible repo
  runbook instead of relying on chat history.

Verification:
- `./.venv/bin/python -c "import pathlib, yaml; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.github/workflows').glob('*.yml')]; print('workflow_yaml_ok')"`
  - SHOWN: `workflow_yaml_ok`.
- `./.venv/bin/python scripts/validate.py --quick`
  - SHOWN: repo doctor and alignment guard passed.
  - SHOWN: quick pytest subset reported `13 passed in 1.33s`.
- `git diff --check`
  - SHOWN: no whitespace errors.
- PR #46 GitHub checks after independent review:
  - SHOWN: `CI validate` passed in `8m45s`.
  - SHOWN: `CI sanity` passed in `4m29s`.
  - SHOWN: `Build (macos-latest)` passed in `1m21s`.
  - SHOWN: `Build (windows-latest)` passed in `2m22s`.
  - SHOWN: `Governance smoke`, `script-path-integrity`, and
    `GitGuardian Security Checks` passed.

Remaining risk:
- MEDIUM: CI/governance workflow naming and external repository protection.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03, with PR #46 CI passing under the new explicit check names.
- Remaining action: merge PR #46, align `review-stabilized` with `master`, then
  configure GitHub branch protection using `docs/GITHUB_BRANCH_PROTECTION.md`.

## 2026-06-03T01:02:12Z - Master Branch Protection Applied

Active role: `GATE`

Objective: apply the documented `master` branch protection after PR #46 merged
with explicit CI check names.

What was found:
- SHOWN: PR #46 merged into `master` with merge commit
  `be005450ec99258046788b9729f7b060fcdc6bde`.
- SHOWN: `origin/master` and `origin/review-stabilized` were aligned at the PR
  #46 merge commit before applying protection.
- SHOWN: GitHub branch protection was previously absent on `master`.

What changed:
- Applied GitHub branch protection to `master` through the GitHub API.
- Required status checks are now strict and include:
  `CI validate`, `CI sanity`, `Governance smoke`, `Build (macos-latest)`,
  `Build (windows-latest)`, and `GitGuardian Security Checks`.
- Enabled admin enforcement.
- Required pull-request review with one approving review.
- Disabled force pushes and branch deletion.
- Left linear history disabled because audited integration PRs use merge
  commits.

Why this change:
- PR #45 proved `master` could advance before all expected checks completed.
- The branch-protection runbook merged in PR #46 made the required settings
  explicit; applying them closes the external GitHub governance gap.

Expected outcome:
- `master` can no longer be advanced through the GitHub PR path until required
  checks are green and at least one PR approval exists.
- Future master updates should use PRs and will expose missing or renamed check
  contexts immediately.

Verification:
- `gh api repos/Ddthomas415/CryptKeep/branches/master/protection`
  - SHOWN: `required_status_checks.strict=true`.
  - SHOWN: required contexts are `CI validate`, `CI sanity`,
    `Governance smoke`, `Build (macos-latest)`, `Build (windows-latest)`,
    and `GitGuardian Security Checks`.
  - SHOWN: `enforce_admins.enabled=true`.
  - SHOWN: `required_approving_review_count=1`.
  - SHOWN: `allow_force_pushes.enabled=false`.
  - SHOWN: `allow_deletions.enabled=false`.
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 0` before this work-log-only follow-up commit.

Remaining risk:
- MEDIUM: external GitHub repository setting, not version-controlled source.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03 before applying the documented branch protection.
- Residual risk: this work-log-only record still needs to land through a PR
  because direct `master` updates are now blocked by the protection just
  applied.

## 2026-06-03T16:28:16Z - Strategy Backlog Additions

Active role: `ENGINEER`

Objective: record the operator request to track a higher-turnover daily/weekly
strategy and short-market strategy work as future backlog, without changing
runtime behavior.

What was found:
- SHOWN: `sma_200_trend` remains a long/flat daily strategy with slow turnover.
- SHOWN: `docs/strategies/es_daily_trend_v1.md` states the current v1 universe
  is one instrument and no expansion happens until paper/shadow gates pass.
- SHOWN: the repo already has strategy candidates such as `ema_cross`,
  `breakout_donchian`, and `mean_reversion_rsi`.

What changed:
- Added Priority 11 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for a
  higher-turnover daily/weekly strategy plan.
- Added Priority 12 to the same checkpoint for short-market strategy research.

Why this change:
- The operator wants the repo roadmap to include strategies better aligned with
  daily/weekly opportunity capture, while preserving the current
  `sma_200_trend` evidence campaign.
- Short-market work changes risk symmetry and should be tracked as a separate
  research stream, not as a parameter tweak to the current long/flat strategy.

Expected outcome:
- Future work can prioritize a paper-only higher-turnover strategy plan and a
  separate short-side research spec without interrupting the current paper gate.
- Short-side strategy work remains explicitly gated behind research, paper
  evidence, risk controls, and operator review.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: financial strategy direction and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: backlog items remain pending future implementation and must
  stay paper/research-scoped until separately reviewed.

## 2026-06-03T16:45:38Z - Pattern And Hybrid Strategy Backlog

Active role: `ENGINEER`

Objective: record the operator-requested pattern-recognition and hybrid
strategy recommendations as future backlog, without changing runtime behavior.

What was found:
- SHOWN: `services/strategies/strategy_registry.py` includes
  `pullback_recovery` in the supported runtime registry.
- SHOWN: `pullback_recovery` is not listed in the current aggregate leaderboard
  rows from `strategy_evidence.latest.json`.
- SHOWN: context-pattern modules exist for `order_book_imbalance`,
  `open_interest_shift`, and `funding_extreme`, but they are not equivalent to
  the standard OHLCV registry path.
- SHOWN: consensus support exists, but the current path scores stored signals
  and reliability; it is not yet a clean backtestable composite strategy
  wrapper.

What changed:
- Added Priority 13 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for pattern
  and hybrid strategy roadmap work.
- Captured `pullback_recovery` leaderboard/evidence evaluation as the first
  recommended pattern-strategy task.
- Captured later candlestick strategy work and context-pattern data plumbing as
  separate follow-up tracks.

Why this change:
- `pullback_recovery` is the lowest-infrastructure way to evaluate pattern-like
  price action using existing code.
- Hybrid and context-pattern strategies are higher-risk design work and should
  be specified before implementation or paper campaigns.

Expected outcome:
- The repo backlog now separates near-term pattern activation
  (`pullback_recovery`) from later candlestick recognition, context-pattern
  data plumbing, and composite/hybrid strategy design.
- Future strategy work can proceed through paper-only evidence gates without
  interrupting the current `sma_200_trend` campaign.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: financial strategy direction and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: roadmap items remain pending future implementation and must
  receive separate review before any trading behavior changes.

## 2026-06-03T16:57:09Z - Infrastructure Activation Audit Backlog

Active role: `ENGINEER`

Objective: record the operator request to investigate underused repo
infrastructure and determine how much of the repo is actually wired into the
current operating path.

What was found:
- SHOWN: the current active campaign remains focused on `sma_200_trend`,
  `BTC/USDT`, paper evidence collection, gate checks, and paper sim monitoring.
- SHOWN: the repo contains additional infrastructure in areas such as
  `services/ai_engine`, `services/signals`, `services/ai_copilot`,
  `services/alerts`, `services/learning`, dashboard pages, desktop surfaces,
  and operator scripts.
- SHOWN: some of those systems are partially wired through scripts, dashboard
  pages, tests, or selectors, so labeling all of them "unused" would be too
  broad without a structured inventory.

What changed:
- Added Priority 14 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` for a repo
  infrastructure activation audit.
- The backlog item requires each subsystem to be classified as `active`,
  `partially_wired`, `dormant`, `research_only`, `superseded`, or
  `unsafe_to_enable`.
- The backlog item requires a prioritized activation roadmap while keeping the
  current `sma_200_trend` campaign isolated.

Why this change:
- The operator wants the repo to be used more completely, but "turn everything
  on" is not a safe engineering strategy for trading infrastructure.
- A visible infrastructure audit gives the project a way to identify dormant
  value, remove confusion, and choose activation order based on evidence and
  risk.

Expected outcome:
- Future work can inventory and prioritize repo infrastructure without mixing
  unvalidated systems into the current evidence campaign.
- The project gains a durable map of which systems are active, partially wired,
  dormant, superseded, or unsafe to enable.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: repository architecture, operational workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-03.
- Remaining action: perform the subsystem-by-subsystem infrastructure inventory
  before enabling dormant or partially wired systems.

## 2026-06-03T17:00:00Z - Initial Infrastructure Activation Audit

Active role: `AUDITOR`

Objective: perform the first-pass infrastructure activation audit requested by
the operator and produce a visible artifact for independent review.

What was found:
- SHOWN: `docs/GOLDEN_PATH.md` identifies the canonical runtime as the managed
  `sma_200_trend` paper campaign and its monitor/gate surfaces.
- SHOWN: `docs/ARCHITECTURE.md` documents the signal/candidate layer as
  paper-only and evidence accumulation phase.
- SHOWN: `docs/ARCHITECTURE.md` marks transitional service families as frozen
  and says not to add new callers.
- SHOWN: repo directories exist for AI engine, signals/candidates, AI copilot,
  alerts, learning/feedback, desktop/service management, dashboard pages, and
  operator scripts.

What changed:
- Added `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md`.
- Updated the Priority 14 checkpoint status to point at the new audit artifact
  and require independent review before activation work.

Why this change:
- The operator asked to investigate underused repo infrastructure.
- A visible audit artifact is safer than enabling dormant systems opportunistically.
- The current evidence campaign must stay isolated while infrastructure is
  inventoried and prioritized.

Expected outcome:
- Reviewers have a concrete subsystem classification table and activation order.
- Future activation work can start from the safest high-leverage item instead
  of trying to use the entire repo at once.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration behavior
  changed.

Remaining risk:
- HIGH: repository architecture, operational workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: activation work remains pending and must be implemented as
  separate scoped changes with proof and review.

## 2026-06-04T13:25:45Z - Infrastructure Activation Audit Second Pass

Active role: `ENGINEER`

Objective: record the corrected second-pass infrastructure sweep and turn the
operator-script visibility gap into a separate backlog item.

What was found:
- SHOWN: `docs/OBJECTIVE.md` describes a larger product than the current
  `sma_200_trend` paper campaign, including learning/adaptive capabilities,
  multi-exchange support, safety controls, and a cross-platform installable app.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has null
  backtest expectation fields for `win_rate`, `avg_win`, and `avg_loss`.
- SHOWN: root `scripts/` contains 90 Python files in this checkout, not 88.
- SHOWN: several earlier hard claims needed correction: the old paper-runner
  importer counts were not reproduced from visible source imports,
  `signal_library` and `market_ranker` are wired through the candidate engine,
  `ws_feature_blacklist` is imported by the WebSocket ticker feed, and shadow
  gates are implemented directly rather than through missing threshold dicts.

What changed:
- Added a "Second-Pass Corrections - 2026-06-04" section to
  `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md`.
- Updated the audit recommendation to include Golden Path/script-index
  alignment as a visible operator-command-map task.
- Updated Priority 14 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to show that
  the initial audit was accepted and the second-pass corrections now need
  independent review.
- Added Priority 15 for Golden Path and script-index alignment.

Why this change:
- The pasted second sweep was directionally useful but contained over-broad
  dormancy labels and unreproduced counts.
- Recording the corrections prevents future activation work from relying on
  inaccurate evidence.
- The script visibility gap is actionable and safer to address before enabling
  broader repo infrastructure.

Expected outcome:
- Reviewers get a corrected infrastructure activation artifact.
- Future work can proceed from a more reliable subsystem map.
- Operators get a dedicated follow-up task to make safe daily commands,
  diagnostics, emergency tools, and research scripts visible in one command map.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration
  behavior changed.

Remaining risk:
- HIGH: repository architecture, operator workflow, and future trading
  automation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: activation work remains pending and must be implemented as
  separate scoped changes with proof and review.

## 2026-06-04T13:31:57Z - Golden Path And Script Index Alignment

Active role: `ENGINEER`

Objective: make the root script surface visible to operators without broadening
the Golden Path or changing runtime behavior.

What was found:
- SHOWN: `docs/GOLDEN_PATH.md` documented the narrow daily paper-campaign path
  but did not point operators to the full script command map.
- SHOWN: `scripts/SCRIPTS.md` listed only a small canonical operator subset.
- SHOWN: root `scripts/` contains 90 Python entrypoints.
- SHOWN: the existing script-path validator parses the `## Canonical Operator`
  section in `scripts/SCRIPTS.md` and verifies listed scripts exist.

What changed:
- Expanded `scripts/SCRIPTS.md` into an operator-facing script index.
- Preserved the `## Canonical Operator` table for validator compatibility and
  safe daily operation.
- Added classified sections for paper runtime internals, service control,
  safety/reconciliation, market data/exchange connectivity, research/model
  tools, validation/release helpers, and desktop/UI scripts.
- Updated `docs/GOLDEN_PATH.md` to point to `scripts/SCRIPTS.md` for the full
  command map while keeping the Golden Path narrow.
- Updated Priority 15 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  implementation-proof-ready pending independent review.

Why this change:
- Operators should not have to infer which scripts are safe daily commands and
  which are specialized, live-adjacent, or research-only tools.
- A visible command map reduces operator-memory burden without activating any
  dormant system or changing trading behavior.
- Keeping the Golden Path narrow prevents specialized scripts from being
  mistaken for the daily evidence-campaign path.

Expected outcome:
- `docs/GOLDEN_PATH.md` remains the current daily path.
- `scripts/SCRIPTS.md` becomes the authoritative root script command map.
- Future script additions/removals have a clear documentation surface to update.

Verification:
- `./.venv/bin/python scripts/validate_script_paths.py`
  - SHOWN: `OK: script paths validated`.
- `./.venv/bin/python -c '...'`
  - SHOWN: `{'script_count': 90, 'missing': []}`.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- MEDIUM: operator workflow and documentation accuracy.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: keep `scripts/SCRIPTS.md` aligned with root script
  entrypoint additions/removals.

## 2026-06-04T13:38:21Z - Daily Loss Halt Contract Alignment

Active role: `ENGINEER`

Objective: close the stale `daily_loss_halt_pct` documentation gap without
changing runtime risk-gate behavior.

What was found:
- SHOWN: `docs/strategies/es_daily_trend_v1.md` states that
  `daily_loss_halt_pct` is declarative in v1 and live enforcement comes from
  `services/risk/live_risk_gates.py` using `risk.live.max_daily_loss_usd`.
- SHOWN: `services/risk/live_risk_gates.py` loads `risk.live.*` through the
  canonical runtime trading config and returns `None` for missing or invalid
  live limits, preserving fail-closed behavior in callers.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still contained a stale
  comment pointing at the removed `services/risk/live_risk_gates_phase82.py`
  path.
- SHOWN: Priority 6 still said the daily-loss-halt discrepancy was pending even
  though the v1 declarative-vs-enforced contract had already been documented
  and accepted in earlier review.

What changed:
- Updated the `configs/strategies/es_daily_trend_v1.yaml` comment so it points
  at `services/risk/live_risk_gates.py` and the explicit
  `risk.live.max_daily_loss_usd` source of truth.
- Updated Priority 6 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to
  implementation-proof-ready pending independent review of the v1 safety
  contract.

Why this change:
- The smallest safe fix is to align the operator-facing config comment with the
  accepted runtime contract.
- Wiring a percentage-to-USD translation without an accepted equity source would
  be unsafe and broader than this defect.
- Leaving the stale Phase 82 path in the strategy config could mislead future
  safety reviews.

Expected outcome:
- The strategy spec and strategy config now describe the same v1 daily-loss
  halt contract.
- Operators and reviewers can see that the percentage target is declarative and
  the live gate is enforced from explicit runtime USD limits.
- Future equity-to-USD translation remains a separate high-risk implementation
  task.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_risk_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `51 passed in 0.43s`.
- `grep -RIn "live_risk_gates_phase82.py" configs/strategies docs/strategies services/risk --include='*.yaml' --include='*.yml' --include='*.md' --include='*.py'`
  - SHOWN: no matches in current strategy config/spec/risk paths.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- HIGH: risk controls and safety enforcement.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: keep the config percentage target and runtime USD limit
  manually consistent until an accepted equity-to-USD translation exists.

## 2026-06-04T13:43:52Z - SMA Round-Trip Fixture Backlog Reconciliation

Active role: `ENGINEER`

Objective: remove a stale backlog item after verifying the deterministic
`sma_200_trend` CI fixture already exists and is covered by tests.

What was found:
- SHOWN: Priority 10 still listed the `sma_200_trend` CI fixture as pending.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json` exists.
- SHOWN: `tests/test_backtest_parity_engine.py` asserts the fixture has 220
  bars, one buy, one sell, one closed trade, SMA long/flat reasons, and
  scorecard fields.
- SHOWN: commit `e4ad5d99c` added the fixture and regression test and had
  already been accepted in the work log.

What changed:
- Updated Priority 10 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` from pending
  to complete as of `e4ad5d99c`.
- Clarified that the fixture remains a synthetic mechanics test, not
  promotion-gate or profitability evidence.

Why this change:
- Leaving completed work in the pending backlog causes duplicate work and
  confusion about the next real blocker.
- The correct action was backlog reconciliation, not another fixture.

Expected outcome:
- The proactive task list no longer points operators or agents at already
  completed CI-hardening work.
- Future `sma_200_trend` semantic changes have a clear fixture/test pair to
  update.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_parity_engine.py tests/test_es_daily_trend.py`
  - SHOWN: `41 passed in 0.58s`.
- `wc -l sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`
  - SHOWN: `1762`.
- `git show --stat --oneline e4ad5d99c`
  - SHOWN: the commit added
    `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json`,
    `tests/test_backtest_parity_engine.py`, and the work log.

Remaining risk:
- LOW: documentation/backlog reconciliation only.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: same-thread low-risk closure after targeted
  verification.
- Remaining action: none for Priority 10.

## 2026-06-04T14:16:45Z - Branch Protection Admin Bypass Policy

Active role: `ENGINEER`

Objective: document the intended branch-protection bypass policy after PR #47
was merged by the human repo admin through the GitHub UI bypass path.

What was found:
- SHOWN: PR #47 merged into `master` at `2026-06-04T14:10:41Z` with merge
  commit `5317e58326c440d32561c57b09eb2499944a03f3`.
- SHOWN: all PR #47 required checks were passing before merge.
- SHOWN: the PR was authored by `Ddthomas415`, and the authenticated GitHub
  account available to this agent was also `Ddthomas415`, so a same-account
  self-review could not satisfy the branch-protection review requirement.
- SHOWN: the human operator reported using the visible GitHub web UI bypass
  path to merge after accepting the audit cycle.
- SHOWN: `origin/master` and `origin/review-stabilized` were reconciled to the
  same merge commit after PR #47 merged.

What changed:
- Updated `docs/GITHUB_BRANCH_PROTECTION.md` to document that administrator
  bypass is intentionally allowed for the solo-project workflow.
- Added policy language stating that AI-agent workflows must not use CLI
  admin-bypass flags.
- Added the audit-note requirements for any future admin-bypass merge.

Why this change:
- The protection rule is intentionally asymmetric: it blocks AI/non-admin
  self-merges while preserving a human owner/admin escape hatch for accepted
  solo-project work.
- Without documenting this, the disabled admin-enforcement setting could look
  accidental instead of deliberate.

Expected outcome:
- Future reviewers understand why administrator bypass is allowed and when it
  may be used.
- AI-agent workflows have an explicit rule not to use admin bypass from the CLI.
- Future bypass merges have a visible PR audit-note standard.

Verification:
- Documentation-only change.
- Verification not run because no code, test, runtime, or configuration
  behavior changed.

Remaining risk:
- MEDIUM: governance/runbook documentation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-04.
- Remaining action: none for the documented admin-bypass policy.

## 2026-06-05T19:28:41Z - EMA Cross Paper Challenger Plan

Active role: `ENGINEER`

Objective: turn the higher-turnover daily/weekly strategy backlog item into a
concrete paper-only challenger plan without disturbing the active
`sma_200_trend` campaign.

What was found:
- SHOWN: Priority 11 requested a dedicated paper-only strategy plan with
  candidate, timeframe, turnover expectations, risk cap, evidence gate,
  backtest baseline, and isolation rules.
- SHOWN: `ema_cross_default` already exists in `services/strategies/presets.py`
  with `ema_fast=12`, `ema_slow=26`, and post-cross filters.
- SHOWN: `docs/strategies/ema_cross_research_note_2026-03-26.md` did not
  justify shortening the EMA pair; deterministic windows favored default
  `12/26`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py --help` exposes the
  command surface needed for an isolated `ema_cross` proof.
- SHOWN: `CBP_STATE_DIR` is the repo-supported state isolation mechanism.

What changed:
- Added `docs/checkpoints/ema_cross_challenger_plan_2026_06_05.md`.
- Updated Priority 11 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` from pending
  strategy design to implementation-proof-ready.
- Defined the first proof as an isolated one-shot run for `ema_cross_default`
  using `public_ohlcv_5m` and a separate `CBP_STATE_DIR`.
- Defined paper-only evidence gates, isolation checks, risk caps, and decision
  rules.

Why this change:
- The active `sma_200_trend` campaign should keep running passively, but its
  slow turnover is structurally mismatched with the operator's faster evidence
  and daily/weekly opportunity objective.
- Planning the challenger first avoids contaminating canonical
  `es_daily_trend_v1` evidence or starting another background campaign before
  state isolation is proven.
- The existing `ema_cross_default` preset is the smallest defensible starting
  point because the repo already rejected an unsupported shorter EMA change.

Expected outcome:
- Operators have a concrete next step for testing a higher-turnover strategy
  without touching the current promotion gate.
- The first challenger run can prove command surface, public OHLCV provenance,
  artifact routing, and journal isolation before any persistent daily loop is
  launched.
- Future `ema_cross` evidence remains separate from `es_daily_trend_v1`
  promotion evidence.

Verification:
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: command succeeded and exposed `--strategies`,
    `--session-strategy-id`, `--symbol`, `--venue`, `--signal-source`,
    `--runtime-sec`, `--daily-loop`, and `--status`.

Remaining risk:
- HIGH: financial strategy selection and future promotion behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 before the isolated Stage 0 challenger proof.
- Remaining action: completed by the Stage 0 isolated proof entry below.

## 2026-06-05T19:50:25Z - EMA Cross Stage 0 Isolated Proof

Active role: `ENGINEER`

Objective: run the accepted Stage 0 one-shot proof for `ema_cross_default`
without disturbing canonical `es_daily_trend_v1` paper evidence.

What was found:
- SHOWN: before the challenger proof, `check_promotion_gates.py --json`
  reported canonical `es_daily_trend_v1` at `7/10` round trips, `14` fills,
  latest fill `2026-05-26T00:00:09.780106+00:00`, and
  `expectancy_per_closed_trade=$5.11`.
- SHOWN: the canonical evidence collector daily loop was alive and idle,
  waiting for the next UTC day.
- SHOWN: the first sandboxed challenger attempt could not fetch public OHLCV;
  `app.log` repeated `ohlcv_live_fetch_failed` for Coinbase and runner status
  reported `note=no_public_ohlcv`.
- SHOWN: rerunning the proof with network access enabled public OHLCV:
  runner status showed `bars=299`, populated `mid`, `signal_source=public_ohlcv_5m`,
  and `signal_reason=no_cross`.
- SHOWN: the isolated proof completed normally with `stop_reason=runtime_elapsed`.

What changed:
- Ran an isolated one-shot proof with
  `CBP_STATE_DIR=.cbp_state_challengers/ema_cross_default_stage0_20260605T1935Z`.
- Added `/.cbp_state_challengers/` to `.gitignore` so isolated proof state does
  not remain as untracked Git noise.
- No trading source code, strategy preset, gate threshold, or canonical
  `.cbp_state` artifact was modified.

Why this change:
- The accepted plan required Stage 0 proof before any persistent challenger
  daily loop.
- A fresh timestamped state directory avoided mixing the restricted failed
  attempt with the network-enabled proof artifacts.
- Ignoring `.cbp_state_challengers/` preserves the intended local-runtime
  boundary and prevents recurring untracked runtime artifacts.

Expected outcome:
- `ema_cross_default` has a verified isolated startup/status/shutdown proof on
  live Coinbase public OHLCV.
- Future challenger runs can use separate state directories without creating
  Git noise.
- Canonical `es_daily_trend_v1` promotion evidence remains isolated from
  challenger experiments.

Verification:
- Restricted attempt:
  - SHOWN: stopped cleanly after `117.89s`, `fills_total=0`,
    `closed_trades_total=0`, and only isolated session evidence.
- Network-enabled attempt:
  - SHOWN: collector completed at `2026-06-05T19:49:34.715316+00:00`.
  - SHOWN: result `runtime_sec=903.4889707565308`, `stop_reason=runtime_elapsed`,
    `signal_action=hold`, `signal_changed=false`, `enqueued_total=0`,
    `fills_total=0`, `closed_trades_total=0`, `net_realized_pnl_total=0.0`.
  - SHOWN: isolated session artifact has `market_data_source=public_ohlcv`,
    `ohlcv_sample_mode=false`, `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`,
    `ohlcv_symbol=BTC/USDT`, and `strategy_id=ema_cross_default`.
  - SHOWN: isolated state wrote
    `.cbp_state_challengers/ema_cross_default_stage0_20260605T1935Z/data/snapshots/ohlcv_coinbase_BTC_USDT_5m.json`.
- Canonical isolation:
  - SHOWN: after the challenger proof, `check_promotion_gates.py --json`
    still reported canonical `es_daily_trend_v1` at `7/10` round trips,
    `14` fills, and latest fill `2026-05-26T00:00:09.780106+00:00`.
- Git hygiene:
  - SHOWN: `git diff --check` passed with no output.
  - SHOWN: `git status --short --branch` listed only `.gitignore` and this
    work-log file as modified; `.cbp_state_challengers/` was no longer
    untracked after the ignore rule.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 before the isolated daily-loop challenger start.
- Remaining action: completed by the isolated daily-loop start entry below.

## 2026-06-05T19:55:45Z - EMA Cross Isolated Daily-Loop Start

Active role: `ENGINEER`

Objective: start the independently accepted `ema_cross_default` paper-only
daily-loop challenger campaign in isolated local state.

What was found:
- SHOWN: before start, canonical `es_daily_trend_v1` collector status was
  `idle`, `daily_loop=true`, `pid_alive=true`, and waiting for the next UTC
  day.
- SHOWN: before start, canonical promotion gates still reported `7/10` round
  trips, `14` fills, and latest fill `2026-05-26T00:00:09.780106+00:00`.
- SHOWN: before start, the dedicated challenger daily state
  `.cbp_state_challengers/ema_cross_default_daily` had no collector status and
  reported `status=not_started`.
- SHOWN: after start, challenger collector status reported `status=running`,
  `reason=collecting`, `pid_alive=true`, `strategies=["ema_cross"]`, and
  `session_strategy_id=ema_cross_default` via isolated evidence paths.
- SHOWN: runner status reported `bars=298`, populated `mid`, `strategy_id=ema_cross`,
  `strategy_preset=ema_cross_default`, `signal_source=public_ohlcv_5m`,
  `signal_action=hold`, and `signal_reason=no_cross`.
- SHOWN: after start, canonical promotion gates still reported `7/10` round
  trips and `14` fills.

What changed:
- Started the challenger command with:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily`.
- Used `--daily-loop`, `--strategies ema_cross`,
  `--session-strategy-id ema_cross_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`, `--runtime-sec 900`,
  `--strategy-drain-sec 2`, and `--poll-interval-sec 300`.
- No source code, strategy preset, gate threshold, or canonical `.cbp_state`
  artifact was edited.

Why this change:
- Stage 0 isolated proof was independently accepted, so the next scoped step
  was the isolated monitored daily-loop challenger.
- The dedicated `CBP_STATE_DIR` keeps challenger evidence separate from
  canonical `es_daily_trend_v1` promotion evidence.
- Daily-loop mode lets the system accumulate paper-only `ema_cross_default`
  observation without operator polling.

Expected outcome:
- The challenger runs one isolated public-OHLCV evidence window per UTC day.
- Fills, if any, accumulate only in
  `.cbp_state_challengers/ema_cross_default_daily`.
- The monitor emits watch reports for meaningful events such as campaign
  completion, fills, position close, or investigate conditions.

Verification:
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: canonical collector remained alive and idle for `es_daily_trend_v1`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical gate remained `7/10` round trips and `14` fills before
    and after challenger start.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: challenger status was `running`, `reason=collecting`,
    `pid_alive=true`, and evidence directory was under
    `.cbp_state_challengers/ema_cross_default_daily`.
- `cat .cbp_state_challengers/ema_cross_default_daily/runtime/flags/strategy_runner.status.json`
  - SHOWN: runner had live public OHLCV state with `bars=298`,
    `signal_source=public_ohlcv_5m`, `signal_action=hold`, and
    `signal_reason=no_cross`.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after the daily-loop start proof.
- Remaining action: monitor the isolated campaign until it records fills or
  reaches a no-trade investigation threshold.

## 2026-06-05T20:14:08Z - Paper Sim Monitor Daily-Loop Fill Visibility

Active role: `ENGINEER`

Objective: fix stale `paper_sim_monitor` summaries after a daily-loop
collector finishes a window and returns to idle.

What was found:
- SHOWN: the isolated `ema_cross_default` daily-loop challenger recorded one
  buy fill in JSONL evidence, `paper_trading.sqlite`, and
  `trade_journal.sqlite`.
- SHOWN: `paper_sim_monitor` watch output fired on the campaign transition but
  the summary still reported `fills=0` and `no fill yet`.
- SHOWN: daily-loop idle status stores the completed collection window under
  `last_result.results`, while `_latest_result()` only read top-level
  `results`.
- SHOWN: because no completed result was found, the monitor used the idle wait
  timestamp as the observation window and filtered out the real fill.

What changed:
- Updated `services/analytics/paper_sim_monitor.py` so `_latest_result()` falls
  back to `payload["last_result"]["results"]` when top-level `results` is
  absent.
- Added `test_collect_once_uses_daily_loop_last_result_when_idle` in
  `tests/test_paper_sim_monitor.py`.
- The regression test proves the monitor uses the completed daily-loop
  `started_ts` and `ended_ts` window, counts the fill, surfaces the latest
  journal fill, and includes `fills=1` plus the latest fill timestamp in the
  summary.

Why this change:
- The monitor is the operator-facing wakeup layer for paper campaigns; its
  summary must agree with canonical fill evidence after daily-loop state
  transitions.
- Reading `last_result.results` is the smallest compatible fix because it
  preserves existing top-level `results` behavior for active collection runs.

Expected outcome:
- When a daily-loop campaign is idle and waiting for the next UTC day, the
  monitor still summarizes the most recent completed evidence window.
- New fills and open positions from the completed window remain visible to the
  operator instead of disappearing until the next active run.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_run_paper_sim_monitor.py`
  - SHOWN: `18 passed in 0.25s`.
- `git diff --check`
  - SHOWN: clean.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python - <<'PY' ... svc.collect_once(...) ... PY`
  - SHOWN: isolated monitor output now reports `fills_observed=1`,
    `latest_journal_fill` populated, `paper_position.qty=0.001`, and summary
    text containing `fills=1` and the buy fill timestamp.
- `CBP_STATE_DIR=.../.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: challenger collector remains `idle`, `daily_loop=true`,
    `pid_alive=true`, and waiting for the next UTC day.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical `es_daily_trend_v1` gate remains unchanged at `7/10`
    round trips and `14` fills.

Remaining risk:
- HIGH: operator monitoring for financial strategy experimentation and
  background jobs.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after commit `ac46fb51c`.
- Remaining action: continue monitoring daily-loop paper campaigns for new
  fills, position closes, and investigate triggers.

## 2026-06-05T20:15:50Z - ES Daily Trend Backtest Baseline Audit

Active role: `ENGINEER`

Objective: determine whether the paper gate's missing `win_rate`, `avg_win`,
and `avg_loss` backtest expectations can be safely populated from visible repo
artifacts.

What was found:
- SHOWN: `scripts/check_promotion_gates.py --json` still reports
  `manual_review_required=true`.
- SHOWN: the only outstanding manual item is
  `win_rate_avg_win_loss_vs_backtest`.
- SHOWN: observed paper-history metrics are `7` closed trades, `14` fills,
  `28.57%` win rate, `$37.33` average win, `-$0.26` average loss, `$35.75`
  net realized PnL, and `$5.11` expectancy per closed trade.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d.json` produced one buy and zero sells
  under the SMA-200 parity run, so it has no closed-trade baseline metrics.
- SHOWN: `.cbp_state/data/snapshots/ohlcv_coinbase_BTC_USDT_1d.json` produced
  zero trades and is local runtime state rather than a committed baseline
  artifact.
- SHOWN: `sample_data/ohlcv/BTC_USDT_1d_sma200_roundtrip.json` produced one
  closed losing trade, but it is synthetic CI mechanics and should not be used
  as a profitability expectation source.

What changed:
- Added `docs/checkpoints/es_daily_trend_backtest_baseline_audit_2026_06_05.md`.
- Updated Priority 7 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to show that
  the strategy performance decision is blocked on an accepted historical
  closed-trade baseline.
- No strategy config, gate threshold, runtime behavior, or campaign state was
  changed.

Why this change:
- Filling `promotion.paper.backtest_expectations` from a synthetic fixture or
  non-closing sample would make the paper gate appear objective while using
  invalid baseline evidence.
- The safer outcome is to leave `manual_review_required=true` until an accepted
  reproducible closed-trade baseline exists.

Expected outcome:
- Future reviewers can see why the current config intentionally leaves
  `backtest_expectations` unset.
- The next correct action is to produce or acquire a reproducible historical
  OHLCV baseline that creates multiple natural `sma_200_trend` closed trades.

Verification:
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical gate remains `7/10` round trips and
    `manual_review_required=true`.
- Parity read-only checks against the three candidate OHLCV sources:
  - SHOWN: committed daily sample: `buy_count=1`, `sell_count=0`,
    `closed_trades=0`.
  - SHOWN: local Coinbase snapshot: `buy_count=0`, `sell_count=0`,
    `closed_trades=0`.
  - SHOWN: synthetic SMA-200 fixture: `buy_count=1`, `sell_count=1`,
    `closed_trades=1`.

Remaining risk:
- LOW for this docs-only audit record.
- HIGH remains for the eventual strategy-performance decision and any future
  config baseline change.
- Acceptance state: `ACCEPTED`.

## 2026-06-05T20:24:00Z - ES Daily Trend Baseline Candidate Runner

Active role: `ENGINEER`

Objective: add a repeatable, non-mutating runner for producing an
`es_daily_trend_v1` SMA-200 backtest baseline candidate from historical OHLCV.

What was found:
- SHOWN: no existing script produced a dedicated ES daily trend paper-gate
  baseline report.
- SHOWN: `services/backtest/parity_engine.py` already provides the accepted
  strategy-registry parity path.
- SHOWN: `services/backtest/signal_replay.py` exposes public OHLCV fetching
  with `since_ms`, but no visible runner paginated enough history for an
  SMA-200 baseline.

What changed:
- Added `scripts/research/run_es_daily_trend_backtest_baseline.py`.
- The runner can read committed/local OHLCV JSON with `--input` or fetch public
  OHLCV with pagination using `--venue`, `--symbol`, `--timeframe`, `--since`,
  `--page-limit`, and `--max-pages`.
- Added `--data-symbol` so exchange OHLCV fetch symbols can differ from the
  strategy/report symbol without hiding the basis difference.
- The runner calls `run_parity_backtest()` with explicit SMA, ATR, warmup,
  fee, slippage, and minimum closed-trade assumptions.
- The runner writes a JSON report containing source metadata, counts,
  scorecard, `candidate_backtest_metrics`, config-ready
  `backtest_expectations`, `baseline_ready`, and `blocking_reasons`.
- When `baseline_ready=false`, `backtest_expectations` remains null-valued and
  the measured values stay under `candidate_backtest_metrics`.
- Added `tests/test_es_daily_trend_backtest_baseline_runner.py`.
- Updated the baseline audit checkpoint and next-actions document to point at
  the runner.
- Added
  `docs/checkpoints/es_daily_trend_backtest_baseline_candidate_2026_06_04.md`
  to record the network-produced candidate without mutating strategy config.
- No strategy config, gate threshold, runtime behavior, or campaign state was
  changed.

Why this change:
- The project needs a reproducible way to produce baseline numbers before
  filling `promotion.paper.backtest_expectations`.
- The runner makes the evidence boundary explicit: it can generate a candidate
  report, but it does not mutate governed promotion config.

Expected outcome:
- Operators can generate a candidate historical closed-trade baseline report
  without hand-written Python snippets.
- If the report lacks enough closed trades or exit signals, it explains why it
  is not baseline-ready.
- Any later config update can cite the exact runner command and output report.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_backtest_parity_engine.py tests/test_check_promotion_gates.py`
  - SHOWN: `80 passed in 1.10s`.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --input sample_data/ohlcv/BTC_USDT_1d.json --min-closed-trades 3 --source-label sample_data:BTC_USDT_1d.json`
  - SHOWN: `baseline_ready=false`.
  - SHOWN: `backtest_expectations` remained null-valued.
  - SHOWN: `candidate_backtest_metrics` preserved the measured non-ready
    values.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --venue coinbase --symbol BTC/USDT --data-symbol BTC/USD --timeframe 1d --since 2018-01-01 --until 2026-06-04 --page-limit 300 --max-pages 20 --min-closed-trades 3 --output /private/tmp/es_daily_trend_v1_baseline_candidate_20260604.json`
  - SHOWN: command exited `0`.
  - SHOWN: `baseline_ready=true`, `rows=3077`, `closed_trades=31`,
    `win_rate=0.22580645161290325`, `avg_win=1881.5222600358036`, and
    `avg_loss=-198.91552614027037`.

Remaining risk:
- HIGH: financial backtest baseline tooling can influence later gate decisions.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by operator on
  2026-06-05 after commit `23e2499a1`.
- Remaining action: do not copy raw dollar `avg_win` and `avg_loss` into the
  promotion config until their sizing basis is compatible with paper-history
  metrics.

## 2026-06-06T02:20:59Z - Normalize Paper Backtest Comparison Metrics

Active role: `ENGINEER`

Objective: make the paper promotion comparison sizing-independent by comparing
closed-trade return percentages rather than raw dollar average win/loss values.

What was found:
- SHOWN: `scripts/check_promotion_gates.py` compared raw paper-history
  `avg_win` and `avg_loss` dollars to raw backtest dollars.
- SHOWN: the accepted candidate used all-in compounding from `$1,000`, while
  paper history used small fixed quantities; those dollar values were not
  comparable.
- SHOWN: `journal_fills` contains entry price, quantity, and allocated fees, so
  net return percentage can be computed per closed trade.
- SHOWN: after fees, paper net win rate is `0.14285714285714285`, not the prior
  gross-PnL-derived `0.2857142857142857`.

What changed:
- Added `net_pnl` and `return_pct` to FIFO closed-trade analytics.
- Added `avg_win_return_pct`, `avg_loss_return_pct`, and
  `expectancy_return_pct` to paper strategy feedback.
- Updated paper gate history output to expose the normalized fields.
- Added explicit `metric_basis: net_return_pct` support to the backtest
  expectation comparison while retaining legacy raw-dollar behavior when no
  metric basis is configured.
- Updated `configs/strategies/es_daily_trend_v1.yaml` to declare the normalized
  metric contract while leaving all baseline values null.
- Updated the baseline runner to emit normalized config candidates.
- Added
  `docs/checkpoints/es_daily_trend_normalized_baseline_candidate_2026_06_04.md`.
- Updated strategy, decision-framework, baseline-audit, next-actions, and
  regression-test contracts.

Why this change:
- Win/loss dollars change with trade quantity and account size, so they cannot
  support a coherent paper-versus-backtest comparison across different sizing
  models.
- Net return divided by entry notional is independent of quantity and includes
  both entry and exit fees.
- Keeping config values null prevents this implementation from silently
  approving the normalized candidate.

Expected outcome:
- The gate compares like-for-like trade performance once a normalized baseline
  is independently accepted and populated.
- Until then, `manual_review_required=true` remains visible.
- Paper win rate is based on net closed-trade outcomes after fees.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_journal_analytics.py tests/test_strategy_feedback.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_check_promotion_gates.py tests/test_es_daily_trend.py`
  - SHOWN: `80 passed in 1.05s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: gate remains `7/10` round trips and
    `manual_review_required=true`.
  - SHOWN: missing baseline fields are `win_rate`,
    `avg_win_return_pct`, and `avg_loss_return_pct`.
  - SHOWN: observed paper metrics include net win rate
    `0.14285714285714285`, average win return `93.63856474626441%`,
    average loss return `-0.34741823139579114%`, and expectancy return
    `13.079150765412809%`.
- `./.venv/bin/python scripts/research/run_es_daily_trend_backtest_baseline.py --venue coinbase --symbol BTC/USDT --data-symbol BTC/USD --timeframe 1d --since 2018-01-01 --until 2026-06-04 --page-limit 300 --max-pages 20 --min-closed-trades 3 --output /private/tmp/es_daily_trend_v1_normalized_baseline_candidate_20260604.json`
  - SHOWN: `baseline_ready=true`, `rows=3077`, `closed_trades=31`,
    `win_rate=0.22580645161290325`,
    `avg_win_return_pct=78.71095396512578`, and
    `avg_loss_return_pct=-4.0629558060999225`.
- `./.venv/bin/python -m pytest -q tests/test_journal_analytics.py tests/test_strategy_feedback.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_check_promotion_gates.py tests/test_es_daily_trend.py tests/test_backtest_evidence_cycle.py`
  - SHOWN: `94 passed in 1.11s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2107 passed, 33 skipped, 13 warnings in 377.72s`.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this changes financial analytics and promotion-gate comparison
  semantics.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `0e81e0aad`.
- Accepted decisions: `net_return_pct` comparison basis, disclosed Coinbase
  `BTC/USD` historical source for the `BTC/USDT` strategy comparison, and
  unchanged `25%` relative tolerance.
- Remaining action: populate the accepted normalized baseline values and verify
  the resulting gate output.

## 2026-06-06T02:31:19Z - Populate Accepted Normalized Baseline

Active role: `ENGINEER`

Objective: copy the independently accepted normalized backtest expectations
into `es_daily_trend_v1` config and verify the resulting paper gate decision.

What was found:
- SHOWN: the normalized candidate was independently accepted with Coinbase
  `BTC/USD` as the disclosed historical data basis, `net_return_pct` as the
  comparison basis, and `25%` relative tolerance.
- SHOWN: before population, the gate could only report missing baseline values.
- SHOWN: after population, the gate can compare all three accepted metrics.

What changed:
- Populated `promotion.paper.backtest_expectations` in
  `configs/strategies/es_daily_trend_v1.yaml` with:
  - source
    `public_ohlcv:coinbase:BTC/USDT:data=BTC/USD:1d:2018-01-01:2026-06-04`
  - `win_rate=0.22580645161290325`
  - `avg_win_return_pct=78.71095396512578`
  - `avg_loss_return_pct=-4.0629558060999225`
- Updated the strategy config contract test to pin the accepted values.
- Updated the gate integration test to require a `machine_blocking` comparison
  rather than a missing-baseline manual-review result.
- Updated the normalized candidate and next-actions checkpoints with the
  resulting metric-by-metric gate outcome.
- No gate threshold, tolerance, campaign process, or paper-history artifact was
  changed.

Why this change:
- The baseline values had completed independent review and were ready to become
  the machine-readable comparison source.
- Populating them converts an unresolved manual review into an explicit
  reproducible performance decision.

Expected outcome:
- The gate reports exactly which paper metrics match or diverge from the
  accepted backtest.
- A favorable but materially different average-loss magnitude remains visible
  as exit-behavior drift rather than being silently treated as equivalent.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_es_daily_trend.py tests/test_check_promotion_gates.py tests/test_es_daily_trend_backtest_baseline_runner.py`
  - SHOWN: `75 passed in 0.86s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2107 passed, 33 skipped, 13 warnings in 369.07s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: paper campaign remains `7/10` round trips.
  - SHOWN: comparison status is `machine_blocking`.
  - SHOWN: win rate fails: observed `0.14285714285714285`, accepted range
    `0.16935483870967744` to `0.28225806451612906`.
  - SHOWN: average win return passes: observed `93.63856474626441%`, accepted
    range `59.033215473844336%` to `98.38869245640723%`.
  - SHOWN: average loss return fails: observed `-0.34741823139579114%`,
    accepted range `-5.078694757624903%` to `-3.047216854574942%`.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this populates financial promotion-gate policy values.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `4651680f5`.
- Remaining action: investigate whether the average-loss drift reflects genuine
  paper strategy behavior or mixed historical evidence attribution.

## 2026-06-06T02:49:14Z - Qualify Paper Promotion History by Fill Provenance

Active role: `ENGINEER`

Objective: prevent unstamped or incompatible legacy paper fills from advancing
the `es_daily_trend_v1` paper promotion gate.

What was found:
- SHOWN: the journal contained `14` `sma_200_trend` fills and `7` raw closed
  trades.
- SHOWN: six raw round trips closed within minutes despite the configured daily
  strategy holding horizon.
- SHOWN: only the 2026-05-26 exit fill carried explicit `public_ohlcv`, `1d`,
  Coinbase, `BTC/USDT`, non-sample provenance.
- SHOWN: no raw round trip had matching provenance on both entry and exit.
- SHOWN: latest-window provenance health previously allowed those older
  unstamped journal fills to supply the separate round-trip and expectancy
  thresholds.

What changed:
- Added `services/control/paper_evidence_qualification.py`.
- JSONL fill records now identify provenance-qualified order IDs; only complete
  entry-to-exit cycles are selected.
- The trade journal supplies immutable price, quantity, and fee data only for
  those selected order IDs.
- The machine gate and paper monitor progress use qualified counts and metrics.
- Raw journal totals remain visible as `paper_history.all_history`,
  `all_history_fills`, and `all_history_closed_trades`.
- Updated evidence-authority, operator, decision-framework, strategy, and
  checkpoint documentation.

Why this change:
- Current collector health cannot retroactively prove the source and timeframe
  of historical trades.
- Keeping raw history while excluding it from promotion is the smallest
  fail-closed correction; no evidence or database rows are deleted.
- A shared qualification service prevents the CLI gate and monitor summary from
  reporting different progress.

Expected outcome:
- The canonical campaign reports `0/10` qualified round trips and `7` raw
  all-history round trips.
- Future trades count only when both legs explicitly match the configured
  daily public-OHLCV contract.
- Performance comparison remains blocked until qualified closed trades exist.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  - SHOWN: `38 passed in 0.64s`.
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_feedback.py`
  - SHOWN: `55 passed in 0.84s`.
- `./.venv/bin/python -m py_compile services/control/paper_evidence_qualification.py scripts/check_promotion_gates.py services/control/paper_promotion_progress.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: final post-edge-case run completed with `2110 passed, 33 skipped,
    13 warnings in 369.22s`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: `0/10` qualified round trips, `10` remaining.
  - SHOWN: `14` raw all-history fills and `7` raw all-history round trips
    remain visible.
  - SHOWN: one provenance-qualified exit fill remains incomplete because its
    entry leg is unstamped.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline complete, no non-canonical duplicate top-level
    directories, and no suspicious top-level files.

Remaining risk:
- HIGH: this changes financial promotion-gate eligibility and resets displayed
  qualified progress from `7/10` to `0/10`.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `7ab11da59`.
- Accepted decisions: require matching provenance on both trade legs, reset
  qualified progress to zero, and preserve the seven raw round trips as
  diagnostic all-history data.

## 2026-06-06T03:47:43Z - Refresh Collector and Correct Window PnL Attribution

Active role: `ENGINEER`

Objective: reload the accepted qualified-progress semantics in the managed
collector and prevent lifetime realized PnL from being labeled as current
campaign-window PnL.

What was found:
- SHOWN: the daily collector was healthy but had started before commit
  `7ab11da59`; its persisted monitor snapshot still displayed raw `7/10`
  promotion progress.
- SHOWN: the collector was idle after the completed 2026-06-06 UTC campaign.
- SHOWN: a read-only refreshed monitor snapshot correctly loaded qualified
  `0/10` progress but reported the lifetime position realized PnL of `$36.52`
  as `current_window_realized_pnl` despite `fills_observed=0`.
- SHOWN: `_result_realized_pnl()` fell back to lifetime position/equity totals
  when no campaign delta existed.

What changed:
- Requested a graceful managed stop and waited for PID `7178` to clear.
- Restarted the daily loop with the recorded parameters:
  `sma_200_trend`, `BTC/USDT`, Coinbase, `public_ohlcv_1d`, 20-second strategy
  runtime, and 300-second polling.
- Verified replacement PID `23879` is alive and idle without rerunning today's
  campaign.
- Changed current-window PnL reporting to use only
  `net_realized_pnl_delta`.
- When no explicit delta exists, the monitor now returns
  `current_window_realized_pnl=null`,
  `current_window_realized_pnl_known=false`, and source `unavailable`.
- Lifetime position and equity realized PnL remain separately visible.
- Updated the Golden Path and added an idle-monitor regression test.

Why this change:
- A long-running process must reload accepted code before operator output can
  reflect the new evidence policy.
- Lifetime totals are not valid substitutes for a campaign-window delta.
- Returning an explicit unknown is safer than displaying a precise but
  misattributed financial value.

Expected outcome:
- The next daily campaign and monitor process use qualified `0/10` promotion
  progress.
- Idle snapshots no longer imply that historical PnL was earned in the current
  window.
- Operators still retain lifetime PnL context in dedicated total fields.

Verification:
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879`, `status=idle`, `pid_alive=true`,
    `signal_source=public_ohlcv_1d`, and no duplicate 2026-06-06 campaign.
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --once --no-desktop-notify`
  - SHOWN before the reporting patch: qualified `0/10` progress loaded; stale
    lifetime PnL attribution reproduced.
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_home_digest.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `51 passed in 1.81s`.
- `./.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_home_digest.py tests/test_dashboard_page_runtime.py tests/test_paper_strategy_evidence_service.py tests/test_run_paper_strategy_evidence_collector.py`
  - SHOWN: `82 passed in 2.03s`.
- `./.venv/bin/python -c "...collect_once..."`
  - SHOWN: idle `current_window_realized_pnl=null`,
    `current_window_realized_pnl_known=false`, source `unavailable`.
  - SHOWN: position lifetime total remains `$36.52320704250005`, equity
    lifetime total remains `-$1014.3944812741194`, and qualified promotion
    progress remains `0/10`.
- `git diff --check`
  - SHOWN: clean.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2111 passed, 33 skipped, 13 warnings in 375.81s`.
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --once --no-desktop-notify`
  - SHOWN: persisted snapshot refreshed with idle window PnL
    `null/unavailable`, qualified `0/10` progress, and collector PID `23879`
    alive.

Remaining risk:
- HIGH: this changes financial operator-reporting semantics and restarts a
  managed background job.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `0003bd71c`.
- Accepted decision: use `null/unavailable` for current-window realized PnL
  when no explicit campaign delta exists while preserving lifetime totals.

## 2026-06-06T09:56:25Z - Unify Paper Evidence Collector Entrypoints

Active role: `ENGINEER`

Objective: ensure every supported operator entrypoint starts, stops, or
inspects the same managed paper evidence collector implementation.

What was found:
- SHOWN: the Makefile routed its three paper evidence targets through
  `scripts/data/run_paper_strategy_evidence_collector.py`.
- SHOWN: that nested script contained a separate one-shot collector CLI and
  did not expose the canonical daily-loop, polling, maximum-loop, or session
  strategy options.
- SHOWN: the root `scripts/run_paper_strategy_evidence_collector.py` is the
  entrypoint used by the dashboard, operator documentation, tests, and active
  daily collector.
- SHOWN: running the Makefile path could therefore start a campaign with
  behavior different from the documented and monitored campaign.

What changed:
- Replaced the nested collector implementation with a compatibility delegate
  to the root collector's `main()` function.
- Routed the Makefile collect, status, and stop targets directly through the
  root canonical collector.
- Documented the root collector as authoritative in `scripts/SCRIPTS.md`.
- Added regression tests that prevent a second parser from returning in the
  compatibility path, lock the Makefile to the canonical path, and verify the
  compatibility path exposes canonical daily-loop and session options.

Why this change:
- Keeping one collector implementation prevents background-job and evidence
  policy drift between operator entrypoints.
- A compatibility delegate preserves direct callers of the historical nested
  path without maintaining duplicate behavior.
- Routing Make directly to the canonical path makes the supported operator
  workflow explicit.

Expected outcome:
- Make, dashboard, documentation, direct root invocation, and the legacy
  nested path all execute the same collector behavior.
- Future collector options and evidence semantics have one implementation
  point.
- Existing callers of the nested path remain functional.

Verification:
- Initial targeted command included nonexistent
  `tests/test_validate_script_paths.py`.
  - SHOWN: pytest stopped before collection with `no tests ran`; this was a
    command-path mistake, not a code failure.
- `./.venv/bin/python -m pytest -q tests/test_bootstrap_helper_adoption.py tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_operator_service.py`
  - SHOWN: `35 passed in 0.78s`.
- `./.venv/bin/python scripts/validate_script_paths.py`
  - SHOWN: `OK: script paths validated`.
- `make -n collect-paper-strategy-evidence status-paper-strategy-evidence stop-paper-strategy-evidence`
  - SHOWN: all three commands use
    `scripts/run_paper_strategy_evidence_collector.py`.
- `scripts/data/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: exits successfully and includes `--daily-loop` and
    `--session-strategy-id`.
- `git diff --check`
  - SHOWN: clean before the work-log entry.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2113 passed, 33 skipped, 13 warnings in 387.96s`.

Remaining risk:
- HIGH: this changes supported entrypoints for a managed background financial
  evidence job.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 after commit `b9c126656`.
- Accepted decision: retain the nested script only as a compatibility delegate
  and route supported Makefile operations through the canonical root
  collector.

## 2026-06-06T10:14:57Z - Open Current Master Integration Review

Active role: `AUDITOR`

Objective: replace the stale conflict-heavy master integration plan with a
current, reviewable path from `review-stabilized` to `master`.

What was found:
- SHOWN: `origin/master...origin/review-stabilized` is `0 / 19`.
- SHOWN: `origin/master` is an ancestor of `origin/review-stabilized`.
- SHOWN: the 2026-05-25 plan describing 25 merge conflicts no longer applies
  to the current branch tips.
- SHOWN: no open pull request already targeted `review-stabilized` into
  `master`.
- SHOWN: the aggregate change contains 30 files, 2,770 insertions, and 176
  deletions across 19 accepted commits.

What changed:
- Opened draft PR #49 from `review-stabilized` to `master`.
- Updated `REMAINING_TASKS.md` and the next-actions checkpoint with the current
  ancestry, PR, and review requirements.
- Retired the stale 25-conflict instructions from the active task index.
- Kept the exact `0 / 19` divergence as timestamped audit evidence here while
  using non-self-staling ancestry language in active task documents.

Why this change:
- Master integration is the highest-leverage structural task because accepted
  work is not canonical until it reaches `master`.
- Direct ancestry means a new conflict-resolution branch would add risk and
  complexity without solving a current problem.
- A draft PR preserves required independent review for the aggregate
  financial and background-job changes.

Expected outcome:
- Reviewers evaluate one current, conflict-free integration diff.
- The canonical branch can advance without reviving obsolete integration
  branches or manual conflict resolutions.
- No merge occurs until PR checks and aggregate independent review pass.

Verification:
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 19`.
- `git merge-base --is-ancestor origin/master origin/review-stabilized`
  - SHOWN: exit `0`.
- `git diff --check origin/master..origin/review-stabilized`
  - SHOWN: clean.
- `gh pr list --state open --head review-stabilized --base master`
  - SHOWN: no existing PR before creation.
- GitHub connector PR creation
  - SHOWN: failed with `403 Resource not accessible by integration`; no PR was
    created by that attempt.
- `gh pr create --draft --base master --head review-stabilized ...`
  - SHOWN: created
    `https://github.com/Ddthomas415/CryptKeep/pull/49`.
- Latest implementation-head full suite:
  - SHOWN: `2113 passed, 33 skipped, 13 warnings in 387.96s`.

Remaining risk:
- HIGH: PR #49 aggregates financial promotion-gate behavior, strategy
  baselines, monitoring semantics, and managed collector entrypoints.
- SHOWN: all eight GitHub checks passed on reviewed head `7e9d9cf34`,
  including CI sanity, CI validate, macOS and Windows builds, governance
  smoke, script-path integrity, and GitGuardian.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the operator on
  2026-06-06 for PR #49 at head `7e9d9cf34`.
- Accepted decision: advance the conflict-free aggregate integration to
  `master` under the documented operator/admin merge policy.

## 2026-06-06T10:38:36Z - Complete Master Integration

Active role: `ENGINEER`

Objective: merge accepted PR #49 and leave `master` and `review-stabilized`
aligned.

What was found:
- SHOWN: PR #49 remained conflict-free and mergeable after the acceptance
  record commit.
- SHOWN: all eight GitHub checks passed again on head `b7130ab52`.
- SHOWN: GitHub reported the ready PR as blocked only by the solo-admin review
  requirement documented in `docs/GITHUB_BRANCH_PROTECTION.md`.

What changed:
- Marked PR #49 ready for review.
- Merged PR #49 through the documented operator/admin bypass path.
- Fast-forwarded `review-stabilized` to the resulting master merge commit.
- Updated the active backlog and checkpoint to mark master integration
  complete.

Why this change:
- The aggregate had explicit independent operator acceptance and complete CI
  proof.
- Keeping both remote branches on the same merge commit avoids immediately
  recreating the branch-divergence problem after integration.
- A follow-up documentation-only PR preserves branch protection while making
  the active task state accurate.

Expected outcome:
- Accepted paper evidence, baseline, monitoring, and collector work is
  canonical on `master`.
- `master` and `review-stabilized` start the next cycle from the same commit.
- The stale conflict-resolution plan no longer appears as pending work.

Verification:
- `gh pr checks 49 --watch`
  - SHOWN: all eight checks passed on head `b7130ab52`.
- `gh pr view 49`
  - SHOWN: state `MERGED`, merge commit `5ab9732a2`, merged at
    `2026-06-06T10:37:05Z`.
- `git fetch origin master review-stabilized`
  - SHOWN: `origin/master` advanced to `5ab9732a2`.
- `git merge --ff-only origin/master`
  - SHOWN: `review-stabilized` advanced from `b7130ab52` to `5ab9732a2`
    without conflicts.
- `git push origin review-stabilized`
  - SHOWN: remote integration branch advanced to `5ab9732a2`.
- `git rev-list --left-right --count origin/master...origin/review-stabilized`
  - SHOWN: `0 0`.
- Paper evidence collector status:
  - SHOWN: PID `23879` remains alive, idle, and waiting for the next UTC day.

Remaining risk:
- LOW: this closure update is documentation-only.
- Acceptance state: `ACCEPTED`.

## 2026-06-06T10:58:00Z - Scope Shadow Gates to Active Shadow Evidence

Active role: `ENGINEER`

Objective: prevent a shadow readiness query from treating historical paper
records as shadow-stage proof.

What was found:
- SHOWN: canonical 2026-06-06 signal records contain `spread_bps`, and session
  records contain `ops_checks_passed=true`.
- SHOWN: before this change, `check_promotion_gates.py --stage shadow --json`
  evaluated 33,318 historical signals and 336 sessions even though the
  persisted strategy stage was still `paper`.
- SHOWN: the override selected shadow gate logic but did not establish a
  shadow evidence window, so paper history could produce false failures and
  contradictory operator details.
- SHOWN: schema validation, provenance, slippage, and retirement checks also
  used all-time paper evidence outside the visible shadow gate list.

What changed:
- Added an active-stage evidence selector that requires both an explicit
  `_stage=shadow` stamp and a timestamp on or after the persisted shadow
  `since_ts`.
- Made shadow readiness report `not_started` with five unknown gates when the
  persisted `current_stage` is not `shadow`.
- Scoped shadow schema validation, provenance, slippage, and retirement checks
  to the same active shadow evidence window.
- Kept `provenance_all_time` as a diagnostic field without allowing it to
  influence shadow readiness.
- Added exact count details for shadow trading days, spread/depth coverage,
  ops checks, fill/slippage evidence, and recovery proof.
- Added regression tests for a paper-stage override and for mixed paper/shadow
  evidence after an actual stage promotion.
- Documented the `--stage shadow` query semantics in the golden path and
  strategy specification.

Why this change:
- A command-line report override must not silently reclassify evidence from a
  different deployment stage.
- Shadow promotion is a time-bounded experiment; using pre-promotion paper
  records makes its operational and market-quality gates untrustworthy.
- Applying one evidence scope to gates and their auxiliary checks avoids a
  report where the visible gates and top-level readiness decision use
  different data.

Expected outcome:
- Before shadow promotion, operators see an honest `UNKNOWN/not_started`
  result rather than paper-derived shadow failures.
- After promotion, only contemporaneous shadow records can advance or block
  the shadow checklist.
- The recovery gate cannot pass until a deliberate shadow-stage restart and
  state-validation drill is recorded.

Verification:
- Initial worktree-local command:
  `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: did not run because the isolated worktree has no `.venv`.
- Shared verified environment:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: `41 passed in 0.79s`.
- Related regression slice:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_deployment_stage.py tests/test_es_daily_trend.py tests/test_paper_promotion_progress.py`
  - SHOWN: `95 passed in 1.32s`.
- Full suite:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2110 passed, 33 skipped, 13 warnings in 206.39s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline present, no non-canonical duplicate trees, and
    no suspicious top-level files.
- Canonical-state readiness query through the isolated source:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --stage shadow --json`
  - SHOWN: `current_stage=paper`,
    `evidence_scope.status=not_started`, all scoped counts zero, and
    `0 pass / 0 fail / 5 unknown`.
- Canonical paper regression query:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: paper logic still reads the existing all-paper evidence scope and
    remains not ready.
- `git diff --check`
  - SHOWN: clean before and after documentation updates.
- Main paper evidence collector status:
  `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879` alive, status `idle`, reason
    `waiting_for_next_day`, with the 2026-06-06 evidence cycle complete.
- GitHub PR #51 checks on implementation commit `7a9c94e78`:
  - SHOWN: macOS build, Windows build, CI sanity, CI validate, governance
    smoke, script-path integrity, and GitGuardian passed.

Remaining risk:
- HIGH: this changes financial promotion-gate evidence selection and
  readiness reporting.
- UNVERIFIED: no real shadow campaign exists yet, so production evidence
  accumulation after an actual paper-to-shadow transition remains unproven.
- UNVERIFIED: the deliberate shadow restart/recovery drill has not been run.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-06 after implementation commit `7a9c94e78` and all PR
  #51 checks passed.

## 2026-06-07T23:09:31Z - Explain Excluded Paper Promotion History

Active role: `ENGINEER`

Objective: make the shared paper promotion progress output explain why the
existing all-history paper round trips are visible diagnostically but do not
advance the paper promotion threshold.

What was found:
- SHOWN: canonical promotion progress on `.cbp_state` reported 33/30 days and
  0/10 qualified round trips while all-history paper history still showed 7
  closed round trips.
- SHOWN: JSONL fill evidence contains 10 fill rows; 9 lack or mismatch the
  required market-data provenance fields, and 1 provenance-qualified fill is
  not part of a complete qualified entry/exit round trip.
- SHOWN: the evidence model explicitly says fresh latest-window provenance
  does not retroactively qualify older unstamped fills.
- SHOWN: current paper-engine tests already prove new order/fill records carry
  provenance forward, so future qualified round trips can count without
  backfilling legacy evidence.
- SHOWN: backfilling the legacy fills would infer unsupported facts and rewrite
  audit history.

What changed:
- Added a structured `qualification_explanation` object to
  `paper_promotion_progress`.
- Appended the qualification explanation to the operator-facing promotion
  summary when all-history round trips are excluded, evidence fills fail the
  provenance contract, qualified fills do not form a complete round trip, or
  qualified evidence order IDs are missing from the journal.
- Added regression coverage for both excluded all-history paper fills and a
  fully qualified paper round trip.
- Documented the reporting-only explanation in `docs/EVIDENCE_MODEL.md`.

Why this change:
- The qualification rule was correct, but the shared monitor/dashboard summary
  did not answer the operator's direct question: why visible historical trades
  were not moving the 10-round-trip gate.
- Reporting the exclusion reason is safer than retroactive qualification
  because it preserves the accepted provenance boundary while making the gate
  state understandable.
- Keeping this in shared progress output makes the monitor, dashboard, and any
  future operator surfaces consume the same explanation.

Expected outcome:
- Operators see the exact blocker without manually inspecting JSONL/journal
  internals.
- The promotion gate remains strict: the current canonical state still reports
  0/10 qualified round trips, not 7/10.
- Future provenance-complete entry/exit cycles will count normally and will not
  be mislabeled as diagnostic-only history.

Verification:
- Targeted regression slice:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_promotion_progress.py tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py`
  - SHOWN: `20 passed in 0.42s`.
- Canonical-state shared progress query through the isolated source:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -c 'import json; from services.control.paper_promotion_progress import load_paper_promotion_progress; p=load_paper_promotion_progress(); print(json.dumps({"days_recorded":p["days_recorded"],"round_trips_recorded":p["round_trips_recorded"],"all_history_round_trips":p["all_history_round_trips"],"qualification_explanation":p["qualification_explanation"],"summary_text":p["summary_text"]}, indent=2))'`
  - SHOWN: `days_recorded=33`, `round_trips_recorded=0`,
    `all_history_round_trips=7`, `evidence_fills=10`,
    `unqualified_evidence_fills=9`,
    `incomplete_qualified_evidence_fills=1`, and summary text explaining that
    7 all-history round trips are diagnostic only.
- Canonical paper gate regression:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: still `ready=false`, `machine_ready=false`, and the 10-round-trip
    gate reports `0/10, 10 remaining`.
- Full suite:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2111 passed, 33 skipped, 13 warnings in 204.44s`.
- Repo doctor:
  `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python tools/repo_doctor.py`
  - SHOWN: supported baseline present, no non-canonical duplicate trees, and
    no suspicious top-level files.
- Main paper evidence collector status:
  `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: PID `23879` alive, status `idle`, reason
    `waiting_for_next_day`, with the 2026-06-07 evidence cycle complete.
- `git diff --check`
  - SHOWN: clean before the work-log update.
- Main workspace branch check:
  - SHOWN: `/Users/baitus/Downloads/crypto-bot-pro` remains
    `review-stabilized...origin/review-stabilized` with `0 0` divergence from
    `origin/master`.

Remaining risk:
- HIGH: this changes financial promotion reporting consumed by operator
  monitor/dashboard surfaces.
- UNVERIFIED: dashboard rendering was not browser-checked in this branch.
- UNVERIFIED: no future complete qualified round trip has occurred yet in the
  live paper campaign.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-07 after implementation commit `99d3bb749`.

## 2026-06-07T23:47:55Z - Breakout Donchian Stage 0 Isolated Proof

Active role: `ENGINEER`

Objective: run a one-shot isolated wiring proof for the `breakout_donchian`
challenger without changing canonical `sma_200_trend` evidence or the active
isolated `ema_cross` campaign.

What was found:
- SHOWN: before the proof, canonical `sma_200_trend` remained at 14 fills, 7
  all-history closed trades, and latest fill
  `2026-05-26T00:00:09.780106+00:00`.
- SHOWN: the isolated `ema_cross_default` daily loop remained alive and idle
  with 2 fills, 1 closed trade, and +0.20272406454938546 net realized PnL.
- SHOWN: `breakout_donchian` maps to preset `breakout_default`.
- SHOWN: the runner received live Coinbase public OHLCV on the 5-minute
  timeframe, selected `breakout_donchian`, and reported a visible
  `hold/inside_channel` reason.
- SHOWN: the observed close remained below the prior Donchian upper boundary,
  and the volume ratio remained below the configured confirmation floor, so no
  order was expected.

What changed:
- Ran a one-shot campaign under the isolated state directory
  `.cbp_state_challengers/breakout_default_stage0_20260607T233204Z`.
- Used `--strategies breakout_donchian`,
  `--session-strategy-id breakout_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`,
  `--runtime-sec 900`, and `--strategy-drain-sec 2`.
- No strategy source, preset, threshold, canonical `.cbp_state` artifact, or
  `ema_cross` challenger artifact was modified.

Why this change:
- `breakout_donchian` is the strongest current synthetic leaderboard
  candidate but had no real paper runtime proof.
- A one-shot isolated proof is the smallest safe step before considering a
  persistent challenger daily loop.
- Separate state preserves strategy evidence ownership and prevents challenger
  results from advancing the `es_daily_trend_v1` promotion gate.

Expected outcome:
- The breakout challenger has verified startup, public-data acquisition,
  strategy selection, monitoring, isolated evidence routing, and clean
  shutdown behavior.
- A no-trade result remains valid Stage 0 evidence because the signal reason is
  visible and consistent with the strategy rules.
- Persistent daily-loop operation remains blocked pending independent review
  of this Stage 0 proof.

Verification:
- One-shot command:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_stage0_20260607T233204Z ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --strategies breakout_donchian --session-strategy-id breakout_default --symbol BTC/USDT --venue coinbase --signal-source public_ohlcv_5m --runtime-sec 900 --strategy-drain-sec 2 --no-desktop-notify`
  - SHOWN: completed normally after `903.963011264801s` with
    `stop_reason=runtime_elapsed`, `runner_status=stopped`,
    `signal_action=hold`, `enqueued_total=0`, `fills_total=0`, and
    `closed_trades_total=0`.
- Runner status during the proof:
  - SHOWN: 279-280 live bars, populated market price, strategy
    `breakout_donchian`, preset `breakout_default`,
    `signal_source=public_ohlcv_5m`, and `signal_reason=inside_channel`.
- Final isolated session evidence:
  - SHOWN: start and end records both carry
    `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`,
    `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`, and
    `ohlcv_symbol=BTC/USDT`.
  - SHOWN: end record reports `campaign_status=completed`,
    `reconciliation_result=pass`, `ops_checks_passed=true`,
    `critical_error=false`, and `kill_switch_tested=true`.
- Isolation checks:
  - SHOWN: canonical `sma_200_trend` remained at 14 fills, 7 closed trades,
    and +35.75316899496567 net realized PnL.
  - SHOWN: isolated `ema_cross` remained at 2 fills, 1 closed trade, and
    +0.20272406454938546 net realized PnL.
- Final collector status:
  - SHOWN: `status=completed`, `pid_alive=false`, and no PID file remains for
    the one-shot proof.
- Git status before this work-log update:
  - SHOWN: clean `review-stabilized...origin/review-stabilized`; isolated
    challenger artifacts remain ignored.

Remaining risk:
- HIGH: financial strategy experimentation and potential future background-job
  operation.
- UNVERIFIED: no actionable breakout signal, order, fill, or round trip
  occurred during Stage 0.
- UNVERIFIED: persistent daily-loop lifecycle for `breakout_donchian` has not
  been started or proven.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-07 after commit `5b4ee9b3c`.

## 2026-06-08T00:09:59Z - Breakout Donchian Isolated Daily-Loop Start

Active role: `ENGINEER`

Objective: start the independently accepted `breakout_donchian` challenger as
a separate paper-only daily-loop campaign in isolated local state.

What was found:
- SHOWN: the dedicated daily challenger state
  `.cbp_state_challengers/breakout_default_daily` had no prior collector status
  before start.
- SHOWN: canonical `sma_200_trend` remained alive, idle, and unchanged at 14
  fills and 7 all-history closed trades.
- SHOWN: isolated `ema_cross_default` had already entered its 2026-06-08
  collection window and remained in its own state directory.
- SHOWN: the first detached `nohup` launch exited before writing collector
  status and wrote no evidence records; it left only an empty app log under the
  isolated breakout state.

What changed:
- Started the breakout challenger daily loop with:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily`.
- Used `--daily-loop`, `--strategies breakout_donchian`,
  `--session-strategy-id breakout_default`, `--symbol BTC/USDT`,
  `--venue coinbase`, `--signal-source public_ohlcv_5m`,
  `--runtime-sec 900`, `--strategy-drain-sec 2`, and
  `--poll-interval-sec 300`.
- Launched the successful collector in a managed long-running process session
  after the detached `nohup` attempt failed to initialize.
- No source code, strategy preset, gate threshold, canonical `.cbp_state`
  artifact, or `ema_cross` challenger artifact was modified.

Why this change:
- Stage 0 proved breakout startup, public OHLCV routing, monitoring, isolated
  evidence routing, and clean shutdown.
- A separate daily loop lets the strongest synthetic leaderboard strategy
  accumulate real paper observations without polluting `es_daily_trend_v1`
  evidence or the existing `ema_cross_default` challenger.
- Keeping the state path separate makes later comparison possible without
  coupling promotion gates.

Expected outcome:
- The breakout challenger runs one isolated public-OHLCV evidence window per
  UTC day.
- Any breakout orders, fills, watch reports, and decision artifacts are written
  only under `.cbp_state_challengers/breakout_default_daily`.
- Canonical `sma_200_trend` and isolated `ema_cross_default` continue
  independently.

Verification:
- Successful breakout status:
  `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `status=running`, `reason=collecting`, `pid=47262`,
    `pid_alive=true`, `strategies=["breakout_donchian"]`, and evidence path
    under `.cbp_state_challengers/breakout_default_daily`.
- Breakout runner status:
  - SHOWN: live 5-minute public OHLCV, `strategy_id=breakout_donchian`,
    `strategy_preset=breakout_default`, `signal_action=hold`,
    `signal_reason=inside_channel`, `pos_qty=0.0`, and `enqueued_total=0`.
- Canonical isolation:
  - SHOWN: `sma_200_trend` collector remains alive and idle with 14 fills, 7
    all-history closed trades, and unchanged promotion-qualified count.
- EMA challenger isolation:
  - SHOWN: `ema_cross_default` collector remains alive and running in its own
    2026-06-08 collection window.
- Git status before this work-log update:
  - SHOWN: clean `review-stabilized...origin/review-stabilized`; isolated
    challenger artifacts remain ignored.

Remaining risk:
- HIGH: financial strategy experimentation and background-job operation.
- RESOLVED: the first persistent breakout daily-loop window completed; see the
  2026-06-08T04:02:48Z entry below.
- UNVERIFIED: no actionable breakout signal, order, fill, or round trip has
  occurred in the daily loop yet.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-08 after commit `bcba08a6b`.

## 2026-06-08T04:02:48Z - Breakout Donchian First Daily-Loop Window Completion

Active role: `AUDITOR`

Objective: verify the first persistent `breakout_donchian` daily-loop window
completed cleanly after the accepted start.

What was found:
- SHOWN: `breakout_default` daily loop completed its 2026-06-08 window and
  returned to idle while keeping PID `47262` alive for the next UTC day.
- SHOWN: the completed result reported `runtime_sec=904.6953809261322`,
  `stop_reason=runtime_elapsed`, `runner_status=stopped`,
  `signal_action=hold`, `fills_total=0`, `closed_trades_total=0`, and
  `net_realized_pnl_total=0.0`.
- SHOWN: the session evidence contains start and end records with
  `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`,
  `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`, and
  `ohlcv_symbol=BTC/USDT`.
- SHOWN: the end record reports `campaign_status=completed`,
  `reconciliation_result=pass`, `ops_checks_passed=true`,
  `critical_error=false`, and `kill_switch_tested=true`.
- SHOWN: `paper_sim_monitor` sees `breakout_default` idle, flat, `fills=0`,
  `round_trips=0`, and `recommendation=continue`.
- SHOWN: canonical `sma_200_trend` completed its 2026-06-08 window with no new
  fills and remains not ready at `0/10` qualified round trips.
- SHOWN: isolated `ema_cross_default` completed its 2026-06-08 window with no
  new fills and remains at 2 fills, 1 closed trade, and +0.20272406454938546
  net realized PnL.

What changed:
- No source code, config, strategy preset, gate threshold, or canonical
  evidence was changed.
- This entry records the first-window completion proof for the accepted
  persistent breakout challenger.

Why this change:
- The accepted daily-loop start still had one open lifecycle risk: whether the
  first persistent window would complete and return to idle cleanly.
- Recording the completion proof keeps the governed work log aligned with the
  actual background-job state.

Expected outcome:
- `breakout_default`, `ema_cross_default`, and canonical `sma_200_trend` now
  continue as three isolated daily observation loops.
- Breakout evidence remains paper-only and isolated under
  `.cbp_state_challengers/breakout_default_daily`.
- Future actionable breakout signals, orders, fills, or position closes should
  be reviewed as challenger evidence only, not as `es_daily_trend_v1`
  promotion evidence.

Verification:
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `status=idle`, `reason=waiting_for_next_day`, `last_completed_day=2026-06-08`, and `pid_alive=true`.
- `cat .cbp_state_challengers/breakout_default_daily/data/evidence/breakout_default/session_2026-06-08.jsonl`
  - SHOWN: public non-sample 5-minute Coinbase provenance on start/end session
    records and clean completed end state.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: idle, flat, `fills_observed=0`, `round_trips_observed=0`, and
    `recommendation=continue`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state ./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: canonical paper gate remains not ready at `0/10` qualified round
    trips and 34/30 days recorded.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: `ema_cross_default` is idle, alive, and waiting for the next UTC
    day after a no-new-fill 2026-06-08 window.

Remaining risk:
- HIGH: ongoing financial strategy experimentation and background-job
  operation.
- UNVERIFIED: no actionable breakout order/fill/round trip has occurred yet.
- UNVERIFIED: no multi-day persistence proof exists yet beyond the first
  completed daily loop window.
- Acceptance state: `ACCEPTED`.

## 2026-06-08T15:12:00Z - Detached Paper Evidence Daily-Loop Launcher

Active role: `ENGINEER`

Objective: fix the operator workflow gap where a paper evidence daily loop
started from a Codex managed process session could die after the session ended.

What was found:
- SHOWN: the previously accepted `breakout_donchian` daily-loop collector PID
  `47262` was no longer alive even though its status file still reported
  `last_completed_day=2026-06-08`.
- SHOWN: canonical `sma_200_trend` PID `23879` and isolated
  `ema_cross_default` PID `8480` remained alive and parented to PID `1`.
- SHOWN: `scripts/run_paper_strategy_evidence_collector.py` exposed
  `--daily-loop`, `--status`, and `--stop`, but no authoritative detached
  top-level launch mode.
- SHOWN: existing service helpers use `start_new_session=True` for durable
  managed child processes, but the collector itself had no equivalent
  operator-facing launch path.

What changed:
- Added `--detach` to the authoritative
  `scripts/run_paper_strategy_evidence_collector.py` CLI.
- Scoped `--detach` to `--daily-loop` only; it cannot be combined with
  `--status` or `--stop`.
- The detached launcher:
  - refuses to start a duplicate collector when the selected `CBP_STATE_DIR`
    already has a live PID;
  - starts the same script without `--detach`;
  - inherits the selected environment, including `CBP_STATE_DIR`;
  - uses `start_new_session=True` on POSIX and detached process flags on
    Windows;
  - redirects child output to
    `<CBP_STATE_DIR>/runtime/logs/paper_strategy_evidence.log`;
  - waits briefly for the child to publish a matching live PID before reporting
    `detached_started`.
- Updated `docs/GOLDEN_PATH.md` and `scripts/SCRIPTS.md` to document
  `--daily-loop --detach` as the persistent operator path.
- Restarted only the isolated `breakout_donchian` challenger using the new
  detached path under
  `.cbp_state_challengers/breakout_default_daily`.

Why this change:
- The previous `nohup` attempt failed to initialize, and the successful
  managed-session launch did not survive as a durable background process.
- Adding the detached mode at the authoritative collector CLI keeps the
  operator workflow on one source of truth instead of adding another wrapper or
  service-manager fork.
- Duplicate-process protection and state-local logging make the launch auditable
  and safe for isolated challenger state directories.

Expected outcome:
- Future paper evidence daily loops can be started with
  `--daily-loop --detach` and survive the Codex session that started them.
- `breakout_donchian` continues as an isolated paper-only challenger and should
  wake on the next UTC day without manual polling.
- Canonical `sma_200_trend` and isolated `ema_cross_default` continue
  independently.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_run_paper_strategy_evidence_collector.py`
  - SHOWN: `10 passed in 0.25s`.
- `./.venv/bin/python -m pytest -q tests/test_run_paper_strategy_evidence_collector.py tests/test_dashboard_operator_service.py tests/test_bootstrap_helper_adoption.py`
  - SHOWN: `37 passed in 0.85s`.
- `./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --help`
  - SHOWN: help exposes `--detach` and describes detached daily-loop startup.
- `git diff --check`
  - SHOWN: clean.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py ... --daily-loop --detach`
  - SHOWN: returned `ok=true`, `reason=detached_started`, `pid=10310`, and
    log file under the isolated breakout state directory.
- `ps -o pid=,ppid=,stat=,etime=,command= -p 10310,23879,8480`
  - SHOWN: breakout PID `10310`, EMA PID `8480`, and canonical PID `23879` are
    all alive with `PPID=1`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/breakout_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: breakout status is `idle`, `reason=waiting_for_next_day`,
    `pid=10310`, `pid_alive=true`, `strategies=["breakout_donchian"]`, and
    evidence path remains under `.cbp_state_challengers/breakout_default_daily`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state_challengers/ema_cross_default_daily ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: EMA remains idle/alive at PID `8480`.
- `CBP_STATE_DIR=/Users/baitus/Downloads/crypto-bot-pro/.cbp_state ./.venv/bin/python scripts/run_paper_strategy_evidence_collector.py --status`
  - SHOWN: canonical `sma_200_trend` remains idle/alive at PID `23879`.

Remaining risk:
- HIGH: background-job operator workflow and financial strategy evidence
  collection.
- UNVERIFIED: no multi-day detached persistence proof exists yet; next proof is
  whether PID `10310` wakes and completes the next UTC daily window.
- UNVERIFIED: no actionable `breakout_donchian` order, fill, or round trip has
  occurred yet.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-08 after commit `c9e79eacd`.

## 2026-06-10 - Master Integration Handoff For Accepted Campaign Fixes

Active role: `GATE`

Objective: publish the accepted promotion-provenance visibility and detached
paper-loop changes for integration from `review-stabilized` into `master`.

What was found:
- SHOWN: the initial local comparison reported `review-stabilized` seven
  commits ahead of the stale local `master`.
- SHOWN: after fetching remote truth, `origin/master` already contained the
  five commits merged by PR `#52`; `review-stabilized` was three commits ahead
  and one merge commit behind.
- SHOWN: the branch diff is limited to promotion-progress explanation,
  detached collector startup, tests, operator documentation, and governed work
  records.
- SHOWN: no open `review-stabilized` to `master` pull request existed.
- SHOWN: canonical `sma_200_trend`, isolated `ema_cross_default`, and isolated
  `breakout_default` all completed the 2026-06-10 daily window and remained
  idle with live collector PIDs.
- SHOWN: the detached breakout collector completed daily windows on
  2026-06-08, 2026-06-09, and 2026-06-10.

What changed:
- Ran the full repository test suite to completion.
- Opened GitHub PR `#53`, `review-stabilized` to `master`:
  `https://github.com/Ddthomas415/CryptKeep/pull/53`.
- Merged current `origin/master` into `review-stabilized` with the `ort`
  strategy and no content conflicts or history rewrite.
- No campaign process, strategy configuration, gate threshold, order-routing
  behavior, or runtime evidence artifact was changed.

Why this change:
- The accepted fixes should not remain only on the review branch.
- A pull request preserves CI evidence and an explicit integration boundary
  before the canonical branch changes.
- Verifying campaign health before and after the suite ensures the integration
  proof did not interrupt active paper observation.

Expected outcome:
- GitHub CI evaluates the exact accepted branch tip.
- After required checks pass, PR `#53` can be merged into `master`.
- The three paper collectors continue independently while integration proceeds.

Verification:
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2118 passed, 33 skipped, 13 warnings in 393.84s`.
- `git diff --check`
  - SHOWN: clean.
- `git fetch origin master review-stabilized` followed by
  `git rev-list --left-right --count origin/master...review-stabilized`
  - SHOWN before synchronization: `1 3`.
- `git merge --no-edit origin/master`
  - SHOWN: clean `ort` merge with no content conflicts.
- GitHub PR `#53` checks on synchronized commit `f99ea206a`:
  - SHOWN: `CI validate`, `CI sanity`, macOS build, Windows build, both
    governance smoke checks, script-path integrity, and GitGuardian all passed.
- Collector status checks:
  - SHOWN: `sma_200_trend` PID `23879`, idle/alive, last completed
    `2026-06-10`.
  - SHOWN: `ema_cross_default` PID `8480`, idle/alive, last completed
    `2026-06-10`.
  - SHOWN: `breakout_default` PID `10310`, idle/alive, last completed
    `2026-06-10`.

Remaining risk:
- MEDIUM: administrative merge of PR `#53` into `master` remains pending.
- HIGH-risk implementation content in this PR was independently reviewed and
  accepted by the human operator before the integration handoff.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted implementation,
  clean local full suite, clean branch synchronization, and all GitHub PR
  checks passing on 2026-06-10.

## 2026-06-11T09:59:36Z - Count Held Bars By Market Timestamp

Active role: `ENGINEER`

Objective: stop the `breakout_donchian` and `ema_cross` paper runners from
consuming a bar-based time stop on repeated polling of the same market bar.

What was found:
- SHOWN: the isolated `breakout_donchian` campaign produced three round trips
  between `2026-06-11T00:03:20Z` and `2026-06-11T00:16:01Z` while consuming
  public Coinbase `5m` OHLCV.
- SHOWN: the first position-close monitor artifact reports
  `bars_held=60`, `exit_reason=strategy_exit:breakout_donchian:time_stop`, and
  `exit_stack_rule=time_stop` only about 162 seconds after entry.
- SHOWN: the isolated `ema_cross` position-close artifact also reports
  `strategy_exit:ema_cross:time_stop` after about 154 seconds.
- SHOWN: `ema_crossover_runner.py` incremented `bars_held` once per polling
  loop whenever a position was open, regardless of whether the latest OHLCV
  timestamp changed.
- SHOWN: the default `max_bars_hold` is `60`; therefore repeated polls of one
  five-minute candle could exhaust the configured limit in roughly 60 loops.
- SHOWN: the runner called `StrategyStateSQLite.delete(...)` during exit-state
  cleanup, but `storage/strategy_state_sqlite.py` did not implement `delete`;
  the resulting exceptions were swallowed.
- UNVERIFIED: the second and third breakout exits did not retain an exit reason
  in their captured monitor snapshots. Their timing is consistent with the
  same defect, but the exact cause of those two exits is not proven.

What changed:
- Added `_advance_held_bar_counter(...)` and a persisted
  `last_held_bar_ts:<venue>:<symbol>:<strategy>` state key.
- The runner now seeds the timestamp without incrementing, ignores repeated or
  older timestamps, and increments `bars_held` only when the market-data
  timestamp advances.
- Entry, flat-position, and sell cleanup now initialize or clear the timestamp
  key together with the existing entry, trailing-peak, and held-bar state.
- Added the missing `StrategyStateSQLite.delete(...)` operation so runner
  cleanup no longer silently fails.
- Added unit and runner-level regression tests proving repeated timestamps do
  not consume the time stop and genuinely newer timestamps still produce
  exactly one configured time-stop sell.

Why this change:
- `max_bars_hold` is a market-observation control, not a CPU-loop control.
  Counting poll iterations made exit timing depend on runner cadence and
  caused minute-scale churn on a five-minute strategy.
- Persisting the last counted timestamp preserves correct behavior across
  loops and process restarts without changing stop-loss, take-profit,
  trailing-stop, signal, order-routing, or gate thresholds.
- Implementing the store method used by the existing cleanup path is smaller
  and safer than continuing to suppress a broken interface contract.

Expected outcome:
- Public OHLCV campaigns count each candle timestamp once, so a 60-bar hold
  limit can no longer fire after 60 repeated polls of the same candle.
- Tick-derived sources count unique observation timestamps rather than raw
  loop iterations.
- Existing time stops still fire when the configured number of genuinely new
  market timestamps has elapsed.
- Stale runner exit state can be deleted when positions close or are flat.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py`
  - SHOWN: `31 passed in 0.76s`.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py tests/test_ema_runner_risk_defaults.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `65 passed in 1.11s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2117 passed, 33 skipped, 13 warnings in 214.60s`.
- `git diff --check`
  - SHOWN: clean.
- `ruff check` on the changed files
  - SHOWN: reports two pre-existing duplicate `sma_200_trend` dictionary keys
    at runner lines 64 and 75; neither finding is introduced or modified by
    this change.
- VERIFIED_ENV: all verification ran in the repository virtual environment
  from isolated worktree `/private/tmp/crypto-bot-pro-bar-hold-fix`.
- Collector status checks from the unchanged main workspace:
  - SHOWN: canonical `sma_200_trend` PID `23879` is idle/alive after completing
    the 2026-06-11 window.
  - SHOWN: isolated `ema_cross` PID `8480` is idle/alive after completing the
    2026-06-11 window.
  - SHOWN: isolated `breakout_donchian` PID `10310` is idle/alive after
    completing the 2026-06-11 window.

Remaining risk:
- HIGH: this changes financial strategy exit timing and background-runner
  state semantics.
- UNVERIFIED: no live paper campaign has run on this branch; active collectors
  remain on accepted commit `13cba446b` and were not restarted or modified.
- UNVERIFIED: sell intent metadata does not directly persist `exit_reason`, so
  later evidence may still require monitor snapshots to attribute an exit.
- SHOWN: the daily-loop collector launches `scripts/run_strategy_runner.py` as
  a fresh subprocess for each strategy window, so integration before the next
  UTC window applies the fix without restarting the collector parents.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `a0a1403de`.

## 2026-06-11T10:11:31Z - Integrate Accepted Market-Bar Time-Stop Fix

Active role: `GATE`

Objective: integrate the independently accepted strategy-runner correction
into `review-stabilized` without interrupting active paper campaigns.

What was found:
- SHOWN: `codex/fix-bar-hold-clock` was a clean two-commit descendant of
  `review-stabilized`; no conflict resolution or history rewrite was needed.
- SHOWN: the daily-loop collector launches a fresh strategy-runner subprocess
  for each UTC evidence window.
- SHOWN: canonical, EMA, and breakout collector parents had already completed
  the 2026-06-11 window and remained idle with live PIDs.

What changed:
- Merged accepted commits `a0a1403de` and `91fd74b50` into
  `review-stabilized` as merge commit `0efcd55c3`.
- After verifying the feature tip was an ancestor of `review-stabilized`,
  removed the temporary worktree and deleted the merged local and remote
  `codex/fix-bar-hold-clock` branches.
- No collector process, evidence artifact, strategy configuration, gate
  threshold, or current position was changed.

Why this change:
- The correction must be on the branch used by the next freshly launched
  strategy runner.
- Preserving the collector parents avoids an unnecessary campaign restart
  while still applying the accepted code on the next UTC window.

Expected outcome:
- The June 12 EMA and breakout strategy windows load the market-timestamp bar
  counter automatically.
- Repeated polling of one five-minute candle no longer consumes the 60-bar
  time stop.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_breakout_runner_exit_stack.py tests/test_exit_control_stack.py tests/test_ema_runner_risk_defaults.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `65 passed in 1.14s`.
- `git diff --check origin/review-stabilized...HEAD`
  - SHOWN: clean.
- `git merge-base --is-ancestor codex/fix-bar-hold-clock review-stabilized`
  - SHOWN: returned success before branch cleanup.
- Collector status checks:
  - SHOWN: `sma_200_trend` PID `23879`, idle/alive.
  - SHOWN: `ema_cross` PID `8480`, idle/alive.
  - SHOWN: `breakout_donchian` PID `10310`, idle/alive.

Remaining risk:
- HIGH implementation risk was independently accepted before integration.
- UNVERIFIED: the corrected behavior has not yet completed a real paper
  window; the next proof point is the June 12 challenger evidence.
- Acceptance state: `ACCEPTED`.

## 2026-06-11T10:18:03Z - Re-enable Breakout Desktop Notifications

Active role: `ENGINEER`

Objective: restore desktop delivery for the existing breakout monitor watches
without changing campaign evidence, strategy settings, or other collectors.

What was found:
- SHOWN: canonical PID `23879` and EMA PID `8480` were launched with the
  default notification-enabled mode.
- SHOWN: breakout PID `10310` was explicitly launched with
  `--no-desktop-notify`.
- SHOWN: the June 11 canonical and EMA watch reports recorded
  `desktop_notification.sent=true`.
- SHOWN: the June 11 breakout investigate report recorded
  `attempted=false`, `sent=false`, and `reason=disabled`.
- SHOWN: all four breakout watches were active and writing report artifacts;
  only desktop delivery was disabled.

What changed:
- Requested a supported stop for idle breakout collector PID `10310`.
- Waited for the 300-second daily-loop poll boundary until status showed
  `stop_requested`, `pid_alive=false`, and no PID file.
- Started the same detached breakout daily-loop command in the same isolated
  state directory without `--no-desktop-notify`.
- The replacement collector is PID `32873`, idle and waiting for the next UTC
  day.

Why this change:
- The monitor and trigger layer already worked; replacing the parent launch
  flag is the smallest correction that restores user-visible notifications.
- The June 11 session was complete, so the supported stop/detach sequence
  avoided interrupting an active runner or duplicating the daily campaign.

Expected outcome:
- The next breakout fill, position close, investigate recommendation, or
  campaign-completed event writes its normal report and attempts local desktop
  delivery.
- The June 12 breakout strategy window also loads the accepted market-bar
  time-stop implementation from `review-stabilized`.

Verification:
- Old collector status:
  - SHOWN: PID `10310` stopped with `reason=stop_requested`,
    `pid_alive=false`, and `has_pid_file=false`.
- Replacement start:
  - SHOWN: detach returned `reason=detached_started`, PID `32873`.
  - SHOWN: status reports `idle`, `waiting_for_next_day`, `pid_alive=true`,
    and `last_completed_day=2026-06-11`.
- Process command inspection:
  - SHOWN: PID `32873` retains the breakout strategy, session ID, BTC/USDT,
    Coinbase, public 5-minute OHLCV, 900-second runtime, and 300-second daily
    poll settings.
  - SHOWN: PID `32873` does not contain `--no-desktop-notify`.
- Evidence integrity:
  - SHOWN: persisted paper history remains six fills, three closed trades, and
    `-0.38540687113248273` net realized PnL.
  - SHOWN: evidence inventory remains one fill file, one order file, four
    session files, and 20 total records.
- Isolation:
  - SHOWN: canonical PID `23879` and EMA PID `8480` remained alive with their
    original command lines.
- VERIFIED_ENV: commands ran from the synchronized `review-stabilized`
  workspace at `bf2aae822`.

Remaining risk:
- HIGH: this changed a persistent background monitoring job.
- UNVERIFIED: no new breakout watch event has fired after PID `32873` started,
  so actual desktop delivery from the replacement process is not yet shown.
- UNVERIFIED: the June 12 paper window has not yet exercised the accepted
  market-bar time-stop correction.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `7f3084f65`.

## 2026-06-11T12:53:51Z - Remove Stale Promotion Worktree Registration

Active role: `ENGINEER`

Objective: remove a dead worktree registration and its fully merged feature
branch so Git no longer advertises a nonexistent checkout.

What was found:
- SHOWN: `/private/tmp/cryptkeep-shadow-gate-evidence-scope` did not exist.
- SHOWN: `git worktree prune --dry-run --verbose` identified its registration
  as prunable because the gitdir target was missing.
- SHOWN: local and remote `codex/promotion-provenance-visibility` were each
  fully contained in `review-stabilized`; the comparison was 18 commits on
  `review-stabilized` and zero unique feature commits.

What changed:
- Pruned the stale worktree registration.
- Deleted the fully merged local
  `codex/promotion-provenance-visibility` branch.
- Deleted the corresponding fully merged remote branch.

Why this change:
- A dead worktree registration can block branch cleanup and create false
  branch-conflict signals.
- Ancestry was proven before deletion, so no unique commit was discarded.

Expected outcome:
- `git worktree list` reports only the active repository checkout.
- Future branch and worktree operations no longer encounter the stale
  promotion-provenance registration.

Verification:
- `git worktree list --porcelain`
  - SHOWN: only `/Users/baitus/Downloads/crypto-bot-pro` remains.
- `git branch -vv | rg 'promotion-provenance-visibility'`
  - SHOWN: no local branch remains.
- `git status -sb`
  - SHOWN: `review-stabilized` is clean and synchronized before this log
    entry.
- VERIFIED_ENV: Git cleanup ran in the canonical repository checkout.

Remaining risk:
- LOW: metadata and fully merged branch cleanup only.
- No runtime process, evidence artifact, source file, or strategy behavior was
  changed.
- Acceptance state: `ACCEPTED`.

## 2026-06-11T13:19:53Z - Persist Strategy Exit Attribution

Active role: `ENGINEER`

Objective: make strategy-driven sell reasons durable across paper intent,
order/fill evidence, reconciliation outcomes, and closed-trade summaries.

What was found:
- SHOWN: the June 11 breakout paper database contains three sell orders whose
  metadata has `exit_reason=None` and `exit_stack_rule=None`.
- SHOWN: the June 11 EMA paper database contains one sell order with the same
  missing attribution.
- SHOWN: the first breakout position-close monitor artifact temporarily
  reported `strategy_exit:breakout_donchian:time_stop`, but that reason was not
  copied into the queued intent or durable paper order.
- SHOWN: `paper_engine.py` copied only market-data provenance fields into order
  and fill JSONL evidence.
- SHOWN: both strategy outcome producers copied `signal_reason` but omitted
  `exit_reason` and `exit_stack_rule`.

What changed:
- Exit-stack and EMA-invalidation sells now add `exit_reason` to intent
  metadata; stack exits also add `exit_stack_rule`.
- Ordinary buy and signal-change intents remain unchanged and do not receive
  exit attribution fields.
- Paper order and fill JSONL evidence now preserves the two exit-attribution
  fields alongside existing market-data provenance.
- Paper intent reconciliation and execution-plan reconciliation now copy the
  fields into strategy outcome rows.
- Closed-trade summaries now expose both fields.
- Added unit and SQLite-backed integration coverage from queued sell intent
  through paper order, fill JSONL, reconciliation, and summary output.

Why this change:
- Exit attribution must survive beyond transient runner status to support
  strategy review, churn diagnosis, and performance analysis by exit type.
- Copying existing metadata is the smallest coherent fix; no order decision,
  side, quantity, venue, risk threshold, or execution route changes.

Expected outcome:
- Future strategy-driven paper exits can be classified as time stop, stop
  loss, take profit, trailing stop, or EMA invalidation from durable evidence.
- Operators no longer need a precisely timed monitor snapshot to determine why
  a position closed.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_paper_engine_integration.py tests/test_intent_reconciler.py tests/test_paper_strategy_journal_flow.py tests/test_outcome_summary.py`
  - SHOWN: `40 passed in 1.30s`.
- Broader paper execution and evidence regression slice:
  - SHOWN: `78 passed in 2.54s`.
- `./.venv/bin/python -m pytest tests -q`
  - SHOWN: `2119 passed, 33 skipped, 13 warnings in 208.72s`.
- `git diff --check`
  - SHOWN: clean.
- `ruff check` on the non-runner changed files
  - SHOWN: reported only pre-existing import-order and unused-import findings
    at the top of `paper_engine.py`; no changed block introduced a lint
    finding.
- VERIFIED_ENV: all tests ran in repository virtual environment from isolated
  worktree `/private/tmp/crypto-bot-pro-exit-attribution`.
- Isolation:
  - SHOWN: canonical workspace remained clean on `review-stabilized`.
  - SHOWN: breakout collector PID `32873` remained idle/alive.

Remaining risk:
- HIGH: this changes financial evidence and execution-observability surfaces.
- UNVERIFIED: no real paper exit has yet written the new fields.
- Historical June 11 evidence is not backfilled; the change applies to future
  orders and fills only.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-11 after commit `493d9d76c`.

## 2026-06-11T13:36:56Z - Integrate Accepted Exit Attribution

Active role: `GATE`

Objective: integrate the independently accepted exit-attribution evidence
change without interrupting active paper collectors.

What was found:
- SHOWN: `codex/persist-exit-attribution` was a clean two-commit descendant of
  `review-stabilized`.
- SHOWN: the feature commit had full-suite proof of `2119 passed, 33 skipped`.
- SHOWN: all three collector parents had completed the June 11 window and were
  idle with live PIDs.

What changed:
- Merged accepted commits `493d9d76c` and `2ad46c2e6` into
  `review-stabilized` as merge commit `d270fe1dc`.
- No collector process, position, strategy configuration, evidence artifact,
  or historical record was modified.

Why this change:
- Future paper exits need durable reason attribution before the next strategy
  windows launch.
- Fresh runner and paper-engine subprocesses are launched for each UTC window,
  so collector-parent restarts are unnecessary.

Expected outcome:
- Future strategy-driven paper sell orders and fills preserve
  `exit_reason` and `exit_stack_rule`.
- Reconciled outcome rows and closed-trade summaries expose the same fields.

Verification:
- Merged execution/evidence regression slice:
  - SHOWN: `78 passed in 2.74s`.
- `git diff --check origin/review-stabilized...HEAD`
  - SHOWN: clean.
- Collector status:
  - SHOWN: canonical PID `23879`, idle/alive.
  - SHOWN: EMA PID `8480`, idle/alive.
  - SHOWN: breakout PID `32873`, idle/alive.

Remaining risk:
- HIGH implementation risk was independently accepted before integration.
- UNVERIFIED: no real post-integration paper exit has yet persisted the new
  attribution fields.
- Historical June 11 orders and fills remain unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-12T09:43:25Z - Explain Excluded Paper Promotion History

Active role: `ENGINEER`

Objective: make the paper promotion gate explain why seven persisted round
trips no longer advance the provenance-qualified threshold.

What was found:
- SHOWN: the strict qualification rule introduced by `7ab11da59` requires both
  entry and exit fills to carry matching public OHLCV provenance.
- SHOWN: the canonical journal contains seven all-history round trips, but the
  JSONL evidence has nine fills with missing provenance and one qualified exit
  that is not paired with a qualified entry.
- SHOWN: April 20 signal prices materially diverge from contemporaneous paper
  fill prices, and the historical collector code explicitly supported sample
  OHLCV. Those trades cannot safely be relabeled as public-market evidence.
- SHOWN: the gate decision is therefore correct at zero qualified round trips;
  the defect is that the round-trip detail does not explain the exclusion.

What changed:
- Added diagnostic-only, unqualified-fill, and incomplete-qualified-fill
  context to the paper round-trip gate detail.
- Added regression coverage for missing JSONL history and the canonical
  `7 all-history / 9 unqualified / 1 incomplete` shape.
- Did not change qualification, threshold, expectancy, retirement, or
  promotion-ready calculations.

Why this change:
- Grandfathering or backfilling missing provenance would convert inference
  into promotion evidence and weaken the gate.
- Explicit reporting preserves the safety rule while preventing operators
  from interpreting `0/10` as lost or deleted trade history.

Expected outcome:
- `check_promotion_gates.py --json` continues to report zero qualified round
  trips, but states that seven all-history trips are diagnostic only and
  identifies the exact JSONL qualification gaps.

Verification:
- Canonical virtualenv targeted promotion tests:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  - SHOWN: `44 passed in 0.93s`.
- Dashboard/monitor regression slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_strategy_evidence_runtime.py tests/test_dashboard_page_runtime.py`
  - SHOWN: `37 passed in 1.05s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2120 passed, 33 skipped, 13 warnings in 209.18s`.
- Canonical gate-output inspection:
  - SHOWN: `ready=false`, `machine_ready=false`, and `7 pass / 2 unknown`
    remain unchanged.
  - SHOWN: the round-trip detail now reports seven diagnostic-only trips,
    nine of ten JSONL fills with missing or mismatched provenance, and one
    incomplete qualified fill.
- Old/new canonical JSON comparison:
  - SHOWN: after normalizing the intended round-trip detail, the only
    remaining difference was the per-run `evidence_scope.since_ts` timestamp.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m py_compile scripts/check_promotion_gates.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.
- VERIFIED_ENV: implementation is isolated in
  `/private/tmp/crypto-bot-pro-provenance-audit`.

Remaining risk:
- HIGH: this is financial promotion-gate reporting, although decision logic is
  unchanged.
- Historical provenance remains unverified and is intentionally not backfilled.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-12 after commit `a8b12463e`.

## 2026-06-12T09:52:44Z - Integrate Accepted Provenance Explanation

Active role: `GATE`

Objective: integrate the independently accepted paper promotion-history
explanation while preserving existing audit records and active campaigns.

What was found:
- SHOWN: accepted branch `codex/explain-provenance-qualification` contained
  implementation commit `a8b12463e` and human-acceptance record `a2d20dea1`.
- SHOWN: `review-stabilized` had a pending, unrelated work-log entry for the
  previously accepted exit-attribution integration.
- SHOWN: canonical, EMA, and breakout collectors were idle/alive after
  completing their June 12 windows.

What changed:
- Preserved the pending exit-attribution integration record in commit
  `27b2e3a00`.
- Merged the accepted provenance-explanation branch into `review-stabilized`
  as `4ac757dfc`.
- Resolved the work-log conflict by retaining both chronological entries.
- No evidence artifact, campaign configuration, threshold, qualification
  decision, order route, or runtime process was changed.

Why this change:
- The accepted reporting fix must be visible on the canonical review branch.
- Keeping both work-log entries preserves the governed audit trail rather than
  choosing one branch's documentation over the other.

Expected outcome:
- Operators see why seven historical round trips are diagnostic only while the
  promotion gate continues to count zero provenance-qualified round trips.
- Active collectors continue without restart or evidence mutation.

Verification:
- Merged promotion, monitor, and dashboard regression slice:
  - SHOWN: `81 passed in 1.87s`.
- Accepted branch full suite:
  - SHOWN: `2120 passed, 33 skipped, 13 warnings in 209.18s`.
- Canonical gate output:
  - SHOWN: `ready=false`, `machine_ready=false`, `7 pass / 2 unknown`.
  - SHOWN: detail reports seven diagnostic-only trips, nine unqualified fills,
    and one incomplete qualified fill.
- `git diff --check`
  - SHOWN: clean before merge completion.
- VERIFIED_ENV: integration and verification ran in the canonical repository
  checkout.

Remaining risk:
- Historical provenance remains unverified and intentionally does not count
  toward promotion.
- No real post-integration exit has yet verified durable exit attribution.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human acceptance on 2026-06-12, followed by GATE
  integration commit `4ac757dfc`.

## 2026-06-12T09:55:27Z - Scope Monitor Promotion Progress

Active role: `ENGINEER`

Objective: prevent challenger paper monitors from displaying the canonical
`es_daily_trend_v1` promotion gate.

What was found:
- SHOWN: `paper_sim_monitor._promotion_progress_snapshot()` unconditionally
  called `load_paper_promotion_progress()` with canonical defaults.
- SHOWN: EMA and breakout monitor artifacts therefore displayed the SMA
  strategy's evidence directory, `0/30` days, and `0/10` round trips.
- SHOWN: the repo defines promotion thresholds only for
  `es_daily_trend_v1` / `sma_200_trend`; no accepted threshold policy exists
  for `ema_cross_default` or `breakout_default`.
- SHOWN: the Operations page rendered every false readiness value as
  `not_ready`, so a monitor-only change would still leave misleading UI text.

What changed:
- The monitor now passes the active preset, strategy, and symbol into the
  promotion-progress resolver.
- Canonical SMA campaigns continue loading the existing paper promotion gate.
- Noncanonical campaigns return `status=not_configured`,
  `applicable=false`, no blockers, and an explicit informational summary.
- Runtime normalization exposes `promotion_thresholds_applicable`.
- Operations renders `not_configured` instead of `not_ready` for challengers.
- Added monitor and dashboard-runtime regression coverage.

Why this change:
- Reusing one strategy's gate for another strategy misstates both evidence and
  policy.
- Inventing challenger thresholds in this patch would be an unsupported policy
  decision; explicit non-applicability is the smallest correct behavior.

Expected outcome:
- EMA and breakout campaign summaries show their own trade metrics without
  claiming progress against the SMA promotion gate.
- Canonical `es_daily_trend_v1` monitoring and gate calculations remain
  unchanged.

Verification:
- Canonical virtualenv targeted monitor, dashboard, and promotion slice:
  - SHOWN: `84 passed in 1.41s`.
- `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest tests -q`
  - SHOWN: `2123 passed, 33 skipped, 13 warnings in 206.42s`.
- Real-state read-only `collect_once` snapshots:
  - SHOWN: canonical `es_daily_trend_v1` returned `applicable=true` and retained
    its existing qualified promotion summary.
  - SHOWN: `ema_cross_default` returned `status=not_configured`,
    `applicable=false`, and its own strategy ID.
  - SHOWN: `breakout_default` returned `status=not_configured`,
    `applicable=false`, and its own strategy ID.
- Python compilation:
  - SHOWN: monitor, dashboard runtime, and Operations page compiled cleanly.
- `git diff --check`
  - SHOWN: clean.
- VERIFIED_ENV: implementation is isolated in
  `/private/tmp/crypto-bot-pro-monitor-progress`.

Remaining risk:
- HIGH: this changes financial operator-status reporting.
- No challenger promotion policy is added; that remains a separate governance
  decision.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-12.

## 2026-06-12T10:07:48Z - Integrate Accepted Monitor Promotion Scoping

Active role: `GATE`

Objective: integrate the accepted challenger monitor promotion-policy scoping
without restarting active paper collectors.

What was found:
- SHOWN: accepted commit `038d5afe3` was a clean descendant of the current
  `review-stabilized` tip.
- SHOWN: canonical, EMA, and breakout collectors remained idle/alive after
  completing their June 12 windows.
- SHOWN: the operator requested that no additional full-suite tests run.

What changed:
- Merged `codex/scope-monitor-promotion-progress` into `review-stabilized` as
  `833b27f6d`.
- No collector process, evidence artifact, strategy threshold, campaign
  configuration, or order path was changed during integration.

Why this change:
- The accepted fix removes false canonical-gate status from challenger monitor
  and Operations surfaces.
- Targeted verification is sufficient for integration because the accepted
  branch already had full-suite proof and the operator explicitly stopped
  further full-suite runs.

Expected outcome:
- Canonical `es_daily_trend_v1` monitoring continues to show its configured
  promotion gate.
- EMA and breakout monitoring show `not_configured` rather than canonical SMA
  gate progress or `not_ready`.

Verification:
- Merged monitor, dashboard, and promotion regression slice:
  - SHOWN: `84 passed in 1.89s`.
- Python compilation:
  - SHOWN: monitor, dashboard runtime, and Operations page compiled cleanly.
- Real-state read-only snapshots:
  - SHOWN: canonical returned `applicable=true`.
  - SHOWN: EMA returned `applicable=false`, `status=not_configured`.
  - SHOWN: breakout returned `applicable=false`, `status=not_configured`.
- `git diff --check`
  - SHOWN: clean.
- Full suite was not rerun after acceptance at the operator's direction.
- VERIFIED_ENV: integration verification ran in the canonical repository
  checkout.

Remaining risk:
- Challenger promotion thresholds remain intentionally undefined pending a
  separate governance decision.
- Active monitor subprocesses will load the integrated code on their next
  daily campaign window; no parent restart was performed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human acceptance on 2026-06-12, followed by GATE
  integration commit `833b27f6d`.

## 2026-06-13T17:29:35Z - Restore Paper Collectors After Host Restart

Active role: `GATE`

Objective: verify the paper campaigns after a host restart and restore the
accepted detached daily loops without duplicating the completed June 13
evidence windows.

What was found:
- SHOWN: `review-stabilized` was clean and synchronized with
  `origin/review-stabilized` at `e18512637`.
- SHOWN: the canonical, EMA, and breakout status artifacts each reported
  `last_completed_day=2026-06-13`, but their recorded pre-restart PIDs were no
  longer alive.
- SHOWN: the completed June 13 windows recorded no new fills:
  canonical remained at 14 fills and 7 all-history closed trades, EMA remained
  at 4 fills and 2 closed trades, and breakout remained at 6 fills and 3
  closed trades.
- SHOWN: the current paper promotion gate counts 0 provenance-qualified round
  trips, not the 7 diagnostic all-history round trips. Nine of ten JSONL fills
  lack or mismatch required provenance, and the one provenance-qualified fill
  is not part of a complete qualified round trip.

What changed:
- Restarted the canonical detached daily loop with `sma_200_trend`,
  `es_daily_trend_v1`, `BTC/USDT`, Coinbase, `public_ohlcv_1d`, a 20-second
  strategy window, and a 300-second poll interval.
- Restarted the isolated EMA detached daily loop with `ema_cross`,
  `ema_cross_default`, `public_ohlcv_5m`, a 900-second strategy window, and a
  300-second poll interval.
- Restarted the isolated breakout detached daily loop with
  `breakout_donchian`, `breakout_default`, `public_ohlcv_5m`, a 900-second
  strategy window, and a 300-second poll interval.
- No strategy configuration, evidence record, promotion threshold, source
  code, or historical trade record was edited.

Why this change:
- The host restart terminated the accepted background processes even though
  their latest daily windows had completed successfully.
- The collector's built-in `--daily-loop --detach` path is the authoritative
  restart mechanism and checks the existing session file before running, so it
  preserves one evidence window per UTC day.
- Keeping each challenger under its dedicated `CBP_STATE_DIR` preserves
  evidence isolation.

Expected outcome:
- All three collectors remain idle for the rest of June 13 and wake for their
  next evidence window after the UTC date changes to June 14.
- Canonical and challenger evidence continue to accumulate independently.
- Promotion output continues to distinguish diagnostic all-history trades from
  provenance-qualified gate evidence.

Verification:
- Canonical status:
  - SHOWN: PID `7795`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- EMA status:
  - SHOWN: PID `7630`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- Breakout status:
  - SHOWN: PID `7628`, `pid_alive=true`, `status=idle`,
    `reason=waiting_for_next_day`, and `last_completed_day=2026-06-13`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: 39/30 calendar days, 0/10 provenance-qualified round trips, 7
    diagnostic all-history round trips, and `manual_review_required=true`.
- No test suite was run because this was an operational restart with no source
  changes and the operator previously directed that full-suite runs stop.
- VERIFIED_ENV: commands ran from the clean synchronized canonical checkout.

Remaining risk:
- HIGH: persistent financial evidence-collection background jobs were
  restarted.
- UNVERIFIED: the replacement processes have not yet crossed a UTC boundary
  and completed their first post-restart windows.
- The canonical promotion gate still requires ten complete
  provenance-qualified round trips; historical unqualified fills cannot
  satisfy that gate.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-13 after commit `8fa0a542a`.

## 2026-06-13T17:36:55Z - Idempotent Paper Campaign Recovery Command

Active role: `ENGINEER`

Objective: reduce post-reboot recovery from three manually reconstructed
collector commands to one explicit, idempotent, auditable operator command.

What was found:
- SHOWN: the June 13 host restart terminated all three detached collector
  parents even though their daily evidence windows had completed.
- SHOWN: the repo's canonical supervisors manage bot/runtime services but do
  not own the canonical and isolated paper evidence campaigns.
- SHOWN: the collector already provides the authoritative
  `--daily-loop --detach` startup path and duplicate-process protection.
- SHOWN: the paper promotion gate's 0/10 qualified result is intentional,
  independently accepted provenance policy from `7ab11da59`, not a new
  counting defect. The seven historical round trips remain diagnostic.

What changed:
- Added `configs/paper_evidence_campaigns.json` as the explicit manifest for
  the accepted canonical SMA, isolated EMA, and isolated breakout campaigns.
- Added `services/analytics/paper_campaign_recovery.py` to validate the
  manifest, query each isolated status surface, start only dead collectors,
  and verify replacement process state.
- Added `scripts/restore_paper_campaigns.py`; read-only status is the default,
  while `--restore` is required to start background jobs.
- Added `make status-paper-campaigns` and `make restore-paper-campaigns`.
- Added focused service/CLI tests and documented the recovery workflow in the
  Golden Path, script index, and `docs/PAPER_CAMPAIGN_RECOVERY.md`.
- Did not add OS-login auto-start and did not add paper campaigns to a generic
  live-adjacent supervisor.

Why this change:
- Reusing the existing collector preserves one process owner, one duplicate
  guard, and the accepted per-state evidence isolation.
- A manifest prevents strategy parameters from being reconstructed from memory
  after every reboot.
- Explicit restore is safer than automatic login startup because it does not
  launch financial background jobs merely because the desktop app opened.
- Extending a generic supervisor would broaden process-control scope and
  create additional stop/status semantics without being required for recovery.

Expected outcome:
- `make status-paper-campaigns` reports all configured campaigns and exits
  nonzero when any collector is not alive.
- `make restore-paper-campaigns` leaves live collectors unchanged, restores
  only dead collectors, and reports verified replacement PIDs.
- Repeated restore calls do not create duplicate collectors.
- Canonical and challenger evidence continue to use their existing isolated
  `CBP_STATE_DIR` paths and accepted signal-source/runtime parameters.

Verification:
- Targeted recovery, collector, and bootstrap regression slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py tests/test_run_paper_strategy_evidence_collector.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `35 passed in 0.97s`.
- Python compilation:
  - SHOWN: `paper_campaign_recovery.py` and
    `restore_paper_campaigns.py` compiled cleanly.
- CLI help:
  - SHOWN: exposes `--status`, `--restore`, repeatable `--campaign`, and
    `--config`.
- Make target dry run:
  - SHOWN: `status-paper-campaigns` invokes the read-only status mode and
    `restore-paper-campaigns` invokes explicit restore mode.
- `git diff --check`
  - SHOWN: clean.
- Canonical collector status from the untouched primary checkout:
  - SHOWN: PID `7795` remained alive and idle for the completed June 13
    canonical window during isolated implementation.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: implementation and verification ran in isolated worktree
  `/private/tmp/crypto-bot-pro-paper-restore`, based on synchronized commit
  `9ba375654`; active collectors in the canonical checkout were not restarted
  or modified.

Remaining risk:
- HIGH: this command starts persistent financial evidence-collection
  background jobs.
- UNVERIFIED: a real dead-process restore has not been executed from this
  feature branch because doing so would replace currently healthy accepted
  collectors.
- UNVERIFIED: post-reboot use still requires one explicit operator command;
  OS-login automation remains intentionally out of scope.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-14 after implementation commit `1b23f67b7`.

## 2026-06-15T02:15:41Z - Accepted Paper Campaign Recovery Integration

Active role: `GATE`

Objective: integrate the independently accepted paper campaign recovery
command into `review-stabilized` and verify the merged operator surface
without restarting active collectors.

What was found:
- SHOWN: accepted implementation commit `1b23f67b7` and acceptance record
  `5233c10d4` were merged into `review-stabilized` as `833a33ecb`.
- SHOWN: the integrated read-only status command reports all three configured
  collector parents alive: canonical SMA, EMA crossover, and Donchian
  breakout.
- SHOWN: each collector reports the June 15 window as completed and is idle
  until the next UTC day.
- SHOWN: the status payload does not prove the June 15 market-data window was
  valid; that health classification remains a separate campaign-lifecycle
  concern.

What changed:
- Recorded the accepted merge and post-merge verification in the governed
  work log.
- No runtime process, campaign configuration, evidence artifact, or trading
  behavior was changed during integration.

Why this change:
- The work log must preserve the accepted feature's transition from isolated
  branch proof to the primary review branch.
- Read-only verification confirms that the merged command observes the
  existing processes without replacing them.

Expected outcome:
- Future operators can trace the recovery feature from implementation through
  human acceptance, merge, and integrated verification.
- `review-stabilized` exposes one auditable command for status and explicit
  post-reboot restore.

Verification:
- `./.venv/bin/python scripts/restore_paper_campaigns.py --status`
  - SHOWN: `all_running=true`, `running_count=3`, `campaign_count=3`.
  - SHOWN: PIDs `7795`, `7630`, and `7628` remain alive.
- `./.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - SHOWN: `12 passed in 0.16s`.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: commands ran from the primary
  `/Users/baitus/Downloads/crypto-bot-pro` checkout at merge `833a33ecb`.

Remaining risk:
- HIGH: the command can start persistent financial evidence-collection
  background jobs when invoked with `--restore`.
- UNVERIFIED: no dead-process restore was performed during integration because
  all accepted collectors were healthy.
- SHOWN: campaign process liveness is distinct from market-data validity; the
  latter requires a separate fail-closed lifecycle fix.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: implementation independently reviewed and accepted by
  the human operator on 2026-06-14; integrated without runtime changes on
  2026-06-15.

## 2026-06-15T02:28:02Z - Fail-Closed Public OHLCV Campaign Health

Active role: `ENGINEER`

Objective: prevent managed paper evidence campaigns from reporting successful
daily completion when the strategy runner receives no public OHLCV market data.

What was found:
- SHOWN: the canonical SMA, EMA, and Donchian collector parents were alive
  after the host restart.
- SHOWN: June 15 runner logs repeatedly reported Coinbase OHLCV fetch failure
  and `note=no_public_ohlcv`.
- SHOWN: no June 15 signal evidence files were produced, but each campaign was
  recorded as `status=completed`, `reason=completed`.
- SHOWN: `_run_strategy_window` replaced the last meaningful runner note with
  the runner's final `stopped` payload.
- SHOWN: the daily loop treated any non-empty session file, including a
  start-only or failed attempt, as a completed day.
- SHOWN: governance `INVALID` is terminal and therefore inappropriate for a
  recoverable infrastructure outage.

What changed:
- Preserved runner observations made during the current strategy window and
  classified a full public-OHLCV window with no observed market price as
  `stop_reason=no_public_ohlcv`.
- Made `run_campaign` return `ok=false`, `status=failed`, and skip leaderboard
  evidence persistence for that condition.
- Added `campaign_reason` to session-end evidence; failed runs now retain the
  existing `critical_error=true` and failed reconciliation classification.
- Changed daily completion detection to require a `phase=end`,
  `campaign_status=completed` session record.
- Added a bounded same-day retry policy: one initial attempt plus one retry,
  followed by failed status until the next UTC day.
- Added `max_daily_attempts` to the canonical campaign manifest and recovery
  launch contract, with a backward-compatible schema-v1 default of `2`.
- Documented that process liveness and campaign health are separate and that
  restore does not replace an alive collector that owns a pending retry.

Why this change:
- A market-data outage is retryable infrastructure failure, not valid strategy
  evidence and not terminal evidence contamination.
- `failed` preserves operator visibility and promotion-gate blocking without
  requiring manual repair of terminal governance state.
- Two attempts permit one transient recovery opportunity while preventing
  indefinite API retry loops and duplicate daily evidence campaigns.
- Keeping retry ownership in the existing parent preserves the accepted
  duplicate-process boundary.

Expected outcome:
- Public-OHLCV outages cannot create false completed campaign days.
- Failed windows create critical session evidence and cannot be mistaken for
  promotion-quality operation.
- Status and recovery output can show `running=true` with `ok=false`, making
  alive-but-unhealthy campaigns visible.
- A transient outage receives one bounded retry; a persistent outage remains
  failed until the next UTC day.
- Successful campaign and evidence-persistence behavior remains unchanged.

Verification:
- Targeted service, collector, and recovery slice:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_strategy_evidence_service.py tests/test_run_paper_strategy_evidence_collector.py tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - SHOWN: `54 passed in 0.67s`.
- Paper simulation monitor contract:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_paper_sim_monitor.py tests/test_run_paper_sim_monitor.py`
  - SHOWN: `21 passed in 0.33s`.
- Promotion-gate session-health contract:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py`
  - SHOWN: `42 passed in 0.95s`.
- Python compilation:
  - SHOWN: the collector, recovery service, and evidence service compiled
    cleanly.
- Collector CLI help:
  - SHOWN: `--max-daily-attempts` is exposed.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: verification used the primary virtual environment against the
  isolated worktree `/private/tmp/crypto-bot-pro-ohlcv-fail-closed` based on
  synchronized `review-stabilized` commit `f8e93e2ba`.

Remaining risk:
- HIGH: this changes financial evidence background-job lifecycle, retry
  behavior, and promotion-gate session inputs.
- UNVERIFIED: no live Coinbase outage/recovery cycle was induced; runtime proof
  is limited to existing logs plus deterministic tests.
- UNVERIFIED: existing collector processes still run the previously loaded
  code and must not be restarted onto this change before independent review.
- SHOWN: the already-written June 15 false-completion records are not mutated;
  a later healthy UTC day will supersede them in the latest-window gate.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-15 after implementation commit `9bd30e8bb`.

## 2026-06-15T02:31:21Z - Accepted Fail-Closed OHLCV Integration

Active role: `GATE`

Objective: integrate the independently accepted public-OHLCV fail-closed
lifecycle into `review-stabilized` without restarting active collectors.

What was found:
- SHOWN: implementation `9bd30e8bb` and human acceptance record `8467a821b`
  were clean and synchronized before integration.
- SHOWN: merge `9a6c3e08a` completed without conflicts.
- SHOWN: the canonical SMA, EMA, and Donchian collector parents remained alive
  at PIDs `7795`, `7630`, and `7628`.
- SHOWN: those existing processes still expose their pre-merge June 15 idle
  status; merging source code does not reload persistent Python processes.

What changed:
- Merged the accepted branch into `review-stabilized`.
- Recorded integrated verification and the explicit non-restart boundary.
- Did not alter runtime state, evidence files, process ownership, or campaign
  configuration outside the reviewed source changes.

Why this change:
- The merge makes the accepted fail-closed behavior canonical on the review
  branch while preserving the currently running evidence campaign.
- Deferring process restart avoids introducing a mid-day lifecycle change into
  active campaigns.

Expected outcome:
- New or intentionally restarted collectors use bounded retry and failed
  campaign classification for missing public OHLCV.
- Current collectors continue undisturbed until the next approved restart.

Verification:
- Integrated service, collector, and recovery slice:
  - SHOWN: `54 passed in 0.67s`.
- Integrated monitor and promotion-gate slice:
  - SHOWN: `63 passed in 0.98s`.
- Read-only campaign status:
  - SHOWN: `all_running=true`, `running_count=3`.
- `git diff --check`
  - SHOWN: clean.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: commands ran from the primary checkout at merge `9a6c3e08a`.

Remaining risk:
- HIGH: active collectors have not yet executed the accepted code.
- UNVERIFIED: the first real outage or healthy window after an approved
  collector restart has not occurred.
- SHOWN: June 15's previously written false-completion records remain
  historical and were not rewritten.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: implementation independently reviewed and accepted by
  the human operator on 2026-06-15 and integrated as `9a6c3e08a`.

## 2026-06-15T02:38:01Z - Fail-Closed Collector Rollout

Active role: `GATE`

Objective: load the independently accepted fail-closed OHLCV lifecycle into
the three persistent paper evidence collector processes without overlapping
collectors or altering historical evidence.

What was found:
- SHOWN: canonical SMA, EMA, and Donchian collectors were idle after recording
  their June 15 sessions.
- SHOWN: no strategy-runner, paper-engine, or tick-publisher lock files were
  active in the three campaign state directories.
- SHOWN: existing PIDs `7795`, `7630`, and `7628` still ran the pre-merge
  in-memory code.
- SHOWN: the accepted restore manifest specifies `max_daily_attempts=2` for
  all three campaigns.

What changed:
- Wrote the supported collector stop flag in each isolated `CBP_STATE_DIR`.
- Waited for all three old parents to exit gracefully and clear their PID
  state; no force-kill was used.
- Ran the accepted idempotent restore command once.
- Started replacement collector PIDs `80255`, `80259`, and `80263`.
- Did not edit or remove any order, fill, signal, session, or strategy-evidence
  artifact.

Why this change:
- Persistent Python processes do not load merged source automatically.
- Graceful stop followed by manifest-driven restore preserves the accepted
  single-owner and duplicate-process boundaries.
- Rolling out while all campaigns were idle avoids interrupting a strategy
  window or partial execution path.

Expected outcome:
- The June 16 UTC campaign windows use the fail-closed public-OHLCV lifecycle.
- A missing-data window reports failed, writes critical session evidence, and
  receives at most one same-day retry.
- Healthy windows continue through the existing completion path.

Verification:
- Pre-stop status:
  - SHOWN: all three collectors reported `status=idle`,
    `reason=waiting_for_next_day`.
- Graceful stop:
  - SHOWN: all three collectors reported `status=stopped`,
    `reason=stop_requested`, `pid_alive=false`.
- Restore:
  - `./.venv/bin/python scripts/restore_paper_campaigns.py --restore`
  - SHOWN: `ok=true`, `all_running=true`, `running_count=3`.
- Read-only process inspection:
  - SHOWN: old PIDs were absent.
  - SHOWN: replacement PIDs were parented to PID 1 and each command line
    contained `--max-daily-attempts 2`.
- VERIFIED_ENV: rollout ran from synchronized `review-stabilized` commit
  `1cca3b535`.

Remaining risk:
- HIGH: persistent financial evidence background jobs were restarted.
- UNVERIFIED: the replacement processes have not yet executed their first
  post-rollout UTC campaign window.
- SHOWN: June 15's prior false-completion records remain historical and were
  not rewritten.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: the human operator authorized the stop and restore
  actions on 2026-06-15 after independently accepting implementation
  `9bd30e8bb`.

## 2026-06-15T02:43:22Z - Qualify Signal-Quality Evidence

Active role: `ENGINEER`

Objective: prevent the signal-quality report from treating historical
unqualified signal rows as canonical evidence of whether the paper strategy
identified market moves early enough.

What was found:
- SHOWN: the canonical report loaded `33,377` signal rows and classified five
  scored rows as `100%` false positives.
- SHOWN: `30,053` rows lacked `market_data_source`; `3,174` used
  `unknown_ohlcv`.
- SHOWN: all `16,740` actionable rows came from those two unqualified groups.
- SHOWN: several unqualified rows carried impossible BTC prices such as
  `$120.90` and `$92.40`, producing fourteen price/OHLCV mismatches.
- SHOWN: all `150` correctly stamped `public_ohlcv` rows matched
  `coinbase`, `BTC/USDT`, `1d`, and non-sample mode, but were flat rather than
  actionable.
- SHOWN: the report excluded explicit sample rows but allowed missing and
  mismatched provenance by default.
- SHOWN: short-signal MAE subtracted `1.0` twice, overstating adverse movement
  by 100 percentage points.

What changed:
- Added strict signal provenance qualification to the analytics core.
- Canonical reports now require non-sample `public_ohlcv` evidence matching
  the requested venue, symbol, and timeframe.
- Added report fields for the qualification policy, qualified signal count,
  excluded unqualified count, and exclusion reason counts.
- Added the explicit CLI opt-out `--allow-unqualified-evidence` for historical
  research only.
- Corrected short-signal MAE to use one relative price move.
- Updated synthetic tests to declare the research opt-out and added regression
  coverage for missing source, mismatched source, wrong symbol, the CLI
  opt-out, and short-side MAE.
- Updated the signal-quality plan and script index to document the implemented
  contract.

Why this change:
- Strategy timing decisions must not be based on synthetic-like or
  provenance-unknown records mixed into canonical paper evidence.
- Strict-by-default behavior aligns this report with the accepted promotion
  evidence boundary.
- An explicit research opt-out preserves historical analysis without allowing
  it to masquerade as production-quality evidence.

Expected outcome:
- Canonical signal-quality summaries reflect only matching real public-OHLCV
  evidence.
- Contaminated historical records remain visible through exclusion counts but
  cannot influence hit rate, false-positive rate, capture ratio, MFE, or MAE.
- The current canonical conclusion becomes `insufficient_sample` until the
  campaign emits qualified actionable signals.
- Short-strategy quality reports produce numerically valid adverse-excursion
  metrics.

Verification:
- Focused analytics and CLI tests:
  - `/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -m pytest -q tests/test_signal_quality.py tests/test_run_signal_quality_report.py`
  - SHOWN: `9 passed`.
- Python compilation:
  - SHOWN: analytics core and CLI compiled cleanly.
- CLI help:
  - SHOWN: `--allow-unqualified-evidence` is exposed.
- Canonical read-only report against `.cbp_state`:
  - SHOWN: `150` qualified records, `33,227` excluded unqualified records,
    `0` qualified actionable signals, and `interpretation=insufficient_sample`.
- Explicit research opt-out:
  - SHOWN: reproduces the historical `16,740` actionable rows, five scored
    false positives, and fourteen price mismatches.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: implementation used isolated worktree
  `/private/tmp/crypto-bot-pro-signal-quality` based on synchronized commit
  `27dbac57e`; active collectors were not modified or restarted.

Remaining risk:
- MEDIUM: this changes decision-support analytics and persisted report content,
  but does not change promotion gates, strategy signals, execution, or
  background-job behavior.
- UNVERIFIED: no qualified actionable public-OHLCV signal exists yet, so timing
  performance remains unknown.
- SHOWN: EMA and Donchian challenger evidence directories currently contain no
  signal records, so their timing reports remain insufficient-sample.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-15 before integration as `e5decec32`.

## 2026-06-15T12:17Z - Accept Signal Quality And Capture VPS Plan

Active role: `GATE`

Objective: integrate the independently accepted signal-quality qualification
change and record the safe role of a Hetzner VPS in the paper campaign.

What was found:
- SHOWN: the human operator independently reviewed and accepted
  `a2b1930eb`.
- SHOWN: all three collectors are alive and idle after completing their
  pre-rollout June 15 UTC windows.
- SHOWN: the replacement collectors have not executed their first corrected
  UTC window; that is scheduled for June 16 UTC.
- SHOWN: the promotion gate remains at zero provenance-qualified round trips
  because nine legacy JSONL fills lack required provenance and the single
  qualified fill does not complete a qualified round trip.
- SHOWN: EMA and Donchian campaigns use isolated state directories and do not
  advance the canonical `es_daily_trend_v1` gate.
- SHOWN: the existing Docker Compose file publishes backend and dashboard ports
  on all interfaces.
- SHOWN: `docs/safety/auth_scope_and_mfa.md` states that remote/public
  deployment is not hardened by default.

What changed:
- Integrated accepted commit `a2b1930eb` into `review-stabilized` as
  `e5decec32`.
- Added a planned Hetzner paper-host task to the next-actions checkpoint.
- Scoped the VPS plan to outbound-only paper collectors, private
  administration, single-owner campaign lifecycle, verified state migration,
  backups, restore rehearsal, and health monitoring.
- Did not restart, migrate, or modify any active collector or evidence
  artifact.

Why this change:
- Strict signal-quality provenance prevents unqualified historical records from
  influencing strategy timing decisions.
- A stable VPS addresses laptop uptime and recovery interruptions.
- Deferring migration until a corrected local UTC cycle is observed avoids
  combining a new collector lifecycle with a new host at the same time.
- Prohibiting public application ports respects the repo's current
  local/private-only security posture.

Expected outcome:
- Canonical signal-quality reports remain provenance-qualified.
- The June 16 UTC windows provide the first evidence of the accepted
  fail-closed lifecycle.
- A later reviewed Hetzner deployment can improve campaign continuity without
  changing strategy semantics or evidence qualification.

Verification:
- Targeted signal-quality tests:
  - SHOWN on the accepted implementation branch: `9 passed`.
- Collector status:
  - SHOWN: canonical PID `80255`, EMA PID `80259`, and Donchian PID `80263`
    report `pid_alive=true`, `status=idle`, and
    `reason=waiting_for_next_day`.
- Promotion gate:
  - SHOWN: `41/30` days and `0/10` provenance-qualified round trips.
- Git integration:
  - SHOWN: cherry-pick completed without conflict as `e5decec32`.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: local repo and all three campaign state directories were read
  directly on 2026-06-15.

Remaining risk:
- HIGH: any VPS deployment would change background-job ownership, remote-host
  security, state custody, and recovery behavior.
- UNVERIFIED: the corrected collectors have not yet completed their June 16
  UTC windows.
- Acceptance state: `ACCEPTED` for signal-quality integration; Hetzner
  deployment remains planning-only and requires a separate high-risk review.
- Acceptance reference: human operator message
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` on 2026-06-15.

## 2026-06-15T12:30Z - Prepare Hetzner Paper-Only Deployment Proof

Active role: `ENGINEER`

Objective: make a future Hetzner paper-campaign proof explicit and reviewable
without provisioning a host or disturbing current collectors.

What was found:
- SHOWN: the campaign manifest uses repo-relative state paths and is portable
  to a checked-out repo.
- SHOWN: the existing recovery command can select a custom manifest and starts
  only collectors that are not alive within that host's state.
- SHOWN: the default manifest enables desktop notifications, which is not
  appropriate for a headless Linux proof.
- SHOWN: the existing Docker Compose stack exposes backend and dashboard ports
  on all interfaces and does not define the paper collectors.
- SHOWN: remote/public app hardening remains outside the accepted deployment
  posture.

What changed:
- Added `docs/HETZNER_PAPER_HOST.md`.
- Added `configs/paper_evidence_campaigns.hetzner.example.json`.
- The example enables only the isolated EMA challenger and disables desktop
  notification.
- Added a focused manifest regression test that also proves the generated
  restore command includes `--no-desktop-notify`.
- Documented host preparation, single-owner stop/copy/checksum/start,
  observation, canonical migration prerequisites, monitoring, backup, and
  rollback.
- Explicitly left automatic boot restoration outside the approved proof.
- Did not access Hetzner, add credentials, expose ports, or change running
  collectors.

Why this change:
- An isolated challenger is the smallest safe deployment proof.
- Single-owner transfer prevents duplicate collectors and divergent evidence.
- Content verification and rollback are required before moving financial
  evidence state between hosts.
- Avoiding the existing Compose stack prevents accidental public exposure of
  surfaces that are not remotely hardened.

Expected outcome:
- A reviewer can evaluate the full VPS proof before any host action.
- The first server proof can improve uptime without changing canonical evidence
  or trading behavior.
- Canonical migration remains blocked until the isolated challenger proves
  uptime, provenance, restart recovery, monitoring, and backup restore.

Verification:
- Targeted recovery and manifest tests:
  - `./.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - SHOWN: `16 passed`.
- Read-only custom-manifest status:
  - SHOWN: the example resolved exactly one campaign,
    `ema_cross_default`, with `all_running=true` against the existing local
    isolated state; no restore action was invoked.
- Diff validation:
  - SHOWN: `git diff --check` passed.
- Full suite will not be run at the operator's direction.
- VERIFIED_ENV: files were prepared on synchronized `review-stabilized`; active
  collectors and runtime state were not modified.

Remaining risk:
- HIGH: the artifacts govern future background-job deployment, state custody,
  remote-host security, and rollback.
- UNVERIFIED: no Hetzner host, firewall, SSH, backup, NTP, restart, or alerting
  configuration has been exercised.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-15 before integration as `dec0b19b5`.

## 2026-06-15T12:45Z - Prepare Secure Hetzner Read-Only Access

Active role: `ENGINEER`

Objective: provide repeatable Hetzner project inventory access without placing
an API token in chat, Git, command arguments, environment files, or output.

What was found:
- SHOWN: the previously posted API token must be treated as compromised and is
  not safe to use.
- SHOWN: the local Python environment uses the macOS Keychain keyring backend.
- SHOWN: `hcloud` is not installed, while Python, Keychain, and HTTPS support
  are available.
- SHOWN: Hetzner tokens can be created with `Read` or `Read & Write`
  permission; project inventory requires only read operations.

What changed:
- Added an OS-keyring-only Hetzner token store.
- Added an interactive hidden-prompt token setter/status/deleter that accepts no
  token command-line argument.
- Added a read-only Hetzner project inventory adapter and operator command.
- The adapter issues only GET requests and returns resource counts plus
  non-secret server summaries.
- Sanitized network and HTTP errors so credentials cannot appear in output.
- Added focused tests and operator documentation.

Why this change:
- A persistent read-only token limits the capability available during planning.
- Reading the credential inside the Python process avoids exposing it through
  shell history or process arguments.
- Separating future short-lived write access prevents routine inventory tooling
  from retaining provisioning authority.

Expected outcome:
- After the operator stores a replacement read-only token through the hidden
  prompt, Codex can inspect the Hetzner project without receiving the token in
  conversation.
- Account inventory is visible without changing any Hetzner resource.

Verification:
- Targeted access and script-bootstrap tests:
  - `./.venv/bin/python -m pytest -q tests/test_hetzner_access.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `20 passed`.
- Script-path validation:
  - SHOWN: `OK: script paths validated`.
- Python compilation:
  - SHOWN: the token store, API adapter, and both commands compiled cleanly.
- Local keyring status:
  - SHOWN: `present=false`; no Hetzner token is currently configured.
- Fail-closed inventory command:
  - SHOWN: returned `hetzner_token_not_configured` without making a live
    request.
- Diff validation:
  - SHOWN: `git diff --check` passed.
- A live account request remains blocked until the compromised token is revoked
  and a replacement read-only token is stored.
- Full suite will not be run at the operator's direction.
- VERIFIED_ENV: macOS Keychain backend detected locally.

Remaining risk:
- HIGH: API credential handling and remote cloud-account access.
- UNVERIFIED: replacement token revocation scope, project selection, and live
  API access.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-15 before integration as `7b01eab71`.

## 2026-06-15T13:05Z - Correct Hetzner TLS Trust Path

Active role: `ENGINEER`

Objective: make the accepted read-only Hetzner client work with certificate
verification in the current Python environment without requiring an operator
environment override.

What was found:
- SHOWN: Keychain token storage succeeded.
- SHOWN: `curl` reached `api.hetzner.cloud` with a valid certificate and
  received the expected unauthenticated `401`.
- SHOWN: Python failed before authentication with
  `SSLCertVerificationError: unable to get local issuer certificate`.
- SHOWN: Python's configured framework CA path does not exist.
- SHOWN: the pinned venv dependency `certifi==2026.2.25` provides a valid CA
  bundle.
- SHOWN: setting `SSL_CERT_FILE` to that bundle allowed the approved GET-only
  inventory to succeed.

What changed:
- Added an explicit default SSL context sourced from `certifi.where()`.
- Passed that context to each Hetzner HTTPS request.
- Kept hostname checking enabled and verification mode at `CERT_REQUIRED`.
- Added regression assertions for the verified SSL context.

Why this change:
- The client should not depend on a missing machine-global Python CA file.
- Using the pinned CA bundle preserves TLS verification; disabling verification
  or suppressing hostname checks would be unsafe.

Expected outcome:
- `scripts/hetzner_account_status.py` works without `SSL_CERT_FILE`.
- Token secrecy, GET-only behavior, pagination, and sanitized errors remain
  unchanged.

Verification:
- Targeted access and script-bootstrap tests:
  - `./.venv/bin/python -m pytest -q tests/test_hetzner_access.py tests/test_bootstrap_helper_adoption.py tests/test_no_duplicate_script_bootstrap.py`
  - SHOWN: `20 passed`.
- Script-path validation:
  - SHOWN: `OK: script paths validated`.
- Python compilation:
  - SHOWN: the corrected Hetzner adapter compiled cleanly.
- Diff validation:
  - SHOWN: `git diff --check` passed.
- Live GET-only inventory without `SSL_CERT_FILE`:
  - SHOWN: `ok=true`; one running server, zero firewalls, two primary IPs,
    one SSH key, zero networks, and zero volumes.
- Full suite will not be run at the operator's direction.
- VERIFIED_ENV: local Python 3.12 venv on macOS.

Remaining risk:
- HIGH: TLS behavior protects cloud-account credentials and API responses.
- UNVERIFIED: behavior on the future Ubuntu host until its venv is built.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-16 before integration as `9fc8a3ff1`.

## 2026-06-17T01:49:51Z - Hetzner Host-Level Hardening Proof

Active role: `ENGINEER`

Objective: prepare the existing Hetzner server for future paper-only campaign
proofs without copying campaign state or starting any remote collectors.

What was found:
- SHOWN: local `review-stabilized` was clean before the host work.
- SHOWN: all three local paper collectors were healthy and idle with
  `last_completed_day=2026-06-17`.
- SHOWN: Hetzner read-only inventory reported one running server:
  `ubuntu-4gb-nbg1-3`, type `cax11`, location `nbg1`.
- SHOWN: the host baseline had UFW inactive, SSH password authentication
  enabled, `fail2ban` inactive, no `cryptkeep` user, and no `/srv/cryptkeep`.
- SHOWN: the local RSA public key matched the registered Hetzner SSH key
  fingerprint, and root key-based SSH worked before hardening.

What changed on the Hetzner host:
- Created non-root user `cryptkeep` with home `/srv/cryptkeep`.
- Created `/srv/cryptkeep/app`, `/srv/cryptkeep/state`, and
  `/srv/cryptkeep/backups`.
- Installed the operator's public key for the `cryptkeep` user.
- Added `/etc/ssh/sshd_config.d/60-cryptkeep-hardening.conf`.
- Disabled SSH password authentication and keyboard-interactive
  authentication.
- Kept root login key-only with `PermitRootLogin prohibit-password`.
- Reduced `MaxAuthTries` from `6` to `3`.
- Enabled UFW with default deny incoming, default allow outgoing, and OpenSSH
  allowed.
- Installed and enabled `fail2ban` with an `sshd` jail.
- Wrote `/etc/cryptkeep_host_hardening.json` as a host-side marker.

What did not change:
- No Git repository was cloned to the server.
- No `.cbp_state` or challenger state was copied.
- No paper collector, dashboard, backend, or trading process was started on
  the server.
- No Hetzner Cloud firewall, backup, primary IP, server protection, or other
  cloud-side resource was changed; the token remains read-only.
- No local collector was stopped, restarted, or migrated.

Why this change:
- The VPS improves future evidence continuity only if it is a single-owner,
  private, paper-only host.
- Hardening the host before deploying collectors prevents exposing the repo's
  non-remote-hardened dashboard/backend surfaces and reduces SSH attack
  surface.
- Keeping the campaign local preserves canonical evidence while the server
  hardening proof awaits review.

Expected outcome:
- The server can support an isolated challenger proof after independent review.
- Root recovery access remains available by key, while day-to-day access can
  use the non-root `cryptkeep` account.
- The host exposes only SSH and has basic local firewall and SSH brute-force
  controls.

Verification:
- Root SSH verification:
  - SHOWN: root key access still works.
- Non-root SSH verification:
  - SHOWN: `cryptkeep` login works and can write under
    `/srv/cryptkeep/state`.
- SSH effective settings:
  - SHOWN: `passwordauthentication no`,
    `kbdinteractiveauthentication no`, `pubkeyauthentication yes`,
    `permitrootlogin without-password`, and `maxauthtries 3`.
- UFW:
  - SHOWN: `Status: active`, default deny incoming, default allow outgoing,
    OpenSSH allowed for IPv4 and IPv6.
- Fail2ban:
  - SHOWN: service active; `sshd` jail active and already banning three scanner
    IPs.
- Listeners:
  - SHOWN: public listeners are SSH only.
- Hetzner inventory:
  - SHOWN: read-only inventory still reports `firewalls=0`, `servers=1`, and
    `volumes=0`.
- Local campaign status:
  - SHOWN: all three local collectors remained healthy and idle after the host
    work.
- Full suite was not run at the operator's direction.
- VERIFIED_ENV: host commands ran on `ubuntu-4gb-nbg1-3` over SSH using the
  matched local RSA key.

Remaining risk:
- HIGH: server security, background job deployment readiness, and future state
  custody.
- UNVERIFIED: Hetzner Cloud firewall, backups, delete/rebuild protection, host
  backup/restore rehearsal, and server-hosted UTC campaign execution.
- SHOWN: Ubuntu reports `40` packages not upgraded after installing `fail2ban`.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-17T01:59:15Z - Hetzner Cloud safeguard planner

Active role: ENGINEER

Objective:
- Add a guarded, reviewed path for Hetzner Cloud safeguards now that a
  write-capable token is available.

What was found:
- SHOWN: the host is hardened locally, but cloud-side safeguards remain open:
  Hetzner firewall, backups, and delete/rebuild protection.
- SHOWN: the previous inventory path was read-only and could not express a
  safe write workflow.
- SHOWN: the keyring account label remains `hetzner_cloud:readonly`, but the
  operator may temporarily store a read/write token there for accepted
  provisioning.

What changed:
- Added cloud safeguard planning/apply functions in `services/ops/hetzner_cloud.py`.
- Added `scripts/hetzner_cloud_safeguards.py`.
- Added tests for missing SSH CIDR, broad CIDR rejection, dry-run planning,
  confirmation mismatch, guarded POST sequencing, and firewall rule drift
  correction.
- Updated `docs/HETZNER_PAPER_HOST.md` with the dry-run/apply workflow and
  safety gates.
- Updated `scripts/SCRIPTS.md` so the new root script is visible as a
  specialized cloud-provisioning command.

Why this change:
- A read/write cloud token is high risk unless the repo encodes the safety
  workflow directly.
- The smallest safe path is plan-by-default, explicit SSH source CIDR, exact
  server-id confirmation for writes, and no token printed or accepted as a
  command argument.
- The firewall helper corrects an existing named firewall if its SSH rule
  source drifts, rather than trusting the firewall name alone.

Expected outcome:
- Operators can see exactly what Hetzner Cloud changes would be made before any
  write.
- Applying cloud safeguards requires deliberate confirmation and a restrictive
  SSH source.
- The paper host can progress toward cloud-side hardening after independent
  review, without starting or migrating any collector.

Verification:
- SHOWN: `./.venv/bin/python -m py_compile services/ops/hetzner_cloud.py scripts/hetzner_cloud_safeguards.py`
  passed.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_hetzner_access.py`
  passed with `14 passed in 0.61s`.
- SHOWN: `./.venv/bin/python scripts/validate_script_paths.py` returned
  `OK: script paths validated`.
- SHOWN: `git diff --check` passed.
- SHOWN: live-safe CLI proof
  `./.venv/bin/python scripts/hetzner_cloud_safeguards.py --server-id 126306158`
  returned `ok=false`, `reason=ssh_source_cidr_required`, and no planned
  changes. This path stops before any Hetzner API request by test proof.
- Full suite was not run at the operator's direction.

Remaining risk:
- HIGH: cloud-provider write operations, firewall lockout risk, backup billing,
  and server protection policy.
- UNVERIFIED: no live Hetzner Cloud write has been performed by this change.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-17 after
  independent review sign-off.

## 2026-06-18T02:45:10Z - Derivatives and intraday roadmap backlog capture

Active role: ENGINEER

Objective:
- Add the reviewed futures, crypto-perpetuals, day-trading, and candlestick
  recommendations to the tracked task list without changing runtime behavior.

What was found:
- SHOWN: `services/strategies/strategy_registry.py` supports
  `pullback_recovery`, `volatility_reversal`, `gap_fill`, and
  `breakout_volume` in the active OHLCV strategy registry.
- SHOWN: `services/backtest/leaderboard.py` does not include
  `pullback_recovery` in the default aggregate leaderboard candidates.
- SHOWN: `services/strategies/funding_extreme.py`,
  `services/strategies/open_interest_shift.py`, and
  `services/strategies/order_book_imbalance.py` exist as context-signal
  modules but are not part of the active OHLCV registry path.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still describes
  BTC/USDT as a crypto proxy until an ES/SPY futures connector exists.

What changed:
- Added Priority 17 to
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`.
- Captured crypto perpetual futures as a research/testnet-only derivatives
  workstream requiring compliance, funding-rate accounting, leverage controls,
  margin tracking, reduce-only exits, and liquidation-risk controls before any
  execution adapter work.
- Captured Bybit as out of scope unless a later compliance review proves the
  operator can legally use it.
- Captured traditional ES/NQ futures as a later broker/FCM workstream.
- Captured intraday/day-trading context and candlestick confirmation as
  read-only evidence first, not order-routing behavior.

Why this change:
- The backlog already had short-market and pattern-roadmap items, but it did
  not explicitly preserve the reviewed sequencing for derivatives, intraday
  context data, venue compliance, and candlestick confirmation.
- Planning documentation is the smallest safe change because derivatives,
  shorting, leverage, and margin are high-risk financial-control surfaces.

Expected outcome:
- Future work can proceed from a visible tracked roadmap instead of relying on
  chat memory.
- The current paper campaigns remain isolated while the next capability layer
  is researched in read-only mode first.
- Any future derivatives or short-side implementation is forced through
  explicit compliance, data-provenance, risk-control, and independent-review
  gates.

Verification:
- SHOWN: `git diff --check` passed.
- Tests not run; this is a documentation-only backlog update.

Remaining risk:
- HIGH: future derivatives execution, shorting, leverage, margin, liquidation
  risk, and strategy-selection behavior.
- UNVERIFIED: no exchange-account eligibility or legal/compliance review has
  been performed by this documentation update.
- Acceptance state: `ACCEPTED` for documentation capture only; any
  implementation must stop at `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-18T03:01:55Z - Pullback recovery leaderboard wiring

Active role: ENGINEER

Objective:
- Add `pullback_recovery` to aggregate leaderboard/evidence evaluation as the
  first low-infrastructure pattern strategy expansion.

What was found:
- SHOWN: `pullback_recovery` was present in
  `services/strategies/strategy_registry.py`.
- SHOWN: `pullback_recovery` was absent from
  `services/backtest/leaderboard.py` default candidates.
- SHOWN: `services/strategies/presets.py` had no
  `pullback_recovery_default` preset.
- SHOWN: `services/strategies/validation.py` rejected `pullback_recovery` even
  though config tools and the registry already supported it.

What changed:
- Added `pullback_recovery_default` in `services/strategies/presets.py`.
- Added `pullback_recovery_default` to
  `services/backtest/leaderboard.py` default strategy candidates.
- Added typed `pullback_recovery` parameter support in
  `services/strategies/config_tools.py`.
- Added `pullback_recovery` validation in
  `services/strategies/validation.py`.
- Updated leaderboard and config-tool tests for the new preset and candidate
  count.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`.

Why this change:
- The backlog called for adding `pullback_recovery` to leaderboard/evidence
  evaluation before adding new candlestick or derivatives strategies.
- The smallest coherent implementation needed the preset, default leaderboard
  candidate, typed config handling, and validator support together; otherwise
  the strategy would remain partially wired.
- No campaign startup, runtime order routing, or paper evidence state was
  changed.

Expected outcome:
- Future strategy evidence cycles can rank `pullback_recovery` alongside the
  existing OHLCV strategy candidates.
- Operators can build and validate a typed `pullback_recovery` strategy block.
- The next safe step remains a separate paper-only `pullback_recovery` campaign
  plan with baseline, turnover expectation, risk cap, and evidence gate.

Verification:
- SHOWN: `./.venv/bin/python -m py_compile services/strategies/presets.py services/backtest/leaderboard.py services/strategies/config_tools.py services/strategies/validation.py`
  passed.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_backtest_leaderboard.py tests/test_strategy_config_tools.py tests/test_strategy_registry.py`
  passed with `24 passed in 0.51s`.
- SHOWN: `./.venv/bin/python -m ruff check services/strategies/presets.py services/backtest/leaderboard.py services/strategies/config_tools.py services/strategies/validation.py tests/test_backtest_leaderboard.py tests/test_strategy_config_tools.py`
  passed.
- SHOWN: `git diff --check` passed.
- Full suite was not run at the operator's direction.

Remaining risk:
- HIGH: strategy-selection and leaderboard/evidence behavior can affect future
  promotion decisions.
- UNVERIFIED: no live/paper campaign has been started for `pullback_recovery`
  by this change.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-18 after
  independent review sign-off.

## 2026-06-18T03:17:05Z - Docs-only CI fast path

Active role: ENGINEER

Objective:
- Reduce unnecessary PR wait time for documentation-only changes without
  weakening full CI coverage for code, strategy, workflow, risk, or execution
  changes.

What was found:
- SHOWN: recent integration PRs spent most of their wait time in required
  `CI validate` and `CI sanity` jobs even when changes were documentation-only.
- SHOWN: `docs/GITHUB_BRANCH_PROTECTION.md` requires stable check names on
  every pull request, so workflow-level path filters could leave required
  checks pending.
- SHOWN: code and strategy changes still need the full remote gate path.

What changed:
- Added an internal docs-only classifier to `.github/workflows/ci.yml`.
- Added the same internal docs-only classifier to
  `.github/workflows/ci-sanity.yml`.
- Added the same internal docs-only classifier to
  `.github/workflows/ci-pyinstaller.yml`.
- For docs-only PRs, the required checks keep their existing names and pass
  through a visible fast-pass step instead of installing dependencies, running
  full tests, or building desktop wrappers.
- Updated `docs/CI_GITHUB_ACTIONS.md` and
  `docs/GITHUB_BRANCH_PROTECTION.md` to document the policy.

Why this change:
- The smallest safe improvement is to keep required workflow names stable and
  fast-pass internally for docs-only changes.
- A broader bypass or path-filter change would either weaken code coverage or
  risk branch-protection hangs.

Expected outcome:
- Docs-only PRs should complete required CI materially faster.
- Any source, script, config, workflow, test, strategy, execution, risk, or
  packaging change still takes the full CI path.
- Branch protection remains compatible because the required check names are not
  removed or skipped at the workflow level.

Verification:
- SHOWN: YAML parser check passed for `.github/workflows/ci.yml`,
  `.github/workflows/ci-sanity.yml`, and `.github/workflows/ci-pyinstaller.yml`.
- SHOWN: local classifier simulation returned `docs_case=true`.
- SHOWN: local classifier simulation returned `code_case=false`.
- SHOWN: `git diff --check` passed.
- Full suite was not run because this is a workflow-policy change and the
  meaningful proof is GitHub Actions behavior after PR creation.

Remaining risk:
- HIGH: CI/branch-protection policy can affect merge safety.
- UNVERIFIED: GitHub Actions has not yet run these workflow changes on a PR.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-18 after
  independent review sign-off.

## 2026-06-19T01:26:30Z - Paper Gate Provenance Window Reporting

Active role: ENGINEER

Objective:
- Make the paper promotion gate explain when provenance-clean fill counting
  began and which historical fill dates remain diagnostic-only.

What was found:
- SHOWN: `scripts/check_promotion_gates.py --json` reported 8 all-history
  closed trades but only 1 provenance-qualified round trip for
  `es_daily_trend_v1`.
- SHOWN: older JSONL fills on 2026-04-20, 2026-05-15, and 2026-05-18 lacked
  the required market-data provenance fields.
- SHOWN: the existing evidence model deliberately keeps unqualified persisted
  history visible under `paper_history.all_history` while excluding it from
  promotion thresholds.

What changed:
- Added first/latest provenance-qualified fill timestamps and first/latest
  completed qualified round-trip close timestamps to the shared paper evidence
  qualification payload.
- Added unqualified fill date counts to the shared qualification payload.
- Surfaced the qualified fill window and unqualified fill dates in
  `check_promotion_gates.py` round-trip detail.
- Surfaced the same diagnostics in `paper_promotion_progress`.
- Updated `docs/EVIDENCE_MODEL.md` to document that these fields are
  diagnostic reporting and do not retroactively qualify historical records.
- Cleaned existing style issues in `scripts/check_promotion_gates.py` that
  blocked targeted Ruff verification for this touched file.

Why this change:
- Retroactively counting missing-provenance fills would weaken the promotion
  gate and contradict the accepted evidence model.
- The smallest useful change is to make the gate's exclusion logic explicit so
  operators can see why the counter is not advancing from all-history trades.

Expected outcome:
- Operators can distinguish all-history trade count from promotion-qualified
  trade count without manually inspecting JSONL files.
- Future check-ins should show the clean evidence window and the excluded
  historical dates directly in gate/progress output.
- Promotion thresholds remain unchanged.

Verification:
- SHOWN: `./.venv/bin/python -m py_compile services/control/paper_evidence_qualification.py scripts/check_promotion_gates.py services/control/paper_promotion_progress.py`
  passed.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  passed with `44 passed in 0.89s`.
- SHOWN: `./.venv/bin/python -m ruff check services/control/paper_evidence_qualification.py scripts/check_promotion_gates.py services/control/paper_promotion_progress.py tests/test_check_promotion_gates.py tests/test_paper_promotion_progress.py`
  passed.
- SHOWN: `git diff --check` passed.
- SHOWN: live `run_check(stage_override="paper")` round-trip detail now reports
  the qualified fill window `2026-05-26T00:00:09.788947+00:00` to
  `2026-06-18T00:04:00.986914+00:00` and unqualified fill dates
  `2026-04-20:6`, `2026-05-15:2`, `2026-05-18:1`.
- Full suite was not run at the operator's direction.

Remaining risk:
- MEDIUM: promotion gate reporting changed, but threshold logic and
  qualification rules were not changed.
- SHOWN: remote PR checks had passed for macOS build, Windows build,
  Governance smoke, CI sanity, GitGuardian, and script-path-integrity at
  acceptance time; CI validate was still pending.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-18 after
  independent review sign-off.

## 2026-06-19T01:50:21Z - Refresh Hetzner Paper Host Status

Active role: ENGINEER

Objective:
- Align the Hetzner paper-host documentation and checkpoint with the current
  verified state before any remote campaign deployment work.

What was found:
- SHOWN: `scripts/set_hetzner_api_token.py --status` reported a token present
  in OS keyring under account `hetzner_cloud:readonly` without printing the
  secret.
- SHOWN: `scripts/hetzner_account_status.py` performed read-only inventory and
  reported one running server: `ubuntu-4gb-nbg1-3`, `id=126306158`, `cax11`,
  `nbg1`.
- SHOWN: read-only inventory reported `firewalls=0`, `ssh_keys=1`,
  `primary_ips=2`, `networks=0`, and `volumes=0`.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` already exists and is the controlling
  paper-only deployment runbook, so creating a duplicate runbook would create a
  source-of-truth problem.

What changed:
- Updated `docs/HETZNER_PAPER_HOST.md` with the refreshed read-only inventory
  timestamp and resource counts.
- Updated Priority 16 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to reflect
  that the runbook is accepted while cloud safeguards and campaign deployment
  remain blocked pending independent review and a narrow operator/VPN SSH CIDR.

Why this change:
- The highest-leverage safe action is to prevent duplicate planning and make
  the remaining blocker explicit.
- Applying Hetzner Cloud safeguards or moving collectors would be high-risk and
  requires an explicit SSH source CIDR plus independent review.

Expected outcome:
- Future check-ins should not rediscover or rewrite the Hetzner runbook.
- The next actionable Hetzner step is explicit: obtain a narrow SSH source CIDR,
  review the safeguard path, then run a dry plan before any `--apply`.
- Active paper campaigns remain owned by the laptop.

Verification:
- SHOWN: `./.venv/bin/python scripts/set_hetzner_api_token.py --status`
  returned `ok=true`, `present=true`, `stored_in=os_keyring`.
- SHOWN: `./.venv/bin/python scripts/hetzner_account_status.py` returned
  `ok=true` with read-only project inventory.
- SHOWN: `git diff --check` passed.
- SHOWN: targeted `rg` confirmed the updated runbook/checkpoint/work-log
  surfaces contain `firewalls=0`, `operator/VPN SSH source CIDR`, and
  `READY_FOR_INDEPENDENT_REVIEW` blocker language.
- Tests were not run because this is a documentation-only status update.

Remaining risk:
- HIGH: Hetzner Cloud safeguard application, remote host operations, and
  campaign state migration remain high-risk.
- UNVERIFIED: no Hetzner Cloud firewall, backup, protection, host backup
  rehearsal, isolated server-hosted UTC cycle, or canonical migration was
  performed by this change.
- SHOWN: remote PR #60 checks passed for macOS build, Windows build,
  CI sanity, CI validate, GitGuardian, and Governance smoke.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-18 after
  independent review sign-off.

## 2026-06-19T02:02:23Z - Record Stale Open PR Disposition Audit

Active role: AUDITOR

Objective:
- Reassess stale open PRs after `review-stabilized` and `master` were realigned,
  then preserve the disposition in the visible task list before any branch is
  closed, merged, or rebuilt.

What was found:
- SHOWN: PR #42 remains a draft branch targeting `master`, with merge state
  `DIRTY`.
- SHOWN: `origin/master...origin/codex/runtime-hardening-ai-alert-monitor`
  reports `224 / 27`.
- SHOWN: PR #43 is not draft, targets `master`, and has merge state `DIRTY`.
- SHOWN: `origin/master...origin/fix/p1-pre-live` reports `224 / 98`.
- SHOWN: PR #3 is not draft, targets `master`, and has merge state `DIRTY`.
- SHOWN: `origin/master...origin/cleanup/import-collection-failures` reports
  `283 / 54`.
- SHOWN: PR #42's branch-only commits are a subset of the broader PR #43
  runtime/monitoring history.
- SHOWN: PR #3 was not represented in the active next-actions checkpoint even
  though it remains open and dirty against `master`.

What changed:
- Updated `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` so
  PR #42 and PR #43 no longer say their current state is unverified.
- Marked PR #42 as superseded by the broader PR #43 extraction task rather than
  merge-ready.
- Marked PR #43 as requiring focused rebuilds from current `master` rather than
  direct merge.
- Added Priority 18 for PR #3 cleanup/disposition, including the requirement
  for a commit-by-commit disposition table before closure or rebuild.

Why this change:
- The old branches touch high-risk runtime, execution, auth/dashboard,
  reconciliation, and background-job surfaces.
- Directly merging dirty, month-old aggregate branches would bypass the focused
  review model established by the accepted audit cycle.
- Closing the PRs without first preserving unique work would risk losing valid
  safety fixes.

Expected outcome:
- Future cleanup work has an explicit path: extract useful content into clean,
  focused PRs or close stale PRs only after documented supersession.
- Operators should not mistake PR #42, PR #43, or PR #3 for merge-ready work.

Verification:
- SHOWN: `gh pr list --state open --json ...` returned PR #43, PR #42, and
  PR #3 as the only open PRs; all three target `master` and report
  `mergeStateStatus=DIRTY`.
- SHOWN: `gh pr view 43 --json ...` returned `mergeStateStatus=DIRTY` and the
  branch file list includes high-risk runtime/execution surfaces.
- SHOWN: local `git rev-list --left-right --count` comparisons produced the
  branch divergence counts listed above.
- SHOWN: local `git log --right-only --cherry-pick --no-merges` comparisons
  produced branch-only commit summaries for all three PR heads.
- Tests were not run because this is a documentation-only audit update.

Remaining risk:
- MEDIUM/HIGH: this change records disposition only. It does not close PRs,
  rebuild unique features, or validate any branch-only implementation.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T02:09:37Z - Draft PR #3 Cleanup Disposition

Active role: AUDITOR

Objective:
- Convert stale PR #3 from an ambiguous dirty open PR into an explicit
  commit-disposition artifact before any closure or rebuild decision.

What was found:
- SHOWN: PR #3 is open, targets `master`, is not draft, and reports
  `mergeStateStatus=DIRTY`.
- SHOWN: `origin/master...origin/cleanup/import-collection-failures` reports
  `283 / 54`.
- SHOWN: the branch-only history has 52 non-merge commits and 2 merge commits.
- SHOWN: PR #3 touches high-risk surfaces including live reconciliation,
  execution consumers, intent queues, paper engine, and storage.
- SHOWN: current `master` already contains related surfaces including
  `services/execution/intent_lifecycle.py`, `scripts/run_paper_scenario.py`,
  `tests/test_execution_claim_race.py`,
  `tests/test_live_intent_queue_integrity.py`, and
  `tests/test_paper_queue_authority.py`.

What changed:
- Added `docs/checkpoints/pr3_cleanup_disposition_2026_06_19.md`.
- Updated Priority 18 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to point to
  the disposition table and require independent review before PR #3 closure.

Why this change:
- Directly merging PR #3 would import stale high-risk execution behavior from a
  dirty branch.
- Closing PR #3 without a disposition table could lose valid safety fixes.
- A commit-by-commit table creates a safe path: close stale branch noise after
  acceptance, then rebuild only still-valid safety fixes from current `master`.

Expected outcome:
- PR #3 can be closed after independent acceptance of the disposition artifact.
- Future implementation work should be split by rebuild group rather than
  cherry-picked from the old aggregate branch.

Verification:
- SHOWN: `git log --right-only --cherry-pick --no-merges --reverse
  --name-status origin/master...origin/cleanup/import-collection-failures`
  listed 52 non-merge branch-only commits and touched files.
- SHOWN: `git log --right-only --cherry-pick --merges --reverse
  origin/master...origin/cleanup/import-collection-failures` listed 2 merge
  commits.
- SHOWN: targeted `rg --files tests` confirmed related current-master test
  surfaces exist.
- SHOWN: targeted `rg` confirmed current-master execution lifecycle,
  paper-scenario, phase1 skip, `INSERT OR IGNORE`, and `atomic_risk_claim`
  surfaces exist.
- Tests were not run because this is an audit/documentation-only change.

Remaining risk:
- HIGH: this audit does not prove behavior equivalence between PR #3 and
  current `master`; rebuilt execution work still requires targeted tests and
  independent review.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T02:17:25Z - Close PR #3 After Accepted Disposition

Active role: GATE

Objective:
- Complete the accepted PR #3 disposition path by merging the disposition
  artifact, closing stale PR #3, and recording the final state.

What was found:
- SHOWN: PR #62 was accepted by human operator review and its checks passed.
- SHOWN: PR #62 merged to `master` as `7e8fb6155`.
- SHOWN: `review-stabilized` was fast-forwarded to `origin/master` and pushed.
- SHOWN: PR #3 was still open after PR #62 merged.

What changed:
- Added PR #3 comments linking the accepted disposition checkpoint and PR #62.
- Closed PR #3 without merging it.
- Updated Priority 18 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to mark the
  PR #3 cleanup/disposition task complete.

Why this change:
- The accepted disposition says PR #3 must not be merged directly and should be
  closed after preserving its branch-only commit decisions.
- Keeping PR #3 open after accepted disposition would recreate stale backlog
  noise and make it look like an active merge candidate.

Expected outcome:
- PR #3 is no longer open backlog.
- Remaining useful PR #3 content must be rebuilt from current `master` using
  the accepted disposition groups.

Verification:
- SHOWN: `gh pr view 3 --json number,state,closed,url,title` returned
  `state=CLOSED`, `closed=true`.
- SHOWN: `gh pr list --state open --json ...` returned only PR #42 and PR #43.
- SHOWN: `origin/master...origin/review-stabilized` reported `0 / 0`.
- SHOWN: `restore_paper_campaigns.py --status` earlier in this gate cycle
  reported all three paper campaigns running and idle for the next UTC day.
- Tests were not run because this is a PR/disposition documentation update.

Remaining risk:
- HIGH: branch closure does not validate any old PR #3 execution fix. Any
  still-needed fix must be rebuilt from current `master` with targeted tests
  and independent review.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  accepted disposition.

## 2026-06-19T16:49:44Z - Draft PR #43 Operator Observability Disposition

Active role: AUDITOR

Objective:
- Convert stale PR #43 from a dirty aggregate runtime branch into an explicit
  rebuild/supersession/drop plan before closure or implementation.

What was found:
- SHOWN: PR #43 is open, targets `master`, is not draft, and reports
  `mergeStateStatus=DIRTY`.
- SHOWN: PR #42 is still open, draft, dirty, and its branch-only commits are a
  subset of the broader PR #43 history.
- SHOWN: `origin/master...origin/fix/p1-pre-live` reports `232 / 98`.
- SHOWN: `git cherry -v origin/master origin/fix/p1-pre-live` shows 96
  patch-unique commits and 2 patch-equivalent commits already represented on
  `master`.
- SHOWN: patch-unique PR #43 history contains 95 non-merge commits and 1 merge
  commit.
- SHOWN: current `master` has `scripts/run_paper_sim_monitor.py` and
  `services/analytics/paper_sim_monitor.py`.
- SHOWN: current `master` does not have `scripts/run_ai_alert_monitor.py`,
  `scripts/run_ai_oversight_watch.py`,
  `services/ai_copilot/alert_monitor.py`,
  `services/ai_copilot/oversight_watch.py`,
  `services/runtime/managed_symbol_config.py`, or
  `services/runtime/managed_symbol_selection.py`.

What changed:
- Added
  `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  with a 98-row disposition table.
- Updated Priority 8 to mark PR #42 as superseded by the PR #43 disposition
  path, pending independent review.
- Updated Priority 9 to link the PR #43 disposition and make direct merge
  explicitly unacceptable.

Why this change:
- PR #43 mixes useful operator observability ideas with high-risk runtime,
  dashboard, live-guard/auth, evidence, and campaign behavior.
- Direct merge would reintroduce stale branch history into the canonical line.
- The useful work should be rebuilt as focused current-master PRs: AI operator
  alerting, safe runtime wrappers, managed multi-symbol paper runtime, and
  supervised soak reporting.

Expected outcome:
- After independent acceptance, PR #43 and superseded PR #42 can be closed with
  comments linking the disposition checkpoint.
- Future implementation should rebuild only the commits marked `rebuild`.

Verification:
- SHOWN: `git rev-list --left-right --count origin/master...origin/fix/p1-pre-live`
  returned `232 / 98`.
- SHOWN: `git rev-list --right-only --cherry-pick --no-merges --count
  origin/master...origin/fix/p1-pre-live` returned `95`.
- SHOWN: `git rev-list --right-only --cherry-pick --merges --count
  origin/master...origin/fix/p1-pre-live` returned `1`.
- SHOWN: `rg -c '^\\| `' against the new disposition document returned `98`.
- SHOWN: targeted file existence checks confirmed current paper-monitor files
  exist and old PR #43 AI alert/oversight/managed-symbol files are absent.
- SHOWN: `git diff --check` passed.
- Tests were not run because this is an audit/documentation-only change.

Remaining risk:
- HIGH: this audit does not prove behavior equivalence between PR #43 and
  current `master`; rebuilt runtime/monitoring work still requires targeted
  tests and independent review.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T17:01:53Z - Close PR #43 And Superseded PR #42

Active role: GATE

Objective:
- Complete the accepted PR #43 disposition path by merging the disposition
  artifact, closing stale PR #43, closing superseded PR #42, and recording the
  final state.

What was found:
- SHOWN: PR #64 was accepted by human operator review and all GitHub checks
  passed.
- SHOWN: PR #64 merged to `master` as `a4539d37b`.
- SHOWN: `review-stabilized` was fast-forwarded to `origin/master` and pushed.
- SHOWN: PR #43 and PR #42 were still open after PR #64 merged.

What changed:
- Added a PR #43 comment linking the accepted disposition checkpoint and PR #64.
- Closed PR #43 without merging it.
- Added a PR #42 comment marking it superseded by the accepted PR #43
  disposition.
- Closed PR #42 without merging it.
- Updated Priorities 8 and 9 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to mark both
  stale PR tasks complete.

Why this change:
- The accepted disposition says PR #43 must not be merged directly and PR #42
  is superseded by PR #43's broader disposition path.
- Keeping either PR open after accepted disposition would leave stale backlog
  noise and make them look like active merge candidates.

Expected outcome:
- There are no open stale PRs.
- Future implementation work should rebuild only the accepted PR #43
  `rebuild` groups from current `master`.

Verification:
- SHOWN: `gh pr view 43 --json number,state,closed,url,title` returned
  `state=CLOSED`, `closed=true`.
- SHOWN: `gh pr view 42 --json number,state,closed,url,title` returned
  `state=CLOSED`, `closed=true`.
- SHOWN: `gh pr list --state open --json ...` returned `[]`.
- Tests were not run because this is a PR/disposition documentation update.

Remaining risk:
- HIGH: branch closure does not validate any old PR #43/#42 runtime or
  monitoring implementation. Any still-needed feature must be rebuilt from
  current `master` with targeted tests and independent review where high risk.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  accepted disposition.

## 2026-06-19T17:09:24Z - Add Supervised Soak Status Report

Active role: ENGINEER

Objective:
- Rebuild the accepted PR #43 supervised-soak reporting idea from current
  `review-stabilized` without reusing the stale branch or changing campaign
  control behavior.

What was found:
- SHOWN: `restore_paper_campaigns.py --status` and the accepted campaign
  recovery API already provide campaign process status without restoring or
  starting collectors when `restore=False`.
- SHOWN: `scripts.check_promotion_gates.run_check()` already returns the paper
  gate payload needed for operator review.
- SHOWN: current local campaign state has three configured campaigns running
  and idle until the next UTC day: `es_daily_trend_v1`, `ema_cross_default`,
  and `breakout_default`.
- SHOWN: the paper gate currently reports 1 qualified round trip against 10
  required, with 8 all-history diagnostic round trips and provenance filtering
  explaining the difference.

What changed:
- Added `scripts/report_supervised_soak_status.py`, a read-only operator report
  that combines supervised paper-campaign status with paper promotion gate
  status.
- Added `tests/test_report_supervised_soak_status.py` covering read-only API
  use, JSON output, strict exit behavior, recommendation generation, and gate
  summarization.
- Updated `scripts/SCRIPTS.md` so the new command is visible in the canonical
  operator script index.

Why this change:
- The smallest useful rebuild from the stale PR #43 scope is an observational
  report, not another control loop.
- This gives the operator one command for campaign and gate state while avoiding
  high-risk process supervision, live execution, auth, or order-routing changes.

Expected outcome:
- Operators can run one read-only command to see whether supervised paper
  campaigns are alive and why the paper promotion gate is or is not ready.
- Gate confusion around all-history versus qualified provenance round trips is
  surfaced directly in the report output.

Verification:
- SHOWN: `./.venv/bin/python -m py_compile scripts/report_supervised_soak_status.py tests/test_report_supervised_soak_status.py` passed before final lint cleanup.
- SHOWN: `./.venv/bin/python -m ruff check scripts/report_supervised_soak_status.py tests/test_report_supervised_soak_status.py` returned `All checks passed!`.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_report_supervised_soak_status.py tests/test_restore_paper_campaigns.py` returned `6 passed in 0.17s`.
- SHOWN: `./.venv/bin/python scripts/report_supervised_soak_status.py --json` returned `ok=true`, `all_running=true`, `campaign_count=3`, `running_count=3`, and the current paper gate details.
- SHOWN: `git diff --check` passed.
- Full suite was not run because the user explicitly asked to stop running
  full tests for these incremental changes.

Remaining risk:
- MEDIUM: this is operator-reporting code that reads live local state, but it
  does not start, stop, restore, route, or place anything.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T17:52:46Z - Draft Pullback Recovery Paper Campaign Plan

Active role: ENGINEER

Objective:
- Convert the accepted pattern-strategy backlog item into a concrete
  paper-only `pullback_recovery_default` campaign plan without changing active
  campaign configuration or runtime behavior.

What was found:
- SHOWN: `pullback_recovery` exists in
  `services/strategies/pullback_recovery.py`.
- SHOWN: `pullback_recovery_default` exists in
  `services/strategies/presets.py`.
- SHOWN: `services/strategies/validation.py` supports `pullback_recovery`
  parameter validation.
- SHOWN: `services/backtest/leaderboard.py` includes
  `pullback_recovery_default` in default aggregate candidates.
- SHOWN: `configs/paper_evidence_campaigns.json` currently has only the three
  accepted campaigns: `es_daily_trend_v1`, `ema_cross_default`, and
  `breakout_default`.

What changed:
- Added
  `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md`.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to point to
  the drafted plan and make independent review the next step.

Why this change:
- Planning the isolated proof is the smallest safe step before starting another
  strategy campaign.
- It preserves current paper evidence collection while giving the pattern
  strategy path explicit state isolation, evidence gates, risk caps, and stop
  conditions.

Expected outcome:
- A reviewer can decide whether to accept a Stage 0 one-shot proof for
  `pullback_recovery_default`.
- No active paper campaign, gate, manifest, order-routing path, or live-control
  surface changes because of this documentation-only step.

Verification:
- SHOWN: source inspection verified the strategy, preset, validation, and
  leaderboard hooks referenced by the plan.
- Tests were not run because this is a documentation-only planning change.

Remaining risk:
- HIGH: any future campaign activation, strategy evidence interpretation, or
  financial strategy selection remains high-risk and must be separately
  reviewed.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T18:19:38Z - Fix Pullback Recovery Paper Attribution

Active role: ENGINEER

Objective:
- Run the accepted Stage 0 isolated `pullback_recovery_default` proof and fix
  the attribution defect it exposed without changing active campaign manifests
  or canonical paper-gate policy.

What was found:
- SHOWN: the accepted Stage 0 one-shot run completed with
  `strategy=pullback_recovery`, no fills, and no canonical `sma_200_trend`
  count change.
- SHOWN: that run reported `strategy_preset=ema_cross_default`, even though
  the session evidence wrote under `pullback_recovery_default`.
- SHOWN: `--status` then searched
  `data/evidence/pullback_recovery` and reported `jsonl_evidence.exists=false`
  while the actual session artifact existed under
  `data/evidence/pullback_recovery_default`.
- SHOWN: `pullback_recovery` was missing from the collector default
  session-strategy map and from the strategy runner alias/default-preset map.

What changed:
- Added `pullback_recovery -> pullback_recovery_default` to
  `scripts/run_paper_strategy_evidence_collector.py`.
- Added `pullback`/`pullback_recovery` aliases and
  `pullback_recovery_default` default preset mapping to
  `services/strategy_runner/ema_crossover_runner.py`.
- Added pullback recovery legacy parameter forwarding and required-history
  calculation in the strategy runner.
- Added targeted tests proving default session strategy ID and runner preset
  attribution for pullback recovery.
- Cleaned the touched collector bootstrap import ordering and removed duplicate
  `sma_200_trend` dictionary keys that ruff surfaced in the touched runner.

Why this change:
- The Stage 0 proof cannot be accepted while runtime status attributes the
  strategy to `ema_cross_default`; monitor, JSONL summary, and future campaign
  accounting would point at the wrong evidence surface.
- Mapping the strategy to its existing preset is the smallest coherent fix and
  avoids changing strategy logic, order routing, gates, or active campaign
  configuration.

Expected outcome:
- Future `pullback_recovery` paper runs report
  `strategy_preset=pullback_recovery_default`.
- Runtime status and JSONL evidence summaries look under the same
  `pullback_recovery_default` evidence directory used by session logging.
- The accepted Stage 0 proof can be rerun for review without contaminating
  canonical `es_daily_trend_v1` promotion evidence.

Verification:
- SHOWN: the initial accepted Stage 0 command completed with
  `status=completed`, `strategy=pullback_recovery`, no fills, and
  `strategy_preset=ema_cross_default`, exposing the defect.
- SHOWN: post-run canonical `.cbp_state/data/trade_journal.sqlite` counts kept
  `sma_200_trend` at `16` fills, `8` buys, and `8` sells.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_run_paper_strategy_evidence_collector.py` returned `38 passed in 0.82s`.
- SHOWN: `./.venv/bin/python -m ruff check scripts/run_paper_strategy_evidence_collector.py services/strategy_runner/ema_crossover_runner.py tests/test_strategy_runtime_runner.py tests/test_run_paper_strategy_evidence_collector.py` returned `All checks passed!`.
- SHOWN: a short isolated fix-check using
  `CBP_STATE_DIR=.cbp_state_challengers/pullback_recovery_default_fixcheck`
  completed with `strategy_preset=pullback_recovery_default` and
  `jsonl_evidence.exists=true`.
- SHOWN: `git diff --check` passed.
- Full suite was not run because the operator requested targeted checks instead
  of broad full-suite runs for incremental changes.

Remaining risk:
- HIGH: this touches paper evidence attribution and strategy runner selection
  for a financial strategy path. The implementation must be independently
  reviewed before acceptance.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after
  independent review sign-off.

## 2026-06-19T18:35:28Z - Refresh Pullback Recovery Campaign Status

Active role: ENGINEER

Objective:
- Align the pullback recovery campaign plan and next-actions backlog with the
  accepted PR #68 state without running another long Stage 0 command.

What was found:
- SHOWN: PR #68 was accepted and merged to `master` as `6d02f2d3`.
- SHOWN: `review-stabilized` and `master` were aligned after the merge.
- SHOWN: `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md`
  still said no isolated pullback campaign had been started, which was stale
  after the pre-fix Stage 0 run.
- SHOWN: Priority 13 still described the pullback plan as pending independent
  review, which was stale after PR #67 and PR #68 were accepted and merged.

What changed:
- Updated the pullback recovery campaign plan to record the completed pre-fix
  Stage 0 run, the attribution defect it exposed, the accepted PR #68 fix, and
  the pending full post-fix Stage 0 rerun.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to state the
  current next action: operator-run full post-fix Stage 0 proof, no persistent
  daily campaign yet.

Why this change:
- The docs should not imply the plan is still pending review or that no
  isolated pullback run happened.
- Keeping the long 900-second proof as an operator-run command respects the
  operator instruction not to run time-heavy commands automatically.

Expected outcome:
- Future check-ins see the correct pullback state immediately: plan accepted,
  attribution fixed, full post-fix Stage 0 proof still pending.
- No runtime, campaign manifest, order-routing, or gate behavior changes.

Verification:
- SHOWN: source docs were inspected before editing.
- SHOWN: `git diff --check` passed.
- Tests were not run because this is a documentation-only status correction.

Remaining risk:
- LOW: documentation status can still become stale after the operator runs the
  full post-fix Stage 0 proof.
- Acceptance state: `ACCEPTED`.

## 2026-06-19T18:40:27Z - Draft Short-Market Strategy Research Spec

Active role: ENGINEER

Objective:
- Capture the short-market strategy workstream as a separate research spec
  before any implementation, configuration, execution, or gate change.

What was found:
- SHOWN: `docs/strategies/es_daily_trend_v1.md` defines the current target
  strategy as long/flat only.
- SHOWN: Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` already
  called for a short-side research spec before implementation.
- SHOWN: the infrastructure activation audit classifies `funding_extreme`,
  `open_interest_shift`, and `order_book_imbalance` as research-only or unsafe
  to enable without data-plumbing and risk proof.
- SHOWN: repo modules exist for funding, open-interest, order-book, and
  liquidation-context scaffolding, but they are not the active campaign
  authority.
- UNVERIFIED: venue eligibility, compliance constraints, account permissions,
  margin/borrow support, derivatives access, and strategy profitability.

What changed:
- Added
  `docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md`.
- Updated Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to point to
  the new spec and require independent review before implementation.

Why this change:
- Short-side work changes tail risk, margin, liquidation, funding/borrow costs,
  compliance assumptions, and failure modes. It needs a separate research path
  instead of being treated as an extension of the current long/flat paper
  campaign.
- A docs-first spec prevents accidental activation of short, derivatives,
  leverage, or margin behavior while preserving a concrete next audit target.

Expected outcome:
- Future short-side work starts with read-only data-quality and replay evidence
  before any paper simulation or execution path.
- The active long/flat campaigns remain untouched.
- The next engineer/auditor has explicit stop conditions for missing venue,
  compliance, funding, borrow, liquidation, reduce-only, and provenance proof.

Verification:
- SHOWN: existing backlog and infrastructure audit docs were inspected.
- SHOWN: repo references to short-side, funding, open-interest, liquidation, and
  derivatives scaffolding were searched before writing the spec.
- Tests not run: documentation-only planning change, with no source, config,
  runtime, gate, or campaign behavior modified.

Remaining risk:
- HIGH: future short-side implementation would affect financial strategy logic,
  derivatives/margin assumptions, risk controls, and potential order routing.
  This change is planning-only and must be independently reviewed before it is
  used as implementation authority.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-19T18:44:46Z - Audit Short Context Data Feasibility

Active role: ENGINEER

Objective:
- Convert the accepted short-market research spec's next action into a
  read-only feasibility audit of the existing funding, open-interest,
  liquidation, and order-book context surfaces.

What was found:
- SHOWN: `services/analytics/crypto_edge_collector.py` is the safest existing
  collector path because it returns `research_only=True` and
  `execution_enabled=False`.
- SHOWN: the collector and store currently cover funding, basis, and quotes,
  not open interest, liquidation, or order-book-depth/imbalance rows.
- SHOWN: `services/market_data/market_intelligence.py` has open-interest
  collection and liquidation scaffolding, but silently skips some failures and
  marks scaffold liquidation output under an `ok=True` wrapper.
- SHOWN: `services/market_data/order_book_intelligence.py` computes imbalance
  and spread/depth fields, but failed symbols are omitted instead of preserved
  as checks.
- SHOWN: `funding_extreme` and `open_interest_shift` exist in presets/config
  support, but the active `strategy_registry.py` does not route those context
  modules.
- UNVERIFIED: venue eligibility, account permissions, compliance assumptions,
  data stability, and profitability for any short/context strategy.

What changed:
- Added
  `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`.
- Updated Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to reference
  the audit and define the smallest next implementation as read-only collector
  and storage extension.

Why this change:
- The short-market research spec called for a read-only feasibility audit before
  implementation.
- The repo already has multiple overlapping context-data surfaces; the audit
  selects the safer base and documents why the other surfaces are not yet
  replay-authoritative.

Expected outcome:
- Future short/context work starts by extending read-only data collection and
  storage, not by routing context signals into paper or live execution.
- Missing funding, open-interest, liquidation, spread, or depth data must be
  explicit instead of silently treated as neutral.

Verification:
- SHOWN: inspected context strategy modules, presets/config support, active
  strategy registry, crypto-edge collector, market-intelligence scaffolding,
  order-book intelligence, collector scripts, sample plans, storage, and tests.
- Tests not run: documentation-only audit change with no source, config,
  runtime, gate, or campaign behavior modified.

Remaining risk:
- HIGH: future implementation would expand research inputs for financial
  strategy selection and may later affect short-side replay or paper
  simulation. This audit is documentation-only and must be independently
  reviewed before implementation authority.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-19T18:52:13Z - Extend Read-Only Crypto Edge Context Rows

Active role: ENGINEER

Objective:
- Implement the smallest accepted short-context data step: add read-only
  open-interest and order-book row support to the existing crypto-edge
  collector/store/report path.

What was found:
- SHOWN: the existing crypto-edge collector was already research-only and
  returned `execution_enabled=False`.
- SHOWN: existing storage/reporting covered funding, basis, and quotes but not
  open interest or order-book depth/imbalance rows.
- SHOWN: the existing live collection script persisted only funding, basis, and
  quote rows.
- SHOWN: bundled sample data did not include open-interest or order-book rows.

What changed:
- Added open-interest and order-book summaries to
  `services/analytics/crypto_edges.py`.
- Added `open_interest_snapshots` and `order_book_snapshots` tables plus append
  and latest-report accessors in `storage/crypto_edge_store_sqlite.py`.
- Extended `services/analytics/crypto_edge_collector.py` to collect
  `open_interest` and `order_books` plan rows with per-symbol checks.
- Extended `scripts/collect_live_crypto_edge_snapshot.py`,
  `scripts/record_crypto_edge_snapshot.py`, and
  `scripts/load_sample_crypto_edge_data.py` to persist the new row families.
- Added bundled `sample_data/crypto_edges/open_interest.json` and
  `sample_data/crypto_edges/order_books.json`, and updated the live collector
  plan.
- Updated targeted tests and research docs.

Why this change:
- The feasibility audit identified the existing crypto-edge collector as the
  safest read-only base for future short/context research.
- Adding data rows and storage is lower risk than adding signal replay or
  strategy routing, and it keeps short-side work blocked from execution.

Expected outcome:
- The repo can collect and persist read-only open-interest and order-book
  context rows for later replay analysis.
- Missing/unsupported open-interest and order-book fetches are surfaced through
  checks instead of silently treated as neutral.
- No active paper campaign, strategy registry, promotion gate, credential, or
  execution behavior changes.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_crypto_edge_analytics.py tests/test_crypto_edge_collector.py tests/test_collect_live_crypto_edge_snapshot.py tests/test_record_crypto_edge_snapshot.py tests/test_load_sample_crypto_edge_data.py`
  returned `15 passed in 0.48s`.
- SHOWN: changed-file ruff check returned `All checks passed!`.
- SHOWN: `git diff --check` passed.
- Full suite intentionally not run unless requested because the operator
  instructed Codex not to run time-heavy commands automatically.

Remaining risk:
- HIGH: this expands research inputs that may later influence financial
  strategy replay and short-side paper simulation. Implementation must be
  separately reviewed before any replay, paper-simulation, or execution use.
- Acceptance state: `ACCEPTED` by human operator review on 2026-06-19 after PR
  #72 checks passed and the merge landed on `master` as `977ea9c3`.

## 2026-06-19T19:06:35Z - Record Crypto Edge Context Sample Proof

Active role: ENGINEER

Objective:
- Record the accepted PR #72 state and run the isolated read-only sample proof
  requested by Priority 12 before any replay use of the new rows.

What was found:
- SHOWN: PR #72 merged to `master` at `977ea9c3`.
- SHOWN: local `review-stabilized` and `origin/master` were aligned after the
  merge.
- SHOWN: Priority 12 still described the collector/store implementation as
  pending review, which was stale after operator acceptance and merge.

What changed:
- Updated Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to record
  accepted/merged status and isolated sample proof completion.
- Updated the prior work-log entry's acceptance state from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED` with the human operator review
  and merge reference.

Why this change:
- The visible backlog and work log should match the accepted GitHub state.
- The sample proof shows the new row families are persisted and surfaced in a
  read-only report before any replay work starts.

Expected outcome:
- Future short/context work starts from an accurate state: collector/store
  extension accepted, isolated sample proof complete, public-data proof still
  optional and not yet accepted.
- No replay, strategy routing, paper execution, promotion gate, or campaign
  behavior is implied by this proof.

Verification:
- SHOWN: `./.venv/bin/python scripts/load_sample_crypto_edge_data.py --db-path /private/tmp/cbp_crypto_edge_context_sample_proof_20260619.sqlite --print-report`
  returned `ok=true`.
- SHOWN: sample proof reported `funding_count=3`, `open_interest_count=2`,
  `basis_count=3`, `quote_count=6`, and `order_book_count=2`.
- SHOWN: report flags remained `research_only=true` and
  `execution_enabled=false`.
- Tests not run: documentation-only status/proof update after accepted PR #72.

Remaining risk:
- HIGH: public-data collection, replay analysis, paper short simulation, and
  any short-side execution remain separate future workstreams requiring
  separate proof and review.
- Acceptance state: `ACCEPTED`.

## 2026-06-19T19:10:58Z - Record Crypto Edge Live-Public Partial Proof

Active role: ENGINEER

Objective:
- Run and record the bounded read-only public-data collection proof for the
  accepted crypto-edge context collector/store extension without using
  canonical state or execution credentials.

What was found:
- SHOWN: the public-data proof completed against
  `/private/tmp/cbp_crypto_edge_context_live_public_proof_20260619.sqlite`.
- SHOWN: the output retained `research_only=true` and
  `execution_enabled=false`.
- SHOWN: Coinbase/Kraken quote collection worked with `quote_count=2`.
- SHOWN: Coinbase order-book collection worked with `order_book_count=1`.
- SHOWN: Binance funding, open-interest, and basis checks failed at exchange
  open with `exchange_open_failed:RuntimeError`.
- SHOWN: `services/security/binance_guard.py` intentionally blocks Binance
  unless `CBP_VENUE` starts with `binance` and `CBP_ALLOW_BINANCE=1`.

What changed:
- Updated Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to record
  the partial live-public proof and the Binance guard condition.

Why this change:
- The public-data proof is materially different from the deterministic sample
  proof: spot quote/order-book context is proven, but derivatives context is
  still not proven under default guard settings.
- Future operators should not mistake missing Binance rows for a connector
  success or for venue/compliance approval.

Expected outcome:
- Replay work can use deterministic sample data or the proven live quote/order
  book row families, but funding/open-interest/basis replay still needs a
  separate accepted Binance guard-enabled proof.
- The Binance guard remains intact; this documentation does not authorize
  derivatives execution or any short-side routing.

Verification:
- SHOWN: `./.venv/bin/python scripts/collect_live_crypto_edge_snapshot.py --plan-file sample_data/crypto_edges/live_collector_plan.json --db-path /private/tmp/cbp_crypto_edge_context_live_public_proof_20260619.sqlite --print-report`
  returned `ok=true`.
- SHOWN: output reported `quote_count=2`, `order_book_count=1`,
  `research_only=true`, and `execution_enabled=false`.
- SHOWN: source inspection confirmed Binance access is guard-blocked by
  `services/security/binance_guard.py` unless explicit environment settings
  allow it.
- Tests not run: documentation-only status/proof update.

Remaining risk:
- HIGH: funding, open-interest, basis, derivatives context, replay analysis,
  paper short simulation, and short-side execution remain separate future
  workstreams requiring separate proof and review.
- Acceptance state: `ACCEPTED`.

## 2026-06-19T19:14:25Z - Record Binance Guard-Enabled Proof Block

Active role: ENGINEER

Objective:
- Attempt the bounded guard-enabled Binance-only read-only public-data proof for
  derivatives context rows without using canonical state or execution
  credentials.

What was found:
- SHOWN: the mixed live collector plan cannot be reused with
  `CBP_VENUE=binance` because the exchange factory treats explicit non-Binance
  venues plus env `binance` as a venue conflict.
- SHOWN: a temporary Binance-only plan was written to
  `/private/tmp/cbp_crypto_edge_binance_only_plan_20260619.json`.
- SHOWN: the guarded command used `CBP_VENUE=binance` and
  `CBP_ALLOW_BINANCE=1`, so the repo-level Binance guard was intentionally
  cleared for this read-only proof.
- SHOWN: the command returned `ok=false` with `reason=no_live_rows_collected`.
- SHOWN: funding, open-interest, and basis checks all failed with
  `exchange_open_failed:NetworkError`.
- SHOWN: output still reported `research_only=true` and
  `execution_enabled=false`.

What changed:
- Updated Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to record
  that Binance derivatives context remains blocked by exchange-open
  `NetworkError` even after guard enablement.

Why this change:
- The derivatives-context path should not be treated as proven. The guard block
  and the network/exchange-open block are distinct failure modes, and the
  second one remains unresolved.

Expected outcome:
- Future replay work may use deterministic sample rows or accepted spot
  quote/order-book public rows.
- Funding, open-interest, and basis rows remain unproven against live public
  Binance data until the `NetworkError` is resolved or an alternate compliant
  read-only derivatives venue is accepted.

Verification:
- SHOWN: `CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/collect_live_crypto_edge_snapshot.py --plan-file /private/tmp/cbp_crypto_edge_binance_only_plan_20260619.json --db-path /private/tmp/cbp_crypto_edge_context_binance_guard_proof_20260619.sqlite --print-report`
  returned exit code `1` with `reason=no_live_rows_collected`.
- SHOWN: checks contained `exchange_open_failed:NetworkError` for funding,
  open interest, and basis.
- Tests not run: documentation-only status/proof update.

Remaining risk:
- HIGH: derivatives data, funding, open interest, basis, replay analysis, paper
  short simulation, and short-side execution remain separate future workstreams
  requiring separate proof and review.
- Acceptance state: `ACCEPTED`.

## 2026-06-20T02:05:58Z - Apply Hetzner Tailscale-Only Firewall

Active role: ENGINEER

Objective:
- Close the Hetzner public-SSH exposure gap for the paper campaign host while
  preserving operator access over Tailscale SSH.

What was found:
- SHOWN: `tailscale status` showed the operator laptop `macbook-pro`
  (`100.76.178.88`) and the Hetzner host `ubuntu-4gb-nbg1-3`
  (`100.86.128.9`) in the same tailnet.
- SHOWN: `tailscale ssh cryptkeep@100.86.128.9 hostname` returned
  `ubuntu-4gb-nbg1-3`.
- SHOWN: plain `ssh cryptkeep@100.86.128.9` is not the supported operator
  command for this boundary; the accepted operator command is
  `tailscale ssh cryptkeep@100.86.128.9`.

What changed:
- Created and applied a Hetzner Cloud firewall named
  `cryptkeep-tailscale-only` to `ubuntu-4gb-nbg1-3`.
- The firewall has `0 Rules`, is applied to `1 Server`, and the console reports
  `Fully applied`.
- Updated `docs/HETZNER_PAPER_HOST.md` to mark the Tailscale SSH boundary and
  no-public-inbound firewall as accepted and verified.
- Updated Priority 16 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to remove
  the obsolete SSH-CIDR blocker and keep deployment blocked on backup,
  protection, restore, and single-owner proof.
- Marked the older CIDR-based `hetzner_cloud_safeguards.py --apply` path as
  partially superseded for SSH because it does not yet model the accepted
  Tailscale-only firewall boundary.

Why this change:
- A public CIDR allowlist is brittle for a residential operator connection and
  unnecessary once Tailscale SSH is verified.
- A no-public-inbound Hetzner firewall plus Tailscale SSH provides the narrower
  access boundary required before any remote paper-campaign proof.
- The docs needed to prevent a future operator from applying the older
  CIDR-based safeguard path and unintentionally weakening the accepted
  Tailscale-only boundary.

Expected outcome:
- Operator access to the host uses `tailscale ssh cryptkeep@100.86.128.9`.
- Public SSH to `178.104.145.242:22` is blocked.
- The server remains available for future isolated challenger proof work, but
  canonical state migration and collector startup remain blocked until
  backup/protection/restore/single-owner requirements are satisfied.

Verification:
- SHOWN: Hetzner Cloud Console listed `cryptkeep-tailscale-only` with
  `0 Rules`, `1 Server`, and `Fully applied`.
- SHOWN: `tailscale ssh cryptkeep@100.86.128.9 'hostname && whoami'` returned
  `ubuntu-4gb-nbg1-3` and `cryptkeep`.
- SHOWN: `ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no
  cryptkeep@178.104.145.242 'hostname && whoami'` failed with
  `Operation timed out`.
- Tests not run: documentation-only repo update after a live cloud-console
  firewall operation. No application code changed.

Remaining risk:
- HIGH: remote host security, backup/protection configuration, persistent
  background jobs, state migration, credentials/configuration, and duplicate
  campaign ownership remain separate high-risk workstreams.
- ACCEPTED_WITH_RISK: the live firewall action was explicitly confirmed by the
  operator with `CONFIRM FIREWALL` and verified after application; follow-on
  deployment work remains blocked until separately reviewed.

## 2026-06-20T02:37:12Z - Add Tailscale-Only Hetzner Safeguard Mode

Active role: ENGINEER

Objective:
- Make the Hetzner safeguard planner/apply path match the accepted
  Tailscale-only SSH boundary without applying any additional live cloud
  changes.

What was found:
- SHOWN: `services/ops/hetzner_cloud.py` still modeled only the older
  CIDR-based firewall named `cryptkeep-paper-ssh-only`.
- SHOWN: `scripts/hetzner_cloud_safeguards.py` still required
  `--ssh-source-cidr`, which is wrong for the accepted no-public-inbound
  Tailscale boundary.
- SHOWN: the runbook had marked the command partially superseded after the
  manual firewall application.

What changed:
- Added `ACCESS_MODE_TAILSCALE_ONLY` to the Hetzner cloud safeguard service.
- Added `--access-mode tailscale-only` to
  `scripts/hetzner_cloud_safeguards.py`.
- In Tailscale-only mode, the planner creates/corrects
  `cryptkeep-tailscale-only` with zero firewall rules, attaches it to the
  selected server, and keeps backup plus delete/rebuild protection checks in
  the same guarded plan.
- Tailscale-only mode rejects `--ssh-source-cidr` so a public SSH allowlist
  cannot be mixed into the accepted private-network boundary.
- Kept the old CIDR mode for compatibility.
- Updated `docs/HETZNER_PAPER_HOST.md`, Priority 16, and `scripts/SCRIPTS.md`
  with the new operator command and review boundary.

Why this change:
- The accepted host access model changed from public SSH with CIDR allowlist to
  Tailscale SSH with no public inbound rules.
- Leaving the safeguard command in CIDR-only form would keep backups and
  server protection blocked behind an obsolete SSH model.
- The smallest coherent fix is a mode switch rather than deleting the old path.

Expected outcome:
- Operators can dry-run the accepted host safeguard plan with:
  `./.venv/bin/python scripts/hetzner_cloud_safeguards.py --server-id 126306158 --access-mode tailscale-only`
- After independent review, the same command can be applied with
  `--apply --confirm-server-id 126306158` to enable missing backups/protection
  without reopening public SSH.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_hetzner_access.py`
  returned `18 passed`.
- SHOWN: `./.venv/bin/python -m py_compile services/ops/hetzner_cloud.py scripts/hetzner_cloud_safeguards.py tests/test_hetzner_access.py`
  completed with exit code `0`.
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: read-only live dry-run
  `./.venv/bin/python scripts/hetzner_cloud_safeguards.py --server-id 126306158 --access-mode tailscale-only`
  returned `ok=true`, `ready_to_apply=true`,
  `tailscale_only_firewall_rules_current`, and
  `tailscale_only_firewall_attached`.
- SHOWN: the live dry-run reported only `enable_delete_rebuild_protection` and
  `enable_backups` as remaining changes.
- No live Hetzner `--apply` command was run.

Remaining risk:
- HIGH: cloud-provider write operations, firewall lockout risk, backup billing,
  server protection changes, and deployment operations remain high-risk.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-20T02:51:31Z - Apply Hetzner Backups And Server Protection

Active role: ENGINEER

Objective:
- Apply the independently reviewed Tailscale-only Hetzner safeguard path to
  enable backups and delete/rebuild protection without changing the accepted
  no-public-inbound SSH boundary.

What was found:
- SHOWN: the read-only safeguard plan reported
  `tailscale_only_firewall_rules_current` and
  `tailscale_only_firewall_attached`.
- SHOWN: the only planned live changes were
  `enable_delete_rebuild_protection` and `enable_backups`.

What changed:
- Ran the accepted live apply command:
  `./.venv/bin/python scripts/hetzner_cloud_safeguards.py --server-id 126306158 --access-mode tailscale-only --apply --confirm-server-id 126306158`.
- Hetzner returned `ok=true` and `applied_count=2`.
- Applied action ids:
  - `enable_delete_rebuild_protection`: `637459053005493`
  - `enable_backups`: `637459053005498`
- Updated `docs/HETZNER_PAPER_HOST.md` and Priority 16 to remove backups and
  delete/rebuild protection from the active blocker list.

Why this change:
- The host had the correct Tailscale-only network boundary but still lacked
  provider-side backup and deletion/rebuild protection.
- Those controls are required before any server-hosted campaign proof or state
  migration.

Expected outcome:
- Accidental server deletion or rebuild is blocked by provider-side protection.
- Hetzner backups are enabled with backup window `10-14`.
- The remaining deployment blockers are now restore rehearsal, server-hosted
  isolated challenger cycle, and single-owner campaign proof.

Verification:
- SHOWN: post-apply read-only plan returned `ok=true`, `changes_needed=[]`,
  `delete_rebuild_protection_enabled`, and `backups_enabled`.
- SHOWN: post-apply plan reported `backup_window="10-14"` and
  `protection.delete=true`, `protection.rebuild=true`.
- SHOWN: `tailscale ssh cryptkeep@100.86.128.9 'hostname && whoami'` returned
  `ubuntu-4gb-nbg1-3` and `cryptkeep`.
- SHOWN: public SSH to `178.104.145.242:22` still failed with
  `Operation timed out`.

Remaining risk:
- HIGH: backup restore has not been rehearsed, no server-hosted collector cycle
  has completed, and canonical state migration remains blocked.
- ACCEPTED_WITH_RISK: live cloud-provider writes were explicitly approved by
  operator escalation and verified after application.

## 2026-06-20T02:58:18Z - Add Paper State Manifest Tool

Active role: ENGINEER

Objective:
- Replace OS-specific manual checksum commands in the Hetzner isolated
  challenger transfer path with a deterministic repo-native manifest tool.

What was found:
- SHOWN: `docs/HETZNER_PAPER_HOST.md` used macOS `shasum` on the laptop and
  Linux `sha256sum` on Hetzner, then told the operator to normalize output
  manually.
- SHOWN: the repo had `restore_paper_campaigns.py` for process recovery, but no
  dedicated paper-state manifest create/verify command for transfer integrity.

What changed:
- Added `scripts/paper_state_manifest.py`.
- The command supports:
  - `create --state-dir ... --output ...`
  - `verify --state-dir ... --manifest ...`
- Manifest paths are deterministic POSIX-relative paths sorted by path.
- The tool rejects manifest output inside the state directory, manifest path
  escapes, invalid digests, duplicate manifest paths, and symlinked state
  files.
- Updated `docs/HETZNER_PAPER_HOST.md` to use the new command for the
  `ema_cross_default` state transfer proof.
- Updated `scripts/SCRIPTS.md` with the new script entry.

Why this change:
- The next Hetzner blocker is isolated challenger proof, and state transfer is
  the highest-risk manual step before starting a remote collector.
- A repo-native manifest reduces operator drift between macOS and Linux and
  makes the proof output machine-readable.

Expected outcome:
- State transfer can be verified with `ok=true`, `missing=[]`, `changed=[]`,
  and `extra=[]` before any Hetzner collector is started.
- Future canonical state migration has a safer reusable integrity primitive,
  though canonical migration remains blocked.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_paper_state_manifest.py tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  returned `21 passed`.
- SHOWN: `./.venv/bin/python -m py_compile scripts/paper_state_manifest.py scripts/restore_paper_campaigns.py services/analytics/paper_campaign_recovery.py tests/test_paper_state_manifest.py`
  completed with exit code `0`.
- SHOWN: `git diff --check` completed with exit code `0`.

Remaining risk:
- HIGH: this supports financial-evidence state migration. It does not start
  collectors, move state, or merge state trees, but it should still receive
  independent review before use in a live migration/proof.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #79 was merged to `master` as `4e0d26b50`.

## 2026-06-20T09:53:08Z - Add Hetzner Paper Host Preflight

Active role: ENGINEER

Objective:
- Add a read-only host readiness check before the accepted Hetzner isolated
  challenger state-transfer and collector-restore path is used.

What was found:
- SHOWN: `docs/HETZNER_PAPER_HOST.md` listed the required host checks as manual
  commands before deployment.
- SHOWN: the next blocker is a server-hosted isolated challenger proof, but
  starting that proof depends on the host being on the accepted checkout, using
  the repo venv, running Tailscale, having synchronized time, and using the
  single-campaign Hetzner config with desktop notifications disabled.
- SHOWN: the repo had a state manifest tool and campaign restore command, but
  no repo-native preflight bundling those readiness checks.

What changed:
- Added `scripts/hetzner_paper_host_preflight.py`.
- The command is read-only and reports JSON.
- It checks:
  - required campaign-transfer scripts and config exist;
  - Python is running from the repo `.venv`;
  - Git checkout is clean and optionally matches an accepted commit prefix;
  - `timedatectl` reports NTP synchronized;
  - `tailscale status --json` reports a running backend and Tailscale IP;
  - the Hetzner campaign config enables exactly `ema_cross_default`, keeps
    `desktop_notify=false`, and optionally requires transferred state to exist.
- Added `tests/test_hetzner_paper_host_preflight.py`.
- Updated `docs/HETZNER_PAPER_HOST.md` to run the preflight before campaign
  deployment and again with `--require-state` after state transfer.
- Updated `scripts/SCRIPTS.md` and the root script count.

Why this change:
- The next operational move crosses background-job and evidence-state risk.
- A read-only preflight reduces manual drift before any collector starts, while
  preserving the existing rule that no campaign is automatically migrated or
  launched.
- This is narrower and safer than starting a server-hosted challenger from this
  thread.

Expected outcome:
- Operators get a single machine-readable `ok=true` readiness gate before
  running the Hetzner isolated challenger restore command.
- Failed Tailscale, NTP, dirty-checkout, wrong-commit, wrong-config, missing
  state, or non-venv conditions are surfaced before a remote paper collector is
  started.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_hetzner_paper_host_preflight.py tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  returned `22 passed`.
- SHOWN: `./.venv/bin/python -m py_compile scripts/hetzner_paper_host_preflight.py tests/test_hetzner_paper_host_preflight.py`
  completed with exit code `0`.
- SHOWN: `./.venv/bin/python -m ruff check scripts/hetzner_paper_host_preflight.py tests/test_hetzner_paper_host_preflight.py`
  returned `All checks passed!`.
- SHOWN: `git diff --check` completed with exit code `0`.

Remaining risk:
- HIGH: this is deployment-adjacent paper-campaign infrastructure. It is
  read-only and does not start collectors, move state, or call Hetzner APIs, but
  it gates a future financial-evidence background job path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #80 was merged to `master` as `c53f413a7`.

## 2026-06-20T10:08:41Z - Add Hetzner Isolated Challenger Proof Template

Active role: ENGINEER

Objective:
- Make the next Hetzner isolated challenger proof auditable before any state
  transfer or remote collector start.

What was found:
- SHOWN: `docs/HETZNER_PAPER_HOST.md` defines the correct single-owner
  sequence, but the command outputs were still expected to be preserved by
  operator discipline rather than a named proof artifact.
- SHOWN: the remaining Hetzner blockers are operational:
  server-hosted isolated challenger cycle, backup/restore rehearsal, and
  single-owner proof.
- SHOWN: starting the challenger from this thread would cross background-job
  and evidence-state risk.

What changed:
- Added
  `docs/deployment_records/hetzner_isolated_challenger_proof_TEMPLATE.md`.
- The template records:
  - accepted deployment commit and host identity;
  - laptop status before stop;
  - laptop stop proof;
  - manifest create and verify proof;
  - transfer proof;
  - Hetzner preflight proof;
  - Hetzner restore/start proof;
  - single-owner proof;
  - first UTC cycle observation;
  - backup restore rehearsal;
  - rollback record and final decision.
- Updated `docs/HETZNER_PAPER_HOST.md` to require the template for Stage 1 and
  acceptance proof.

Why this change:
- The next operational step must not depend on memory or chat context.
- A template creates the audit artifact before the high-risk operation starts,
  without launching collectors, moving state, or touching cloud resources.

Expected outcome:
- The first server-hosted isolated challenger proof can be reviewed from a
  single committed deployment record.
- Future canonical migration remains blocked until that record shows a healthy
  server-hosted UTC cycle, backup rehearsal, and single-owner evidence.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_checkpoints_repo_path_references_exist.py`
  returned `2 passed`.

Remaining risk:
- HIGH: this documents deployment-adjacent financial-evidence operations. It is
  docs-only and does not run commands, but it is still part of the operational
  control path for a future background collector.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #81 was merged to `master` as `b6b274861`.

## 2026-06-20T10:18:00Z - Correct PR80 And PR81 Work Log Acceptance States

Active role: ENGINEER

Objective:
- Correct the governed work log after the accepted PR #80 and PR #81 merges.

What was found:
- SHOWN: PR #80 was independently reviewed and accepted by the human operator,
  then merged to `master` as `c53f413a7`.
- SHOWN: PR #81 was independently reviewed and accepted by the human operator,
  then merged to `master` as `b6b274861`.
- SHOWN: the corresponding work-log entries still ended with
  `READY_FOR_INDEPENDENT_REVIEW`, which no longer matched the repository state.

What changed:
- Updated the Hetzner paper-host preflight entry acceptance state to
  `ACCEPTED` and added the PR #80 merge reference.
- Updated the Hetzner isolated challenger proof-template entry acceptance state
  to `ACCEPTED` and added the PR #81 merge reference.

Why this change:
- The work log is a governed audit artifact and must reflect completed human
  acceptance after high-risk review.
- Leaving accepted merged work as `READY_FOR_INDEPENDENT_REVIEW` creates a
  false pending-review signal.

Expected outcome:
- Future audits can distinguish active pending high-risk work from already
  accepted Hetzner deployment-prep work.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `rg -n 'PR #80 was merged|PR #81 was merged|c53f413a7|b6b274861|Correct PR80 And PR81' docs/work_log/review_stabilized_work_log.md`
  returned the expected PR #80 and PR #81 merge references plus this correction
  entry.

Remaining risk:
- LOW: documentation-only audit-trail correction.
- Acceptance state: `ACCEPTED`.

## 2026-06-20T15:56:20Z - Harden Hetzner Preflight Runtime Dependency Check

Active role: ENGINEER

Objective:
- Prevent another Hetzner migration attempt from passing host preflight when
  the repo-local venv exists but runtime dependencies are not installed.

What was found:
- SHOWN: the 2026-06-20 isolated challenger proof reached state transfer before
  discovering `ModuleNotFoundError: No module named 'yaml'`.
- SHOWN: the previous preflight checked required files, venv prefix, Git state,
  NTP, Tailscale, and campaign config, but did not import the collector runtime.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` documented `python3 -m venv .venv` but did
  not mention Ubuntu's required `python3.12-venv` package or a dependency smoke
  import.

What changed:
- Added a bounded `collector_imports` check to
  `scripts/hetzner_paper_host_preflight.py`.
- The new check runs the active venv Python in a subprocess and imports
  `services.analytics.paper_strategy_evidence_service`.
- Added test coverage proving the check uses the provided venv executable and
  surfaces missing dependency stderr such as `No module named 'yaml'`.
- Updated `docs/HETZNER_PAPER_HOST.md` to install `python3.12-venv`, rebuild
  `.venv`, install requirements, and verify `import yaml`.

Why this change:
- Importing the collector service is the smallest read-only check that validates
  the dependency path needed to start a paper evidence collector.
- It catches the actual blocker before stopping local ownership or transferring
  state.

Expected outcome:
- Hetzner preflight fails early with `collector_imports_failed` when runtime
  dependencies are missing.
- A future migration attempt reaches state transfer only after the host can
  import the collector service.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_hetzner_paper_host_preflight.py`
  could not run because the current local `.venv` reports
  `No module named pytest`.
- SHOWN: `./.venv/bin/python -m py_compile scripts/hetzner_paper_host_preflight.py tests/test_hetzner_paper_host_preflight.py`
  completed with exit code `0`.
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: a direct `check_collector_imports` function smoke check returned
  `collector_imports_direct_smoke_ok`, covering both success and
  `ModuleNotFoundError: No module named 'yaml'` failure reporting.

Remaining risk:
- HIGH: deployment preflight behavior sits on the high-risk paper-host
  migration path.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-20T16:20:04Z - Complete Hetzner Host Dependency Setup

Active role: ENGINEER

Objective:
- Resolve the Hetzner host dependency blocker without changing local campaign
  ownership or starting a remote collector.

What was found:
- SHOWN: direct `cryptkeep` sudo failed because the account password was not
  known.
- SHOWN: Tailscale SSH as `root` succeeded.
- SHOWN: before setup, Hetzner `.venv` had no `pip` and could not import
  `yaml`.
- SHOWN: no remote challenger state was present before setup.

What changed:
- Used root Tailscale SSH to install `python3.12-venv`.
- Rebuilt `/srv/cryptkeep/app/.venv` as the `cryptkeep` user.
- Installed repo requirements into the Hetzner venv.
- Did not transfer state or start any Hetzner collector.

Why this change:
- The previous migration proof was blocked by host package/dependency setup,
  not by state-transfer integrity.
- Completing the host setup allows the next migration attempt to start from a
  clean single-owner boundary after PR #89 is accepted and merged.

Expected outcome:
- Hetzner can import the paper evidence collector runtime before any future
  state transfer.
- Local laptop campaigns remain the active owners until a fresh migration retry
  is performed.

Verification:
- SHOWN: remote setup command printed `yaml_ok`.
- SHOWN: Hetzner `./.venv/bin/python -m pip --version` returned `pip 26.1.2`
  from `/srv/cryptkeep/app/.venv`.
- SHOWN: Hetzner `import services.analytics.paper_strategy_evidence_service`
  printed `collector_import_ok`.
- SHOWN: Hetzner preflight at `a3159aa64` returned `ok=true`.
- SHOWN: remote state remains absent with `REMOTE_STATE=absent`.
- SHOWN: local `./.venv/bin/python scripts/restore_paper_campaigns.py --status`
  returned `ok=true`, `all_running=true`, and `running_count=3`.

Remaining risk:
- HIGH: host dependency setup is part of the high-risk deployment path.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-06-20T15:09:08Z - Fix Hetzner Preflight Venv Detection

Active role: ENGINEER

Objective:
- Remove a false-negative blocker in the Hetzner paper-host preflight before
  any local campaign state is stopped or transferred.

What was found:
- SHOWN: Hetzner checkout was clean at
  `affa5938bd9ec494ca9ba85a0a349fcc7eadb645`.
- SHOWN: Hetzner `.venv/bin/python` reported `sys.prefix` as
  `/srv/cryptkeep/app/.venv`, but the preflight failed `python_venv` because
  it resolved the interpreter symlink to `/usr/bin/python3.12`.
- SHOWN: no local collector state was stopped, transferred, or restarted.

What changed:
- Updated `scripts/hetzner_paper_host_preflight.py` so `python_venv` validates
  the active interpreter environment by `sys.prefix`, not by the resolved
  executable symlink path.
- Added a regression test covering the symlinked Ubuntu venv case.

Why this change:
- `sys.prefix` is Python's authoritative signal for the active virtual
  environment. On Ubuntu, `.venv/bin/python` may be a symlink into `/usr/bin`,
  so resolving the executable path rejects valid repo-local venvs.

Expected outcome:
- A valid Hetzner repo-local venv passes host preflight, while non-venv or
  wrong-prefix interpreters still fail before state transfer or collector
  startup.

Verification:
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_hetzner_paper_host_preflight.py`
  returned `7 passed`.
- SHOWN: `./.venv/bin/python -m py_compile scripts/hetzner_paper_host_preflight.py tests/test_hetzner_paper_host_preflight.py`
  completed with exit code `0`.
- SHOWN: `git diff --check` completed with exit code `0`.

Remaining risk:
- HIGH: deployment preflight behavior sits on the high-risk paper-host
  migration path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #87 was merged to `master` as `a3159aa64`.

## 2026-06-20T15:27:55Z - Attempt Hetzner Isolated Challenger Migration

Active role: ENGINEER

Objective:
- Execute the accepted single-owner migration proof for only the isolated
  `ema_cross_default` challenger campaign.

What was found:
- SHOWN: PR #87 was merged to `master` as
  `a3159aa646634c87fc4b8a2eb6d47928c371215a`.
- SHOWN: local `review-stabilized`, `origin/review-stabilized`, and
  `origin/master` were aligned at that commit before the attempt.
- SHOWN: Hetzner preflight passed at `a3159aa64` before state transfer.
- SHOWN: the local `ema_cross_default` collector was stopped and verified with
  `pid_alive=false` before transfer.
- SHOWN: state manifest creation succeeded with `249` files and SHA-256
  `b5939d7cd03c6e0a50824ffa133a0f2bea51045b6fe6248e7ec63445a50d1b80`.
- SHOWN: transferred state verified exactly after removing macOS AppleDouble
  `._*` sidecars created by the tar stream.
- SHOWN: Hetzner start failed with `collector_exit_1`; bounded foreground
  execution exposed `ModuleNotFoundError: No module named 'yaml'`.
- SHOWN: Hetzner `.venv` has no `pip`, `/usr/bin/python3` has no `ensurepip`,
  `python3.12-venv` is not installed, and passwordless sudo is unavailable.

What changed:
- Added `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  documenting the attempted migration, successful integrity checks, dependency
  blocker, and rollback state.
- No source code, config, or strategy logic was changed.
- Remote stale transferred challenger state and manifest were removed after the
  dependency blocker was confirmed.
- Local `ema_cross_default` ownership was restored.

Why this change:
- The proof record is required because the operation touched high-risk runtime
  ownership and state-transfer workflow.
- Removing the stale remote copy prevents a future false assumption that
  Hetzner owns current challenger state.
- Restoring the laptop collector preserves campaign continuity until the host
  dependency setup is completed by the operator with sudo.

Expected outcome:
- `ema_cross_default` continues running locally.
- Hetzner remains preflight-clean but has no active challenger state.
- The next attempt starts from a clean boundary after the operator installs
  `python3.12-venv` and repo requirements on the host.

Verification:
- SHOWN: local `./.venv/bin/python scripts/restore_paper_campaigns.py --status`
  returned `ok=true`, `all_running=true`, `running_count=3`, with
  `ema_cross_default` running as PID `19570`.
- SHOWN: remote Hetzner preflight without transferred state returned `ok=true`
  at `a3159aa64`.
- SHOWN: remote `REMOTE_STATE=absent` after cleanup.
- SHOWN: no full test suite was run per operator instruction to avoid
  long-running test commands.

Remaining risk:
- HIGH: deployment remains blocked on host package setup requiring operator
  sudo password entry.
- Acceptance state: `ACCEPTED_WITH_RISK`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #88 merge. Operational migration remains blocked
  until host dependency setup is completed.

## 2026-06-20T10:30:40Z - Record Paper Gate Status Checkpoint

Active role: ENGINEER

Objective:
- Capture the current paper campaign and promotion-gate state in a durable
  checkpoint after the Hetzner prep work was accepted.

What was found:
- SHOWN: `review-stabilized` was synced with `origin/review-stabilized` before
  the checkpoint was written.
- SHOWN: all three configured paper collectors were alive, healthy, idle, and
  waiting for the next UTC day after completing the `2026-06-20` session.
- SHOWN: the canonical `es_daily_trend_v1` paper gate was not ready:
  `ready=false`, `machine_ready=false`, and `manual_review_required=true`.
- SHOWN: the raw all-history journal reported `8` closed `sma_200_trend`
  trades, but the promotion gate counted only `1/10` provenance-qualified
  round trips.

What changed:
- Added `docs/checkpoints/paper_gate_status_2026_06_20.md`.
- The checkpoint records:
  - commands used;
  - campaign liveness for `es_daily_trend_v1`, `ema_cross_default`, and
    `breakout_default`;
  - canonical paper-gate state;
  - raw-history versus provenance-qualified evidence distinction;
  - manual-review blocker status;
  - current operational conclusion.

Why this change:
- The visible gate counter can look inconsistent unless raw journal history is
  separated from provenance-qualified promotion evidence.
- Recording this state prevents future check-ins from treating raw `8/10`
  history as gate-eligible `8/10` evidence.

Expected outcome:
- Future audits have a stable reference explaining why the current gate counter
  is `1/10` qualified round trips even though the raw journal contains eight
  closed trades.
- The next action remains either continued local collection or a separately
  accepted Hetzner isolated challenger proof.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_checkpoints_repo_path_references_exist.py`
  returned `2 passed`.
- SHOWN: `rg -n 'Paper Gate Status - 2026-06-20|1/10|8 closed|provenance-qualified|waiting_for_next_day|Record Paper Gate Status Checkpoint' docs/checkpoints/paper_gate_status_2026_06_20.md docs/work_log/review_stabilized_work_log.md`
  returned the expected checkpoint and work-log references.

Remaining risk:
- MEDIUM: documentation-only checkpoint for a high-risk promotion/evidence
  path. No runtime, collector, cloud, or gate-policy change was made.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #85 was merged to `master` as `f8d2e4f1a`.

## 2026-06-20T10:34:23Z - Correct PR85 Work Log Acceptance State

Active role: ENGINEER

Objective:
- Correct the governed work log after the accepted PR #85 merge.

What was found:
- SHOWN: PR #85 was independently reviewed and accepted by the human operator,
  then merged to `master` as `f8d2e4f1a`.
- SHOWN: the corresponding work-log entry still ended with
  `READY_FOR_INDEPENDENT_REVIEW`, which no longer matched the repository state.

What changed:
- Updated the paper gate status checkpoint entry acceptance state to
  `ACCEPTED` and added the PR #85 merge reference.

Why this change:
- The work log is a governed audit artifact and should not show completed,
  accepted work as still pending independent review.

Expected outcome:
- Future audits see the true remaining paper-gate blocker: provenance-qualified
  evidence accumulation and performance review, not checkpoint review.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `rg -n 'PR #85 was merged|f8d2e4f1a|Correct PR85 Work Log Acceptance State' docs/work_log/review_stabilized_work_log.md`
  returned the expected PR #85 merge reference and correction entry.

Remaining risk:
- LOW: documentation-only audit-trail correction.
- Acceptance state: `ACCEPTED`.

## 2026-06-20T10:22:58Z - Refresh Priority 16 Hetzner Backlog State

Active role: ENGINEER

Objective:
- Align the active next-actions checkpoint with the accepted Hetzner paper-host
  prep now merged to `master`.

What was found:
- SHOWN: `review-stabilized` and `master` are aligned at `2396c13e9`.
- SHOWN: Priority 16 still described state-transfer integrity, host preflight,
  and proof-record setup as future work even though PR #79, PR #80, and PR #81
  had been accepted and merged.
- SHOWN: actual Hetzner deployment remains blocked on explicit single-owner
  operation, server-hosted UTC cycle proof, and backup/restore rehearsal.

What changed:
- Updated Priority 16 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`.
- Recorded accepted artifacts:
  - `scripts/paper_state_manifest.py`;
  - `scripts/hetzner_paper_host_preflight.py`;
  - `docs/deployment_records/hetzner_isolated_challenger_proof_TEMPLATE.md`.
- Clarified the next operational sequence:
  - create a dated proof record;
  - record laptop status and stop proof;
  - create and verify the state manifest;
  - run Hetzner preflight;
  - restore/start only after single-owner proof;
  - record first UTC cycle and backup rehearsal before canonical migration.

Why this change:
- The backlog is the operator-facing to-do list. Stale status creates a false
  impression that repo prep remains unfinished when the true blocker is now the
  high-risk operational proof.
- This keeps the next action explicit without starting collectors, moving state,
  or touching the Hetzner host.

Expected outcome:
- Future check-ins will not rework accepted prep items.
- The next meaningful action is clearly separated from repo work: execute and
  record the isolated `ema_cross_default` VPS proof under the accepted runbook.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `./.venv/bin/python -m pytest -q tests/test_checkpoints_repo_path_references_exist.py`
  returned `2 passed`.
- SHOWN: `rg -n 'state-transfer manifest tooling|hetzner_paper_host_preflight.py|hetzner_isolated_challenger_proof_TEMPLATE.md|single-owner operation|backup/restore rehearsal|Refresh Priority 16 Hetzner Backlog State' docs/checkpoints/review_stabilized_next_actions_2026_05_28.md docs/work_log/review_stabilized_work_log.md`
  returned the expected updated Priority 16 and work-log references.

Remaining risk:
- MEDIUM: documentation-only backlog accuracy for a high-risk deployment path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #83 was merged to `master` as `2b5240674`.

## 2026-06-20T10:26:21Z - Correct PR83 Work Log Acceptance State

Active role: ENGINEER

Objective:
- Correct the governed work log after the accepted PR #83 merge.

What was found:
- SHOWN: PR #83 was independently reviewed and accepted by the human operator,
  then merged to `master` as `2b5240674`.
- SHOWN: the corresponding work-log entry still ended with
  `READY_FOR_INDEPENDENT_REVIEW`, which no longer matched the repository state.

What changed:
- Updated the Priority 16 Hetzner backlog refresh entry acceptance state to
  `ACCEPTED` and added the PR #83 merge reference.

Why this change:
- The work log is a governed audit artifact and should not show completed,
  accepted work as still pending independent review.

Expected outcome:
- Future audits see the true remaining Hetzner blocker: operational proof, not
  backlog documentation review.

Verification:
- SHOWN: `git diff --check` completed with exit code `0`.
- SHOWN: `rg -n 'PR #83 was merged|2b5240674|Correct PR83 Work Log Acceptance State' docs/work_log/review_stabilized_work_log.md`
  returned the expected PR #83 merge reference and correction entry.

Remaining risk:
- LOW: documentation-only audit-trail correction.
- Acceptance state: `ACCEPTED`.

## 2026-06-20T20:00:31Z - Migrate EMA Challenger To Hetzner

Active role: ENGINEER

Objective:
- Retry the isolated `ema_cross_default` paper challenger migration after PR #89
  and the Hetzner host dependency setup removed the prior `yaml`/venv blocker.

What was found:
- SHOWN: PR #89 merged to `master` as
  `b86105b1f491058aac235dcbb33748729dee7297`.
- SHOWN: `review-stabilized` was fast-forwarded and pushed to the same merge
  commit.
- SHOWN: Hetzner checkout updated cleanly to
  `b86105b1f491058aac235dcbb33748729dee7297`.
- SHOWN: Hetzner preflight returned `ok=true`; `collector_imports` returned
  `collector_import_ok`; remote state was absent before retry.
- SHOWN: local `ema_cross_default` was running/idle before the retry and had
  already recorded the 2026-06-20 UTC session.

What changed:
- Stopped only the local `ema_cross_default` collector.
- Created a fresh SHA-256 manifest for
  `.cbp_state_challengers/ema_cross_default_daily`.
- Transferred only that isolated challenger state tree to Hetzner.
- Verified transferred content on Hetzner with the manifest.
- Ran Hetzner preflight with `--require-state`.
- Started only the Hetzner `ema_cross_default` campaign from
  `configs/paper_evidence_campaigns.hetzner.example.json`.
- Updated
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  with the migration evidence.

Why this change:
- The project needs a durable paper-campaign host so challenger evidence can
  accumulate without depending on the laptop being awake.
- Migrating only the isolated EMA challenger is the narrowest safe deployment
  proof because canonical `.cbp_state`, live exchange credentials, and the
  active `es_daily_trend_v1` gate campaign remain on the laptop.

Expected outcome:
- `ema_cross_default` continues collecting paper evidence on Hetzner as a
  single-owner campaign.
- Laptop remains responsible only for `es_daily_trend_v1` and
  `breakout_default`.
- The first server-hosted UTC cycle can be observed before considering any
  broader migration.

Verification:
- SHOWN: local stop flag was written for `ema_cross_default`.
- SHOWN: targeted `SIGINT` stopped only PID `19570` after the daily loop did
  not immediately consume the stop flag while sleeping on its `300` second poll
  interval.
- SHOWN: local status reported `ema_cross_default` `pid_alive=false`,
  `has_pid_file=false`, and `running=false`.
- SHOWN: local `es_daily_trend_v1` remained running as PID `80255`.
- SHOWN: local `breakout_default` remained running as PID `80263`.
- SHOWN: manifest create returned `ok=true`, `file_count=248`, and
  `manifest_sha256=d3f3494ada77ff03dd506ebfc573b696f465dbcb596e784695924b56eff17b59`.
- SHOWN: remote manifest verify returned `ok=true`, `expected_file_count=248`,
  `actual_file_count=248`, `missing=[]`, `changed=[]`, and `extra=[]`.
- SHOWN: remote preflight with `--require-state` returned `ok=true`,
  `collector_imports_ok`, clean git checkout, NTP synchronized, Tailscale
  running, and `state_exists=true`.
- SHOWN: remote restore returned `ok=true`, `all_running=true`, one configured
  campaign, and Hetzner PID `1286864` for `ema_cross_default`.
- SHOWN: local process scan returned only PIDs `80255` and `80263` for the
  remaining local collectors and no local `ema_cross` collector.

Remaining risk:
- HIGH: this is operational migration/background-job ownership work.
- The first Hetzner-hosted UTC cycle has not completed yet.
- Backup/restore rehearsal is still required before canonical state migration.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #90 was merged.

## 2026-06-20T20:11:43Z - Rehearse Hetzner EMA Backup Restore

Active role: ENGINEER

Objective:
- Complete the isolated backup/restore rehearsal for the Hetzner-hosted
  `ema_cross_default` challenger without touching active state or canonical
  `.cbp_state`.

What was found:
- SHOWN: current UTC time was `2026-06-20T20:10:18Z`, so the first
  Hetzner-hosted UTC cycle was not due yet.
- SHOWN: `review-stabilized`, `origin/master`, and
  `origin/review-stabilized` were aligned at `d6a6ae5696fdaa65ca55a6b53f59fc88db493f3f`.
- SHOWN: Hetzner `ema_cross_default` was running/idle as PID `1286864`.
- SHOWN: local `ema_cross_default` was stopped, while local
  `es_daily_trend_v1` and `breakout_default` remained running.
- SHOWN: `/srv/cryptkeep/backups` existed and was owned by `cryptkeep`.
- SHOWN: host disk and inode usage had available capacity.

What changed:
- Created a Hetzner backup manifest for the active isolated EMA state.
- Created a compressed backup archive under `/srv/cryptkeep/backups`.
- Restored the archive into an isolated rehearsal path under
  `/srv/cryptkeep/restore_rehearsals`.
- Verified the restored copy against the backup manifest.
- Updated
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  with the backup/restore rehearsal evidence.

Why this change:
- The Hetzner runbook requires a backup and isolated restore rehearsal before
  any canonical state migration.
- Doing the rehearsal against only the isolated EMA challenger proves the
  backup mechanics without risking the active campaign owner or production
  `.cbp_state`.

Expected outcome:
- The backup/restore requirement is implementation-proof-ready for independent
  review.
- The only remaining observation blocker before wider migration planning is the
  first healthy server-hosted UTC cycle, plus human review of this backup proof.

Verification:
- SHOWN: manifest create returned `ok=true`, `file_count=248`, and
  `manifest_sha256=fca0c5700899708029c0287d5dde58b8c851bffd6e03b42bd13be273a1c15a8e`.
- SHOWN: backup archive path:
  `/srv/cryptkeep/backups/ema_cross_default_20260620T201143Z.tar.gz`.
- SHOWN: backup manifest path:
  `/srv/cryptkeep/backups/ema_cross_default_20260620T201143Z.manifest`.
- SHOWN: isolated restore root:
  `/srv/cryptkeep/restore_rehearsals/ema_cross_default_20260620T201143Z`.
- SHOWN: restored manifest verify returned `ok=true`,
  `expected_file_count=248`, `actual_file_count=248`, `missing=[]`,
  `changed=[]`, and `extra=[]`.
- SHOWN: restored and active evidence file counts both returned `24`.
- SHOWN: restored runtime pid file count returned `0`.
- SHOWN: active Hetzner campaign remained running as `ema_cross_default`, PID
  `1286864`.

Remaining risk:
- HIGH: backup/restore rehearsal is deployment/operational state handling.
- The first Hetzner-hosted UTC cycle has not completed yet.
- Canonical `.cbp_state` migration remains blocked.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #91 was merged.

## 2026-06-20T20:21:10Z - Record Hetzner EMA Controlled Stop Recovery

Active role: ENGINEER

Objective:
- Document the controlled-stop/operator-visible-failure proof and recovery for
  the isolated Hetzner `ema_cross_default` challenger.

What was found:
- SHOWN: the first Hetzner-hosted UTC cycle was still not due at
  `2026-06-20T20:18:44Z`.
- SHOWN: local `es_daily_trend_v1` and `breakout_default` remained running.
- SHOWN: local `ema_cross_default` remained stopped.
- SHOWN: Hetzner `ema_cross_default` was the only remote campaign.
- SHOWN: the operator pasted terminal output proving the restart completed
  after Codex was blocked by an execution/usage limit while attempting the
  restart command.

What changed:
- Updated
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  with a controlled stop and recovery section.
- Updated the proof-record status to
  `CONTROLLED_STOP_READY_FOR_REVIEW_PENDING_FIRST_UTC_CYCLE`.
- Updated current `ema_cross_default` ownership PID from `1286864` to
  `1287182`.

Why this change:
- The Hetzner runbook requires an operator-visible failure from a controlled
  collector stop before broader migration planning.
- The pasted operator output is the authoritative evidence for the recovery
  because it shows the stopped state before restore and the running state after
  restore.

Expected outcome:
- The controlled-stop/recovery proof is available for independent review.
- The active EMA challenger remains ready for the first server-hosted UTC cycle.

Verification:
- SHOWN: stop flag path:
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily/runtime/flags/paper_strategy_evidence.stop`.
- SHOWN: stopped status returned `ok=false`, `all_running=false`,
  `running_count=0`, `status=stopped`, `reason=stop_requested`,
  `pid_alive=false`, and `has_pid_file=false`.
- SHOWN: stopped summary text was
  `Paper evidence collector daily loop was stopped by request.`
- SHOWN: restore returned `ok=true`, `all_running=true`, exactly one
  configured campaign, and `running_count=1`.
- SHOWN: final status returned `ema_cross_default` running as PID `1287182`,
  `pid_alive=true`, `status=idle`, `reason=waiting_for_next_day`, and
  `last_completed_day=2026-06-20`.

Remaining risk:
- HIGH: controlled stop/recovery is deployment/background-job ownership work.
- The first Hetzner-hosted UTC cycle has not completed yet.
- Canonical `.cbp_state` migration remains blocked.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #92 was merged.

## 2026-06-21T02:23:20Z - Record Hetzner EMA First UTC Cycle

Active role: ENGINEER

Objective:
- Document the first completed server-hosted UTC cycle for the isolated
  Hetzner `ema_cross_default` challenger.

What was found:
- SHOWN: PR #92 merged to `master` as `87c4a5b116e892af34b46ff65a35ec07b2ef70e7`.
- SHOWN: `review-stabilized`, `origin/master`, and
  `origin/review-stabilized` were aligned at the same commit before this proof.
- SHOWN: Hetzner `ema_cross_default` completed its first hosted 2026-06-21 UTC
  cycle and returned to idle.
- SHOWN: local `ema_cross_default` remained stopped.
- SHOWN: local `es_daily_trend_v1` and `breakout_default` continued to run on
  the laptop.
- SHOWN: local `es_daily_trend_v1` also recorded a new 2026-06-21 fill, which
  is separate canonical campaign evidence and not part of the Hetzner EMA
  proof.

What changed:
- Updated
  `docs/deployment_records/hetzner_isolated_challenger_proof_2026_06_20.md`
  with the first UTC-cycle observation.
- Updated the proof-record status to `FIRST_UTC_CYCLE_READY_FOR_REVIEW`.

Why this change:
- The Hetzner runbook requires one healthy hosted UTC cycle with public-OHLCV
  provenance before broader migration planning.
- Capturing the proof now preserves the exact remote status, evidence counts,
  and session provenance while keeping canonical state untouched.

Expected outcome:
- The isolated EMA challenger has satisfied the hosted-cycle implementation
  proof and is ready for independent review.
- Canonical `.cbp_state` migration remains blocked until this proof is accepted
  and a separate canonical migration plan is reviewed.

Verification:
- SHOWN: Hetzner status returned `ok=true`, `all_running=true`,
  `running_count=1`, `status=idle`, `reason=waiting_for_next_day`,
  `pid_alive=true`, and active PID `1287182`.
- SHOWN: Hetzner `last_completed_day=2026-06-21`.
- SHOWN: last hosted run started at `2026-06-21T00:01:11.880557+00:00` and
  ended at `2026-06-21T00:16:15.594165+00:00`.
- SHOWN: last hosted run had `campaign_status=completed`,
  `completed_strategies=1`, `strategy=ema_cross`, `signal_action=hold`,
  `fills_delta=0`, and `closed_trades_delta=0`.
- SHOWN: `session_2026-06-21.jsonl` existed on Hetzner with `2` rows.
- SHOWN: session provenance included `market_data_source=public_ohlcv`,
  `ohlcv_sample_mode=false`, `ohlcv_timeframe=5m`, `ohlcv_venue=coinbase`, and
  `ohlcv_symbol=BTC/USDT`.
- SHOWN: Hetzner evidence counts advanced to `session=17` and
  `total_records=44`.
- SHOWN: local `ema_cross_default` status remained `pid_alive=false` and
  `has_pid_file=false`.

Remaining risk:
- HIGH: this is deployment/background-job ownership proof.
- Canonical `.cbp_state` migration remains blocked pending independent review
  and a separate migration plan.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #93 was merged.

## 2026-06-21T02:33:27Z - Split Laptop Paper Campaign Manifest From Hetzner EMA Owner

Active role: ENGINEER

Objective:
- Stop the laptop paper-campaign health shortcut from reporting the accepted
  Hetzner-owned `ema_cross_default` campaign as a local outage.

What was found:
- SHOWN: `./.venv/bin/python scripts/restore_paper_campaigns.py --status`
  returned `ok=false`, `all_running=false`, `campaign_count=3`, and
  `running_count=2` because local `ema_cross_default` was stopped.
- SHOWN: the same local status showed `es_daily_trend_v1` and
  `breakout_default` running/idle on the laptop.
- SHOWN: Hetzner status with
  `configs/paper_evidence_campaigns.hetzner.example.json` returned `ok=true`,
  `all_running=true`, `running_count=1`, and `ema_cross_default` running/idle.
- SHOWN: the accepted Hetzner proof record says `ema_cross_default` is the
  Hetzner owner after the first hosted UTC cycle.

What changed:
- Added `configs/paper_evidence_campaigns.laptop.json` with only the laptop
  owned campaigns: `es_daily_trend_v1` and `breakout_default`.
- Updated `make status-paper-campaigns` and `make restore-paper-campaigns` to
  use `PAPER_CAMPAIGN_CONFIG`, defaulting to the laptop manifest.
- Kept `configs/paper_evidence_campaigns.json` unchanged as the full
  three-campaign local manifest for pre-migration or single-host operation.
- Updated `docs/PAPER_CAMPAIGN_RECOVERY.md` and `docs/GOLDEN_PATH.md` to
  describe the laptop/Hetzner ownership split and the override path.
- Added a regression test asserting the laptop manifest excludes the
  Hetzner-owned EMA challenger.

Why this change:
- Local operator health checks should reflect local ownership, not report an
  intentionally migrated remote campaign as a laptop outage.
- Keeping the full manifest available avoids removing a valid single-host
  operation mode.

Expected outcome:
- `make status-paper-campaigns` reports only laptop-owned paper collectors.
- Hetzner EMA health remains checked with the Hetzner manifest.
- Operators can still opt into the full local manifest by setting
  `PAPER_CAMPAIGN_CONFIG=configs/paper_evidence_campaigns.json`.

Verification:
- `make status-paper-campaigns`
  - SHOWN: command now reads `configs/paper_evidence_campaigns.laptop.json`.
  - SHOWN: returned `ok=true`, `all_running=true`, `campaign_count=2`, and
    `running_count=2`.
  - SHOWN: checked `es_daily_trend_v1` and `breakout_default`; local
    `ema_cross_default` was not treated as a laptop outage.
- `./.venv/bin/python -c 'from services.analytics.paper_campaign_recovery import ...'`
  - SHOWN: laptop manifest resolves to `['es_daily_trend_v1',
    'breakout_default']`.
  - SHOWN: Hetzner manifest resolves to `['ema_cross_default']`.
  - SHOWN: full manifest remains `['es_daily_trend_v1', 'ema_cross_default',
    'breakout_default']`.
- `./.venv/bin/python -m py_compile services/analytics/paper_campaign_recovery.py scripts/restore_paper_campaigns.py`
  - SHOWN: command passed.
- `./.venv/bin/python -m py_compile tests/test_paper_campaign_recovery.py`
  - SHOWN: command passed.
- `git diff --check`
  - SHOWN: command passed.
- `./.venv/bin/python -m pytest -q tests/test_paper_campaign_recovery.py tests/test_restore_paper_campaigns.py`
  - NOT RUN locally to completion: local `.venv` is missing `pytest`
    (`No module named pytest`). CI or reviewer should run this targeted slice.

Remaining risk:
- HIGH: this changes operator recovery shortcuts for background paper
  campaign processes.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #94 was merged.

## 2026-06-21T03:48:47Z - Record Paper Gate Status After Laptop Manifest Split

Active role: ENGINEER

Objective:
- Capture the current read-only paper gate and campaign ownership state after
  PR #94 merged the laptop/Hetzner campaign manifest split.

What was found:
- SHOWN: `review-stabilized`, `origin/review-stabilized`, and `origin/master`
  were aligned at `7f884c0f7b251b07a8884614d963e922a0493a96`.
- SHOWN: laptop campaign status returned `ok=true`, `all_running=true`,
  `campaign_count=2`, and `running_count=2`.
- SHOWN: laptop-owned `es_daily_trend_v1` and `breakout_default` were running
  and idle after recording `2026-06-21`.
- SHOWN: canonical `es_daily_trend_v1` paper gate remained `ready=false`,
  `machine_ready=false`, and `manual_review_required=true`.
- SHOWN: canonical qualified round-trip progress remained `1/10` with
  `9` remaining.
- SHOWN: raw all-history reported `17` fills and `8` closed trades, while
  qualified paper history reported `2` fills and `1` closed trade.
- SHOWN: the Hetzner status command required Tailscale browser re-auth and was
  interrupted, so remote EMA health was not reverified in this checkpoint.

What changed:
- Added `docs/checkpoints/paper_gate_status_2026_06_21.md`.
- The checkpoint records laptop-owned campaign health, the blocked Hetzner
  re-auth check, the canonical `1/10` qualified gate state, and the current
  raw-history versus qualified-evidence distinction.

Why this change:
- The prior June 20 checkpoint was stale after both the Hetzner EMA ownership
  split and the new June 21 canonical fill.
- Capturing the current state prevents the audit trail from drifting back to
  the obsolete `9/12` unqualified-fill and single-incomplete-fill snapshot.

Expected outcome:
- Future audits can distinguish the healthy laptop collectors from the
  unverified remote EMA check.
- Future gate reviews use the current `9/13` unqualified-fill and
  `2` incomplete-qualified-fill snapshot.

Verification:
- `make status-paper-campaigns`
  - SHOWN: returned `ok=true`, `all_running=true`, `campaign_count=2`, and
    `running_count=2`.
- `./.venv/bin/python scripts/check_promotion_gates.py --json`
  - SHOWN: returned `ready=false`, `machine_ready=false`,
    `manual_review_required=true`, `47/30` days, `1/10` qualified round trips,
    and `9` remaining.
- `./.venv/bin/python -c 'from services.control.paper_promotion_progress import ...'`
  - SHOWN: returned `round_trips_recorded=1`,
    `round_trips_remaining=9`, `all_history_round_trips=8`,
    `unqualified_evidence_fills=9`, and
    `incomplete_qualified_evidence_fills=2`.
- `tailscale ssh cryptkeep@100.86.128.9 ... restore_paper_campaigns.py --status`
  - NOT VERIFIED: Tailscale required browser re-auth and the command was
    interrupted.

Remaining risk:
- MEDIUM: this is a read-only checkpoint for a high-risk promotion/evidence
  path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #95 was merged.

## 2026-06-21T03:59:43Z - Record Hetzner EMA Health After Tailscale Re-Auth

Active role: ENGINEER

Objective:
- Update the June 21 paper-gate checkpoint after the operator completed
  Tailscale authentication and reran the Hetzner `ema_cross_default` status
  command.

What was found:
- SHOWN: `review-stabilized`, `origin/review-stabilized`, and `origin/master`
  were aligned at `928c60f61471ea2887d77c11600987187e8ba215`.
- SHOWN from the operator-provided terminal output: Hetzner status returned
  `ok=true`, `all_running=true`, `campaign_count=1`, and `running_count=1`.
- SHOWN: Hetzner `ema_cross_default` was running and idle as PID `1287182`.
- SHOWN: `last_completed_day=2026-06-21`.
- SHOWN: the hosted state path remained
  `/srv/cryptkeep/app/.cbp_state_challengers/ema_cross_default_daily`.
- SHOWN: the latest hosted run had `strategy=ema_cross`,
  `strategy_preset=ema_cross_default`, `signal_action=hold`,
  `fills_delta=0`, and `closed_trades_delta=0`.
- SHOWN: Hetzner JSONL evidence existed with `fill=4`, `order=4`,
  `session=17`, and `total_records=44`.

What changed:
- Updated `docs/checkpoints/paper_gate_status_2026_06_21.md` so the Hetzner
  EMA section records verified remote health instead of the earlier
  Tailscale-auth-blocked state.
- Marked the checkpoint back to `READY_FOR_INDEPENDENT_REVIEW` because this
  commit amends an accepted audit artifact with new evidence.

Why this change:
- The previous checkpoint accurately recorded that remote status was blocked by
  Tailscale re-auth at that moment.
- The operator-provided command output later supplied the missing material fact:
  remote EMA ownership is healthy.

Expected outcome:
- Future audits see both sides of the ownership split as healthy: laptop-owned
  `es_daily_trend_v1` and `breakout_default`, plus Hetzner-owned
  `ema_cross_default`.

Verification:
- SHOWN: read the attached operator terminal output from
  `/Users/baitus/.codex/attachments/97577ed3-84bb-4c26-a565-34cb52ace869/pasted-text.txt`.
- `git rev-parse HEAD origin/master origin/review-stabilized`
  - SHOWN: all three refs were aligned at
    `928c60f61471ea2887d77c11600987187e8ba215` before this update.

Remaining risk:
- MEDIUM: this is a read-only checkpoint update for a high-risk
  deployment/evidence path.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #96 was merged.

## 2026-06-21T04:08:11Z - Refresh Remaining Tasks Index For Active Paper Campaigns

Active role: ENGINEER

Objective:
- Refresh the lightweight remaining-task index after the accepted paper-gate and
  Hetzner EMA campaign checkpoints.

What was found:
- SHOWN: the current active blocker is paper-evidence collection, not live
  launch.
- SHOWN: the accepted June 21 checkpoint records laptop-owned
  `es_daily_trend_v1` and `breakout_default` campaigns as healthy.
- SHOWN: the accepted June 21 checkpoint records Hetzner-owned
  `ema_cross_default` as healthy after Tailscale re-authentication.
- SHOWN: canonical `es_daily_trend_v1` paper promotion remains blocked at
  `1/10` provenance-qualified round trips, with `9` remaining.
- SHOWN: raw all-history reports `8` closed trades, but that count is
  diagnostic unless both entry and exit fills carry the required non-sample
  public-OHLCV provenance.
- SHOWN: `REMAINING_TASKS.md` still foregrounded the older root-runtime launch
  blocker framing.

What changed:
- Updated `REMAINING_TASKS.md` to make the current paper-campaign/gate state the
  first visible operator context.
- Linked the accepted June 21 paper-gate checkpoint.
- Separated root-runtime launch blockers from paper-evidence campaign blockers.
- Added the current strategy-research planning links for pullback recovery and
  short-market strategy work.
- Added an explicit warning not to treat raw all-history trade count as
  promotion progress.

Why this change:
- The remaining-task index is used as operator orientation.
- Mixing launch blockers with the current paper-evidence blocker caused
  confusing check-ins and made the next action less clear.
- The smallest correct fix was to update the index, not change campaign or gate
  behavior.

Expected outcome:
- Future check-ins distinguish the active paper-campaign path from the separate
  live-launch blocker path.
- Operators use `scripts/check_promotion_gates.py --json` as the promotion
  source of truth instead of raw all-history trade count.

Verification:
- `sed -n '1,180p' REMAINING_TASKS.md`
  - SHOWN: the index now surfaces current paper-campaign state, ownership split,
    accepted checkpoint, and provenance-qualified gate count.
- No test suite was run because this is a docs/index-only change.

Remaining risk:
- LOW: docs/index only; no runtime, gate, campaign, deploy, or secret behavior
  changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session before PR #97 was merged.

## 2026-06-21T04:24:22Z - Align Admin Bypass Runbook With Chat Acceptance Workflow

Active role: ENGINEER

Objective:
- Correct the branch-protection runbook so it matches the intended solo-project
  workflow for chat-accepted admin merges and branch alignment.

What was found:
- SHOWN: PR #97 checks passed before merge.
- SHOWN: PR #97 was blocked only by the owner-self-review rule.
- SHOWN: the existing runbook stated that AI-agent workflows must not use CLI
  admin-bypass flags.
- SHOWN: this Codex thread ran `gh pr merge 97 --rebase --admin` after human
  chat acceptance, which conflicts with the existing runbook even though the
  work had been accepted.
- SHOWN: the first PR #98 draft made the visible GitHub UI/admin bypass path
  mandatory after chat acceptance.
- SHOWN: the human operator rejected that as an unintended workflow change:
  chat acceptance should authorize the agent to proceed when the remaining
  blocker is only the owner-self-review rule.
- SHOWN: GitHub created `master` commit `9ff718d89` while
  `origin/review-stabilized` remained at sibling commit `19602b7ed`.
- SHOWN: `origin/master` and `origin/review-stabilized` had no file diff and
  identical tree hash `dea725496774d6b5c11429bb5d9666fc31231c3c`.
- SHOWN: local `review-stabilized` was rebased onto `origin/master`; Git skipped
  `19602b7ed` as already applied.
- SHOWN: `origin/review-stabilized` was moved to `9ff718d89` with
  `git push --force-with-lease`.
- SHOWN: final `HEAD`, `origin/master`, and `origin/review-stabilized` were all
  aligned at `9ff718d891565ff6335ffc1e11b99d84958585e7`.

What changed:
- Updated `docs/GITHUB_BRANCH_PROTECTION.md` to allow Codex to run
  `gh pr merge --admin` after explicit human chat acceptance.
- Added guardrails for chat-authorized CLI admin merges: PR must not be draft,
  required checks must pass, GitHub must report the PR mergeable, the only
  blocker must be the owner-self-review rule, acceptance must occur after the
  latest pushed PR commit, and no material audit blocker may remain.
- Added a post-merge branch-alignment procedure that is allowed only after the
  PR is already merged and the `master`/`review-stabilized` file trees are
  proven identical.
- Updated the previous work-log entry acceptance state for PR #97 from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The branch-alignment step is useful and should remain documented.
- The user rejected the extra UI-only step because it changed the existing
  accepted workflow.
- The correct boundary is explicit human acceptance plus passing checks, not an
  additional manual UI action every time.
- The guardrails preserve the review boundary while allowing the agent to carry
  out the merge operation after the human decision is visible in the thread.

Expected outcome:
- Future accepted PRs can be merged by Codex with `gh pr merge --admin` after
  explicit human chat acceptance and green checks.
- Agents may still repair same-tree branch drift after the merge by following
  the documented, lease-protected alignment procedure.

Verification:
- `git rev-parse HEAD origin/master origin/review-stabilized`
  - SHOWN before this docs change: all three refs were aligned at
    `9ff718d891565ff6335ffc1e11b99d84958585e7`.
- `make status-paper-campaigns`
  - SHOWN: local laptop campaigns remained running and idle for the next UTC
    day.
- `tailscale ssh cryptkeep@100.86.128.9 ... restore_paper_campaigns.py --status`
  - SHOWN: Hetzner `ema_cross_default` remained running and idle for the next
    UTC day.
- No test suite was run because this is a docs/runbook-only change.

Remaining risk:
- MEDIUM: governance/process documentation for merge authority and branch
  alignment.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #98 commit
  `db39192dd9c14c7c4385aca58b2a538b36a871fc`; PR #98 merged as
  `d3682666a354522c839bdaf003d8493129f1fe27`.

## 2026-06-21T04:35:45Z - Expose Supervised Paper Soak Status Make Target

Active role: ENGINEER

Objective:
- Make the existing read-only supervised paper-soak status report discoverable
  through the operator Makefile path.

What was found:
- SHOWN: `scripts/report_supervised_soak_status.py` already exists and is a
  read-only combined report for configured campaign health plus paper promotion
  gate status.
- SHOWN: `scripts/SCRIPTS.md` listed the script but no Makefile wrapper.
- SHOWN: `Makefile` exposed `status-paper-campaigns` and `check-gates-json`
  separately but did not expose the combined report.
- SHOWN: the script's internal default campaign config is the full
  `configs/paper_evidence_campaigns.json`, while the current laptop ownership
  split should use `configs/paper_evidence_campaigns.laptop.json` through
  `PAPER_CAMPAIGN_CONFIG`.

What changed:
- Added `make status-paper-soak` and `make status-paper-soak-json`.
- Wired both targets through `PAPER_CAMPAIGN_CONFIG`, preserving the current
  laptop-default manifest.
- Updated `docs/GOLDEN_PATH.md`, `docs/PAPER_CAMPAIGN_RECOVERY.md`, and
  `scripts/SCRIPTS.md` so the command is visible and scoped as a local/laptop
  check-in command.

Why this change:
- The operator has been repeatedly asking for check-ins while the evidence
  campaign is passive.
- The repo already had the right read-only report; adding a Make target is the
  smallest correct change.
- Using `PAPER_CAMPAIGN_CONFIG` prevents the laptop shortcut from accidentally
  treating the Hetzner-owned `ema_cross_default` state as local truth.

Expected outcome:
- Daily local check-ins can use one command for laptop campaign health plus
  paper gate state: `make status-paper-soak`.
- Hetzner-owned campaign status remains a separate host-specific check.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `make -n status-paper-soak status-paper-soak-json`
  - SHOWN: both targets resolve to `scripts/report_supervised_soak_status.py`
    with `--config configs/paper_evidence_campaigns.laptop.json`.
- `make status-paper-soak`
  - SHOWN: report completed successfully.
  - SHOWN: laptop campaigns reported `2/2 running`.
  - SHOWN: paper gate reported `ready=False`, `machine_ready=False`,
    `manual_review_required=True`, and `1/10` qualified round trips.
- `./.venv/bin/python -m pytest -q tests/test_report_supervised_soak_status.py`
  - NOT RUN: current local venv lacks `pytest` (`No module named pytest`).
- No full test suite was run because this is a Makefile/docs operator-wrapper
  change over an existing script.

Remaining risk:
- LOW: operator workflow wrapper and docs only; no runtime, gate, campaign,
  deploy, or secret behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #100 commit
  `141756031afc6be8ce7dfc4943791b055bdde100`; PR #100 merged as
  `a45540eeb905502b1bbbfc8dd22a6060978f5f73`.

## 2026-06-21T04:52:47Z - Point Remaining Tasks To Paper Soak Status Target

Active role: ENGINEER

Objective:
- Keep the lightweight remaining-task index aligned with the accepted
  `make status-paper-soak` operator workflow.

What was found:
- SHOWN: PR #100 merged and branch refs were aligned at
  `a45540eeb905502b1bbbfc8dd22a6060978f5f73`.
- SHOWN: `make status-paper-soak` reports the local laptop campaign health and
  paper-gate state in one read-only command.
- SHOWN: `REMAINING_TASKS.md` still listed separate local status and raw
  promotion-gate commands as the current paper-campaign path.
- SHOWN: current local status remains `2/2` laptop campaigns running, with the
  paper gate at `1/10` qualified round trips.

What changed:
- Updated `REMAINING_TASKS.md` so the default local check-in is
  `make status-paper-soak`.
- Kept `make status-paper-campaigns` as the lower-level command for raw laptop
  process restore/status detail.
- Kept Hetzner-owned `ema_cross_default` as a separate host/manifest check.
- Updated the previous work-log entry for PR #100 from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The index should point operators to the newest accepted workflow rather than
  the pre-wrapper command sequence.
- This is the smallest correction and avoids touching campaign runtime or gate
  behavior.

Expected outcome:
- Future check-ins use the combined paper-soak status command first.
- Operators still know when to use raw laptop campaign status and separate
  Hetzner status.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `sed -n '1,120p' REMAINING_TASKS.md`
  - SHOWN: the current paper-campaign path now starts with
    `make status-paper-soak`.
- `make status-paper-soak`
  - SHOWN: report completed successfully.
  - SHOWN: laptop campaigns reported `2/2 running`.
  - SHOWN: paper gate reported `ready=False`, `machine_ready=False`,
    `manual_review_required=True`, and `1/10` qualified round trips.
- No tests were run because this is a docs/index-only change.

Remaining risk:
- LOW: docs/index and acceptance-log update only; no runtime, gate, campaign,
  deploy, or secret behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #101 commit
  `11777d7f52013d8efeeeab2c275eaaf10ec0ecdd`; PR #101 merged as
  `e2738a22a64152a6bf93232568089dedf04a6caa`.

## 2026-06-21T10:07:14Z - Add Hetzner Paper Status Make Target

Active role: ENGINEER

Objective:
- Add a read-only Makefile shortcut for the Hetzner-owned paper campaign status
  check.

What was found:
- SHOWN: `make status-paper-soak` reports laptop campaign health and the
  canonical paper gate, but intentionally excludes Hetzner-owned
  `ema_cross_default`.
- SHOWN: the Hetzner check currently requires copying the long Tailscale SSH
  command from docs.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` records the accepted Tailscale SSH target
  as `cryptkeep@100.86.128.9`, the accepted app path as
  `/srv/cryptkeep/app`, and the Hetzner manifest as
  `configs/paper_evidence_campaigns.hetzner.example.json`.
- SHOWN: current local status remains `2/2` laptop campaigns running, with the
  paper gate at `1/10` qualified round trips.

What changed:
- Added Makefile variables:
  - `HETZNER_SSH_TARGET`
  - `HETZNER_APP_DIR`
  - `HETZNER_PAPER_CAMPAIGN_CONFIG`
- Added `make status-paper-hetzner`, a read-only Tailscale SSH wrapper around
  the existing remote `restore_paper_campaigns.py --status` command.
- Updated `docs/GOLDEN_PATH.md`, `docs/PAPER_CAMPAIGN_RECOVERY.md`, and
  `REMAINING_TASKS.md` to point operators at the new remote check-in target.
- Updated the previous work-log entry for PR #101 from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The local and remote check-in paths should be equally discoverable.
- A Makefile wrapper reduces copy/paste error without changing campaign runtime,
  ownership, or restore behavior.
- The wrapper keeps remote status separate from laptop status so the
  single-owner split stays explicit.

Expected outcome:
- Daily check-in path becomes:
  - `make status-paper-soak` for laptop-owned campaigns and canonical gate
  - `make status-paper-hetzner` for the Hetzner-owned EMA campaign
- Operators can override target/app/config variables if the deployment record
  changes.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `make -n status-paper-hetzner`
  - SHOWN: target resolves to the accepted Tailscale SSH status command for
    `cryptkeep@100.86.128.9`, `/srv/cryptkeep/app`, and
    `configs/paper_evidence_campaigns.hetzner.example.json`.
- `make status-paper-hetzner`
  - SHOWN: command completed successfully.
  - SHOWN: Hetzner status returned `ok=true`, `all_running=true`,
    `campaign_count=1`, and `running_count=1`.
  - SHOWN: `ema_cross_default` was running and idle as PID `1287182`, waiting
    for the next UTC day.
- No full test suite was run because this is a Makefile/docs read-only wrapper
  over an existing remote status command.

Remaining risk:
- LOW: read-only operator workflow wrapper and docs only; no runtime, gate,
  campaign restore/start, deploy, or secret behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #102 commit
  `0d390024a6b592c0bb849314df658ca25e1ad843`; PR #102 merged as
  `a3983511ca7fb4fc945d6a4fd21dfa44da3003c6`.

## 2026-06-21T10:30:14Z - Format Hetzner Paper Status Output

Active role: ENGINEER

Objective:
- Keep the accepted `make status-paper-hetzner` command but make its output
  operator-readable instead of raw campaign-recovery JSON.

What was found:
- SHOWN: `make status-paper-soak` prints a concise local campaign and paper-gate
  summary.
- SHOWN: `make status-paper-hetzner` previously called the remote
  `restore_paper_campaigns.py --status` command directly, which returned a long
  raw JSON payload.
- SHOWN: depending on a new script already being deployed to Hetzner would be
  brittle, because the remote host may lag the repo branch during review.

What changed:
- Added `scripts/report_paper_campaign_status.py`, a read-only formatter for
  paper campaign recovery status.
- Added `--from-json` support so an existing
  `restore_paper_campaigns.py --status` payload can be formatted locally from
  stdin or a file.
- Updated `make status-paper-hetzner` to run the existing remote raw status
  command, then format the returned JSON locally.
- Added `tests/test_report_paper_campaign_status.py`.
- Updated `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md`, and
  `docs/PAPER_CAMPAIGN_RECOVERY.md` to document the concise status output.

Why this change:
- The operator should not need to read raw nested JSON for routine remote
  campaign check-ins.
- Keeping the same Make target avoids adding another step to the workflow.
- Formatting locally avoids a deployment-order dependency on the Hetzner host.

Expected outcome:
- `make status-paper-hetzner` remains read-only and uses the accepted Tailscale
  SSH path, but prints the same kind of concise campaign health summary as the
  local status flow.
- If the remote repo has not pulled the latest branch yet, the target still
  works because the remote side only needs the already-accepted recovery script.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: passed.
- `make -n status-paper-hetzner`
  - SHOWN: target now resolves to remote
    `restore_paper_campaigns.py --status` piped into local
    `report_paper_campaign_status.py --from-json -`.
- `./.venv/bin/python scripts/restore_paper_campaigns.py --config configs/paper_evidence_campaigns.laptop.json --status | ./.venv/bin/python scripts/report_paper_campaign_status.py --from-json -`
  - SHOWN: formatter printed a concise report with `2/2` local campaigns
    running and recommendation `continue_paper_observation`.
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_paper_campaign_status.py`
  - SHOWN: not run successfully in this local environment because `.venv` does
    not have `pytest` installed.

Remaining risk:
- LOW: read-only operator-output formatting and docs/tests only; no campaign
  restore/start behavior, gate logic, deploy logic, or secret handling changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #103 commit
  `a99e8a05474fc92a9dfaa0453b68c67cea5583b6`; PR #103 merged as
  `781fd240d59200c6c3d9f1d6e7f97ca4e25912f5`.

## 2026-06-21T10:48:30Z - Fail Closed On Broken Hetzner Status Formatting

Active role: ENGINEER

Objective:
- Keep `make status-paper-hetzner` read-only while ensuring broken or malformed
  remote status output exits non-zero.

What was found:
- SHOWN: `scripts/report_paper_campaign_status.py --from-json
  /tmp/definitely-missing-status.json` printed an investigation recommendation
  but exited `0`.
- SHOWN: adding `--strict` to the same formatter command returned exit `1`.
- SHOWN: `services.analytics.paper_campaign_recovery.manage_campaigns` returns
  `ok=false` unless all selected campaigns are running and individually `ok`.

What changed:
- Updated `make status-paper-hetzner` to pass `--strict` to the local formatter.
- Added a regression test proving strict formatting returns `1` for invalid
  status JSON.
- Updated `docs/GOLDEN_PATH.md` and `docs/PAPER_CAMPAIGN_RECOVERY.md` to state
  that malformed remote JSON or `ok=false` remote status exits non-zero after
  printing the investigation recommendation.

Why this change:
- A status command used for operations should not silently return success when
  the remote status payload is missing, malformed, or reports a failed campaign.
- This is the smallest correction because it does not alter remote recovery
  behavior, campaign runtime, gate logic, or the operator command name.

Expected outcome:
- Healthy Hetzner status still prints the concise campaign-health summary.
- Broken Tailscale/SSH output, malformed JSON, or remote `ok=false` campaign
  state makes `make status-paper-hetzner` fail at the shell level.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: passed.
- `make -n status-paper-hetzner`
  - SHOWN: target now resolves to remote
    `restore_paper_campaigns.py --status` piped into local
    `report_paper_campaign_status.py --strict --from-json -`.
- `./.venv/bin/python scripts/report_paper_campaign_status.py --strict --from-json /tmp/definitely-missing-status.json; printf 'exit=%s\n' $?`
  - SHOWN: formatter printed `investigate_report_failure` and returned
    `exit=1`.
- `make status-paper-hetzner`
  - SHOWN: live remote status completed successfully.
  - SHOWN: Hetzner reported `1/1` campaigns running and
    `ema_cross_default` idle, waiting for the next UTC day.
- `git diff --check`
  - SHOWN: passed.
- Targeted pytest was not run because this local `.venv` does not have
  `pytest` installed.

Remaining risk:
- LOW: Makefile strictness, docs, and a formatter regression test only; no
  campaign restore/start behavior, gate logic, deploy logic, or secret handling
  changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #104 commit
  `d82d7831660a40db32e9aa7d49147cff0b78616f`; PR #104 merged as
  `d1a7a588979ef1976e081b3e5263b530dc698822`.

## 2026-06-21T11:08:09Z - Declare Documented Operator Make Targets Phony

Active role: ENGINEER

Objective:
- Make documented operator-facing Make targets robust against same-named files
  in the repo.

What was found:
- SHOWN: `scripts/SCRIPTS.md` and `docs/GOLDEN_PATH.md` document operator
  Make targets such as `check-gates`, `kill-switch-on`,
  `kill-switch-off`, and `paper-stop-now`.
- SHOWN: those later Makefile targets were not covered by the existing `.PHONY`
  declarations, while earlier paper-campaign targets were.
- SHOWN: if a file or directory with a target's name appears, `make` can treat
  that target as up to date and skip the command unless it is phony.

What changed:
- Added `.PHONY` declarations for the remaining developer, operator, emergency,
  gate, and script-index Make targets defined later in the file.
- Updated the prior PR #104 work-log entry from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- Operator commands should always execute when invoked.
- This is the smallest safe fix because it changes only Make target metadata;
  no command body, runtime behavior, gate logic, campaign state, or secrets are
  touched.

Expected outcome:
- `make check-gates`, `make paper-stop-now`, `make kill-switch-on/off`, and the
  other documented targets cannot be shadowed by same-named files.

Verification:
- `make -n check-gates`
  - SHOWN: resolved to `./.venv/bin/python scripts/check_promotion_gates.py`.
- `make -n paper-stop-now`
  - SHOWN: resolved to `./.venv/bin/python scripts/paper_stop.py --force-now`.
- `make -n kill-switch-on`
  - SHOWN: resolved to `./.venv/bin/python scripts/killswitch.py --arm`.
- `make -n script-index`
  - SHOWN: resolved to the documented operator script index echo block.
- `git diff --check`
  - SHOWN: passed.
- No runtime commands or tests were run because this change only declares
  Makefile targets phony and dry-run output proves command resolution.

Remaining risk:
- LOW: Makefile metadata and work-log update only; no command bodies or runtime
  behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #105 commit
  `ca31dc5581d90025468d1840237101591a9bfcd0`; PR #105 merged as
  `be587d7652fab1f2cb518086b23e653860ade0d9`.

## 2026-06-21T11:22:52Z - Add Unified Paper Status Check-In Target

Active role: ENGINEER

Objective:
- Restore a one-command daily paper check-in while preserving the accepted
  split-host ownership between laptop campaigns and the Hetzner EMA campaign.

What was found:
- SHOWN: `REMAINING_TASKS.md` required `make status-paper-soak` and
  `make status-paper-hetzner` as two separate routine check-in commands.
- SHOWN: `docs/GOLDEN_PATH.md` still said to check all accepted paper campaigns
  with `make status-paper-campaigns`, but that target follows only the laptop
  manifest after the accepted Hetzner migration.
- SHOWN: both local and Hetzner status paths are already read-only and accepted.

What changed:
- Added `make status-paper-all`, a read-only wrapper that runs
  `status-paper-soak` and `status-paper-hetzner` in sequence.
- The wrapper preserves both reports even if one side fails, then exits
  non-zero if either side reports failure.
- Updated `REMAINING_TASKS.md`, `docs/GOLDEN_PATH.md`,
  `docs/PAPER_CAMPAIGN_RECOVERY.md`, and `scripts/SCRIPTS.md` to use the new
  unified check-in command.
- Updated the prior PR #105 work-log entry from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The operator check-in should be one command, not a memory task requiring two
  separate commands.
- This is the smallest safe fix because it composes existing read-only status
  targets and does not alter campaign runtime, restore/start behavior, gate
  logic, deployment, or secrets.

Expected outcome:
- Routine check-in becomes `make status-paper-all`.
- Operators can still run `make status-paper-soak` or
  `make status-paper-hetzner` when intentionally checking only one host.

Verification:
- `make -n status-paper-all`
  - SHOWN: resolved to `status-paper-soak` followed by
    `status-paper-hetzner`.
- `make status-paper-all`
  - SHOWN: local laptop status reported `2/2` campaigns running.
  - SHOWN: canonical gate remained `ready=False`,
    `manual_review_required=True`, and `1/10` provenance-qualified round trips.
  - SHOWN: Hetzner status reported `1/1` campaigns running and
    `ema_cross_default` idle, waiting for the next UTC day.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is a Makefile/docs wrapper over existing
  read-only status targets.

Remaining risk:
- LOW: Makefile wrapper and docs only; no campaign restore/start behavior, gate
  logic, deploy logic, or secret handling changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #106 commit
  `bfe63f9992ac375419340e34780e065c6d24931c`; PR #106 merged as
  `b49d6c769962a7234ce2362ea92df831a4cf8f7b`.

## 2026-06-22T02:48:29Z - Surface Unified Paper Status In Script Index

Active role: ENGINEER

Objective:
- Keep the built-in Makefile operator index aligned with the accepted daily
  paper check-in path.

What was found:
- SHOWN: `make status-paper-all` is now the documented daily check-in in
  `REMAINING_TASKS.md`, `docs/GOLDEN_PATH.md`, and `scripts/SCRIPTS.md`.
- SHOWN: `make script-index` still omitted `status-paper-all`, so the built-in
  operator command menu did not surface the current daily path.

What changed:
- Added `make status-paper-all` to the `script-index` echo output.
- Updated the prior PR #106 work-log entry from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The built-in operator menu should match the current documented workflow.
- This is the smallest safe correction because it only changes an echo line and
  work-log metadata.

Expected outcome:
- Running `make script-index` shows the unified daily paper campaign check-in
  command first.

Verification:
- `make script-index`
  - SHOWN: output lists `make status-paper-all` first as the daily paper
    campaign check-in.
- `make -n script-index`
  - SHOWN: dry-run output includes the same `status-paper-all` echo line.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this change only updates Makefile echo output and
  work-log metadata.

Remaining risk:
- LOW: Makefile echo output and work-log update only; no command bodies,
  campaign behavior, gate logic, deploy logic, or secret handling changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #107 commit
  `88b72cb71f5e318b51b3714e0bfd25bf296d1ee7`; PR #107 merged as
  `06eeefe7e9e982742db4ab20e774aff45da3a9a0`.

## 2026-06-22T03:03:58Z - Capture Active Backlog In Remaining Tasks

Active role: ENGINEER

Objective:
- Persist the current remaining backlog list in the repo so it is visible in
  git instead of only in chat.

What was found:
- SHOWN: `REMAINING_TASKS.md` pointed at the canonical blocker lists and
  strategy planning docs, but did not contain a concise current backlog list.
- SHOWN: the current accepted task sources are
  `docs/checkpoints/launch_blockers_root_runtime.md`,
  `docs/checkpoints/root_runtime_next_actions.md`,
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`,
  `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md`, and
  `docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md`.
- SHOWN: PR #107 was independently accepted and merged as
  `06eeefe7e9e982742db4ab20e774aff45da3a9a0`.

What changed:
- Added an `Active Backlog` section to `REMAINING_TASKS.md` summarizing the
  visible remaining tasks across paper evidence, root-runtime launch,
  strategy research, Hetzner follow-through, and operator documentation.
- Updated the prior PR #107 work-log entry from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.

Why this change:
- The operator asked for the remaining backlog; keeping it in the repo avoids
  losing the task list in chat history.
- The change is intentionally an index only. It does not create new runtime
  requirements or change gate policy.

Expected outcome:
- `REMAINING_TASKS.md` is the concise starting point for the next planning
  pass, with links to the deeper checkpoint docs still preserved above it.

Verification:
- `sed -n '1,130p' REMAINING_TASKS.md`
  - SHOWN: the `Active Backlog` section is present and lists 14 remaining
    tasks.
- `rg -n 'Active Backlog|PR #107|06eeefe7|Capture Active Backlog' REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: backlog and acceptance references are visible.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is a docs/work-log update only.

Remaining risk:
- LOW: docs/work-log update only; no runtime, campaign, gate, strategy,
  deployment, or secret behavior changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #108 commit
  `06bb41c135386a2e45539ad275cc56aa0739ae3e`; PR #108 merged as
  `494643e6d0ee46a8da8fb59a05cad8b89f69b835`.

## 2026-06-22T03:21:47Z - Persist Supervised Pipeline Log Evidence

Active role: ENGINEER

Objective:
- Close the root-runtime P3 implementation gap for supervised pipeline exit
  evidence while the paper campaigns continue passively.

What was found:
- SHOWN: `docs/checkpoints/launch_blockers_root_runtime.md` still described a
  live-readiness gap where `pipeline.status.json` can remain stale after a
  process exits before writing a failure state.
- SHOWN: `services/runtime/process_supervisor.py` already redirected
  supervised child stdout/stderr to runtime log files, but the behavior was not
  covered by a targeted test and the returned/status payloads did not expose a
  durable `log_path` consistently.
- SHOWN: `scripts/bot_status.py` and
  `services/process/bot_runtime_truth.py` read from
  `process_supervisor.status(...)`, so status-time log discovery belongs in the
  supervisor status payload rather than only in start-time output.

What changed:
- Added a `_logfile(name)` helper in `services/runtime/process_supervisor.py`
  for `<CBP_STATE_DIR>/runtime/logs/<name>.log`.
- Updated `start_process(...)` to return `log_path` for both newly-started and
  already-running processes.
- Updated `status(...)` to return `log_path` with each supervised service row.
- Added targeted process-supervisor tests for durable `pipeline.log` routing,
  already-running `log_path` output, and status payload `log_path` output.
- Updated `docs/checkpoints/launch_blockers_root_runtime.md` to record the
  implementation-proof state and remaining independent-review close condition.

Why this change:
- A stale status JSON file should not be the only artifact available after a
  supervised process exits.
- Returning `log_path` from both start and status paths is the smallest
  coherent interface change because existing operator status tools already use
  the supervisor status surface.

Expected outcome:
- Supervised runtime processes leave stdout/stderr evidence in deterministic
  runtime log files.
- Operators and tooling can locate the relevant log from the process start
  response or later supervisor status output.

Verification:
- `./.venv/bin/python -m py_compile services/runtime/process_supervisor.py tests/test_process_supervisor.py`
  - SHOWN: passed.
- Direct supervised child proof with
  `CBP_STATE_DIR=/private/tmp/cbp-process-supervisor-proof`
  - SHOWN: `start_process(...)` returned
    `/private/tmp/cbp-process-supervisor-proof/runtime/logs/pipeline_log_proof.log`.
  - SHOWN: `process_supervisor.status(...)` returned the same `log_path`.
  - SHOWN: the log file existed and contained `supervised-output-proof`.
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_process_supervisor.py`
  - SHOWN: not runnable in this local venv:
    `No module named pytest`.
  - UNVERIFIED: pytest execution of the new regression tests is pending CI or
    an environment with pytest installed.

Remaining risk:
- HIGH-adjacent: runtime supervision supports live-readiness evidence and
  process observability. The change is intentionally narrow, but it should be
  independently reviewed before treating P3 as closed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after latest PR #109 implementation commit
  `b4db2dba2b532dbbdd44519774981d2fdb46f93b`.

## 2026-06-22T03:30:09Z - Close Pipeline Log Evidence Backlog Item

Active role: ENGINEER

Objective:
- Keep the visible backlog and root-runtime blocker list aligned after PR #109
  was accepted and merged.

What was found:
- SHOWN: PR #109 merged as `f4b8c296d`.
- SHOWN: `HEAD`, `origin/master`, and `origin/review-stabilized` all pointed
  at `f4b8c296d` after branch alignment.
- SHOWN: `docs/checkpoints/launch_blockers_root_runtime.md` still described
  P3 as implementation-proof-ready and pending independent review.
- SHOWN: `REMAINING_TASKS.md` still listed durable supervised pipeline log
  capture as an active backlog item.

What changed:
- Marked P3 pipeline exit evidence capture as `CLOSED` in
  `docs/checkpoints/launch_blockers_root_runtime.md`.
- Added the PR #109 close evidence: implementation commit, human acceptance,
  merge commit, and passing GitHub checks before merge.
- Removed the completed item from the active backlog in `REMAINING_TASKS.md`
  and added it under `Recently completed`.

Why this change:
- Completed runtime evidence work should not remain in the active backlog.
- The smallest correct change is documentation alignment only; the runtime
  implementation and acceptance already landed through PR #109.

Expected outcome:
- Future planning starts from the real remaining backlog instead of repeatedly
  selecting the already-closed pipeline log capture item.

Verification:
- `sed -n '35,75p' REMAINING_TASKS.md`
  - SHOWN: active backlog is renumbered to 13 items and no longer lists
    pipeline log capture as active.
- `sed -n '64,92p' docs/checkpoints/launch_blockers_root_runtime.md`
  - SHOWN: P3 status is `CLOSED` and includes PR #109 close evidence.
- `rg -n "Pipeline exit evidence|Status: CLOSED|Recently completed|PR #109|f4b8c296d|b4db2dba2" REMAINING_TASKS.md docs/checkpoints/launch_blockers_root_runtime.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: backlog, blocker doc, and work log contain the expected references.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is docs/work-log alignment only.

Remaining risk:
- LOW: docs/work-log alignment only; no runtime, campaign, gate, deployment,
  or secret behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-06-22T03:34:45Z - Align Shadow Spread Evidence Checkpoint Status

Active role: ENGINEER

Objective:
- Correct stale checkpoint wording after the shadow spread/depth evidence
  implementation had already been accepted.

What was found:
- SHOWN: `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`
  still listed Priority 5 as `implementation proof ready, pending independent
  review`.
- SHOWN: the work log records the shadow spread/depth implementation as
  accepted after `9f0dd8b0c`.
- SHOWN: `git log --all --grep='shadow|spread|depth'` shows
  `4c414b256 docs: accept shadow spread evidence fix` and PR #51 merge
  `64bd86e54` for shadow-gate evidence scoping.
- SHOWN: the remaining work is not another implementation review; it is
  observing fresh signal records with `spread_bps` when tick data is fresh.

What changed:
- Updated Priority 5 status to `implementation accepted; fresh-record
  verification pending`.
- Replaced the stale independent-review next action with explicit acceptance
  evidence and the remaining fresh-record verification action.
- Clarified the active backlog item so it says implementation is accepted but
  fresh stamped records still need to be observed.

Why this change:
- Planning docs should not route the operator back into an already-completed
  independent review.
- The remaining work is evidence collection/verification, not code or policy
  review.

Expected outcome:
- Future proactive work does not re-open the accepted shadow spread/depth
  implementation.
- The operator-facing backlog points at the real remaining task: verify new
  stamped evidence when fresh tick data is available.

Verification:
- `sed -n '145,180p' docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`
  - SHOWN: Priority 5 status is `implementation accepted; fresh-record
    verification pending` with acceptance evidence for `9f0dd8b0c`,
    `4c414b256`, and `64bd86e54`.
- `sed -n '170,190p' docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`
  - SHOWN: the next action is now fresh evidence observation, not another
    independent review.
- `sed -n '45,62p' REMAINING_TASKS.md`
  - SHOWN: active backlog item 5 states the implementation is accepted and
    fresh stamped records still need observation.
- `rg -n "implementation accepted|fresh-record verification|fresh stamped|9f0dd8b0c|4c414b256|64bd86e54|Align Shadow Spread Evidence" REMAINING_TASKS.md docs/checkpoints/review_stabilized_next_actions_2026_05_28.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: expected references are present in the backlog, checkpoint, and
    work log.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is docs/work-log alignment only.

Remaining risk:
- LOW: docs/work-log alignment only; no runtime, campaign, gate, deployment,
  strategy, or secret behavior changed.
- UNVERIFIED: no fresh post-fix signal record with `spread_bps` was produced
  during this docs alignment pass.
- Acceptance state: `ACCEPTED`.

## 2026-06-22T03:41:44Z - Scope Read-Only Candidate Layer Activation

Active role: ENGINEER

Objective:
- Convert the generic dormant-infrastructure backlog item into one concrete
  scoped objective with proof requirements.

What was found:
- SHOWN: `docs/OBJECTIVE.md` names learning/adaptive capability as a standing
  product objective and requires read-only evidence mode first.
- SHOWN: `docs/checkpoints/infrastructure_activation_audit_2026_06_03.md`
  identifies the signal/candidate layer as the highest-leverage partially
  wired activation target after paper-campaign isolation.
- SHOWN: `docs/ARCHITECTURE.md` documents the candidate layer as paper-only and
  warns not to enable `CBP_USE_CANDIDATE_ADVISOR=1` until outcome attribution
  confirms signal value.
- SHOWN: `services/signals/candidate_engine.py`,
  `scripts/data/run_candidate_scan.py`, `scripts/candidate_trade_summary.py`,
  and `scripts/dev/review_candidate_outcomes.py` already provide partial
  candidate scan and candidate-vs-outcome surfaces.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`.
- SHOWN: `make candidate-summary` existed, but `make script-index` did not
  display it.

What changed:
- Added
  `docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md`.
- Updated `REMAINING_TASKS.md` to replace the generic dormant-infrastructure
  item with the accepted candidate outcome report objective.
- Corrected `docs/ARCHITECTURE.md` candidate-layer script references and linked
  the scoped activation objective.
- Updated `make script-index` to show `make candidate-summary`.
- Clarified `scripts/SCRIPTS.md` so `candidate_trade_summary.py` is explicitly
  read-only and tied to `make candidate-summary`.

Why this change:
- The candidate layer is the safest high-leverage dormant subsystem to advance
  because it directly addresses whether the repo identifies moves early enough
  while staying read-only.
- The smallest correct step is a scoped objective and operator-doc alignment,
  not enabling candidate-advisor strategy selection.

Expected outcome:
- Future implementation work has a bounded target: produce a read-only
  candidate outcome artifact before any candidate layer can become
  authoritative.
- The operator does not confuse candidate research commands with paper-gate or
  live-routing controls.

Verification:
- `sed -n '1,180p' docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md`
  - SHOWN: the scoped objective, boundaries, implementation path, and proof
    requirements are present.
- `sed -n '60,78p' REMAINING_TASKS.md`
  - SHOWN: backlog item 12 now points to the read-only candidate outcome
    report objective.
- `sed -n '251,278p' docs/ARCHITECTURE.md`
  - SHOWN: candidate-layer script references and the scoped activation
    objective link are present.
- `make script-index`
  - SHOWN: output includes `make candidate-summary`.
- `rg -n "candidate_layer_read_only_activation_objective|candidate-summary|use_candidate_advisor: false|SCOPED_OBJECTIVE_READY|read-only candidate outcome" REMAINING_TASKS.md docs/ARCHITECTURE.md docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md scripts/SCRIPTS.md Makefile configs/strategies/es_daily_trend_v1.yaml docs/work_log/review_stabilized_work_log.md`
  - SHOWN: expected references are present and
    `configs/strategies/es_daily_trend_v1.yaml` still has
    `use_candidate_advisor: false`.
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is docs/Makefile index alignment only.

Remaining risk:
- LOW: docs/Makefile index alignment only; no runtime, campaign, strategy
  selection, promotion gate, deployment, order routing, or secret behavior
  changed.
- UNVERIFIED: the candidate outcome report itself is not implemented by this
  planning pass.
- Acceptance state: `ACCEPTED`.

## 2026-06-23T02:14:53Z - Implement Read-Only Candidate Outcome Report

Active role: ENGINEER

Objective:
- Implement the accepted candidate-layer read-only activation objective without
  enabling candidate-advisor strategy selection.

What was found:
- SHOWN: PR #112 merged the scoped candidate-layer objective to `master`.
- SHOWN: `scripts/dev/review_candidate_outcomes.py` contained useful
  candidate-vs-journal comparison logic but did not persist an operator-facing
  report artifact.
- SHOWN: `scripts/candidate_trade_summary.py` summarized attributed candidate
  trade buckets but also did not produce the required latest/dated JSON
  artifact.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`.

What changed:
- Added `services/signals/candidate_outcomes.py` to build and persist a
  read-only candidate-vs-paper-outcome report.
- Added `scripts/run_candidate_outcome_report.py` as a root operator CLI.
- Added `make candidate-outcomes`.
- Added targeted tests in `tests/test_candidate_outcomes.py` for empty
  history, no-outcome history, matching closed-outcome metrics, and artifact
  writes.
- Updated `docs/ARCHITECTURE.md`, `scripts/SCRIPTS.md`,
  `REMAINING_TASKS.md`, and the candidate-layer objective checkpoint.

Why this change:
- The repo needs to answer whether candidate rankings identify useful moves
  early enough before the candidate layer can become authoritative.
- Persisting latest and dated artifacts gives operators an audit trail without
  enabling strategy overrides or changing promotion gates.

Expected outcome:
- `make candidate-outcomes` produces a read-only candidate outcome report and
  writes `.cbp_state/data/candidate_outcomes/candidate_outcomes.latest.json`.
- Empty or insufficient candidate history is reported explicitly instead of
  being treated as success.
- Candidate-advisor strategy selection remains disabled.

Verification:
- `./.venv/bin/python -m py_compile services/signals/candidate_outcomes.py scripts/run_candidate_outcome_report.py tests/test_candidate_outcomes.py`
  - SHOWN: passed.
- Synthetic temp-state proof with generated candidate history and SQLite paper
  fills
  - SHOWN: report `status` was `ok`.
  - SHOWN: `candidates_reviewed` was `2`.
  - SHOWN: top-rank net PnL was `10.0`.
  - SHOWN: non-top-rank net PnL was `-5.0`.
  - SHOWN: latest artifact existed.
  - SHOWN: safety flags were `read_only=true`,
    `candidate_advisor_enabled=false`, `orders_routed=false`, and
    `promotion_gate_mutated=false`.
  - SHOWN: limitations include symbol-level attribution and repeated candidate
    rows possibly referencing the same paper fills.
- `make script-index`
  - SHOWN: output includes `make candidate-outcomes`.
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_candidate_outcomes.py`
  - SHOWN: not runnable in the local venv:
    `No module named pytest`.
  - UNVERIFIED: pytest execution of the new regression tests is pending CI or
    an environment with pytest installed.

Remaining risk:
- HIGH-adjacent: financial/strategy-evaluation logic, even though this pass is
  read-only and does not affect routing, gates, campaigns, or strategy
  selection.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: human operator independently reviewed and accepted in
  the Codex session after PR #113 implementation commit
  `614bae6e7a1ab5a16129c00b5b919ecfc5a12ef6`.

## 2026-06-24T02:53:03Z - Align Short Context Backlog State

Active role: ENGINEER

Objective:
- Remove a stale backlog instruction that still asked operators to run the
  short-side feasibility audit after that audit and its first accepted
  read-only follow-through had already landed.

What was found:
- SHOWN: `docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md`
  already exists and documents the read-only short/context feasibility audit.
- SHOWN: work-log entry `2026-06-19T18:44:46Z` recorded the feasibility audit
  as completed.
- SHOWN: Priority 12 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` now reports
  the collector/store extension accepted, sample and spot-context proofs
  complete, and Binance derivatives context blocked.
- SHOWN: work-log entries for PR #72 record accepted open-interest and
  order-book row support plus deterministic sample and live-public partial
  proofs.
- SHOWN: `REMAINING_TASKS.md` still said to run the feasibility audit, which
  was stale.

What changed:
- Marked the short-market research spec and short-context feasibility audit as
  accepted planning/audit artifacts while keeping their no-execution scopes
  explicit.
- Updated both documents' next-action sections to point at the current
  remaining work: deterministic/accepted-public replay only, derivatives
  public-data proof, and no short/context routing without separate review.
- Replaced the stale backlog item with the current short/context follow-up and
  added the completed feasibility audit to `REMAINING_TASKS.md`.

Why this change:
- The task index should not ask the operator or future agents to repeat an
  audit that is already present and accepted in the repo.
- Preserving the remaining blockers prevents the correction from implying that
  derivatives data, replay, paper short simulation, or execution are ready.

Expected outcome:
- Future proactive work starts from the correct short/context state: feasibility
  audit complete, read-only row support accepted, deterministic and partial
  public proofs recorded, Binance derivatives data still blocked.
- No strategy routing, paper execution, promotion-gate behavior, credentials,
  campaign ownership, or live behavior changes.

Verification:
- SHOWN: `rg -n "Run the read-only short-side feasibility audit|READY_FOR_INDEPENDENT_REVIEW|Acceptance state|Current Next Action|Completed Follow-Through|short-side feasibility audit is complete" REMAINING_TASKS.md docs/checkpoints/short_context_data_feasibility_audit_2026_06_19.md docs/checkpoints/short_market_strategy_research_spec_2026_06_19.md`
  no longer found the stale active-backlog instruction.
- SHOWN: `git diff --check` passed.
- Tests not run: documentation-only backlog/status alignment with no source,
  config, runtime, gate, or campaign behavior modified.

Remaining risk:
- HIGH: derivatives, shorting, leverage, margin, liquidation risk, replay
  analysis, paper short simulation, and future order-routing behavior remain
  separate high-risk workstreams.
- Acceptance state: `ACCEPTED`.

## 2026-06-24T03:00:00Z - Refresh Paper Gate Status Snapshot

Active role: ENGINEER

Objective:
- Update the lightweight task index with the current local laptop paper-gate
  status after the previous snapshot became stale.

What was found:
- SHOWN: `make status-paper-soak` is local-only and calls
  `scripts/report_supervised_soak_status.py` with the laptop campaign
  manifest.
- SHOWN: `make status-paper-soak` reported `Campaigns: 2/2 running
  (all_running=True)`.
- SHOWN: `es_daily_trend_v1` reported `fills=18`, `closed=9`, and
  `pnl=32.1776`.
- SHOWN: `breakout_default` reported `fills=9`, `closed=4`, and `pnl=-2.2281`.
- SHOWN: the canonical paper gate reported `2/10` provenance-qualified round
  trips, `8` remaining, `50/30` days, and manual review still required.
- SHOWN: raw all-history reported `9` closed trades, but the gate still treated
  7 all-history round trips as diagnostic-only and reported `9/14` JSONL fills
  lacking or mismatching required provenance.
- UNVERIFIED: Hetzner-owned `ema_cross_default` status was not checked by this
  local-only command.

What changed:
- Added `docs/checkpoints/paper_gate_status_2026_06_24.md` as a read-only
  status snapshot.
- Updated `REMAINING_TASKS.md` current state from the stale June 21 `1/10`
  gate count to the June 24 local `2/10` gate count.
- Preserved the distinction between provenance-qualified gate progress and raw
  diagnostic all-history trade count.

Why this change:
- Operators were seeing active gate changes in the command output while the
  task index still displayed the older `1/10` state.
- Capturing the current snapshot in a checkpoint keeps the repo evidence trail
  visible without requiring chat history.

Expected outcome:
- The top-level backlog now reflects current local paper-gate progress:
  `2/10`, `8` remaining, days satisfied, manual review still required.
- No campaign, gate, strategy, remote host, or execution behavior changes.

Verification:
- SHOWN: `make status-paper-soak` returned exit code `0` with the values above.
- SHOWN: `git diff --check` passed.
- Tests not run: documentation-only status snapshot with no source, config,
  runtime, gate, or campaign behavior modified.

Remaining risk:
- MEDIUM: this is a point-in-time local laptop snapshot only. Hetzner remote
  status still requires the accepted remote status command when intentionally
  needed.
- Acceptance state: `ACCEPTED`.

## 2026-06-24T03:02:24Z - Narrow PR #43 Rebuild Follow-Up

Active role: ENGINEER

Objective:
- Replace the broad active PR #43 rebuild instruction with a current-master
  follow-up status that separates completed rebuild work from still-open
  candidates.

What was found:
- SHOWN: `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  grouped PR #43 rebuild work into AI operator alerting/oversight, safe runtime
  wrappers and bot topology, managed multi-symbol paper runtime, and
  supervised-soak reporting.
- SHOWN: `scripts/report_supervised_soak_status.py` exists.
- SHOWN: `tests/test_report_supervised_soak_status.py` exists.
- SHOWN: `scripts/SCRIPTS.md` lists `report_supervised_soak_status.py` with
  `make status-paper-soak` and `make status-paper-soak-json`.
- SHOWN: work-log entry `2026-06-19T17:09:24Z` records supervised-soak
  reporting as rebuilt and accepted.
- SHOWN: PR #109 closed durable supervised pipeline log evidence.
- SHOWN: current source does not contain `scripts/run_ai_alert_monitor.py`,
  `scripts/run_ai_oversight_watch.py`,
  `services/ai_copilot/alert_monitor.py`,
  `services/ai_copilot/oversight_watch.py`,
  `services/runtime/managed_symbol_config.py`,
  `services/runtime/managed_symbol_selection.py`, or
  `scripts/run_pipeline_safe.py`.

What changed:
- Added `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`.
- Updated `REMAINING_TASKS.md` so PR #43 follow-up no longer treats
  supervised-soak reporting or pipeline log evidence as active work.
- Updated Priority 9 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to list the
  still-open rebuild candidates and their preconditions.

Why this change:
- The accepted PR #43 disposition remains useful, but the active backlog should
  not point future work at groups already rebuilt or closed.
- Narrowing the task reduces the risk of reviving stale branch code or mixing
  unrelated runtime surfaces in one PR.

Expected outcome:
- Future PR #43 follow-up starts from a single scoped candidate: AI alerting,
  managed multi-symbol runtime, or safe-pipeline wrapper/startup hardening.
- No runtime, campaign, gate, strategy, dashboard, or execution behavior
  changes.

Verification:
- SHOWN: source-existence check found the supervised-soak report/test present
  and the AI alert/oversight, managed-symbol, and safe-pipeline source files
  absent.
- SHOWN: `git diff --check` passed.
- Tests not run: documentation-only backlog/status alignment.

Remaining risk:
- HIGH: future implementation of any remaining PR #43 rebuild candidate may
  affect background jobs, runtime supervision, startup topology,
  multi-symbol campaign ownership, or operator alerting. This change is
  planning-only.
- Acceptance state: `ACCEPTED`.

## 2026-06-24T03:06:33Z - Correct PR #3 Closure Wording

Active role: ENGINEER

Objective:
- Remove stale present-tense wording from the completed PR #3 cleanup
  checkpoint after the PR #3, PR #42, and PR #43 disposition paths were already
  closed.

What was found:
- SHOWN: Priority 18 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` had status
  `complete as of 2026-06-19; PR #3 closed after accepted disposition`.
- SHOWN: the same Priority 18 section still said "PR #3 is still open" in
  "Why it matters."
- SHOWN: the same section still said "only PR #42 and PR #43 remain open after
  the closure check," which was stale after the later accepted PR #43
  disposition closure.
- SHOWN: work-log entry `2026-06-19T02:17:25Z` recorded `gh pr view 3`
  returning `state=CLOSED` and `closed=true`.
- SHOWN: work-log entry `2026-06-19T17:01:53Z` recorded PR #43 and superseded
  PR #42 closure after accepted disposition.

What changed:
- Updated Priority 18 wording to describe PR #3 as a previously stale branch
  that was closed after accepted disposition.
- Replaced the stale "only PR #42 and PR #43 remain open" evidence with the
  current closure state.

Why this change:
- Completed stale-PR disposition work should not keep present-tense wording
  that implies an old branch is still open or mergeable.

Expected outcome:
- Future backlog audits treat PR #3/#42/#43 as closed disposition history, not
  active stale PR cleanup.
- No runtime, campaign, strategy, gate, execution, or GitHub state changes.

Verification:
- SHOWN: `git diff --check` passed.
- Tests not run: documentation-only wording correction.

Remaining risk:
- LOW: documentation correction only. Any old PR #3 execution/reconciliation
  idea still requires a fresh current-master gap and separate high-risk review
  before implementation.
- Acceptance state: `ACCEPTED`.

## 2026-06-24T03:15:09Z - Close Shadow Spread Fresh-Record Proof

Active role: ENGINEER

Objective:
- Close Priority 5's remaining observation gap after fresh public-OHLCV signal
  records were written with spread evidence while tick data was fresh.

What was found:
- SHOWN: `.cbp_state/data/evidence/es_daily_trend_v1/signal_2026-06-24.jsonl`
  exists.
- SHOWN: `wc -l` reported `9` records in the file.
- SHOWN: `rg -c '"spread_bps"'` returned `9`.
- SHOWN: `rg -c '"market_quality_reason": "ok"'` returned `9`.
- SHOWN: sampled records include `market_data_source=public_ohlcv`,
  `ohlcv_sample_mode=false`, `market_quality_ok=true`, fresh market bid/ask
  fields, `market_age_sec`, and `spread_bps`.

What changed:
- Added
  `docs/checkpoints/shadow_spread_fresh_record_proof_2026_06_24.md`.
- Updated Priority 5 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` from
  fresh-record verification pending to complete.
- Removed the fresh-record observation task from the active backlog in
  `REMAINING_TASKS.md` and added it under recently completed.

Why this change:
- The implementation was already accepted, but the repo still needed visible
  proof that a fresh evidence run actually stamped signal records with spread
  data.
- Closing only the observation gap preserves the separate requirement for a
  future shadow-stage campaign to collect its own signal logs.

Expected outcome:
- Future backlog work no longer repeats the accepted spread-stamping
  observation.
- Historical unstamped records remain insufficient as shadow proof.
- No strategy, gate, execution, campaign, or runtime behavior changes.

Verification:
- SHOWN: `wc -l .cbp_state/data/evidence/es_daily_trend_v1/signal_2026-06-24.jsonl`
  returned `9`.
- SHOWN: `rg -c '"spread_bps"' .cbp_state/data/evidence/es_daily_trend_v1/signal_2026-06-24.jsonl`
  returned `9`.
- SHOWN: `rg -c '"market_quality_reason": "ok"' .cbp_state/data/evidence/es_daily_trend_v1/signal_2026-06-24.jsonl`
  returned `9`.
- SHOWN: `git diff --check` passed.
- Tests not run: documentation-only proof/status update.

Remaining risk:
- MEDIUM: this proves paper-stage fresh spread stamping, not future
  shadow-stage readiness or profitability.
- Acceptance state: `ACCEPTED`.

## 2026-06-24T03:22:53Z - Composite Hybrid Wrapper Design

Active role: ENGINEER

Objective:
- Capture a governed design for combining strategies before any composite or
  hybrid strategy implementation starts.

What was found:
- SHOWN: `services/strategies/strategy_registry.py` dispatches exactly one
  configured strategy name through `compute_signal()`.
- SHOWN: `services/backtest/leaderboard.py` evaluates individual strategy
  candidates through `run_parity_backtest()`.
- SHOWN: the existing leaderboard candidate list includes individual
  `ema_cross`, `breakout_donchian`, `pullback_recovery`, and
  `sma_200_trend` candidates, but no composite wrapper candidate.
- SHOWN: `docs/checkpoints/candidate_layer_read_only_activation_objective_2026_06_22.md`
  keeps the candidate layer read-only and confirms
  `use_candidate_advisor: false`.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`.
- SHOWN: `docs/checkpoints/pullback_recovery_campaign_plan_2026_06_19.md`
  requires a post-fix Stage 0 proof before any persistent
  `pullback_recovery` campaign.

What changed:
- Added
  `docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md`.
- Updated `REMAINING_TASKS.md` so the active task is independent review of the
  wrapper design, not direct implementation.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to reference
  the review-ready design and keep `pullback_recovery` Stage 0 separate.

Why this change:
- Combining strategies is financial decision logic and should not be
  implemented ad hoc while evidence campaigns are still running.
- The design creates a deterministic backtest-first path with explicit
  boundaries around candidate rankings, exit precedence, strategy IDs, and
  evidence isolation.
- A confirmation-gate wrapper is recommended before weighted voting because it
  is narrower, easier to test, and less likely to mask exits.

Expected outcome:
- Future composite/hybrid work starts from a reviewed contract instead of
  directly wiring multiple strategies into production paths.
- No runtime, campaign, gate, order routing, candidate-advisor, short-side, or
  live behavior changes.

Verification:
- `git diff --check`
  - SHOWN: passed.
- Tests not run: documentation-only design and backlog alignment. No Python
  source, config, runtime path, gate logic, or campaign manifest was changed.

Remaining risk:
- HIGH: future implementation would affect financial strategy selection and
  potentially paper, shadow, sandbox, or live behavior.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-24 in the Codex session after draft PR #119 checks
  passed.

## 2026-06-24T03:32:00Z - Accept Composite Hybrid Wrapper Design

Active role: ENGINEER

Objective:
- Record human acceptance of the composite/hybrid strategy wrapper design and
  move the backlog to the first implementation-proof step.

What was found:
- SHOWN: PR #119 was open as a draft PR from `review-stabilized` into
  `master`.
- SHOWN: PR #119 checks reported 7 passing checks.
- SHOWN: the local branch was clean and synced with `origin/review-stabilized`
  before this acceptance update.
- SHOWN: `make status-paper-soak` reported both laptop campaigns running.
- SHOWN: canonical `es_daily_trend_v1` gate progress remained `2/10`
  provenance-qualified round trips with `8` remaining.

What changed:
- Updated
  `docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md`
  from `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.
- Updated `REMAINING_TASKS.md` so the next composite/hybrid task is pure
  combiner tests before leaderboard, paper, or production activation.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to mark the
  design accepted and keep implementation staged.
- Updated the prior work-log entry with the human acceptance reference.

Why this change:
- The design was high risk and could not be accepted by the same implementation
  thread without human review.
- The human operator explicitly provided `INDEPENDENTLY_REVIEWED AND ACCEPTED`.
- The next safe step is isolated combiner proof, not runtime activation.

Expected outcome:
- PR #119 can be moved out of draft after this acceptance update.
- Future implementation remains constrained to pure combiner tests first.
- No campaign, gate, order routing, candidate-advisor, short-side, or live
  behavior changes.

Verification:
- `make status-paper-soak`
  - SHOWN: `Campaigns: 2/2 running`, `es_daily_trend_v1` at `2/10`
    provenance-qualified round trips, and `manual_review_required=True`.
- `gh pr checks 119`
  - SHOWN: 7 checks passing before this acceptance update.
- `git diff --check`
  - SHOWN: passed.
- Tests not run: documentation-only acceptance/status update. No source,
  config, gate, campaign, or runtime behavior was changed.

Remaining risk:
- HIGH: future composite/hybrid implementation remains financial strategy
  logic and must stay review-gated before any paper, shadow, sandbox, or live
  activation.
- Acceptance state: `ACCEPTED`.

## 2026-06-26T04:03:07Z - Composite Hybrid Pure Combiner Proof

Active role: ENGINEER

Objective:
- Implement the accepted composite/hybrid wrapper's first proof step as a pure
  confirmation-gate combiner with targeted tests, without registering it as a
  runtime strategy.

What was found:
- SHOWN: `docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md`
  is accepted and requires pure combiner tests before parity backtest
  integration.
- SHOWN: `services/strategies/strategy_registry.py` registers individual
  strategies only; no composite strategy is registered.
- SHOWN: `REMAINING_TASKS.md` says the next composite/hybrid step is pure
  combiner tests and explicitly blocks leaderboard, paper, and production path
  activation before review.

What changed:
- Added `services/strategies/composite_hybrid.py` with a pure Mode A
  confirmation-gate combiner.
- Added `tests/test_composite_hybrid.py` covering confirmed entries, blocked
  unconfirmed entries, long-exit precedence, risk-exit precedence, short-entry
  blocking, invalid child signals, and non-registration in the runtime
  strategy registry.
- Updated
  `docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md`
  with the pure-combiner proof status.
- Updated `REMAINING_TASKS.md` and Priority 13 so the next step is independent
  review before any parity backtest integration.

Why this change:
- The accepted design requires a deterministic combiner contract before any
  backtest, leaderboard, paper, or production integration.
- Keeping the function pure prevents accidental market-data access, candidate
  advisor activation, order routing, or evidence contamination.
- Tests explicitly prove `sell` remains a long exit and does not become a
  short entry.

Expected outcome:
- The repo now has a reviewable pure combiner proof for `composite_hybrid_v1`.
- No campaign, gate, leaderboard, candidate-advisor, paper, shadow, sandbox, or
  live behavior changes.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_composite_hybrid.py`
  - SHOWN: failed before test collection because the active `.venv` does not
    have `pytest` installed.
- `python3 -m pytest -q tests/test_composite_hybrid.py`
  - SHOWN: `8 passed in 0.09s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: this is financial strategy decision logic. It is isolated and
  unregistered, but follow-up backtest or runtime integration must remain
  review-gated.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-26 after PR #120 checks passed.

## 2026-06-26T04:18:49Z - Accept Composite Hybrid Pure Combiner Proof

Active role: ENGINEER

Objective:
- Record human acceptance of the composite/hybrid pure combiner proof and move
  the backlog to the next gated step.

What was found:
- SHOWN: PR #120 was open as a draft PR from `review-stabilized` into
  `master`.
- SHOWN: PR #120 checks reported 7 passing checks.
- SHOWN: the local branch was clean and synced with `origin/review-stabilized`
  before this acceptance update.
- SHOWN: the pure combiner remains unregistered in
  `services/strategies/strategy_registry.py`.

What changed:
- Updated
  `docs/checkpoints/composite_hybrid_strategy_wrapper_design_2026_06_24.md`
  to record the pure combiner proof as independently accepted.
- Updated `REMAINING_TASKS.md` so the next composite/hybrid task is
  research-only parity backtest integration, still review-gated before any
  leaderboard, paper, or production activation.
- Updated Priority 13 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to record
  pure-combiner acceptance and the next gated proof step.
- Updated the prior work-log entry from `READY_FOR_INDEPENDENT_REVIEW` to
  `ACCEPTED` with the human acceptance reference.

Why this change:
- The combiner proof was high risk and required human acceptance before moving
  beyond `READY_FOR_INDEPENDENT_REVIEW`.
- The next safe progression is parity backtest integration as research-only
  proof, not leaderboard registration or paper activation.

Expected outcome:
- PR #120 can be moved out of draft after this acceptance update.
- Future composite/hybrid implementation remains constrained to backtest proof
  before any campaign or production path.
- No source, campaign, gate, order routing, candidate-advisor, short-side, or
  live behavior changes in this acceptance update.

Verification:
- `gh pr checks 120`
  - SHOWN: 7 checks passing before this acceptance update.
- `git diff --check`
  - SHOWN: passed.
- Tests not run for this acceptance update: documentation-only status update.
  The implementation proof was already verified with
  `python3 -m pytest -q tests/test_composite_hybrid.py` showing
  `8 passed in 0.09s`.

Remaining risk:
- HIGH: future parity backtest integration is still financial strategy logic
  and must stop for independent review before any leaderboard, paper, shadow,
  sandbox, or live activation.
- Acceptance state: `ACCEPTED`.

## 2026-06-26T19:27:21Z - Composite Hybrid Research Parity Proof

Active role: ENGINEER

Objective:
- Add research-only parity backtest integration for the accepted
  `composite_hybrid_v1` confirmation-gate combiner without registering it for
  runtime strategy dispatch.

What was found:
- SHOWN: `services/backtest/parity_engine.py` feeds expanding OHLCV windows
  into `strategy_registry.compute_signal()`.
- SHOWN: the accepted pure combiner lives in
  `services/strategies/composite_hybrid.py`.
- SHOWN: `services/strategies/strategy_registry.py` does not register
  `composite_hybrid_v1`.
- SHOWN: the accepted design says parity backtest integration is the next step
  after pure combiner acceptance.

What changed:
- Updated `services/backtest/parity_engine.py` to support explicit
  `composite_hybrid_v1` configs in research backtests.
- Composite backtests compute child signals through the existing registry
  path, then pass those child signals into the pure confirmation-gate combiner.
- Preserved the SMA-200 flat-signal backtest exit translation for both
  top-level `sma_200_trend` and SMA child signals inside the composite wrapper.
- Added `tests/test_composite_hybrid_parity.py`.
- Updated the composite design checkpoint, Priority 13, active backlog, and
  work log to mark the parity proof ready for independent review.

Why this change:
- The accepted design requires the wrapper to prove backtest compatibility
  before any leaderboard row, paper campaign, or production wiring.
- Keeping the integration inside `services/backtest/parity_engine.py` avoids
  runtime strategy registration and keeps this proof research-only.
- Testing with monkeypatched child signals verifies the orchestration contract
  without relying on market-data fixture luck.

Expected outcome:
- Operators can evaluate an explicit `composite_hybrid_v1` config through the
  parity backtest path for research.
- The wrapper remains unavailable to normal runtime strategy selection.
- No campaign, gate, leaderboard, candidate-advisor, paper, shadow, sandbox, or
  live behavior changes.

Verification:
- `python3 -m pytest -q tests/test_composite_hybrid.py tests/test_composite_hybrid_parity.py tests/test_backtest_parity_engine.py`
  - SHOWN: `17 passed in 0.26s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: this is financial strategy decision logic. It is research-only and
  unregistered, but any leaderboard row, paper campaign, or production wiring
  must remain independently reviewed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-26 after PR #121 checks passed; merged to `master` as
  `7ab2cb66a`.

## 2026-06-26T19:37:00Z - Paper Gate Qualification Diagnostic

Active role: ENGINEER

Objective:
- Add a read-only operator diagnostic that explains why the paper promotion
  gate reports `2/10` provenance-qualified round trips while all-history paper
  history reports more closed trades.

What was found:
- SHOWN: `scripts/check_promotion_gates.py` computes the round-trip gate
  through `_paper_history_gate_summary(...)`, which delegates to
  `services.control.paper_evidence_qualification.qualify_paper_history(...)`.
- SHOWN: the canonical gate expects fill provenance:
  `market_data_source=public_ohlcv`, `ohlcv_sample_mode=false`,
  `ohlcv_timeframe=1d`, `ohlcv_venue=coinbase`, and
  `ohlcv_symbol=BTC/USDT`.
- SHOWN: current canonical evidence has `14` JSONL fills, `5` fills with
  matching provenance, `4` fills that form complete qualified round trips, and
  `2` provenance-qualified closed round trips.
- SHOWN: the `9` rejected legacy fills are dated 2026-04-20, 2026-05-15, and
  2026-05-18 and lack all required market-data provenance fields.
- SHOWN: the 2026-05-26 qualified sell fill does not count because its entry
  leg was from an unqualified pre-provenance cycle.

What changed:
- Added `services/control/paper_gate_qualification_report.py`.
- Added `scripts/report_paper_gate_qualification.py`.
- Added `make status-paper-gate-qualification` and
  `make status-paper-gate-qualification-json`.
- Added `tests/test_paper_gate_qualification_report.py`.
- Documented the new read-only diagnostic in `scripts/SCRIPTS.md`.

Why this change:
- The existing status output gives aggregate counts but does not list each fill
  with its count/reject/incomplete reason.
- A fill-level report lets operators distinguish strategy inactivity from
  provenance filtering without weakening the promotion gate or backfilling old
  unqualified history.

Expected outcome:
- Operators can run one read-only command to see exactly which fills count
  toward the gate and why other fills do not.
- No promotion threshold, qualification rule, campaign, order routing, journal,
  or evidence-writing behavior changes.

Verification:
- `python3 -m pytest -q tests/test_paper_gate_qualification_report.py`
  - SHOWN: `2 passed in 0.13s`.
- `python3 -m py_compile services/control/paper_gate_qualification_report.py scripts/report_paper_gate_qualification.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: passed.
- `make status-paper-gate-qualification`
  - SHOWN: report returned `qualified=2`, `all_history=9`, `counted=4`,
    `incomplete=1`, `rejected=9`, and listed each rejected/incomplete/counting
    fill with exact reasons.

Remaining risk:
- MEDIUM: this is read-only gate observability. It does not change gate logic,
  but future operators could still misread all-history trades as promotion
  progress unless they use the qualification status.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-26 after PR #122 checks passed; merged to `master` as
  `99c54b09d`.

## 2026-06-26T20:01:29Z - Accept Merged Composite And Gate Diagnostic Work

Active role: ENGINEER

Objective:
- Correct visible governance records after human acceptance and merge of the
  composite parity proof and paper-gate qualification diagnostic.

What was found:
- SHOWN: PR #121 merged the composite parity proof to `master` as `7ab2cb66a`
  after human operator acceptance.
- SHOWN: PR #122 merged the paper-gate qualification diagnostic to `master` as
  `99c54b09d` after human operator acceptance.
- SHOWN: the checkpoint, active backlog, and work log still described the
  composite parity proof as pending independent review.
- SHOWN: the work log still described the paper-gate diagnostic as
  `READY_FOR_INDEPENDENT_REVIEW`.

What changed:
- Updated the composite design checkpoint to mark parity backtest integration
  complete and independently accepted.
- Updated Priority 13 and `REMAINING_TASKS.md` so the next composite step is a
  research-only leaderboard row, not review of already-accepted parity proof.
- Updated prior work-log entries for PR #121 and PR #122 from
  `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED` with merge references.

Why this change:
- Governance records must match the actual accepted repository state before
  starting the next implementation stage.
- Leaving accepted merged work marked as awaiting review creates false blockers
  and weakens the work log as an audit artifact.

Expected outcome:
- Operators see the correct current state: parity proof and gate diagnostic are
  accepted; the next composite task is only the research leaderboard row.
- No source, runtime, strategy, campaign, gate, or deployment behavior changes.

Verification:
- `git diff --check`
  - SHOWN: passed.
- Tests were not run because this is a docs-only governance correction.

Remaining risk:
- LOW: documentation/governance-only change. It records existing human
  acceptance and does not change behavior.
- Acceptance state: `ACCEPTED`.

## 2026-06-26T20:07:52Z - Composite Hybrid Research Leaderboard Row

Active role: ENGINEER

Objective:
- Add the accepted `composite_hybrid_v1` confirmation-gate wrapper as a
  research-only default leaderboard candidate without registering it for runtime
  strategy dispatch or campaign use.

What was found:
- SHOWN: `services/backtest/leaderboard.py` owns the default aggregate
  leaderboard candidate set.
- SHOWN: `services/backtest/parity_engine.py` already supports explicit
  `composite_hybrid_v1` configs in research backtests.
- SHOWN: `services/strategies/strategy_registry.py` does not register
  `composite_hybrid_v1`.
- SHOWN: the accepted composite checkpoint says the next permitted stage is a
  research-only leaderboard row after parity proof acceptance.

What changed:
- Added `COMPOSITE_HYBRID_RESEARCH_CANDIDATE` to
  `services/backtest/leaderboard.py`.
- Added a research-only config builder that combines `breakout_donchian` as the
  primary child and `sma_200_trend` as the confirmer child in confirmation-gate
  mode.
- Added that candidate to `default_strategy_candidates(...)`.
- Updated leaderboard tests to prove the candidate appears in leaderboard
  output and remains absent from runtime strategy registry.
- Updated checkpoint/backlog docs to mark the row ready for independent review.

Why this change:
- The composite wrapper needed a controlled comparison surface before any
  persistent paper campaign or production path.
- Keeping the row inside the backtest leaderboard avoids adding a general
  runtime preset, strategy-registry entry, paper campaign, or order-routing
  behavior.

Expected outcome:
- Aggregate research evidence can compare the composite candidate against its
  child strategies using the existing backtest leaderboard machinery.
- Runtime strategy selection, paper campaigns, promotion gates, and execution
  paths remain unchanged.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py`
  - SHOWN: failed before executing tests because the repo venv did not have
    `pytest` installed.
- `python3 -m pytest -q tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py`
  - SHOWN: `10 passed in 0.44s`.
- `python3 -m py_compile services/backtest/leaderboard.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: this affects financial strategy research ranking. The implementation is
  research-only and unregistered for runtime, but any persistent paper campaign,
  shadow, sandbox, live, promotion, or order-routing use must remain separately
  reviewed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-26 after PR #124 checks passed.

## 2026-06-26T20:19:33Z - Accept Composite Hybrid Research Leaderboard Row

Active role: GATE

Objective:
- Record human acceptance of the high-risk composite/hybrid research leaderboard
  row before merging PR #124.

What was found:
- SHOWN: PR #124 checks passed: macOS build, Windows build, CI sanity, CI
  validate, GitGuardian, and both governance smoke jobs.
- SHOWN: the work log and checkpoints still described the row as pending
  independent review.
- SHOWN: the human operator provided `INDEPENDENTLY_REVIEWED AND ACCEPTED` in
  the Codex session.

What changed:
- Updated the composite checkpoint, Priority 13, active backlog, and work log to
  mark the research leaderboard row accepted.
- Updated the next action to leaderboard comparison evidence review, while
  preserving the block on persistent paper, shadow, sandbox, live, promotion, or
  order-routing use.

Why this change:
- The accepted implementation should not be merged with stale
  `READY_FOR_INDEPENDENT_REVIEW` governance text.
- The next risk boundary is not implementation of the row; it is whether the
  row's comparison evidence justifies any later campaign.

Expected outcome:
- PR #124 can merge with governance records already aligned.
- Operators see the correct next task: compare the composite against child
  strategies before any runtime or campaign expansion.

Verification:
- `gh pr checks 124`
  - SHOWN: all 7 checks passed.
- `git diff --check`
  - SHOWN: passed.
- Tests were not rerun for this docs-only acceptance update.

Remaining risk:
- MEDIUM: governance/status-only update for high-risk strategy research work.
  It records human acceptance but does not change source behavior.
- Acceptance state: `ACCEPTED`.

## 2026-06-27T23:52:01Z - Composite Hybrid Leaderboard Comparison Evidence

Active role: ENGINEER

Objective:
- Generate read-only comparison evidence for the accepted
  `composite_hybrid_v1_breakout_sma200_research` leaderboard row.

What was found:
- SHOWN: `run_strategy_evidence_cycle(...)` can build aggregate synthetic
  leaderboard evidence without starting a paper campaign.
- SHOWN: the comparison artifact was written to
  `/private/tmp/composite_hybrid_leaderboard_comparison_20260627.json`.
- SHOWN: the composite candidate ranked `5/10`, with decision `freeze`,
  evidence status `insufficient`, and `0` closed trades.
- SHOWN: every default evidence window had fewer than `200` bars.
- SHOWN: `services/strategies/es_daily_trend.py` returns `hold` with reason
  `insufficient_history` when the bar count is below `sma_period`.

What changed:
- Added
  `docs/checkpoints/composite_hybrid_leaderboard_comparison_2026_06_27.md`.
- Updated the composite design checkpoint, Priority 13, and active backlog to
  point at the comparison checkpoint for independent review.

Why this change:
- The accepted leaderboard row needed comparison evidence before any paper
  campaign or production path could be considered.
- The first comparison result should be preserved as a visible audit artifact
  because it blocks paper advancement for the current composite definition.

Expected outcome:
- Reviewers can see that the current composite row has no realized
  participation and should not advance to paper.
- The next strategy work should either add a longer research-only evidence
  window or define a separate shorter-confirmer composite candidate.

Verification:
- `./.venv/bin/python` generated the temp evidence artifact successfully.
- `git diff --check`
  - SHOWN: passed.
- Tests were not run because this is a docs-only evidence checkpoint.

Remaining risk:
- HIGH: this is financial strategy comparison evidence. It is read-only and
  does not change source behavior, but it can influence future campaign
  selection.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-27 after PR #125 checks passed.

## 2026-06-27T23:57:38Z - Accept Composite Hybrid Comparison Evidence

Active role: GATE

Objective:
- Record human acceptance of the read-only composite/hybrid leaderboard
  comparison checkpoint before merging PR #125.

What was found:
- SHOWN: PR #125 checks passed: macOS build, Windows build, CI sanity, CI
  validate, GitGuardian, and both governance smoke jobs.
- SHOWN: the comparison checkpoint concluded that the current composite
  candidate should not advance to paper because it produced no realized
  participation.
- SHOWN: the human operator provided `INDEPENDENTLY_REVIEWED AND ACCEPTED` in
  the Codex session.

What changed:
- Updated the comparison checkpoint, composite design checkpoint, Priority 13,
  active backlog, and work log to mark the comparison evidence accepted.
- Updated the next action to either add a longer research-only evidence window
  or define a separate shorter-confirmer variant before any paper expansion.

Why this change:
- The accepted evidence should not merge with stale
  `READY_FOR_INDEPENDENT_REVIEW` text.
- The accepted conclusion is a blocker: the current composite definition has no
  realized participation and should not advance to paper.

Expected outcome:
- PR #125 can merge with governance records aligned.
- Future composite work stays research-only until it produces accepted
  comparison evidence with realized participation.

Verification:
- `gh pr checks 125`
  - SHOWN: all 7 checks passed.
- `git diff --check`
  - SHOWN: passed.
- Tests were not rerun for this docs-only acceptance update.

Remaining risk:
- MEDIUM: governance/status-only update for high-risk strategy comparison
  evidence. It records human acceptance and does not change source behavior.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T00:07:28Z - Composite Hybrid Long Window Research Proof

Active role: ENGINEER

Objective:
- Add one research-only evidence window long enough for the accepted
  `composite_hybrid_v1_breakout_sma200_research` candidate to exercise its
  `sma_200_trend` confirmer.

What was found:
- SHOWN: the accepted PR #125 comparison had zero composite participation
  because the default windows had fewer than `200` bars.
- SHOWN: `sma_200_trend` needs `200` bars for SMA history and additional
  ATR/regime history before entries can be allowed.
- SHOWN: a 320-bar long trend/reversal synthetic window produces one closed
  composite round trip.

What changed:
- Added `long_trend_confirmation` to `default_evidence_windows()` in both
  `services/backtest/evidence_cycle.py` and
  `services/backtest/evidence_windows.py`.
- Added tests proving both window sources include the long window and that the
  composite candidate produces a closed trade in that window.
- Added
  `docs/checkpoints/composite_hybrid_long_window_research_proof_2026_06_27.md`
  and updated the active backlog/checkpoints.

Why this change:
- The accepted comparison showed the current composite could not be judged
  fairly using only short windows.
- A longer research-only window is the smallest change that tests the existing
  200-SMA confirmer without adding a new strategy variant or paper campaign.

Expected outcome:
- Future evidence cycles can compare the composite candidate after the
  confirmer has enough history to participate.
- The candidate remains blocked from paper until accepted comparison evidence
  exists across at least three realized synthetic windows.

Verification:
- `python3 -m pytest -q tests/test_backtest_evidence_cycle.py tests/test_backtest_leaderboard.py tests/test_composite_hybrid_parity.py`
  - SHOWN: `26 passed in 1.86s`.
- `python3 -m py_compile services/backtest/evidence_cycle.py services/backtest/evidence_windows.py tests/test_backtest_evidence_cycle.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python` generated
  `/private/tmp/composite_hybrid_leaderboard_comparison_long_window_20260627.json`.
  - SHOWN: composite rank `3/10`, `1` closed trade, `2.0568%` net return after
    costs, decision `freeze`, evidence status `synthetic_only`, acceptance
    `false`.

Remaining risk:
- HIGH: this changes financial strategy research evidence and future aggregate
  leaderboard results. It does not add runtime registration, paper campaigns,
  promotion behavior, or order routing.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-28 after PR #126 checks passed.

## 2026-06-28T00:21:55Z - Accept Composite Hybrid Long Window Research Proof

Active role: GATE

Objective:
- Record human acceptance of the high-risk composite/hybrid long-window
  research proof before merging PR #126.

What was found:
- SHOWN: PR #126 checks passed: macOS build, Windows build, CI sanity, CI
  validate, GitGuardian, and both governance smoke jobs.
- SHOWN: the long-window proof fixed the mechanical warmup/participation gap by
  producing one closed synthetic composite round trip.
- SHOWN: the proof still blocks paper advancement because evidence remains
  synthetic-only, low confidence, and represented in only one realized window.
- SHOWN: the human operator provided `INDEPENDENTLY_REVIEWED AND ACCEPTED` in
  the Codex session.

What changed:
- Updated the long-window checkpoint, composite comparison checkpoint, composite
  design checkpoint, Priority 13, active backlog, and work log to mark the proof
  accepted.
- Updated the next action to add more long-window research variants until the
  candidate has comparison evidence across at least three realized synthetic
  windows.

Why this change:
- The accepted proof should not merge with stale `READY_FOR_INDEPENDENT_REVIEW`
  text.
- The accepted result improves research fairness but remains insufficient for
  paper expansion.

Expected outcome:
- PR #126 can merge with governance records aligned.
- Future composite work remains research-only and focused on additional
  realized synthetic windows before any paper campaign is reconsidered.

Verification:
- `gh pr checks 126`
  - SHOWN: all 7 checks passed.
- `git diff --check`
  - SHOWN: passed.
- Tests were not rerun for this docs-only acceptance update.

Remaining risk:
- MEDIUM: governance/status-only update for high-risk strategy research
  evidence. It records human acceptance and does not change source behavior.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T10:33:21Z - Surface Paper Gate Qualification Timestamps In Soak Status

Active role: ENGINEER

Objective:
- Make the routine laptop paper-soak status output explain why the paper gate
  has not advanced when all-history closed trades differ from
  provenance-qualified round trips.

What was found:
- SHOWN: `scripts/report_paper_gate_qualification.py --json` reported
  `all_history_round_trips=9`, `qualified_round_trips=2`,
  `counted_evidence_fills=4`, `incomplete_evidence_fills=1`, and
  `rejected_evidence_fills=9`.
- SHOWN: the rejected fills are dated 2026-04-20, 2026-05-15, and 2026-05-18
  and are missing market-data source, sample-mode, timeframe, venue, and symbol
  provenance.
- SHOWN: the only counted qualified round trips closed on 2026-06-18 and
  2026-06-24.
- SHOWN: the latest all-history fill is also 2026-06-24, so the current plateau
  is explained by no newer qualifying `sma_200_trend` close, not by a hidden
  gate counting defect.

What changed:
- `scripts/report_supervised_soak_status.py` now includes paper-history and
  qualification details from `check_promotion_gates.py` in its JSON payload.
- The human-readable soak report now prints qualified closed trades,
  all-history closed trades, latest all-history fill, counted/rejected/incomplete
  evidence fills, and latest qualified close timestamp.
- `tests/test_report_supervised_soak_status.py` now covers those added fields.

Why this change:
- The daily `make status-paper-all` check-in is the operator's primary surface.
  It should show whether gate progress is waiting on new market behavior or
  blocked by provenance qualification, without requiring a separate diagnostic
  command.
- This preserves the accepted provenance policy and changes reporting only.

Expected outcome:
- Future check-ins make the `2/10` qualified gate state easier to interpret.
- Operators can see that old all-history trades remain diagnostic-only while
  future provenance-complete entry/exit cycles are the path to progress.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_supervised_soak_status.py tests/test_report_supervised_soak_status.py`
  - SHOWN: passed.
- `./.venv/bin/python scripts/report_supervised_soak_status.py --config configs/paper_evidence_campaigns.laptop.json`
  - SHOWN: output includes `paper history: qualified_closed=2
    all_history_closed=9 latest_all_history_fill=2026-06-24T00:04:01.768973+00:00`.
  - SHOWN: output includes `qualification: counted_fills=4/14 incomplete=1
    rejected=9 latest_qualified_close=2026-06-24T00:04:01.770530+00:00`.
- `git diff --check`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_supervised_soak_status.py`
  - NOT RUN TO COMPLETION: local `.venv` reported `No module named pytest`.
- Full test suite was not run per operator constraint against long test runs.

Remaining risk:
- LOW: reporting-only change. It does not change qualification rules,
  promotion thresholds, campaign execution, financial logic, or order routing.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T10:46:28Z - Refresh Active Backlog After Paper Status Visibility Merge

Active role: ENGINEER

Objective:
- Keep the visible active backlog aligned after PR #126 and PR #127 merged.

What was found:
- SHOWN: `master`, `origin/master`, and `origin/review-stabilized` were aligned
  at `845a4259019295a8a4cd5263b52a9a5a52a6d068` after PR #127 merged.
- SHOWN: `REMAINING_TASKS.md` still said the branches were aligned only through
  PR #124.
- SHOWN: the latest local paper-soak status reported `es_daily_trend_v1`
  `fills=18`, `closed=9`, `pnl=32.1776` and `breakout_default` `fills=11`,
  `closed=5`, `pnl=-4.1182`.
- SHOWN: PR #127 added compact paper-history qualification details to the daily
  soak status output.

What changed:
- Updated `REMAINING_TASKS.md` current-state text from PR #124 to PR #127.
- Refreshed the visible laptop campaign figures for `breakout_default`.
- Added the PR #127 paper-soak qualification visibility outcome to the current
  state and recently-completed list.
- Added the accepted PR #126 composite/hybrid long-window research proof to the
  recently-completed list.

Why this change:
- The active backlog is the operator's first orientation surface. Keeping it
  stale after accepted merges recreates the branch/status confusion this repo
  has been actively removing.

Expected outcome:
- Future proactive work starts from the correct state: branches aligned through
  PR #127, paper gate still blocked at `2/10`, and daily status output now
  includes qualification visibility.

Verification:
- `git diff --check`
  - SHOWN: passed.
- No tests were run because this is a documentation-only backlog refresh.

Remaining risk:
- LOW: documentation-only status refresh. It does not change runtime behavior,
  gate policy, strategy logic, or operator commands.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T10:52:31Z - Scope PR43 AI Operator Oversight Rebuild

Active role: ENGINEER

Objective:
- Convert the remaining PR #43 AI operator alerting/oversight rebuild candidate
  into a current-master scoped objective before any implementation.

What was found:
- SHOWN: `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`
  requires a scoped objective before implementing any remaining PR #43 rebuild
  group.
- SHOWN: current source still lacks the old PR #43 AI alert/oversight files:
  `scripts/run_ai_alert_monitor.py`, `scripts/run_ai_oversight_watch.py`,
  `services/ai_copilot/alert_monitor.py`, and
  `services/ai_copilot/oversight_watch.py`.
- SHOWN: current source has the accepted paper simulation monitor at
  `scripts/run_paper_sim_monitor.py` and
  `services/analytics/paper_sim_monitor.py`.
- SHOWN: `./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  reported four active watches: `next_fill`, `position_closed`,
  `campaign_completed`, and `investigate`.
- SHOWN: the same monitor status reported recent watch reports with
  `desktop_notification.sent=true`, plus promotion-progress and
  provenance-qualification context.
- SHOWN: `services/alerts/alert_dispatcher.py` and
  `services/alerts/alert_router.py` provide lower-level alert primitives, but
  not a paper-campaign oversight product by themselves.

What changed:
- Added
  `docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md`.
- Updated `REMAINING_TASKS.md` to point PR #43 AI operator oversight at a
  read-only one-shot synthesis report over existing monitor/watch/gate
  artifacts, not a second background monitor.
- Updated `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`.
- Updated Priority 9 in
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`.

Why this change:
- The current paper-sim monitor is already the wake-up layer. Rebuilding a
  second background alert monitor from stale PR #43 code would duplicate state
  ownership and risk contradictory operator guidance.
- A scoped objective keeps the useful AI oversight idea while requiring any
  future implementation to remain read-only, one-shot, and based on current
  artifacts.

Expected outcome:
- Future PR #43 follow-through starts from a narrow current-master objective.
- The next implementation, if pursued, builds advisory synthesis instead of
  duplicating monitor/notification ownership.

Verification:
- `./.venv/bin/python scripts/run_paper_sim_monitor.py --status`
  - SHOWN: returned current monitor status with active watches, recent watch
    reports, desktop notification results, and gate qualification context.
- `git diff --check`
  - SHOWN: passed.
- Tests were not run because this is a documentation/planning-only change.

Remaining risk:
- LOW: planning-only change. It does not modify runtime behavior, background
  jobs, strategy logic, order routing, promotion gates, or alert dispatch.
- Future implementation of operator oversight remains HIGH risk and must be
  independently reviewed if it affects background jobs, notifications, or
  financial operator decisions.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T11:05:47Z - Implement Read-Only AI Operator Oversight Report

Active role: ENGINEER

Objective:
- Implement the accepted PR #43 AI operator oversight objective as a one-shot,
  read-only synthesis report over existing monitor/watch/gate artifacts.

What was found:
- SHOWN: the accepted objective requires a read-only one-shot report, not a
  second background monitor.
- SHOWN: `scripts/run_paper_sim_monitor.py --status` already exposes active
  watches, recent watch reports, desktop notification outcomes, and paper-gate
  qualification context.
- SHOWN: `services/alerts/alert_dispatcher.py` and
  `services/alerts/alert_router.py` are lower-level alert primitives, not a
  paper-campaign oversight product by themselves.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` still has
  `use_candidate_advisor: false`.

What changed:
- Added `services/ai_copilot/operator_oversight.py`.
- Added `scripts/run_ai_operator_oversight.py`.
- Added `tests/test_ai_copilot_operator_oversight.py`.
- Added `tests/test_run_ai_operator_oversight.py`.
- Added `make ai-operator-oversight`.
- Updated `scripts/SCRIPTS.md`, `docs/ARCHITECTURE.md`,
  `REMAINING_TASKS.md`, `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`,
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md`, and
  `docs/checkpoints/pr43_ai_operator_oversight_rebuild_objective_2026_06_28.md`.

Why this change:
- The paper-sim monitor is already the accepted wake-up layer. The missing
  piece is advisory synthesis for the operator, using existing facts without
  duplicating background monitoring or notification ownership.
- Defaulting to machine-only output avoids network/API dependency and makes the
  command deterministic unless the operator explicitly passes `--use-ai`.

Expected outcome:
- Operators get one root command that summarizes current monitor, watch, and
  paper-gate facts into action items.
- The report writes durable JSON/Markdown artifacts under
  `.cbp_state/runtime/ai_reports/`.
- Missing monitor status, missing watch reports, investigate watches, and
  paper-gate blockers are surfaced explicitly.

Verification:
- `./.venv/bin/python -m py_compile services/ai_copilot/operator_oversight.py scripts/run_ai_operator_oversight.py tests/test_ai_copilot_operator_oversight.py tests/test_run_ai_operator_oversight.py`
  - SHOWN: passed.
- `./.venv/bin/python scripts/run_ai_operator_oversight.py --no-write`
  - SHOWN: returned `status=investigate`, `watch_report_status=available`,
    `read_only=True`, and `ai_summary_status=machine_only` against current
    local state.
- `CBP_STATE_DIR=/private/tmp/cbp-operator-oversight-proof ./.venv/bin/python scripts/run_ai_operator_oversight.py --json`
  - SHOWN: wrote latest and dated JSON/Markdown artifacts under
    `/private/tmp/cbp-operator-oversight-proof/runtime/ai_reports/`.
  - SHOWN: returned safety flags with no background monitor start, no watch
    mutation, no external notification dispatch, no gate mutation, no order
    routing, and no live execution touch.
- `git diff --check`
  - SHOWN: passed.
- `rg -n "use_candidate_advisor:" configs/strategies/es_daily_trend_v1.yaml`
  - SHOWN: `use_candidate_advisor: false`.
- `./.venv/bin/python -m pytest -q tests/test_ai_copilot_operator_oversight.py tests/test_run_ai_operator_oversight.py`
  - NOT RUN TO COMPLETION: local `.venv` reported `No module named pytest`.
- Full test suite was not run per operator constraint against long test runs.

Remaining risk:
- HIGH: read-only implementation, but it creates operator guidance around
  financial strategy experimentation.
- No runtime/background job behavior, campaign control, promotion gate,
  strategy selection, alert dispatch, live execution, or order-routing behavior
  was changed.
- Acceptance state: `ACCEPTED`.
- Acceptance reference: independently reviewed and accepted by the human
  operator on 2026-06-28.

## 2026-06-28T11:24:47Z - Document AI Operator Oversight In Golden Path

Active role: ENGINEER

Objective:
- Align the narrow daily operator workflow documentation with the accepted
  read-only AI operator oversight command.

What was found:
- SHOWN: `make ai-operator-oversight` exists in `Makefile`.
- SHOWN: `scripts/SCRIPTS.md` documents `run_ai_operator_oversight.py` as a
  read-only one-shot advisory report.
- SHOWN: `docs/GOLDEN_PATH.md` documented `make status-paper-all` but did not
  explain where the accepted operator oversight report fits in the daily
  workflow.

What changed:
- Added an optional `make ai-operator-oversight` step after
  `make status-paper-all` in `docs/GOLDEN_PATH.md`.
- Documented that the command writes advisory reports under
  `.cbp_state/runtime/ai_reports/`.
- Documented the read-only boundary: no campaign start/stop, no watch or gate
  mutation, and no order routing.

Why this change:
- `docs/GOLDEN_PATH.md` is the narrow daily-path document. Adding the accepted
  command there prevents the operator from having to rediscover it from the
  larger script index while keeping the command clearly optional.

Expected outcome:
- Operators can run the daily status command first, then optionally generate a
  read-only synthesis report without confusing it for a campaign controller or
  promotion authority.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "make ai-operator-oversight|read-only operator synthesis|runtime/ai_reports|does not route orders" docs/GOLDEN_PATH.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: the Golden Path and work log contain the expected operator command,
    report path, and read-only boundary language.

Remaining risk:
- LOW: documentation-only workflow clarification. Runtime behavior, strategy
  logic, background jobs, gates, alerts, and order routing are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T11:45:13Z - Scope Managed Multi-Symbol Paper Runtime Rebuild

Active role: ENGINEER

Objective:
- Convert the remaining PR #43 managed multi-symbol paper-runtime rebuild group
  into a current-master scoped objective without changing runtime behavior.

What was found:
- SHOWN: `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  groups nine old PR #43 commits under managed multi-symbol paper runtime.
- SHOWN: current source lacks `services/runtime/managed_symbol_config.py` and
  `services/runtime/managed_symbol_selection.py`.
- SHOWN: current source already has explicit manifest-based multi-campaign
  status/restore through `services/analytics/paper_campaign_recovery.py`,
  `scripts/restore_paper_campaigns.py`, and the accepted laptop/Hetzner
  campaign manifests.
- SHOWN: the current manifests already provide per-campaign state isolation
  and host ownership for `es_daily_trend_v1`, `breakout_default`, and
  `ema_cross_default`.

What changed:
- Added
  `docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md`.
- Updated `REMAINING_TASKS.md`,
  `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`, and
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to point
  managed multi-symbol runtime work at the new read-only planner objective.
- Refreshed `REMAINING_TASKS.md` branch-alignment text through PR #131.

Why this change:
- The current repo already has an explicit multi-campaign manifest runtime. The
  missing product capability is not another autonomous starter; it is a
  reviewed way to propose future campaign rows while preserving state
  isolation, host ownership, and human control.
- A read-only planner is the smallest safe next boundary before any high-risk
  managed campaign runtime work.

Expected outcome:
- Future managed multi-symbol work starts from a precise objective: propose
  campaign rows only, reject unsafe duplicates, prove no manifest mutation, and
  require separate review before any campaign can be started.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `sed -n '1,260p' docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md`
  - SHOWN: the checkpoint defines a read-only planner, not an autonomous
    campaign starter.
- `rg -n "read-only|MUST NOT|MUST:|Proof Required|campaign proposal|autonomous|state directory|host ownership|use_candidate_advisor" docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md`
  - SHOWN: the checkpoint contains the expected read-only boundaries,
    proof requirements, duplicate/state isolation constraints, host ownership
    requirement, and candidate-advisor guard.

Remaining risk:
- LOW: planning-only documentation update. Runtime behavior, background jobs,
  campaign manifests, gates, strategy logic, live execution, and order routing
  are unchanged.
- Future implementation remains HIGH risk because it affects financial
  strategy experimentation, background job ownership, and evidence attribution.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T11:57:18Z - Scope Safe Pipeline Startup Hardening Rebuild

Active role: ENGINEER

Objective:
- Convert the remaining PR #43 safe-runtime-wrapper/startup-topology rebuild
  group into a current-master scoped objective without changing runtime
  behavior.

What was found:
- SHOWN: `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  groups nine old PR #43 commits under safe runtime wrappers and bot topology.
- SHOWN: current source lacks `scripts/run_pipeline_safe.py`.
- SHOWN: current source already has canonical operator controls:
  `scripts/start_bot.py`, `scripts/stop_bot.py`, and `scripts/bot_status.py`.
- SHOWN: `docs/CURRENT_RUNTIME_TRUTH.md`, `docs/PROCESS_CONTROL.md`, and
  `docs/BOT_CONTROL.md` identify those scripts as the canonical control plane
  and mark `scripts/run_bot_safe.py` as compatibility-only.
- SHOWN: current source already has several safe wrappers and tests covering
  safe-idle/startup behavior.

What changed:
- Added
  `docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md`.
- Updated `REMAINING_TASKS.md`,
  `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md`, and
  `docs/checkpoints/review_stabilized_next_actions_2026_05_28.md` to point
  safe-pipeline/startup work at the new read-only topology/gap audit objective.

Why this change:
- The current repo already has a canonical startup path and existing safe
  wrappers. Recreating `run_pipeline_safe.py` without a reproduced
  current-master gap would add another control surface and risk obscuring the
  runtime truth.
- A read-only audit report is the smallest safe boundary before any high-risk
  startup or fail-closed runtime change.

Expected outcome:
- Future startup-hardening work must first prove whether a current-master gap
  exists. Only a separate high-risk implementation PR may add a wrapper or
  change startup behavior.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `sed -n '1,260p' docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md`
  - SHOWN: the checkpoint defines a read-only topology/gap audit before any
    runtime behavior change.
- `rg -n "pr43_safe_pipeline_startup_hardening_objective|read-only startup topology|run_pipeline_safe|current-master gap|MUST NOT|Proof Required|canonical startup|safe wrappers" REMAINING_TASKS.md docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md docs/checkpoints/review_stabilized_next_actions_2026_05_28.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: the checkpoint and indexes contain the expected read-only audit,
    no-new-wrapper-by-default, proof, and current-master gap language.

Remaining risk:
- LOW: planning-only documentation update. Runtime behavior, background jobs,
  startup scripts, service definitions, gates, live execution, and order
  routing are unchanged.
- Future implementation remains HIGH risk because it affects startup topology,
  runtime supervision, and fail-closed behavior.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T18:25:16Z - Refresh Backlog After PR43 Scope Checkpoints

Active role: ENGINEER

Objective:
- Remove stale backlog wording after PR #132 and PR #133 scoped the final PR
  #43 rebuild candidates.

What was found:
- SHOWN: `review-stabilized`, `origin/review-stabilized`, and `origin/master`
  are aligned at `bc841c33bf9e7e7f0288efc74fc6ab107d66039c`.
- SHOWN: no open PRs are present.
- SHOWN: `REMAINING_TASKS.md` still said reviewed PRs were aligned only
  through PR #131.
- SHOWN: `REMAINING_TASKS.md` still summarized the PR #43 follow-up as if
  AI alerting, managed multi-symbol runtime, and safe-pipeline wrapper remained
  generic separate scoped candidates, even though AI oversight is accepted and
  the latter two now have explicit objective checkpoints.

What changed:
- Updated `REMAINING_TASKS.md` to say alignment is current through PR #133.
- Reworded the PR #43 recently-completed entry to say the follow-up is fully
  scoped, with managed multi-symbol runtime and safe-pipeline/startup hardening
  still implementation-open under their read-only objectives.
- Reworded `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` to
  distinguish implementation-open scoped candidates from unscoped rebuild
  work.

Why this change:
- The backlog is the operator-facing source for what remains. Leaving it at PR
  #131 and using stale PR #43 wording would make future work look less settled
  than it is.

Expected outcome:
- Future check-ins see the branch state through PR #133 and the remaining PR
  #43 work as scoped objectives, not broad undefined rebuilds.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "reviewed PRs through PR #131|AI alerting, managed multi-symbol runtime, and safe-pipeline wrapper remain|fully scoped|Implementation-open as separate scoped rebuild candidates|PR #133|bc841c33" REMAINING_TASKS.md docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: stale PR #131 and stale PR #43 summary wording are absent from
    active backlog text; replacement PR #133 and implementation-open scoped
    language are present.

Remaining risk:
- LOW: documentation-only backlog/status correction. Runtime behavior,
  background jobs, campaigns, gates, strategy logic, live execution, and order
  routing are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T18:32:39Z - Refresh Branch Alignment After PR134

Active role: ENGINEER

Objective:
- Keep the lightweight backlog index aligned with the latest merged PR while
  the operator's full pytest run proceeds separately.

What was found:
- SHOWN: `review-stabilized`, `origin/review-stabilized`, and `origin/master`
  are aligned at `a6acaaba507714ae092682d225f9109fa4183ea7`.
- SHOWN: no open PRs are present.
- SHOWN: `REMAINING_TASKS.md` still said reviewed PRs were aligned only
  through PR #133.

What changed:
- Updated `REMAINING_TASKS.md` to say reviewed PR alignment is current through
  PR #134.

Why this change:
- `REMAINING_TASKS.md` is the operator-facing backlog index. Leaving it one PR
  behind makes check-ins look stale even though the branches are aligned.

Expected outcome:
- Future check-ins see the current merge boundary without re-checking GitHub
  history.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "reviewed PRs through PR #13[34]|a6acaaba|Refresh Branch Alignment After PR134|operator's full pytest" REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: PR #134 alignment text and the work-log reference are present.

Remaining risk:
- LOW: documentation-only alignment correction. Runtime behavior, background
  jobs, campaigns, gates, strategy logic, live execution, tests, and order
  routing are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T18:39:28Z - Remove Fragile PR Number From Branch Alignment Backlog

Active role: ENGINEER

Objective:
- Stop `REMAINING_TASKS.md` from becoming stale after every accepted PR merge.

What was found:
- SHOWN: `review-stabilized`, `origin/review-stabilized`, and `origin/master`
  are aligned at `272465f8b3d2c97817c4fbfe26a5301cc9b65d11`.
- SHOWN: no open PRs are present.
- SHOWN: `REMAINING_TASKS.md` still said branch alignment was current through
  PR #134, which became stale immediately after PR #135 merged.

What changed:
- Replaced the specific "through PR #..." wording in `REMAINING_TASKS.md` with
  a stable instruction to verify the current boundary using
  `git rev-parse HEAD origin/master origin/review-stabilized`.

Why this change:
- Repeatedly updating a PR number creates self-inflicted backlog churn. The
  repo already has the authoritative branch state in git; the backlog should
  describe the alignment policy and verification command, not a per-merge
  number that must be edited after every PR.

Expected outcome:
- Future accepted PR merges no longer require a follow-up docs-only PR just to
  bump the latest PR number in the backlog.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "reviewed PRs through PR|git rev-parse HEAD origin/master origin/review-stabilized|Remove Fragile PR Number|272465f8" REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: active `REMAINING_TASKS.md` now uses the stable `git rev-parse`
    verification command. Remaining `reviewed PRs through PR...` matches are
    historical work-log entries, not active backlog instructions.

Remaining risk:
- LOW: documentation-only wording correction. Runtime behavior, background
  jobs, campaigns, gates, strategy logic, live execution, tests, and order
  routing are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T18:49:47Z - Implement Read-Only Startup Hardening Audit

Active role: ENGINEER

Objective:
- Implement the accepted PR #43 safe-pipeline/startup hardening objective as
  a read-only topology and gap audit, without changing runtime startup
  behavior.

What was found:
- SHOWN: `scripts/start_bot.py` is the canonical supervised startup surface.
- SHOWN: current startup commands include safe-wrapper services and three
  unwrapped commands: `pipeline`, `ops_signal_adapter`, and `ops_risk_gate`.
- SHOWN: `scripts/compat/run_pipeline_loop.py` can raise the
  `CBP_CONFIG_REQUIRED` runtime error before its first static `_write_status`
  call.
- SHOWN: `docs/STARTUP_STATUS_GATE.md` documents startup-status evidence as
  reconciliation evidence, not a current canonical launch gate.

What changed:
- Added `services/runtime/startup_hardening_audit.py` to build a static,
  read-only startup hardening report.
- Added `scripts/audit_startup_hardening.py` as the root CLI for the report.
- Added tests for topology parsing, safe-wrapper recognition, no service
  start/stop side effects, no pid/status-file writes, JSON no-write mode, and
  default artifact writing.
- Documented the CLI in `scripts/SCRIPTS.md` and
  `docs/CURRENT_RUNTIME_TRUTH.md`.
- Updated `REMAINING_TASKS.md` and the PR #43 startup checkpoint to mark the
  implementation proof ready for independent review.

Why this change:
- The accepted objective requires proving the current startup topology before
  considering any new wrapper or startup behavior change. A read-only report is
  the smallest safe implementation that produces machine-readable evidence
  without touching high-risk runtime behavior.

Expected outcome:
- Operators can run `python scripts/audit_startup_hardening.py` to generate a
  latest and dated startup-hardening audit under
  `.cbp_state/runtime/startup_audits/`.
- Any future startup wrapper/topology change must cite this report and still
  go through a separate high-risk review.

Verification:
- `./.venv/bin/python -m py_compile services/runtime/startup_hardening_audit.py scripts/audit_startup_hardening.py tests/test_startup_hardening_audit.py tests/test_audit_startup_hardening_script.py`
  - SHOWN: passed.
- `./.venv/bin/python scripts/audit_startup_hardening.py --no-write`
  - SHOWN: exited 0 and printed `gap_status=insufficient_evidence`,
    `read_only=True`, and warning actions for unwrapped startup commands and
    the pipeline pre-status config-error path.
- `CBP_STATE_DIR=/private/tmp/cbp-startup-audit-proof ./.venv/bin/python scripts/audit_startup_hardening.py --json`
  - SHOWN: exited 0 and wrote latest/dated JSON and Markdown artifacts under
    `/private/tmp/cbp-startup-audit-proof/runtime/startup_audits/`.
- `./.venv/bin/python -m pytest -q tests/test_startup_hardening_audit.py tests/test_audit_startup_hardening_script.py`
  - SHOWN: `5 passed in 0.43s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: startup topology, background jobs, fail-closed semantics, and
  live-adjacent service ownership are high-risk areas. This change is read-only
  and any follow-up startup wrapper, launch-gate, or service-topology change
  remains a separate high-risk implementation.
- Acceptance reference: accepted by human operator through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` on 2026-06-28 after PR #137 checks
  passed.
- Acceptance state: `ACCEPTED`.

## 2026-06-28T19:10:30Z - Record Startup Hardening Audit Acceptance

Active role: ENGINEER

Objective:
- Record the human acceptance of the PR #137 startup hardening audit proof in
  governed repo artifacts before merge.

What was found:
- SHOWN: PR #137 is open, ready for review, and all visible checks are
  successful.
- SHOWN: the implementation checkpoint and work-log entry still showed
  `READY_FOR_INDEPENDENT_REVIEW`.
- SHOWN: the operator supplied `INDEPENDENTLY_REVIEWED AND ACCEPTED`.

What changed:
- Updated the PR #43 startup hardening checkpoint implementation proof status
  from `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.
- Updated the implementation work-log entry with the human acceptance
  reference.

Why this change:
- Accepted high-risk work should not merge with stale pending-review wording
  in the governed checkpoint and work log.

Expected outcome:
- Future audits can trace that PR #137 passed CI and was accepted by the human
  operator before merge.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "Implementation proof status: ACCEPTED|Acceptance reference: accepted by human operator|Record Startup Hardening Audit Acceptance" docs/checkpoints/pr43_safe_pipeline_startup_hardening_objective_2026_06_28.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: acceptance status, acceptance reference, and this work-log entry are
    present.

Remaining risk:
- LOW: docs-only acceptance recording. Runtime behavior, startup topology,
  background jobs, live execution, order routing, and tests are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-06-29T04:14:01Z - Implement Read-Only Managed Campaign Planner

Active role: ENGINEER

Objective:
- Implement the accepted PR #43 managed multi-symbol paper-runtime objective
  as a read-only campaign proposal planner, without changing manifests or
  starting campaigns.

What was found:
- SHOWN: the accepted current runtime uses explicit campaign manifests for
  laptop and Hetzner ownership.
- SHOWN: `configs/paper_evidence_campaigns.laptop.json` owns
  `es_daily_trend_v1` and `breakout_default`.
- SHOWN: `configs/paper_evidence_campaigns.hetzner.example.json` owns
  `ema_cross_default`.
- SHOWN: current candidate snapshot data exists under
  `.cbp_state/runtime/candidates/latest_candidates.json`.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` keeps
  `use_candidate_advisor: false`.

What changed:
- Added `services/analytics/managed_paper_campaign_planner.py` to build a
  static read-only proposal report from current manifests and candidate
  artifacts.
- Added `scripts/plan_managed_paper_campaigns.py` as the root CLI.
- Added tests for explicit host proposals, manifest preservation, duplicate
  name/state/owner rejection, missing candidate evidence, no-write mode,
  default artifact writing, and no campaign-start/restore side effects.
- Documented the command in `scripts/SCRIPTS.md` and `docs/GOLDEN_PATH.md`.
- Updated `REMAINING_TASKS.md` and the PR #43 managed-runtime checkpoint to
  mark the implementation proof ready for independent review.

Why this change:
- The accepted objective rejects autonomous scanner-managed campaign starts.
  A proposal artifact is the smallest useful implementation: it turns candidate
  signals into reviewable manifest-shaped rows while preserving explicit human
  ownership and all running campaign boundaries.

Expected outcome:
- Operators can run `python scripts/plan_managed_paper_campaigns.py --no-write`
  for a read-only review, or pass `--host laptop` / `--host hetzner` to produce
  advisory manifest-shaped rows in the report.
- Applying any proposed row remains a separate high-risk reviewed change.

Verification:
- `./.venv/bin/python -m py_compile services/analytics/managed_paper_campaign_planner.py scripts/plan_managed_paper_campaigns.py tests/test_managed_paper_campaign_planner.py tests/test_plan_managed_paper_campaigns_script.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_managed_paper_campaign_planner.py tests/test_plan_managed_paper_campaigns_script.py`
  - SHOWN: `9 passed in 0.24s`.
- `./.venv/bin/python scripts/plan_managed_paper_campaigns.py --no-write`
  - SHOWN: exited 0 with `status=no_eligible_proposals`, `read_only=True`,
    `candidate_rows_reviewed=2`, and `proposal_count=0`.
- `CBP_STATE_DIR=/private/tmp/cbp-managed-campaign-plan-proof ./.venv/bin/python scripts/plan_managed_paper_campaigns.py --host laptop --json`
  - SHOWN: exited 0 and wrote latest/dated JSON and Markdown artifacts under
    `/private/tmp/cbp-managed-campaign-plan-proof/data/managed_paper_campaign_plans/`.
- `./.venv/bin/python scripts/plan_managed_paper_campaigns.py --host laptop --json --no-write`
  - SHOWN: current repo state produces two laptop-targeted
    `mean_reversion_rsi` proposal rows without writing.

Remaining risk:
- HIGH: managed campaign expansion affects financial strategy experimentation,
  background jobs, evidence attribution, and operator workflow. This change is
  read-only. Any follow-up manifest mutation, campaign start, or autonomous
  managed-runtime behavior remains a separate high-risk implementation.
- Acceptance reference: accepted by human operator through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` on 2026-06-29 after PR #138 checks
  passed.
- Acceptance state: `ACCEPTED`.

## 2026-06-29T04:35:01Z - Record Managed Campaign Planner Acceptance

Active role: ENGINEER

Objective:
- Record the human acceptance of the PR #138 managed campaign planner proof in
  governed repo artifacts before merge.

What was found:
- SHOWN: PR #138 is open and all visible checks are successful.
- SHOWN: the implementation checkpoint and work-log entry still showed
  `READY_FOR_INDEPENDENT_REVIEW`.
- SHOWN: the operator supplied `INDEPENDENTLY_REVIEWED AND ACCEPTED`.

What changed:
- Updated `REMAINING_TASKS.md` to classify the managed planner implementation
  proof as accepted.
- Updated the PR #43 managed-runtime checkpoint implementation proof status
  from `READY_FOR_INDEPENDENT_REVIEW` to `ACCEPTED`.
- Updated the implementation work-log entry with the human acceptance
  reference.

Why this change:
- Accepted high-risk work should not merge with stale pending-review wording in
  the governed backlog, checkpoint, and work log.

Expected outcome:
- Future audits can trace that PR #138 passed CI and was accepted by the human
  operator before merge.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "managed multi-symbol runtime implementation proof is accepted|Implementation proof status: ACCEPTED|Record Managed Campaign Planner Acceptance|Acceptance reference: accepted by human operator" REMAINING_TASKS.md docs/checkpoints/pr43_managed_multi_symbol_runtime_objective_2026_06_28.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: acceptance status, acceptance references, and this work-log entry
    are present.

Remaining risk:
- LOW: docs-only acceptance recording. Runtime behavior, campaign manifests,
  state directories, background jobs, candidate-advisor configuration, live
  execution, order routing, and tests are unchanged.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T02:01:51Z - Fail Closed On Malformed Paper Campaign Status

Active role: ENGINEER

Objective:
- Make Hetzner paper campaign status failures visible instead of rendering
  malformed or failed remote status as a misleading `0/0 running` report.

What was found:
- SHOWN: `make status-paper-all` reported laptop campaigns running, but the
  Hetzner status formatter printed `Campaigns: 0/0 running` with only
  `investigate_report_failure`, hiding the underlying failure reason.
- SHOWN: direct Tailscale SSH verification required an interactive web
  authentication check and was cancelled before remote state was verified.
- SHOWN: `scripts/report_paper_campaign_status.py` accepted any JSON object
  from `--from-json`, defaulted missing counts to zero, and did not print a
  top-level failure reason in human-readable output.

What changed:
- Added validation for `--from-json` status payloads before formatting.
- Preserved top-level failure reasons from failed status payloads.
- Printed top-level failure reasons in human-readable reports.
- Included an input preview when JSON parsing or shape validation fails.
- Added regression tests for malformed payloads, preserved failure reasons,
  and human-readable reason output.

Why this change:
- The formatter is an operator diagnostic surface. If remote status collection
  fails, the report should fail closed with an explicit reason rather than
  looking like a valid empty campaign set.

Expected outcome:
- Future Hetzner status failures should point operators toward the actual
  status/reporting failure path instead of creating a false impression that
  there are simply no configured campaigns.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_paper_campaign_status.py`
  - SHOWN: `8 passed in 0.10s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- LOW: this changes read-only status formatting and validation only. It does
  not start, stop, restore, mutate, or deploy any paper campaign.
- Remote Hetzner state remains UNVERIFIED because Tailscale SSH required an
  interactive authentication step during the check.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T02:18:37Z - Add Timeout-Aware Hetzner Status Wrapper

Active role: ENGINEER

Objective:
- Prevent `make status-paper-hetzner` from blocking indefinitely when
  Tailscale SSH requires interactive browser authentication or returns a
  malformed remote status payload.

What was found:
- SHOWN: the existing `status-paper-hetzner` Make target invoked
  `tailscale ssh` directly and piped the result into the local formatter.
- SHOWN: recent remote checks required an interactive Tailscale authentication
  step, which makes the direct pipeline a poor daily status surface.
- SHOWN: `scripts/report_paper_campaign_status.py` now fails closed on
  malformed payloads, but the raw Make pipeline could still block before the
  formatter receives input.

What changed:
- Added `scripts/report_hetzner_paper_campaign_status.py`, a read-only
  timeout-aware Tailscale SSH wrapper around the remote
  `restore_paper_campaigns.py --status` command.
- Updated `make status-paper-hetzner` to call the wrapper instead of a raw SSH
  pipe.
- Added regression tests for successful remote payload formatting, Tailscale
  SSH failure, timeout handling, and strict JSON exit behavior.
- Updated `scripts/SCRIPTS.md`, `docs/GOLDEN_PATH.md`, and
  `docs/PAPER_CAMPAIGN_RECOVERY.md` to document the wrapper behavior.

Why this change:
- Daily operator status should be read-only and bounded. A Tailscale browser
  auth prompt is an external access condition, not a valid campaign status;
  the command should report it explicitly and return control to the operator.

Expected outcome:
- `make status-paper-hetzner` remains the single operator command for Hetzner
  campaign status, but it now exits with an explicit failure reason if SSH
  auth, timeout, command failure, or malformed remote JSON prevents a valid
  status report.

Verification:
- `find scripts -maxdepth 1 -type f -name '*.py' | wc -l`
  - SHOWN: `110`, matching the updated script index.
- `make -n status-paper-hetzner`
  - SHOWN: invokes `scripts/report_hetzner_paper_campaign_status.py` with the
    configured target, app directory, and campaign manifest.
- `./.venv/bin/python -m py_compile scripts/report_hetzner_paper_campaign_status.py tests/test_report_hetzner_paper_campaign_status.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_hetzner_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: `12 passed in 0.15s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- MEDIUM: this changes an operator workflow and uses Tailscale SSH, but remains
  read-only and does not start, stop, restore, mutate, deploy, or route orders.
- Remote Hetzner campaign state remains UNVERIFIED until an authenticated
  Tailscale SSH status check succeeds.
- Acceptance reference: accepted by human operator through
  `INDEPENDENTLY_REVIEWED AND ACCEPTED` on 2026-07-02 after PR #163 checks
  passed.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T02:46:24Z - Surface Hetzner Status Failure Previews

Active role: ENGINEER

Objective:
- Make the human-readable Hetzner paper status report show the stdout/stderr
  previews already captured by failed status payloads.

What was found:
- SHOWN: after PR #163, `make status-paper-all` failed fast for the Hetzner
  side but the human output still showed only
  `remote_status_parse_failed:JSONDecodeError` without the captured output.
- SHOWN: `./.venv/bin/python scripts/report_hetzner_paper_campaign_status.py
  --strict --json --timeout-sec 5` exposed the real condition in
  `stderr_preview`: Tailscale SSH required an additional browser
  authentication check.

What changed:
- Updated `scripts/report_paper_campaign_status.py` to print bounded
  `stdout_preview` and `stderr_preview` fields in human-readable reports.
- Added a regression test proving those previews appear in normal report
  output.
- Updated the Golden Path and paper-campaign recovery docs to describe the
  preview behavior.

Why this change:
- The captured preview is the actionable diagnostic. Without printing it, the
  daily operator command still requires a second JSON-only command to discover
  the Tailscale auth URL or remote failure text.

Expected outcome:
- `make status-paper-hetzner` and `make status-paper-all` now show the bounded
  remote/Tailscale failure context directly in their normal output.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_paper_campaign_status.py tests/test_report_hetzner_paper_campaign_status.py`
  - SHOWN: `13 passed in 0.16s`.
- `./.venv/bin/python scripts/report_hetzner_paper_campaign_status.py --strict --timeout-sec 5`
  - SHOWN: exited non-zero and printed `Stderr preview:` with the Tailscale
    browser-auth prompt and authentication URL.

Remaining risk:
- LOW: read-only human-output formatting only. It does not alter campaign
  start/stop/restore behavior, Tailscale command arguments, deployment, state,
  or order routing.
- Remote Hetzner campaign state remains UNVERIFIED until an authenticated
  Tailscale SSH status check succeeds.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T03:00:33Z - Expose Hetzner Status Timeout Knob

Active role: ENGINEER

Objective:
- Bound the routine `make status-paper-hetzner` wait time through a visible
  Make variable instead of requiring operators to call the wrapper script
  directly to tune status-check latency.

What was found:
- SHOWN: `scripts/report_hetzner_paper_campaign_status.py` already accepts
  `--timeout-sec`.
- SHOWN: `make status-paper-hetzner` did not expose that timeout, so the daily
  operator command always used the script default.
- SHOWN: Tailscale SSH may require browser authentication, making bounded
  status latency part of the normal operator workflow.

What changed:
- Added `HETZNER_STATUS_TIMEOUT_SEC ?= 15` to the root Makefile.
- Passed `--timeout-sec $(HETZNER_STATUS_TIMEOUT_SEC)` from
  `make status-paper-hetzner` to the Hetzner status wrapper.
- Updated `docs/GOLDEN_PATH.md` and `docs/PAPER_CAMPAIGN_RECOVERY.md` with
  the default and override form.

Why this change:
- The daily status command should remain the canonical entrypoint, but
  operators need a documented way to shorten or lengthen the remote status
  wait without bypassing the Make target.

Expected outcome:
- `make status-paper-hetzner` remains read-only and now has an explicit,
  documented timeout budget. `HETZNER_STATUS_TIMEOUT_SEC=30 make
  status-paper-hetzner` extends the wait when the operator intentionally wants
  a slower host check.

Verification:
- `make -n status-paper-hetzner`
  - SHOWN: expands to the wrapper with `--timeout-sec 15`.
- `HETZNER_STATUS_TIMEOUT_SEC=1 make -n status-paper-hetzner`
  - SHOWN: expands to the wrapper with `--timeout-sec 1`.
- `HETZNER_STATUS_TIMEOUT_SEC=1 make status-paper-hetzner`
  - SHOWN: exited non-zero quickly and printed the captured local Tailscale
    failure preview: `The Tailscale CLI failed to start: Failed to load
    preferences.`
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- LOW: this changes only a read-only Make target's timeout argument and docs.
  It does not start, stop, restore, mutate, deploy, or route orders.
- Remote Hetzner campaign state remains UNVERIFIED until authenticated
  Tailscale SSH status succeeds.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T11:01:54Z - Refresh Remaining Tasks Campaign State

Active role: ENGINEER

Objective:
- Keep the lightweight backlog index aligned with the latest visible paper
  campaign status and accepted Hetzner status-reporting workflow.

What was found:
- SHOWN: `git rev-parse HEAD origin/master origin/review-stabilized` returned
  the same commit for all three refs.
- SHOWN: `HETZNER_STATUS_TIMEOUT_SEC=1 make status-paper-all` reported laptop
  campaigns running, with `es_daily_trend_v1` at `fills=18`, `closed=9`,
  `pnl=32.1776` and `breakout_default` at `fills=12`, `closed=6`,
  `pnl=-4.1120`.
- SHOWN: the same command reported the canonical gate still blocked at `2/10`
  provenance-qualified round trips.
- SHOWN: the Hetzner side failed before remote verification because the local
  Tailscale CLI printed `The Tailscale CLI failed to start: Failed to load
  preferences.`
- SHOWN: `REMAINING_TASKS.md` still listed stale `breakout_default` counts.

What changed:
- Updated `REMAINING_TASKS.md` current-state counts for `breakout_default`.
- Recorded the current local Hetzner status limitation as unverified remote
  state caused by a local Tailscale preference failure.
- Added the accepted timeout-aware Hetzner status-reporting behavior to the
  recently completed section.

Why this change:
- The backlog is used as the operator-facing task index. Stale campaign counts
  and missing Hetzner status-reporting context create avoidable confusion
  during daily check-ins.

Expected outcome:
- Future check-ins distinguish three separate facts: laptop campaigns are
  healthy, the canonical paper gate remains blocked at `2/10`, and Hetzner
  remote status still requires a working local Tailscale path before it can be
  trusted.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "breakout_default.*fills=12|The Tailscale CLI failed to start|Hetzner status reporting is bounded|Refresh Remaining Tasks Campaign State|2/10" REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: updated campaign count, local Tailscale failure note, bounded
    Hetzner status note, and this work-log entry are present.

Remaining risk:
- LOW: docs-only backlog alignment. Runtime behavior, campaign manifests,
  state directories, Tailscale commands, collectors, and order routing are
  unchanged.
- Remote Hetzner campaign state remains UNVERIFIED.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T11:08:54Z - Classify Tailscale Non-JSON Status Failures

Active role: ENGINEER

Objective:
- Make the Hetzner paper status wrapper report known Tailscale local/auth
  failures as specific status reasons instead of generic remote JSON parse
  failures.

What was found:
- SHOWN: `HETZNER_STATUS_TIMEOUT_SEC=1 make status-paper-hetzner` exited
  non-zero with `remote_status_parse_failed:JSONDecodeError` even though the
  bounded output preview clearly showed the local Tailscale CLI failure:
  `The Tailscale CLI failed to start: Failed to load preferences.`
- SHOWN: the wrapper already captured stdout/stderr previews, but classified
  all zero-exit non-JSON output as remote-status parse failure.

What changed:
- Added pre-JSON classification for known Tailscale non-JSON output:
  `tailscale_cli_preferences_unavailable` and `tailscale_ssh_auth_required`.
- Added regression tests for the local Tailscale preferences failure and
  browser-auth prompt when Tailscale returns non-JSON output with exit code 0.
- Updated `docs/GOLDEN_PATH.md` and `docs/PAPER_CAMPAIGN_RECOVERY.md` to name
  the specific reasons and operator interpretation.

Why this change:
- A local Tailscale CLI failure is materially different from malformed remote
  campaign JSON. The operator should see the correct failure class immediately
  from the top-level `Reason:` line.

Expected outcome:
- Routine Hetzner status checks now distinguish local Tailscale preference
  failure, Tailscale SSH browser-auth requirement, Tailscale non-zero failure,
  timeout, and genuine remote status JSON parse failures.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_hetzner_paper_campaign_status.py tests/test_report_hetzner_paper_campaign_status.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_hetzner_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: `15 passed in 0.17s`.
- `HETZNER_STATUS_TIMEOUT_SEC=1 make status-paper-hetzner`
  - SHOWN: exited non-zero with `Reason:
    tailscale_cli_preferences_unavailable` and the bounded stdout preview.

Remaining risk:
- LOW: read-only status classification and docs only. It does not alter SSH
  targets, remote commands, campaign manifests, collectors, state directories,
  or order routing.
- Remote Hetzner campaign state remains UNVERIFIED until local Tailscale status
  succeeds.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T11:26:49Z - Document Hetzner Tailscale Status Troubleshooting

Active role: ENGINEER

Objective:
- Align the Hetzner paper-host runbook with the accepted timeout-aware status
  command and its specific Tailscale failure reasons.

What was found:
- SHOWN: `docs/HETZNER_PAPER_HOST.md` documented accepted Tailscale SSH access
  and the operator SSH command.
- SHOWN: the same runbook did not document `make status-paper-hetzner` or the
  new `tailscale_cli_preferences_unavailable` and
  `tailscale_ssh_auth_required` status reasons.
- SHOWN: `docs/GOLDEN_PATH.md` and `docs/PAPER_CAMPAIGN_RECOVERY.md` already
  described those reasons, so the host-specific runbook was the remaining
  source-of-truth gap.

What changed:
- Added the routine read-only `make status-paper-hetzner` command to
  `docs/HETZNER_PAPER_HOST.md`.
- Documented how to interpret `tailscale_cli_preferences_unavailable` and
  `tailscale_ssh_auth_required`.
- Clarified that the status command is read-only and does not restore, stop, or
  start Hetzner collectors.

Why this change:
- Operators troubleshooting Hetzner access are likely to open the host runbook.
  The status command's new failure reasons need to be visible there, not only
  in the Golden Path and recovery docs.

Expected outcome:
- Future Hetzner check-ins distinguish a local Tailscale CLI/app problem from
  an unhealthy remote campaign without requiring the operator to cross-reference
  multiple docs.

Verification:
- `git diff --check`
  - SHOWN: passed.
- `rg -n "make status-paper-hetzner|tailscale_cli_preferences_unavailable|tailscale_ssh_auth_required|Document Hetzner Tailscale Status Troubleshooting|does not restore, stop, or start" docs/HETZNER_PAPER_HOST.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: runbook command, both failure reasons, read-only clarification, and
    this work-log entry are present.

Remaining risk:
- LOW: docs-only runbook alignment. Runtime behavior, Tailscale commands,
  campaign manifests, collectors, state directories, and order routing are
  unchanged.
- Remote Hetzner campaign state remains UNVERIFIED until local Tailscale status
  succeeds.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T11:33:53Z - Preserve Valid Hetzner JSON With Tailscale Stderr

Active role: ENGINEER

Objective:
- Fix the Hetzner status wrapper so valid remote campaign JSON on stdout is not
  rejected just because Tailscale writes authentication chatter to stderr.

What was found:
- SHOWN: sandboxed Tailscale CLI calls returned
  `The Tailscale CLI failed to start: Failed to load preferences.`
- SHOWN: an out-of-sandbox `tailscale status` succeeded and showed both
  `macbook-pro` and `ubuntu-4gb-nbg1-3` in the tailnet.
- SHOWN: an out-of-sandbox `make status-paper-hetzner` produced valid remote
  JSON on stdout but also Tailscale authentication text on stderr, causing the
  wrapper to report `tailscale_ssh_auth_required`.
- SHOWN: after the parsing-order fix, out-of-sandbox
  `HETZNER_STATUS_TIMEOUT_SEC=20 make status-paper-hetzner` reported
  `Campaigns: 1/1 running`, `ema_cross_default`, `fills=6`, `closed=3`,
  `pnl=-0.2678`, latest fill `2026-06-24T00:01:43.601405+00:00`, and
  `continue_paper_observation`.

What changed:
- Updated `scripts/report_hetzner_paper_campaign_status.py` to parse and
  accept valid stdout JSON before classifying known Tailscale non-JSON failure
  text.
- Added a regression test for valid campaign JSON on stdout with Tailscale
  authentication chatter on stderr.
- Updated `REMAINING_TASKS.md` to replace stale unverified Hetzner status with
  the verified `ema_cross_default` status and to clarify the Codex sandbox
  Tailscale limitation.

Why this change:
- Tailscale may write informational/authentication text to stderr even when the
  remote command returns valid JSON on stdout. The status wrapper should trust
  valid stdout JSON and only classify Tailscale text when JSON parsing fails.

Expected outcome:
- Routine Hetzner status checks report real campaign state when remote JSON is
  valid, while still failing closed with specific Tailscale reasons when no
  valid JSON is available.

Verification:
- `./.venv/bin/python -m py_compile scripts/report_hetzner_paper_campaign_status.py tests/test_report_hetzner_paper_campaign_status.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_report_hetzner_paper_campaign_status.py tests/test_report_paper_campaign_status.py`
  - SHOWN: `16 passed in 0.16s`.
- `HETZNER_STATUS_TIMEOUT_SEC=20 make status-paper-hetzner` outside the Codex
  sandbox
  - SHOWN: exited 0 with `Campaigns: 1/1 running`.

Remaining risk:
- LOW: read-only status parsing, test coverage, and backlog state update. It
  does not alter SSH targets, remote commands, campaign manifests, collectors,
  state directories, or order routing.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T13:45:50Z - Scope Live Crypto Edge Printed Reports

Active role: ENGINEER

Objective:
- Prevent the read-only live crypto edge collector CLI from printing a mixed
  latest report that can include stale `sample_bundle` rows during a
  `live_public` collection.

What was found:
- SHOWN: `scripts/collect_live_crypto_edge_snapshot.py --print-report` used
  `CryptoEdgeStoreSQLite.latest_report()`, which selects the latest snapshot
  per table without filtering by source.
- SHOWN: `CryptoEdgeStoreSQLite.latest_report_for_source(source=...)` already
  exists and is used by the collector service path.
- SHOWN: a sandboxed live collection attempt collected no live rows because
  exchange network calls failed, while an escalated read-only collection
  collected `live_public` quote/order-book rows but still could print old
  sample funding/basis rows through the global report path.

What changed:
- Updated `scripts/collect_live_crypto_edge_snapshot.py` so `--print-report`
  uses `latest_report_for_source(source=args.source or "live_public")`.
- Added a regression test where a database already contains `sample_bundle`
  funding, a live collection writes only `live_public` quotes, and the printed
  report must not show the sample funding as live evidence.

Why this change:
- The short-context readiness gate already filters by source. The operator CLI
  output should use the same evidence boundary so a partial live-public
  collection cannot look more complete than it is.

Expected outcome:
- `make collect-live-crypto-edges` with `--print-report` reports only rows from
  the requested source label. Operators will see missing live funding,
  open-interest, or basis families instead of mixed sample/live evidence.

Verification:
- `./.venv/bin/python -m py_compile scripts/collect_live_crypto_edge_snapshot.py tests/test_collect_live_crypto_edge_snapshot.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_collect_live_crypto_edge_snapshot.py tests/test_crypto_edge_store_sqlite.py`
  - SHOWN: `7 passed in 0.20s`.

Remaining risk:
- LOW: read-only reporting change. It does not alter collection fetches,
  database schema, short-context readiness logic, trading execution, or risk
  gates.
- Binance-derived live funding/open-interest/basis collection remains
  incomplete and must still be solved separately before the short/context
  replay gate is live-public ready.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T13:52:08Z - Allow Mixed-Venue Crypto Edge Research Collection

Active role: ENGINEER

Objective:
- Remove the repo-side mixed-venue conflict in the read-only crypto edge
  collector while preserving the explicit Binance allowance requirement.

What was found:
- SHOWN: `services/analytics/crypto_edge_collector.py` opened every public
  venue through `services.security.exchange_factory.make_exchange()`.
- SHOWN: `make_exchange()` applies the execution-oriented `CBP_VENUE`
  explicit/env conflict rule.
- SHOWN: a guarded read-only probe with `CBP_VENUE=binance` and
  `CBP_ALLOW_BINANCE=1` made Binance eligible but caused Coinbase/Kraken legs
  to fail with `VenueResolutionError`.
- SHOWN: without the Binance allowance, the same plan fails Binance rows with
  the repo's existing Binance guard.

What changed:
- Updated the crypto edge collector's private `_open_public_exchange()` helper
  to construct public CCXT clients directly for research-only market-data
  collection.
- Kept `require_binance_allowed()` for Binance venues.
- Kept public clients credentialless with `apiKey=None` and `secret=None`.
- Added targeted tests proving non-Binance research clients can open under the
  Binance allowance and Binance remains blocked without the allowance.
- Updated `REMAINING_TASKS.md` so the short/context backlog now distinguishes
  the fixed repo-side mixed-venue conflict from the still-open external
  Binance derivatives availability failure.

Why this change:
- The crypto edge collector is intentionally mixed-venue and read-only. The
  execution factory's global `CBP_VENUE` conflict rule is appropriate for order
  routing surfaces, but it blocks a research snapshot plan that needs Binance
  derivatives context plus Coinbase/Kraken quote/order-book context in the
  same run.

Expected outcome:
- Operators can run a guarded mixed-venue read-only collection with
  `CBP_VENUE=binance CBP_ALLOW_BINANCE=1` and still collect Coinbase/Kraken
  public rows. The short/context gate remains fail-closed until live-public
  derivatives row families are present.

Verification:
- `./.venv/bin/python -m py_compile services/analytics/crypto_edge_collector.py tests/test_crypto_edge_collector.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_crypto_edge_collector.py tests/test_collect_live_crypto_edge_snapshot.py`
  - SHOWN: `8 passed in 0.21s`.
- `CBP_VENUE=binance CBP_ALLOW_BINANCE=1 ./.venv/bin/python scripts/collect_live_crypto_edge_snapshot.py --plan-file sample_data/crypto_edges/live_collector_plan.json --db-path /private/tmp/cbp_crypto_edge_mixed_venue_after_fix.sqlite --print-report`
  - SHOWN: exited 0; Coinbase and Kraken quote checks passed; Coinbase
    order-book check passed; Binance funding/open-interest/basis checks still
    failed with `exchange_open_failed:ExchangeNotAvailable`.
- `./.venv/bin/python -c '<read-only OKX derivatives collector probe>'`
  - SHOWN: OKX funding, open-interest, and basis checks passed and returned
    rows. This was a candidate probe only; the canonical live collector plan was
    not changed.

Remaining risk:
- MEDIUM: this changes public exchange construction for a read-only research
  collector, not execution. It intentionally does not alter order routing,
  credentials, risk gates, or the execution exchange factory.
- Binance derivatives availability remains externally blocked on this network;
  OKX is a validated read-only candidate, but adopting it into the canonical
  live collector plan still needs explicit config/docs review before
  live-public short/context replay can clear.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T22:18:23Z - Add Strategy Discovery Findings To Backlog

Active role: ENGINEER

Objective:
- Make the accepted strategy-discovery audit findings visible in the canonical
  backlog instead of leaving them only in chat context.

What was found:
- SHOWN: `REMAINING_TASKS.md` already recorded the mixed-venue collector fix
  and the OKX read-only derivatives probe.
- SHOWN: it did not explicitly track archive-first backtesting or context
  strategy execution as active backlog items.
- SHOWN: `services/backtest/signal_replay.py` still fetches OHLCV live with a
  shallow single-call default while `storage/market_store_sqlite.py` contains a
  `market_ohlcv` archive table.
- SHOWN: `funding_extreme`, `open_interest_shift`, and
  `order_book_imbalance` exist as context-signal strategy modules, while
  `strategy_registry.py` executes only OHLCV strategy functions today.

What changed:
- Added an active backlog item for archive-first backtesting with paginated
  archive ingestion, dataset hashes, and repeatable backtest proof.
- Added an active backlog item for wiring crypto-edge context strategies into
  the research/paper execution path without enabling live execution.
- Renumbered the following active backlog items.

Why this change:
- The current repo can collect useful crypto-edge context, but strategy
  discovery remains blocked until backtests become reproducible and the context
  strategies can run through the same evidence path as OHLCV strategies.

Expected outcome:
- Future planning can prioritize research/profitability discovery work without
  confusing it with live-money readiness or collector plumbing.

Verification:
- `rg -n "archive-first|market_ohlcv|funding_extreme|open_interest_shift|order_book_imbalance|context" REMAINING_TASKS.md`
  - SHOWN: backlog entries for archive-first backtesting and context strategy
    wiring are present.

Remaining risk:
- LOW: backlog/work-log documentation only. No runtime, trading, collector,
  gate, or deployment behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T22:31:26Z - Add Remaining Audit Matrix Findings To Backlog

Active role: ENGINEER

Objective:
- Capture the remaining actionable audit-matrix findings that were not covered
  by PR #172's strategy-discovery backlog entries.

What was found:
- SHOWN: PR #172 represented the strategy-discovery findings: fail-closed
  registry behavior, archive-first backtesting, context strategy wiring,
  crypto-edge qualification proof, and scheduled edge collection after a source
  decision.
- SHOWN: `REMAINING_TASKS.md` did not explicitly track live-money substrate
  findings for Decimal money math, fail-closed trading config, typed order
  retry handling, submit-path crash testing, deployment units/Docker cleanup,
  loop dead-man alerting, trading-state consolidation, or full-state
  backup/restore drills.
- SHOWN: it also did not explicitly track lower-priority hygiene findings for
  runtime stubs, duplicate/twin modules, archive walk-forward depth proof,
  `ws_*` naming versus REST reality, or backtest-to-paper fill parity.

What changed:
- Added a `Deferred Live-Money Substrate Backlog` section to
  `REMAINING_TASKS.md`.
- Added a `Deferred Structure And Research Hygiene` section to
  `REMAINING_TASKS.md`.
- Kept the new items explicitly deferred so they do not interrupt the current
  paper/research campaign, while making them visible before any capped-live
  decision.

Why this change:
- The project is paper-first today, but live-money blockers should not remain
  only in chat/audit text. Recording them as deferred backlog prevents a future
  live gate from advancing without revisiting the substrate risks.

Expected outcome:
- Current work can stay focused on paper evidence and strategy discovery, while
  the live-readiness substrate and concrete hygiene gaps remain visible in the
  repo.

Verification:
- `rg -n "Deferred Live-Money|Decimal|fail closed|clientOrderId|systemd|dead-man|backup/restore|Deferred Structure|run_mode.py|walk-forward|ws_\\*|fill parity" REMAINING_TASKS.md`
  - SHOWN: all new backlog categories and representative items are present.

Remaining risk:
- LOW: backlog/work-log documentation only. No runtime, trading, collector,
  gate, deployment, or test behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-02T22:21:45Z - Refine Strategy Discovery Implementation Constraints

Active role: ENGINEER

Objective:
- Add the follow-up implementation-plan findings to the active backlog so the
  strategy-discovery work is sequenced safely.

What was found:
- SHOWN: the backlog had archive-first backtesting and context strategy wiring
  as high-level items.
- SHOWN: it did not yet state the shared prerequisite that unknown strategy
  names must fail closed instead of silently falling back to `ema_cross`.
- SHOWN: it did not yet state that `funding_extreme` should be wired first,
  `open_interest_shift` should wait for snapshot-history OI deltas, and
  `order_book_imbalance` should wait for tighter-cadence or streaming depth
  data.
- SHOWN: it did not yet call out the crypto-edge paper-qualification extension
  as high-risk gate work requiring accept-and-reject proof.

What changed:
- Added an active backlog item for fail-closed strategy registry behavior.
- Expanded the context-strategy backlog item to prioritize `funding_extreme`
  and defer `open_interest_shift` / `order_book_imbalance` until their data
  prerequisites are credible.
- Added an active backlog item requiring edge-provenance qualification proof
  and unchanged OHLCV qualification behavior.
- Added an active backlog item to start scheduled read-only crypto-edge
  collection after the canonical source decision is accepted.
- Renumbered the following active backlog items.

Why this change:
- The implementation-plan audit identified sequencing risks that matter for
  evidence integrity. The backlog should prevent a future implementation from
  silently running the wrong strategy, weakening the gate, or producing
  low-quality order-book evidence from REST snapshots.

Expected outcome:
- Future strategy-discovery work starts with fail-closed registry behavior,
  reproducible archive data, and the smallest proofable context strategy
  (`funding_extreme`) before broader derivative/intraday work.

Verification:
- `rg -n "fail closed|funding_extreme|open_interest_shift|order_book_imbalance|high-risk gate|scheduled read-only crypto-edge" REMAINING_TASKS.md`
  - SHOWN: the new prerequisite, strategy ordering, gate-proof requirement, and
    collection timing are present.

Remaining risk:
- LOW: backlog/work-log documentation only. No runtime, trading, collector,
  gate, or deployment behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Make Strategy Registry Fail Closed For Unknown Names

Active role: ENGINEER

Objective:
- Prevent explicit unknown strategy names from silently falling back to
  `ema_cross` before crypto-edge context strategy wiring lands.

What was found:
- SHOWN: `services/strategies/strategy_registry.py` converted any unsupported
  `strategy.name` to `ema_cross`.
- SHOWN: `tests/test_strategy_registry.py` had a regression test asserting that
  unknown strategies fall back instead of failing closed.
- SHOWN: `REMAINING_TASKS.md` tracks this as the prerequisite for new strategy
  discovery wiring because typos such as `funding_extrem` could otherwise
  produce actionable EMA signals under the wrong strategy identity.

What changed:
- Updated `compute_signal()` so an explicit unknown strategy returns
  `ok=false`, `action=hold`, `reason=unknown_strategy`, the requested strategy
  name, and the symbol.
- Preserved the existing missing-name default to `ema_cross` for configs that
  do not provide a strategy block.
- Replaced the old fallback test with a fail-closed regression test and added a
  test for the preserved missing-name default.
- Updated `REMAINING_TASKS.md` to mark the implementation proof ready for
  independent review.

Why this change:
- The smallest safe boundary fix is inside the registry itself. It prevents an
  unsupported or mistyped strategy from emitting a buy/sell signal while
  avoiding a broader runner, gate, or context-strategy change.

Expected outcome:
- A typo in strategy configuration becomes visible as a non-actionable
  `unknown_strategy` signal instead of being silently executed as `ema_cross`.
- Future `funding_extreme` / context-strategy wiring can rely on fail-closed
  dispatch before adding new execution contracts.

Verification:
- `./.venv/bin/python -m py_compile services/strategies/strategy_registry.py tests/test_strategy_registry.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_registry.py`
  - SHOWN: `11 passed in 0.10s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: strategy dispatch is financial/trading-adjacent logic and may affect
  paper/live-adjacent runtime decisions if an invalid strategy name is supplied.
- UNVERIFIED: broader strategy-runner and paper-campaign integration beyond
  the targeted registry tests.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-03 before PR publication.

## 2026-07-03 - Prove Unknown Strategy Fails Closed Through Runner Evidence

Active role: ENGINEER

Objective:
- Extend the accepted registry fail-closed behavior through the strategy runner
  evidence path so an explicit strategy-name typo cannot be canonicalized to
  `ema_cross` before reaching the registry.

What was found:
- SHOWN: `services/execution/strategy_runner.py` still had its own
  `_canonical_strategy_name()` fallback that mapped unsupported names to
  `ema_cross` before calling `strategy_registry.compute_signal()`.
- SHOWN: the public-OHLCV branch rebuilt a selected strategy block with
  `build_strategy_block()`, which could not carry an unsupported name through
  to the registry for a fail-closed status result.
- SHOWN: `es_daily_trend_v1` is a common strategy identifier in configs/docs
  while the executable registry strategy is `sma_200_trend`.
- SHOWN: during test construction, `_strategy_signal()` had no visible caller
  in the current runner; the accepted proof therefore targets the public-OHLCV
  path used by the active paper evidence campaigns and records the
  synthetic/tick branch as a separate backlog investigation.

What changed:
- Added explicit strategy-name source detection so missing strategy config
  still defaults to `ema_cross`, while explicit unknown or empty names become
  unsupported strategy blocks.
- Added an `es_daily_trend_v1` alias to `sma_200_trend` to avoid treating the
  canonical campaign identifier as an unknown runner strategy.
- Made unsupported strategy blocks use the generic 5-bar minimum history
  instead of falling through to EMA history defaults.
- Added a helper for public-OHLCV selected strategy blocks so unsupported names
  pass through to the registry and produce `unknown_strategy` hold results
  instead of falling back or raising in `build_strategy_block()`.
- Added runner tests proving explicit unknown and explicit empty names are
  preserved as unsupported config, and a public-OHLCV runner loop records
  `signal_ok=false`, `signal_action=hold`, and
  `signal_reason=unknown_strategy` with zero intents, zero paper orders, and
  zero paper fills.
- Updated `REMAINING_TASKS.md` with the runner proof status and the separate
  synthetic/tick branch follow-up.

Why this change:
- The registry-only fix protected direct registry callers, but the production
  runner had a pre-registry alias layer that could still silently execute EMA
  for a typo. The smallest correct fix is to fail closed at the runner config
  boundary while preserving missing-config defaults and known aliases.

Expected outcome:
- Future strategy-discovery wiring can rely on the runner preserving an
  unsupported strategy name through status/evidence as a non-actionable hold.
- A typo such as `funding_extrem` does not enqueue a strategy intent and does
  not create paper orders or fills on the public-OHLCV runner path.

Verification:
- `./.venv/bin/python -m py_compile services/execution/strategy_runner.py tests/test_strategy_runtime_runner.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_registry.py tests/test_strategy_runtime_runner.py`
  - SHOWN: `38 passed in 0.72s`.

Remaining risk:
- HIGH: strategy-runner dispatch is trading-adjacent financial logic.
- UNVERIFIED: full suite, live execution surfaces, and the tick/synthetic
  strategy-runner branch. The latter is documented as a separate backlog item
  because `_strategy_signal()` currently has no visible caller in
  `services/execution/strategy_runner.py`.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-03 after PR #175 checks passed.

## 2026-07-03 - Fail Closed on Corrupt Runtime Config for Strategy Runner

Active role: ENGINEER

Objective:
- Close the highest-risk config fail-open slice identified by the repo audit:
  an existing corrupt runtime user config must not silently become `{}` and let
  the strategy runner trade from defaults.

What was found:
- SHOWN: `services/admin/config_editor.py::load_user_yaml()` caught all load
  and parse exceptions, printed the error, and returned `{}`.
- SHOWN: `services/config_loader.py::load_user_config()` and `_load_yaml_file()`
  caught all load and parse exceptions and returned `{}`.
- SHOWN: `services/execution/strategy_runner.py::_cfg()` read user config
  before queue/database setup and was the narrow startup choke point for the
  active paper strategy dispatch path.
- UNVERIFIED: other runtime trading-config consumers, including bot startup,
  live executor/consumer/reconciler, and risk-gate config readers, still need a
  separate sweep before capped live.

What changed:
- Added `ConfigLoadError` and `strict=True` load modes to
  `services/admin/config_editor.py` and `services/config_loader.py`.
- Preserved existing lenient behavior by default: missing files still return
  `{}`, and non-strict callers still return `{}` for corrupt or non-mapping
  files.
- Changed the strategy runner startup config read to `load_user_yaml(strict=True)`.
- Added runner startup handling that writes a visible stopped status with
  `reason=config_load_failed` and returns before queueing any intents.
- Added tests proving strict loader behavior for missing, corrupt, and explicit
  runtime config paths, and proving corrupt `user.yaml` produces zero strategy
  intents, paper orders, and paper fills.
- Updated `REMAINING_TASKS.md` to mark this as the first proof-ready slice while
  keeping the broader live-money config sweep open.

Why this change:
- The smallest safe fix is to add strict behavior without changing every legacy
  config reader at once, then wire the strict path at the active trading
  dispatch boundary. This prevents evidence poisoning from a corrupt existing
  user config while avoiding opportunistic rewrites across unrelated UI/helper
  consumers.

Expected outcome:
- A malformed existing runtime `user.yaml` halts the strategy runner visibly
  instead of applying default strategy settings.
- Paper evidence campaigns that depend on the strategy runner cannot generate
  new strategy intents/orders/fills from a silently defaulted corrupt config.

Verification:
- `./.venv/bin/python -m py_compile services/admin/config_editor.py services/config_loader.py services/execution/strategy_runner.py tests/test_runtime_trading_config.py tests/test_config_editor_compat.py tests/test_strategy_runtime_runner.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_runtime_trading_config.py tests/test_config_editor_compat.py tests/test_strategy_runtime_runner.py`
  - SHOWN: `55 passed in 0.98s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: runtime config loading controls trading-adjacent financial behavior.
- UNVERIFIED: full test suite, paper evidence service persistence branch, and
  live-money runtime consumers beyond the strategy-runner dispatch path.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-03 before PR #177 merge.

## 2026-07-03 - Restore Synthetic Strategy Runner Signal Dispatch

Active role: ENGINEER

Objective:
- Restore strategy signal computation in the `synthetic_mid_ohlcv` /
  tick-based strategy runner path after PR #175 exposed that `_strategy_signal()`
  had no visible caller.

What was found:
- SHOWN: `services/execution/strategy_runner.py` initialized each loop with
  `signal = {"ok": True, "action": "hold", "reason": "no_signal"}`.
- SHOWN: the public-OHLCV branch computed `signal` from `compute_signal()`, but
  the tick/synthetic branch continued after warmup without calling
  `_strategy_signal()`.
- SHOWN: `_strategy_signal()` existed and had direct unit coverage, but no
  visible runtime caller.
- SHOWN: the tick/synthetic warmup block had an unconditional sleep/continue
  after writing warmup status, preventing the shared decision/action section
  from seeing a computed strategy signal.

What changed:
- Moved the tick/synthetic sleep/continue inside the `len(prices) < min_bars`
  warmup branch.
- Called `_strategy_signal(sym_cfg, prices, ts_ms=ts_ms)` once enough prices
  exist, and set `bars = len(prices)` for downstream status.
- Added a runner regression proving `synthetic_mid_ohlcv` calls
  `_strategy_signal()` after warmup, records the signal reason in the queued
  intent metadata, creates exactly one queued strategy intent for a synthetic
  buy signal, and creates zero paper orders/fills.
- Updated `REMAINING_TASKS.md` so the synthetic/tick branch item records the
  implementation proof boundary.

Why this change:
- The previous runner proof deliberately scoped itself to public OHLCV, but
  leaving the synthetic/tick branch unable to call strategy logic would keep a
  dormant runtime path misleadingly present. The smallest correction is to
  restore the existing helper call after warmup without touching public-OHLCV,
  risk gates, order routing, or paper order execution.

Expected outcome:
- Tick/synthetic strategy-runner mode can once again convert warmed mid-price
  history into strategy signals and queued intents.
- The paper order/fill boundary remains unchanged: the strategy runner only
  queues intents; paper execution still belongs to the paper runner/reconciler.

Verification:
- `./.venv/bin/python -m py_compile services/execution/strategy_runner.py tests/test_strategy_runtime_runner.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_registry.py tests/test_strategy_runtime_runner.py`
  - SHOWN: `39 passed in 1.68s`.

Remaining risk:
- HIGH: strategy-runner dispatch is trading-adjacent financial logic and this
  restores actionable signal generation in tick/synthetic mode.
- UNVERIFIED: full suite, long-running paper campaigns, and any live-adjacent
  runtime surface outside the targeted strategy-runner tests.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-03 before PR #176 merge.

## 2026-07-03 - Strict Config Reloads for Active Paper Evidence Path

Active role: ENGINEER

Objective:
- Finish the #177 follow-through in the active paper evidence path so
  mid-session corrupt runtime user config cannot silently revert to `{}` while
  the strategy runner or evidence service continues producing evidence.

What was found:
- SHOWN: `services/execution/strategy_runner.py::_cfg()` already used
  `load_user_yaml(strict=True)` at startup after PR #177.
- SHOWN: `_resolve_venue_candidates()` still used non-strict
  `load_user_yaml()` for in-loop venue candidate fallback.
- SHOWN: the public-OHLCV signal branch still used non-strict
  `load_user_yaml()` before building the selected strategy block.
- SHOWN: `services/analytics/paper_strategy_evidence_service.py` still used
  non-strict `load_user_yaml()` as `base_cfg` immediately before regenerating
  leaderboard evidence and decision records.
- UNVERIFIED: live-money config consumers outside the active paper evidence
  path remain open backlog work.

What changed:
- Added a shared strategy-runner status writer for `config_load_failed` that
  records a non-actionable hold signal.
- Made `_resolve_venue_candidates()` and the public-OHLCV selected strategy
  config reload use `load_user_yaml(strict=True)`.
- Handled in-loop `ConfigLoadError` by writing visible `config_load_failed`
  status, sleeping, and skipping the tick without enqueuing strategy intents.
- Made paper evidence service use strict config loading before the evidence
  cycle; on failure it writes a failed campaign status and returns before
  leaderboard persistence or decision-record generation.
- Added targeted tests proving mid-session runner config corruption writes
  `config_load_failed`, holds without side effects, and creates zero intents,
  paper orders, or paper fills.
- Added targeted tests proving paper evidence service config-load failure
  stops before evidence persistence.
- After CI exposed the repository's no-raw-exception-text guard, sanitized the
  paper evidence and strategy-runner config-load failure payloads to expose
  `config_load_failed` plus `error_type` instead of raw parser/path text.
- Updated `REMAINING_TASKS.md` to record the active paper evidence path proof
  while keeping the broader capped-live config sweep open.

Why this change:
- The prior strict startup fix prevented a corrupt config from starting a new
  runner, but non-strict reloads could still poison evidence after startup.
  Strict reload handling at the active evidence boundary is the smallest patch
  that closes the paper-campaign gap without sweeping unrelated live consumers.

Expected outcome:
- Corrupt runtime config during a paper evidence session becomes an explicit
  `config_load_failed` status instead of silently defaulting to `{}`.
- Strategy runner does not enqueue new intents while config is unreadable.
- Paper evidence service does not regenerate leaderboard or decision artifacts
  from default config after a strict config-load failure.
- Config-load failure status remains operator-visible without leaking raw
  exception text.

Verification:
- `./.venv/bin/python -m py_compile services/execution/strategy_runner.py services/analytics/paper_strategy_evidence_service.py tests/test_strategy_runtime_runner.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: passed.
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `57 passed in 1.02s`.
- GitHub Actions for PR #179
  - SHOWN: CI failed in `test_ops_services_do_not_log_raw_exception_text`
    because `paper_strategy_evidence_service.py` contained `"error": str(exc)`.
- GitHub Actions for PR #179 after sanitized-status follow-up
  - SHOWN: all 7 checks passed: CI validate, CI sanity, macOS wrapper build,
    Windows wrapper build, Governance smoke push, Governance smoke pull request,
    and GitGuardian.
- `./.venv/bin/python -m pytest -q tests/test_ops_services_no_raw_exception_text.py tests/test_strategy_runtime_runner.py tests/test_paper_strategy_evidence_service.py`
  - SHOWN: `58 passed in 0.98s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: runtime config loading affects trading-adjacent strategy dispatch and
  evidence generation.
- UNVERIFIED: full suite, long-running campaign behavior, safety/load-gates,
  live executor/consumer/reconciler config consumers, and master promotion PR
  #178.
- Acceptance state: `ACCEPTED`.
- Review reference: independently reviewed and accepted by the human operator
  on 2026-07-03 after PR #179 CI passed.

## 2026-07-03 - Strategic Review Backlog Triage

Active role: ENGINEER

Objective:
- Process the strategic production-readiness review findings that were not
  covered by the strict config reload implementation, and preserve any missing
  actionable item in the visible backlog.

What was found:
- SHOWN: `REMAINING_TASKS.md` already tracks archive-first backtesting,
  crypto-edge context strategy wiring, Decimal money math, typed retry
  classification, fault-injection, systemd deployment, loop dead-man alerting,
  state-store consolidation, backup/restore drill, and duplicate-module
  cleanup.
- SHOWN: `scripts/check_promotion_gates.py` requires shadow fill/slippage
  evidence for the shadow slippage gate.
- SHOWN: `services/execution/_executor_shared.py` blocks submit operations in
  observe-only shadow mode.
- SHOWN: the existing shadow backlog/proof text covered spread/depth stamping,
  but did not explicitly require a would-be-fill recorder.

What changed:
- Added an active backlog item requiring a shadow would-be-fill recorder before
  shadow slippage gates are treated as actionable.
- The item requires proof that shadow mode records intended fill/slippage
  evidence while still creating zero live orders.
- Renumbered the active backlog so the shadow recorder is visible before
  sandbox lifecycle and launch-packet work.

Why this change:
- The strategic review identified a structural proof gap: shadow can collect
  signal records, but the slippage gate cannot be satisfied if observe-only
  submits do not persist would-be-fill records.
- Capturing the task in `REMAINING_TASKS.md` prevents the repo from treating
  shadow spread/depth stamping as complete shadow readiness.

Expected outcome:
- The next shadow-stage implementation has a clear objective: record
  would-be-fill slippage evidence without placing live orders.
- Operators can distinguish completed spread/depth signal proof from the still
  missing fill/slippage evidence path.

Verification:
- `sed -n '1,240p' /Users/baitus/.codex/attachments/23e1567a-b478-4841-9ed5-0be75b60e09c/pasted-text.txt`
  - SHOWN: the strategic review identifies shadow would-be-fill recording as a
    missing proof path.
- `sed -n '780,825p' scripts/check_promotion_gates.py`
  - SHOWN: the shadow slippage gate reports missing shadow fill/slippage
    evidence and asks operators to collect would-be-fill slippage evidence.
- `sed -n '400,425p' services/execution/_executor_shared.py`
  - SHOWN: shadow observe-only mode disables submit operations.

Remaining risk:
- LOW: this is a docs/backlog tracking change only.
- UNVERIFIED: implementation design for the future recorder, storage schema,
  and gate integration.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Principal Audit Delta Backlog Capture

Active role: ENGINEER

Objective:
- Capture the new actionable deltas from the principal-engineer
  production-readiness audit so they remain visible after the shadow recorder
  and strict-config items were already merged or tracked.

What was found:
- SHOWN: `SUPPORTED - ALLOWED_STRATEGIES` is
  `breakout_volume`, `gap_fill`, `sma_200_trend`, and
  `volatility_reversal`; `ALLOWED_STRATEGIES - SUPPORTED` is empty.
- SHOWN: `services/signals/candidate_advisor.py` defines
  `ALLOWED_STRATEGIES` as a hard-coded subset of the strategy registry with no
  explicit exclusion set.
- SHOWN: `services/execution/strategy_runner.py::_acquire_lock()` checks
  `LOCK_FILE.exists()` and then writes the lock file, with no atomic create
  path and no stale-PID recovery.
- SHOWN: `services/execution/strategy_runner.py` and
  `scripts/run_paper_strategy_evidence_collector.py` stamp sample-mode
  provenance from `CBP_USE_SAMPLE_OHLCV`; the paper qualification gate then
  treats `ohlcv_sample_mode` as authoritative.
- SHOWN: the audit identified evidence-write failure surfacing and
  paper-ledger invariant tests as proof gaps.

What changed:
- Added backlog items for advisor/registry classification, strategy-runner
  atomic lock and stale-PID recovery, and source-derived sample-mode
  provenance.
- Added deferred proof items for surfacing repeated evidence-write failures and
  preserving paper-ledger invariants around `PaperTradingSQLite.apply_fill`.

Why this change:
- The findings are real but should not be mixed into the accepted strict-config
  or shadow-recorder tracking PRs.
- Capturing them in `REMAINING_TASKS.md` preserves the audit signal without
  starting new high-risk implementation work inside a docs-only branch.

Expected outcome:
- Future strategy-discovery work cannot silently omit registered strategies
  without an explicit exclusion rationale.
- Runner restart robustness, sample/provenance trust, evidence-write
  observability, and paper-ledger consistency have visible follow-up tasks.

Verification:
- `./.venv/bin/python - <<'PY' ...`
  - SHOWN: `SUPPORTED_MINUS_ALLOWED=['breakout_volume', 'gap_fill',
    'sma_200_trend', 'volatility_reversal']` and
    `ALLOWED_MINUS_SUPPORTED=[]`.
- `nl -ba services/execution/strategy_runner.py | sed -n '240,260p;748,760p'`
  - SHOWN: `_acquire_lock()` is check-then-write and `run_forever()` reports
    `lock_exists` without stale lock recovery.
- `rg -n "ohlcv_sample_mode|CBP_USE_SAMPLE_OHLCV|sample_mode" services/execution services/control scripts tests`
  - SHOWN: sample-mode provenance is stamped from env and later consumed by
    paper evidence qualification.

Remaining risk:
- LOW: this is a docs/backlog tracking change only.
- UNVERIFIED: implementation designs and test details for each captured item.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Shadow Would-Be-Fill Recorder Implementation Proof

Active role: ENGINEER

Objective:
- Implement the smallest shadow-stage recorder needed for observe-only submit
  attempts to produce fill/slippage evidence without placing live orders.

What was found:
- SHOWN: `services/execution/_executor_submit.py::submit_pending_live()` returns
  early in `LIVE_SHADOW` observe-only mode before venue submission.
- SHOWN: `scripts/check_promotion_gates.py::evaluate_shadow_gates()` already
  reads shadow `fill` evidence and reports manual slippage review as available
  once fill records exist.
- SHOWN: `services/strategies/evidence_logger.py` can write `fill_*.jsonl`
  records under the active strategy evidence directory while preserving
  caller-supplied `_stage`.
- SHOWN: the live-executor facade synchronizes monkeypatched dependencies into
  `_executor_submit`, allowing a focused observe-only regression test.

What changed:
- Added private shadow-recorder helpers in
  `services/execution/_executor_submit.py`.
- In `LIVE_SHADOW` observe-only submit mode, pending live intents are scanned
  and converted into idempotent `shadow_would_be_fill` evidence records.
- Each record captures side, quantity, symbol, venue, bid, ask, last,
  reference mid, spread bps, modeled fill price, fee, slippage, selected
  strategy, strategy preset, `_stage=shadow`, and non-sample local snapshot
  provenance.
- The recorder uses the existing deterministic fill model and does not call the
  exchange client, update intent status, or insert execution-store fills.
- Added a regression test proving one pending live intent produces exactly one
  shadow fill-evidence record and remains pending with zero execution-store
  fills.
- Added a gate test proving `evaluate_shadow_gates()` surfaces shadow
  would-be-fill evidence as manual slippage-review input.
- Updated `REMAINING_TASKS.md` to mark the item as implementation-proof-ready
  pending independent review.

Why this change:
- Shadow mode previously had an unstartable evidence gate: submit was correctly
  observe-only, but there was no artifact for the slippage gate to inspect.
- Writing evidence records instead of execution-store fills preserves the
  observe-only safety boundary while allowing the shadow gate to accumulate
  reviewable would-be-fill slippage data.
- Idempotency by intent prevents a repeated shadow submit loop from generating
  one evidence fill per tick for the same pending intent.

Expected outcome:
- Once paper promotes to shadow, pending live intents can produce slippage
  evidence for manual review without opening orders or mutating live fill
  tables.
- The shadow gate can distinguish "no slippage evidence exists" from
  "manual review is required across N would-be-fill records."

Verification:
- `./.venv/bin/python -m py_compile services/execution/_executor_submit.py tests/test_live_executor_shadow_and_trade_reconcile.py tests/test_check_promotion_gates.py`
  - SHOWN: command completed successfully.
- `./.venv/bin/python -m pytest -q tests/test_live_executor_shadow_and_trade_reconcile.py tests/test_check_promotion_gates.py::TestShadowGateMarketQuality`
  - SHOWN: initial implementation proof returned `9 passed in 0.99s`.
  - SHOWN: post-acceptance merge-resolution rerun returned
    `9 passed in 1.04s`.
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- HIGH: this touches executor-adjacent financial logic and shadow/live submit
  behavior.
- UNVERIFIED: full-suite result and a live-like shadow campaign run against the
  operator host were not run in this thread.
- Human review: user stated `INDEPENDENTLY_REVIEWED AND ACCEPTED` on
  2026-07-03 after PR #182 checks passed.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Agent Message Backlog Reconciliation

Active role: AUDITOR

Objective:
- Reconcile the user's pasted agent/audit messages against
  `REMAINING_TASKS.md` and make sure material recommendations are visible in
  the governed backlog.

What was found:
- SHOWN: 27 pasted attachment files were available under
  `/Users/baitus/.codex/attachments/*/pasted-text.txt`.
- SHOWN: the major high-risk production blockers were already tracked:
  Decimal/venue quantization, fail-closed config, typed retry classification,
  crash/fault tests, deployment units, loop dead-man alerting,
  state-store decision record, backup/restore drill, evidence-write failure
  surfacing, advisor allow-list drift, stale runner locks, and sample-mode
  provenance.
- SHOWN: several recommendations from the pasted audits were absent or too
  implicit in the backlog: per-strategy YAML governance for challengers,
  paper/gate event alerting, pullback leaderboard/config follow-through,
  backtest expectation population, crypto-edge collection-decision urgency,
  config authority consolidation, clock skew checks, server secret rotation,
  supply-chain verification, operator/action audit coverage, paper-runner
  surface classification, signal-discovery module classification, storage
  orphan classification, future gate-library extraction, product-objective
  triage, pattern/candlestick research, and dashboard data-page wiring.

What changed:
- Updated `REMAINING_TASKS.md` active backlog items for paper manual review,
  pullback follow-through, crypto-edge collection urgency, per-strategy config
  governance, and paper/gate event alerting.
- Expanded deferred live-money backlog items for boundary quantization,
  admin-wizard strict config, loop kill-check/alert delivery proof, config
  authority consolidation, clock/venue-time checks, server secret handling,
  supply-chain checks, and operator/action audit coverage.
- Expanded deferred structure/research hygiene with paper-surface
  classification, signal-discovery module classification, storage orphan
  classification, gate-library extraction, product-objective triage,
  pattern/candlestick research, and dashboard data-page wiring.

Why this change:
- The user explicitly requested that pasted-agent recommendations stop being
  ignored and be captured in the visible backlog.
- The patch keeps runtime behavior unchanged while preserving the omitted
  audit signal for later prioritization.

Expected outcome:
- Future agents can see the full backlog surface without relying on old chat
  memory or pasted attachments.
- The active paper/shadow path remains focused, while larger product,
  research, and live-money substrate work stays visible but deferred.

Verification:
- `find /Users/baitus/.codex/attachments -name 'pasted-text.txt' -maxdepth 2 -print`
  - SHOWN: 27 pasted attachment files were available for reconciliation.
- `sed -n '1,260p' REMAINING_TASKS.md`
  - SHOWN: active and deferred backlog sections were read before editing.
- `rg -n "alert_dispatcher|dispatch_alert|AlertDispatcher" services scripts tests dashboard -g"*.py"`
  - SHOWN: alert dispatcher is used by Hetzner host health and tests, not yet
    by paper/gate event transitions.
- `rg -n "signal_library|market_ranker|candidate_strategy_mapper|trade_type_classifier|universe_loader" services scripts tests dashboard -g"*.py"`
  - SHOWN: signal-discovery modules exist and are partially wired, but their
    operator-facing production role remains unclear.

Remaining risk:
- LOW: docs/backlog reconciliation only.
- UNVERIFIED: current correctness of every historical pasted-agent claim was
  not re-proven from source; only material backlog coverage was reconciled.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Execution-Cost Research Backlog Follow-Up

Active role: ENGINEER

Objective:
- Capture the missing maker-vs-taker / execution-cost optimization research
  item identified by the user's follow-up agent review.

What was found:
- SHOWN: `rg` found no maker/taker, post-only, fee-tier, limit-fill
  probability, spread-crossing, or execution-cost backlog item in
  `REMAINING_TASKS.md`, checkpoint docs, or the work log.
- SHOWN: `services/execution/paper_engine.py` supports `limit` orders and
  evaluates open orders for fills.
- SHOWN: `services/execution/paper_fees.py` exposes a single flat
  `paper_fee_bps` model.
- SHOWN: `services/execution/fill_model.py` models fills as mid-price plus or
  minus configured bps, without maker/taker, queue, or spread-crossing
  distinctions.

What changed:
- Added a deferred live-money substrate backlog item for execution-cost
  research: maker-vs-taker rates, fee tiers, venue cost stack, modeled maker
  versus taker fills, limit-fill probability, and reproducible cost-stack
  reporting from shadow records.

Why this change:
- Execution costs can erase daily-horizon crypto signal edge, and the existing
  fill-model and shadow-recorder items did not explicitly cover maker/taker
  policy or venue fee-stack research.
- The item is scoped as research/shadow-only so it does not alter live routing
  or the canonical paper campaign while expectancy remains unproven.

Expected outcome:
- Future profitability work has a visible execution-cost research path that
  consumes shadow evidence instead of creating a second collection pipeline.

Verification:
- `rg -n "maker|taker|post-only|fee-tier|limit-fill|spread-crossing|spread crossing|execution-cost|cost stack" REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md docs/checkpoints -g"*.md"`
  - SHOWN: no matches before the backlog update.
- `rg -n "limit|fee_bps|paper_fees|apply_fee_slippage|open_orders|order_type" services/execution/paper_engine.py services/execution/fill_model.py services/execution/paper_fees.py`
  - SHOWN: paper limit-order support exists, while fee/fill modeling remains
    flat and generic.

Remaining risk:
- LOW: docs/backlog tracking only.
- UNVERIFIED: detailed implementation design and venue fee schedule sources.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Decision Checklist Backlog Follow-Up

Active role: ENGINEER

Objective:
- Capture the actionable decision checklist items from the user's latest agent
  review so they are visible in the backlog.

What was found:
- SHOWN: the backlog already tracks paper evidence collection, expectancy
  baseline, edge collection, execution-cost research, dead-man alerting,
  backup/restore, advisor strategy coverage, and shadow recorder work.
- SHOWN: the backlog did not explicitly require written stop/retirement
  criteria for individual strategies or the whole project.
- SHOWN: the backlog did not explicitly require a first-hour paper-to-shadow
  operator runbook before the paper gate turns green.
- SHOWN: the backlog used copied paper-gate counts in current-state text, but
  the checklist correctly identified operator-host gate output as the
  authoritative status artifact.

What changed:
- Updated the paper manual-review backlog item to state that fresh gate/status
  command output is the ground truth, not stale backlog counts.
- Added a backlog item requiring explicit strategy/project stop and retirement
  criteria before any strategy advances beyond paper.
- Added a backlog item requiring a first-hour paper-to-shadow runbook and
  rehearsal before the paper gate turns green.

Why this change:
- These are decision-quality controls, not code features. Without them, the
  repo can produce evidence while the operator still lacks written criteria
  for when to advance, pause, retire, or stop.

Expected outcome:
- Future gate-green events have a defined operator decision path.
- Strategy retirement and project stop decisions are made against written
  thresholds rather than emotional interpretation during drawdown or excitement.

Verification:
- `rg -n "stop criteria|kill criteria|retire|shutdown|shut down|first hour|paper.*shadow|shadow.*runbook|gate.*ground truth|cost stack|dead-man|restore drill|edge collector|expectancy baseline" REMAINING_TASKS.md docs/checkpoints docs/work_log/review_stabilized_work_log.md -g"*.md"`
  - SHOWN: related items existed, but explicit stop criteria and first-hour
    paper-to-shadow runbook language were not present before this update.

Remaining risk:
- LOW: docs/backlog tracking only.
- UNVERIFIED: exact stop thresholds and paper-to-shadow runbook content remain
  to be written in future artifacts.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Strategic Concentration Backlog Follow-Up

Active role: ENGINEER

Objective:
- Capture the user's latest pasted strategic assessment in the governed backlog
  so the repo keeps the material "full control" recommendations visible.

What was found:
- SHOWN: `REMAINING_TASKS.md` already tracked product-objective triage,
  dead-man alerting, deployment units, execution-cost research, stop criteria,
  crypto-edge collection, and shadow runbook work.
- SHOWN: the backlog did not explicitly state the lab-mode concentration
  stance: freeze desktop/product polish until expectancy is proven, focus on
  one venue/strategy pair for discovery, decide whether to widen the paper
  symbol universe to buy evidence velocity, tier governance by risk, prefer
  boring infrastructure over custom ops code, and define the repo as a
  profit-measurement lab rather than a profitable trading product.
- CLAIMED: the pasted assessment referenced broad surfaces such as desktop,
  dashboard, and companion-repo residue. This entry captures the strategic
  recommendations as backlog decisions; it does not re-audit every file count
  from that pasted text.

What changed:
- Updated the crypto-edge collection item to state that one-venue research is
  the near-term focus and multi-exchange is a later scaling objective.
- Expanded stop criteria to include a dated project-level thesis gate.
- Added an active backlog item requiring an explicit decision before widening
  the paper universe for faster qualified evidence.
- Expanded live-substrate items to prefer systemd/journald/external dead-man
  checks before more custom supervisor or alert infrastructure.
- Expanded structure/research backlog with lab-mode product-surface freeze,
  companion-repo decision, risk-tiered governance lanes, operational-core and
  quarantine policy, operator-attention protection, and repo-identity clarity.

Why this change:
- The recommendations change project direction and operator workflow, not
  runtime behavior. Capturing them as backlog/decision items is the smallest
  safe change and avoids turning strategic advice into unreviewed code churn.

Expected outcome:
- Future work can prioritize evidence velocity, profitability discovery, cost
  measurement, safety, recovery, and operator wake-up quality ahead of product
  polish or low-value audit churn.
- Future agents can see the concentration decisions in git without relying on
  chat memory.

Verification:
- `sed -n '1,420p' REMAINING_TASKS.md`
  - SHOWN: active and deferred backlog sections were read before editing.
- `tail -n 180 docs/work_log/review_stabilized_work_log.md`
  - SHOWN: existing work-log format and recent backlog entries were read before
    adding this entry.

Remaining risk:
- LOW: docs/backlog tracking only.
- UNVERIFIED: no independent source audit was performed for every pasted-file
  claim in the strategic assessment; this patch records decisions to evaluate,
  not proof that all claims are current.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Recent Attachment Reconciliation Follow-Up

Active role: ENGINEER

Objective:
- Re-read the recent pasted attachment set instead of relying on chat memory,
  then compare material recommendations against `REMAINING_TASKS.md`.

What was found:
- SHOWN: 29 pasted attachment files were present under
  `/Users/baitus/.codex/attachments/*/pasted-text.txt`, totaling 4,484 lines.
- SHOWN: the major production and research findings were already represented
  in the backlog: fail-closed config, retry typing, Decimal/venue
  quantization, crash-consistency tests, state-store consolidation, deployment
  units, dead-man alerting, full-state restore, archive-first backtesting,
  crypto-edge strategy wiring, advisor/registry drift, stale runner locks,
  sample-mode provenance, dashboard/product triage, companion-repo cleanup,
  execution-cost research, and stop criteria.
- SHOWN: several recommendations were present only implicitly or lacked
  operational specificity: sandbox lifecycle proof can be run before the paper
  gate because it is no-capital testnet learning, archive work should feed
  systematic parameter sweeps and walk-forward discovery, `funding_extreme`
  should be treated as the flagship profitability hypothesis once wired,
  edge-collector history should be collected beyond the active campaign and
  alerted on cadence gaps, and Hetzner runbooks must distinguish server
  commands from laptop commands with verified privilege/venv prerequisites.

What changed:
- Updated the sandbox/testnet lifecycle item to state it can be executed before
  the paper gate clears if kept isolated and no-capital.
- Expanded archive-first backtesting to include post-archive parameter-sweep
  and walk-forward research throughput.
- Expanded crypto-edge strategy wiring to frame `funding_extreme` as the first
  profitability hypothesis, with `es_daily_trend_v1` remaining the
  pipeline-validation strategy unless evidence changes that.
- Expanded scheduled edge collection with broader symbol/second-venue data
  hoarding and a cadence-gap alert requirement.
- Expanded Hetzner follow-through with explicit host privilege, venv/app-path,
  Tailscale host, and laptop-vs-server command requirements.

Why this change:
- The user explicitly challenged whether recent pasted messages had actually
  been read. This change makes the reconciliation visible in git and captures
  the remaining materially distinct recommendations without touching runtime
  code.

Expected outcome:
- The backlog better preserves the strategic direction from the recent
  attachments: improve evidence velocity, widen edge discovery, avoid
  deployment/runbook confusion, and do no-capital execution-stack learning in
  parallel with paper evidence collection.

Verification:
- `find /Users/baitus/.codex/attachments -maxdepth 2 -name pasted-text.txt -print | sort`
  - SHOWN: 29 pasted attachment files were available.
- `wc -l /Users/baitus/.codex/attachments/*/pasted-text.txt`
  - SHOWN: 4,484 total lines across the pasted attachment set.
- `sed -n '70,230p' REMAINING_TASKS.md`
  - SHOWN: active backlog items were read before patching the missing
    refinements.

Remaining risk:
- LOW: docs/backlog tracking only.
- UNVERIFIED: some attachment command-output logs were truncated in terminal
  display during review; the patch captures material recommendations observed
  from the readable attachment content, but it is not a source-code re-audit of
  every claim inside those attachments.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Candidate Advisor Strategy Classification Guard

Active role: ENGINEER

Objective:
- Prevent the candidate advisor's strategy allow-list from silently drifting
  away from the executable strategy registry.

What was found:
- SHOWN: `services/strategies/strategy_registry.py::SUPPORTED` registers nine
  OHLCV strategies.
- SHOWN: `services/signals/candidate_advisor.py::ALLOWED_STRATEGIES` allowed
  only five of those strategies.
- SHOWN: the omitted registry strategies were `breakout_volume`, `gap_fill`,
  `sma_200_trend`, and `volatility_reversal`.
- SHOWN: no existing test required advisor strategies to be explicitly allowed
  or explicitly excluded.

What changed:
- Added `ADVISOR_EXCLUDED_STRATEGIES` with one-line rationales for the four
  registered strategies that are intentionally not advisor-selectable yet.
- Added `tests/test_candidate_advisor_classification.py` to assert every
  registry strategy is classified as either advisor-allowed or
  advisor-excluded, that the sets do not overlap, and that exclusion rationales
  are non-empty.
- Updated `REMAINING_TASKS.md` item 19 to record the implementation proof.

Why this change:
- Future strategy additions should not disappear from the advisor path by
  omission. A failing classification test forces a conscious allowed/excluded
  decision whenever the registry changes.

Expected outcome:
- Candidate discovery coverage becomes explicit and regression-guarded without
  changing runtime advisor recommendations.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_candidate_advisor_classification.py tests/test_candidate_layer.py`
  - SHOWN: `42 passed in 0.27s`.
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- MEDIUM: this is strategy-discovery governance, not execution or live routing.
- Runtime behavior is intended to remain unchanged because the allow-list is
  unchanged; only omitted strategies now have documented rationales.
- Independently reviewed and accepted by the human operator on 2026-07-03.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Single-Operator Continuity Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's production-repo comparison and add any missing backlog task
  that materially improves production readiness.

What was found:
- SHOWN: `REMAINING_TASKS.md` already tracks Decimal money math, transactional
  state decisions, typed retry classification, crash/fault tests, systemd
  deployment, loop heartbeats/dead-man alerting, full-state restore drills,
  duplicate safety modules, sandbox lifecycle proof, and operator stop
  criteria.
- SHOWN: the backlog did not explicitly require a single-operator continuity or
  absence runbook, even though the pasted assessment correctly identified that
  the repo's recovery knowledge still depends heavily on one operator.

What changed:
- Added active backlog item 27 requiring a single-operator continuity and
  absence runbook before shadow or server migration becomes the primary
  operating mode.

Why this change:
- The repo's technical controls are only production-grade if they fail safe
  while the operator is asleep, unavailable, or disconnected. This item turns
  that human-dependency risk into a concrete operator-workflow artifact.

Expected outcome:
- Future shadow/server operation has a written answer for what continues,
  alerts, degrades, stops, can be accessed, can be restored, and must not be
  touched when the operator is unavailable.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: backlog/work-log only.
- UNVERIFIED: the actual runbook content, access model, and emergency delegate
  remain to be written and reviewed later.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Edge Collector And Baseline Sequencing Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's autonomous-execution sequencing plan and capture missing
  backlog refinements that improve evidence velocity and gate readiness.

What was found:
- SHOWN: `REMAINING_TASKS.md` already tracks shadow would-be-fill recording,
  archive-first backtesting, crypto-edge strategy wiring, edge-collector
  cadence alerts, full-state drills, and process-cap/operator attention.
- SHOWN: the backlog did not explicitly state that `es_daily_trend_v1`
  expectancy fields should prefer an archive-backed multi-year baseline if the
  archive lands before manual review.
- SHOWN: the edge-collector item required scheduled collection and cadence-gap
  alerts, but did not explicitly require a first operational proof showing host
  schedule state, recent snapshot timestamps, and cadence gaps before downstream
  strategy wiring depends on the history.

What changed:
- Updated the paper manual-review item to prefer archive-backed, dataset-hashed
  multi-year baseline metrics before populating `es_daily_trend_v1.yaml`
  expectancy fields.
- Updated the scheduled crypto-edge collection item to require a first
  post-source-decision operational proof of scheduler and snapshot cadence.

Why this change:
- These are sequencing details that prevent two common failure modes:
  populating a gate baseline from shallow non-reproducible data, and wiring
  `funding_extreme` against an edge-history clock that is not actually running.

Expected outcome:
- When the paper gate reaches manual review, the expectancy comparison points
  at the best available reproducible dataset.
- When crypto-edge wiring begins, the team already has proof that funding/OI
  history is accruing on schedule.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: backlog/work-log only.
- UNVERIFIED: the archive implementation, edge collector scheduler, and
  baseline regeneration remain future work.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - AI Copilot And AI Engine Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's AI-layer audit and add any missing backlog tasks that
  materially affect production readiness.

What was found:
- SHOWN: `docs/AI_COPILOT_BOUNDARY.md` already states that AI/copilot surfaces
  are advisory and cannot become direct live-trading authority.
- SHOWN: `services/ai_copilot/context_collector.py::_safe_sqlite_query` opens
  SQLite databases through a normal read-write connection while accepting a SQL
  string from its caller. Current callers pass hardcoded read queries, but the
  read-only assumption is not enforced by the helper.
- SHOWN: `services/live_router/router.py` can enable `services/ai_engine`
  through env/config and, on AI-service/model exceptions, records
  `ai_error_ignored` with `ok=true` unless strict mode is explicitly enabled.
- SHOWN: `docs/AI_ENGINE.md` documents default pass-through behavior for the
  AI engine.
- CLAIMED: the attached audit characterizes `services/ai_copilot` as generally
  capability-limited/read-only and `services/ai_engine` as the material
  doctrine violation. That broader package assessment was not fully re-audited
  in this patch.

What changed:
- Added a deferred live-money substrate backlog item requiring the optional
  `ai_engine` live-router hook to be quarantined or made fail-closed before any
  capped-live exposure.
- Added a deferred structure/research-hygiene backlog item requiring enforced
  read-only SQLite access for AI-copilot context collection, explicit provider
  data-governance documentation for `use_ai=true`, and advisory-only handling
  for the LLM PR reviewer unless a stronger design is accepted.

Why this change:
- The AI-engine hook sits on an order-routing path and should not be treated as
  a generic research scaffold if it can fail open when enabled.
- The copilot context collector is lower risk today, but its helper name
  implies a safety property the code does not enforce. Recording the gap keeps
  future AI-summary work bounded by actual read-only controls.

Expected outcome:
- Live-readiness work has an explicit AI-engine quarantine/fail-closed blocker
  instead of relying on broad fail-open backlog language.
- AI-copilot reporting can mature without accidentally widening data-access or
  provider-disclosure assumptions.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: this patch is backlog/work-log only.
- HIGH for the future `ai_engine` implementation because it touches live order
  routing and fail-open behavior; that future code change must stop at
  `READY_FOR_INDEPENDENT_REVIEW`.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Dashboard Resume Gate And Deep-Audit Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's deep audit of previously unexamined areas and add missing
  backlog tasks or refinements that materially affect production readiness.

What was found:
- SHOWN: `services/admin/resume_gate.py::resume_if_safe()` can write
  `execution.live_enabled=true` when live is not enabled, calls
  `live_allowed()` with kill-switch and system-guard halted bypasses, sets live
  armed state, sets `CBP_EXECUTION_ARMED=YES`, disarms the kill switch, and sets
  the system guard RUNNING.
- SHOWN: `dashboard/pages/60_Operations.py` exposes that path through the
  `Resume Live Trading` button.
- SHOWN: `services/execution/live_enable.py` is a separate token/checklist
  ceremony, so dashboard resume is not currently constrained to prior
  ceremony provenance.
- SHOWN: `scripts/check_promotion_gates.py::_count_round_trips()` counts
  `min(buys, sells)` without symbol-aware chronological pairing.
- SHOWN: `.github/workflows/ci.yml` runs pytest with permanent `--ignore`
  entries for `tests/test_symbol_scanner.py`,
  `tests/test_dashboard_view_data.py`,
  `tests/test_dashboard_page_runtime.py`, and
  `tests/test_dashboard_home_digest.py`.
- SHOWN: `services/execution/live_reconciler.py` contains a
  verify-before-retry path for `submit_unknown` intents through
  client-order-id lookup.
- CLAIMED: the attached audit's broader dashboard/reconciler/supervisor/
  packaging conclusions were not fully re-audited in this patch.

What changed:
- Added a deferred live-money substrate backlog item requiring the dashboard
  resume path to preserve resume-hard governance: no cold write of
  `live_enabled`, valid prior live-enable ceremony provenance, bounded arming
  window, and targeted tests.
- Refined the paper-universe widening item to require symbol-aware,
  chronological round-trip pairing before cross-symbol fills count toward a
  gate, or an explicit single-symbol-only gate policy.
- Refined the retry-classification live blocker to record that
  verify-before-retry exists, with remaining work focused on typed exception
  classification, fault-injection proof, and venue-lookup-not-found policy.
- Refined the duplicate safety-module task with the current four-module
  kill-switch map.
- Added a CI/test hygiene item requiring the permanently ignored tests to be
  made CI-safe, moved to a named optional job, or replaced by covered slices.

Why this change:
- The resume path is a governance bypass in an action-capable dashboard
  surface. It is not active while strategies remain paper-stage, but it must be
  fixed before capped-live exposure.
- Multi-symbol evidence acceleration should not reuse a single-symbol
  round-trip helper.
- CI should not silently exempt dashboard and scanner behavior without a named
  policy.

Expected outcome:
- Future live-readiness work has a specific resume-gate blocker instead of a
  broad "dashboard write surface" concern.
- Multi-symbol campaign planning keeps the evidence contract honest.
- Existing retry/reconciler work is scoped to the remaining proof gaps, not
  re-solving a mechanism that is already present.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: this patch is backlog/work-log only.
- HIGH for the future resume-gate implementation because it touches live
  arming/governance behavior; that code change must stop at
  `READY_FOR_INDEPENDENT_REVIEW`.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Fee, Heartbeat, And Fail-Open Guard Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's proactive audit findings covering paper profitability
  measurement, watchdog heartbeats, market-quality defaults, stale intents, and
  non-evidence order gates, then add any missing backlog tasks or refinements.

What was found:
- SHOWN: `storage/paper_trading_sqlite.py::apply_fill()` subtracts buy fees
  from cash and sell fees from proceeds, but returned/stored
  `realized_pnl_usd` is gross of fees.
- SHOWN: `services/execution/paper_engine.py` logs sell-fill evidence
  `pnl_usd` from `realized_pnl_usd`, and
  `scripts/check_promotion_gates.py::_check_expectancy()` gates on `pnl_usd`.
- SHOWN: `services/execution/paper_fees.py::fee_bps_paper()` defaults to
  `0.0` when no paper fee is configured.
- SHOWN: `services/process/heartbeat.py::write_heartbeat()` exists, but repo
  search found no callers while `services/process/watchdog.py` reads heartbeat
  state and can arm the kill switch / set `HALTING` on staleness.
- SHOWN: `services/risk/market_quality_guard.py` defaults to
  `block_when_unknown=false`, `require_bid_ask=false`, `max_spread_bps=500`,
  and missing quotes can return `ok=true`, `reason=no_quote_data`.
- SHOWN: `storage/live_intent_queue_sqlite.py` claims queued intents by
  `created_ts ASC` with no visible TTL/age filter in the queue.
- SHOWN: `services/feature_gate.py::proba_gate()` can influence order flow from
  `CBP_FUSED_PROBA` and tolerates missing/invalid values when strict mode is
  false.
- SHOWN: `services/execution/paper_engine.py` falls back to `60000.0` when no
  usable reference price is available for pre-submit safety checks.
- CLAIMED: the pasted audit's broader statements about paper maker-fill
  semantics, retention policy, and watchdog host scheduling were not fully
  re-audited beyond the targeted code checks above.

What changed:
- Added active backlog item 28 to fix paper fee/PnL semantics before treating
  expectancy gates as profitability evidence.
- Added active backlog item 29 to make market-quality defaults/config fail
  closed before shadow cost/slippage evidence is trusted.
- Refined the trading-loop metrics/dead-man item with the dormant heartbeat
  writer finding, required loop writers, watchdog alert dispatch, host
  scheduling proof, and watchdog-surface consolidation.
- Refined the maker-vs-taker execution-cost item to state that current paper
  fills cannot be used as maker-fill evidence without shadow records or an
  explicit engine extension.
- Refined the AI/probability gate quarantine item to include `proba_gate`.
- Added live substrate items for stale intent TTL and hardcoded paper
  reference-price fallback removal.
- Added a structure/research-hygiene item for explicit retention policy.
- Refined the runner stale-lock item to reuse the existing stale-lock helper if
  possible.

Why this change:
- The paper gate's expectancy surface is the bridge between "machinery works"
  and "strategy may be profitable"; gross PnL and zero-fee defaults can make a
  net-negative strategy appear gate-positive.
- Watchdog design is only useful if managed loops write the heartbeat and
  operators are alerted when it fires.
- Fail-open market-quality and probability-gate defaults share the same safety
  pattern: guards must fail closed by default or carry an explicit opt-out
  decision.

Expected outcome:
- The backlog now separates evidence/profitability correctness from broader
  live-money substrate work.
- Future shadow/live work has explicit tasks for stale intent expiry, real
  heartbeat inputs, and reference-price fail-closed behavior.
- Existing broad execution-cost and AI-quarantine tasks now include the newly
  verified constraints.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: this patch is backlog/work-log only.
- HIGH for future implementations touching PnL semantics, live consumers,
  watchdog behavior, market-quality gating, or order-routing gates; those code
  changes require independent review as governed high-risk work.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Trader Method Stack Backlog Follow-Up

Active role: ENGINEER

Objective:
- Review the user's final method-stack audit and capture any missing backlog
  tasks that move the repo toward disciplined, evidence-backed strategy
  improvement rather than more raw finding generation.

What was found:
- SHOWN: `services/strategies/es_daily_trend.py::regime_stability()` computes
  market regime, entry allowance, and size factor.
- SHOWN: `configs/strategies/es_daily_trend_v1.yaml` enables
  `entry.require_regime: true`.
- SHOWN: `services/strategies/es_daily_trend.py::signal_from_ohlcv()` gates
  action on both SMA signal and `reg["entry_allowed"]`, then logs
  `regime_flag` and `entry_allowed`.
- SHOWN: `services/strategies/es_daily_trend.py::decide()` and
  `compute_position_size()` implement ATR-stop/capital-at-risk sizing, but repo
  search found usage only in tests while the strategy runner emits orders using
  fixed `cfg["qty"]`.
- SHOWN: `services/strategies/composite_hybrid.py` has confirmation-gate logic,
  and tests assert `composite_hybrid` is intentionally not in
  `strategy_registry.SUPPORTED`.
- SHOWN: `services/signals/signal_library.py`,
  `services/market_data/composite_ranker.py`, and
  `services/market_data/rotation_engine.py` contain setup-quality /
  symbol-selection machinery.
- SHOWN: paper diagnostic and loss-replay tooling exists through
  `scripts/report_paper_run_diagnostics.py`,
  `scripts/dev/replay_paper_losses.py`, and the AI-copilot simulation job.
- UNVERIFIED: whether every non-flagship strategy's documented no-trade
  filters are enabled in its actual campaign config.

What changed:
- Refined the crypto-edge context-strategy item to include a shared
  `regime_context` provider extracted from existing `sma_200_trend` regime
  logic, with unchanged flagship behavior as proof.
- Refined per-strategy governance-config requirements to include explicit
  no-trade filter enablement or waiver.
- Refined the fee/PnL item to block activation of sizing, setup-quality
  thresholds, confirmation gates, and sweeps until net-fee metrics are fixed.
- Added a governed activation task for dormant risk-based sizing.
- Refined dormant signal-discovery classification to include
  `composite_ranker` and `rotation_engine`, and to require archive
  walk-forward proof before setup scores affect trade/no-trade or sizing.
- Added a weekly strategy-review ritual task using existing diagnostics and
  loss-replay tooling.

Why this change:
- The repo already contains several pieces of a disciplined trader method
  stack. The production gap is unification, activation governance, and review
  cadence, not inventing more prediction logic.
- Dormant sizing and confirmation should not be switched on until the
  measurement target is net-fee and archive-backed, or the system could
  optimize the wrong metric.

Expected outcome:
- Future strategy-improvement work is sequenced through shared context,
  archive/walk-forward proof, net-fee metrics, and explicit operator review
  artifacts.
- The backlog now distinguishes active flagship regime gating from missing
  shared regime availability for other strategies.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: this patch is backlog/work-log only.
- MEDIUM/HIGH for future implementation, depending on whether it changes
  strategy sizing, campaign configs, context provenance, or promotion evidence.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Candidate Advisor Acceptance Record

Active role: ENGINEER

Objective:
- Record the human operator's independent acceptance for the candidate-advisor
  strategy classification guard.

What was found:
- SHOWN: `REMAINING_TASKS.md` item 19 still described the implementation proof
  as ready for review after the human operator accepted it.
- SHOWN: the candidate-advisor work-log entry still ended at
  `READY_FOR_INDEPENDENT_REVIEW`.

What changed:
- Updated `REMAINING_TASKS.md` item 19 to state the implementation proof was
  independently reviewed and accepted by the human operator on 2026-07-03.
- Updated the candidate-advisor work-log entry acceptance state to `ACCEPTED`.

Why this change:
- Accepted work should not remain marked as pending review; stale acceptance
  states make the visible audit trail less trustworthy.

Expected outcome:
- The backlog and work log now match the human review decision for PR #185's
  candidate-advisor guard.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: acceptance-record documentation only.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Operator Runbook And Governance Backlog Batch

Active role: ENGINEER

Objective:
- Advance as many low-risk backlog items as possible in one pass without
  touching high-risk money, live, gate, or background-job code paths.

What was found:
- SHOWN: `REMAINING_TASKS.md` had written-runbook/policy tasks for strategy
  stop criteria, first-hour paper-to-shadow operation, single-operator
  continuity, governance lanes, operator attention, repo identity, and
  retention policy.
- SHOWN: `docs/RUNBOOKS.md`, `docs/GOLDEN_PATH.md`, `docs/OBJECTIVE.md`, and
  `docs/LOG_POLICY.md` existed as the visible places to link or clarify these
  operator policies.
- SHOWN: `docs/runbooks/` did not exist, so adding unlinked runbook files there
  would create another source-of-truth convention.
- UNVERIFIED: first-hour shadow rehearsal, backup restore rehearsal, dead-man
  alert delivery, and server-specific retention thresholds still require future
  runtime proof.

What changed:
- Added `docs/STRATEGY_STOP_AND_RETIREMENT_POLICY.md`.
- Added `docs/PAPER_TO_SHADOW_FIRST_HOUR_RUNBOOK.md`.
- Added `docs/SINGLE_OPERATOR_CONTINUITY.md`.
- Added `docs/OPERATOR_GOVERNANCE_LANES.md`.
- Added `docs/RETENTION_POLICY.md`.
- Added `docs/PROJECT_IDENTITY_AND_SCOPE.md`.
- Linked the new policies from `docs/RUNBOOKS.md`, `docs/GOLDEN_PATH.md`,
  `docs/OBJECTIVE.md`, and `docs/LOG_POLICY.md`.
- Updated `REMAINING_TASKS.md` to record which policy/runbook work is written
  and which rehearsal or host-specific proof remains open.

Why this change:
- These tasks were decision/runbook gaps that could be closed or materially
  advanced without waiting for campaign round trips and without changing
  financial runtime behavior.
- The high-risk backlog items remain separate because they require targeted
  implementation proof and independent review.

Expected outcome:
- Operators now have visible written criteria for strategy retirement,
  paper-to-shadow first-hour operation, one-operator absence, governance
  friction, repo identity, and retention.
- Future runtime work has clearer preconditions and proof requirements instead
  of relying on chat history.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: documentation/runbook/policy changes only.
- MEDIUM/HIGH: future implementation work that changes stage transitions,
  strategy gates, shadow evidence, retention deletion, backup automation, or
  alerting still requires separate proof and review.
- Acceptance state: `ACCEPTED`.

## 2026-07-03 - Structure Classification Backlog Batch

Active role: ENGINEER

Objective:
- Advance the next batch of low-risk deferred structure/research hygiene tasks
  through current-source classification and visible policy docs.

What was found:
- SHOWN: `git ls-files services/paper ...` found no tracked `services/paper/`
  source, while `services/paper_trader/` and `services/execution/paper_engine.py`
  remain tracked.
- SHOWN: `services/execution/paper_engine.py` is imported by canonical paper
  execution adapters/tests; `services/paper_trader/` is still used by
  `services/trading_runner/run_trader.py` and compatibility tests.
- SHOWN: signal discovery modules are imported by the read-only candidate scan
  and tests, while `composite_ranker` / `rotation_engine` are consumed by
  selector backtests.
- SHOWN: `order_dedupe_store_sqlite` and `execution_guard_store_sqlite` are
  active live/execution boundary stores, while `fill_reconciler_store_sqlite`,
  `order_idempotency_sqlite`, and `order_tracker_store_sqlite` had no visible
  current source importers in the static grep used for this pass.
- SHOWN: `.github/workflows/ci.yml` and `Makefile` ignore four dashboard /
  symbol-scanner test files in the normal pytest path.
- SHOWN: docs and smoke scripts reference `phase1_research_copilot/`, but
  `git ls-files phase1_research_copilot` showed no tracked companion source.
- SHOWN: `docs/REPO_LAYOUT.md` still described retired overlap families as
  current unresolved examples, while `docs/ARCHITECTURE.md` marks those
  families retired as of 2026-07-01.

What changed:
- Added `docs/CORE.md`.
- Added `docs/architecture/paper_execution_surfaces.md`.
- Added `docs/research/signal_discovery_classification.md`.
- Added `docs/architecture/storage_surface_classification.md`.
- Added `docs/CI_IGNORED_TEST_POLICY.md`.
- Added `docs/PRODUCT_SURFACE_TRIAGE.md`.
- Added `docs/COMPANION_REPO_DEPENDENCY.md`.
- Added `docs/research/pattern_strategy_backlog.md`.
- Added `docs/dashboard/DATA_PAGE_BACKLOG.md`.
- Added `docs/STRATEGY_REVIEW_RITUAL.md`.
- Linked the new docs from `docs/ARCHITECTURE.md`, `docs/GOLDEN_PATH.md`,
  `docs/RUNBOOKS.md`, and `docs/REPO_LAYOUT.md`.
- Updated `REMAINING_TASKS.md` to record which classification/policy tasks are
  documented and which implementation or proof work remains.

Why this change:
- These backlog tasks were source-of-truth and classification gaps that could
  be advanced without changing runtime behavior or restarting any campaign.
- Capturing the decisions now reduces repeated rediscovery and prevents agents
  from treating archived, retired, or advisory surfaces as active production
  requirements.

Expected outcome:
- Future work can distinguish core, research-only, advisory-only,
  compatibility, retired, and sidecar surfaces before implementing changes.
- CI ignored tests, companion repo references, dashboard priorities, and
  product-surface deferrals are visible policy decisions rather than chat-only
  context.

Verification:
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: docs/classification only; no runtime behavior changed.
- MEDIUM/HIGH: future deletion, rewiring, CI behavior changes, dashboard
  mutations, or storage consolidation still require separate targeted proof and
  review.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Repo Layout CI Compatibility Fix

Active role: ENGINEER

Objective:
- Fix the PR #185 CI failure caused by the structure-classification docs batch.

What was found:
- SHOWN: PR #185 `CI sanity` failed in
  `tests/test_repo_layout_scope_doc.py`.
- SHOWN: the failing assertions expected
  `actively referenced from the main README, Makefile, dashboard research fallback, and tests`
  and the historical overlap examples ``market_data/` and `marketdata/``,
  ``paper/` and `paper_trader/``, ``strategy/` and `strategies/``, and
  ``trading/` and `trading_runner/`` to remain visible in
  `docs/REPO_LAYOUT.md`.

What changed:
- Restored those tested phrases in `docs/REPO_LAYOUT.md` while preserving the
  newer sidecar/archived companion and retired-family classification language.

Why this change:
- The previous docs batch changed wording that existing CI treats as a
  regression guard. Restoring the phrases keeps compatibility with the guard
  without weakening the new classification decision.

Expected outcome:
- PR #185 `CI sanity` and `CI validate` no longer fail on
  `tests/test_repo_layout_scope_doc.py`.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_repo_layout_scope_doc.py`
  - SHOWN: `9 passed in 0.08s`.
- `git diff --check`
  - SHOWN: command completed successfully.

Remaining risk:
- LOW: docs-only compatibility fix.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Paper Fee PnL Semantics Fix

Active role: ENGINEER

Objective:
- Correct forward paper PnL semantics so expectancy evidence is net of paper
  fees instead of gross of fees.

What was found:
- SHOWN: `storage/paper_trading_sqlite.py::apply_fill()` subtracted buy fees
  from cash and sell fees from proceeds, but returned/stored sell
  `realized_pnl_usd` as `(sell_price - avg_price) * qty`.
- SHOWN: `services/execution/paper_engine.py` wrote that value to strategy fill
  evidence as `pnl_usd`.
- SHOWN: `scripts/check_promotion_gates.py::_check_expectancy()` gates on
  `pnl_usd`.

What changed:
- Updated paper buy fills to fold fees into average cost basis.
- Updated paper sell fills to compute realized PnL as fee-adjusted proceeds
  minus fee-inclusive cost basis.
- Added `pnl_usd_semantics=net_of_fees` to new paper fill results and evidence
  records.
- Updated the paper-engine fill-evidence regression so a flat round trip with
  10 bps fees records negative `pnl_usd`.
- Added a promotion-gate helper regression proving negative net-fee PnL fails
  expectancy.
- Updated `REMAINING_TASKS.md` item 28 with implementation-proof status and
  remaining review/config checks.

Why this change:
- The paper gate's expectancy surface is the bridge between "the machinery
  works" and "the strategy may be profitable." Gross-of-fee PnL can let
  fee-negative strategies appear profitable.
- Folding fees into cost basis is the smallest forward-compatible change that
  makes new paper evidence net of both buy and sell fees without adding a DB
  migration.
- The semantics marker preserves historical comparability: old records lack
  `pnl_usd_semantics`, new records explicitly identify `net_of_fees`.

Expected outcome:
- New paper evidence and paper-gate expectancy checks use net-fee PnL for paper
  fills produced through the canonical paper engine.
- A flat-price round trip with fees is treated as a losing trade instead of a
  break-even trade.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_engine_integration.py`
  - SHOWN: `12 passed in 0.49s`.
- `./.venv/bin/python -m pytest -q tests/test_paper_engine_integration.py tests/test_check_promotion_gates.py`
  - SHOWN: `56 passed in 1.66s`.

Remaining risk:
- HIGH: this changes financial/evidence semantics; human/operator independent
  review accepted the implementation on 2026-07-04.
- UNVERIFIED: active campaign config fee/slippage values were not read from the
  operator host in this implementation pass.
- UNVERIFIED: historical paper evidence remains gross or unknown semantics
  unless regenerated or explicitly segmented during analysis.
- Acceptance state: `ACCEPTED_WITH_RISK`.

## 2026-07-04 - Paper Market Quality Reference Price Guard

Active role: ENGINEER

Objective:
- Make the canonical paper engine fail closed when market-quality output lacks
  a usable reference price.

What was found:
- SHOWN: `services/risk/market_quality_guard.py` can return `ok=true` with
  `reason=no_quote_data` when `block_when_unknown` is not configured.
- SHOWN: `services/execution/paper_engine.py::_pre_submit_gate()` previously
  used `60000.0` as a fallback reference price when market-quality output did
  not include `price_used` or `last`.
- SHOWN: active backlog item 29 requires missing-quote fixtures to hold
  orders/signals with an operator-visible reason before shadow cost evidence is
  trusted.

What changed:
- Removed the paper pre-submit fallback from missing/invalid reference price to
  `60000.0`.
- Added a deterministic `market_quality:no_reference_price` block when neither
  limit price nor market-quality `price_used`/`last` is usable.
- Added a paper-engine regression where market quality returns `ok=true` with
  `reason=no_quote_data` and no price fields; the order is not inserted.
- Updated `REMAINING_TASKS.md` item 29 to mark this as partial implementation
  proof and preserve the remaining strict-config/default-flip work.

Why this change:
- A hardcoded BTC-shaped reference price can make safety/notional checks run on
  garbage when quote data is missing.
- Blocking the paper order at the canonical evidence path is the smallest
  useful hardening step and avoids changing live routing or global
  market-quality defaults before the requested observed cycle.

Expected outcome:
- Paper evidence cannot record an order based on a synthetic fallback reference
  price when market quality has no usable quote.
- Operators see the explicit block reason
  `market_quality:no_reference_price`.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_engine_integration.py`
  - SHOWN: `13 passed in 0.51s`.

Remaining risk:
- HIGH: this changes paper execution gate behavior; human/operator independent
  review accepted the implementation on 2026-07-04.
- UNVERIFIED: active campaign market-quality config was not changed or observed
  for a no-storm cycle in this pass.
- UNVERIFIED: live intent consumers and legacy executor submit paths still need
  separate review before any equivalent live/shadow behavior change.
- Acceptance state: `ACCEPTED_WITH_RISK`.

## 2026-07-04 - Fixed-Size Sizing Activation Guard

Active role: ENGINEER

Objective:
- Guard the canonical strategy runner against accidental activation of dormant
  risk-based sizing for `sma_200_trend`.

What was found:
- SHOWN: `services/strategies/es_daily_trend.py::compute_position_size()` and
  `decide()` implement capital-at-risk sizing.
- SHOWN: `services/execution/strategy_runner.py` emits strategy intents using
  `qty = float(cfg["qty"])`.
- SHOWN: `REMAINING_TASKS.md` item 30 requires fixed-size behavior unchanged by
  default before any future risk-based sizing activation.

What changed:
- Added a strategy-runner regression where `sma_200_trend` has risk-sizing
  fields present but still emits the configured fixed `qty`.
- Updated `REMAINING_TASKS.md` item 30 to record the guard and keep actual
  risk-based sizing activation deferred behind archive/walk-forward proof,
  explicit config, size provenance, and exposure-cap tests.

Why this change:
- The repo already has sizing logic, but accidental activation would change
  paper evidence semantics. A test guard is the smallest useful protection
  while the sizing policy remains unproven.

Expected outcome:
- Future changes that switch `sma_200_trend` from fixed-size campaign behavior
  to risk-based sizing must update the guard and provide the activation proof.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_runtime_runner.py::test_run_forever_keeps_sma_200_trend_fixed_size_when_risk_sizing_config_present`
  - SHOWN: `1 passed in 0.16s`.

Remaining risk:
- LOW: test/backlog/work-log only; runtime behavior was not changed.
- UNVERIFIED: actual risk-based sizing activation design and walk-forward proof
  remain future work.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Paper Ledger Invariant Coverage

Active role: ENGINEER

Objective:
- Close the deferred backlog item requiring direct invariant tests around
  `PaperTradingSQLite.apply_fill()`.

What was found:
- SHOWN: `storage/paper_trading_sqlite.py::apply_fill()` updates order status,
  fills, position quantity/average price, cash, and realized PnL in one
  transaction.
- SHOWN: existing paper-engine tests covered fee semantics through the engine
  path, but the deferred backlog item specifically asked for direct storage
  invariant coverage.

What changed:
- Added direct storage-level tests for a mixed buy/sell fill sequence.
- Added a flat-price round-trip test proving fees make net realized PnL
  negative.
- Updated `REMAINING_TASKS.md` item 7 with the implementation proof.

Why this change:
- The ledger is the accounting substrate behind paper evidence. Direct tests
  make the cash/position/fill/PnL reconciliation invariant visible even if the
  engine path changes later.

Expected outcome:
- Future changes to `PaperTradingSQLite.apply_fill()` that break fee-inclusive
  average cost, net realized PnL, cash reconciliation, filled order status, or
  fill insertion will fail a narrow regression before affecting evidence.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_trading_sqlite_invariants.py`
  - SHOWN: `2 passed in 0.13s`.

Remaining risk:
- LOW: test/backlog/work-log only; runtime behavior was not changed.
- UNVERIFIED: broader paper-engine and gate suites were not rerun in this pass
  by operator request to avoid excessive long-running tests.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - State Store Consolidation Decision Record

Active role: ENGINEER

Objective:
- Close the backlog requirement to write a state-store consolidation decision
  record before implementation.

What was found:
- SHOWN: `PaperTradingSQLite` is the paper execution accounting authority for
  paper orders, fills, positions, cash, and realized PnL.
- SHOWN: `TradeJournalSQLite` is a paper/history evidence surface consumed by
  feedback and promotion paths.
- SHOWN: `ExecutionStore`, live intent/position/risk stores, and execution DB
  tables remain separate live/execution surfaces.
- SHOWN: storage-surface classification already exists, but it did not state a
  consolidation target or accepted-risk boundary.

What changed:
- Added `docs/architecture/state_store_consolidation_decision.md`.
- Updated `REMAINING_TASKS.md` live-money substrate item 7 to link the decision
  and preserve remaining migration/proof work.

Why this change:
- The repo needed a written ownership and migration policy before more
  reconciliation or live-accounting work adds new stores or broadens state
  drift.

Expected outcome:
- Future storage work has a documented rule: freeze current store ownership
  during the paper campaign, treat evidence as derivative rather than
  accounting authority, and require transactional/fault-injection proof before
  capped-live reliance.

Verification:
- `git diff --check`
  - SHOWN: passed with no whitespace errors.

Remaining risk:
- LOW: docs/backlog/work-log only; no runtime behavior changed.
- UNVERIFIED: actual transactional migration, fault-injection tests, and
  backup/restore drill remain future capped-live work.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Storage Candidate Caller Audit

Active role: ENGINEER

Objective:
- Complete the current-master caller audit for the three storage modules
  previously classified as unwired candidates.

What was found:
- SHOWN: `storage/fill_reconciler_store_sqlite.py` defines
  `FillReconcilerStoreSQLite`.
- SHOWN: `storage/order_idempotency_sqlite.py` defines
  `OrderIdempotencySQLite`.
- SHOWN: `storage/order_tracker_store_sqlite.py` defines
  `OrderTrackerStoreSQLite`.
- SHOWN: static caller audit across `services`, `scripts`, `storage`, `tests`,
  `docs`, and `REMAINING_TASKS.md` found no visible current production source
  importer for those modules; matches were the modules themselves and prior
  docs/audit artifacts.

What changed:
- Updated `docs/architecture/storage_surface_classification.md` with the
  2026-07-04 caller audit command and result.
- Updated `REMAINING_TASKS.md` item 10 with the current audit result and the
  remaining delete/migrate/retain decision.

Why this change:
- Reconciliation work should not build on dormant or duplicate storage schemas
  without an explicit migration decision.

Expected outcome:
- Future reconciliation/storage work can see that these three modules are still
  unwired candidates and must not be adopted accidentally.

Verification:
- Caller audit command is recorded in
  `docs/architecture/storage_surface_classification.md`.
  - SHOWN: only self/docs/audit artifact matches for the three candidate
    modules.

Remaining risk:
- LOW: docs/backlog/work-log only; no runtime behavior changed.
- UNVERIFIED: archived/migration data dependency on these schemas was not
  proven or disproven.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Strategy Review Make Target

Active role: ENGINEER

Objective:
- Convert the documented weekly strategy-review ritual into an explicit
  operator-run command without adding automatic scheduling.

What was found:
- SHOWN: `docs/STRATEGY_REVIEW_RITUAL.md` documented the weekly review inputs
  and suggested commands.
- SHOWN: `Makefile` had paper status and evidence targets but no
  `strategy-review` target.
- SHOWN: `scripts/report_paper_run_diagnostics.py` and
  `scripts/dev/replay_paper_losses.py` already exist.

What changed:
- Added `make strategy-review`.
- Added overridable variables:
  `STRATEGY_REVIEW_STRATEGY_ID`, `STRATEGY_REVIEW_SYMBOL`, and
  `STRATEGY_REVIEW_LOSS_LIMIT`.
- Updated `docs/STRATEGY_REVIEW_RITUAL.md` and `REMAINING_TASKS.md`.

Why this change:
- The review ritual was documented but not easy to run consistently. A Make
  target is the smallest operator workflow improvement and does not schedule or
  mutate strategy decisions.

Expected outcome:
- Operators have one repeatable command to produce the status, diagnostics, and
  loss replay inputs for a dated advisory strategy review.

Verification:
- `make -n strategy-review`
  - SHOWN: dry-run prints `status-paper-all`,
    `scripts/report_paper_run_diagnostics.py`, and
    the expected `replay_paper_losses.py` command for `sma_200_trend` /
    `BTC/USD` without executing them.

Remaining risk:
- LOW: operator workflow/docs only; no automatic scheduler or runtime trading
  behavior changed.
- UNVERIFIED: the target was not executed against live campaign state in this
  pass because it can invoke remote status checks and the operator requested
  avoidance of long-running commands.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Challenger Strategy Governance Configs

Active role: ENGINEER

Objective:
- Add inactive per-strategy governance configs for challenger strategies before
  any future promotion or persistent campaign activation.

What was found:
- SHOWN: `configs/strategies/` only contained `es_daily_trend_v1.yaml`.
- SHOWN: backlog item 22 requires strategy-specific config contracts for
  `ema_cross`, `breakout_donchian`, `pullback_recovery`, and future context
  strategies before promotion.
- SHOWN: visible runtime/gate code references `es_daily_trend_v1.yaml` by
  explicit path; no current source path was shown to auto-load every strategy
  YAML in `configs/strategies/`.

What changed:
- Added governance-only configs for `ema_cross_default`,
  `breakout_default`, and `pullback_recovery_default`.
- Each config keeps `trade_enabled=false`, `campaign_enabled=false`, and
  `promotion_candidate=false`.
- Added a config regression test verifying inactive activation state,
  registry-backed strategy names, baseline placeholders, net-fee manual review,
  and explicit no-trade filter contracts.
- Updated `REMAINING_TASKS.md` item 22.

Why this change:
- Challenger strategies need documented risk/evidence/manual-review contracts
  before campaign manifests or promotion gates can rely on them. Keeping them
  inactive prevents a config file from becoming an accidental runtime signal.

Expected outcome:
- Future challenger activation starts from an explicit governance contract and
  cannot silently reference an unsupported strategy or skip baseline/manual
  review requirements.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_challenger_strategy_governance_configs.py`
  - SHOWN: `2 passed in 0.11s`.

Remaining risk:
- LOW: inactive configs plus tests; no campaign manifest or runtime behavior
  changed.
- UNVERIFIED: archive-backed baselines are still null and must be populated
  before these strategies become promotion candidates.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Paper Universe Widening Decision

Active role: ENGINEER

Objective:
- Decide whether to widen the canonical paper universe to accelerate qualified
  evidence.

What was found:
- SHOWN: backlog item 26 identified evidence velocity as a problem and required
  a decision record before changing the campaign.
- SHOWN: the backlog also identified
  `scripts/check_promotion_gates.py::_count_round_trips` as needing
  symbol-aware chronological pairing before cross-symbol round trips can count.
- CLAIMED: operator status has shown qualified round trips progressing slowly,
  but current raw/cross-symbol fills must not bypass provenance qualification.

What changed:
- Added
  `docs/strategies/paper_universe_widening_decision_2026-07-04.md`.
- Updated `REMAINING_TASKS.md` item 26.

Why this change:
- Widening the universe changes the meaning of the paper gate. The smallest
  safe decision is to defer widening until symbol-aware counting, per-symbol
  provenance, risk caps, and correlation caveats are proven.

Expected outcome:
- The canonical paper campaign remains unchanged, and any future multi-symbol
  expansion starts as a separate evidence-design change instead of an ad hoc
  acceleration shortcut.

Verification:
- `git diff --check`
  - SHOWN: passed with no whitespace errors.
- `rg -n "SERVER_SECRETS_ROTATION_MODEL|server secrets|rotation drill|secret injection" docs/SERVER_SECRETS_ROTATION_MODEL.md docs/LAUNCH_CHECKLIST.md docs/AUTHORITY_MATRIX.md REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: model links and remaining proof language are present.

Remaining risk:
- LOW: docs/backlog/work-log only; no runtime campaign, gate, or config behavior
  changed.
- UNVERIFIED: future symbol-aware counting and per-symbol provenance fixtures
  remain unimplemented.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - CI-Ignored Test Optional Target

Active role: ENGINEER

Objective:
- Add a named optional local command for the pytest files intentionally ignored
  by the fast/full CI paths.

What was found:
- SHOWN: `docs/CI_IGNORED_TEST_POLICY.md` documents four ignored test files and
  the manual command to run them.
- SHOWN: `Makefile` ignored those files in `test-fast` and `test-full`, but had
  no named target for the exact ignored slice.

What changed:
- Added `make test-ci-ignored`.
- Updated `docs/CI_IGNORED_TEST_POLICY.md`.
- Updated `REMAINING_TASKS.md` item 21.

Why this change:
- A named optional local job makes the ignored slice easier to run and record
  before dashboard or symbol-scanner changes, without changing CI behavior in
  this low-risk batch.

Expected outcome:
- Operators and reviewers have one stable command for the ignored test slice
  while the longer-term CI-safe split remains open.

Verification:
- `make -n test-ci-ignored`
  - SHOWN: dry-run prints the four expected ignored test files without
    executing pytest.

Remaining risk:
- LOW: Make/docs/backlog/work-log only; CI behavior was not changed.
- UNVERIFIED: the ignored tests were not executed in this pass by operator
  request to avoid excessive long-running tests.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Promotion Branch Deletion Guard

Active role: ENGINEER

Objective:
- Prevent future master-promotion merges from deleting the long-lived
  `review-stabilized` branch.

What was found:
- SHOWN: PR #194 used `review-stabilized` as the head branch for promotion to
  `master`.
- SHOWN: merging PR #194 with branch deletion removed remote
  `review-stabilized`; `git ls-remote origin refs/heads/review-stabilized`
  returned no remote ref.
- SHOWN: local `review-stabilized` remained intact at the accepted PR #195
  merge commit and was pushed back to restore the remote branch.

What changed:
- Updated `docs/GITHUB_BRANCH_PROTECTION.md` with a long-lived branch safety
  rule: do not use `--delete-branch` or delete the branch in the UI when
  `review-stabilized` is the PR head.
- Added verification and recovery commands for accidental deletion.

Why this change:
- `review-stabilized` is an integration branch, not a disposable feature
  branch. Deleting it during promotion creates avoidable branch drift and PR
  creation failures.

Expected outcome:
- Future accepted/admin promotion merges preserve the long-lived branch and
  keep the `master` / `review-stabilized` workflow stable.

Verification:
- `git ls-remote origin refs/heads/master refs/heads/review-stabilized`
  - SHOWN during the incident: only `master` was returned.
- `git push origin review-stabilized`
  - SHOWN: remote `review-stabilized` was recreated.

Remaining risk:
- LOW: docs/work-log only; no branch protection settings or runtime behavior
  changed.
- UNVERIFIED: PR #196 promotion checks are still pending at the time of this
  entry.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Retention Policy Server Threshold Link

Active role: ENGINEER

Objective:
- Close the documentation gap between the general retention policy and the
  existing Hetzner server storage-health thresholds.

What was found:
- SHOWN: `docs/RETENTION_POLICY.md` still said a host-specific retention packet
  was required before canonical server operation.
- SHOWN: `docs/HETZNER_PAPER_HOST.md` already defines the paper-host storage
  baseline: `/srv/cryptkeep/backups`, minimum 2 GiB free space, minimum 10,000
  free inodes, UTC/NTP sync, backup age, restore-test status, and campaign
  health checks.

What changed:
- Updated `docs/RETENTION_POLICY.md` to link the current Hetzner threshold
  baseline.
- Updated `REMAINING_TASKS.md` item 22 to preserve the remaining
  backup/restore-drill proof requirement.

Why this change:
- The backlog should distinguish missing policy from missing executed proof.
  The threshold policy exists; the future launch packet still needs fresh
  restore evidence.

Expected outcome:
- Operators looking at retention policy can find the server minimums without
  duplicating or contradicting the Hetzner runbook.

Verification:
- `git diff --check`
  - SHOWN: passed with no whitespace errors.
- `rg -n "CONFIG_AUTHORITY_DECISION|CLOCK_VENUE_TIME_SANITY_POLICY|OPERATOR_ACTION_AUDIT_COVERAGE|2\\.12|2\\.13|2\\.14" docs/CONFIG_AUTHORITY_DECISION.md docs/CLOCK_VENUE_TIME_SANITY_POLICY.md docs/OPERATOR_ACTION_AUDIT_COVERAGE.md docs/LAUNCH_CHECKLIST.md REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: launch-checklist links, backlog links, and work-log references are present.

Remaining risk:
- LOW: docs/backlog/work-log only; no retention/pruning command or server
  behavior changed.
- UNVERIFIED: no fresh backup/restore drill was run in this pass.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - AI Copilot Provider Data Boundary

Active role: ENGINEER

Objective:
- Document what runtime fields may be sent to external LLM providers when an
  AI-backed copilot summary is explicitly enabled.

What was found:
- SHOWN: `docs/AI_COPILOT_OPERATING_RULES.md` defined copilot jobs as
  advisory/read-only.
- SHOWN: `REMAINING_TASKS.md` item 20 required provider-data governance in
  addition to future read-only SQLite enforcement.

What changed:
- Added an external provider data-boundary section to
  `docs/AI_COPILOT_OPERATING_RULES.md`.
- Updated `REMAINING_TASKS.md` item 20 to mark the disclosure-policy subtask
  documented while preserving the SQLite read-only enforcement task.

Why this change:
- External provider summaries need an explicit data boundary before they become
  a routine operator path. Documentation is the smallest safe slice; changing
  database access enforcement remains a separate security-sensitive task.

Expected outcome:
- Copilot jobs have a visible allowed/forbidden payload policy and remain
  advisory-only when `use_ai=true`.

Verification:
- `git diff --check`
  - SHOWN: passed with no whitespace errors.
- `rg -n "FULL_STATE_BACKUP_RESTORE_DRILL|EVIDENCE_WRITE_FAILURE_STATUS_POLICY|EXECUTION_COST_RESEARCH_POLICY|3\\.7|4\\.7|4\\.8" docs/FULL_STATE_BACKUP_RESTORE_DRILL.md docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md docs/EXECUTION_COST_RESEARCH_POLICY.md docs/LAUNCH_CHECKLIST.md REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: launch-checklist links, backlog links, and work-log references are present.

Remaining risk:
- LOW for this docs slice.
- HIGH/UNVERIFIED for the remaining code task: `_safe_sqlite_query()` still
  needs read-only connection enforcement and a write-SQL regression.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Server Secrets Rotation Model

Active role: ENGINEER

Objective:
- Document the server-side secret injection and rotation model required before
  capped-live deployment.

What was found:
- SHOWN: `REMAINING_TASKS.md` listed server secrets and rotation as a deferred
  live-money substrate blocker.
- SHOWN: existing docs covered pieces of the boundary: Hetzner paper-host docs
  forbid live exchange credentials on the paper host, launch checklist requires
  API keys outside YAML, and AI copilot rules forbid sending secrets to
  providers.
- UNVERIFIED: no capped-live server secret injection rehearsal or rotation
  drill has been executed.

What changed:
- Added `docs/SERVER_SECRETS_ROTATION_MODEL.md`.
- Linked the model from `docs/LAUNCH_CHECKLIST.md` and
  `docs/AUTHORITY_MATRIX.md`.
- Updated `REMAINING_TASKS.md` item 12 to distinguish documented policy from
  remaining executed proof.

Why this change:
- A capped-live server needs a visible credential authority, injection path,
  rotation trigger list, redaction rule, and launch-gate proof packet before
  any real-money deployment. A docs-only policy is the smallest safe step and
  avoids changing secret handling behavior during paper evidence collection.

Expected outcome:
- Future server/live work has a concrete checklist for secret handling and
  cannot treat current desktop/paper keyring/env handling as sufficient
  capped-live proof.

Verification:
- Docs-only change. `git diff --check` will be run before commit.

Remaining risk:
- LOW: docs/backlog/checklist/authority update only; no credential, runtime,
  deploy, or live-order behavior changed.
- HIGH/UNVERIFIED for the later capped-live proof: server secret injection,
  rotation, revocation, redacted status output, and artifact leak scans still
  need an executed evidence packet.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Supply-Chain Release Verification Policy

Active role: ENGINEER

Objective:
- Document the supply-chain/release verification policy required before
  capped-live deployment.

What was found:
- SHOWN: `REMAINING_TASKS.md` listed supply-chain verification as a deferred
  live-money substrate blocker.
- SHOWN: `requirements.txt` points at pinned requirements, CI installs pinned
  runtime dependencies in the main validation workflow, and release docs already
  describe artifact hash manifests.
- UNVERIFIED: no dependency vulnerability audit, SBOM, hash-locked install, or
  release attestation is currently a required gate for capped live.

What changed:
- Added `docs/SUPPLY_CHAIN_RELEASE_POLICY.md`.
- Linked the policy from `docs/CI_GITHUB_ACTIONS.md` and
  `docs/LAUNCH_CHECKLIST.md`.
- Updated `REMAINING_TASKS.md` item 13 to distinguish documented policy from
  remaining capped-live proof.

Why this change:
- The repo needed a clear decision boundary before adding CI scanners or
  stricter release gates. A docs-only policy preserves current paper/research
  speed while making capped-live supply-chain proof explicit.

Expected outcome:
- Future release/live work can decide whether to add `pip-audit`, SBOMs,
  hash-locked installs, or attestations against a visible policy instead of
  treating the current pinned requirements as full production proof.

Verification:
- `git diff --check`
  - SHOWN: passed with no whitespace errors.
- `rg -n "SUPPLY_CHAIN_RELEASE_POLICY|supply-chain|dependency vulnerability audit|hash-locked|SBOM" docs/SUPPLY_CHAIN_RELEASE_POLICY.md docs/CI_GITHUB_ACTIONS.md docs/LAUNCH_CHECKLIST.md REMAINING_TASKS.md docs/work_log/review_stabilized_work_log.md`
  - SHOWN: policy links and remaining capped-live proof language are present.

Remaining risk:
- LOW: docs/backlog/checklist update only; no CI, dependency, release,
  signing, or runtime behavior changed.
- UNVERIFIED: dependency audit, SBOM, hash-locked install, and release
  attestation proof remain open before capped live.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Live-Readiness Policy Batch

Active role: ENGINEER

Objective:
- Advance multiple deferred live-readiness backlog items through docs-only
  policy decisions without touching runtime, gate, or execution code.

What was found:
- SHOWN: `REMAINING_TASKS.md` listed config authority consolidation,
  clock/venue-time sanity, and operator/action audit coverage as deferred
  capped-live substrate work.
- SHOWN: existing docs/code already contain pieces of each topic, including
  `execution.live_enabled`, UTC campaign windows, Hetzner UTC/NTP requirements,
  and audit/event surfaces.
- UNVERIFIED: no capped-live config-reader inventory, host-to-venue skew proof,
  or complete operator-action audit coverage matrix has been executed.

What changed:
- Added `docs/CONFIG_AUTHORITY_DECISION.md`.
- Added `docs/CLOCK_VENUE_TIME_SANITY_POLICY.md`.
- Added `docs/OPERATOR_ACTION_AUDIT_COVERAGE.md`.
- Linked all three policies from `docs/LAUNCH_CHECKLIST.md`.
- Updated `REMAINING_TASKS.md` items 10, 11, and 14 to distinguish documented
  policy from remaining executed proof.

Why this change:
- These tasks need explicit production rules before later code work starts.
  The smallest safe step is to make the authority/proof requirements visible
  while avoiding any behavior change during paper evidence collection.

Expected outcome:
- Future capped-live work has concrete acceptance packets for config
  authority, clock sanity, and audit coverage instead of vague backlog labels.

Verification:
- Docs-only change. `git diff --check` will be run before commit.

Remaining risk:
- LOW: docs/backlog/checklist update only; no runtime, deployment, order,
  config-loading, audit-store, or gate behavior changed.
- UNVERIFIED: all runtime proof remains open before capped live.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Evidence Ops Policy Batch

Active role: ENGINEER

Objective:
- Advance backup/restore, evidence-write failure status, and execution-cost
  research backlog items through docs-only policy packets.

What was found:
- SHOWN: `REMAINING_TASKS.md` listed full-state backup/restore drill,
  evidence-write failure status, and execution-cost research as unresolved
  deferred work.
- SHOWN: existing docs/code already include partial pieces: Hetzner storage
  preflight, paper campaign restore tooling, shadow would-be-fill requirements,
  and basic fee/slippage modeling.
- UNVERIFIED: no full canonical state restore drill, bounded evidence-writer
  refusal proof, or accepted maker/taker cost-stack report has been executed.

What changed:
- Added `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md`.
- Added `docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md`.
- Added `docs/EXECUTION_COST_RESEARCH_POLICY.md`.
- Linked the policies from `docs/LAUNCH_CHECKLIST.md`.
- Updated `REMAINING_TASKS.md` items 8, 9, and 15 to distinguish documented
  policy from remaining executed proof.

Why this change:
- These items need clear proof packets before runtime work starts. A docs-only
  policy pass is the smallest safe progress that does not disturb paper
  evidence collection or alter execution behavior.

Expected outcome:
- Future implementation can target explicit acceptance criteria for restore,
  evidence-write failure visibility, and execution-cost research instead of
  broad backlog descriptions.

Verification:
- Docs-only change. `git diff --check` will be run before commit.

Remaining risk:
- LOW: docs/backlog/checklist update only; no backup, restore, evidence writer,
  gate, order-routing, or execution-cost behavior changed.
- UNVERIFIED: all runtime proof remains open before capped live or execution
  policy changes.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Evidence Writer Status Counters

Active role: ENGINEER

Objective:
- Surface central evidence JSONL writer health so repeated write failures are
  visible instead of silently starving promotion evidence.

What was found:
- SHOWN: `services/strategies/evidence_logger.py::_append()` is the central
  JSONL evidence writer for signal, order, fill, session, and drawdown records.
- SHOWN: the existing writer logs write exceptions but does not persist bounded
  failure counters or a refusal/degraded status for operators or gates to read.
- UNVERIFIED: campaign status and promotion gates do not yet consume a persisted
  writer-health artifact.

What changed:
- Added `runtime/health/evidence_writer.status.json` as the persisted writer
  health artifact, resolved through `CBP_STATE_DIR`.
- Added total and consecutive failure counters, last error/success timestamps,
  last record/strategy/path metadata, and `ok`/`degraded`/`refusing` state.
- Added targeted tests proving successful writes update status, repeated
  injected write failures become `refusing`, and recovery resets consecutive
  failures while preserving total failures.
- Updated `docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md` and
  `REMAINING_TASKS.md` to distinguish implementation proof from remaining
  campaign/gate integration proof.

Why this change:
- The central logger is the smallest correct boundary: every existing
  EvidenceLogger caller gains writer-health visibility without touching
  trading/order behavior or broadening the change into gate semantics.

Expected outcome:
- Operators and later status/gate code can read one state-scoped health artifact
  to detect evidence starvation, rather than inferring it from missing JSONL
  rows after the fact.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_evidence_logger.py`
  - SHOWN: `21 passed in 1.57s`.

Remaining risk:
- HIGH: evidence/gate reliability surface.
- UNVERIFIED: campaign summaries do not yet surface the writer status, and
  promotion gates do not yet reject or flag a `refusing` evidence writer.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-04 - Evidence Writer Gate And Status Integration

Active role: ENGINEER

Objective:
- Wire persisted evidence-writer health into promotion and operator status so a
  refusing writer cannot be treated as promotion-quality evidence.

What was found:
- SHOWN: PR #206 added the central
  `runtime/health/evidence_writer.status.json` artifact and targeted writer
  counters.
- SHOWN: `scripts/check_promotion_gates.py::run_check()` is the canonical gate
  payload consumed by supervised soak status.
- SHOWN: `scripts/report_supervised_soak_status.py` already summarizes gate
  JSON for daily operator checks.
- UNVERIFIED: no real operator-host writer failure has occurred; this proof
  uses injected persisted status.

What changed:
- Added `evidence_writer` status to promotion gate JSON.
- Added an `Evidence writer accepting records` gate that fails when persisted
  status is `refusing`.
- Added supervised-soak summary and recommendation output for refusing writer
  status.
- Added targeted tests proving a persisted `refusing` status fails the gate and
  that supervised soak recommends `investigate_evidence_writer`.
- Updated `docs/EVIDENCE_WRITE_FAILURE_STATUS_POLICY.md` and
  `REMAINING_TASKS.md` to mark the gate/status integration proof ready.

Why this change:
- The smallest correct follow-through is to consume the central writer-health
  artifact in the existing gate/status path instead of adding a second monitor
  or changing evidence-write semantics.

Expected outcome:
- Daily gate/status commands can tell the operator when evidence is starving,
  and a refusing writer is a machine gate failure until recovered/reviewed.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py::TestGateOutput::test_refusing_evidence_writer_blocks_machine_readiness tests/test_report_supervised_soak_status.py`
  - SHOWN: `4 passed in 0.24s`.
- `./.venv/bin/python -m pytest -q tests/test_check_promotion_gates.py tests/test_report_supervised_soak_status.py`
  - SHOWN: `48 passed in 1.32s`.
- `git diff --check`
  - SHOWN: passed with no whitespace errors.

Remaining risk:
- HIGH: evidence/gate reliability surface.
- UNVERIFIED: real host writer-failure observation and alert-dispatch wiring
  remain outside this implementation proof.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-04 - AI Copilot Read-Only SQLite Context

Active role: ENGINEER

Objective:
- Enforce read-only SQLite access for AI-copilot incident context collection
  before external LLM summaries become a normal operator path.

What was found:
- SHOWN: `services/ai_copilot/context_collector.py::_safe_sqlite_query()`
  opened SQLite databases with a normal writable connection.
- SHOWN: current callers pass hardcoded `SELECT` queries, but the helper did
  not enforce that contract.
- SHOWN: backlog item 20 required read-only SQLite access plus a regression
  proving write SQL cannot mutate the source DB.

What changed:
- `_safe_sqlite_query()` now rejects non-`SELECT` SQL before opening a DB.
- SQLite connections now use a `mode=ro` URI, so missing DB files are not
  created as a side effect of context collection.
- Added targeted regressions proving normal reads still work, rejected write
  SQL does not mutate the DB, and missing DB reads do not create files.
- Updated `docs/AI_COPILOT_OPERATING_RULES.md` and `REMAINING_TASKS.md` to
  record the enforced boundary.

Why this change:
- The helper boundary is the smallest correct enforcement point: all incident
  context SQLite reads go through it, and no provider, prompt, trading, gate, or
  dashboard behavior needs to change.

Expected outcome:
- AI-copilot incident context remains advisory/read-only even if a future
  caller accidentally passes write SQL.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_ai_copilot_context_collector.py`
  - SHOWN: `3 passed in 0.09s`.
- `git diff --check`
  - SHOWN: passed with no whitespace errors.

Remaining risk:
- HIGH: security-sensitive AI/provider context surface.
- UNVERIFIED: broader external provider prompt-injection hardening remains out
  of scope; this proof covers SQLite mutation prevention only.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-04 - Structure Disposition Batch

Active role: ENGINEER

Objective:
- Close low-risk structure-hygiene backlog decisions for runtime TODO stubs,
  legacy paper runner classification, and unwired storage candidate disposition.

What was found:
- SHOWN: `services/runtime/run_mode.py` and
  `services/runtime/bot_process.py` contained only phase comments and
  `TODO: implement`.
- SHOWN: source import scan found no active source importers for either runtime
  placeholder module.
- SHOWN: `services/trading_runner/run_trader.py` is a paper-only EMA runner
  using `services/paper_trader/`, not the canonical
  `services/execution/paper_engine.py` evidence path.
- SHOWN: storage candidate scan still shows no visible production source
  importers for `fill_reconciler_store_sqlite.py`,
  `order_idempotency_sqlite.py`, or `order_tracker_store_sqlite.py`.

What changed:
- Deleted the two TODO-only runtime placeholder modules.
- Added `docs/architecture/runtime_stub_disposition.md`.
- Updated `docs/architecture/paper_execution_surfaces.md` to classify
  `services/trading_runner/run_trader.py` as a legacy compatibility runner.
- Updated `docs/architecture/storage_surface_classification.md` to explicitly
  retain the three unwired storage candidates as quarantined retained schemas,
  not runtime authorities.
- Updated `REMAINING_TASKS.md` for the three backlog entries.

Why this change:
- The smallest correct path is to remove misleading empty placeholders and
  classify legacy/unwired surfaces before anyone builds new runtime or
  reconciliation work on the wrong module.

Expected outcome:
- Future runtime/process work starts from documented managed-component/control
  surfaces, new paper execution work stays on the canonical paper engine, and
  reconciliation work does not accidentally adopt dormant storage schemas.

Verification:
- `rg -n "runtime\\.run_mode|runtime\\.bot_process|services/runtime/run_mode|services/runtime/bot_process" services scripts tests docs Makefile pyproject.toml -g '*.*'`
  - SHOWN: only `docs/architecture/runtime_stub_disposition.md` references
    remain.
- `rg -n "fill_reconciler_store_sqlite|order_idempotency_sqlite|order_tracker_store_sqlite|FillReconciler|OrderIdempotency|OrderTracker" services scripts storage tests docs REMAINING_TASKS.md -g '*.*'`
  - SHOWN: no production source importers; matches are modules themselves and
    docs/audit references.
- `./.venv/bin/python -m pytest -q tests/test_run_trader_compat.py tests/test_run_trader_integration_minimal.py`
  - SHOWN: `5 passed in 0.82s`.
- `git diff --check`
  - SHOWN: passed with no whitespace errors.

Remaining risk:
- LOW: structure/docs classification plus deletion of TODO-only modules with no
  source importers.
- UNVERIFIED: external consumers outside the repo are not checked.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Backtest-To-Paper Fill Parity Guard

Active role: ENGINEER

Objective:
- Add a direct regression that paper market fills stay aligned with the shared
  fee/slippage model used by backtest parity.

What was found:
- SHOWN: `services/backtest/parity_engine.py` calls
  `services.execution.fill_model.apply_fee_slippage()`.
- SHOWN: `services/execution/paper_engine.py` applies equivalent mid-price
  plus/minus slippage math inline for market orders and computes fees from the
  executed price.
- SHOWN: `services/execution/fill_model.py` explicitly states that paper should
  call the same function for perfect parity, but the current paper engine does
  not delegate to it.

What changed:
- Added a paper-engine honesty regression proving paper market buy and sell
  fill price/fee match `apply_fee_slippage()` for the same mid price, side,
  qty, fee bps, and slippage bps.
- Updated `REMAINING_TASKS.md` to record the parity guard.

Why this change:
- The smallest safe proof is a regression around current behavior. It guards
  transferability without changing paper execution semantics during an active
  evidence campaign.

Expected outcome:
- Future changes to either the shared fill model or paper market-fill math will
  fail a targeted test if they drift apart.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_engine_honesty.py`
  - SHOWN: `2 passed in 0.19s`.
- `git diff --check`
  - SHOWN: passed with no whitespace errors.

Remaining risk:
- LOW: test-only guard; no runtime behavior changed.
- UNVERIFIED: limit-order parity and full backtest-to-paper lifecycle parity
  remain outside this narrow guard.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Safety And Websocket Surface Classification

Active role: ENGINEER

Objective:
- Close low-risk structure backlog items by documenting duplicate-looking
  safety/order/risk surfaces and websocket-named surfaces without changing
  runtime behavior.

What was found:
- SHOWN: `services/admin/kill_switch.py` is the canonical operator kill-switch
  state used by CLI/admin/onboarding/watchdog/paper-status flows.
- SHOWN: `services/risk/killswitch.py` is not dormant; `place_order` imports it
  as the live kill-switch safety probe, and it also reads the canonical admin
  switch.
- SHOWN: `services/risk/kill_conditions.py` is strategy-runner cooldown logic,
  not the global kill-switch state.
- SHOWN: `services/risk/live_risk_gates.py`, `services/execution/risk_gates.py`,
  and `services/ops/risk_gate_*` represent different concepts: hard live risk
  enforcement, executor adapter, and ops telemetry gating.
- SHOWN: `services/execution/client_order_id.py` is the governed live
  client-order-id builder; `services/execution/client_oid.py` is used by
  legacy/compat intent executors.
- SHOWN: `services/live_trader_multi/main.py` and
  `services/live_trader_fleet/main.py` are duplicate dry-run legacy stubs.
- SHOWN: `services/market_data/ws_ticker_feed.py` and
  `services/fills/user_stream_ws.py` are real optional ccxt.pro websocket
  wrappers, while `ws_clients`, `ws_common`, feature blacklist, and health
  logger modules are helpers/telemetry.

What changed:
- Added `docs/BACKLOG_EXECUTION_LANES.md`.
- Added `docs/architecture/safety_surface_classification.md`.
- Added `docs/architecture/websocket_surface_classification.md`.
- Updated `docs/CORE.md`, `docs/ARCHITECTURE.md`, and `docs/REPO_LAYOUT.md`
  so the operational-core policy links the new classification records.
- Updated `REMAINING_TASKS.md` items 2, 4, 17, and 18 with the disposition.

Why this change:
- The smallest safe improvement is classification before consolidation.
  Deleting or rewiring live-money safety surfaces would be high risk; this
  patch only records which surface owns which concept.

Expected outcome:
- Future agents should not add new code to legacy dry-run live traders, should
  not delete active kill-switch probes as dormant, and should not assume every
  `ws_*` file is a canonical streaming data path.
- Future cleanup should start from the core/quarantine classification records
  rather than naming similarity alone.
- Future backlog batches should stay within one risk lane; high-risk
  gate/execution/deploy work should be split into separate objectives and stop
  at `READY_FOR_INDEPENDENT_REVIEW`.

Verification:
- `rg --files services scripts docs tests | rg '(ws|websocket|user_stream|ticker_feed|market_ws)'`
  - SHOWN: visible websocket-named surfaces enumerated.
- `rg --files services scripts docs tests | rg '(kill|killswitch|client_oid|client_order_id|live_trader|risk_gate)'`
  - SHOWN: visible safety/order/risk surfaces enumerated.
- Targeted file reads of classified modules.
  - SHOWN: classification matches imports and module behavior listed above.

Remaining risk:
- LOW: docs/backlog only; no runtime behavior changed.
- UNVERIFIED: external consumers outside this repository and host-level
  websocket supervision were not checked.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Backlog Acceptance-State Cleanup

Active role: ENGINEER

Objective:
- Remove stale backlog wording after accepted/merged work and master branch
  synchronization.

What was found:
- SHOWN: PR #211 merged the accepted `review-stabilized` batch to `master` at
  merge commit `7861f7292b418f8ccbc53ca002635618f87a079b`.
- SHOWN: `HEAD`, `origin/master`, and `origin/review-stabilized` were all
  verified at `7861f7292b418f8ccbc53ca002635618f87a079b`.
- SHOWN: `scripts/check_promotion_gates.py` includes the `evidence_writer`
  status and an `Evidence writer accepting records` gate that fails when the
  persisted writer status is `refusing`.
- SHOWN: `services/ai_copilot/context_collector.py` uses SQLite read-only URI
  connections and rejects non-`SELECT` context queries.
- SHOWN: `services/execution/paper_engine.py` returns
  `market_quality:no_reference_price` instead of using the previous hardcoded
  `60000.0` reference-price fallback in the canonical paper pre-submit gate.

What changed:
- Updated `REMAINING_TASKS.md` to describe the strategy-registry unknown-name
  fallback as a resolved prior finding, not current behavior.
- Updated `REMAINING_TASKS.md` to describe the paper fee/PnL semantics proof
  as independently accepted, with remaining operational proof separated.
- Updated `REMAINING_TASKS.md` to mark the evidence-writer status/gate work as
  accepted rather than awaiting independent review.
- Updated `REMAINING_TASKS.md` to mark AI-copilot read-only context access as
  accepted rather than awaiting independent review.
- Updated `REMAINING_TASKS.md` to mark the canonical paper-engine reference
  price fallback as accepted, leaving only broader legacy/demo price cleanup.
- Recorded the PR #211 master synchronization boundary.

Why this change:
- The backlog should reflect current accepted state. Stale "ready for review"
  wording creates false open blockers and makes future prioritization worse.

Expected outcome:
- Future backlog passes start from the real remaining work: alert dispatch,
  provider-boundary preservation, broader legacy hardcoded-price cleanup, and
  high-risk gate/execution/deploy items.

Verification:
- `git rev-parse HEAD origin/master origin/review-stabilized`
  - SHOWN: all three refs returned
    `7861f7292b418f8ccbc53ca002635618f87a079b`.
- Targeted source reads listed above.
  - SHOWN: backlog status updates match visible code and accepted branch state.

Remaining risk:
- LOW: docs/backlog only; no runtime behavior changed.
- UNVERIFIED: external runtime host state was not checked.
- Acceptance state: `ACCEPTED`.

## 2026-07-04 - Websocket Auto-Disable Doc Alignment

Active role: ENGINEER

Objective:
- Align the websocket auto-disable note with current source paths and the new
  websocket surface classification.

What was found:
- SHOWN: `docs/WS_AUTO_DISABLE.md` referenced retired
  `services/marketdata/*` paths.
- SHOWN: current source contains `services/market_data/ws_feature_blacklist.py`
  and `services/market_data/ws_ticker_feed.py`.
- SHOWN: no current tracked `services/market_data/ws_microstructure_manager.py`
  or `services/marketdata/ws_microstructure_manager.py` file was found.

What changed:
- Updated `docs/WS_AUTO_DISABLE.md` to name the current
  `services/market_data/*` ticker-feed/blacklist surfaces, identify
  `scripts/data/run_ws_ticker_feed.py` as the canonical runner implementation,
  and mark the old microstructure manager reference as not currently present.
- Updated `REMAINING_TASKS.md` item 4 to record the stale-doc correction.

Why this change:
- The smallest safe fix is documentation alignment. Intraday/shadow work should
  not infer a supported order-book/trades websocket manager from a stale phase
  note.

Expected outcome:
- Operators and future agents see the current optional ticker websocket path
  and do not route new work through retired `services/marketdata` paths.

Verification:
- `rg --files services/market_data services/marketdata docs | rg '(ws_feature_blacklist|ws_microstructure_manager|ws_ticker_feed|WS_AUTO_DISABLE|websocket_surface)'`
  - SHOWN: current ticker/blacklist docs and modules exist; no microstructure
    manager source was listed.
- `rg -n 'services/marketdata|marketdata/ws_|ws_microstructure_manager|ws_feature_blacklist|ws_ticker_feed' docs/WS_AUTO_DISABLE.md docs/architecture/websocket_surface_classification.md docs/REPO_LAYOUT.md docs/ARCHITECTURE.md`
  - SHOWN before patch: stale `docs/WS_AUTO_DISABLE.md` references existed.

Remaining risk:
- LOW: docs/backlog only; no runtime behavior changed.
- UNVERIFIED: host-level websocket service deployment was not checked.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T08:45:00Z - Crypto Edge Source Decision

Active role: ENGINEER

Objective:
- Close the low-risk config/docs review gap for the read-only crypto-edge
  derivatives source without touching execution, risk, gates, or strategy
  routing.

What was found:
- SHOWN: `REMAINING_TASKS.md` recorded OKX funding/open-interest/basis as a
  validated read-only candidate, but still said OKX adoption needed explicit
  config/docs review.
- SHOWN: `docs/work_log/review_stabilized_work_log.md` records the 2026-07-02
  bounded OKX read-only collector probe and says funding, open-interest, and
  basis checks passed.
- SHOWN: `sample_data/crypto_edges/live_collector_plan.json` still pointed its
  derivatives legs at Binance even though Binance derivatives availability was
  recorded as externally blocked from the current network.

What changed:
- Added `docs/research/crypto_edge_source_decision.md`.
- Changed the default read-only collector plan's funding, open-interest, and
  basis legs from Binance to OKX.
- Updated `REMAINING_TASKS.md` item 14 to record the source decision and the
  remaining host-schedule/cadence proof.
- Added dated follow-up notes to the short/context feasibility and research
  checkpoint docs so their next-action guidance points at the accepted OKX
  read-only source decision instead of the now-resolved venue-selection step.

Why this change:
- Funding and open-interest history mostly accrues in real time. Leaving the
  default plan on an externally blocked derivatives source delays the
  profitability research path without improving safety.
- OKX adoption is constrained to read-only research collection. No live venue,
  order routing, risk gate, promotion gate, or strategy-dispatch behavior is
  changed.

Expected outcome:
- Operators have a default read-only collector plan that can accumulate the
  context history needed for future `funding_extreme` and
  `open_interest_shift` research, pending host cadence proof.

Verification:
- `./.venv/bin/python -m json.tool sample_data/crypto_edges/live_collector_plan.json`
  - SHOWN: plan JSON parsed successfully.
- `rg -n '"venue": "okx"|crypto_edge_source_decision|OKX|live_collector_plan.json' ...`
  - SHOWN: OKX plan entries and decision-record references are present.
- `git diff --check`
  - SHOWN: passed.
- Long live-public collection was not run in this pass by operator rule; the
  required host proof remains explicitly open.

Remaining risk:
- MEDIUM: this changes a read-only research data-source default. It does not
  authorize live routing or strategy promotion evidence. Long-run OKX
  reliability, scheduled collection, and cadence-gap alerting remain
  UNVERIFIED.
- Acceptance state: `ACCEPTED_WITH_RISK`.

## 2026-07-05T09:12:00Z - Crypto Edge Operator Guide Follow-Up

Active role: ENGINEER

Objective:
- Keep operator-facing crypto-edge documentation aligned with the accepted OKX
  read-only source decision.

What was found:
- SHOWN: `docs/research/crypto_edge_source_decision.md` now records OKX as the
  default read-only derivatives context source.
- SHOWN: `docs/research/crypto_structural_edges.md` described the collector
  generically but did not point operators to the source decision or explain the
  OKX/Binance implication.
- SHOWN: `docs/RUNBOOKS.md` linked the main runbooks but not the crypto-edge
  source decision.

What changed:
- Added the OKX source decision and live-collector plan interpretation to the
  crypto structural edges guide.
- Linked the source decision from the runbook index.

Why this change:
- The source decision changes what the default read-only collector plan means.
  Operator docs should show that this is research collection only, not a live
  venue approval or strategy-promotion proof.

Expected outcome:
- Operators following the crypto-edge guide can see why OKX is used and what
  remains blocked before context rows can influence strategy promotion.

Verification:
- `rg -n "crypto_edge_source_decision|OKX|read-only derivatives|strategy promotion|live trading venue" ...`
  - SHOWN: source-decision links and OKX/read-only boundaries are present.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- LOW: docs-only operator guidance. No command behavior, collector behavior,
  execution path, strategy routing, or gate behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T10:36:00Z - OKX Backlog Status Cleanup

Active role: ENGINEER

Objective:
- Remove stale backlog wording that still treated the crypto-edge source
  decision as open after the accepted OKX read-only decision landed.

What was found:
- SHOWN: `REMAINING_TASKS.md` item 14 still said "If the canonical source
  decision remains open" after OKX had been documented as the default
  read-only derivatives context source.
- SHOWN: item 9 still mixed venue-selection wording with the now-accepted OKX
  decision.

What changed:
- Updated item 9 to say remaining short/context proof is data-readiness, not
  venue selection.
- Updated item 14 to start from the accepted OKX source decision and keep the
  remaining proof focused on host schedule, recent snapshots, cadence-gap
  alerting, and downstream context/provenance review.

Why this change:
- The backlog should not direct operators to redo a decision that has already
  been documented. The remaining blocker is operational evidence that the
  collector is actually running and producing usable `live_public` rows.

Expected outcome:
- Future backlog reads distinguish the closed source-selection decision from
  the still-open host-cadence and data-readiness proof.

Verification:
- `rg -n "canonical source decision remains open|remaining short/context proof is now data-readiness|Start scheduled read-only crypto-edge collection from the accepted OKX|OKX Backlog Status Cleanup" ...`
  - SHOWN: `REMAINING_TASKS.md` now uses the accepted OKX status wording; the
    old open-decision phrase remains only in this work-log finding as quoted
    historical evidence.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- LOW: backlog/work-log wording only. No command behavior, collector behavior,
  execution path, strategy routing, or gate behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T10:45:00Z - Backlog Lane Map OKX Cleanup

Active role: ENGINEER

Objective:
- Keep the backlog execution-lane map aligned with the accepted OKX read-only
  source decision and latest backlog wording.

What was found:
- SHOWN: `docs/BACKLOG_EXECUTION_LANES.md` still listed "Short/context venue
  readiness and source decision" and "Scheduled crypto-edge collection source
  decision and host schedule proof" under passive/operator evidence.
- SHOWN: `REMAINING_TASKS.md` now records OKX as the accepted read-only
  derivatives context source and keeps remaining proof focused on live-public
  data readiness, host cadence, snapshots, and cadence-gap alerting.

What changed:
- Updated the passive/operator evidence lane entries to remove source
  selection as open work.
- Added the OKX source-decision docs/backlog cleanup to the low-risk recent
  examples list.

Why this change:
- The lane map controls batching decisions. If it says source selection is
  still open, future passes can waste time redoing an accepted decision instead
  of collecting host evidence.

Expected outcome:
- Future proactive passes distinguish passive host/data-readiness proof from
  completed source-decision documentation.

Verification:
- `rg -n "source decision|OKX read-only|host cadence|data readiness|Backlog Lane Map OKX Cleanup|Crypto-edge OKX" ...`
  - SHOWN: lane-map entries now describe accepted OKX source-decision status
    and remaining host/data-readiness proof.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- LOW: docs-only planning metadata. No command behavior, collector behavior,
  execution path, strategy routing, or gate behavior changed.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T14:09:55Z - Backlog Hardening Batch 223

Active role: ENGINEER

Objective:
- Remediate a small batch of verified backlog hardening items from the attached
  agent reports without importing generated artifacts or changing campaign state.

What was found:
- SHOWN: the attached first patch was not directly usable because it included a
  corrupt generated `.coverage` binary patch.
- SHOWN: `services/live_router/router.py` still recorded `ai_error_ignored` and
  `proba_gate_error_ignored` in enabled gate error paths.
- SHOWN: `services/execution/strategy_runner.py::_acquire_lock()` still used a
  check-then-write lock file path with no stale-PID recovery.
- SHOWN: `scripts/check_promotion_gates.py` did not surface
  `pnl_usd_semantics`, so legacy gross-PnL and new net-of-fees evidence could
  be averaged without operator visibility.
- SHOWN: no committed strict market-quality operator template existed under
  `config/templates/`.

What changed:
- Enabled AI/proba router gate errors now fail closed; disabled gates remain
  non-blocking.
- Strategy-runner lock acquisition now uses atomic `O_CREAT|O_EXCL`, reclaims
  only dead-PID stale locks via `clean_stale_lock_file()`, and treats malformed
  locks as held.
- Promotion gate paper metrics now report `expectancy_pnl_semantics`,
  `expectancy_mixed_semantics`, and `expectancy_semantics_warning` on both the
  paper-history and JSONL evidence paths without changing expectancy pass/fail.
- Added `config/templates/market_quality_strict.yaml` as an opt-in fail-closed
  market-quality template.
- Added targeted tests for router gate fail-closed behavior, runner locks,
  PnL-semantics visibility, and the strict market-quality template.
- Updated `REMAINING_TASKS.md` to mark these remediations as implementation
  proof ready for independent review.

Why this change:
- These items remove fail-open routing behavior, close a runner concurrency
  race, make mixed legacy/net evidence visible before gate decisions, and
  provide a versioned operator config for stricter market-quality evidence.

Expected outcome:
- Enabled optional routing gates cannot silently pass orders after internal
  errors.
- Duplicate strategy-runner starts are prevented atomically, and dead stale
  locks are recoverable without manual deletion.
- Operators can identify mixed PnL semantics before treating expectancy as
  profitability evidence.
- The market-quality no-storm cycle can be run from a reviewed template instead
  of ad hoc host config.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_router_ai_engine.py tests/test_router_gates_fail_closed.py tests/test_gate_pnl_semantics_visibility.py tests/test_market_quality_strict_template.py tests/test_strategy_runner_lock.py`
  - SHOWN: `24 passed in 0.56s`.
- `git diff --check`
  - SHOWN: passed.
- Full suite was not run in this thread per the operator instruction to avoid
  long-running tests unless explicitly requested.

Remaining risk:
- HIGH: this batch touches order-routing fail-open behavior, promotion gate
  reporting, and runner concurrency. Behavior is targeted-test verified, but
  it requires independent review before acceptance.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-05T14:35:03Z - Live Router Reference Price And Safety Fail-Closed

Active role: ENGINEER

Objective:
- Remove the live-router hardcoded reference-price fallback and close the
  safety-gate exception fail-open path.

What was found:
- SHOWN: `services/live_router/router.py` used `60000.0` when no explicit
  `limit_price` or `reference_price` was supplied.
- SHOWN: the same router converted safety-gate exceptions into
  `ok_s=True, why_s="safety_check_error_ignored"`, allowing the order to
  continue after a safety-check failure.
- SHOWN: existing live-router tests pinned the old BTC-shaped fallback by
  expecting an allowed order with `limit_price == 60000.0`.

What changed:
- Added `_positive_float_or_none()` and require a finite positive explicit
  reference price from router or top-level overrides.
- Missing, zero, non-finite, or invalid reference prices now return
  `RouterDecision(False, "no_reference_price", ...)` before safety gates run.
- Safety-gate exceptions now set `safety_ok=false` and return
  `safety:safety_check_error_fail_closed:<ExceptionType>`.
- Updated live-router tests to provide explicit reference prices when testing
  downstream AI/proba/safety behavior.
- Added tests for missing reference price, invalid reference price, and
  safety-gate exception fail-closed behavior.
- Updated `REMAINING_TASKS.md` to record the live-router implementation proof
  and keep the remaining broader live fail-closed sweep visible.

Why this change:
- A synthetic BTC-shaped price can make notional/safety checks look valid for
  the wrong symbol or wrong context. A safety gate that errors must not become
  an allow decision. Both issues are order-routing fail-open risks.

Expected outcome:
- Live-router decisions require caller-provided price authority before any
  safety decision.
- Router safety-gate failures are visible and blocking instead of silently
  permissive.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_live_router_safety_contract.py tests/test_live_router_ai_engine.py tests/test_router_gates_fail_closed.py`
  - SHOWN: `13 passed in 0.34s`.
- `rg "safety_check_error_ignored|or 60000\\.0|no_reference_price|safety_check_error_fail_closed" services/live_router tests/test_live_router_safety_contract.py tests/test_live_router_ai_engine.py tests/test_router_gates_fail_closed.py -n`
  - SHOWN: no stale `safety_check_error_ignored` or `or 60000.0` remains in
    the live-router path; new fail-closed reasons are covered by tests.

Remaining risk:
- HIGH: this touches live order-routing preconditions and fail-open behavior.
  Targeted tests pass, but independent review is required before acceptance.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-05T14:54:16Z - PR 224 Paper Runner Reference Price CI Fix

Active role: ENGINEER

Objective:
- Fix the PR #224 CI/full-suite regression caused by removing the live-router
  synthetic reference-price fallback.

What was found:
- SHOWN: the operator full-suite output failed three tests:
  `test_consume_queued_intents_once_submits_and_links_order`,
  `test_queued_strategy_intent_becomes_journaled_paper_fill`, and
  `test_exit_attribution_survives_paper_order_fill_and_outcome`.
- SHOWN: those failures rejected synthetic paper market intents before
  submission because `paper_runner._decide_batch()` now called the live router
  without any explicit reference price after the `60000.0` fallback was removed.
- SHOWN: real `strategy_runner` queued intents also did not persist the current
  signal price as `reference_price` metadata.

What changed:
- Strategy-runner queued intent metadata now includes `reference_price=float(m)`
  and `reference_price_source="strategy_runner_signal_price"`.
- Paper-runner and paper-journal flow fixtures now include explicit
  `reference_price` metadata instead of relying on the removed router fallback.

Why this change:
- PR #224's fail-closed router rule is correct, but paper-market intents need a
  caller-provided price authority before the router can run safety gates. The
  correct integration fix is to pass the strategy signal price, not restore a
  BTC-shaped synthetic fallback.

Expected outcome:
- Real strategy-runner paper intents can pass router safety preconditions with
  explicit price provenance.
- Synthetic paper-flow tests exercise the same contract.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_runner_lifecycle.py::test_consume_queued_intents_once_submits_and_links_order tests/test_paper_strategy_journal_flow.py::test_queued_strategy_intent_becomes_journaled_paper_fill tests/test_paper_strategy_journal_flow.py::test_exit_attribution_survives_paper_order_fill_and_outcome tests/test_live_router_safety_contract.py tests/test_live_router_ai_engine.py tests/test_router_gates_fail_closed.py`
  - SHOWN: `16 passed in 1.09s`.
- `./.venv/bin/python -m pytest -q tests/test_paper_runner_lifecycle.py tests/test_paper_strategy_journal_flow.py tests/test_live_router_safety_contract.py tests/test_live_router_ai_engine.py tests/test_router_gates_fail_closed.py`
  - SHOWN: `19 passed in 0.78s`.

Remaining risk:
- HIGH: this is still part of the live-router/paper-runner safety precondition
  change. Full suite and GitHub CI must be re-run by the operator/CI.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-05T17:14:29Z - Resume-Hard Live Governance (Substrate Backlog #17)

Active role: ENGINEER

Objective:
- Close the substrate backlog #17 dashboard resume bypass: the
  `Resume Live Trading` path could re-enable live config from a cold state
  without the one-time-token live-enable ceremony.

What was found:
- SHOWN: `services/admin/resume_gate.py::resume_if_safe()` wrote
  `execution.live_enabled=true` via `save_user_yaml` whenever
  `is_live_enabled()` was false, then armed live state, set
  `CBP_EXECUTION_ARMED=YES`, disarmed the kill switch, and set the system
  guard RUNNING, with no ceremony provenance requirement.
- SHOWN: two existing tests encoded that bypass as expected behavior:
  `test_resume_gate_reenables_live_config_before_real_guard_check` and the
  cold-state setup of
  `test_resume_gate_rolls_back_kill_switch_when_system_guard_restore_fails`
  in `tests/test_placeholder_recovery_phase2.py`.
- SHOWN: the live-enable ceremony (`services/execution/live_enable.py::enable_live`)
  already leaves durable provenance in `live_arming.json`: a consumed token
  record with `consumed`/`consumed_epoch` written by
  `services/execution/live_arming.py::verify_and_consume`.
- SHOWN (same-file fail-open sweep): Python `json.loads` accepts `NaN`, so an
  unguarded `consumed_epoch: NaN` in the state file would make every window
  comparison false and pass provenance; an env window of `inf`/`nan` would
  create an unbounded resume window. A non-finite explicit `now_epoch` input
  would create the same age-comparison fail-open in future helper/test callers.
  All three were guarded before landing.

What changed:
- `services/execution/live_arming.py` adds read-only
  `ceremony_resume_provenance()`: valid provenance requires a consumed
  ceremony token with a finite positive `consumed_epoch` inside a bounded
  window (`CBP_RESUME_CEREMONY_MAX_AGE_S`, default `3600.0` seconds,
  non-finite/non-positive/invalid env values fall back to the strict
  default), refusing with stable reasons: `no_ceremony_provenance`,
  `ceremony_token_not_consumed`, `ceremony_provenance_invalid_ts`,
  `ceremony_provenance_future_ts`, `ceremony_window_expired:<age>s`.
- `services/admin/resume_gate.py::resume_if_safe()` no longer imports
  `save_user_yaml` or `set_live_enabled` and cannot write config. Cold/absent
  live config refuses with `live_not_enabled_ceremony_required` before any
  provenance read, guard check, or mutation. Missing/expired provenance
  refuses with `ceremony_provenance:<reason>`. All refusal and success
  payloads include the provenance record for dashboard/audit visibility; the
  existing Operations page already renders `reason` on refusal.
- `dashboard/pages/60_Operations.py` updates the Live Trading Control caption
  so the Resume button no longer claims to re-enable live trading; it now
  states the ceremony requirement and RUNNING restore behavior.
- Tests: `tests/test_resume_gate_ceremony_provenance.py` (new) proves the
  fail-closed provenance matrix (missing file, unconsumed token, invalid ts,
  future ts, expired window, corrupt state file, env override + invalid env
  fallback, non-finite `consumed_epoch` and non-finite explicit clock
  regressions) and the resume proofs required by the backlog item: refusal
  without ceremony, refusal on expired window, and
  ceremony-armed-then-halted success using the real provenance reader.
  `tests/test_placeholder_recovery_phase2.py` updates the two
  bypass-encoding tests (cold-state now must refuse without any config
  write) and adds a provenance stub plus removes obsolete `save_user_yaml`
  guard patches on the three preserved tests.

Why this change:
- The resume gate must be a bounded recovery path inside an accepted arming
  window, not a second live-enable path. Anchoring resume authority to the
  consumed ceremony token keeps `services/execution/live_enable.py` the only
  path that can turn live on.

Deliberate contract changes for reviewer attention:
- Cold-state resume now refuses instead of re-enabling live config; the
  operator recovery path is re-running the ceremony.
- A halt older than the resume window also requires a fresh ceremony. The
  `3600.0`-second default window is a policy number chosen conservatively and
  is explicitly open to operator adjustment in review.

Verification:
- `python3 -m pytest -q tests/test_resume_gate_ceremony_provenance.py tests/test_placeholder_recovery_phase2.py`
  - SHOWN: `22 passed`.
- Neighborhood (all arming/resume/live-enable test files):
  - SHOWN: `51 passed`.
- Every test file importing `live_arming`/`resume_gate`/`live_enable` (28 files):
  - SHOWN: `262 passed, 1 warning`.
- Full local suite in six chunks over all 707 test files:
  - SHOWN: `2358 passed, 33 skipped, 0 failed`; all skips are explicit
    optional-companion or dated-deadline skips.

Remaining risk:
- HIGH-risk review completed: independently reviewed and accepted by the human
  operator on 2026-07-05, then merged as PR #226 to `review-stabilized` and
  synced to `master` by PR #227.
- The accepted resume window default is `3600.0` seconds with `60s`
  future-skew tolerance unless a future reviewed policy change adjusts it.
- CI passed on PR #226 and on the master sync PR #227 before merge.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T21:42:07Z - Intent TTL For Live Consumers (Substrate Backlog #18)

Active role: ENGINEER

Objective:
- Close the substrate backlog #18 intent-age gap: live consumers checked
  market snapshot freshness but not the intent's own age, so a restart after
  hours or days could submit an intent sized and justified by stale context
  at current prices.

What was found:
- SHOWN: `storage/live_intent_queue_sqlite.py::claim_next_queued()` dequeues
  by `created_ts ASC` and `services/execution/live_intent_consumer.py`
  processes claimed intents through market-quality/risk/dedupe/router with no
  check on `created_ts` age; only `is_snapshot_fresh()` gates market data
  freshness before queue claims.
- SHOWN: the canonical production consumer is `live_intent_consumer.py`
  (wrapped by `scripts/run_intent_consumer_safe.py` via
  `scripts.live.run_live_intent_consumer`); the older
  `services/execution/intent_consumer.py` is reached only through
  `scripts/compat/run_intent_consumer.py` and uses non-claiming `next_queued()`.
  TTL was scoped to the canonical consumer only.
- SHOWN: reconciler scan sources are `submitted`/`submit_unknown`
  (`intent_lifecycle.RECONCILER_LIVE_QUEUE_SOURCES`), so an `expired` status
  outside that set is terminal for the reconciler by construction.
- SHOWN: pre-change fixture audit found the fail-closed contract would affect
  exactly three test files: two live-consumer harness files whose fake intents
  carried no `created_ts`, and `tests/test_live_execution_wiring.py` whose two
  real-store intents carried a hardcoded stale `2026-04-02` timestamp. Those
  fixtures were updated to runtime-fresh timestamps as a direct consequence of
  the new contract.

What changed:
- `services/execution/intent_ttl.py` (new): `check_intent_age()` with
  `CBP_MAX_INTENT_AGE_SEC` (default `300.0`s). Fail-closed matrix: missing
  `created_ts` -> `intent_ttl:missing_created_ts`; unparseable or non-finite
  -> `intent_ttl:invalid_created_ts`; non-finite explicit clock input ->
  `intent_ttl:invalid_now`; more than 60s in the future ->
  `intent_ttl:future_created_ts`; older than the window ->
  `intent_ttl:expired:<age>s`. Env overrides that are empty, unparseable,
  non-finite, or non-positive fall back to the strict default.
- `services/execution/intent_lifecycle.py`: `expired` added as a terminal
  status reachable from `queued` and `submitting` only, and added to
  `SUBMIT_OWNER_LIVE_QUEUE_TARGETS`. `submitted` intents deliberately cannot
  expire because that lane belongs to the reconciler. Reconciler source/target
  sets are unchanged.
- `storage/live_intent_queue_sqlite.py::update_status()`: SQL transition
  guard kept in sync with the lifecycle table (`expired` in the terminal
  NOT-IN list; reachable from `queued`/`submitting`).
- `services/execution/live_intent_consumer.py`: age check at the claim
  boundary before market-quality, risk, dedupe, and router processing.
  Age-failed intents are marked `expired` with the TTL reason as `last_error`;
  an `expired` counter is included in consumer status writes. If the expiry
  write itself fails, the consumer logs and skips the intent without submitting
  because nothing has reached the venue.
- Tests: `tests/test_intent_ttl_expiry.py` (new) covers the fail-closed unit
  matrix, lifecycle vocabulary, real-SQLite store transitions, and consumer
  integration for aged, missing-ts, fresh, and mixed batches. Existing
  live-consumer harness fixtures gained fresh `created_ts` values.

Why this change:
- The claim boundary is the single choke point every live submission passes
  through, so one check there covers restart-after-idle, backlog-drain, and
  stale-queue scenarios without touching queue schema, paper paths, or
  reconciler behavior.

Deliberate contract changes for reviewer attention:
- Intents without a usable `created_ts` are now expired rather than submitted.
- The `300.0`s default window and `60`s future-skew tolerance are policy
  numbers, not evidence-derived; operator may adjust in review.
- The legacy compat consumer (`services/execution/intent_consumer.py`) is
  explicitly out of scope and should be retired or classified before any live
  use.
- Intents already in `submitted` cannot expire through TTL; reconciler remains
  authoritative for that state.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_intent_ttl_expiry.py tests/test_live_execution_wiring.py tests/test_live_intent_consumer_duplicate_prevention.py tests/test_live_intent_consumer_order_store_gating.py`
  - SHOWN: `35 passed in 2.19s`.
- `./.venv/bin/python -m pytest -q tests/test_intent_ttl_expiry.py tests/test_live_execution_wiring.py tests/test_live_intent_consumer_duplicate_prevention.py tests/test_live_intent_consumer_order_store_gating.py tests/test_live_consumer_risk_claim.py tests/test_live_intent_consumer_orphan_fix.py tests/test_live_intent_queue_claim_race.py tests/test_live_intent_queue_integrity.py tests/test_live_queue_submit_owner_authority.py tests/test_live_state_authority_write_result.py`
  - SHOWN: `55 passed in 2.48s`.
- `./.venv/bin/python -m py_compile services/execution/intent_ttl.py services/execution/intent_lifecycle.py services/execution/live_intent_consumer.py storage/live_intent_queue_sqlite.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH-risk review completed: independently reviewed and accepted by the human
  operator on 2026-07-05, then merged as PR #230 to `review-stabilized`.
  GitHub CI passed on PR #230 before merge.
- Intents stranded in `submitting` by a crashed consumer are not reclaimed or
  expired by this change (pre-existing behavior, unchanged); they remain
  visible via queue listing.
- Acceptance state: `ACCEPTED`.

## 2026-07-05T22:38:00Z - Sample-Mode Provenance From Actual OHLCV Source (Active Backlog #21)

Active role: ENGINEER

Objective:
- Close Active Backlog #21's evidence-poisoning gap: paper evidence labels
  `ohlcv_sample_mode` from `CBP_USE_SAMPLE_OHLCV`, while the trust decision
  should derive from the actual data source/path that produced OHLCV rows.

What was found:
- SHOWN: `services/execution/strategy_runner.py::_fetch_public_ohlcv()` returned
  rows only, so the caller could not distinguish public exchange OHLCV from
  sample-file OHLCV after fetch.
- SHOWN: `_public_ohlcv_evidence_extra()` previously stamped
  `market_data_source` and `ohlcv_sample_mode` from the env flag, then the
  runner attached those fields to strategy evidence and intent metadata.
- SHOWN: env-only stampers also existed in
  `services/strategies/evidence_logger.py`,
  `scripts/run_paper_strategy_evidence_collector.py`,
  `services/strategies/es_daily_trend.py`, and the shadow would-be-fill stamp
  in `services/execution/_executor_submit.py`; none marked those labels as
  env-derived.
- SHOWN: the submitted patch had one parser inconsistency: fetch treated only
  `1`/`true`/`yes` as sample mode, while evidence stamping also treated `on`
  as truthy. That could create a false provenance mismatch for
  `CBP_USE_SAMPLE_OHLCV=on`.

What changed:
- `strategy_runner._fetch_public_ohlcv()` now returns `(rows, source_info)`.
  `source_info` carries the actual source (`sample_ohlcv`, `public_ohlcv`, or
  `none`), sample file path when applicable, fallback flag, row count, and the
  env claim at fetch time.
- `strategy_runner._public_ohlcv_evidence_extra()` derives
  `market_data_source` and `ohlcv_sample_mode` from `source_info`, records the
  env claim as `ohlcv_sample_mode_env`, marks source-derived fields with
  `ohlcv_sample_mode_origin="source"`, and sets `ohlcv_source_mismatch` on
  env/source disagreement or unknown source.
- The runner loop holds the signal fail-closed on `ohlcv_source_mismatch`:
  operator status note `sample_mode_provenance_mismatch`, no signal
  computation, no intent enqueue.
- Env-only stampers now mark `ohlcv_sample_mode_origin="env"`, so claimed
  labels are distinguishable from source-derived labels.
- `_executor_submit` no longer hardcodes `ohlcv_sample_mode=False`; it records
  the env-derived claim and origin marker for shadow would-be-fill records.
- Local correction added in this thread: `_sample_ohlcv_env_enabled()` centralizes
  runner truthy parsing and includes `on`, with a regression proving fetch and
  evidence agree for `CBP_USE_SAMPLE_OHLCV=on`.
- `REMAINING_TASKS.md` documents the separate remaining laundering path:
  sample rows can still be persisted into the local OHLCV snapshot store
  without source metadata and later read as `local_snapshot`, which the gate
  currently counts as public.

Why this change:
- The fetch site is the earliest point where the runner knows whether rows
  came from public exchange data or a sample file. Carrying that truth forward
  is smaller and safer than trying to infer provenance later from env or
  downstream artifacts.

Expected outcome:
- Paper evidence cannot be labeled public merely because the env flag says it
  is public when the runner knows rows came from sample data.
- If future code drift creates a disagreement between env claim and fetch
  source, the campaign holds fail-closed before producing signal or intent
  evidence.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_sample_mode_provenance.py tests/test_strategy_runtime_runner.py`
  - SHOWN: `44 passed in 1.43s`.
- `./.venv/bin/python -m py_compile services/execution/strategy_runner.py services/execution/_executor_submit.py services/strategies/es_daily_trend.py services/strategies/evidence_logger.py scripts/run_paper_strategy_evidence_collector.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this changes provenance semantics for the canonical paper evidence
  runner and can affect what the promotion gate means; it must not land without
  independent human review and a fresh GitHub CI run.
- The local snapshot-store laundering path is documented but not closed in
  this patch; it needs a separate reviewed schema/source-metadata change or a
  sample-mode snapshot persistence block.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-06T19:08:55Z - Next Strategy Validation Sequencing Note

Active role: DIRECTOR

Objective:
- Make the 2026-07-06 check-in recommendation visible in git: identify the
  next strategy validation action without starting another persistent campaign.

What was found:
- SHOWN: `configs/paper_evidence_campaigns.laptop.json` already runs
  `es_daily_trend_v1` and `breakout_default`.
- SHOWN: `configs/paper_evidence_campaigns.hetzner.example.json` already runs
  `ema_cross_default`.
- SHOWN: `configs/strategies/pullback_recovery_default.yaml` exists, and
  `REMAINING_TASKS.md` already requires an isolated Stage 0 proof before any
  persistent `pullback_recovery_default` campaign.
- SHOWN: `REMAINING_TASKS.md` item 12 already frames `funding_extreme` as the
  first crypto-edge context strategy to wire, but that path still needs the
  context/crypto-edge contract before it can produce governed paper evidence.

What changed:
- Updated `REMAINING_TASKS.md` current state, item 7, and item 12 to record:
  `pullback_recovery_default` is the next runnable non-persistent Stage 0
  validation candidate; `funding_extreme` is the higher-value profitability
  candidate but remains blocked on context/crypto-edge wiring; no new
  persistent campaign should be started before proof.

Why this change:
- The note prevents the next check-in from conflating two different tasks:
  a runnable isolated proof (`pullback_recovery_default`) versus a higher-value
  strategy family that first needs infrastructure (`funding_extreme`).

Expected outcome:
- Future strategy work follows the intended order: run isolated Stage 0
  pullback proof first; build crypto-edge context wiring before attempting a
  governed `funding_extreme` paper campaign.

Verification:
- Docs-only change.
- No tests run; no runtime behavior changed.

Remaining risk:
- LOW: backlog sequencing note only.
- Acceptance state: `ACCEPTED`.

## 2026-07-08T21:39:10Z - OHLCV Snapshot Source Provenance Substrate

Active role: ENGINEER

Objective:
- Add source provenance to local OHLCV snapshots so sample-fed rows cannot be
  indistinguishable from public OHLCV at the snapshot-file layer.

What was found:
- SHOWN: `services/market_data/local_data_reader.py::write_local_ohlcv_snapshot`
  wrote bare JSON candle lists with no source metadata.
- SHOWN: `services/execution/strategy_runner.py::_fetch_public_ohlcv` already
  knows which branch produced rows (`sample_ohlcv` or `public_ohlcv`) after the
  prior sample-mode provenance work, but `_persist_public_ohlcv_snapshot`
  discarded that source when writing the shared snapshot file.
- SHOWN: `services/analytics/signal_quality.py` reads either explicit OHLCV
  files or local snapshots; before this change, its provenance metadata could
  not report whether snapshot rows came from sample or public data.
- SHOWN: the promotion gate still counts `market_data_source=local_snapshot` as
  public. Therefore this change adds provenance substrate but does not by
  itself close gate-level acceptance of local snapshots.

What changed:
- `write_local_ohlcv_snapshot(..., source=)` now writes a versioned envelope:
  `{version: 2, source, written_ts, candles}`. The default source is
  `"unknown"` so a caller that forgets to pass source cannot mint public
  ancestry.
- Existing `_load_local_ohlcv()` remains envelope-compatible and still reads
  legacy bare-list snapshots.
- Added `load_local_ohlcv_snapshot_provenance()` to inspect source, legacy
  status, row count, path, and timestamp without changing consumer data paths.
  Missing, corrupt, and legacy snapshots report `source="unknown"` fail-closed.
- `strategy_runner` now threads fetch-branch truth into snapshot writes:
  sample fetch/fallback writes `sample_ohlcv`; live fetch writes
  `public_ohlcv`.
- `signal_quality` now includes `snapshot_source` and
  `snapshot_source_legacy` for local-snapshot and explicit-file OHLCV loads.
- `REMAINING_TASKS.md` was updated to state the remaining boundary explicitly:
  if future promotion evidence accepts `market_data_source=local_snapshot`, a
  separate reviewed gate assertion should require non-legacy
  `snapshot_source=public_ohlcv`.

Why this change:
- The snapshot writer is the single point where OHLCV rows are persisted into
  local files. Carrying source there is the smallest compatible way to prevent
  sample/public ancestry from being lost before downstream research or gate
  code can assert it.

Expected outcome:
- New snapshot files are self-describing with source ancestry.
- Legacy snapshots remain readable but are explicitly unknown rather than
  trusted public.
- Campaign-planner/signal-quality artifacts can expose sample ancestry instead
  of silently treating every local snapshot the same.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_ohlcv_snapshot_provenance.py tests/test_signal_quality.py tests/test_strategy_runtime_runner.py`
  - SHOWN: `49 passed in 1.12s`.
- `./.venv/bin/python -m py_compile services/market_data/local_data_reader.py services/execution/strategy_runner.py services/analytics/signal_quality.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- HIGH: this touches paper evidence/provenance substrate and the canonical
  runner snapshot path; it needs independent review and CI before merge.
- Gate-level closure remains separate: `scripts/check_promotion_gates.py` still
  treats `local_snapshot` as public and does not yet consume
  `snapshot_source`.
- External scripts outside the repo that parse OHLCV snapshot JSON as a bare
  list would need to adopt the envelope-tolerant reader pattern.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-08T21:43:22Z - Typed Order Retry Classification

Active role: ENGINEER

Objective:
- Replace substring/message-based retry classification with typed,
  fail-closed exception classification for order submission/retry paths.

What was found:
- SHOWN: `services/execution/retry_policy.py::is_retryable_exception()` used
  substrings from both exception type name and message text.
- SHOWN: that legacy classifier could misclassify a transient venue/network
  error as non-retryable if the message contained words like `account`, and
  could classify an arbitrary exception as retryable if the message contained
  strings like `429`, `503`, `timeout`, or `temporary`.
- SHOWN: current installed `ccxt.InvalidNonce` subclasses `ccxt.NetworkError`,
  but the prior policy treated invalid nonce as a hard non-retryable class.
- SHOWN: `services/execution/order_router.py` and
  `services/execution/fill_confirmation.py` are the in-repo users of
  `is_retryable_exception()`.

What changed:
- `is_retryable_exception()` now classifies by exception type only.
- Retryable classes: `ccxt.NetworkError` and subclasses, built-in
  `ConnectionError`/`TimeoutError`, plus exact transient type-name fallbacks
  for non-ccxt transport errors.
- Definitive non-retryable classes: `InsufficientFunds`, `InvalidOrder`
  including `OrderNotFound`, `AuthenticationError`, `BadRequest`,
  `ArgumentsRequired`, `NotSupported`, and `InvalidNonce`.
- Generic `ccxt.ExchangeError`/`ccxt.BaseError` and unknown exceptions now fail
  closed to non-retryable.
- Message text is never consulted.
- Added `tests/test_retry_policy_typed.py` to pin transient/fatal ccxt classes,
  `InvalidNonce` precedence, generic exchange error fail-closed behavior,
  message-immunity regressions, built-in transport exceptions, exact name
  fallback, and unknown exception default.
- `REMAINING_TASKS.md` documents this slice and leaves the fault-injection
  proof plus venue-lookup-not-found policy as separate remaining work.

Why this change:
- Retry eligibility should depend on a typed error contract, not mutable venue
  phrasing, order IDs, quantities, or arbitrary message contents. For submit
  paths, fail-closed non-retryable classification is safer than duplicate
  submission.

Expected outcome:
- Transient ccxt/network failures can still enter the router's
  verify-before-retry path.
- Definitive venue/request/auth/funds/order errors stop retrying immediately.
- Unknown venue errors no longer blind-retry; ambiguity is left to reconcile
  paths rather than message guessing.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_retry_policy_typed.py tests/test_order_router_retry_flow.py`
  - SHOWN: `26 passed in 0.74s`.
- `./.venv/bin/python -m py_compile services/execution/retry_policy.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.
- An earlier attempted pytest command used stale test filenames
  (`tests/test_order_router.py`, etc.) and did not run tests; it was replaced
  by the repo-discovered affected test files above.

Remaining risk:
- HIGH: this changes live order retry semantics and must go through
  independent review and GitHub CI before merge.
- Deliberate policy choices needing review: generic `ccxt.ExchangeError` is
  non-retryable, and `InvalidNonce` stays non-retryable despite its current
  ccxt `NetworkError` inheritance.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-08T21:47:35Z - Crash-Consistency Fault-Injection Proof

Active role: ENGINEER

Objective:
- Package the accepted crash-consistency proof for live submit, fill,
  reconcile, and restart paths without changing production behavior.

What was found:
- SHOWN: the new test file uses real sqlite stores and raises `SystemExit`
  from mocked side effects so the consumer's `except Exception` recovery path
  cannot soften the simulated process death.
- SHOWN: exactly-once venue submission is pinned across submit crash points,
  and fill accounting is pinned exactly-once by fill id across replay.
- SHOWN: crashes between dedupe claim or venue submit and queue status write
  strand intents at `submitting`; the dedupe guard preserves safety by blocking
  resubmission, but liveness still needs operator attention or a future
  dedupe-informed aged-submitting sweep.
- SHOWN: crashes after canonical fill accounting but before the `filled`
  transition converge via the reconciler cursor overlap and idempotent inserts.

What changed:
- Added `tests/test_crash_consistency_fault_injection.py` with seven
  crash-injection scenarios covering submit, ambiguous submit recovery,
  reconciler fill convergence, canonical fill accounting replay, and filled
  transition replay.
- Updated `REMAINING_TASKS.md` to record the implementation proof and the two
  follow-up findings: aged `submitting` liveness and the residual multi-fill
  cursor edge beyond the overlap window.

Why this change:
- Fault injection converts prior code-reading assumptions about live-path
  crash behavior into executable regression proof while keeping production
  logic unchanged.

Expected outcome:
- Future changes to live intent consumption, reconciliation, or canonical fill
  accounting fail tests if they break exactly-once submit/accounting or the
  documented convergence behavior.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_crash_consistency_fault_injection.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_reconciler_cursor_safety.py tests/test_live_intent_queue_claim_race.py tests/test_intent_ttl_expiry.py`
  - SHOWN: `32 passed, 4 warnings in 2.77s`.
- `./.venv/bin/python -m py_compile tests/test_crash_consistency_fault_injection.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.

Remaining risk:
- MEDIUM/HIGH: test-only proof touches live-trading failure modes but does not
  implement production recovery for aged `submitting` rows or the residual
  multi-fill cursor edge.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-09T23:13:04Z - Live Submit/Reconcile Convergence Recovery Stack

Active role: ENGINEER

Objective:
- Package the accepted stacked live-path recovery patches that convert the
  crash-consistency findings into convergence behavior: stale `submitting`
  recovery, canonical-fill lookback for deferred filled transitions, and
  bounded terminal disposition for persistent venue not-found `submit_unknown`
  intents.

What was found:
- SHOWN: the prior fault-injection proof left three documented-safe
  `submitting` strandings where duplicate submission was prevented but liveness
  required operator attention.
- SHOWN: a later fill can advance the shared venue/symbol trade cursor beyond
  the overlap window while an earlier order is already canonically accounted
  but still waiting on its `filled` queue transition.
- SHOWN: the `submit_unknown` recovery lane confirmed ambiguous venue orders
  when found by client order id, but had no bounded terminal policy for repeated
  clean venue not-found responses.

What changed:
- `services/execution/live_intent_consumer.py` now runs a startup
  `_recover_stale_submitting()` sweep. It never submits; aged venue-found rows
  converge to `submitted`, aged venue-absent rows move to `submit_unknown`,
  young rows and lookup failures stay untouched, and env parsing fails back to
  a strict default.
- `services/execution/live_reconciler.py` now has a read-only
  `_accounted_fills_for_order()` lookback in the deferred filled-transition
  branch. If the trade cursor no longer re-fetches a fill but the canonical
  journal already accounted it by order id or client order id, the queue
  transition can converge to `filled`.
- `services/execution/live_reconciler.py` now tracks repeated clean
  not-found observations for `submit_unknown` intents and permits terminal
  `error` disposition only after both configured thresholds pass.
- `services/execution/intent_lifecycle.py` now permits the reconciler-specific
  `submit_unknown -> error` transition for that bounded terminal policy while
  still blocking other premature submit-unknown targets.
- Added `tests/test_stale_submitting_recovery.py` and
  `tests/test_submit_unknown_not_found_policy.py`, and extended
  `tests/test_crash_consistency_fault_injection.py`.
- Updated `REMAINING_TASKS.md` item 3 and item 4 with the closure proofs and
  remaining live-capital review risks.

Why this change:
- The smallest production change is to let existing authority owners converge
  their own states: the consumer owns stale `submitting` recovery, and the
  reconciler owns ambiguous submit recovery and filled-transition convergence.
  This avoids a new repair daemon or schema migration.

Expected outcome:
- Crash/restart cases that were previously safe-but-stranded now converge
  without duplicate venue submission.
- Already-accounted fills do not remain deferred forever solely because a
  later fill advanced the cursor outside the overlap window.
- Persistent venue not-found responses leave an auditable terminal error after
  a bounded observation window instead of polling forever.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_stale_submitting_recovery.py tests/test_crash_consistency_fault_injection.py tests/test_submit_unknown_not_found_policy.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_reconciler_cursor_safety.py tests/test_live_intent_queue_claim_race.py tests/test_intent_ttl_expiry.py tests/test_retry_policy_typed.py tests/test_order_router_retry_flow.py`
  - SHOWN: `73 passed, 7 warnings in 3.94s`.

Remaining risk:
- HIGH: this changes live intent consumer/reconciler behavior and lifecycle
  authority for `submit_unknown -> error`; it requires independent review and
  GitHub CI before merge.
- Policy values are review decisions: stale `submitting` recovery defaults to
  120 seconds; terminal not-found disposition defaults to 3 observations and
  15 minutes.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-10T00:10:54Z - Clock/Venue-Time Sanity Gate (Backlog Item #11)

Active role: ENGINEER

Objective:
- Implement the clock/venue-time sanity slice: every window-based safety
  mechanism now on master (intent TTL, resume ceremony window,
  stale-submitting threshold, submit-unknown not-found age, reconciler
  cursor overlap) silently assumes sane host and venue clocks; a skewed
  clock corrupts all of them at once.

What was found:
- CLAIMED by the submitted patch author: `ccxt.coinbase().has['fetchTime'] == True`;
  this thread did not perform a live venue probe.
- SHOWN: the consumer's market-quality block provides the established
  reject-with-reason + escalate-on-write-failure pattern; the clock gate
  mirrors it exactly.
- Interaction considered: a skew rejection is terminal (`rejected`), so a
  blocked intent never enters the stale-submitting -> submit_unknown ->
  not-found disposition chain; and because exceeded measurements are never
  cached, a single-measurement blip rejects at most one loop iteration's
  intents before re-measuring.

What changed:
- `services/execution/clock_sanity.py` (new): `measure_venue_skew(ex)`
  computes skew = venue_time − round-trip midpoint with rtt recorded as
  measurement quality; non-finite/non-positive venue times are unmeasured
  (fail-closed shape checks). `check_venue_clock(venue, factory)` is the
  cached gate: `ok=False` ONLY on an affirmative measured skew beyond
  `CBP_MAX_CLOCK_SKEW_MS` (default 5000ms); OK results cached for
  `CBP_CLOCK_SKEW_CHECK_INTERVAL_S` (default 300s); exceeded and failed
  measurements never cached; unsupported venues are a cached limitation
  record; the factory is invoked only on cache misses and its handle is
  closed after measurement. Both envs fail-closed parsed.
- `services/execution/live_intent_consumer.py`: per-intent gate after the
  market-quality check, before the risk claim (no risk budget consumed for
  clock-blocked intents): not-ok -> status note `clock_skew_blocked` +
  reject with `clock_skew_blocked:<reason>`, escalating to
  `submit_unknown` if the rejection write fails — byte-for-byte the mq
  pattern.
- `scripts/check_clock_sanity.py` (new): operator launch-evidence tool —
  host UTC, best-effort NTP status (timedatectl/chronyc, degrades to
  "unavailable"), per-venue skew and verdict; exit codes 0 ok / 1 exceeded
  / 2 unmeasurable.
- `tests/test_clock_sanity.py` (new, 18 tests): midpoint math incl.
  negative skew; unsupported/limitation record; fetch errors and invalid
  venue times (nan/inf/0/negative/non-numeric) unmeasured; gate blocks only
  on affirmative excess; unsupported/unmeasured/factory errors never block;
  OK-result caching honors the interval; exceeded results re-measure
  immediately; unsupported venues cached; env overrides with nan/inf
  fallbacks for both knobs; consumer integration — exceeded skew rejects
  the intent with the reason and zero venue submits, ok skew submits.

Deliberate v1 boundaries for reviewer attention:
- Venues without a server-time endpoint never block (recorded limitation,
  per the backlog's "venue server-time query or limitation record").
- Measurement errors never block — only affirmative measured excess does.
  Blocking on persistently unmeasurable time is a stricter follow-up if
  desired.
- Policy numbers: 5000ms threshold, 300s check interval; both
  operator-adjustable via env with fail-closed parsing.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_clock_sanity.py`
  - SHOWN: `18 passed in 0.22s`.
- `./.venv/bin/python -m pytest -q tests/test_clock_sanity.py tests/test_consumer_locking_and_paths.py tests/test_crash_consistency_fault_injection.py tests/test_intent_ttl_expiry.py tests/test_live_consumer_state_risk_reset.py tests/test_live_consumer_risk_claim.py tests/test_live_execution_wiring.py tests/test_live_intent_consumer_orphan_fix.py tests/test_live_intent_queue_claim_race.py tests/test_live_intent_consumer_duplicate_prevention.py tests/test_live_intent_queue_lifecycle_fields.py tests/test_live_intent_upsert_insert_only.py tests/test_live_lock_stale_pid_cleanup.py tests/test_live_reconciler_cursor_safety.py tests/test_live_intent_consumer_order_store_gating.py tests/test_live_reconciler_fill_attribution.py tests/test_live_intent_queue_integrity.py tests/test_live_reconciler_order_store_gating.py tests/test_live_submit_unknown_lifecycle.py tests/test_live_reconciler.py tests/test_queue_update_status_preserves_ids.py tests/test_stale_submitting_recovery.py tests/test_submit_unknown_not_found_policy.py`
  - SHOWN: `124 passed, 7 warnings in 4.67s`.
- `./.venv/bin/python -m py_compile services/execution/clock_sanity.py services/execution/live_intent_consumer.py scripts/check_clock_sanity.py tests/test_clock_sanity.py`
  - SHOWN: passed.
- `git diff --check`
  - SHOWN: clean.
- Full local suite was not run by this thread; GitHub CI remains the required
  merge gate.

Remaining risk:
- HIGH: adds a gate on the live submit path; independent human review and
  GitHub CI required before landing.
- Host-side NTP enforcement remains an operator/server task; the script
  provides the evidence artifact.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-10T08:26:56Z - Trading-Loop Heartbeats + External Dead-Man (Substrate Backlog #6 Slice)

Active role: ENGINEER

Objective:
- Give each managed trading loop an independent liveness signal and an
  external alert-on-absence check within a defined window. Systemd units
  (#5 slice) restart crashes; nothing detected silent hangs — existing
  status files are event-driven and can read "running" while a loop is
  stuck inside a venue call.

Course correction (recorded deliberately):
- SHOWN: mid-batch, the item's own 2026-07-03 audit note surfaced existing
  dormant infrastructure — `services/process/heartbeat.py::write_heartbeat()`
  with zero callers and `services/process/watchdog.py` reading heartbeat
  state. A parallel heartbeat module had already been drafted; it was
  deleted and the work reshaped to EXTEND the existing module instead,
  per the item's "prefer boring infrastructure over more custom code" and
  Structure Hygiene #1 (no twin modules).

What changed:
- `services/process/heartbeat.py`: named per-loop beats added —
  `write_named_heartbeat(name, extra=)` writes
  `runtime/heartbeats/{name}.json` atomically (tmp+rename) with pid/seq,
  rate-limited via `CBP_HEARTBEAT_MIN_INTERVAL_S` (default 5.0s; 0 =
  every iteration; invalid/non-finite -> default), and NEVER raises — a
  heartbeat must not be able to break a trading loop. Readers:
  `read_named_heartbeat`, `named_heartbeat_age_s`. The legacy
  single-file bot-runner path is byte-identical (watchdog and
  crash-snapshot readers untouched; contract pinned by test).
- `services/execution/live_intent_consumer.py` +
  `services/execution/live_reconciler.py`: one `write_named_heartbeat`
  call at the top of each loop iteration (`intent_consumer`,
  `live_reconciler`) with the loop counter as extra. No other loop
  behavior changed.
- `scripts/check_dead_man.py`: external liveness verdicts over named
  beats — exit 0 healthy / 1 stale / 2 missing (missing dominates);
  `--names` declares what MUST be alive on the host and an empty name set
  fails closed as missing;
  `CBP_DEAD_MAN_MAX_AGE_S` default 180.0s fail-closed parsed; `--json`
  report; `--alert` dispatches a critical alert best-effort through the
  existing `services/alerts/alert_dispatcher.send_alert` (never raises).
- `packaging/systemd/cbp-dead-man.service` (oneshot, hardened, no arming
  tokens, `CBP_STATE_DIR=/var/lib/cbp`, `StateDirectory=cbp`) +
  `cbp-dead-man.timer` (every 60s, 120s boot grace).
  `scripts/SCRIPTS.md` entry anchored away from the pending #5 slice's
  insertion point so both patches apply in either order.
- `tests/test_dead_man.py` (new, 11 tests): sequenced atomic payloads;
  rate limiting; never-raises on unwritable dir; interval env fallbacks;
  checker verdict matrix incl. missing-dominates-stale, empty-name
  fail-closed behavior, and max-age env fallbacks; CLI end-to-end exit
  codes 0/2; both loops emit beats under a
  one-iteration harness; LEGACY-CONTRACT PIN (single-file payload shape and
  path unchanged); item-mandated bounded-stop proof (stop honored one
  iteration after request — startup deliberately clears stale stop files,
  which the proof respects); item-mandated synthetic alert-delivery proof
  (no configured channels still lands the local JSONL fallback).

Deliberate boundaries for reviewer attention:
- Policy numbers: 5.0s beat interval, 180s dead-man age, 60s timer cadence.
- The watchdog's auto-stop is NOT wired to named beats in this slice; the
  item prefers the external dead-man lane first, and watchdog policy per
  loop is a separate decision. Push channels (healthchecks/ntfy) layer on
  the checker's exit codes as operator choices.

Verification:
- `python3 -m pytest -q tests/test_dead_man.py`
  - CLAIMED by originating patch author before review packaging:
    `11 passed`.
- `./.venv/bin/python -m py_compile services/process/heartbeat.py services/execution/live_intent_consumer.py services/execution/live_reconciler.py scripts/check_dead_man.py tests/test_dead_man.py`
  - SHOWN in review branch: passed with no output.
- `./.venv/bin/python -m pytest -q tests/test_dead_man.py`
  - SHOWN in review branch: `11 passed in 0.80s`.
- 31 nearby test files importing or exercising the touched loop, reconciler,
  heartbeat, checker, and alert surfaces:
  - SHOWN in review branch: `189 passed, 7 warnings in 7.18s`.
- `git diff --check`
  - SHOWN in review branch: passed with no output.

Remaining risk:
- MEDIUM-HIGH: one added call per iteration in both live loops (wrapped
  never-raise); everything else is new files. Independent human review and
  GitHub CI required before landing.
- Full local suite was not rerun in this review branch per operator time
  constraints; use GitHub CI as the broad-suite proof.
- Independent of the pending systemd-units slice except trivial doc-tail
  overlaps; both orders apply.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
## 2026-07-10T15:25:22Z - Durable Data-State Backup/Restore Tooling (Substrate Backlog #8 Tooling Half)

Active role: ENGINEER

Objective:
- Ship the durable `data_dir()` tooling half of the full-state
  backup/restore drill: consistent backups of data-state databases,
  tamper-evident verification, and a guarded restore — leaving runtime/
  config/snapshot family inclusion decisions, host drill execution, and
  evidence filing as the operator half, per the existing policy doc.

What was found:
- SHOWN: `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md` already documents the
  drill policy, procedure, and pass criteria (status POLICY_DOCUMENTED,
  "does not execute"). A freshly drafted duplicate runbook was deleted and
  the existing doc extended with a Tooling section instead — same
  no-twin discipline as the heartbeat batch, applied to docs.
- SHOWN (alignment guard catch): a `Path("data")` literal in the new
  script tripped `test_no_legacy_state_paths`; the archive-internal
  prefix was renamed to a named constant (`ARCHIVE_SUBDIR="state"`) so
  state paths flow only through `app_paths`.

What changed:
- `scripts/backup_state.py` (new): `backup --dest` takes sqlite
  backup-API snapshots of every database under the data dir —
  transactionally consistent even under active writers, where plain file
  copies tear pages under WAL — plus checksummed copies of non-database
  state, recorded in `backup_manifest.json` (per-file sha256, sizes,
  counts); SQLite sidecars (`-wal`, `-shm`, `-journal`) are excluded
  because the backup API folds committed database content into the
  snapshot; safe to run while services are live. `verify` is read-only:
  every checksum plus `PRAGMA integrity_check` per database, and rejects
  invalid manifest relative paths.
  `restore [--force]` fail-closed guard order: (1) the backup must
  verify completely before anything is touched; (2) any `*.lock` under
  the state dir blocks restore — live writers during restore corrupt both
  worlds; (3) a non-empty data dir requires `--force` and the existing
  data is moved aside to `data.pre-restore-<stamp>`, never deleted;
  (4) only manifest-listed files are restored; (5) post-restore every
  file is re-checksummed against the manifest. Exit codes 0/1/2
  (ok/failure/guard-blocked). Scratch restore per policy step 4 = point
  `CBP_STATE_DIR` at the scratch root.
- `docs/FULL_STATE_BACKUP_RESTORE_DRILL.md`: Tooling section mapping the
  tool to procedure steps 3-5; boundary updated (tooling SHOWN, drill
  execution still UNVERIFIED); runtime/config/snapshot families outside
  `data_dir()`, secrets scan, and resume/idempotence proofs named as
  deliberately drill-time operator steps.
- `scripts/SCRIPTS.md`: entry at a third distinct anchor so the two
  pending batches' entries and this one apply in any order.
- `tests/test_state_backup_restore.py` (new, 9 tests): round trip
  recovers exactly backup-time state with the mutated world preserved
  aside; consistency under a hammering concurrent writer
  (integrity_check clean, transactionally whole); verify detects tamper
  and missing files; restore refuses a tampered backup BEFORE touching the
  target; restore rejects manifest path traversal BEFORE touching the
  target; restore ignores unmanifested backup files; live-lock guard;
  non-empty-target --force guard; CLI end-to-end exit codes including the
  guard-blocked 2.

Verification:
- GitHub Actions `CI validate` before follow-up fix:
  - SHOWN: failed in `test_backup_is_consistent_under_active_writer`;
    snapshot verify reported `integrity_failed:state/live_trading.sqlite`
    under Linux CI writer concurrency.
- Follow-up fix:
  - SHOWN: source snapshots now open through a normal SQLite connection
    with `PRAGMA busy_timeout=5000`, and `_iter_state_files` excludes
    rollback-journal sidecars (`-journal`) alongside WAL sidecars.
- `python3 -m pytest -q tests/test_state_backup_restore.py`
  - CLAIMED by originating patch author before review packaging:
    `7 passed`.
- `./.venv/bin/python -m pytest -q tests/test_state_backup_restore.py`
  - SHOWN in review branch after CI fix: `9 passed in 0.39s`.
- `./.venv/bin/python -m py_compile scripts/backup_state.py tests/test_state_backup_restore.py`
  - SHOWN in review branch: passed with no output.
- `./.venv/bin/python scripts/validate_script_paths.py --strict`
  - SHOWN in review branch: `OK: script paths validated`.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN in review branch after CI fix: `"ok": true`, guard tests
    `23 passed`.
- `git diff --check`
  - SHOWN in review branch: passed with no output.
- Full local suite was not rerun in this review branch per operator time
  constraints; use GitHub CI as the broad-suite proof.

Remaining risk:
- New files plus doc edits only; no production code paths changed. The
  drill execution on the Hetzner host, explicit runtime/config/snapshot
  family inclusion or exclusion, evidence filing, and the backup-artifact
  secrets scan are operator follow-through.
- Independent human review and GitHub CI required before landing.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-10T17:02:00Z - Config Fail-Closed Sweep: Risk-Gate/Router Slice (Substrate Backlog #2)

Active role: ENGINEER

Objective:
- Continue the fail-closed trading-config sweep on surfaces independent of
  the pending backup/dead-man branches: order-router retry knobs,
  market-quality thresholds, live-arming cap parsing, and the atomic risk
  claim enforcement layer.

What was found:
- SHOWN: `market_quality_guard.check` compared `age_sec` and
  `spread_bps` against config thresholds after permissive float parsing;
  NaN/inf thresholds make the comparisons silently false. Base
  non-numeric thresholds could also crash before the guard returned.
- SHOWN: per-symbol market-quality overrides still coerced with `float()`
  before validation; targeted test initially failed on that path and the
  fix moved coercion behind the shared fail-closed threshold validation.
- SHOWN: `order_router._cfg()` parsed retry knobs with raw `int()` and
  `float()`, allowing non-finite delay values or config-load crashes.
- SHOWN: `live_arming._float_value()` returned NaN/inf candidates instead
  of skipping to the next/default cap.
- SHOWN: `atomic_risk_claim()` enforced cap<=0 as no-cap; NaN/inf caps or
  poisoned stored accumulators could disable comparisons.

What changed:
- `services/risk/market_quality_guard.py`: base and per-symbol
  `max_tick_age_sec` / `max_spread_bps` now validate after final threshold
  selection; non-numeric, non-finite, or non-positive values return
  `invalid_threshold:<name>`.
- `services/execution/order_router.py`: `_bounded_float` and
  `_bounded_int` helpers bound retry config: max retries 0..10, base delay
  0.05..60s, max delay 0.05..300s; garbage/non-finite values fall back to
  defaults.
- `services/execution/live_arming.py`: `_float_value` skips non-finite
  values and falls through to the next/default candidate.
- `storage/live_intent_queue_sqlite.py`: `atomic_risk_claim` now rejects
  non-finite caps (`risk:invalid_cap`), non-finite or negative estimates
  (`risk:invalid_notional_est`), and corrupt stored counters
  (`risk:corrupt_state`); cap<=0 no-cap behavior remains unchanged.
- `tests/test_config_fail_closed_sweep.py` added 11 regression tests for
  the changed contracts.

Filed, not fixed:
- `risk_daily.snapshot` may still pass non-finite store fields to
  downstream gates; ingestion is best-effort-never-raise, so the read side
  needs a corrupt marker that consumers honor.

Verification:
- `./.venv/bin/python -m py_compile services/risk/market_quality_guard.py services/execution/order_router.py services/execution/live_arming.py storage/live_intent_queue_sqlite.py tests/test_config_fail_closed_sweep.py`
  - SHOWN: passed with no output.
- `./.venv/bin/python -m pytest -q tests/test_config_fail_closed_sweep.py`
  - SHOWN: first run failed on invalid per-symbol override, then passed
    after moving override coercion behind shared validation:
    `11 passed in 0.45s`.
- 40 nearby test files importing or exercising the touched surfaces:
  - SHOWN: `282 passed, 7 warnings in 6.48s`.

Remaining risk:
- HIGH: changes live risk enforcement and market-quality failure modes;
  independent human review and GitHub CI required before merge.
- Policy values are review decisions: retry clamp bounds 0..10,
  0.05..60s, and 0.05..300s.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
## 2026-07-10T20:53:00Z - Paper/Gate Event Alerting, First Slice (Active Backlog #23)

Active role: ENGINEER

Objective:
- Apply the first notification-only paper/gate event alerting slice so
  evidence-writer health transitions and promotion-gate flips can wake the
  operator instead of relying only on manual polling.

What was found:
- SHOWN: Active backlog item #23 asks for paper/gate event alerting, with
  evidence-write failure thresholds and gate-ready transitions included in
  the first read-only/notification-only implementation target.
- SHOWN: substrate backlog item #9 previously deferred any future
  alert-dispatch hook to the paper/gate event alerting item.
- SHOWN: the incoming patch applied cleanly to current `review-stabilized`
  except for the work-log tail because #244 had advanced the branch. The
  functional hunks were applied unchanged; this entry was appended at the
  current tail.
- SHOWN: the incoming module/test docstrings referred to "Active backlog
  #19"; the actual backlog item is #23, so both docstrings were corrected.

What changed:
- `services/alerts/paper_gate_events.py` (new): best-effort
  notification-only helpers for evidence-writer status transitions and
  promotion-gate flip snapshots. The gate snapshot is written to
  `runtime/health/promotion_gates.last.json`, first run is a silent
  baseline, and alert dispatch errors are swallowed so snapshots still
  advance.
- `services/strategies/evidence_logger.py`: evidence-writer success and
  failure recorders now capture the prior status, persist the new status,
  then call the transition alert hook inside a never-raise wrapper.
- `scripts/check_promotion_gates.py`: adds `--alert`; gate results and
  exit-code behavior are unchanged, and snapshot persistence runs
  best-effort outside the gate decision.
- `tests/test_paper_gate_event_alerts.py` (new): pins transition
  deduplication, severity levels, evidence-writer end-to-end behavior,
  gate baseline/flip/recovery behavior, corrupt snapshot recovery, and
  never-raise alert handling.
- `REMAINING_TASKS.md`: records this as the first Active #23 slice and
  marks substrate #9's alert-dispatch hook as implemented by this item.

Why this change was chosen:
- It is the smallest operator-visible alerting slice: notification-only,
  opt-in for promotion-gate alerts, no trading decisions, no gate
  pass/fail changes, and no evidence-write control-flow dependency on
  the alert stack.

Expected outcome:
- Evidence-writer degradation/refusal/recovery and promotion-gate flips
  become visible through the existing alert dispatcher without changing
  trading, evidence, or promotion decisions.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_gate_event_alerts.py`
  - SHOWN: `8 passed in 0.11s`.
- `./.venv/bin/python -m py_compile services/alerts/paper_gate_events.py services/strategies/evidence_logger.py scripts/check_promotion_gates.py tests/test_paper_gate_event_alerts.py`
  - SHOWN: passed with no output.
- `./.venv/bin/python -m pytest -q tests/test_paper_gate_event_alerts.py tests/test_evidence_logger.py tests/test_check_promotion_gates.py tests/test_alert_dispatcher_fallback.py`
  - SHOWN: `77 passed in 1.66s`.
- `./.venv/bin/python scripts/validate_script_paths.py --strict`
  - SHOWN: `OK: script paths validated`.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `"ok": true`, guard tests `23 passed`.
- `./.venv/bin/python scripts/check_promotion_gates.py --help`
  - SHOWN: help lists `--alert`.
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python -m ruff check ...`
  - SHOWN: not run successfully because this local venv has no `ruff`
    module installed. Use GitHub CI as the lint proof.
- Full local suite not run in this branch per operator time constraint;
  use GitHub CI as the broad-suite proof.

Remaining risk:
- HIGH by repo rule because this touches gate/evidence surfaces, even
  though the implementation is notification-only and wrapped never-raise.
- Remaining Active #23 event families are still open: qualified
  round-trip changes, campaign stop/failure, and strategy decision
  changes.
- Independent human review and GitHub CI required before landing.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-10T21:58:00Z - Risk Daily Corrupt Snapshot Marker (Substrate Backlog #2 Follow-up)

Active role: ENGINEER

Objective:
- Close the filed-but-not-fixed `risk_daily.snapshot` read-side gap from
  the config fail-closed sweep: non-finite or unparseable stored risk
  fields must not silently become safe defaults in downstream gates.

What was found:
- SHOWN: `risk_daily.snapshot()` converted `trades`, `realized_pnl_usd`,
  `fees_usd`, and `notional_usd` directly into numeric fields without a
  corruption marker. A stored `nan` could make downstream comparisons
  silently false if consumers converted it without checking.
- SHOWN: direct live order fail-closed logic in `place_order` consumes
  `risk_daily.snapshot()` and compares `trades`, `pnl`, and `notional`.
- SHOWN: ops telemetry consumes the same snapshot and feeds the ops risk
  gate through `RawSignalSnapshot.extra`.
- SHOWN: `_executor_submit` uses `RiskDailyDB.realized_today_usd()` rather
  than `snapshot()`, so that read path also needed fail-closed handling.

What changed:
- `services/risk/risk_daily.py`: `snapshot()` now returns additive fields
  `risk_daily_corrupt`, `risk_daily_corrupt_fields`, and
  `risk_daily_corrupt_reason` when stored numeric fields are unparseable,
  non-finite, or invalid. Numeric fields remain present for compatibility,
  but the marker is authoritative for consumers. `realized_today_usd()`
  now raises `ValueError("risk_daily_corrupt:...")` when the snapshot is
  corrupt, causing live submit paths to fail closed instead of comparing
  against NaN.
- `services/execution/place_order.py`: blocks directly with
  `CBP_ORDER_BLOCKED:risk_daily_corrupt` before evaluating daily trade,
  PnL, or notional limits.
- `services/ops/telemetry_snapshot_builder.py`: carries the corrupt marker
  and field list into `RawSignalSnapshot.extra`.
- `services/ops/risk_gate_engine.py`: classifies a corrupt risk-daily
  marker as `FULL_STOP`, with `risk_daily_corrupt` hazard/reason and a
  high stress score.
- Tests pin corrupt snapshot marking, direct order blocking,
  `realized_today_usd()` fail-closed behavior, telemetry propagation, and
  ops risk-gate `FULL_STOP` classification.

Why this change was chosen:
- This is the narrowest read-side fix: ingestion remains best-effort and
  existing numeric keys remain backward-compatible, while critical
  consumers honor an explicit corruption marker in the fail-closed
  direction.

Expected outcome:
- A poisoned `risk_daily` row can no longer make live order and ops risk
  gates treat unknown risk state as safe.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_risk_daily_atomic.py tests/test_place_order_fail_closed.py tests/test_ops_risk_gate_engine.py tests/test_ops_signal_adapter_service.py tests/test_live_executor_latency_safety_integration.py`
  - SHOWN: `54 passed in 1.09s`.
- `./.venv/bin/python -m py_compile services/risk/risk_daily.py services/execution/place_order.py services/ops/telemetry_snapshot_builder.py services/ops/risk_gate_engine.py tests/test_risk_daily_atomic.py tests/test_place_order_fail_closed.py tests/test_ops_risk_gate_engine.py tests/test_ops_signal_adapter_service.py tests/test_live_executor_latency_safety_integration.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.
- Full local suite not run in this branch per operator time constraint;
  use GitHub CI as the broad-suite proof.

Remaining risk:
- HIGH: changes live risk/read-side gate semantics and order-blocking
  behavior for corrupt risk state. Independent human review and GitHub CI
  required before landing.
- Remaining substrate #2 sweep is still open for other live executor,
  consumer/reconciler config reads, and admin live controls.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-10T22:35:13Z - Qualified Round-Trip Change Alerts (Active Backlog #23 Slice)

Active role: ENGINEER

Objective:
- Continue paper/gate event alerting with the smallest notification-only
  slice still open under Active backlog #23: alert when the machine-gate
  qualified paper round-trip count changes.

What was found:
- SHOWN: `evaluate_paper_gates()` already computes the qualified
  `round_trips` from `paper_history`, but `run_check()` exposed that count
  only through the human-readable gate detail string.
- SHOWN: `services/alerts/paper_gate_events.py` already persists a
  first-run silent baseline for gate pass/fail flips in
  `runtime/health/promotion_gates.last.json`, making it the correct
  single snapshot for this notification family.

What changed:
- `scripts/check_promotion_gates.py`: adds an additive paper-stage
  `paper_progress` object to the JSON result. It contains the structured
  qualified round-trip count used by the machine gate:
  `round_trips_recorded`, `round_trips_required`,
  `round_trips_remaining`, `round_trips_ready`, source, and diagnostic
  all-history round-trip count. Gate pass/fail logic, printed report, and
  exit codes are unchanged.
- `services/alerts/paper_gate_events.py`: persists `paper_progress` in the
  existing promotion-gate snapshot and, when `--alert` is used, dispatches
  `paper_gate:qualified_round_trips_changed` exactly once per count change.
  Count increases alert at `info`; count decreases alert at `warning`
  because they usually mean requalification/provenance recalculation
  invalidated previously counted history. First run remains a silent
  baseline. Alert dispatch remains best-effort and never freezes snapshot
  advancement.
- `tests/test_paper_gate_event_alerts.py`: pins baseline behavior,
  increase alert, decrease warning, steady-state dedupe, and snapshot
  advancement when the alert channel raises.
- `tests/test_check_promotion_gates.py`: pins the new source-level
  `paper_progress` contract for both zero qualified trips with diagnostic
  all-history and one qualified round trip.
- `REMAINING_TASKS.md`: records this as the second Active #23
  notification-only slice and leaves campaign stop/failure and strategy
  decision alerts open.

Why this change was chosen:
- The alert must follow the same structured value the machine gate uses,
  not parse display text or use a separate dashboard progress service.
  Keeping this as an additive JSON field avoids changing existing gate
  behavior while making the operator wake-up condition machine-readable.

Expected outcome:
- Operators running `scripts/check_promotion_gates.py --alert` receive a
  notification when qualified paper round-trip progress moves, including
  regressions caused by stricter provenance qualification. Manual polling is
  still possible, but the count-change event no longer depends on the
  operator noticing the gate output.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_paper_gate_event_alerts.py tests/test_check_promotion_gates.py`
  - SHOWN: `56 passed in 0.95s`.
- `./.venv/bin/python -m py_compile services/alerts/paper_gate_events.py scripts/check_promotion_gates.py tests/test_paper_gate_event_alerts.py tests/test_check_promotion_gates.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- HIGH: touches promotion-gate JSON and operator alerting. Notification-only
  code must still receive independent human review and GitHub CI before
  landing.
- Full suite not run locally per operator time rule; use GitHub CI as broad
  proof.
- Remaining Active #23 event families: campaign stop/failure and strategy
  decision changes.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.

## 2026-07-11T02:13:35Z - Campaign Stop/Failure Alerts (Active Backlog #23 Batch A)

Active role: ENGINEER

Objective:
- Add the campaign stop/failure half of the remaining Active #23 alert lane
  without mixing in strategy-decision or deployment-stage transition alerts.
- Fold candidate-advisor backlog hygiene into the same docs touch because
  that classification was already accepted and no longer belongs in active
  remaining wording.

What was found:
- SHOWN: `services.analytics.paper_strategy_evidence_service._write_status()`
  is the single campaign status chokepoint and already reads
  `current_status` before validating and writing the new status. That makes
  it the correct seam for campaign status transition alerting.
- SHOWN: `services.alerts.paper_gate_events` establishes the local alerting
  pattern to match: notification-only, first observation silent baseline,
  alert once per transition, never raise, and do not affect gate/evidence
  decisions.
- SHOWN: candidate-advisor classification is already implemented and
  accepted via `ADVISOR_EXCLUDED_STRATEGIES` plus the registry coverage test,
  so the active backlog wording was stale.

What changed:
- `services/alerts/campaign_events.py`: new notification-only alerter for
  campaign status transitions. It alerts only on transitions into
  stop/failure terminal states: `failed`/`error`/`aborted` are critical,
  `stopped` is warning, and normal `completed` is intentionally silent.
  First observation remains a silent baseline, repeated same-status writes
  do not re-alert, and the entry point never raises.
- `services/analytics/paper_strategy_evidence_service.py`: `_write_status()`
  invokes the alerter after the status file write succeeds, using the
  already-read previous status. Alert failures are swallowed so campaign
  status advancement cannot be blocked by notification delivery.
- `tests/test_campaign_event_alerts.py`: pins transition semantics,
  severity, baseline, no-alert cases, payload forwarding, and never-raise
  behavior.
- `tests/test_campaign_event_alerts_integration.py`: proves the real
  `_write_status()` path alerts on `running -> stopped` and that a raising
  alert channel does not block a `failed` status write.
- `REMAINING_TASKS.md`: reclassifies candidate-advisor coverage as done and
  records campaign stop/failure alerting as Batch A; strategy decision-change
  alerts remain open as Batch B.

Why this change was chosen:
- Campaign status transitions have a distinct detection seam from strategy
  decision changes and deployment-stage transitions. Keeping this batch to
  one seam avoids a cross-subsystem patch while still improving operator
  wake-up quality.

Expected outcome:
- Operators receive an alert when a governed paper evidence campaign stops
  or fails abnormally, without changing campaign status persistence,
  evidence generation, trading behavior, or promotion-gate results.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_campaign_event_alerts.py tests/test_campaign_event_alerts_integration.py`
  - SHOWN: `12 passed in 0.25s`.
- `./.venv/bin/python -m pytest -q tests/test_paper_strategy_evidence_service.py tests/test_campaign_event_alerts.py tests/test_campaign_event_alerts_integration.py`
  - SHOWN: `39 passed in 0.43s`.
- `./.venv/bin/python -m py_compile services/alerts/campaign_events.py services/analytics/paper_strategy_evidence_service.py tests/test_campaign_event_alerts.py tests/test_campaign_event_alerts_integration.py`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `"ok": true`, guard tests `23 passed`.
- `git diff --check`
  - SHOWN: passed with no output.

Remaining risk:
- HIGH: touches operator alerting and campaign status workflow. The change is
  notification-only and ordered after status persistence.
- Strategy decision-change alerts remain open as Active #23 Batch B.
- Deployment-stage transition alerts are a separate surface and are not part
  of this batch.
- Acceptance state: `ACCEPTED` by human operator review on 2026-07-10 after
  targeted proof was shown.

## 2026-07-11T02:27:48Z - Strategy Decision-Change Alerts (Active Backlog #23 Batch B)

Active role: ENGINEER

Objective:
- Add the remaining Active #23 strategy decision-change alert lane without
  mixing in deployment-stage transition alerts or changing promotion-gate
  decisions.

What was found:
- SHOWN: `services.backtest.evidence_cycle.persist_strategy_evidence()`
  is the active persistence entry point used by
  `scripts/data/run_strategy_evidence_cycle.py` and
  `services.analytics.paper_strategy_evidence_service`.
- SHOWN: `persist_strategy_evidence()` already builds a `comparison` object
  from the previous latest strategy evidence artifact before writing the new
  latest/history JSON files. That comparison includes per-strategy
  `decision_changed`, previous/current decisions, top-strategy change state,
  and previous/current `as_of` values.
- SHOWN: `services/backtest/evidence_persist.py` duplicates similar
  persistence logic but has no active callers in the current grep results, so
  widening it would broaden a dormant surface rather than improve the active
  operator path.

What changed:
- `services/alerts/strategy_decision_events.py`: new notification-only
  alerter for persisted strategy decision changes. First persisted evidence
  remains a silent baseline, rank/score-only movement does not alert,
  new/improved decisions alert at info level, degraded decisions alert at
  warning level, and retire decisions alert at critical level. The entry
  point never raises.
- `services/backtest/evidence_cycle.py`: `persist_strategy_evidence()`
  invokes the alerter after latest/history JSON artifacts are written.
  Alert failures are swallowed so strategy evidence persistence cannot be
  blocked by notification delivery.
- `tests/test_strategy_decision_event_alerts.py`: pins alert semantics and
  the real persistence path, including the proof that a raising alert channel
  still leaves the latest evidence artifact advanced.
- `REMAINING_TASKS.md`: records Active #23 Batch B and the explicit
  `evidence_persist.py` dormant-surface boundary.

Why this change was chosen:
- The existing comparison object already defines the exact decision delta the
  operator cares about. Reusing it keeps the alert read-only and avoids a
  second snapshot or decision-comparison implementation.

Expected outcome:
- Operators receive one alert when persisted strategy decisions change versus
  the previous latest evidence artifact, without changing strategy ranking,
  evidence persistence, decision-record rendering, trading behavior, or
  promotion-gate results.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_strategy_decision_event_alerts.py`
  - SHOWN: `8 passed in 0.19s`.
- `./.venv/bin/python -m pytest -q tests/test_backtest_evidence_cycle.py tests/test_strategy_decision_event_alerts.py`
  - SHOWN: `24 passed in 4.98s`.
- `./.venv/bin/python -m py_compile services/alerts/strategy_decision_events.py services/backtest/evidence_cycle.py tests/test_strategy_decision_event_alerts.py`
  - SHOWN: passed with no output.
- `LC_ALL=C rg -n "[^\\x00-\\x7F]" services/alerts/strategy_decision_events.py tests/test_strategy_decision_event_alerts.py`
  - SHOWN: no non-ASCII matches.

Remaining risk:
- HIGH: touches operator alerting and strategy decision workflow. The change
  is notification-only and ordered after evidence persistence.
- Deployment-stage transition alerts are a separate surface and are not part
  of this batch.
- Acceptance state: `ACCEPTED` by human operator review on 2026-07-10 after
  targeted proof was shown.

## 2026-07-11T02:38:54Z - Archive-First Backtesting Slice (Active Backlog #11)

Active role: ENGINEER

Objective:
- Make the existing `market_ohlcv` archive table usable by the shared
  backtest OHLCV fetch path before relying on strategy comparisons.

What was found:
- SHOWN: `storage/market_store_sqlite.py` already owns a `market_ohlcv`
  table and `upsert_ohlcv()` writer, but had no read API for backtests.
- SHOWN: `services.backtest.signal_replay.fetch_ohlcv()` was a single
  exchange fetch through ccxt and had no archive path or dataset hash.
- SHOWN: `services.market_data.ohlcv_fetcher` delegates to
  `signal_replay.fetch_ohlcv()`, so a narrow change there reaches existing
  backtest/market-data callers without creating a second fetcher.

What changed:
- `storage/market_store_sqlite.py`: added `MarketStore.load_ohlcv()` with
  latest-window and `since_ms` reads from `market_ohlcv`.
- `services/backtest/ohlcv_archive.py`: added archive path resolution
  (`CBP_MARKET_ARCHIVE_DB` or app data `market_raw.sqlite`), row
  normalization/deduplication, symbol-candidate lookup, complete-window
  archive loading, and deterministic dataset hashing.
- `services/backtest/signal_replay.py`: now tries a complete archive window
  first and falls back to the existing exchange fetch when the archive is
  missing or incomplete.
- `tests/test_ohlcv_archive_backtest.py`: added regression proof for archive
  reads, archive-first no-exchange behavior, incomplete-archive fallback, and
  dataset-hash determinism.
- `tests/test_signal_replay.py`: pinned the legacy exchange-delegation test to
  a missing archive path so local operator archives cannot make the test
  environment-sensitive.
- `REMAINING_TASKS.md`: recorded this as the first archive-first slice and
  left pagination/backfill, downstream hash persistence, and walk-forward
  sweeps open.

Why this change was chosen:
- It is the smallest path that converts already-collected OHLCV into
  reproducible backtest input without changing caller return types or removing
  the existing ccxt fallback.

Expected outcome:
- Backtests use archived OHLCV when enough rows exist for the requested window;
  repeated runs over the same archive rows have a stable dataset hash; partial
  archives do not silently shorten a backtest sample.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_ohlcv_archive_backtest.py tests/test_signal_replay.py tests/test_marketdata_ohlcv_fetcher.py`
  - SHOWN: `9 passed in 0.29s`.
- `./.venv/bin/python -m py_compile services/backtest/ohlcv_archive.py services/backtest/signal_replay.py storage/market_store_sqlite.py tests/test_ohlcv_archive_backtest.py tests/test_signal_replay.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `ok=true`.

Remaining risk:
- HIGH: this touches research/profitability measurement plumbing, not live
  trading, but incorrect archive selection could bias strategy comparisons.
- UNVERIFIED: paginated archive ingestion/backfill is still not reusable here.
- UNVERIFIED: downstream backtest artifacts do not yet persist the dataset
  hash emitted by `ohlcv_archive`.
- Acceptance state: `ACCEPTED` by human operator review on 2026-07-10 after
  targeted proof was shown.

## 2026-07-11T02:52:59Z - Strategy Evidence Dataset Metadata (Active Backlog #11)

Active role: ENGINEER

Objective:
- Persist dataset identity in downstream strategy-evidence artifacts so
  strategy comparisons can be tied back to the exact scored OHLCV windows.

What was found:
- SHOWN: `run_strategy_evidence_cycle()` built `window_reports` from candles
  but did not persist any dataset hash or source metadata for those windows.
- SHOWN: current default evidence windows are synthetic benchmark windows, so
  blindly labeling hashes as archive-backed would misrepresent the source.
- SHOWN: `persist_strategy_evidence()` writes the report payload as-is, so
  adding metadata at `run_strategy_evidence_cycle()` is sufficient to make it
  visible in both latest and history artifacts.

What changed:
- `services/backtest/ohlcv_archive.py`: `ohlcv_dataset_hash()` now accepts an
  explicit `source` while preserving the archive default.
- `services/backtest/evidence_cycle.py`: each evidence window now carries
  `dataset_hash` and a `dataset` metadata block with source, venue, timeframe,
  symbol, bars, and start/end timestamps. The top-level report includes a
  `dataset_summary` containing hashed-window count, source list, and hashes.
- `tests/test_ohlcv_archive_backtest.py`: proves hashes are source-sensitive.
- `tests/test_backtest_evidence_cycle.py`: proves strategy-evidence reports
  include dataset metadata and that the current default source is
  `synthetic_evidence_window`.
- `REMAINING_TASKS.md`: records this as the second archive-first slice and
  keeps reusable pagination/backfill and archive-backed sweeps open.

Why this change was chosen:
- It adds data-identity evidence without changing ranking inputs, decision
  policy, persistence shape beyond additive fields, or live trading paths.

Expected outcome:
- Operators and reviewers can see which exact OHLCV datasets were scored in a
  strategy-evidence artifact, preventing synthetic, archive, and future
  provided windows from being conflated.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_ohlcv_archive_backtest.py tests/test_backtest_evidence_cycle.py`
  - SHOWN: `21 passed in 5.11s`.
- `./.venv/bin/python -m py_compile services/backtest/evidence_cycle.py services/backtest/ohlcv_archive.py tests/test_backtest_evidence_cycle.py tests/test_ohlcv_archive_backtest.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `ok=true`.

Remaining risk:
- HIGH: still profitability-measurement plumbing. Additive metadata should not
  alter decisions, but reviewers should confirm no downstream consumer assumes
  a fixed evidence payload schema.
- UNVERIFIED: reusable paginated archive ingestion/backfill is still open.
- UNVERIFIED: archive-backed parameter sweep/walk-forward research is still
  open.
- Acceptance state: `ACCEPTED` by human operator review on 2026-07-10 after
  targeted proof was shown.

## 2026-07-11T08:16:18Z - Archive Pagination and Baseline Dataset Hash (Active Backlog #11)

Active role: ENGINEER

Objective:
- Finish the reusable archive pagination/backfill slice and make the ES
  daily-trend baseline artifact persist the exact-row dataset hash.

What was found:
- SHOWN: `signal_replay.fetch_ohlcv()` had archive-first behavior but returned
  only rows, discarding source and dataset-hash metadata.
- SHOWN: `scripts/research/run_es_daily_trend_backtest_baseline.py` still owned
  its own pagination loop, so the logic was not reusable outside that script.
- SHOWN: the ES baseline report wrote source/options/metrics but did not stamp
  a deterministic hash of the rows used for the run.

What changed:
- `services/backtest/signal_replay.py`: added `fetch_ohlcv_with_meta()` that
  returns rows plus source, dataset hash, venue, symbol, timeframe, count, and
  archive path/stored symbol when archive-backed. Existing `fetch_ohlcv()`
  remains a bare-rows wrapper.
- `services/backtest/ohlcv_archive.py`: added `paginate_ohlcv()` with bounded
  forward paging, max-pages/max-bars/until controls, and non-advancing-cursor
  termination; added `backfill_archive()` for idempotent upsert into
  `market_ohlcv`.
- `scripts/research/run_es_daily_trend_backtest_baseline.py`: switched
  `fetch_paginated_ohlcv()` to the shared paginator and added a `dataset`
  block with source label, venue, symbol/data symbol, timeframe, row count,
  first/last timestamps, and SHA-256/dataset hash.
- `tests/test_ohlcv_archive_pagination.py`: added offline tests for
  pagination, bounds, empty termination, idempotent backfill, archive loading,
  and metadata fetch.
- `tests/test_es_daily_trend_backtest_baseline_runner.py`: pins baseline report
  dataset metadata and output/printed hash consistency.
- `REMAINING_TASKS.md`: records the third archive-first slice and leaves only
  archive-backed parameter-sweep/walk-forward research open under item #11.

Why this change was chosen:
- It keeps existing row-only callers stable while exposing metadata to callers
  that need reproducibility, and it removes the one-off pagination loop from
  the baseline script by routing through a reusable archive primitive.

Expected outcome:
- Archive backfills can be run and re-run idempotently; archive-backed fetches
  can surface their dataset hash; ES baseline artifacts now identify the exact
  dataset used rather than relying on a label alone.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_ohlcv_archive_backtest.py tests/test_ohlcv_archive_pagination.py tests/test_signal_replay.py tests/test_marketdata_ohlcv_fetcher.py tests/test_es_daily_trend_backtest_baseline_runner.py tests/test_backtest_evidence_cycle.py`
  - SHOWN: `35 passed in 5.33s`.
- `./.venv/bin/python -m py_compile services/backtest/ohlcv_archive.py services/backtest/signal_replay.py scripts/research/run_es_daily_trend_backtest_baseline.py tests/test_ohlcv_archive_pagination.py tests/test_es_daily_trend_backtest_baseline_runner.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `ok=true`.

Remaining risk:
- HIGH: research/profitability measurement plumbing. It does not touch live
  trading, order routing, or promotion gates, but review should confirm the
  compatibility wrapper preserves existing row-only behavior.
- UNVERIFIED: archive-backed parameter-sweep/walk-forward research remains
  open.
- Acceptance state: `ACCEPTED` by human operator review on 2026-07-11 after
  targeted proof was shown.

## 2026-07-11T15:44:00Z - Archive-Backed Walk-Forward Artifact (Active Backlog #11)

Active role: ENGINEER

Objective:
- Add the safe half of archive-backed walk-forward research: one explicit
  strategy config, complete archive rows only, anchored walk-forward windows,
  and a reproducible JSON artifact stamped with dataset hashes. Exclude
  parameter sweeps, ranking policy, and strategy-selection decisions.

What was found:
- SHOWN: `run_anchored_walk_forward()` already produced anchored train/test
  windows from caller-provided candles, but it had no archive loader or dataset
  provenance contract.
- SHOWN: `ohlcv_archive.load_archived_ohlcv()` already returned complete
  archive rows plus `dataset_hash`, `archive_path`, stored symbol, venue,
  timeframe, and row counts.
- SHOWN: the previous archive-pagination slice made archive backfill reusable,
  so the remaining safe seam was a consumer wrapper and artifact writer, not a
  new backtest engine.

What changed:
- `services/backtest/walk_forward.py`: added
  `run_archive_backed_walk_forward()` and a config hash helper. The wrapper
  refuses missing/incomplete archives, never falls back to live OHLCV, runs the
  existing anchored walk-forward over complete archive rows, and stamps the
  result plus each window with the archive dataset hash/source.
- `scripts/research/run_archive_walk_forward.py`: added a research-only CLI
  that requires an explicit JSON/YAML `strategy.name` config and writes the
  archive-backed walk-forward JSON artifact. It supports archive DB selection,
  row limit/since, walk-forward sizing parameters, fee/slippage assumptions,
  and `--fail-if-not-ok`.
- `tests/test_backtest_walk_forward.py`: added archive-backed service tests
  for dataset-hash stamping and incomplete-archive refusal.
- `tests/test_archive_walk_forward_runner.py`: added CLI artifact tests for
  output/printed JSON consistency and missing-archive exit code behavior.
- `REMAINING_TASKS.md`: marks the prior pagination slice accepted and records
  this single-config artifact slice as ready for review, leaving only the
  separate parameter-sweep/ranking layer open under item #11.

Why this change was chosen:
- It keeps the work mechanical and provable: archive-backed reproducibility
  before any parameter-grid or ranking decisions that could create misleading
  research conclusions. Reusing the existing walk-forward engine avoids a twin
  research path.

Expected outcome:
- Operators can run one archived strategy config through multi-window
  walk-forward validation and keep a JSON artifact that proves the exact OHLCV
  archive dataset and config hash behind the result.

Verification:
- `./.venv/bin/python -m pytest -q tests/test_backtest_walk_forward.py tests/test_archive_walk_forward_runner.py tests/test_ohlcv_archive_backtest.py tests/test_ohlcv_archive_pagination.py`
  - SHOWN: `17 passed in 0.59s`.
- `./.venv/bin/python -m py_compile services/backtest/walk_forward.py scripts/research/run_archive_walk_forward.py tests/test_backtest_walk_forward.py tests/test_archive_walk_forward_runner.py`
  - SHOWN: passed with no output.
- `git diff --check`
  - SHOWN: passed with no output.
- `./.venv/bin/python scripts/check_repo_alignment.py --json`
  - SHOWN: `ok=true`.

Remaining risk:
- HIGH: financial strategy research infrastructure can affect future strategy
  selection even though this patch is read-only and does not touch live
  trading, order routing, or promotion gates.
- UNVERIFIED: full test suite and GitHub CI were not run in this session.
- UNVERIFIED: parameter-grid sweeps and ranking/selection policy remain a
  separate follow-up.
- Acceptance state: `READY_FOR_INDEPENDENT_REVIEW`.
