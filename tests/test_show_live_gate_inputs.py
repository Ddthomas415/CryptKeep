from __future__ import annotations

import json

from scripts import show_live_gate_inputs as sli


def test_show_live_gate_inputs_uses_runtime_config(monkeypatch, capsys, tmp_path) -> None:
    exec_db = str(tmp_path / "execution.sqlite")
    monkeypatch.setattr(
        sli,
        "load_runtime_trading_config",
        lambda: {
            "execution": {"db_path": exec_db},
            "risk": {
                "live": {
                    "max_daily_loss_usd": 100.0,
                    "max_notional_per_trade_usd": 25.0,
                    "max_trades_per_day": 4,
                    "max_position_notional_usd": 50.0,
                }
            },
        },
    )
    monkeypatch.setattr(sli, "ensure_dirs", lambda: None)
    monkeypatch.setattr(sli, "get_admin_kill_switch_state", lambda: {"armed": False, "note": "manual"})

    class _FakeDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def killswitch_on(self) -> bool:
            return False

        def day_row(self):
            return {"day": "2026-04-10", "trades": 2, "realized_pnl_usd": 1.25, "updated_at": "2026-04-10T00:00:00Z"}

    class _FakeJournal:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def realized_pnl_today_usd(self) -> float:
            return 1.25

        def trades_today(self) -> int:
            return 2

    monkeypatch.setattr(sli, "LiveGateDB", _FakeDB)
    monkeypatch.setattr(sli, "JournalSignals", _FakeJournal)

    out = sli.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["exec_db"] == exec_db
    assert payload["killswitch"] is False
    assert payload["killswitch_admin"] is False
    assert payload["killswitch_db"] is False
    assert payload["limits"] == {
        "max_daily_loss_usd": 100.0,
        "max_notional_per_trade_usd": 25.0,
        "max_trades_per_day": 4,
        "max_position_notional_usd": 50.0,
    }
    assert payload["computed"] == {"realized_pnl_today_usd": 1.25, "trades_today": 2}


def test_show_live_gate_inputs_returns_null_limits_when_runtime_risk_missing(monkeypatch, capsys, tmp_path) -> None:
    exec_db = str(tmp_path / "execution.sqlite")
    monkeypatch.setattr(sli, "load_runtime_trading_config", lambda: {"execution": {"db_path": exec_db}})
    monkeypatch.setattr(sli, "ensure_dirs", lambda: None)
    monkeypatch.setattr(sli, "get_admin_kill_switch_state", lambda: {"armed": True, "note": "manual"})

    class _FakeDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def killswitch_on(self) -> bool:
            return False

        def day_row(self):
            return {"day": "2026-04-10", "trades": 0, "realized_pnl_usd": 0.0, "updated_at": "2026-04-10T00:00:00Z"}

    class _FakeJournal:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def realized_pnl_today_usd(self) -> float:
            return 0.0

        def trades_today(self) -> int:
            return 0

    monkeypatch.setattr(sli, "LiveGateDB", _FakeDB)
    monkeypatch.setattr(sli, "JournalSignals", _FakeJournal)

    out = sli.main()

    assert out == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["exec_db"] == exec_db
    assert payload["killswitch"] is True
    assert payload["killswitch_admin"] is True
    assert payload["killswitch_db"] is False
    assert payload["limits"] is None
