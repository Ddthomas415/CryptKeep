def should_invalidate_ema_long(
    *,
    avg_range_pct: float,
    trend_efficiency: float,
    cross_gap_pct: float,
    min_volatility_pct: float,
    min_trend_efficiency: float,
    min_cross_gap_pct: float,
) -> str | None:
    if avg_range_pct < min_volatility_pct:
        return "strategy_exit:ema_cross:low_volatility_invalidation"
    if trend_efficiency < min_trend_efficiency:
        return "strategy_exit:ema_cross:chop_invalidation"
    if cross_gap_pct < min_cross_gap_pct:
        return "strategy_exit:ema_cross:cross_gap_invalidation"
    return None


def test_ema_cross_invalidates_on_low_vol():
    assert should_invalidate_ema_long(
        avg_range_pct=0.05,
        trend_efficiency=0.30,
        cross_gap_pct=0.08,
        min_volatility_pct=0.20,
        min_trend_efficiency=0.15,
        min_cross_gap_pct=0.03,
    ) == "strategy_exit:ema_cross:low_volatility_invalidation"


def test_ema_cross_invalidates_on_chop():
    assert should_invalidate_ema_long(
        avg_range_pct=0.30,
        trend_efficiency=0.05,
        cross_gap_pct=0.08,
        min_volatility_pct=0.20,
        min_trend_efficiency=0.15,
        min_cross_gap_pct=0.03,
    ) == "strategy_exit:ema_cross:chop_invalidation"


def test_ema_cross_invalidates_on_cross_gap_loss():
    assert should_invalidate_ema_long(
        avg_range_pct=0.30,
        trend_efficiency=0.30,
        cross_gap_pct=0.01,
        min_volatility_pct=0.20,
        min_trend_efficiency=0.15,
        min_cross_gap_pct=0.03,
    ) == "strategy_exit:ema_cross:cross_gap_invalidation"
