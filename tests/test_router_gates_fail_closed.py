"""AI/proba router gates fail closed on error — REMAINING_TASKS deferred item 16.

The ai_engine hook previously returned ok=True with reason=ai_error_ignored
when the gate raised and ai_strict was unset — the only fail-open error path
in an order-routing gate. These tests prove:
- an ENABLED ai gate that raises now BLOCKS the order, strict or not
- a DISABLED ai gate is untouched by these changes (no evaluation at all)
- a DISABLED proba gate with an import/evaluation error does not affect routing
"""
from __future__ import annotations

import asyncio

from services.live_router.router import decide_order


def test_ai_gate_error_fails_closed_when_enabled(monkeypatch):
    import services.ai_engine.signal_service as sig

    class _Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("model_load_failed")

    monkeypatch.setattr(sig, "AISignalService", _Boom)
    monkeypatch.setenv("CBP_AI_ENGINE_ENABLED", "1")
    monkeypatch.delenv("CBP_AI_ENGINE_STRICT", raising=False)

    dec = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 60000.0},
        )
    )
    assert dec.allowed is False
    assert str(dec.reason).startswith("ai_gate:error:")
    assert str(dec.meta.get("ai", {}).get("reason", "")).startswith("ai_error_fail_closed:")


def test_ai_gate_disabled_is_not_evaluated(monkeypatch):
    import services.ai_engine.signal_service as sig

    class _Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("must_never_be_constructed")

    monkeypatch.setattr(sig, "AISignalService", _Boom)
    monkeypatch.delenv("CBP_AI_ENGINE_ENABLED", raising=False)
    monkeypatch.delenv("CBP_USE_FUSED_PROBA", raising=False)

    dec = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 60000.0},
        )
    )
    # Disabled gate: routing proceeds and no ai meta indicates a fail-closed block.
    assert dec.allowed is True
    assert "ai" not in dec.meta or dec.meta["ai"].get("ok") is not False


def test_proba_gate_disabled_import_error_does_not_block(monkeypatch):
    from services import feature_gate as fg

    def _boom(*_args, **_kwargs):
        raise RuntimeError("proba_failed")

    monkeypatch.setattr(fg, "proba_gate", _boom)
    monkeypatch.delenv("CBP_USE_FUSED_PROBA", raising=False)

    dec = asyncio.run(
        decide_order(
            venue="coinbase",
            symbol_norm="BTC/USD",
            delta_qty=1.0,
            overrides={"reference_price": 60000.0},
        )
    )
    assert dec.allowed is True
