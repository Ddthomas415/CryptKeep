import hashlib
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pytest

from scripts.research import cmc_bounded_adapter as adapter
from scripts.research import cmc_bounded_daily as calculator
from scripts.research.cmc_quote_qualification import ACCEPTED_COLLECTORS


def ticker(t, price=100):
    return {'payload': {'bid': str(price), 'ask': str(price), 'time': t.isoformat()},
            'request_started_utc': (t-timedelta(seconds=.1)).isoformat(),
            'received_utc': t.isoformat(), 'response_sha256': 'a'*64}


def book(t):
    return {'product_id': 'X-USD', 'request_url': 'https://api.exchange.coinbase.com/products/'
            + quote('X-USD', safe='') + '/book?level=1',
            'response': {'payload': {'bids': [['100', '10', 1]], 'asks': [['100', '10', 1]],
                                     'sequence': 1, 'auction_mode': False, 'auction': None,
                                     'time': t.isoformat()},
                         'request_started_utc': (t-timedelta(seconds=.1)).isoformat(),
                         'received_utc': t.isoformat(), 'response_sha256': 'a'*64}}


@pytest.fixture
def sources(tmp_path):
    manifest = []
    start = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)
    for i in range(127):
        t = start + timedelta(days=i)
        rows = [{'type': 'listing', 'cmc_id': '2', 'identity_eligible': False}]
        if t.date() == calculator.START:
            rows.append({'type': 'listing', 'cmc_id': '1', 'identity_eligible': True,
                         'coinbase_product': 'X-USD', 'coinbase': ticker(t)})
        d = {'artifact_type': 'research_only_forward_log_v3', 'schema_version': 3,
             'places_orders': False, 'snapshot_utc': t.isoformat(),
             'collector_sha256': sorted(ACCEPTED_COLLECTORS)[0],
             'trending_status': 'OBSERVED', 'source_errors': [], 'trending_hidden_boost': rows,
             'tracked_coinbase': [{'cmc_id': '1', 'coinbase_product': 'X-USD',
                                   'identity_eligible': True, 'quote': ticker(t, 110)}],
             'majors_coinbase': {'BTC': ticker(t)}, 'coinbase_level1_books': {'X-USD': book(t)},
             'source_responses': {'hidden': {'received_utc': t.isoformat()}}}
        path = tmp_path / f'{i}.json'
        raw = json.dumps(d).encode()
        path.write_bytes(raw)
        manifest.append({'file': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
    return manifest


NOW = calculator.boundary_ms(calculator.START + timedelta(days=89))


def test_real_composition_preserves_hashes_and_raw_return(sources):
    result = adapter.build(sources, now_ms=NOW)
    assert len(result['calendar']) == 90
    assert sum(row['eligible'] for row in result['calendar']) == 1
    event = result['calendar'][0]['events'][0]
    assert event['net_excess'] > .05
    assert event['entry_source_sha256'] in {s['sha256'] for s in sources}
    assert result['source_authentication'] == 'UNVERIFIED'
    assert result['scoring_authorized'] is False
    calculated = calculator.evaluate(result, now_ms=NOW)
    assert calculated['clipped_events'] == 1
    assert calculated['zero_event_days'] == 89


def test_pre_maturity_does_not_open_sources():
    with pytest.raises(ValueError, match='not mature'):
        adapter.build([{'file': '/not/read', 'sha256': 'x'}], now_ms=0)


def test_changed_and_duplicate_sources_refuse(sources):
    changed = [dict(s) for s in sources]
    changed[0]['sha256'] = 'b'*64
    with pytest.raises(ValueError, match='changed'):
        adapter.build(changed, now_ms=NOW)
    with pytest.raises(ValueError, match='duplicate'):
        adapter.build(sources + sources[:1], now_ms=NOW)


def test_missing_calendar_or_prior_history_refuses(sources):
    for index in (0, 40, 119):
        with pytest.raises(ValueError):
            adapter.build(sources[:index] + sources[index+1:], now_ms=NOW)


def test_missing_exit_is_not_zero_event_day(sources):
    # Remove all tracked quotes; content-hash rebind models an explicitly different fixture.
    from pathlib import Path
    for source in sources:
        path = Path(source['file'])
        data = json.loads(path.read_bytes())
        data['tracked_coinbase'] = []
        raw = json.dumps(data).encode()
        path.write_bytes(raw)
        source['sha256'] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match='incomplete declared cohort'):
        adapter.build(sources, now_ms=NOW)


def test_late_entry_evidence_cannot_create_exclusion(sources):
    from pathlib import Path
    source = sources[30]
    path = Path(source['file'])
    data = json.loads(path.read_bytes())
    late = datetime.fromtimestamp((calculator.boundary_ms(calculator.START)+1)/1000, timezone.utc)
    data['coinbase_level1_books']['X-USD']['response']['received_utc'] = late.isoformat()
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    source['sha256'] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match='late source receipt'):
        adapter.build(sources, now_ms=NOW)
