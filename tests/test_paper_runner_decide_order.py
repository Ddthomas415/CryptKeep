from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fresh_qdb(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import storage.intent_queue_sqlite as iq_mod
    importlib.reload(iq_mod)
    return iq_mod.IntentQueueSQLite()


def _seed_intent(qdb, *, side="buy", qty=0.01):
    iid = str(uuid.uuid4())
    qdb.upsert_intent({
        "intent_id": iid,
        "created_ts": _now(),
        "ts": _now(),
        "source": "test",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": side,
        "order_type": "limit",
        "qty": qty,
        "limit_price": 60000.0,
        "status": "queued",
        "last_error": None,
        "client_order_id": None,
        "linked_order_id": None,
    })
    return iid


def _allowed():
    from services.live_router.router import RouterDecision
    return RouterDecision(True, "ok", "buy", 0.01, "limit", 60000.0, {})


def _blocked():
    from services.live_router.router import RouterDecision
    return RouterDecision(False, "blocked", "none", 0.0, "none", None, {})


# ------------------------------------------------------------

def test_allowed_reaches_submit(monkeypatch, tmp_path):
    import services.execution.paper_runner as pr

    qdb = _fresh_qdb(monkeypatch, tmp_path)
    iid = _seed_intent(qdb)

    async def decide(*a, **k):
        return _allowed()

    monkeypatch.setattr(pr, "decide_order", decide)

    eng = MagicMock()
    eng.submit_order.return_value = {"ok": True, "order": {"order_id": "1"}}

    res = pr._consume_queued_intents_once(qdb=qdb, eng=eng)

    assert res["submitted"] == 1
    eng.submit_order.assert_called_once()
    assert qdb.get_intent(iid)["status"] == "submitted"


def test_blocked_rejects(monkeypatch, tmp_path):
    import services.execution.paper_runner as pr

    qdb = _fresh_qdb(monkeypatch, tmp_path)
    iid = _seed_intent(qdb)

    async def decide(*a, **k):
        return _blocked()

    monkeypatch.setattr(pr, "decide_order", decide)

    eng = MagicMock()

    res = pr._consume_queued_intents_once(qdb=qdb, eng=eng)

    assert res["rejected"] == 1
    eng.submit_order.assert_not_called()
    assert qdb.get_intent(iid)["status"] == "rejected"


def test_invalid_side_rejects(monkeypatch, tmp_path):
    import services.execution.paper_runner as pr

    qdb = _fresh_qdb(monkeypatch, tmp_path)
    iid = _seed_intent(qdb)

    claimed = qdb.claim_next_queued(limit=1)
    bad = dict(claimed[0])
    bad["side"] = ""

    monkeypatch.setattr(qdb, "claim_next_queued", lambda limit=20: [bad])

    eng = MagicMock()

    res = pr._consume_queued_intents_once(qdb=qdb, eng=eng)

    assert res["rejected"] == 1
    eng.submit_order.assert_not_called()


def test_zero_qty_rejects(monkeypatch, tmp_path):
    import services.execution.paper_runner as pr

    qdb = _fresh_qdb(monkeypatch, tmp_path)
    iid = _seed_intent(qdb)

    claimed = qdb.claim_next_queued(limit=1)
    bad = dict(claimed[0])
    bad["qty"] = 0.0

    monkeypatch.setattr(qdb, "claim_next_queued", lambda limit=20: [bad])

    eng = MagicMock()

    res = pr._consume_queued_intents_once(qdb=qdb, eng=eng)

    assert res["rejected"] == 1
    eng.submit_order.assert_not_called()


def test_empty_queue(monkeypatch, tmp_path):
    import services.execution.paper_runner as pr

    qdb = _fresh_qdb(monkeypatch, tmp_path)

    eng = MagicMock()

    res = pr._consume_queued_intents_once(qdb=qdb, eng=eng)

    assert res == {
        "queued_seen": 0,
        "submitted": 0,
        "rejected": 0,
        "idempotent": 0,
    }
