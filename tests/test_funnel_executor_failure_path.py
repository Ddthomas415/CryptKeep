from services.execution.funnel import FunnelExecutor, FunnelIntent

def test_funnel_executor_returns_not_ok_on_submit_exception():
    def boom(**_kwargs):
        raise RuntimeError("submit exploded")

    ex = FunnelExecutor(submit_fn=boom)
    res = ex.execute(
        FunnelIntent(
            venue="binance",
            symbol="BTC/USDT",
            side="buy",
            qty=1.0,
            order_type="market",
            client_oid="oid-1",
        )
    )

    assert res.ok is False
    assert res.reason == "submit_exception"
    assert res.response is None
    assert res.details is not None
    assert res.details["exception_type"] == "RuntimeError"
    assert "submit exploded" in res.details["error"]
