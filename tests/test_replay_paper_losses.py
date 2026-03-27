from __future__ import annotations

import json

from scripts import replay_paper_losses as script


def test_replay_paper_losses_runs_with_args(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _fake_build(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "strategy_id": kwargs["strategy_id"], "symbol_filter": kwargs["symbol"] or None}

    monkeypatch.setattr(
        script,
        "build_loss_replay",
        _fake_build,
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "replay_paper_losses.py",
            "--strategy-id",
            "mean_reversion_rsi",
            "--symbol",
            "ETH/USD",
            "--limit",
            "3",
            "--timeframe",
            "5m",
            "--context-bars",
            "2",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["strategy_id"] == "mean_reversion_rsi"
    assert out["symbol_filter"] == "ETH/USD"
    assert seen["timeframe"] == "5m"
    assert seen["context_bars"] == 2
