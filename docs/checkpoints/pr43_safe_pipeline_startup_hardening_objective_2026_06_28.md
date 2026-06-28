# PR #43 Safe Pipeline / Startup Hardening Objective - 2026-06-28

Status: ACCEPTED

Implementation proof status: READY_FOR_INDEPENDENT_REVIEW

Active role: DIRECTOR

## Purpose

Convert the remaining PR #43 safe-runtime-wrapper and startup-topology rebuild
group into one current-master objective.

This checkpoint does not implement a new wrapper, change startup behavior, or
revive stale PR #43 source. It defines the only defensible next boundary after
comparing the old `run_pipeline_safe.py` idea against the accepted current
canonical startup path and existing safe wrappers.

## Evidence

SHOWN:
- `docs/checkpoints/pr43_operator_observability_disposition_2026_06_19.md`
  groups these old PR #43 commits under safe runtime wrappers and bot topology:
  `db032231`, `4ee1f81c`, `46549f9d`, `a2be80f6`, `32b327fa`,
  `287fd125`, `45430d04`, `ef71b8b1`, and `626bdd82`.
- `docs/checkpoints/pr43_rebuild_followup_status_2026_06_24.md` keeps safe
  pipeline wrapper/startup hardening open only if current process-supervisor
  and bot-runtime truth surfaces still leave a reproduced startup or
  fail-closed gap.
- Current source does not contain `scripts/run_pipeline_safe.py`.
- Current source already contains canonical operator control scripts:
  - `scripts/start_bot.py`
  - `scripts/stop_bot.py`
  - `scripts/bot_status.py`
- Current docs identify the canonical startup/control plane:
  - `docs/CURRENT_RUNTIME_TRUTH.md`
  - `docs/PROCESS_CONTROL.md`
  - `docs/BOT_CONTROL.md`
- Current source already contains existing safe wrappers:
  - `scripts/run_intent_consumer_safe.py`
  - `scripts/run_intent_executor_safe.py`
  - `scripts/run_intent_reconciler_safe.py`
  - `scripts/run_live_reconciler_safe.py`
  - `scripts/run_ws_ticker_feed_safe.py`
  - `scripts/run_bot_safe.py`
- `scripts/start_bot.py` currently starts:
  - `pipeline` through `scripts/compat/run_pipeline_loop.py`
  - `executor` through `scripts/run_intent_executor_safe.py`
  - `intent_consumer` through `scripts/run_intent_consumer_safe.py run`
  - `ops_signal_adapter` through `scripts/run_ops_signal_adapter.py run`
  - `ops_risk_gate` through `scripts/run_ops_risk_gate_service.py run`
  - optional `reconciler` through `scripts/run_live_reconciler_safe.py run`
- Tests already cover pieces of the current startup topology and wrappers:
  - `tests/test_bot_orchestration_scripts.py`
  - `tests/test_canonical_execution_safe_wrappers.py`
  - `tests/test_run_ws_ticker_feed_safe.py`
  - `tests/test_service_ctl_smoke.py`
  - `tests/test_run_bot_runner.py`
- `docs/STARTUP_STATUS_GATE.md` records that `startup_status.json` is
  reconciliation evidence, not a currently shown canonical launch gate.

UNVERIFIED:
- Whether `scripts/compat/run_pipeline_loop.py` needs a dedicated safe wrapper
  on the current canonical path.
- Whether the current startup topology has a reproduced fail-open or
  fail-closed gap not already covered by existing safe wrappers and tests.
- Whether startup-status freshness should become an active launch gate.
- Whether adding another wrapper would simplify or obscure the current
  canonical operator path.

## Decision

Do not rebuild `scripts/run_pipeline_safe.py` merely because the old PR #43
branch had it.

The current repo already has a canonical startup path and several safe wrappers.
Before implementation, the next task must reproduce and document a
current-master startup/fail-closed gap. If no gap reproduces, the correct
outcome is to close the rebuild candidate as superseded by current startup
truth and tests.

The first implementation objective, if pursued, is a read-only startup topology
and gap audit:

- read current canonical startup scripts
- read process-supervisor service definitions/status surfaces
- read existing safe-wrapper behavior and tests
- verify whether `pipeline` has weaker failure semantics than adjacent services
- report one of:
  - `gap_reproduced`
  - `gap_not_reproduced`
  - `insufficient_evidence`
- write an artifact only

Only a follow-up high-risk implementation PR may add or change runtime startup
behavior.

## Scoped Objective

Build a read-only startup hardening audit report that answers:

- What is the current canonical startup topology?
- Which service commands are wrapped by safe wrappers?
- Which service commands are not wrapped, and why?
- Which current tests prove safe-idle, fail-closed, or status behavior?
- Is there a reproduced current-master gap that justifies a new wrapper or
  startup-topology change?
- What exact follow-up implementation would be required if a gap is reproduced?

## Required Boundaries

MUST NOT:
- start or stop services
- call `scripts/start_bot.py`
- call `scripts/stop_bot.py`
- mutate process-supervisor state
- create or delete pid files
- edit startup scripts or service definitions
- enable live execution
- route orders, enqueue orders, or touch live execution
- change startup-status gate behavior
- rely on stale PR #43 source files or compiled cache artifacts

