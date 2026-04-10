import pytest

from services.execution import live_executor as le


def test_cfg_from_yaml_requires_live_exchange_id(tmp_path):
    p = tmp_path / "trading.yaml"
    p.write_text(
        """
live:
  enabled: true
symbols:
  - BTC/USD
""",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="CBP_CONFIG_REQUIRED:missing_config:live.exchange_id"):
        le.cfg_from_yaml(str(p))


def test_cfg_from_yaml_requires_symbols_first_entry(tmp_path):
    p = tmp_path / "trading.yaml"
    p.write_text(
        """
live:
  enabled: true
  exchange_id: coinbase
symbols: []
""",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match=r"CBP_CONFIG_REQUIRED:missing_config:symbols\[0\]"):
        le.cfg_from_yaml(str(p))


def test_cfg_from_yaml_accepts_explicit_exchange_and_symbol(tmp_path):
    p = tmp_path / "trading.yaml"
    p.write_text(
        """
live:
  enabled: true
  exchange_id: coinbase
symbols:
  - ETH/USD
""",
        encoding="utf-8",
    )
    cfg = le.cfg_from_yaml(str(p))
    assert cfg.exchange_id == "coinbase"
    assert cfg.symbol == "ETH/USD"


def test_cfg_from_yaml_default_path_prefers_runtime_trading_config(monkeypatch):
    monkeypatch.setattr(
        le,
        "load_runtime_trading_config",
        lambda path="config/trading.yaml": {
            "live": {"exchange_id": "binance", "sandbox": True},
            "execution": {"db_path": "/tmp/runtime.sqlite", "live_enabled": True},
            "symbols": ["BTC/USDT"],
        },
    )

    cfg = le.cfg_from_yaml()

    assert cfg.exchange_id == "binance"
    assert cfg.symbol == "BTC/USDT"
    assert cfg.exec_db == "/tmp/runtime.sqlite"
    assert cfg.enabled is True
    assert cfg.sandbox is True
