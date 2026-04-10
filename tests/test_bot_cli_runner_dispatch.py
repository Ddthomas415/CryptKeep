from __future__ import annotations

from services.bot import cli_live, cli_paper


def test_cli_paper_dispatches_to_execution_runner(monkeypatch):
    calls = {"run_forever": 0}

    monkeypatch.setattr(cli_paper.paper_runner, "run_forever", lambda: calls.__setitem__("run_forever", calls["run_forever"] + 1))
    monkeypatch.delattr(cli_paper.paper_runner, "main", raising=False)
    monkeypatch.delattr(cli_paper.paper_runner, "run_paper", raising=False)

    assert cli_paper.main() == 0
    assert calls["run_forever"] == 1


def test_cli_paper_run_paper_receives_runtime_trading_config(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.delattr(cli_paper.paper_runner, "main", raising=False)
    monkeypatch.delattr(cli_paper.paper_runner, "run_forever", raising=False)
    monkeypatch.setattr(
        cli_paper,
        "load_runtime_trading_config",
        lambda: {"execution": {"executor_mode": "paper"}, "symbols": ["BTC/USD"]},
    )

    def _run_paper(cfg):
        captured["cfg"] = cfg
        return 0

    monkeypatch.setattr(cli_paper.paper_runner, "run_paper", _run_paper, raising=False)

    assert cli_paper.main() == 0
    assert captured["cfg"] == {"execution": {"executor_mode": "paper"}, "symbols": ["BTC/USD"]}


def test_cli_live_dispatches_to_execution_runner(monkeypatch):
    calls = {"run_forever_live": 0}

    monkeypatch.setattr(cli_live.live_trader_loop, "run_forever_live", lambda: calls.__setitem__("run_forever_live", calls["run_forever_live"] + 1))
    monkeypatch.delattr(cli_live.live_trader_loop, "main", raising=False)
    monkeypatch.delattr(cli_live.live_trader_loop, "run_live", raising=False)

    assert cli_live.main() == 0
    assert calls["run_forever_live"] == 1


def test_cli_live_run_live_receives_runtime_trading_config(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.delattr(cli_live.live_trader_loop, "main", raising=False)
    monkeypatch.delattr(cli_live.live_trader_loop, "run_forever_live", raising=False)
    monkeypatch.setattr(
        cli_live,
        "load_runtime_trading_config",
        lambda: {"execution": {"live_enabled": True}, "live": {"sandbox": True}},
    )
    def _run_live(cfg):
        captured["cfg"] = cfg
        return 0

    monkeypatch.setattr(cli_live.live_trader_loop, "run_live", _run_live, raising=False)

    assert cli_live.main() == 0
    assert captured["cfg"] == {"execution": {"live_enabled": True}, "live": {"sandbox": True}}
