from datetime import date, timedelta

import pytest

from scripts.research import test_low_value_top100 as study


def row(identity=10, rank=60, price=.5, **updates):
    result = [identity, "X", "asset-x", rank, price, 2e6, 1e9, 10, "2018-01-01", []]
    for key, value in updates.items():
        result[int(key)] = value
    return result


def test_three_groups_are_separate_and_btc_eth_never_selected():
    history = [{10: row(rank=110), 11: row(11, 150, 10)} for _ in range(4)]
    history.append({10: row(), 11: row(11, 60, 10), 1: row(1), 1027: row(1027)})
    choices = study.choose(history, 4)
    assert choices["under_1"] == [10]
    assert choices["ranks_51_100"] == [10, 11]
    assert choices["new_entrants"] == [10, 11]
    assert choices["altcoin_control"] == [10, 11]


def test_missing_history_is_not_an_entrant_and_future_does_not_change_selection():
    history = [{}, {10: row(rank=101)}, {10: row(rank=101)}, {10: row(rank=101)}, {10: row()}]
    before = study.choose(history, 4)
    history.append({10: row(price=100000)})
    assert before == study.choose(history, 4)
    assert before["new_entrants"] == []


@pytest.mark.parametrize("asset", [row(1), row(1027), row(rank=101), row(price=1, **{"7": .1}),
                                   row(**{"9": ["stablecoin"]}), row(**{"5": 999999}),
                                   row(price=float("nan")), row(price=0)])
def test_eligibility_exclusions(asset):
    assert not study.eligible(asset)


def test_fee_inclusive_affordability_and_worst_loss():
    result = study.cycle([10], {10: row()}, {10: row(price=1)}, {10: row(price=1)})
    expected = 1000 / (1.0025 * 1.005) * .9975 * .995 - 1000
    assert result["net_dollars_lower"] == pytest.approx(expected)
    assert result["gross_dollars"] == 0
    loss = study.cycle([10], {10: row()}, {10: row(price=1)}, {10: row(price=.01)})
    assert -1000 < loss["net_dollars_lower"] < -990


def test_missing_entry_stays_cash_without_redistribution_and_unknown_exit_retained():
    selection = {10: row(), 11: row(11)}
    result = study.cycle([10, 11], selection, {10: row(price=1)}, {10: row(price=2)})
    assert result["missing_entries"] == 1
    assert result["net_dollars_lower"] == pytest.approx(500 * (study.terminal_multiple(1, 2, .005, .0025) - 1))
    unknown = study.cycle([10], selection, {10: row(price=1)}, {})
    assert unknown["unresolved_exits"] == 1
    assert unknown["net_dollars_lower"] == -1000
    assert "UNKNOWN" in unknown["members"][0]["status"]


def test_same_ticker_different_id_is_not_a_price_match():
    result = study.cycle([10], {10: row()}, {11: row(11, price=10)}, {11: row(11, price=100)})
    assert result["missing_entries"] == 1
    assert result["net_dollars_lower"] == 0


def test_empty_group_is_cash():
    result = study.cycle([], {}, {}, {})
    assert result["net_dollars_lower"] == 0 and result["members"] == []
    assert study.describe([]) == {"cycles": 0, "point_status": "NO_CYCLES"}


def test_next_snapshot_entry_and_four_week_exit_not_selection_price():
    dates = [date(2018, 12, 2) + timedelta(days=7 * i) for i in range(215)]
    snapshots = [{10: row(price=.5)} for _ in dates]
    first = next(i for i, d in enumerate(dates) if d >= date(2019, 1, 1))
    snapshots[first + 1] = {10: row(price=1)}
    snapshots[first + 5] = {10: row(price=2)}
    result = study.run(dates, snapshots)
    first_cycle = result["cycles"]["under_1"][0]
    assert first_cycle["members"][0]["entry"] == 1
    assert first_cycle["members"][0]["exit"] == 2
    assert first_cycle["gross_dollars"] == 1000
    next_cycle = result["cycles"]["under_1"][1]
    assert first_cycle["exit_date"] == next_cycle["entry_date"]


def test_bootstrap_deterministic_and_simultaneous_interval_no_narrower():
    data = [None if i % 8 == 0 else float(i - 15) for i in range(32)]
    result = study.interval(data)
    assert result == study.interval(data)
    assert result["paired_cycles"] == 28
    assert result["simultaneous_ci"][0] <= result["ci95"][0]
    assert result["simultaneous_ci"][1] >= result["ci95"][1]
