from __future__ import annotations

import importlib.util
import pytest

if importlib.util.find_spec("phase1_research_copilot") is None:
    pytest.skip("phase1_research_copilot package not present in this repo checkout", allow_module_level=True)


import importlib.util
import sys
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
CONFIG_PATH = PHASE1_ROOT / "shared" / "config.py"


def _load_config_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, CONFIG_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_config_falls_back_when_pydantic_settings_is_missing(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "pydantic_settings", None)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("GATEWAY_PORT", "9001")
    monkeypatch.setenv("EXCHANGE_SYMBOLS", "BTC/USDT,ETH/USDT")

    config = _load_config_module("phase1_config_fallback_test")

    assert config._HAS_PYDANTIC_SETTINGS is False

    settings = config.get_settings()
    assert settings.openai_api_key == "sk-test"
    assert settings.openai_model == "gpt-4.1-mini"
    assert settings.gateway_port == 9001
    assert settings.exchange_symbols_list == ["BTC/USDT", "ETH/USDT"]
