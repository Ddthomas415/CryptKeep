import pytest
from scripts.research.calibrate_cmc_synthetic import null_returns, rate


def test_null_generation_reproducible_and_bounded():
    for mode in ("iid", "overlap7", "persistent"):
        assert len(null_returns(60, 42, mode)) == 60
        assert null_returns(60, 42, mode) == null_returns(60, 42, mode)
    with pytest.raises(ValueError):
        null_returns(60, 42, "unknown")


def test_monte_carlo_uncertainty_not_hidden():
    result = rate(0, 30)
    assert result["rate"] == 0
    assert result["wilson95"][1] > .05
