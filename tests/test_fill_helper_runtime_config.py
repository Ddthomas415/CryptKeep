from __future__ import annotations

import json
from types import SimpleNamespace

from scripts import inject_test_fill
from scripts import record_dummy_fill


def test_record_dummy_fill_uses_runtime_config_exec_db(monkeypatch, capsys) -> None:
    monkeypatch.setattr(record_dummy_fill, "load_runtime_trading_config", lambda: {"execution": {"db_path": "/tmp/runtime-exec.sqlite"}})
    monkeypatch.setattr(record_dummy_fill, "ensure_dirs", lambda: None)
    monkeypatch.setattr(record_dummy_fill, "record_fill", lambda exec_db, fill: SimpleNamespace(exec_db=exec_db, **fill))

    class _FakeRiskDailyDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def get(self):
            return {"exec_db": self.exec_db, "realized_pnl_usd": 3.5}

    monkeypatch.setattr(record_dummy_fill, "RiskDailyDB", _FakeRiskDailyDB)
    monkeypatch.setattr(record_dummy_fill.sys, "argv", ["record_dummy_fill.py", "--symbol", "BTC-USD", "--pnl", "3.5", "--fee", "0.2"])

    assert record_dummy_fill.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["fill"]["exec_db"] == "/tmp/runtime-exec.sqlite"
    assert payload["risk_daily_today"]["exec_db"] == "/tmp/runtime-exec.sqlite"


def test_inject_test_fill_uses_runtime_config_exec_db(monkeypatch, capsys) -> None:
    monkeypatch.setattr(inject_test_fill, "load_runtime_trading_config", lambda: {"execution": {"db_path": "/tmp/runtime-exec.sqlite"}})
    monkeypatch.setattr(inject_test_fill, "ensure_dirs", lambda: None)

    captured: dict[str, object] = {}

    class _FakeSink:
        def __init__(self, exec_db: str):
            captured["exec_db"] = exec_db

        def on_fill(self, fill: dict) -> None:
            captured["fill"] = fill

    monkeypatch.setattr(inject_test_fill, "CanonicalFillSink", _FakeSink)
    monkeypatch.setattr(
        inject_test_fill.sys,
        "argv",
        ["inject_test_fill.py", "--symbol", "BTC/USDT", "--side", "buy", "--qty", "0.001", "--price", "100.0", "--venue", "test"],
    )

    assert inject_test_fill.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["exec_db"] == "/tmp/runtime-exec.sqlite"
    assert payload["exec_db"] == "/tmp/runtime-exec.sqlite"
    assert payload["fill"]["symbol"] == "BTC/USDT"
