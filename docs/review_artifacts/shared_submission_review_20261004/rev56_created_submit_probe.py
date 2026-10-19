"""Run only as an isolated candidate test, with the supplied fake venue fixture."""
import pytest
from tests.test_live_submit_ambiguous_classification import rig
from services.execution._executor_submit import _submit_may_have_reached_venue


def test_a_created_row_after_interrupted_submit_is_not_proof_of_never_sent(rig):
    venue, submit, dedupe = rig
    venue.fail_with = KeyboardInterrupt("process interrupted after venue acceptance")
    with pytest.raises(KeyboardInterrupt):
        submit()
    assert len(venue.orders) == 1
    row = dedupe.get_by_intent("binance", "intent-1")
    assert row["status"] == "created"
    assert _submit_may_have_reached_venue(dedupe, "binance", "intent-1"), (
        "created dedupe state is not evidence that the request was never sent"
    )