MUST:
- be read-only by default
- consume current-master source/docs/tests only
- write any output under a dedicated audit artifact path
- classify every claim as shown, unverified, or not reproduced
- identify whether `pipeline` is the only unwrapped canonical service
- include proof that existing wrappers and tests were considered
- require separate high-risk review before any runtime behavior change

## Smallest Implementation Path

1. Add a service such as `services/runtime/startup_hardening_audit.py`.
2. Add a root command such as `scripts/audit_startup_hardening.py`.
3. Read and summarize:
   - `scripts/start_bot.py`
   - `scripts/stop_bot.py`
   - `scripts/bot_status.py`
   - `services/runtime/process_supervisor.py`
   - `scripts/compat/run_pipeline_loop.py`
   - current safe wrappers
   - startup/topology tests
4. Write latest and dated JSON/Markdown audit artifacts.
5. Do not add or alter wrappers in the same PR.

## Proof Required

Before implementation can be accepted:

- A root CLI command runs without network access.
- Tests prove:
  - no service start command is invoked
  - no service stop command is invoked
  - no pid/status files are written
  - canonical service commands are parsed from current source or declared
    fixtures
  - existing safe wrappers are recognized
  - `scripts/compat/run_pipeline_loop.py` is classified explicitly
  - output contains `gap_reproduced`, `gap_not_reproduced`, or
    `insufficient_evidence`
- `scripts/SCRIPTS.md`, `docs/CURRENT_RUNTIME_TRUTH.md` if affected, and
  `REMAINING_TASKS.md` describe the report as read-only.

## Out Of Scope

- creating `scripts/run_pipeline_safe.py`
- changing `scripts/start_bot.py`
- changing `services/runtime/process_supervisor.py`
- changing startup-status gate behavior
- changing live execution, routing, or order submission
- starting any process
- stopping any process
- automatic recovery or restart behavior

## Risk

HIGH for later implementation:
- Startup topology and safe-wrapper behavior affect background jobs, runtime
  supervision, fail-closed behavior, live-adjacent service ownership, and
  operator recovery.

LOW for this checkpoint:
- This is planning-only. It does not modify runtime behavior, background jobs,
  startup scripts, service definitions, gates, live execution, or order
  routing.

Acceptance state: ACCEPTED

## Implementation Proof - 2026-06-28

SHOWN:
- `services/runtime/startup_hardening_audit.py` builds a read-only startup
  hardening report from current repo source.
- `scripts/audit_startup_hardening.py` exposes the report through a root CLI.
- The implementation reads canonical startup scripts, existing safe wrappers,
  `scripts/compat/run_pipeline_loop.py`, startup-related tests, and the
  startup-status gate documentation.
- Initial proof output identifies three unwrapped canonical service commands:
  `pipeline`, `ops_signal_adapter`, and `ops_risk_gate`.
- The implementation writes latest and dated JSON/Markdown artifacts under
  the runtime startup-audit directory only.
- Tests cover the current topology, unwrapped command classification, existing
  safe wrappers, the static pipeline pre-status-exit condition, `--json
  --no-write`, default artifact writing, and the no-pid/status-file boundary.

Changed artifacts:
- `services/runtime/startup_hardening_audit.py`
- `scripts/audit_startup_hardening.py`
- `tests/test_startup_hardening_audit.py`
- `tests/test_audit_startup_hardening_script.py`
- `scripts/SCRIPTS.md`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `REMAINING_TASKS.md`
- `docs/work_log/review_stabilized_work_log.md`

Expected outcome:
- Operators get a repeatable report that answers whether current startup
  topology has an identified hardening gap before any wrapper or service
  topology change is proposed.
- The audit can report `insufficient_evidence`, `gap_not_reproduced`, or a
  future reproduced gap without changing runtime behavior.

Verification:
- `./.venv/bin/python -m py_compile services/runtime/startup_hardening_audit.py scripts/audit_startup_hardening.py tests/test_startup_hardening_audit.py tests/test_audit_startup_hardening_script.py`
  - SHOWN: passed.
- `./.venv/bin/python scripts/audit_startup_hardening.py --no-write`
  - SHOWN: exited 0 and printed `gap_status=insufficient_evidence`,
    `read_only=True`, and the two warning action items.
- `CBP_STATE_DIR=/private/tmp/cbp-startup-audit-proof ./.venv/bin/python scripts/audit_startup_hardening.py --json`
  - SHOWN: exited 0 and wrote startup-audit JSON/Markdown artifacts under the
    isolated runtime directory.
- `./.venv/bin/python -m pytest -q tests/test_startup_hardening_audit.py tests/test_audit_startup_hardening_script.py`
  - SHOWN: `5 passed in 0.43s`.
- `git diff --check`
  - SHOWN: passed.

Remaining risk:
- HIGH: startup topology, fail-closed behavior, background jobs, and
  live-adjacent service ownership remain high-risk surfaces. This proof does
  not change them and must remain at `READY_FOR_INDEPENDENT_REVIEW` until a
  separate reviewer or human accepts it.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW
