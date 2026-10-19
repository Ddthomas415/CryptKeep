import numpy as np
import pytest
from scripts.research.cmc_calibration_models import MODELS, generate, stream_seed


def test_all_models_reproducible_finite_and_ordered():
    for model in MODELS:
        a = generate("development", model, 90, 0, 0)
        b = generate("development", model, 90, 0, 0)
        assert np.array_equal(a["truth"], b["truth"])
        assert np.isfinite(a["truth"]).all()
        assert np.all(np.diff(a["day_index"]) >= 0)
        assert a["observed"].shape == a["truth"].shape
        assert a["refusal_only"] == (model in MODELS[6:])


def test_stream_and_stage_separation():
    assert len({stream_seed(s, "iid", 90, 0, 0, r)
                for s in ("development", "confirmation")
                for r in ("innovations", "bootstrap", "heavy_tail_denominator")}) == 6
    with pytest.raises(ValueError):
        stream_seed("unknown", "iid", 90, 0, 0, "bootstrap")


def test_event_counts_and_missingness_preserve_truth():
    unequal = generate("development", "shared_unequal", 90, 0, 0)
    assert len(unequal["truth"]) == 109
    assert np.count_nonzero(unequal["day_index"] == 45) == 20
    sparse = generate("development", "sparse", 90, 0, 0)
    assert 0 < len(sparse["truth"]) < 90
    for model in ("random_missing", "loss_missing"):
        result = generate("development", model, 90, 0, 0)
        assert len(result["truth"]) == 90
        assert 0 < result["observed"].sum() < 90
