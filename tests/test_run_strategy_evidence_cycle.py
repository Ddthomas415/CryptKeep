from __future__ import annotations

import json

from scripts import run_strategy_evidence_cycle as script


def test_run_strategy_evidence_cycle_persists_and_writes_decision_record(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "load_user_yaml", lambda: {"risk": {"max_order_quote": 25.0}})
    monkeypatch.setattr(
        script,
        "run_strategy_evidence_cycle",
        lambda **kwargs: {
            "ok": True,
            "as_of": "2026-03-19T12:00:00Z",
            "symbol": kwargs["symbol"],
            "aggregate_leaderboard": {"rows": []},
            "decisions": [],
            "windows": [],
            "window_count": 0,
            "initial_cash": kwargs["initial_cash"],
            "fee_bps": kwargs["fee_bps"],
            "slippage_bps": kwargs["slippage_bps"],
        },
    )
    monkeypatch.setattr(
        script,
        "persist_strategy_evidence",
        lambda report, latest_path="": {"ok": True, "latest_path": latest_path or "/tmp/strategy_evidence.latest.json", "history_path": "/tmp/history.json"},
    )
    monkeypatch.setattr(
        script,
        "write_decision_record",
        lambda report, path="", artifact_path="": {"ok": True, "path": path or "/tmp/decision_record.md", "artifact_path": artifact_path},
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_strategy_evidence_cycle.py",
            "--symbol",
            "ETH/USDT",
            "--write-decision-record",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["report"]["symbol"] == "ETH/USDT"
    assert out["persisted"]["latest_path"] == "/tmp/strategy_evidence.latest.json"
    assert out["decision_record"]["path"] == "/tmp/decision_record.md"
