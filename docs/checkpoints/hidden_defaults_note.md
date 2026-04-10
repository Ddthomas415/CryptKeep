# Hidden Defaults Note

Status: LANDED

## Objective
Record the remaining hidden defaults on runtime-capable repo surfaces after the canonical root-runtime launch path was tightened.

## Updated status
Recent landed cleanup:
- `scripts/run_pipeline_loop.py` now requires explicit:
  - `symbols[0]`
  - `pipeline.exchange_id`
  - `execution.executor_mode`
- `scripts/run_pipeline_once.py` now requires explicit:
  - `symbols[0]`
  - `pipeline.exchange_id`
  - `execution.executor_mode`
- commit landed:
  - `87cafb0` — `config: require explicit pipeline exchange, symbol, and mode`

The canonical operator/config path now requires explicit venue and symbol inputs in:
- `scripts/run_bot_safe.py`
- `scripts/bot_ctl.py`
- `services/execution/live_executor.py`

This closes the launch-path risk from silent defaults on the actively used operator path.
Hidden defaults may still remain in non-canonical or not-yet-classified paths.

Current classification from script review:
- `scripts/run_reconcile_safe_steps.py` still has venue/symbol defaults, but appears to be an admin/helper entrypoint
- `scripts/run_bot_runner.py` no longer silently defaults mode/venue/symbol and now fails closed on missing runtime config
- latest caller grep still only showed `tests/test_run_bot_runner.py`
- it remains non-canonical, but the hidden-default classification for that runner is now closed
- `scripts/run_tick_publisher.py` no longer treats legacy `config/trading.yaml` presence as the prerequisite truth and now accepts merged runtime config availability
- `scripts/run_intent_executor_safe.py` and `scripts/run_intent_reconciler_safe.py` no longer treat legacy `config/trading.yaml` presence as the prerequisite truth and now accept merged runtime config availability
- `services/setup/config_manager.py` still contains broad defaults (`coinbase`, `BTC/USD`, `paper`)
- current caller review places it primarily on setup/admin flows rather than the tightened canonical runtime path
- it remains classified rather than patched in the current pass



## Updated status
Recent landed cleanup:
- `services/pipeline/ema_strategy.py` no longer silently defaults:
  - `exchange_id` to `coinbase`
  - `symbol` to a venue-derived fallback
  - `mode` to `paper`
- commit landed:
  - `dbbf53d` — `config: remove silent runtime defaults from ema strategy cfg`

## Remaining classified defaults
The repo currently includes runtime-capable defaults such as:

- default venue: `coinbase`
- default symbol: `BTC/USD`

These now appear primarily on non-canonical or setup/admin-oriented paths rather than the chosen root-runtime launch path.

## Current repo truth
For the chosen supported root-runtime path, launch selections are explicit in:

- `scripts/run_bot_safe.py`
- `scripts/bot_ctl.py`
- `services/execution/live_executor.py`

Remaining defaults are classified as:
- non-canonical helper/admin flows
- setup/config convenience surfaces
- companion/runtime-adjacent paths not currently frozen as the supported launch path

## Landed close condition
The chosen launch path now has explicit:

1. venue
2. symbol(s)
3. mode
4. account / credentials source

Defaults retained for local/dev convenience remain fenced outside the supported launch path by scope documentation rather than treated as launch blockers.

## Risk
High if runtime behavior changes

## Review lane
Closed by documentation and scope narrowing; behavior changes would require independent review
