import pytest

from scripts.research.cmc_return_math import net_return, paired_excess


def test_flat_price_pays_both_fees():
    assert net_return(100, 100) == pytest.approx(0.988 / 1.012 - 1)


def test_spread_and_zero_fee():
    assert net_return(101, 100, 0) == pytest.approx(100/101 - 1)


def test_identical_benchmark_has_zero_excess():
    result = paired_excess(100, 110, 100, 110)
    assert result["excess_return"] == 0
    assert result["fee_per_side"] == 0.012


@pytest.mark.parametrize("ask,bid,fee", [(0, 1, .012), (1, -1, .012),
    (True, 1, .012), (1, 1, True), (1, float("nan"), .012), (1, 1, 1), (1, 1, -.1)])
def test_invalid_inputs_refused(ask, bid, fee):
    with pytest.raises(ValueError):
        net_return(ask, bid, fee)
