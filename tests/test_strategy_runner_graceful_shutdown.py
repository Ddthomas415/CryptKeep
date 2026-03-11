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

def test_run_forever_exits_immediately_when_shutdown_already_set(monkeypatch):
    strategy_runner._SHUTDOWN_EVENT.set()

    monkeypatch.setattr(strategy_runner, "_install_shutdown_signal_handlers", lambda: None)
    monkeypatch.setattr(strategy_runner, "_record_heartbeat_latency", lambda: None)
    monkeypatch.setattr(strategy_runner, "log_event", lambda *args, **kwargs: None)

    calls = {"run_once": 0}

    def _run_once():
        calls["run_once"] += 1

    monkeypatch.setattr(strategy_runner, "run_once", _run_once)

    strategy_runner.run_forever(interval_sec=0.01)

    assert calls["run_once"] == 0
    strategy_runner._SHUTDOWN_EVENT.clear()


def test_request_shutdown_is_idempotent_when_called_twice(monkeypatch):
    strategy_runner._SHUTDOWN_EVENT.clear()

    events = []

    def _log_event(*args, **kwargs):
        events.append((args, kwargs))

    monkeypatch.setattr(strategy_runner, "log_event", _log_event)

    strategy_runner.request_shutdown("first")
    strategy_runner.request_shutdown("second")

    assert strategy_runner._SHUTDOWN_EVENT.is_set()
    assert len(events) == 1
    strategy_runner._SHUTDOWN_EVENT.clear()


