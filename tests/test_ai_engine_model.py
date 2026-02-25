from __future__ import annotations

from services.ai_engine.features import build_feature_map, vectorize_features
from services.ai_engine.model import LinearSignalModel


def test_build_feature_map_side_flags():
    fm = build_feature_map({"side": "buy", "telemetry": {"ws_lag_ms": 12}})
    assert fm["side_buy"] == 1.0
    assert fm["side_sell"] == 0.0
    assert fm["ws_lag_ms"] == 12.0


def test_vectorize_features_uses_order():
    fm = {"a": 1.0, "b": 2.0}
    vec = vectorize_features(fm, feature_order=["b", "a", "x"])
    assert vec == [2.0, 1.0, 0.0]


def test_linear_signal_model_buy_sell_threshold_behavior():
    model = LinearSignalModel(
        feature_order=["side_buy", "side_sell"],
        weights={"side_buy": 2.0, "side_sell": -2.0},
        bias=0.0,
        version=1,
    )
    ok_buy, _, p_buy = model.evaluate_side(
        side="buy",
        features={"side_buy": 1.0, "side_sell": 0.0},
        buy_threshold=0.55,
    )
    ok_sell, _, p_sell = model.evaluate_side(
        side="sell",
        features={"side_buy": 0.0, "side_sell": 1.0},
        sell_threshold=0.45,
    )
    assert ok_buy is True
    assert ok_sell is True
    assert p_buy > 0.5
    assert p_sell < 0.5

