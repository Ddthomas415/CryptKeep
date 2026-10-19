import pytest
from scripts.research.report_breakout_segments import attribute


def test_segments_add_to_total_without_reset():
    result = attribute([{"hour": 4, "equity": 1200}], 5, 1500)
    assert result["earlier_dollar_change"] == 200
    assert result["later_dollar_change"] == 300
    assert result["later_return_on_carried_equity"] == pytest.approx(.25)


def test_unknown_boundary_not_filled_from_neighbor():
    assert attribute([{"hour": 3, "equity": 1200}, {"hour": 4, "equity": None}], 5, 1500)["status"] == "INCOMPLETE"
