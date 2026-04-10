from __future__ import annotations

from services import config_loader as loader


def test_load_runtime_trading_config_merges_runtime_over_legacy_default_path(monkeypatch, tmp_path):
    legacy_cfg = tmp_path / "config" / "trading.yaml"
    legacy_cfg.parent.mkdir(parents=True, exist_ok=True)
    legacy_cfg.write_text(
        """
live:
  exchange_id: coinbase
  enabled: false
symbols:
  - BTC/USD
execution:
  db_path: /tmp/legacy.sqlite
""",
        encoding="utf-8",
    )
    runtime_cfg = tmp_path / "runtime-user.yaml"
    runtime_cfg.write_text(
        """
live:
  sandbox: true
execution:
  db_path: /tmp/runtime.sqlite
  live_enabled: true
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "code_root", lambda: tmp_path)
    monkeypatch.setattr(loader, "_CFG_PATH", runtime_cfg)

    cfg = loader.load_runtime_trading_config()

    assert cfg["live"]["exchange_id"] == "coinbase"
    assert cfg["live"]["enabled"] is True
    assert cfg["live"]["sandbox"] is True
    assert cfg["execution"]["live_enabled"] is True
    assert cfg["execution"]["db_path"] == "/tmp/runtime.sqlite"
    assert cfg["symbols"] == ["BTC/USD"]


def test_load_runtime_trading_config_fills_symbols_and_exchange_from_preflight(monkeypatch, tmp_path):
    legacy_cfg = tmp_path / "config" / "trading.yaml"
    legacy_cfg.parent.mkdir(parents=True, exist_ok=True)
    legacy_cfg.write_text("{}", encoding="utf-8")
    runtime_cfg = tmp_path / "runtime-user.yaml"
    runtime_cfg.write_text(
        """
preflight:
  venues: [binance]
  symbols: [BTC/USDT]
execution:
  live_enabled: false
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "code_root", lambda: tmp_path)
    monkeypatch.setattr(loader, "_CFG_PATH", runtime_cfg)

    cfg = loader.load_runtime_trading_config()

    assert cfg["live"]["exchange_id"] == "binance"
    assert cfg["symbols"] == ["BTC/USDT"]
    assert cfg["live"]["enabled"] is False
    assert cfg["execution"]["live_enabled"] is False


def test_load_runtime_trading_config_explicit_path_skips_runtime_overlay(monkeypatch, tmp_path):
    explicit_cfg = tmp_path / "explicit.yaml"
    explicit_cfg.write_text(
        """
live:
  exchange_id: coinbase
symbols:
  - ETH/USD
execution:
  db_path: /tmp/explicit.sqlite
""",
        encoding="utf-8",
    )
    runtime_cfg = tmp_path / "runtime-user.yaml"
    runtime_cfg.write_text(
        """
live:
  exchange_id: binance
execution:
  live_enabled: true
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(loader, "_CFG_PATH", runtime_cfg)

    cfg = loader.load_runtime_trading_config(str(explicit_cfg))

    assert cfg["live"]["exchange_id"] == "coinbase"
    assert cfg["execution"]["db_path"] == "/tmp/explicit.sqlite"
    assert "live_enabled" not in cfg["execution"]
    assert cfg["symbols"] == ["ETH/USD"]


def test_runtime_trading_config_available_accepts_runtime_only_default_path(monkeypatch, tmp_path):
    runtime_cfg = tmp_path / "runtime-user.yaml"
    runtime_cfg.write_text("execution:\n  live_enabled: false\n", encoding="utf-8")

    monkeypatch.setattr(loader, "code_root", lambda: tmp_path)
    monkeypatch.setattr(loader, "_CFG_PATH", runtime_cfg)

    assert loader.runtime_trading_config_available() is True
