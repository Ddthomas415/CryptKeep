from __future__ import annotations

from types import SimpleNamespace

from scripts import preflight as spf


def _resolution() -> SimpleNamespace:
    return SimpleNamespace(
        requested_port=8501,
        requested_available=True,
        resolved_port=8501,
        auto_switched=False,
    )


def test_run_accepts_runtime_only_default_config(monkeypatch) -> None:
    monkeypatch.setattr(spf, "REQUIRED_IMPORTS", [])
    monkeypatch.setattr(spf, "REQUIRED_PATHS", [])
    monkeypatch.setattr(spf, "resolve_preferred_port", lambda host, port, max_offset=50: _resolution())
    monkeypatch.setattr(spf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(spf, "runtime_trading_config_available", lambda path="config/trading.yaml": True)
    monkeypatch.setattr(
        spf,
        "load_runtime_trading_config",
        lambda path="config/trading.yaml": {
            "live": {"exchange_id": "binance"},
            "symbols": ["BTC/USDT"],
        },
    )

    out = spf.run()
    checks = {item["name"]: item for item in out["checks"]}

    assert out["ok"] is True
    assert "exists:config/trading.yaml" not in checks
    assert checks["runtime_trading_config"]["ok"] is True
    assert checks["runtime_trading_config"]["detail"] == "exchange_id=binance symbols=1"


def test_run_blocks_when_runtime_config_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(spf, "REQUIRED_IMPORTS", [])
    monkeypatch.setattr(spf, "REQUIRED_PATHS", [])
    monkeypatch.setattr(spf, "resolve_preferred_port", lambda host, port, max_offset=50: _resolution())
    monkeypatch.setattr(spf, "can_bind", lambda host, port: True)
    monkeypatch.setattr(spf, "runtime_trading_config_available", lambda path="config/trading.yaml": False)

    out = spf.run()
    checks = {item["name"]: item for item in out["checks"]}

    assert out["ok"] is False
    assert checks["runtime_trading_config"]["ok"] is False
    assert "Missing runtime trading config" in checks["runtime_trading_config"]["detail"]
