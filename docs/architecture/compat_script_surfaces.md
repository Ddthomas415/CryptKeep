# Compat Script Surfaces

Date: 2026-08-11

## Scope

This document classifies the tracked `scripts/compat/*.py` family. It is a
classification record only; it does not promote, retire, or change any runtime
entrypoint.

The current operator-facing control plane remains documented in
`docs/CURRENT_RUNTIME_TRUTH.md`, `docs/BOT_CONTROL.md`, and
`docs/PROCESS_CONTROL.md`.

## Finding

SHOWN from current source:

- `scripts/compat/` contains compatibility implementations and historical
  wrappers with mixed behavior.
- Some root scripts still delegate into `scripts/compat/` for backward
  compatibility.
- Presence under `scripts/compat/` does not make a script canonical operator
  control, campaign control, promotion authority, or live-execution authority.

## Classification

| Surface | Classification | Current role |
|---|---|---|
| `scripts/compat/_bootstrap.py` | `compat_bootstrap_helper` | Shared path bootstrap for compatibility scripts. |
| `scripts/compat/run_bot_runner.py` | `compat_implementation_backing_root_wrapper` | Backing implementation for `scripts/run_bot_runner.py`; not the canonical operator start/stop/status plane. |
| `scripts/compat/run_intent_consumer.py` | `retired_run_mode_with_stop_compat` | `run` refuses with `legacy_intent_consumer_retired`; `stop` remains a compatibility stop helper. |
| `scripts/compat/run_intent_executor.py` | `compat_implementation_use_safe_root_wrapper` | Backing implementation reached through safe wrapper paths; new operator use should prefer guarded root/live wrappers. |
| `scripts/compat/run_intent_reconciler.py` | `compat_implementation_use_safe_root_wrapper` | Backing implementation reached through safe wrapper paths; new operator use should prefer guarded root/live wrappers. |
| `scripts/compat/run_live_trader.py` | `compat_live_loop_shim_not_canonical` | Direct live-trader loop shim; not the canonical live launch or safety-proof surface. |
| `scripts/compat/run_meta_strategy_runner.py` | `compat_meta_runner_not_canonical` | Meta-strategy compatibility runner; not canonical paper promotion authority. |
| `scripts/compat/run_pipeline_loop.py` | `compat_pipeline_loop_managed_by_start_bot` | Pipeline loop used by managed startup paths; do not replace with a new parallel safe wrapper without a current reproduced gap. |
| `scripts/compat/run_pipeline_once.py` | `compat_pipeline_one_shot` | One-shot pipeline compatibility helper; not a canonical campaign proof command. |
| `scripts/compat/run_strategy_runner.py` | `legacy_strategy_runner_wrapper` | Historical strategy-runner wrapper retained for compatibility; canonical root script is `scripts/run_strategy_runner.py`. |
| `scripts/compat/service_ctl.py` | `compat_implementation_backing_root_wrapper` | Backing implementation for `scripts/service_ctl.py`. |
| `scripts/compat/start_supervisor.py` | `legacy_supervisor_pid_helper` | Legacy PID-file supervisor helper; not the canonical production deployment plan. |
| `scripts/compat/stop_supervisor.py` | `legacy_supervisor_pid_helper` | Legacy PID-file supervisor stop helper; not the canonical production deployment plan. |
| `scripts/compat/supervisor.py` | `legacy_supervisor_wrapper` | Compatibility wrapper for older supervisor calls. |
| `scripts/compat/supervisor_ctl.py` | `compat_supervisor_ctl` | Compatibility supervisor-control helper used by root/operator paths where documented. |
| `scripts/compat/watchdog.py` | `compat_watchdog_wrapper` | Compatibility wrapper around `services.process.watchdog`. |

## Rules

- New operator runbooks should use the canonical root commands documented in
  `docs/CURRENT_RUNTIME_TRUTH.md` and `scripts/SCRIPTS.md`.
- New work must not infer canonical authority from a `scripts/compat/` file
  name.
- If a compatibility script becomes canonical, update this document, the
  runtime-truth docs, and the executable guard in the same change.
- If a compatibility script is retired, keep the stable refusal or delegation
  contract pinned by tests before deleting historical behavior.

## Executable Guard

`tests/test_compat_script_surface_classification.py` pins that:

- every tracked `scripts/compat/*.py` file has a classification row;
- `scripts/compat/run_intent_consumer.py` remains explicitly retired for `run`;
- root docs link this classification record; and
- the document does not authorize campaigns, live trading, promotion-gate
  changes, or new broker/symbol support.
