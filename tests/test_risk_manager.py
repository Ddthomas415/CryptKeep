from core.risk_manager import RiskConfig, RiskState, allow_order
from core.models import Order, OrderType, Side, TimeInForce, PortfolioState, utc_now, Position


def mk_order(symbol="BTC/USDT", side=Side.BUY, qty=1.0):
    return Order(
        client_order_id="t1",
        venue="paper",
        symbol=symbol,
        side=side,
        qty=float(qty),
        order_type=OrderType.MARKET,
        limit_price=None,
        tif=TimeInForce.IOC,
        reduce_only=False,
        post_only=False,
        ts=utc_now(),
    )


def test_blocks_without_price():
    cfg = RiskConfig()
    st = RiskState(day_key="2025-01-01", trades_today=0, peak_equity_today=100.0)
    port = PortfolioState(ts=utc_now(), cash=1000.0, equity=1000.0, positions={})
    ok, reason = allow_order(mk_order(), port, {}, cfg, st)
    assert ok is False
    assert reason == "NO_LATEST_PRICE"


def test_blocks_max_trades():
    cfg = RiskConfig(max_trades_per_day=1)
    st = RiskState(day_key="2025-01-01", trades_today=1, peak_equity_today=1000.0)
    port = PortfolioState(ts=utc_now(), cash=1000.0, equity=1000.0, positions={})
    ok, reason = allow_order(mk_order(), port, {"BTC/USDT": 100.0}, cfg, st)
    assert ok is False
    assert reason == "MAX_TRADES_PER_DAY"


def test_blocks_position_notional_cap():
    cfg = RiskConfig(max_position_notional=100.0)
    st = RiskState(day_key="2025-01-01", trades_today=0, peak_equity_today=1000.0)
    pos = Position(venue="paper", symbol="BTC/USDT", qty=0.5, avg_price=100.0, unrealized_pnl=0.0)
    port = PortfolioState(ts=utc_now(), cash=1000.0, equity=1000.0, positions={"paper:BTC/USDT": pos})
    ok, reason = allow_order(mk_order(qty=1.0), port, {"BTC/USDT": 200.0}, cfg, st)
    assert ok is False
    assert reason == "MAX_POSITION_NOTIONAL"


def test_blocks_drawdown():
    cfg = RiskConfig(max_drawdown_frac=0.10)
    st = RiskState(day_key="2025-01-01", trades_today=0, peak_equity_today=1000.0)
    port = PortfolioState(ts=utc_now(), cash=800.0, equity=800.0, positions={})
    ok, reason = allow_order(mk_order(), port, {"BTC/USDT": 100.0}, cfg, st)
    assert ok is False
    assert reason == "MAX_DRAWDOWN"
