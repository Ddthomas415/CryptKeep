from __future__ import annotations

from scripts import start_bot


def test_start_bot_delegates_to_supervised_converge(monkeypatch):
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        start_bot.rbr,
        "load_trading_cfg",
        lambda: {"cfg": True},
    )
    monkeypatch.setattr(
        start_bot.rbr,
        "desired_state",
        lambda cfg: {
            "mode": "paper",
            "live_enabled": False,
            "venue": "coinbase",
            "symbols": ["BTC/USD"],
            "with_reconcile": False,
        },
    )
    monkeypatch.setattr(
        start_bot.rbr,
        "apply_state",
        lambda state, *, force_restart=False: calls.append({"state": dict(state), "force_restart": force_restart}) or {"ok": True, "started": [], "stopped": [], "status": {}},
    )
    monkeypatch.setattr(start_bot.rbr, "state_signature", lambda state: "sig")
    monkeypatch.setattr(start_bot.rbr, "write_status", lambda payload: None)
    monkeypatch.setattr(start_bot.sys, "argv", ["start_bot.py"])

    assert start_bot.main() == 0
    assert calls == [
        {
            "state": {
                "mode": "paper",
                "live_enabled": False,
                "venue": "coinbase",
                "symbols": ["BTC/USD"],
                "with_reconcile": False,
            },
            "force_restart": False,
        }
    ]
