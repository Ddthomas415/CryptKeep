import math

import numpy as np
import pytest

from scripts.research import cmc_calibration_models as v2
from scripts.research import cmc_calibration_v3 as v3


def test_generator_is_verbatim_v2_under_a_v2_stage():
    for model in v3.MODELS:
        a = v2.generate("development", model, 90, 2, 3)
        b = v3.generate("development", model, 90, 2, 3, allowed=("development",))
        for key in ("day_index", "truth", "observed"):
            assert np.array_equal(a[key], b[key])


def test_new_stage_labels_give_new_seeds():
    assert v3.stream_seed("v3_confirmation", "iid", 90, 0, 0, "innovations") != \
        v2.stream_seed("confirmation", "iid", 90, 0, 0, "innovations")
    with pytest.raises(ValueError):
        v3.generate("confirmation", "iid", 90, 0, 0)  # v2 labels refused by default


def test_t_quantiles_match_tables():
    assert abs(v3.t_quantile_95(9)-1.8331) < 1e-3 and abs(v3.t_quantile_95(51)-1.6753) < 1e-3


def test_refusal_only_models_refuse():
    for model in ("sparse", "random_missing", "loss_missing"):
        for method in v3.METHODS:
            assert v3.evaluate(method, "v3_development", model, 90, 0, 0)["status"] == "REFUSED"


def test_day_weighting_counts_each_day_once():
    h = {"refusal_only": False, "days": 2, "day_index": np.array([0]*20+[1]),
         "truth": np.array([.5]*20+[-.01]), "observed": np.ones(21, dtype=bool)}
    assert np.allclose(v3.day_series(h), [.5, -.01])


def test_methods_detect_large_effect_and_not_strong_negative():
    for method in v3.METHODS:
        assert v3.evaluate(method, "v3_development", "iid", 365, 3, 1)["positive"] is True
    y = np.full(365, -.01) + np.random.default_rng(1).normal(0, .001, 365)
    assert v3.method_A(y)["lower"] < 0 and v3.method_C(y)["lower"] < 0
    assert v3.method_B(y, np.random.default_rng(2))["lower"] < 0


def test_wilson_bounds():
    lo, hi = v3.wilson(58, 1000)
    assert lo < .058 < hi and abs(hi - .0744) < 2e-3
