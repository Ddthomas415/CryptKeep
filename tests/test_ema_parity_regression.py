import pandas as pd


def _mk_market(closes):
    class _M:
        def __init__(self, closes):
            self.ohlcv = [[0, 0, 0, 0, float(c), 0] for c in closes]
    return _M(closes)


def _mk_position(base_amt):
    class _P:
        def __init__(self, base_amt):
            self.base_amt = float(base_amt)
    return _P(base_amt)

from services.strategies.ema_cross import ema_crossover_signal
from services.strategies.impl_ema_cross import EmaCrossStrategy
from services.strategies.ema_crossover_live import EMACrossoverLive
from services.strategies.live_base import LiveContext


def _ctx(position_qty: float = 0.0):
    return LiveContext(
        venue="paper",
        symbol="BTC/USDT",
        base="BTC",
        quote="USDT",
        bucket="1m",
        position_qty=float(position_qty),
        last_price=100.0,
        last_candle_ts=0,
    )


def test_ema_parity_insufficient_candles():
    closes = [100.0, 101.0, 102.0]
    df = pd.DataFrame({"close": closes})

    canonical = ema_crossover_signal(closes=closes, fast=3, slow=5)
    impl = EmaCrossStrategy().compute_signal(cfg={"strategy": {"ema_fast": 3, "ema_slow": 5}}, market=_mk_market(closes), position=_mk_position(0.0))
    live = EMACrossoverLive(fast=3, slow=5).decide(df, _ctx(0.0))

    assert canonical["ok"] is False
    assert impl.action == "hold"
    assert live.action == "hold"


def test_ema_parity_buy_signal():
    closes = [10, 9, 8, 9, 10, 11, 12, 13]
    closes = [float(x) for x in closes]
    df = pd.DataFrame({"close": closes})

    canonical = ema_crossover_signal(closes=closes, fast=2, slow=4)
    impl = EmaCrossStrategy().compute_signal(cfg={"strategy": {"ema_fast": 2, "ema_slow": 4}}, market=_mk_market(closes), position=_mk_position(0.0))
    live = EMACrossoverLive(fast=2, slow=4).decide(df, _ctx(0.0))

    assert canonical["ok"] is True
    assert impl.action in {"buy", "sell", "hold"}
    assert canonical["signal"] == impl.action
    if canonical["signal"] == "buy":
        assert live.action == "enter"
        assert live.side == "buy"
    else:
        assert live.action == "hold"


def test_ema_parity_sell_signal_with_open_position():
    closes = [13, 12, 11, 10, 9, 8, 7, 6]
    closes = [float(x) for x in closes]
    df = pd.DataFrame({"close": closes})

    canonical = ema_crossover_signal(closes=closes, fast=2, slow=4)
    impl = EmaCrossStrategy().compute_signal(cfg={"strategy": {"ema_fast": 2, "ema_slow": 4}}, market=_mk_market(closes), position=_mk_position(0.0))
    live = EMACrossoverLive(fast=2, slow=4).decide(df, _ctx(1.0))

    assert canonical["ok"] is True
    assert impl.action in {"buy", "sell", "hold"}
    assert canonical["signal"] == impl.action
    if canonical["signal"] == "sell":
        assert live.action == "exit"
        assert live.side == "sell"
    else:
        assert live.action == "hold"


def test_ema_parity_no_signal():
    closes = [10, 10.1, 10.2, 10.25, 10.3, 10.31, 10.32, 10.33]
    closes = [float(x) for x in closes]
    df = pd.DataFrame({"close": closes})

    canonical = ema_crossover_signal(closes=closes, fast=2, slow=4)
    impl = EmaCrossStrategy().compute_signal(cfg={"strategy": {"ema_fast": 2, "ema_slow": 4}}, market=_mk_market(closes), position=_mk_position(0.0))
    live_flat = EMACrossoverLive(fast=2, slow=4).decide(df, _ctx(0.0))
    live_open = EMACrossoverLive(fast=2, slow=4).decide(df, _ctx(1.0))

    assert canonical["ok"] is True
    assert impl.action in {"buy", "sell", "hold"}
    assert canonical["signal"] == impl.action == "hold"
    assert live_flat.action == "hold"
    assert live_open.action == "hold"
