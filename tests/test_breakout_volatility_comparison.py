import pytest
from scripts.research import compare_breakout_volatility_filter as comparison


def test_other_filters_remain_and_next_open_label(monkeypatch):
    def signal(*, cfg, **kwargs):
        assert cfg["strategy"]["min_volume_ratio"] == .95
        return {"action": "hold" if "min_volatility_pct" in cfg["strategy"] else "buy",
                "reason": "low_volatility_filter" if "min_volatility_pct" in cfg["strategy"] else "ok",
                "ind": {"close": 101, "upper_prev": 100}}
    monkeypatch.setattr(comparison, "compute_signal", signal)
    rows = [[i*300000, 100+i, 200, 90, 100, 1] for i in range(44)]
    strategy = {"min_volatility_pct": .2, "min_volume_ratio": .95, "breakout_buffer_pct": .05}
    result = comparison.evaluate(rows, strategy)
    assert result["variant_buy_labels"] == 1
    assert result["mean_gross_bps"] == pytest.approx((143/140-1)*10000)
    assert result["mean_net_scenario_bps"]["20"] == pytest.approx(result["mean_gross_bps"]-20)
    assert strategy["min_volatility_pct"] == .2
    assert result["candidates"][-1]["gross_bps"] is None


def test_duplicate_rows_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        comparison.evaluate([[0, 1, 1, 1, 1, 1]]*2, {})


@pytest.mark.parametrize("index,value", [(0, 1), (0, -300000), (1, 0),
                                        (1, float("nan")), (2, 90),
                                        (3, -1), (4, float("inf")), (5, -1)])
def test_invalid_candle_rejected(index, value):
    row = [0, 100, 102, 99, 101, 1]
    row[index] = value
    with pytest.raises(ValueError, match="invalid candle"):
        comparison.evaluate([row], {})


def test_gap_restarts_warmup(monkeypatch):
    calls = []
    def signal(**kwargs):
        calls.append(kwargs)
        return {"action": "hold", "reason": "inside_channel",
                "ind": {"close": 100, "upper_prev": 101}}
    monkeypatch.setattr(comparison, "compute_signal", signal)
    rows = [[i*300000, 100, 102, 99, 101, 1] for i in list(range(30))+list(range(31, 61))]
    assert comparison.evaluate(rows, {"breakout_buffer_pct": .05})["filtered_upward_candidates"] == 0
    assert calls == []


@pytest.mark.parametrize("raw", [
    [1790294700.5, 99, 102, 100, 101, 1],
    [1790294700, 99, 102, True, 101, 1],
    [1790294700, 99, 102, 100, 101],
    ["1790294700", 99, 102, 100, 101, 1],
])
def test_raw_ingestion_rejects_coercion(raw):
    with pytest.raises(ValueError, match="invalid raw candle"):
        comparison.normalize_candle(raw)


def test_raw_ingestion_maps_coinbase_columns():
    assert comparison.normalize_candle([300, 99, 102, 100, 101, 1]) == [300000, 100, 102, 99, 101, 1]
