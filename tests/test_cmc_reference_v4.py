import pytest

from scripts.research import run_cmc_reference_v4 as v4


def part():
    return {"model": "iid", "days": 90, "stage": v4.STAGE,
            "histories": 1000, "identity": {"test": True}, "null_means": [0.01]*1000}


def test_exact_reference_contract():
    assert v4.validate_part(part(), "iid", 90, {"test": True}) == 0.01


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "0.1"])
def test_invalid_means_refuse(value):
    p = part()
    p["null_means"][0] = value
    with pytest.raises(ValueError):
        v4.validate_part(p, "iid", 90, {"test": True})


def test_wrong_identity_and_incomplete_count_refuse():
    with pytest.raises(ValueError):
        v4.validate_part(part(), "iid", 90, {})
    p = part()
    p["null_means"].pop()
    with pytest.raises(ValueError):
        v4.validate_part(p, "iid", 90, {"test": True})


def test_preserve_existing_output(tmp_path):
    path = tmp_path / "receipt.json"
    v4.write_new(path, {"original": True})
    with pytest.raises(FileExistsError):
        v4.write_new(path, {"original": False})


def test_seed_streams_separate():
    stages = ("v3_development", "v3_confirmation", v4.STAGE, v4.CONFIRM_STAGE)
    seeds = [v4.models.stream_seed(s, "iid", 90, 0, 0, "innovations", allowed=stages)
             for s in stages]
    assert len(set(seeds)) == 4


def test_unexpected_resume_file_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "OUT", tmp_path)
    monkeypatch.setattr(v4, "identity", lambda: {"test": True})
    v4.write_new(tmp_path / "reference" / "unexpected.json", part())
    with pytest.raises(ValueError, match="unexpected_reference_file"):
        v4.build()


def test_budget_bounds():
    for kw in ({"max_cells": 0}, {"max_cells": True}, {"budget_seconds": 121}):
        with pytest.raises(ValueError):
            v4.build(**kw)
