
import json
import sqlite3
import pytest

def duplicate_event_keys_must_quarantine(flow):
    from tests.test_paper_exit_accounting import _event, _refresh, _counts, _scope, TS
    h=flow
    first=_event(h,"ambiguous")
    loss=first["meta"]["exit_event"]
    win=h.accounting_lib.make_event(scope=_scope(h),entry_price=100.0,current_price=102.0,created_ts=TS)
    raw="{\"exit_event\":"+json.dumps(loss)+",\"exit_event\":"+json.dumps(win)+"}"
    with sqlite3.connect(h.queue_store.DB_PATH) as db:
        db.execute("UPDATE trade_intents SET meta=? WHERE intent_id=?",(raw,"ambiguous"))
    report=_refresh(h)
    assert report["unsettled"] is True, f"ambiguous metadata accepted: report={report}; counters={_counts(h)}"
    assert _counts(h)["cum_pnl"] == 0

def pending_payload_is_queue_evidence_not_stale_local(flow):
    from tests.test_paper_exit_accounting import _event, _refresh, _counts, _scope
    h=flow
    _event(h,"one")
    original=h.accounting.journal.confirm
    called=[]
    def fail_after(*args,**kwargs):
        original(*args,**kwargs)
        called.append(True)
        raise OSError("confirmation acknowledgement lost")
    h.mp.setattr(h.accounting.journal,"confirm",fail_after)
    assert _refresh(h)["unsettled"]
    h.mp.setattr(h.accounting.journal,"confirm",original)
    assert _refresh(h)["unsettled"] is False
    assert _counts(h)["loss_streak"] == 1
    assert _refresh(h)["applied"] == []

class Probes:
    def pytest_collection_modifyitems(self,items):
        parent=items[0].parent
        items[:]=[pytest.Function.from_parent(parent,name=f.__name__,callobj=f) for f in (duplicate_event_keys_must_quarantine,pending_payload_is_queue_evidence_not_stale_local)]
raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","--tb=short","tests/test_paper_exit_accounting.py"],plugins=[Probes()]))
