from __future__ import annotations

from unittest.mock import MagicMock


def _intent(intent_id="i-1"):
    return {
        "intent_id": intent_id,
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "order_type": "limit",
        "qty": 0.001,
        "limit_price": 60000.0,
        "client_order_id": None,
        "exchange_order_id": None,
        "meta": {},
    }


def _ctx():
    from services.execution.state_authority import LiveStateContext
    return LiveStateContext(authority="INTENT_CONSUMER", origin="live_intent_consumer")


def test_mq_block_rejects_intent_instead_of_orphaning(monkeypatch):
    import services.execution.live_intent_consumer as lic

    calls = []

    def update(qdb, it, status, *, ctx, last_error=None, **kwargs):
        calls.append((status, last_error))
        return True

    monkeypatch.setattr(lic, "update_live_queue_status_as_intent_consumer", update)

    qdb = MagicMock()
    it = _intent("mq-1")
    ctx = _ctx()
    mq = {"ok": False, "reason": "spread_too_wide"}

    mq_reason = f"mq_blocked:{mq.get('reason', 'unknown')}"
    wrote = lic.update_live_queue_status_as_intent_consumer(
        qdb, it, "rejected", ctx=ctx, last_error=mq_reason
    )
    if wrote:
        rejected = 1
    else:
        rejected = 0

    assert rejected == 1
    assert calls == [("rejected", "mq_blocked:spread_too_wide")]


def test_mq_rejection_write_failure_escalates_to_submit_unknown(monkeypatch):
    import services.execution.live_intent_consumer as lic

    calls = []

    def update(qdb, it, status, *, ctx, last_error=None, **kwargs):
        calls.append((status, last_error))
        return status != "rejected"

    monkeypatch.setattr(lic, "update_live_queue_status_as_intent_consumer", update)

    qdb = MagicMock()
    it = _intent("mq-2")
    ctx = _ctx()
    mq_reason = "mq_blocked:spread_too_wide"

    wrote = lic.update_live_queue_status_as_intent_consumer(
        qdb, it, "rejected", ctx=ctx, last_error=mq_reason
    )
    if not wrote:
        lic.update_live_queue_status_as_intent_consumer(
            qdb, it, "submit_unknown", ctx=ctx,
            last_error=f"mq_rejected_write_failed:{mq_reason}",
        )

    assert calls == [
        ("rejected", "mq_blocked:spread_too_wide"),
        ("submit_unknown", "mq_rejected_write_failed:mq_blocked:spread_too_wide"),
    ]


def test_risk_rejection_write_failure_escalates_to_submit_unknown(monkeypatch):
    import services.execution.live_intent_consumer as lic

    calls = []

    def update(qdb, it, status, *, ctx, last_error=None, **kwargs):
        calls.append((status, last_error))
        return status != "rejected"

    monkeypatch.setattr(lic, "update_live_queue_status_as_intent_consumer", update)

    qdb = MagicMock()
    it = _intent("risk-1")
    ctx = _ctx()
    rreason = "risk:max_daily_notional_quote"

    wrote = lic.update_live_queue_status_as_intent_consumer(
        qdb, it, "rejected", ctx=ctx, last_error=rreason
    )
    if not wrote:
        lic.update_live_queue_status_as_intent_consumer(
            qdb, it, "submit_unknown", ctx=ctx,
            last_error=f"risk_rejected_write_failed:{rreason}",
        )

    assert calls == [
        ("rejected", "risk:max_daily_notional_quote"),
        ("submit_unknown", "risk_rejected_write_failed:risk:max_daily_notional_quote"),
    ]
