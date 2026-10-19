"""Hash-bound, read-only input adapter; no source authentication or scoring."""
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.research.cmc_bounded_daily import START, DAYS, boundary_ms
from scripts.research.cmc_completeness_adapter import audit_cohorts
from scripts.research.cmc_daily_cohorts import build_cohorts
from scripts.research.cmc_diagnostic_evaluator import evaluate as evaluate_event
from scripts.research.cmc_quote_qualification import _time, qualify_capture
from scripts.research.cmc_snapshot_evidence import load_snapshot


def _receipt(record, upper):
    value = _time(record['received_utc'])
    if not 0 <= int(value.timestamp()*1000) <= upper:
        raise ValueError('late source receipt')
    return int(value.timestamp()*1000)


def _capture_time(envelope, product, coin, upper):
    data = envelope['data']
    times = [int(envelope['snapshot_utc'].timestamp()*1000),
             _receipt(coin, upper), _receipt(data['majors_coinbase']['BTC'], upper),
             _receipt(data['coinbase_level1_books'][product]['response'], upper)]
    if max(times) > upper:
        raise ValueError('late snapshot')
    return max(times)


def build(manifest, *, now_ms):
    """Manifest lists preserved snapshot paths plus expected content SHA256 values."""
    end = START + timedelta(days=DAYS-1)
    if type(now_ms) is not int or now_ms < boundary_ms(end):
        raise ValueError('declared window not mature')
    if not isinstance(manifest, list) or not manifest:
        raise ValueError('source manifest required')
    envelopes, paths, hashes = [], set(), set()
    for source in manifest:
        path = Path(source['file']).resolve()
        item = load_snapshot(path)
        if path in paths or item['sha256'] in hashes:
            raise ValueError('duplicate snapshot source')
        if item['sha256'] != source['sha256']:
            raise ValueError('source content changed')
        if item['snapshot_utc'].timestamp()*1000 > now_ms:
            raise ValueError('future snapshot')
        paths.add(path)
        hashes.add(item['sha256'])
        envelopes.append(item)
    cohorts = build_cohorts(envelopes)
    by_file = {item['file']: item for item in envelopes}
    observed = {}
    for item in envelopes:
        day = item['snapshot_utc'].date().isoformat()
        if day not in cohorts['observed_utc_days']:
            continue
        # Bind availability to the recorded list response, not snapshot start time.
        response = item['data']['source_responses']['hidden']
        received = _receipt(response, now_ms)
        if _time(response['received_utc']).date().isoformat() != day:
            raise ValueError('list receipt crosses declared capture day')
        observed[day] = max(observed.get(day, 0), received)
    outcomes, qualifications, events_by_day = [], [], {}
    for event in cohorts['events']:
        day = datetime.fromisoformat(event['utc_day']).date()
        if not START <= day <= end:
            continue
        if (event['cohort_status'] != 'PRIMARY_COHORT_CANDIDATE'
                or event['identity_eligible_at_first_observation'] is not True):
            continue
        upper = boundary_ms(day)
        entry_env = by_file[event['first_snapshot_file']]
        listing = next(r for r in entry_env['data']['trending_hidden_boost']
                       if r.get('type') == 'listing' and str(r['cmc_id']) == event['cmc_id'])
        product, coin = listing['coinbase_product'], listing['coinbase']
        # An exclusion is evidence too; unavailable evidence cannot erase an event.
        entry_time = _capture_time(entry_env, product, coin, upper)
        entry = qualify_capture(entry_env['data'], product, coin, 'buy',
                                identity_eligible=listing.get('identity_eligible'))
        qualification = {'utc_day': event['utc_day'], 'cmc_id': event['cmc_id'],
                         'horizon_days': 7, 'entry': entry, 'exit': {'status': 'UNRESOLVED'},
                         'qualified': False}
        qualifications.append(qualification)
        if entry['status'] != 'QUALIFIED':
            continue
        candidates, links = [], {}
        for item in envelopes:
            if item['snapshot_utc'].timestamp()*1000 > upper:
                continue
            for tracked in item['data']['tracked_coinbase']:
                if (not isinstance(tracked, dict) or str(tracked.get('cmc_id')) != event['cmc_id']
                        or tracked.get('coinbase_product') != product):
                    continue
                quote = tracked['quote']
                received = _time(quote['received_utc'])
                if received.timestamp()*1000 > upper:
                    continue
                if received in links:
                    raise ValueError('ambiguous endpoint source')
                links[received] = (item, tracked)
                candidates.append({'identity_eligible': tracked.get('identity_eligible'),
                                   'coin_quote': quote,
                                   'btc_quote': item['data']['majors_coinbase'].get('BTC', {})})
        outcome = evaluate_event({'cohort_status': event['cohort_status'], 'identity_eligible': True,
                                  'coin_quote': coin,
                                  'btc_quote': entry_env['data']['majors_coinbase'].get('BTC', {})}, candidates, 7)
        outcomes.append({**outcome, 'utc_day': event['utc_day'], 'cmc_id': event['cmc_id'],
                         'horizon_days': 7, 'source_sha256': event['first_snapshot_sha256']})
        if outcome.get('status') != 'DIAGNOSTIC':
            continue
        exit_env, tracked = links[outcome['observation_time']]
        exit_ = qualify_capture(exit_env['data'], product, tracked['quote'], 'sell',
                                quantity=entry['quantity'], identity_eligible=tracked.get('identity_eligible'))
        qualification.update(exit=exit_, qualified=exit_['status'] == 'QUALIFIED')
        if exit_['status'] != 'QUALIFIED':
            continue
        available = max(entry_time, _capture_time(exit_env, product, tracked['quote'], upper))
        events_by_day.setdefault(event['utc_day'], []).append(
            {'event_id': event['utc_day'] + ':' + event['cmc_id'],
             'net_excess': outcome['excess_return'], 'qualification': 'QUALIFIED_PAIRED_ENDPOINTS',
             'evidence_available_at_ms': available,
             'entry_source_sha256': entry_env['sha256'], 'exit_source_sha256': exit_env['sha256']})
    completeness = audit_cohorts(cohorts, outcomes, qualifications,
                                datetime.fromtimestamp(now_ms/1000, timezone.utc),
                                start_day=START.isoformat(), end_day=end.isoformat())
    if completeness['status'] != 'COMPLETE_FULL_COHORT':
        raise ValueError('incomplete declared cohort')
    calendar = []
    for row in completeness['calendar']:
        day = datetime.fromisoformat(row['day']).date()
        events = events_by_day.get(row['day'], [])
        if len(events) != row['eligible']:
            raise ValueError('qualified event linkage incomplete')
        calendar.append({'day': row['day'], 'status': 'COMPLETE_DAY', 'list_observed': True,
                         'list_available_at_ms': observed[row['day']],
                         'maturity_boundary_ms': boundary_ms(day), 'eligible': len(events),
                         'unknown': 0, 'missing_outcomes': 0, 'events': events})
    return {'status': 'COMPLETE_FULL_COHORT', 'calendar': calendar, 'scoring_authorized': False,
            'source_files': [{'file': i['file'], 'sha256': i['sha256']} for i in envelopes],
            'entry_rule_exclusions': completeness['entry_rule_exclusions'],
            'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'dependency_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                  for name in ('cmc_snapshot_evidence.py', 'cmc_daily_cohorts.py',
                                               'cmc_cohort_coverage.py', 'cmc_completeness_adapter.py',
                                               'cmc_cohort_completeness.py', 'cmc_diagnostic_evaluator.py',
                                               'cmc_endpoint_timing.py', 'cmc_quote_evidence.py',
                                               'cmc_quote_qualification.py', 'cmc_book_evidence.py',
                                               'cmc_return_math.py')},
            'fee_per_side': 0.012,
            'source_authentication': 'UNVERIFIED', 'inventory_completeness': 'UNVERIFIED',
            'execution': 'NOT_FILL_PROOF', 'scope': 'HASH_BOUND_STRUCTURAL_INPUT_NOT_SCORING'}
