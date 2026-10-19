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


def test_recovery_cursor_survives_restart(evidence_rig, monkeypatch):
    pe, ev_dir = evidence_rig
    engine = pe.PaperEngine()
    first = _submit(engine, 'restart-first', 'buy')
    _kill_during_evidence_write(monkeypatch, engine)
    second = _submit(engine, 'restart-second', 'buy')
    _kill_during_evidence_write(monkeypatch, engine)
    assert engine.backfill_fill_evidence(limit=1)['backfilled'] == 1
    assert pe.PaperEngine().backfill_fill_evidence(limit=1)['backfilled'] == 1
    assert {first, second} <= {record['order_id'] for record in _fill_records(ev_dir)}


def test_fill_pages_cover_more_than_default_limit(evidence_rig):
    pe, _ = evidence_rig
    engine = pe.PaperEngine()
    for index in range(505):
        engine.db.insert_fill({'fill_id': f'page-{index}', 'order_id': f'order-{index}',
                              'ts': '2026-01-01T00:00:00+00:00', 'price': 1.0,
                              'qty': 1.0, 'fee': 0.0, 'fee_currency': 'USD'})
    first = engine.db.list_fills_page(after_rowid=0)
    second = engine.db.list_fills_page(after_rowid=first[-1]['rowid'])
    assert len(first) == 500 and len(second) == 5
    assert len({row['fill_id'] for row in first + second}) == 505
