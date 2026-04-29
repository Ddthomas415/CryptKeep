from __future__ import annotations

from scripts import run_intent_consumer_safe as consumer_safe
from scripts import run_live_reconciler_safe as reconciler_safe


def test_intent_consumer_run_mode_nonzero_exit_enters_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    def _raise_keyboard_interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(consumer_safe, "log", messages.append)
    monkeypatch.setattr(consumer_safe, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(consumer_safe.runpy, "run_module", _raise_exit)
    monkeypatch.setattr(consumer_safe.time, "sleep", _raise_keyboard_interrupt)

    assert consumer_safe.main(["run"]) == 0
    assert any("exited nonzero" in message for message in messages)
    assert any("SAFE-IDLE" in message for message in messages)


def test_intent_consumer_invalid_args_do_not_enter_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    monkeypatch.setattr(consumer_safe, "log", messages.append)
    monkeypatch.setattr(consumer_safe.runpy, "run_module", _raise_exit)

    assert consumer_safe.main(["--bad-flag"]) == 2
    assert not any("SAFE-IDLE" in message for message in messages)


def test_live_reconciler_run_mode_nonzero_exit_enters_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    def _raise_keyboard_interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(reconciler_safe, "log", messages.append)
    monkeypatch.setattr(reconciler_safe, "runtime_trading_config_available", lambda: True)
    monkeypatch.setattr(reconciler_safe.runpy, "run_module", _raise_exit)
    monkeypatch.setattr(reconciler_safe.time, "sleep", _raise_keyboard_interrupt)

    assert reconciler_safe.main(["run"]) == 0
    assert any("exited nonzero" in message for message in messages)
    assert any("SAFE-IDLE" in message for message in messages)


def test_live_reconciler_invalid_args_do_not_enter_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    monkeypatch.setattr(reconciler_safe, "log", messages.append)
    monkeypatch.setattr(reconciler_safe.runpy, "run_module", _raise_exit)

    assert reconciler_safe.main(["--bad-flag"]) == 2
    assert not any("SAFE-IDLE" in message for message in messages)
