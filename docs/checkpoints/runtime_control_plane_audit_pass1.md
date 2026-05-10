# Runtime Control Plane Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 1. Runtime Control Plane  
**Status:** IN PROGRESS

This pass covers the current supervised startup/stop/status control plane and
its operator-facing runtime truth surfaces.

## Scope

- startup orchestration
- stop behavior
- supervisor PID truth
- runtime-truth helper surfaces
- current paper-soak runtime alignment

## Evidence reviewed

- `scripts/start_bot.py`
- `scripts/stop_bot.py`
- `scripts/bot_status.py`
- `scripts/run_bot_runner.py`
- `services/runtime/process_supervisor.py`
- `services/process/bot_runtime_truth.py`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `tests/test_bot_orchestration_scripts.py`
- `tests/test_run_bot_runner.py`
- `tests/test_process_supervisor.py`
- `tests/test_bot_runtime_truth.py`
- live read-only status from:
  - `python scripts/bot_status.py`
  - `python scripts/report_supervised_soak_status.py --json`

## Checklist status

- [x] Canonical startup/stop/status path is documented and matches current code.
- [x] Process supervisor PID truth vs current paper runtime status-file truth is aligned.
- [x] One-shot converge vs hot-reload behavior is visible in source and tests.
- [~] Dead-process detection exists for PID files, but status-file freshness is not fully coherent across all service names.
- [~] Current docs correctly de-emphasize legacy startup paths, but one legacy status filename still leaks into canonical runtime-truth code.
- [ ] Lock-file behavior was not fully re-traced in this pass beyond the existing managed-loop surfaces already covered by targeted tests.

## SHOWN findings

### 1. Clean worktree import path is broken because `managed_symbol_config.py` is local-only, not tracked

**Severity:** Critical  
**Classification:** SHOWN

Evidence:

- the side audit worktree and the active soak checkout are both at commit
  `e4f26e7f6`.
- in the side worktree, `services/runtime/managed_symbol_config.py` is missing.
- in the active soak checkout, the same file exists locally but `git status
  --ignored` marks it as ignored:
  `!! services/runtime/managed_symbol_config.py`.
- current repo code imports that module from:
  - `scripts/run_pipeline_loop.py`
  - `scripts/run_pipeline_once.py`
  - `scripts/run_intent_executor.py`
  - `services/runtime/managed_symbol_selection.py`
- targeted control-plane verification from the clean side worktree fails during
  test collection with:
  `ModuleNotFoundError: No module named 'services.runtime.managed_symbol_config'`.

Impact:

- the current branch is not self-contained from a clean checkout/worktree.
- control-plane code and tests depend on a local-only ignored file.
- the active soak can appear healthy while the committed branch remains broken
  for fresh worktrees, CI, or other developers.

### 2. Canonical runtime-truth helper still points `intent_consumer` at a stale status filename

**Severity:** High  
**Classification:** SHOWN

Evidence:

- `services/process/bot_runtime_truth.py` maps `intent_consumer` to
  `runtime/flags/live_consumer.status.json`.
- `scripts/run_bot_runner.py` maps the managed `intent_consumer` service status
  path to `runtime/flags/live_intent_consumer.status.json`.
- `services/execution/live_intent_consumer.py` writes
  `runtime/flags/live_intent_consumer.status.json`.
- The active runtime contains both files:
  - `live_consumer.status.json` last updated `2026-05-07 08:35:57 -0400`
  - `live_intent_consumer.status.json` last updated `2026-05-10 10:39:14 -0400`

Impact:

- live-mode heartbeat or operator views that rely on
  `services/process/bot_runtime_truth.py` can read stale `intent_consumer`
  status even when the managed live consumer is writing a newer canonical file.
- this is a stale runtime-truth risk, not just a naming inconsistency.

### 3. No visible control-plane regression test covers the canonical `intent_consumer` status filename mapping

**Severity:** Medium  
**Classification:** SHOWN

Evidence:

- repo-wide test search shows `live_intent_consumer.status.json` coverage in
  live consumer tests.
- the same test search shows no visible test asserting that
  `services/process/bot_runtime_truth.py` reads the `intent_consumer` status
  from `live_intent_consumer.status.json`.

Impact:

- the stale filename mapping in Finding 2 was able to persist without direct
  coverage at the control-plane/runtime-truth layer.

## SHOWN strengths

- `scripts/start_bot.py` now converges to desired state instead of blindly
  starting services.
- `scripts/run_bot_runner.py` uses a deterministic symbol signature and no
  longer restarts symbol services on order-only changes.
- `services/runtime/process_supervisor.py` clears stale PID files on failed
  liveness checks.
- current paper runtime matches the expected paper topology:
  - `pipeline=True`
  - `executor=True`
  - `ops_signal_adapter=True`
  - `ops_risk_gate=True`
  - `ai_alert_monitor=True`
  - `intent_consumer=False`
  - `reconciler=False`

## UNVERIFIED points

- live-mode end-to-end operator truth was not exercised in this pass.
- no fresh live reconcile / live intent-consumer restart was performed.
- status-file freshness policy is not yet defined beyond current helper logic.

## Highest-leverage next action

Restore clean-checkout correctness first:

1. make `services/runtime/managed_symbol_config.py` part of tracked repo truth
   or remove the dependency on it
2. rerun the blocked control-plane test slice from a clean worktree
3. only then fix the stale `intent_consumer` status-path mapping in
   `services/process/bot_runtime_truth.py`
4. add a focused regression in `tests/test_bot_runtime_truth.py` proving the
   runtime-truth helper uses `live_intent_consumer.status.json`

## Handoff

- Active role: `AUDITOR`
- Acceptance state: `INCOMPLETE`
- Improvement from this pass:
  - confirmed the current paper control plane is coherent
  - exposed one stale-truth bug and one higher-priority clean-checkout blocker
- Proof required next:
  - tracked or replaced `managed_symbol_config.py`
  - clean-worktree control-plane test slice passes
  - code change for canonical live consumer status path
  - focused regression test for runtime-truth helper behavior
