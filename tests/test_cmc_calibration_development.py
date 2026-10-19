from scripts.research.run_cmc_calibration_development import select_method


def test_unavailable_method_filtered_before_ranking():
    cell = {"methods": {"entry_day": {"available": 10, "positive": 3},
                        "block28": {"available": 10, "positive": 2},
                        "block56": {"available": 0, "positive": 0}}}
    assert select_method([cell]) == "block28"


def test_tie_preference_and_no_available_method():
    cell = {"methods": {m: {"available": 10, "positive": 2}
                        for m in ("entry_day", "block28", "block56")}}
    assert select_method([cell]) == "block56"
    for value in cell["methods"].values():
        value["available"] = 0
    assert select_method([cell]) == "NO_METHOD_LOCKED"
