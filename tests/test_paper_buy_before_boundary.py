"""Same behavioral assertions against current source or preserved before-source."""
import importlib.util
import os
from pathlib import Path

from tests.test_paper_buy_lifecycle import rig, seed


def _baseline_module(name, relative):
    root = os.environ.get("CBP_BUY_BEFORE_ROOT")
    if not root:
        return None
    path = Path(root) / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_old_buy_cannot_commit_a_late_fill(rig, monkeypatch, tmp_path):
    from storage import paper_trading_sqlite as current
    baseline = _baseline_module("buy_before_store", "storage/paper_trading_sqlite.py")
    module = baseline or current
    monkeypatch.setattr(module, "DB_PATH", tmp_path / "probe.sqlite")
    db = module.PaperTradingSQLite()
    db.set_state("cash_quote", "1000")
    db.set_state("realized_pnl", "0")
    db.insert_order({"order_id": "late", "client_order_id": "late", "ts": "2000-01-01T00:00:00Z",
                     "venue": "coinbase", "symbol": "ADA/USD", "side": "buy", "order_type": "market",
                     "qty": 1, "status": "new", "meta": {"paper_buy_created_ts": "2000-01-01T00:00:00Z"}})
    order = db.get_order_by_client_id("late")
    result = db.apply_fill(order=order, ts=rig.clock(), price=100, qty=1, fee=.5, fee_currency="USD")
    assert not result["ok"], "an expired buy committed a fill"
    assert db.list_fills() == [] and float(db.get_state("cash_quote")) == 1000


def test_committed_order_response_loss_is_not_reported_as_refused(rig, monkeypatch):
    baseline = _baseline_module("buy_before_runner", "paper_runner.py")
    consumer = baseline or rig.runner
    if baseline:
        async def allowed(*args, **kwargs):
            from types import SimpleNamespace
            return SimpleNamespace(allowed=True)
        monkeypatch.setattr(consumer, "decide_order", allowed)
    seed(rig)
    submit = rig.eng.submit_order
    def lost_response(**kwargs):
        assert submit(**kwargs)["ok"]
        raise RuntimeError("response_lost")
    monkeypatch.setattr(rig.eng, "submit_order", lost_response)
    consumer._consume_queued_intents_once(qdb=rig.q, eng=rig.eng)
    assert rig.q.get_intent("buy")["status"] == "submitted", "durably written order was disposed as refused"
    assert len(rig.eng.db.list_orders()) == 1
