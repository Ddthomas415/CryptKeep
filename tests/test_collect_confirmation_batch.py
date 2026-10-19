import json
import fcntl
import sqlite3

import pytest

from scripts.research import collect_confirmation_batch as batch


@pytest.fixture
def setup(tmp_path, monkeypatch):
    h = batch.HOUR
    archive = tmp_path / 'archive.sqlite'
    with sqlite3.connect(archive) as db:
        db.execute('CREATE TABLE market_ohlcv (exchange, symbol, timeframe, ts_ms, o, h, l, cl, v)')
        for symbol in ('BTC/USD', 'ETH/USD'):
            for t in (0, h):
                db.execute('INSERT INTO market_ohlcv VALUES (?,?,?,?,?,?,?,?,?)',
                           ('coinbase', symbol, '1h', t, 10, 11, 9, 10, 1))
    plan = {'venue': 'coinbase', 'symbols': ['BTC/USD', 'ETH/USD'],
            'archive_start_utc': '1970-01-01T00:00:00Z',
            'evaluation_start_utc': '1970-01-01T01:00:00Z',
            'evaluation_end_exclusive_utc': '1970-01-02T00:00:00Z'}
    monkeypatch.setattr(batch, 'load_contract', lambda _: (plan, {}, {'frozen': 'hash'}))
    monkeypatch.setattr(batch, 'check_registration', lambda *a: 'registered')
    prior = tmp_path / 'prior.json'
    rows = [[t, 10, 11, 9, 10, 1] for t in (0, h)]
    prior.write_text(json.dumps({'kind': 'COLLECTION_CHECKPOINT_NOT_PHASE_COMPLETION',
                                'identity': {'frozen': 'hash'}, 'scoring_authorized': False,
                                'cutoff_exclusive_utc': batch.stamp(2*h),
                                'markets': {s: {'total_bars': 2, 'total_rows_sha256': batch.rows_hash(rows),
                                                'evaluation_bars': 1,
                                                'evaluation_rows_sha256': batch.rows_hash(rows[1:])}
                                            for s in plan['symbols']}}))
    return archive, prior, tmp_path / 'output.json'


def invoke(setup, **kwargs):
    archive, prior, output = setup
    return batch.collect('plan', archive, prior, 'registration', output,
                         now_ms=3*batch.HOUR + 123, **kwargs)


def test_status_has_no_network_or_output(setup):
    result = invoke(setup, fetcher=lambda *a, **k: pytest.fail('network'))
    assert result['missing_bars'] == {'BTC/USD': 1, 'ETH/USD': 1}
    assert not setup[2].exists()


def test_mutated_prefix_refuses_before_fetch(setup):
    with sqlite3.connect(setup[0]) as db:
        db.execute('UPDATE market_ohlcv SET cl=10.5 WHERE ts_ms=0')
    with pytest.raises(ValueError, match='parent_prefix_changed'):
        invoke(setup, dry_run=False, fetcher=lambda *a, **k: pytest.fail('network'))
    assert not setup[2].exists()


def test_completed_hours_only_and_no_repeat(setup, monkeypatch):
    calls = []
    def fake_backfill(fetcher, **kwargs):
        rows = fetcher('coinbase', kwargs['symbol'], timeframe='1h', limit=24,
                       since_ms=kwargs['since_ms'])
        with sqlite3.connect(kwargs['db_path']) as db:
            for row in rows:
                db.execute('INSERT INTO market_ohlcv VALUES (?,?,?,?,?,?,?,?,?)',
                           ('coinbase', kwargs['symbol'], '1h', *row))
    def fetch(venue, symbol, **kwargs):
        calls.append((symbol, kwargs))
        return [[t, 10, 11, 9, 10, 1] for t in (0, 2*batch.HOUR, 3*batch.HOUR)]
    monkeypatch.setattr(batch, 'backfill_archive', fake_backfill)
    result = invoke(setup, dry_run=False, fetcher=fetch)
    assert result['kind'] == 'COLLECTION_CHECKPOINT_NOT_PHASE_COMPLETION', result
    assert result['scoring_authorized'] is False
    assert all(m['total_bars'] == 3 for m in result['markets'].values())
    assert len(calls) == 2
    assert invoke(setup)['missing_bars'] == {'BTC/USD': 0, 'ETH/USD': 0}
    with pytest.raises(FileExistsError):
        invoke(setup, dry_run=False, fetcher=fetch)
    assert len(calls) == 2


def test_fetch_failure_preserved(setup):
    def fail(*args, **kwargs):
        raise RuntimeError('offline')
    result = invoke(setup, dry_run=False, fetcher=fail)
    assert result['status'] == 'INCOMPLETE'
    assert set(result['errors']) == {'BTC/USD', 'ETH/USD'}
    assert json.loads(setup[2].read_text()) == result


def test_alias_cannot_bypass_archive_lock(setup):
    archive, prior, output = setup
    alias = archive.with_name('alias.sqlite')
    alias.symlink_to(archive)
    with open(str(archive.resolve()) + '.collection.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            batch.collect('plan', alias, prior, 'registration', output,
                          now_ms=3*batch.HOUR, dry_run=False)
    assert not output.exists()


def test_real_backfill_and_store_preserve_prefix(setup):
    # Real ingestion distinguishes second timestamps from modern millisecond timestamps.
    base = batch.utc_ms('2026-10-10T00:00:00Z')
    plan, _, _ = batch.load_contract('plan')
    for key in ('archive_start_utc', 'evaluation_start_utc', 'evaluation_end_exclusive_utc'):
        plan[key] = batch.stamp(batch.utc_ms(plan[key]) + base)
    with sqlite3.connect(setup[0]) as db:
        db.execute('UPDATE market_ohlcv SET ts_ms=ts_ms+?', (base,))
    prior = json.loads(setup[1].read_text())
    prior['cutoff_exclusive_utc'] = batch.stamp(base + 2*batch.HOUR)
    rows = [[base+t, 10, 11, 9, 10, 1] for t in (0, batch.HOUR)]
    for market in prior['markets'].values():
        market['total_rows_sha256'] = batch.rows_hash(rows)
        market['evaluation_rows_sha256'] = batch.rows_hash(rows[1:])
    setup[1].write_text(json.dumps(prior))
    def fetch(venue, symbol, **kwargs):
        return [[base+t, 10, 11, 9, 10, 1] for t in (batch.HOUR, 2*batch.HOUR, 3*batch.HOUR)]
    result = batch.collect('plan', setup[0], setup[1], 'registration', setup[2],
                           now_ms=base + 3*batch.HOUR, dry_run=False, fetcher=fetch)
    assert not result.get('errors'), result.get('errors')
    assert result['kind'] == 'COLLECTION_CHECKPOINT_NOT_PHASE_COMPLETION', result
    assert all(m['total_bars'] == 3 for m in result['markets'].values())
    assert batch.collect('plan', setup[0], setup[1], 'registration', setup[2],
                         now_ms=base + 3*batch.HOUR)['missing_bars'] == {'BTC/USD': 0, 'ETH/USD': 0}


@pytest.mark.parametrize('limit', [0, 25, True, 1.5])
def test_budget_refuses(setup, limit):
    with pytest.raises(ValueError, match='max_hours'):
        invoke(setup, max_hours=limit)
