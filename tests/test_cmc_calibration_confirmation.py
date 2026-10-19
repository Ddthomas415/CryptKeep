import pytest
from scripts.research.run_cmc_calibration_confirmation import evaluate_chunk, verify_lock, validate_counts, REQUIRED_SOURCES


def test_confirmation_refusal_preserves_all_trial_denominators():
    assert evaluate_chunk("loss_missing", 90, 0, 0, size=3) == {
        "positive": 0, "unavailable": 3, "refused": 3}


def test_lock_rejects_method_change_and_source_mismatch(tmp_path):
    with pytest.raises(ValueError, match="method lock"):
        verify_lock({"method": "entry_day"})
    path = tmp_path/"source.py"
    path.write_text("original")
    with pytest.raises(ValueError, match="manifest"):
        verify_lock({"method": "block28", "confirmation_started": False,
                     "source_hashes": {str(path): "wrong"}})


def test_empty_manifest_and_invalid_checkpoint_counts_rejected():
    with pytest.raises(ValueError, match="manifest"):
        verify_lock({"method": "block28", "confirmation_started": False, "source_hashes": {}})
    for counts in ({"positive": True, "unavailable": 0, "refused": 0},
                   {"positive": 90, "unavailable": 20, "refused": 0},
                   {"positive": 0, "unavailable": 10, "refused": 11}):
        with pytest.raises(ValueError):
            validate_counts(counts)


def test_runtime_version_mismatch_rejected_before_resume():
    with pytest.raises(ValueError, match="NumPy"):
        verify_lock({"method": "block28", "confirmation_started": False,
                     "source_hashes": dict.fromkeys(REQUIRED_SOURCES, "unused"),
                     "numpy_version": "different"})
