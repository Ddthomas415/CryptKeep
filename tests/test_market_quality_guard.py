from __future__ import annotations

import services.risk.market_quality_guard as mqg


def test_market_quality_guard_allows_when_disabled(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": False}},
    )
    out = mqg.check("coinbase", "BTC/USD")
    assert out["ok"] is True
    assert out["reason"] == "guard_disabled"


def test_market_quality_guard_blocks_on_missing_quotes_when_configured(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": True, "block_when_unknown": True}},
    )
    monkeypatch.setattr(mqg, "get_best_bid_ask_last", lambda venue, symbol: None)
    out = mqg.check("coinbase", "BTC/USD")
    assert out["ok"] is False
    assert out["reason"] == "no_quote_data"


def test_market_quality_guard_requires_bid_ask(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": True, "require_bid_ask": True}},
    )
    monkeypatch.setattr(
        mqg,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 9999999999999, "bid": None, "ask": None, "last": 100.0},
    )
    out = mqg.check("coinbase", "BTC/USD")
    assert out["ok"] is False
    assert out["reason"] == "missing_bid_ask"


def test_market_quality_guard_spread_and_staleness(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": True, "max_spread_bps": 50.0, "max_tick_age_sec": 1.0}},
    )
    monkeypatch.setattr(
        mqg,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 102.0, "last": 101.0},
    )
    out_spread = mqg.check("coinbase", "BTC/USD")
    assert out_spread["ok"] is False
    assert out_spread["reason"] == "spread_too_wide"

    monkeypatch.setattr(
        mqg,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.02, "last": 100.01},
    )
    out_stale = mqg.check("coinbase", "BTC/USD")
    assert out_stale["ok"] is False
    assert out_stale["reason"] == "stale_tick"


def test_market_quality_guard_happy_path(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": True, "max_spread_bps": 500.0, "max_tick_age_sec": 9999999}},
    )
    monkeypatch.setattr(
        mqg,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 9999999999999, "bid": 100.0, "ask": 100.5, "last": 100.2},
    )
    out = mqg.check("coinbase", "BTC/USD")
    assert out["ok"] is True
    assert out["price_used"] > 0
    assert out["spread_bps"] is not None


def test_market_quality_guard_symbol_threshold_overrides(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {
            "market_quality_guard": {
                "enabled": True,
                "max_spread_bps": 500.0,
                "max_tick_age_sec": 9999999.0,
                "symbol_thresholds": {
                    "BTC/USD": {"max_spread_bps": 20.0, "max_tick_age_sec": 30.0},
                },
            }
        },
    )
    monkeypatch.setattr(
        mqg,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 9999999999999, "bid": 100.0, "ask": 100.30, "last": 100.2},
    )
    out = mqg.check("coinbase", "btc-usd")
    assert out["ok"] is False
    assert out["reason"] == "spread_too_wide"


def test_market_quality_guard_compat_wrapper_returns_tuple(monkeypatch):
    monkeypatch.setattr(
        mqg,
        "load_user_yaml",
        lambda: {"market_quality_guard": {"enabled": True, "block_when_unknown": True}},
    )
    monkeypatch.setattr(mqg, "get_best_bid_ask_last", lambda venue, symbol: None)

    out = mqg.check("coinbase", "BTC/USD")
    ok, reason = mqg.check_market_quality("coinbase", "BTC/USD")

    assert out["ok"] is False
    assert out["reason"] == "no_quote_data"
    assert ok is out["ok"]
    assert reason == out["reason"]
