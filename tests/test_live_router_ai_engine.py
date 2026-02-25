from __future__ import annotations

import asyncio
import json

from services.live_router.router import decide_order


def _write_test_model(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "feature_order": ["side_buy", "side_sell"],
                "weights": {"side_buy": 2.0, "side_sell": -2.0},
                "bias": 0.0,
                "version": 1,
            },
            f,
        )


def test_live_router_allows_with_ai_gate_pass(monkeypatch, tmp_path):
    model_path = str(tmp_path / "ai_model.json")
    _write_test_model(model_path)
    monkeypatch.setenv("CBP_AI_ENGINE_ENABLED", "1")
    monkeypatch.setenv("CBP_AI_MODEL_PATH", model_path)
    monkeypatch.setenv("CBP_AI_BUY_THRESHOLD", "0.55")
    monkeypatch.delenv("CBP_AI_ENGINE_STRICT", raising=False)

    dec = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"ai_context": {"telemetry": {"order_reject_rate": 0.02}}},
        )
    )
    assert dec.allowed is True
    assert dec.meta.get("ai", {}).get("ok") is True


def test_live_router_blocks_with_ai_gate_fail(monkeypatch, tmp_path):
    model_path = str(tmp_path / "ai_model.json")
    _write_test_model(model_path)
    monkeypatch.setenv("CBP_AI_ENGINE_ENABLED", "1")
    monkeypatch.setenv("CBP_AI_MODEL_PATH", model_path)
    monkeypatch.setenv("CBP_AI_BUY_THRESHOLD", "0.99")

    dec = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"ai_context": {"telemetry": {"order_reject_rate": 0.5}}},
        )
    )
    assert dec.allowed is False
    assert str(dec.reason).startswith("ai_gate:")

