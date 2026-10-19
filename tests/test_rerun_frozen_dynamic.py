import json

import pytest

from scripts.research.rerun_frozen_dynamic import Book, merge


def make_ns(opens, closes, marks):
    T = [i * 3600 for i in range(len(opens))]
    return {"T": T, "OPEN": {"X": opens}, "ACTUAL_CLOSE": {"X": closes}, "mark": lambda pid, i: marks[i]}


def test_buy_fills_at_decision_hour_open_not_last_close():
    ns = make_ns([None, 110.0, 110.0], [100.0, 120.0, 120.0], [100.0, 100.0, 120.0])
    b = Book(ns, 0.0, "strict")
    b.buy("X", 100.0, 1)            # decision mark is 100 (last close); first tradable price is the 110 open
    assert b.pos["X"]["q"] == pytest.approx(100.0 / (110.0 * 1.001))


def test_buy_without_bar_is_skipped_not_filled_at_stale_price():
    ns = make_ns([None, None], [100.0, None], [100.0, 100.0])
    b = Book(ns, 0.0, "strict")
    b.buy("X", 100.0, 1)
    assert "X" not in b.pos and b.entries_skipped == 1 and b.cash == 1000.0


def test_sale_without_bar_is_deferred_to_next_observed_open():
    ns = make_ns([100.0, None, 90.0], [100.0, None, 90.0], [100.0, 100.0, 100.0])
    b = Book(ns, 0.0, "outage")
    b.buy("X", 100.0, 0)
    assert b.sell("X", 1, "time_stop") is False and "X" in b.pos
    assert b.start_hour(2) is True and "X" not in b.pos
    assert b.trades[0]["ret"] == pytest.approx(90 * 0.999 / (100 * 1.001) - 1)


def test_strict_mode_stops_when_held_coin_has_no_bar():
    ns = make_ns([100.0, None], [100.0, None], [100.0, 100.0])
    b = Book(ns, 0.0, "strict")
    b.buy("X", 100.0, 0)
    assert b.start_hour(1) is False and b.status == "INCOMPLETE"


def test_nav_unknown_when_held_coin_has_no_close_not_forward_filled():
    ns = make_ns([100.0, None], [100.0, None], [100.0, 100.0])
    b = Book(ns, 0.0, "outage")
    b.buy("X", 100.0, 0); b.end_hour(0); b.end_hour(1)
    assert b.nav[0][1] is not None and b.nav[1][1] is None


def _part(tmp_path, name, script="a", results=None):
    d = {"artifact_type": "t", "not_promotion_evidence": True, "not_independent_holdout": True, "script_sha256": script,
         "shared_math_sha256": "m", "original_source_sha256": {"s": "1"}, "input_sha256": {"i": "2"},
         "results": results or {name: {"status": "COMPLETE"}}}
    (tmp_path / f"out.json.part.{name}.json").write_text(json.dumps(d))


def test_merge_keeps_every_part(tmp_path):
    _part(tmp_path, "a"); _part(tmp_path, "b")
    m = merge(str(tmp_path / "out.json"))
    assert set(m["results"]) == {"a", "b"} and len(m["parts"]) == 2


def test_merge_refuses_mixed_script_hashes(tmp_path):
    _part(tmp_path, "a", "x"); _part(tmp_path, "b", "y")
    with pytest.raises(SystemExit):
        merge(str(tmp_path / "out.json"))


def test_merge_refuses_duplicate_result_keys(tmp_path):
    _part(tmp_path, "a", results={"k": {}}); _part(tmp_path, "b", results={"k": {}})
    with pytest.raises(SystemExit):
        merge(str(tmp_path / "out.json"))


@pytest.mark.parametrize("manifest", ["original_source_sha256", "input_sha256"])
def test_merge_refuses_conflicting_manifests(tmp_path, manifest):
    _part(tmp_path, "a"); _part(tmp_path, "b")
    path = tmp_path / "out.json.part.b.json"
    data = json.loads(path.read_text())
    key = next(iter(data[manifest]))
    data[manifest][key] = "conflicting"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="conflicting"):
        merge(str(tmp_path / "out.json"))
    assert not (tmp_path / "out.json").exists()


def test_merge_preserves_existing_output(tmp_path):
    _part(tmp_path, "a")
    output = tmp_path / "out.json"
    output.write_text("original")
    with pytest.raises(FileExistsError):
        merge(str(output))
    assert output.read_text() == "original"


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf"), 0.0])
def test_unknown_holding_blocks_buys_but_not_protective_sales(missing):
    ns = make_ns([100.0, missing, 90.0], [100.0, None, 90.0], [100.0]*3)
    ns["OPEN"]["Y"] = [100.0]*3
    ns["ACTUAL_CLOSE"]["Y"] = [100.0]*3
    b = Book(ns, 0.0, "outage")
    b.buy("X", 100.0, 0)
    b.buy("Y", 100.0, 1)
    assert "Y" not in b.pos and b.entries_skipped == 1
    b.buy("Y", 100.0, 2)
    assert "Y" in b.pos
    assert b.sell("X", 2, "protective") is True
