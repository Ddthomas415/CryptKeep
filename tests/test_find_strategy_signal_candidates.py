from __future__ import annotations

from scripts import find_strategy_signal_candidates as scanner


def test_select_symbols_filters_active_spot_quote_and_sorts_by_volume() -> None:
    markets = {
        "BTC/USD": {"symbol": "BTC/USD", "active": True, "spot": True, "quoteVolume": 1000},
        "ETH/USD": {"symbol": "ETH/USD", "active": True, "spot": True, "quoteVolume": 5000},
        "XRP/USDC": {"symbol": "XRP/USDC", "active": True, "spot": True, "quoteVolume": 9000},
        "DOGE/USD": {"symbol": "DOGE/USD", "active": False, "spot": True, "quoteVolume": 9999},
        "SOL-PERP": {"symbol": "SOL-PERP", "active": True, "spot": False, "quoteVolume": 9999},
    }

    out = scanner._select_symbols(markets, quotes=["USD"], max_symbols=3)

    assert out == ["ETH/USD", "BTC/USD"]


def test_scan_candidates_returns_only_requested_action(monkeypatch) -> None:
    class _FakeExchange:
        def load_markets(self):
            return {
                "AAA/USD": {"symbol": "AAA/USD", "active": True, "spot": True, "quoteVolume": 100},
                "BBB/USD": {"symbol": "BBB/USD", "active": True, "spot": True, "quoteVolume": 50},
            }

        def fetch_ohlcv(self, symbol, timeframe="1m", limit=120):
            return [[1, 1, 2, 0.5, 1.5, 10.0] for _ in range(limit)]

        def close(self):
            return None

    def _fake_compute_signal(*, cfg, symbol, ohlcv):
        name = str(cfg.get("strategy", {}).get("name") or "")
        if symbol == "AAA/USD" and name == "breakout_donchian":
            return {
                "ok": True,
                "action": "buy",
                "reason": "donchian_break_up",
                "ind": {"volume_ratio": 1.5, "avg_range_pct": 0.9, "trend_efficiency": 0.4},
            }
        return {"ok": True, "action": "hold", "reason": "no_signal", "ind": {"volume_ratio": 0.5}}

    monkeypatch.setattr(scanner, "compute_signal", _fake_compute_signal)

    out = scanner.scan_candidates(
        venue="coinbase",
        quotes=["USD"],
        strategies=["breakout_donchian", "ema_cross"],
        timeframes=["5m"],
        action="buy",
        max_symbols=10,
        limit=40,
        exchange=_FakeExchange(),
    )

    assert out["ok"] is True
    assert out["scanned_symbols"] == 2
    assert out["errors"] == []
    assert len(out["candidates"]) == 1
    assert out["candidates"][0]["symbol"] == "AAA/USD"
    assert out["candidates"][0]["strategy"] == "breakout_donchian"
    assert out["candidates"][0]["action"] == "buy"


def test_scan_candidates_uses_explicit_symbols_without_market_discovery(monkeypatch) -> None:
    class _FakeExchange:
        def load_markets(self):
            return {}

        def fetch_ohlcv(self, symbol, timeframe="1m", limit=120):
            return [[1, 1, 2, 0.5, 1.5, 10.0] for _ in range(limit)]

    monkeypatch.setattr(
        scanner,
        "compute_signal",
        lambda *, cfg, symbol, ohlcv: {"ok": True, "action": "buy", "reason": "forced", "ind": {}},
    )

    out = scanner.scan_candidates(
        venue="coinbase",
        quotes=["USD"],
        strategies=["ema_cross"],
        timeframes=["1m"],
        action="buy",
        max_symbols=10,
        limit=10,
        symbols=["btc-usd", "ETH/USD"],
        exchange=_FakeExchange(),
    )

    assert out["scanned_symbols"] == 2
    assert [item["symbol"] for item in out["candidates"]] == ["ETH/USD", "BTC/USD"]

