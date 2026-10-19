import shutil

import pytest

from scripts.research import run_cmc_confirmation_v4 as v4


def valid():
    return {"model": "iid", "days": 90, "mean_index": 0, "mean": 0.,
            "identity": {}, "stage": v4.ref.CONFIRM_STAGE, "histories": 1000,
            "status_counts": {"AVAILABLE": 1000}, "positives": 0}


def test_valid_cell():
    assert v4.validate(valid(), {}) == ("iid", 90, 0)


@pytest.mark.parametrize("key,value", [("positives", True), ("positives", 1001),
                                     ("histories", 999), ("mean", float("nan")),
                                     ("identity", {"changed": True}), ("days", True),
                                     ("stage", v4.ref.STAGE)])
def test_invalid_cell_refuses(key, value):
    p = valid()
    p[key] = value
    with pytest.raises(ValueError):
        v4.validate(p, {})


def test_incomplete_summary_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(v4.ref, "OUT", tmp_path)
    monkeypatch.setattr(v4, "context", lambda: ({}, {}))
    with pytest.raises(ValueError, match="incomplete_confirmation_grid"):
        v4.summarize()


def test_misnamed_saved_cell_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(v4.ref, "OUT", tmp_path)
    v4.ref.write_new(tmp_path / "confirmation" / "wrong.json", valid())
    with pytest.raises(ValueError, match="misnamed"):
        v4.parts({})


def test_acceptance_required_before_generation(tmp_path, monkeypatch):
    source = v4.ref.OUT
    shutil.copytree(source / "reference", tmp_path / "reference")
    shutil.copyfile(source / "lock_v4.json", tmp_path / "lock_v4.json")
    monkeypatch.setattr(v4.ref, "OUT", tmp_path)
    with pytest.raises(FileNotFoundError, match="confirmation_review_accepted"):
        v4.context()
