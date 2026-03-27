import services.backtest.signal_replay as signal_replay
from services.backtest.signal_replay import replay_signals_on_ohlcv


def test_fetch_ohlcv_passes_since_ms(monkeypatch):
    seen: dict[str, object] = {}

    class _FakeExchange:
        def fetch_ohlcv(self, symbol, **kwargs):
            seen["symbol"] = symbol
            seen.update(kwargs)
            return [[1, 2, 3, 4, 5, 6]]

        def close(self):
            seen["closed"] = True

    monkeypatch.setattr(signal_replay, "normalize_venue", lambda venue: venue)
    monkeypatch.setattr(signal_replay, "normalize_symbol", lambda symbol: symbol)
    monkeypatch.setattr(signal_replay, "map_symbol", lambda venue, symbol: symbol)
    monkeypatch.setattr(signal_replay, "make_exchange", lambda *args, **kwargs: _FakeExchange())

    rows = signal_replay.fetch_ohlcv("coinbase", "BTC/USD", timeframe="5m", limit=10, since_ms=123456)

    assert rows == [[1, 2, 3, 4, 5, 6]]
    assert seen["symbol"] == "BTC/USD"
    assert seen["timeframe"] == "5m"
    assert seen["limit"] == 10
    assert seen["since"] == 123456
    assert seen["closed"] is True


def test_replay_signals_on_ohlcv_minimal():
    ohlcv = [
        [1000, 100.0, 101.0, 99.0, 100.0, 1.0],
        [2000, 110.0, 111.0, 109.0, 110.0, 1.0],
    ]
    signals = [
        {"ts_ms": 1000, "action": "buy"},
        {"ts_ms": 2000, "action": "sell"},
    ]

    out = replay_signals_on_ohlcv(
        ohlcv,
        signals,
        fee_bps=0.0,
        slippage_bps=0.0,
        initial_cash=10000.0,
    )

    assert out["initial_cash"] == 10000.0
    assert out["signals_used"] == 2
    assert len(out["trades"]) == 2
    assert len(out["equity"]) == 2
    assert out["final_equity"] == 11000.0
    assert out["realized_pnl_est"] == 1000.0
