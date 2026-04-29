from __future__ import annotations

from scripts import run_intent_executor_safe as executor_safe
from scripts import run_intent_reconciler_safe as reconciler_safe
from scripts import run_intent_consumer_safe as consumer_safe
from scripts import run_live_reconciler_safe as live_reconciler_safe


def test_intent_executor_safe_accepts_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(executor_safe, "runtime_trading_config_available", lambda: True)

    assert executor_safe._prereqs_ok() == (True, "ok")


def test_intent_executor_safe_reports_missing_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(executor_safe, "runtime_trading_config_available", lambda: False)

    assert executor_safe._prereqs_ok() == (False, "missing runtime trading config")


def test_intent_reconciler_safe_accepts_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(reconciler_safe, "runtime_trading_config_available", lambda: True)

    assert reconciler_safe._prereqs_ok() == (True, "ok")


def test_intent_reconciler_safe_reports_missing_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(reconciler_safe, "runtime_trading_config_available", lambda: False)

    assert reconciler_safe._prereqs_ok() == (False, "missing runtime trading config")


def test_intent_consumer_safe_accepts_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(consumer_safe, "runtime_trading_config_available", lambda: True)

    assert consumer_safe._prereqs_ok() == (True, "ok")


def test_intent_consumer_safe_reports_missing_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(consumer_safe, "runtime_trading_config_available", lambda: False)

    assert consumer_safe._prereqs_ok() == (False, "missing runtime trading config")


def test_live_reconciler_safe_accepts_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(live_reconciler_safe, "runtime_trading_config_available", lambda: True)

    assert live_reconciler_safe._prereqs_ok() == (True, "ok")


def test_live_reconciler_safe_reports_missing_runtime_config(monkeypatch) -> None:
    monkeypatch.setattr(live_reconciler_safe, "runtime_trading_config_available", lambda: False)

    assert live_reconciler_safe._prereqs_ok() == (False, "missing runtime trading config")
