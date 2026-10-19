"""ENTR-CB-1 runner on synthetic data: Coinbase filter timing, exclusions, exit rule, decision rule."""
from datetime import date, timedelta
import json
import sys

import pytest

from scripts.research import run_coinbase_tradable_entrants as cb
from scripts.research import test_low_value_top100 as engine


def row(identity, rank, price, symbol="X"):
    return [identity, symbol, f"asset-{identity}", rank, price, 2e6, 1e9, 10, "2018-01-01", []]


def history(weeks=30, start=date(2018, 12, 2)):
    """Coin 10: always top-100. Coins 20 and 21: outside top 100 until week 9, which is a cycle index."""
    dates = [start + timedelta(days=7 * i) for i in range(weeks)]
    snapshots = []
    for i in range(weeks):
        snap = {10: row(10, 50, 1.0 + 0.01 * i)}
        for coin in (20, 21):
            rank = 150 if i < 9 else 70
            snap[coin] = row(coin, rank, 0.5 * (1 + 0.05 * i) if coin == 20 else 0.3 * (1 + 0.02 * i))
        snapshots.append(snap)
    return dates, snapshots


def listings(**overrides):
    base = {cid: {"status": "mapped", "product": f"C{cid}-USD", "first": date(2015, 1, 1), "last": None}
            for cid in (10, 20, 21)}
    for key, value in overrides.items():
        base[int(key[1:])] = value
    return base


def entrant_cycle_index(dates):
    first = next(i for i, d in enumerate(dates) if d >= date(2019, 1, 1))
    return [k for k, index in enumerate(range(max(4, first), len(dates) - 5, 4)) if index == 9][0]


def test_all_tradable_listing_reproduces_the_unchanged_engine_exactly():
    dates, snaps = history()
    result = cb.run_filtered(dates, snaps, listings())
    reference = engine.run(dates, snaps)
    for arm in cb.ARMS:
        assert result["cb_cycles"][arm] == reference["cycles"][arm]
        for key in ("mean_net_dollars_lower", "median_net_dollars_lower", "funded_cycles", "selections"):
            assert result["cb_summary"][arm][key] == reference["summary"][arm][key]
            assert result["reference_v2_summary"][arm][key] == reference["summary"][arm][key]
    assert result["filter_accounting"]["new_entrants"]["tradable"] == result["filter_accounting"]["new_entrants"]["selections_before_filter"] > 0


def test_listing_must_predate_entry_by_one_day():
    dates, snaps = history()
    k = entrant_cycle_index(dates)
    entry = date.fromisoformat(cb.run_filtered(dates, snaps, listings())["cb_cycles"]["new_entrants"][k]["entry_date"])
    on_entry = listings(c20={"status": "mapped", "product": "C20-USD", "first": entry, "last": None})
    day_before = listings(c20={"status": "mapped", "product": "C20-USD", "first": entry - timedelta(days=1), "last": None})
    removed = cb.run_filtered(dates, snaps, on_entry)
    kept = cb.run_filtered(dates, snaps, day_before)
    assert [m["id"] for m in removed["cb_cycles"]["new_entrants"][k]["members"]] == [21]
    assert removed["filter_accounting"]["new_entrants"]["not_yet_listed"] == 1
    assert [m["id"] for m in kept["cb_cycles"]["new_entrants"][k]["members"]] == [20, 21]


@pytest.mark.parametrize("record,state", [({"status": "never_listed"}, "never_listed"),
                                          ({"status": "unknown"}, "unknown")])
def test_never_listed_and_unknown_are_removed_and_counted_and_survivor_gets_full_allocation(record, state):
    dates, snaps = history()
    k = entrant_cycle_index(dates)
    result = cb.run_filtered(dates, snaps, listings(c20=record))
    members = result["cb_cycles"]["new_entrants"][k]["members"]
    assert [m["id"] for m in members] == [21]
    assert members[0]["allocation"] == 1000
    acc = result["filter_accounting"]["new_entrants"]
    assert acc[state] == 1 and acc["removed_ids"][state] == [20]
    assert 20 not in [m["id"] for c in result["cb_cycles"]["altcoin_control"] for m in c["members"]]


def test_entrant_status_is_computed_before_the_filter():
    dates, snaps = history()
    k = entrant_cycle_index(dates)
    both_removed = cb.run_filtered(dates, snaps, listings(c20={"status": "never_listed"}, c21={"status": "never_listed"}))
    cycle = both_removed["cb_cycles"]["new_entrants"][k]
    assert cycle["selected"] == 0 and cycle["net_dollars_lower"] == 0.0
    assert both_removed["filter_accounting"]["new_entrants"]["selections_before_filter"] == 2


def test_delisted_before_entry_is_not_tradable():
    dates, snaps = history()
    k = entrant_cycle_index(dates)
    gone = listings(c20={"status": "mapped", "product": "C20-USD", "first": date(2015, 1, 1), "last": date(2018, 6, 1)})
    result = cb.run_filtered(dates, snaps, gone)
    assert [m["id"] for m in result["cb_cycles"]["new_entrants"][k]["members"]] == [21]
    assert result["filter_accounting"]["new_entrants"]["delisted_before_entry"] == 1


