import copy
import pytest
from scripts.research.merge_frozen_altcoin_results import GROUPS, merge


def parts():
    return {g: {"script_sha256": "a", "shared_math_sha256": "b", "original_source_sha256": {},
                "results": {g: {"value": 1}}, "input_sha256": {"same": {"file": "hash"}}} for g in GROUPS}


def test_recovery_preserved_and_inputs_unmodified():
    items = parts()
    before = copy.deepcopy(items)
    assert set(merge(items)["results"]) == set(GROUPS)
    assert items == before


@pytest.mark.parametrize("change", ["source", "input", "duplicate"])
def test_conflicts_refused(change):
    items = parts()
    if change == "source":
        items["ideas"]["shared_math_sha256"] = "changed"
    elif change == "input":
        items["ideas"]["input_sha256"]["same"]["file"] = "changed"
    else:
        items["ideas"]["results"] = {"recovery": {}}
    with pytest.raises(ValueError):
        merge(items)
