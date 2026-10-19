import pytest
from scripts.research.compare_frozen_strategies import simulate
from scripts.research.compare_frozen_strategies import validate_plan, compare
from services.strategies.presets import PRESETS
from copy import deepcopy


def test_cash_and_flat_round_trip_costs():
    rows = [[i*300000, 100, 101, 99, 100, 1] for i in range(103)]
    actions = ["hold"]*103
    assert simulate(rows, actions, 10)["net_dollars"] == 0
    actions[99], actions[100] = "buy", "sell"
    result = simulate(rows, actions, 10, 0)
    assert result["net_dollars"] == pytest.approx(-.2)
    assert result["closed_trades_including_terminal"] == 1
    assert result["trade_events"][0]["ts"] == rows[100][0]
    assert result["trade_events"][1]["ts"] == rows[101][0]


def test_terminal_exit_and_fee_stress():
    rows = [[i*300000, 100, 110, 99, 110, 1] for i in range(102)]
    actions = ["hold"]*102
    actions[99] = "buy"
    low, high = simulate(rows, actions, 10), simulate(rows, actions, 60)
    assert low["terminal_forced_exit"]
    assert low["net_dollars"] > high["net_dollars"]
    assert len(low["trade_events"]) == 1
    assert "bar_close_and_terminal_liquidation_drawdown_pct" in low


@pytest.mark.parametrize("mutation", ["none", "dates", "cost", "strategy", "disabled"])
def test_plan_enforced(mutation):
    rows = [[i*300000, 100, 101, 99, 100, 1] for i in range(8740)]
    plan = {"start_sec": 0, "end_exclusive_sec": 8740*300,
            "market": "coinbase BTC/USD", "granularity_sec": 300,
            "warmup_bars": 100, "capital": 1000, "entry_notional": 100,
            "fee_bps_per_side": [10,25,60], "slippage_bps_per_side": 5,
            "execution": "next_open_signal_only_with_terminal_liquidation",
            "strategies": {k:deepcopy(PRESETS[k]["strategy"]) for k in
                           ("breakout_default", "ema_cross_default", "mean_reversion_default")}}
    if mutation == "dates": plan["start_sec"] = 300
    if mutation == "cost": plan["slippage_bps_per_side"] = 0
    if mutation == "strategy": plan["strategies"].pop("ema_cross_default")
    if mutation == "disabled": plan["strategies"]["ema_cross_default"]["trade_enabled"] = False
    if mutation == "none":
        validate_plan(rows, plan)
    else:
        with pytest.raises(ValueError): validate_plan(rows, plan)


def test_existing_artifact_preserved(tmp_path):
    report = tmp_path/"comparison.json"
    report.write_text("original")
    with pytest.raises(FileExistsError): compare(tmp_path)
    assert report.read_text() == "original"
