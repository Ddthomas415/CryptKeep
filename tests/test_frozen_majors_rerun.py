import datetime as dt

import pytest

from scripts.research.rerun_frozen_majors import run


def inputs():
    start = int(dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc).timestamp())
    days = [start + i * 86400 for i in range(40)]
    raw = {a: {t: [t, 200, 210, 90, 100, 1] for t in days} for a in ("BTC", "ETH")}
    namespace = {"days": days, "P": {a: [100] * 40 for a in raw},
                 "target": lambda rule, i: {"BTC": 1},
                 "stats": lambda curve, exposure: {"end_usd": curve[-1][1]}}
    day = lambda i: dt.datetime.fromtimestamp(days[i], dt.timezone.utc).date().isoformat()
    return namespace, raw, day


def test_prior_close_signal_fills_next_open_not_prior_close():
    namespace, raw, day = inputs()
    result = run(namespace, raw, "hold_btc", 0, day(30), day(31))
    assert result["marked_stats"]["end_usd"] == pytest.approx(500 / 1.0005)


def test_missing_warmup_not_scored():
    namespace, raw, day = inputs()
    with pytest.raises(ValueError, match="warmup"):
        run(namespace, raw, "sma100", .005, day(30), day(31))


def test_benchmark_pays_same_buy_cost():
    namespace, raw, day = inputs()
    result = run(namespace, raw, "hold_btc", .005, day(30), day(31))
    assert result["marked_stats"]["end_usd"] == pytest.approx(500 / (1.0005 * 1.005))
    assert result["terminal_liquidation_usd"] < result["marked_stats"]["end_usd"]
