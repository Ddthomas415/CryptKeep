env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-accounting-runner-probe.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c '
import json,sqlite3
import pytest

def ambiguous_metadata_must_not_admit_buy(flow):
    from tests.test_paper_exit_accounting import _event, _scope, _counts, TS
    h=flow
    row=_event(h,"ambiguous-root",status="filled")
    win=h.accounting_lib.make_event(scope=_scope(h),entry_price=100.0,current_price=102.0,created_ts=TS)
    raw="{\"exit_event\":"+json.dumps(row["meta"]["exit_event"])+",\"exit_event\":"+json.dumps(win)+"}"
    with sqlite3.connect(h.queue_store.DB_PATH) as db:
        db.execute("UPDATE trade_intents SET meta=? WHERE intent_id=?",(raw,row["intent_id"]))
    h.cfg["symbols"]=["BTC/USD"]
    h.signal_action="buy"
    h.run(1)
    assert not h.intents("buy"), f"ambiguous accounting admitted new buy; counters={_counts(h)}; buys={h.intents(chr(98)+chr(117)+chr(121))}"

class Probe:
    def pytest_collection_modifyitems(self,items):
        parent=items[0].parent
        items[:]=[pytest.Function.from_parent(parent,name="ambiguous_metadata_must_not_admit_buy",callobj=ambiguous_metadata_must_not_admit_buy)]
raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","--tb=short","tests/test_paper_exit_accounting.py"],plugins=[Probe()]))
'
