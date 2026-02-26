from __future__ import annotations

import time

from services.execution import strategy_runner


def test_shutdown_signal_sets_runner_event():
    strategy_runner._SHUTDOWN_EVENT.clear()
    strategy_runner._handle_shutdown_signal(15, None)
    assert strategy_runner._SHUTDOWN_EVENT.is_set()
    strategy_runner._SHUTDOWN_EVENT.clear()


def test_run_forever_exits_cleanly_on_requested_shutdown(monkeypatch):
    strategy_runner._SHUTDOWN_EVENT.clear()
    monkeypatch.setattr(strategy_runner, "_install_shutdown_signal_handlers", lambda: None)
    monkeypatch.setattr(strategy_runner, "_record_heartbeat_latency", lambda: None)
    monkeypatch.setattr(strategy_runner, "log_event", lambda *args, **kwargs: None)

    def _run_once_then_stop():
        strategy_runner.request_shutdown("unit_test")

    monkeypatch.setattr(strategy_runner, "run_once", _run_once_then_stop)

    start = time.time()
    strategy_runner.run_forever(interval_sec=0.01)
    elapsed = time.time() - start
    assert elapsed < 0.5
    strategy_runner._SHUTDOWN_EVENT.clear()
