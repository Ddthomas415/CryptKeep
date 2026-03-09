from __future__ import annotations

import logging

from services.execution import strategy_runner


class DummyLatencyError(Exception):
    pass


def test_request_shutdown_logs_warning_when_event_log_fails(monkeypatch, caplog):
    strategy_runner._SHUTDOWN_EVENT.clear()

    def _boom(*args, **kwargs):
        raise DummyLatencyError("log failure")

    monkeypatch.setattr(strategy_runner, "log_event", _boom)

    with caplog.at_level(logging.WARNING):
        strategy_runner.request_shutdown("unit_test")

    assert strategy_runner._SHUTDOWN_EVENT.is_set()
    assert "strategy shutdown log failed" in caplog.text
    strategy_runner._SHUTDOWN_EVENT.clear()


def test_record_heartbeat_latency_logs_warning_when_tracker_fails(monkeypatch, caplog):
    class BrokenTracker:
        def record_submit(self, **kwargs):
            raise DummyLatencyError("submit failure")

    monkeypatch.setattr(strategy_runner, "_LATENCY_TRACKER", BrokenTracker())

    with caplog.at_level(logging.WARNING):
        strategy_runner._record_heartbeat_latency()

    assert "strategy heartbeat latency recording failed" in caplog.text
