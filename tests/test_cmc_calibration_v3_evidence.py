import json

import pytest

from scripts.research import run_cmc_calibration_v3 as runner


def part(model="iid", days=90, mi=0):
    return {"model": model, "days": days, "mean_index": mi, "mean": runner.v3.MEANS[mi],
            "lock_sha256": "lock", "histories": 1000, "positives": 0,
            "status_counts": {"AVAILABLE": 1000}}


def test_part_identity_and_counters_fail_closed():
    assert runner.validate_part(part(), "lock") == ("iid", 90, 0)
    changes = [{"lock_sha256": "other"}, {"histories": True}, {"histories": 999},
               {"days": True}, {"mean_index": True}, {"model": "unknown"}, {"mean": float("nan")},
               {"mean": True}, {"positives": -1}, {"positives": True}, {"positives": 1001},
               {"status_counts": {}}, {"status_counts": {"AVAILABLE": True}},
               {"status_counts": {"AVAILABLE": 999}}, {"status_counts": {"OTHER": 1000}}]
    for delta in changes:
        with pytest.raises(ValueError):
            runner.validate_part({**part(), **delta}, "lock")
    with pytest.raises(ValueError):
        runner.validate_part(part(), "lock", ("iid", 180, 0))


def setup_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "OUT", tmp_path)
    identity = {"source": "fixed", "numpy_version": "test"}
    monkeypatch.setattr(runner, "experiment_identity", lambda: identity)
    lock = {"locked_method": runner.v3.METHODS[1], "identity": identity,
            "locked_before_confirmation": True}
    (tmp_path / "lock_v3.json").write_text(json.dumps(lock))
    (tmp_path / "review_accepted_v3.json").write_text(json.dumps({
        "lock_sha256": runner.sha(tmp_path / "lock_v3.json"), "identity": identity,
        "status": "ACCEPTED_WITH_RISK"}))
    return lock


def test_old_or_changed_lock_is_refused(tmp_path, monkeypatch):
    lock = setup_lock(tmp_path, monkeypatch)
    assert runner.validated_lock() == lock
    for change in ({"identity": {}}, {"locked_before_confirmation": False}, {"locked_method": "unknown"}):
        (tmp_path / "lock_v3.json").write_text(json.dumps({**lock, **change}))
        with pytest.raises(ValueError):
            runner.validated_lock()


def test_108_duplicate_cells_cannot_certify(tmp_path, monkeypatch):
    setup_lock(tmp_path, monkeypatch)
    lock_hash = runner.sha(tmp_path / "lock_v3.json")
    directory = tmp_path / "confirmation"
    directory.mkdir()
    for i in range(108):
        (directory / f"{i}.json").write_text(json.dumps({**part(), "lock_sha256": lock_hash}))
    with pytest.raises(ValueError, match="duplicate"):
        runner.summarize()
    assert not (tmp_path / "confirmation_summary_v3.json").exists()


def test_exact_grid_and_refusal_cells_required(tmp_path, monkeypatch):
    setup_lock(tmp_path, monkeypatch)
    lock_hash = runner.sha(tmp_path / "lock_v3.json")
    directory = tmp_path / "confirmation"
    directory.mkdir()
    for model, days, mi in runner.EXPECTED_CELLS:
        p = part(model, days, mi)
        p["lock_sha256"] = lock_hash
        if model not in runner.v3.SUPPORTED:
            p["status_counts"] = {"REFUSED": 1000}
        (directory / f"{model}_{days}_{mi}.json").write_text(json.dumps(p))
    result = runner.summarize()
    assert result["result"] == "SIZE_TOLERANCE_MET_POINTWISE"
    assert len(result["size_cells"]) == 18 and len(result["refusal_cells"]) == 36


def test_resume_checks_acceptance_and_existing_cell_before_generation(tmp_path, monkeypatch):
    lock = setup_lock(tmp_path, monkeypatch)
    lock_hash = runner.sha(tmp_path / "lock_v3.json")
    acceptance = {"lock_sha256": lock_hash, "identity": lock["identity"], "status": "ACCEPTED_WITH_RISK"}
    acceptance_path = tmp_path / "review_accepted_v3.json"
    acceptance_path.write_text(json.dumps({**acceptance, "lock_sha256": "wrong"}))
    monkeypatch.setattr(runner.v3, "evaluate", lambda *args: pytest.fail("must not generate"))
    with pytest.raises(ValueError, match="acceptance"):
        runner.confirm(1)
    acceptance_path.write_text(json.dumps(acceptance))
    directory = tmp_path / "confirmation"
    directory.mkdir()
    (directory / "iid_90_0.json").write_text(json.dumps({**part(), "lock_sha256": "wrong"}))
    with pytest.raises(ValueError, match="mismatch"):
        runner.confirm(1)
