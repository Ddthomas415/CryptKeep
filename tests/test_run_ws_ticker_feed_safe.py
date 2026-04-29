from __future__ import annotations

from scripts import run_ws_ticker_feed_safe as mod


def test_run_mode_nonzero_exit_enters_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    def _raise_keyboard_interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(mod, "log", messages.append)
    monkeypatch.setattr(mod.runpy, "run_module", _raise_exit)
    monkeypatch.setattr(mod.time, "sleep", _raise_keyboard_interrupt)

    assert mod.main(["run"]) == 0
    assert any("exited nonzero" in message for message in messages)
    assert any("SAFE-IDLE" in message for message in messages)


def test_invalid_args_do_not_enter_safe_idle(monkeypatch):
    messages: list[str] = []

    def _raise_exit(*_args, **_kwargs):
        raise SystemExit(2)

    monkeypatch.setattr(mod, "log", messages.append)
    monkeypatch.setattr(mod.runpy, "run_module", _raise_exit)

    assert mod.main(["--bad-flag"]) == 2
    assert not any("SAFE-IDLE" in message for message in messages)
