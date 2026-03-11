from decimal import Decimal

from services.execution_sim.pricing import apply_market_slippage, compute_fee


def test_apply_market_slippage_buy_and_sell():
    price = Decimal("100")
    bps = Decimal("10")  # 0.10%

    buy_fill = apply_market_slippage(price=price, side="buy", slippage_bps=bps)
    sell_fill = apply_market_slippage(price=price, side="sell", slippage_bps=bps)

    assert buy_fill == Decimal("100.100")
    assert sell_fill == Decimal("99.900")


def test_apply_market_slippage_zero_bps_no_change():
    price = Decimal("145.20")
    out = apply_market_slippage(price=price, side="buy", slippage_bps=Decimal("0"))
    assert out == price


def test_compute_fee_from_notional_and_bps():
    fee = compute_fee(notional=Decimal("1000"), fee_bps=Decimal("5"))  # 0.05%
    assert fee == Decimal("0.5000")
