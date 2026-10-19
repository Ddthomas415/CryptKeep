import pytest
from scripts.research.report_breakout_uncertainty import paired_daily, block_mean_gap


def test_complete_days_and_aligned_returns():
    a = [{"hour": h, "equity": 100 + h} for h in range(72)]
    b = [{"hour": h, "equity": 100} for h in range(72)]
    pairs = paired_daily(a, b, 0, 24)
    assert [r[0] for r in pairs] == [47, 71]
    assert pairs[0][1] == pytest.approx(147 / 123 - 1)


def test_missing_interior_hour_is_not_deleted():
    a = [{"hour": h, "equity": 100 if h != 30 else None} for h in range(72)]
    with pytest.raises(ValueError, match="unknown"):
        paired_daily(a, a, 0, 24)


def test_paired_constant_gap_and_reproducibility():
    pairs = [(h, .02, .01) for h in range(60)]
    first = block_mean_gap(pairs, 14)
    assert first == block_mean_gap(pairs, 14)
    assert first["p025"] == pytest.approx(.01)
    assert first["p975"] == pytest.approx(.01)