def test_delisted_before_exit_becomes_unresolved_but_trading_on_exit_day_is_resolved():
    dates, snaps = history()
    k = entrant_cycle_index(dates)
    cyc = cb.run_filtered(dates, snaps, listings())["cb_cycles"]["new_entrants"][k]
    exit_day = date.fromisoformat(cyc["exit_date"])
    early = listings(c20={"status": "mapped", "product": "C20-USD", "first": date(2015, 1, 1), "last": exit_day - timedelta(days=1)})
    on_exit = listings(c20={"status": "mapped", "product": "C20-USD", "first": date(2015, 1, 1), "last": exit_day})
    unresolved = cb.run_filtered(dates, snaps, early)
    member = [m for m in unresolved["cb_cycles"]["new_entrants"][k]["members"] if m["id"] == 20][0]
    assert member["status"] == "UNKNOWN_EXIT_ZERO_RECOVERY_BOUND"
    assert unresolved["filter_accounting"]["new_entrants"]["exits_unresolved_by_delisting"] == 1
    resolved = cb.run_filtered(dates, snaps, on_exit)
    assert [m["status"] for m in resolved["cb_cycles"]["new_entrants"][k]["members"]] == ["MODELLED", "MODELLED"]


def test_selected_id_missing_from_listing_file_refuses():
    dates, snaps = history()
    partial = listings()
    del partial[21]
    with pytest.raises(ValueError, match="lacks selected CMC id 21"):
        cb.run_filtered(dates, snaps, partial)


def _doc(assets):
    return json.dumps({"schema": cb.LISTING_SCHEMA, "assets": assets})


def test_listing_parser_accepts_valid_records():
    parsed = cb.parse_listings(_doc({"20": {"status": "mapped", "product": "ABC-USD", "first_candle": "2021-03-04", "last_candle": None},
                                     "21": {"status": "never_listed"}, "22": {"status": "unknown"}}))
    assert parsed[20]["first"] == date(2021, 3, 4) and parsed[20]["last"] is None
    assert parsed[21] == {"status": "never_listed"} and parsed[22] == {"status": "unknown"}


@pytest.mark.parametrize("raw", [
    json.dumps({"schema": "other", "assets": {}}),
    _doc({"20": {"status": "listed"}}),
    _doc({"20": {"status": "mapped", "product": "ABC-USD", "first_candle": "2021-03-04"}}),
    _doc({"20": {"status": "mapped", "product": "ABC-USD", "first_candle": "2021-03-04", "last_candle": "2020-01-01"}}),
    _doc({"20": {"status": "mapped", "product": "ABC", "first_candle": "2021-03-04", "last_candle": None}}),
    _doc({"20": {"status": "never_listed", "note": "x"}}),
    _doc({"020": {"status": "unknown"}}),
    _doc({"abc": {"status": "unknown"}}),
    '{"schema": "entr-cb1-listings-v1", "assets": {"20": {"status": "mapped", "product": "A-USD", "first_candle": NaN, "last_candle": null}}}',
])
def test_listing_parser_refuses_malformed_documents(raw):
    with pytest.raises(ValueError):
        cb.parse_listings(raw)


def _cycles(values, unresolved=0):
    return [{"net_dollars_lower": v, "unresolved_exits": unresolved} for v in values]


def _decide(values, paired, funded=40, before=100, unknown=0, funded_selections=50, unresolved=0):
    summary = {"funded_cycles": funded, "funded_selections": funded_selections, "unresolved_exits": unresolved}
    accounting = {"selections_before_filter": before, "unknown": unknown}
    return cb.decide(_cycles(values), paired, summary, accounting)


def test_decision_continue_only_when_all_four_conditions_hold():
    assert _decide([10, 20, 30], [5, 5])["verdict"] == "CONTINUE"


@pytest.mark.parametrize("kwargs,verdict", [
    (dict(values=[-10, -20, 5], paired=[5]), "STOP"),                    # c1 fails
    (dict(values=[10, 20, 30], paired=[-5, -1]), "STOP"),                # c3 fails
    (dict(values=[10, 20, 30], paired=[None, None]), "STOP"),            # c3 undefined
    (dict(values=[-5, -5, 100], paired=[5]), "INCONCLUSIVE"),            # only c2 fails
    (dict(values=[10, 20, 30], paired=[5], funded=29), "INCONCLUSIVE"),   # c4 sample
    (dict(values=[10, 20, 30], paired=[5], unknown=11), "INCONCLUSIVE"),  # c4 unknown share 11%
    (dict(values=[10, 20, 30], paired=[5], unresolved=6), "INCONCLUSIVE"),  # c4 unresolved 12%
])
def test_decision_stop_and_inconclusive_branches(kwargs, verdict):
    assert _decide(**kwargs)["verdict"] == verdict


def test_decision_removes_exactly_one_largest_cycle():
    d = _decide([-1, -1, 100, 100], [5])
    assert d["c2_mean_without_largest_cycle_gt_0"]["value"] == pytest.approx(98 / 3)


def test_main_refuses_until_preregistration_is_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(cb, "FROZEN_PREREG_SHA256", None)
    args = ["prog"] + [x for name in ("archive", "input-manifest", "listings", "prereg", "output")
                       for x in (f"--{name}", str(tmp_path / name))] + ["--listings-sha256", "0" * 64]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit, match="not frozen"):
        cb.main()
    assert not (tmp_path / "output").exists()


def test_main_refuses_when_a_pinned_input_differs(monkeypatch, tmp_path):
    prereg = tmp_path / "prereg.md"
    prereg.write_text("frozen\n")
    monkeypatch.setattr(cb, "FROZEN_PREREG_SHA256", "f" * 64)
    args = ["prog", "--archive", str(tmp_path / "a"), "--input-manifest", str(tmp_path / "m"),
            "--listings", str(tmp_path / "l"), "--prereg", str(prereg), "--output", str(tmp_path / "out"),
            "--listings-sha256", "0" * 64]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit, match="pinned input changed"):
        cb.main()
    assert not (tmp_path / "out").exists()
