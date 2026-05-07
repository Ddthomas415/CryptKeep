from __future__ import annotations

from scripts import start_bot


def test_start_bot_uses_pipeline_safe_wrapper(monkeypatch):
    cmds: dict[str, list[str]] = {}

    def _start_process(name, cmd):
        cmds[str(name)] = list(cmd)
        return {"ok": True, "name": name}

    monkeypatch.setattr(start_bot, "start_process", _start_process)
    monkeypatch.setattr(start_bot, "status", lambda _names: {})
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert cmds["pipeline"] == [start_bot.sys.executable, "scripts/run_pipeline_safe.py"]
