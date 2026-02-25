from __future__ import annotations

import json

from services.ai_engine.signal_service import AISignalService


def test_signal_service_pass_through_without_model(tmp_path):
    svc = AISignalService(model_path=str(tmp_path / "missing_model.json"))
    out = svc.evaluate(side="buy", context={"side": "buy"})
    assert out.ok is True
    assert out.reason == "model_missing_pass_through"


def test_signal_service_uses_model_file(tmp_path):
    model_path = tmp_path / "ai_model.json"
    model_path.write_text(
        json.dumps(
            {
                "feature_order": ["side_buy", "side_sell"],
                "weights": {"side_buy": 2.0, "side_sell": -2.0},
                "bias": 0.0,
                "version": 1,
            }
        ),
        encoding="utf-8",
    )
    svc = AISignalService(model_path=str(model_path))
    out = svc.evaluate(side="buy", context={"side": "buy"}, buy_threshold=0.55)
    assert out.ok is True
    assert out.model_version == 1
    assert out.proba_up > 0.5

