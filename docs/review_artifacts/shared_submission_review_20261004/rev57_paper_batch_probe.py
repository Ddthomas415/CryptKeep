from tests.test_paper_fill_quote_freshness import rig as quote_rig, _buy, _write
from tests.test_paper_fill_evidence_backfill import (
    rig as evidence_rig, _submit, _kill_during_evidence_write, _fill_records,
)


def test_fill_checks_the_quote_it_actually_uses(quote_rig, monkeypatch):
    engine, path = quote_rig
    _buy(engine)
    _write(path, price=40000.0, tick_age_s=10800)
    original = type(engine)._price

    def read_then_refresh(self, venue, symbol):
        stale = original(self, venue, symbol)
        _write(path, price=61000.0)
        return stale

    monkeypatch.setattr(type(engine), '_price', read_then_refresh)
    result = engine.evaluate_open_orders()
    assert result['filled'] == 0, engine.db.list_fills()


def test_backfill_advances_past_already_repaired_newest_fill(evidence_rig, monkeypatch):
    pe, ev_dir = evidence_rig
    engine = pe.PaperEngine()
    first = _submit(engine, 'missing-first', 'buy')
    _kill_during_evidence_write(monkeypatch, engine)
    _submit(engine, 'missing-second', 'buy')
    _kill_during_evidence_write(monkeypatch, engine)
    engine.backfill_fill_evidence(limit=1)
    engine.backfill_fill_evidence(limit=1)
    assert first in {record['order_id'] for record in _fill_records(ev_dir)}
