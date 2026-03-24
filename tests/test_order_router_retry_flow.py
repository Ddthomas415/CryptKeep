import inspect

import pytest


def _call_router(order_router, **kwargs):
    sig = inspect.signature(order_router.place_order_idempotent)
    filtered = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return order_router.place_order_idempotent(**filtered)


def test_order_router_blocks_retry_when_reconciliation_inconclusive(monkeypatch):
    from services.execution import order_router

    monkeypatch.setattr(order_router.IdempotencySQLite, "get", lambda self, key: None)
    monkeypatch.setattr(order_router, "load_exchange_credentials", lambda venue: {"apiKey": "x", "secret": "y"})
    monkeypatch.setattr(order_router, "make_exchange", lambda *a, **k: object())

    monkeypatch.setattr(order_router, "_place_order_ccxt", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("timeout")))
    monkeypatch.setattr(order_router, "is_retryable_exception", lambda e: True)
    monkeypatch.setattr(
        order_router,
        "reconcile_ambiguous_submission",
        lambda **kwargs: type("R", (), {"outcome": "inconclusive"})(),
    )

    with pytest.raises(RuntimeError, match="retry_blocked_after_ambiguous_submit:inconclusive"):
        _call_router(
            order_router,
            venue="binance",
            symbol="BTC/USDT",
            type="market",
            side="buy",
            amount=1.0,
            price=None,
            params={},
            idempotency_key="cid-retry-confirmed-not-placed-test",
            dry_run=False,
        )


def test_order_router_retries_only_when_confirmed_not_placed(monkeypatch):
    from services.execution import order_router

    monkeypatch.setattr(order_router.IdempotencySQLite, "get", lambda self, key: None)
    monkeypatch.setattr(order_router, "load_exchange_credentials", lambda venue: {"apiKey": "x", "secret": "y"})
    monkeypatch.setattr(order_router, "make_exchange", lambda *a, **k: object())


    calls = {"n": 0}

    def fail_then_succeed(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("timeout")
        return {"id": "o1"}

    monkeypatch.setattr(order_router, "_place_order_ccxt", fail_then_succeed)
    monkeypatch.setattr(order_router, "is_retryable_exception", lambda e: True)
    monkeypatch.setattr(order_router, "backoff_sleep", lambda *a, **k: None)
    monkeypatch.setattr(
        order_router,
        "reconcile_ambiguous_submission",
        lambda **kwargs: type("R", (), {"outcome": "confirmed_not_placed"})(),
    )

    out = _call_router(
        order_router,
        venue="binance",
        symbol="BTC/USDT",
        type="market",
        side="buy",
        amount=1.0,
        price=None,
        params={},
        idempotency_key="cid-retry-confirmed-not-placed-test",
        dry_run=False,
    )

    assert calls["n"] == 2
    assert out["ok"] is True
    assert out["result"] == {"id": "o1"}
