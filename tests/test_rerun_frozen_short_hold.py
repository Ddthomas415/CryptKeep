import pytest

from scripts.research.rerun_frozen_short_hold import Book


def make_ns(opens, closes, marks):
    return {"T": [i * 3600 for i in range(len(opens))], "OPEN": {"X": opens, "Y": [100.0] * len(opens)},
            "ACTUAL_CLOSE": {"X": closes, "Y": [100.0] * len(opens)}, "mark": lambda pid, i: marks[i]}


def test_fill_is_decision_hour_open():
    b = Book(make_ns([None, 120.0], [100.0, 120.0], [100.0, 100.0]), 0.0, "strict")
    b.buy("X", 100.0, 1)
    assert b.pos["X"]["q"] == pytest.approx(100.0 / (120.0 * 1.001))


def test_sale_without_bar_deferred_then_filled():
    b = Book(make_ns([100.0, None, 80.0], [100.0, None, 80.0], [100.0] * 3), 0.0, "outage")
    b.buy("X", 100.0, 0)
    assert b.sell("X", 1, "rotated_out") is False
    b.start_hour(2)
    assert "X" not in b.pos and b.tr[0]["ret"] == pytest.approx(80 * 0.999 / (100 * 1.001) - 1)


def test_strict_stops_on_held_missing_bar():
    b = Book(make_ns([100.0, None], [100.0, None], [100.0, 100.0]), 0.0, "strict")
    b.buy("X", 100.0, 0)
    assert b.start_hour(1) is False and b.status == "INCOMPLETE"


def test_no_new_buy_while_held_coin_lacks_bar():
    b = Book(make_ns([100.0, None], [100.0, None], [100.0, 100.0]), 0.0, "outage")
    b.buy("X", 100.0, 0); b.buy("Y", 100.0, 1)
    assert "Y" not in b.pos and b.entries_skipped == 1


def test_nav_unknown_not_forward_filled():
    b = Book(make_ns([100.0, None], [100.0, None], [100.0, 100.0]), 0.0, "outage")
    b.buy("X", 100.0, 0); b.end_hour(0); b.end_hour(1)
    assert b.nav[0] is not None and b.nav[1] is None
