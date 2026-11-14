"""DRAFT tests for the BA-51 record-only fix (Claude, 2026-11-14). NOT in tests/; Codex copies after applying
PROPOSED_PATCH.md. Reuses the fixtures of tests/test_group_b_weekly_selection.py (selection, reseal, NOW).
Before the patch: test 1 fails (selection_identity_or_week); tests 2-3 pass. After: all pass."""
import pytest

from services.market_data import group_b_selection as g
from tests.test_group_b_weekly_selection import NOW, reseal, selection


def test_published_artifact_survives_a_later_producer_edit(monkeypatch):
    # BA-51: the file was produced by the code identity recorded inside it; a later edit to a producer file
    # must not make the already-published week unreadable.
    artifact = selection()
    assert g.validate_selection(artifact, now=NOW) is artifact
    changed = {name: "f" * 64 for name in g.PRODUCER_FILES}
    monkeypatch.setattr(g, "producer_identity", lambda: changed)
    assert g.validate_selection(artifact, now=NOW) is artifact


@pytest.mark.parametrize("bad", [
    None,
    {},
    {name: "f" * 64 for name in list(g.PRODUCER_FILES)[:-1]},            # a file missing
    {**{name: "f" * 64 for name in g.PRODUCER_FILES}, "extra": "f" * 64},  # an extra file
    {name: "F" * 64 for name in g.PRODUCER_FILES},                        # not lowercase hex
    {name: "f" * 63 for name in g.PRODUCER_FILES},                        # wrong length
    {name: 1 for name in g.PRODUCER_FILES},                               # not a string
])
def test_missing_or_malformed_producer_code_is_refused(bad):
    artifact = selection()
    if bad is None:
        artifact.pop("producer_code")
    else:
        artifact["producer_code"] = bad
    with pytest.raises(ValueError, match="selection_identity_or_week"):
        g.validate_selection(reseal(artifact), now=NOW)


def test_build_still_records_the_current_producer_identity():
    artifact = selection()
    assert artifact["producer_code"] == g.producer_identity()
    assert set(artifact["producer_code"]) == set(g.PRODUCER_FILES)
