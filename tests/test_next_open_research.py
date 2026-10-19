from copy import deepcopy
import sys

import pytest

from services.backtest.next_open_research import run_frozen_segment, simulate_next_open, validate_bars


def bars():
    return [[i*3600000, 100., 110., 90., 100., 1.] for i in range(5)]


def test_next_open_and_two_leg_fees():
    rows = bars()
    rows[1] = [3600000, 200., 210., 190., 200., 1.]
    result = simulate_next_open(rows, ["buy", "sell", "hold", "hold", "hold"],
                                start_index=1, interval_ms=3600000, fee_bps=10, slippage_bps=0)
    assert result["trades"][0]["price"] == 200.
    assert result["trades"][0]["ts_ms"] == rows[1][0]
    assert result["trades"][0]["qty"] == .5
    assert result["net_quote_profit"] == pytest.approx(-50.15)
    assert result["fees_quote"] == pytest.approx(.15)


def test_flat_round_trip_costs_and_terminal_exit():
    result = simulate_next_open(bars(), ["buy", "hold", "hold", "hold", "buy"],
                                start_index=1, interval_ms=3600000, fee_bps=10, slippage_bps=0)
    assert result["net_quote_profit"] == pytest.approx(-.2)
    assert result["closed_cycles"] == 1
    assert result["terminal_liquidation"]
    assert result["trades"][-1]["ts_ms"] == 5*3600000
    assert result["trades"][-1]["terminal"]
    assert result["terminal_equity_quote"] == result["final_cash_quote"]


def test_cash_and_fixed_size_refusal():
    actions = ["hold"]*5
    assert simulate_next_open(bars(), actions, start_index=1, interval_ms=3600000)["net_quote_profit"] == 0
    actions[0] = "buy"
    result = simulate_next_open(bars(), actions, start_index=1, interval_ms=3600000,
                                initial_cash=100, entry_notional=100, fee_bps=10)
    assert result["trades"] == []
    assert result["refused_entries_insufficient_cash"] == 1


@pytest.mark.parametrize("mutation", ["gap", "duplicate", "reverse", "nan", "negative", "bounds", "timestamp", "bool"])
def test_invalid_archive_refused(mutation):
    rows = bars()
    if mutation == "gap": rows.pop(2)
    if mutation == "duplicate": rows[2][0] = rows[1][0]
    if mutation == "reverse": rows.reverse()
    if mutation == "nan": rows[2][4] = float("nan")
    if mutation == "negative": rows[2][5] = -1
    if mutation == "bounds": rows[2][2] = 99
    if mutation == "timestamp": rows[2][0] += 1
    if mutation == "bool": rows[2][1] = True
    with pytest.raises(ValueError): validate_bars(rows, interval_ms=3600000)


def test_no_future_signal_input_or_mutation():
    rows, seen = bars(), []
    original = deepcopy(rows)
    strategy = {"name":"ema_cross", "trade_enabled":True}
    def signal(**kw):
        seen.append([r[0] for r in kw["ohlcv"]])
        assert kw["cfg"]["strategy"]["emit_evidence"] is False
        kw["ohlcv"][0][1] = 999
        return {"ok":True, "action":"buy" if len(seen)==1 else "hold"}
    result = run_frozen_segment(rows, strategy=strategy, symbol="BTC/USDT",
                                start_index=2, interval_ms=3600000, signal_fn=signal)
    assert seen[0] == [rows[0][0], rows[1][0]]
    assert seen[-1][-1] == rows[-2][0]
    assert result["trades"][0]["ts_ms"] == rows[2][0]
    assert rows == original and "emit_evidence" not in strategy


@pytest.mark.parametrize("cost,value", [("fee_bps", -1), ("slippage_bps", 10000), ("initial_cash", True)])
def test_invalid_costs(cost, value):
    with pytest.raises(ValueError):
        simulate_next_open(bars(), ["hold"]*5, start_index=1, interval_ms=3600000, **{cost:value})


def test_strategy_and_dataset_hashes_change():
    args = dict(symbol="BTC/USDT", start_index=1, interval_ms=3600000,
                signal_fn=lambda **kw: {"ok":True,"action":"hold"})
    a = run_frozen_segment(bars(), strategy={"name":"ema_cross","ema_fast":12}, **args)
    b = run_frozen_segment(bars(), strategy={"name":"ema_cross","ema_fast":13}, **args)
    assert a["strategy_config_sha256"] != b["strategy_config_sha256"]
    rows = bars()
    rows[-1][5] = 2.
    c = run_frozen_segment(rows, strategy={"name":"ema_cross","ema_fast":12}, **args)
    assert a["dataset_sha256"] != c["dataset_sha256"]


@pytest.mark.parametrize("price,entry", [
    (sys.float_info.max, 100.),
    (sys.float_info.max, 5e-324),
    (5e-324, 100.),
])
def test_overflow_or_zero_quantity_refused(price, entry):
    rows = [[i*3600000, price, price, price, price, 1.] for i in range(5)]
    with pytest.raises(ValueError):
        simulate_next_open(rows, ["buy", "hold", "hold", "hold", "hold"],
                           start_index=1, interval_ms=3600000, entry_notional=entry,
                           slippage_bps=5 if entry == 100. else 0)


def test_equity_overflow_refused():
    rows = bars()
    rows[1] = [3600000, .01, .01, .01, .01, 1.]
    rows[2] = [2*3600000, sys.float_info.max, sys.float_info.max,
               sys.float_info.max, sys.float_info.max, 1.]
    with pytest.raises(ValueError):
        simulate_next_open(rows, ["buy", "hold", "hold", "hold", "hold"],
                           start_index=1, interval_ms=3600000, slippage_bps=0)


def test_terminal_sell_underflow_refused():
    rows = [[i*3600000, sys.float_info.max, sys.float_info.max,
             sys.float_info.max, sys.float_info.max, 1.] for i in range(4)]
    rows[-1] = [3*3600000, 5e-324, 5e-324, 5e-324, 5e-324, 1.]
    with pytest.raises(ValueError, match="invalid_numeric_range"):
        simulate_next_open(rows, ["buy", "hold", "hold", "hold"],
                           start_index=1, interval_ms=3600000, slippage_bps=0)


@pytest.mark.parametrize("preset", ["breakout_default", "ema_cross_default", "mean_reversion_default"])
def test_registered_presets_through_real_registry(preset):
    from services.strategies.presets import PRESETS
    rows = [[i*3600000, 100., 110., 90., 100., 1.] for i in range(310)]
    result = run_frozen_segment(rows, strategy=deepcopy(PRESETS[preset]["strategy"]),
                                symbol="BTC/USDT", start_index=300, interval_ms=3600000)
    assert len(result["equity"]) == 10
    assert result["qualification"] == "MODELLED_EXPLORATORY_NOT_PROMOTION_EVIDENCE"
