"""services/strategy_runner/ema_crossover_runner.py — public API facade.

Implementation lives in:
  _runner_shared.py   — config helpers, lock/status, strategy block builders
  _runner_signal.py   — signal helpers, OHLCV fetch, _strategy_signal
  _runner_loop.py     — run_forever (the main loop)

All names accessed by tests and scripts are re-exported here so that
  import services.strategy_runner.ema_crossover_runner as runner
continues to work without changes anywhere.
"""
from __future__ import annotations

# Module-level re-export so tests can do `runner.time.sleep` and
# `monkeypatch.setattr(runner.time, ...)`.
import time  # noqa: F401

from services.strategy_runner._runner_shared import (  # noqa: F401
    # Public entrypoints
    request_stop,
    _cfg,
    _no_fresh_tick_note,
    # Module-level constants (patched by tests)
    STATUS_FILE,
    STOP_FILE,
    TICK_SNAPSHOT_FILE,
    # Names re-exported so monkeypatch.setattr(runner, "X", ...) works
    load_user_yaml,
    make_exchange,
    get_best_bid_ask_last,
    IntentQueueSQLite,
    PaperTradingSQLite,
    StrategyStateSQLite,
)
from services.strategy_runner._runner_signal import (  # noqa: F401
    _strategy_signal,
    _fetch_mid,
    _fetch_public_ohlcv,
)
from services.strategy_runner._runner_loop import (  # noqa: F401
    run_forever,
    # Re-exported so tests can monkeypatch it on the runner module
    evaluate_strategy_exit_stack,
)
