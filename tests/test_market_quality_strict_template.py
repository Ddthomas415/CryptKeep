from __future__ import annotations

import time
from pathlib import Path

import pytest
import yaml

import services.risk.market_quality_guard as mq

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "templates"
    / "market_quality_strict.yaml"
)


def _load_template_cfg() -> dict:
    data = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "market_quality_guard" in data
    return data


def _use_cfg(monkeypatch: pytest.MonkeyPatch, cfg: dict) -> None:
    monkeypatch.setattr(mq, "load_user_yaml", lambda *args, **kwargs: cfg)


@pytest.fixture()
def fresh_quote(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        mq,
        "get_best_bid_ask_last",
        lambda venue, symbol: {
            "bid": 100.0,
            "ask": 100.02,
            "last": 100.01,
            "ts_ms": int(time.time() * 1000),
        },
    )


@pytest.fixture()
def missing_quote(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mq, "get_best_bid_ask_last", lambda venue, symbol: None)


def test_template_parses_and_is_strict():
    guard = _load_template_cfg()["market_quality_guard"]
    assert guard["block_when_unknown"] is True
    assert guard["require_bid_ask"] is True
    assert float(guard["max_spread_bps"]) <= 100.0


def test_strict_template_holds_on_missing_quote(monkeypatch, missing_quote):
    _use_cfg(monkeypatch, _load_template_cfg())
    result = mq.check("okx", "BTC/USDT")
    assert result["ok"] is False
    assert result.get("reason") == "no_quote_data"


def test_strict_template_passes_fresh_quote(monkeypatch, fresh_quote):
    _use_cfg(monkeypatch, _load_template_cfg())
    result = mq.check("okx", "BTC/USDT")
    assert result["ok"] is True
    assert result.get("spread_bps") is not None


def test_strict_template_blocks_wide_spread(monkeypatch):
    def wide_quote(venue, symbol):
        return {
            "bid": 100.0,
            "ask": 101.0,
            "last": 100.5,
            "ts_ms": int(time.time() * 1000),
        }

    monkeypatch.setattr(mq, "get_best_bid_ask_last", wide_quote)
    _use_cfg(monkeypatch, _load_template_cfg())
    result = mq.check("okx", "BTC/USDT")
    assert result["ok"] is False
    assert result["reason"] == "spread_too_wide"


def test_permissive_default_still_passes_missing_quote(monkeypatch, missing_quote):
    _use_cfg(monkeypatch, {})
    result = mq.check("okx", "BTC/USDT")
    assert result["ok"] is True
    assert result.get("reason") == "no_quote_data"
