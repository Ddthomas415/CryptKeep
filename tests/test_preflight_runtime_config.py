from __future__ import annotations

from services.preflight import preflight as pf


def test_run_preflight_default_path_accepts_runtime_config_without_legacy_file(monkeypatch, tmp_path):
    monkeypatch.setattr(pf, "ensure_dirs", lambda: None)
    monkeypatch.setattr(pf, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(pf, "runtime_trading_config_available", lambda cfg_path="config/trading.yaml": True)
    monkeypatch.setattr(
        pf,
        "load_runtime_trading_config",
        lambda cfg_path="config/trading.yaml": {
            "live": {"exchange_id": "binance"},
            "execution": {
                "executor_mode": "paper",
                "db_path": str(tmp_path / "execution.sqlite"),
                "live_enabled": False,
            },
            "symbols": ["BTC/USDT"],
        },
    )

    out = pf.run_preflight()
    checks = {item["name"]: item for item in out.checks}

    assert out.ok is True
    assert checks["exchange_supported"]["ok"] is True
    assert checks["symbols_configured"]["ok"] is True
    assert checks["db_writable"]["ok"] is True
