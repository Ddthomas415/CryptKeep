from __future__ import annotations

from services.bot import cli_live, cli_paper


def test_cli_paper_dispatches_to_execution_runner(monkeypatch):
    calls = {"run_forever": 0}

    monkeypatch.setattr(cli_paper.paper_runner, "run_forever", lambda: calls.__setitem__("run_forever", calls["run_forever"] + 1))
    monkeypatch.delattr(cli_paper.paper_runner, "main", raising=False)
    monkeypatch.delattr(cli_paper.paper_runner, "run_paper", raising=False)

    assert cli_paper.main() == 0
    assert calls["run_forever"] == 1


def test_cli_live_dispatches_to_execution_runner(monkeypatch):
    calls = {"run_forever_live": 0}

    monkeypatch.setattr(cli_live.live_trader_loop, "run_forever_live", lambda: calls.__setitem__("run_forever_live", calls["run_forever_live"] + 1))
    monkeypatch.delattr(cli_live.live_trader_loop, "main", raising=False)
    monkeypatch.delattr(cli_live.live_trader_loop, "run_live", raising=False)

    assert cli_live.main() == 0
    assert calls["run_forever_live"] == 1
