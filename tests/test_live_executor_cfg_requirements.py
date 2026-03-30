import pytest

from services.execution.live_executor import cfg_from_yaml


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
        cfg_from_yaml(str(p))


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
        cfg_from_yaml(str(p))


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
    cfg = cfg_from_yaml(str(p))
    assert cfg.exchange_id == "coinbase"
    assert cfg.symbol == "ETH/USD"
