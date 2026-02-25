from __future__ import annotations

from services.ai_engine.trainer import TrainingRow, train_linear_signal_model


def test_trainer_produces_directional_weights():
    rows = [
        TrainingRow(context={"side": "buy", "telemetry": {"order_reject_rate": 0.01}}, label=1),
        TrainingRow(context={"side": "buy", "telemetry": {"order_reject_rate": 0.02}}, label=1),
        TrainingRow(context={"side": "sell", "telemetry": {"order_reject_rate": 0.20}}, label=0),
        TrainingRow(context={"side": "sell", "telemetry": {"order_reject_rate": 0.25}}, label=0),
    ]
    model = train_linear_signal_model(rows)
    assert "order_reject_rate" in model.weights
    # Higher reject rate in negative class should push weight negative.
    assert model.weights["order_reject_rate"] < 0.0

