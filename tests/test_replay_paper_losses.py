from __future__ import annotations

import json

from scripts import replay_paper_losses as script


def test_replay_paper_losses_runs_with_args(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_loss_replay",
        lambda **kwargs: {"ok": True, "strategy_id": kwargs["strategy_id"], "symbol_filter": kwargs["symbol"] or None},
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        ["replay_paper_losses.py", "--strategy-id", "mean_reversion_rsi", "--symbol", "ETH/USD", "--limit", "3"],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["strategy_id"] == "mean_reversion_rsi"
    assert out["symbol_filter"] == "ETH/USD"
