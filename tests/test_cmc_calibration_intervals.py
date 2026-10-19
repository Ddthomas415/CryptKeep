import numpy as np
import pytest
from scripts.research.cmc_calibration_models import generate
from scripts.research.cmc_calibration_intervals import METHODS, interval


def test_constant_returns_and_seed_reproducibility():
    history = generate("development", "iid", 180, 0, 0)
    history["truth"][:] = .02
    for method in METHODS:
        result = interval(history, method, 42, repeats=100)
        assert result == interval(history, method, 42, repeats=100)
        assert result["p05"] == pytest.approx(.02)
        assert result["p95"] == pytest.approx(.02)


def test_short_block_method_is_unavailable_not_positive():
    history = generate("development", "iid", 90, 0, 0)
    assert interval(history, "block56", 42)["status"] == "INSUFFICIENT_DAYS"


def test_refusal_and_missingness_not_survivor_inference():
    for model in ("sparse", "random_missing", "loss_missing"):
        history = generate("development", model, 180, 0, 0)
        for method in METHODS:
            assert interval(history, method, 42)["status"] == "REFUSED_UNSUPPORTED_MODEL"
    history = generate("development", "iid", 180, 0, 0)
    history["observed"][0] = False
    assert interval(history, "entry_day", 42)["status"] == "REFUSED_MISSING_OUTCOMES"


def test_unequal_event_weighting_and_noncircular_block_reference():
    history = generate("development", "shared_unequal", 180, 0, 0)
    result = interval(history, "block28", 42, repeats=100)
    assert result["mean"] == pytest.approx(history["truth"].mean())
    totals = np.bincount(history["day_index"], weights=history["truth"], minlength=180)
    counts = np.bincount(history["day_index"], minlength=180)
    starts = np.random.Generator(np.random.PCG64(42)).integers(0,153,size=(100,7))
    samples = []
    for row in starts:
        days = [day for start in row for day in range(start,start+28)][:180]
        samples.append(totals[days].sum()/counts[days].sum())
    samples.sort()
    assert result["p05"] == pytest.approx(samples[5])
    assert result["p95"] == pytest.approx(samples[95])
