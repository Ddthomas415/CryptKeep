"""Reporting audit for repeated hourly leader events; not a portfolio simulator."""
import hashlib
import json
from pathlib import Path
from statistics import mean


def audit(events):
    distinct = {}
    for event in events:
        if 'entry_time' in event:
            distinct.setdefault((event['symbol'], event['entry_time']), event)
    closed = [e for e in distinct.values() if 'net_usd' in e]
    marked = [e.get('net_usd', e.get('last_mark_net_usd')) for e in distinct.values()]
    priced = [value for value in marked if value is not None]
    return {'distinct_entry_count': len(distinct), 'distinct_closed_count': len(closed),
            'distinct_closed_net_winners': sum(e['net_usd'] > 0 for e in closed),
            'distinct_mean_closed_net_usd': mean(e['net_usd'] for e in closed) if closed else None,
            'distinct_closed_plus_marks_mean_usd': mean(priced) if priced else None,
            'unpriced_entries': len(marked)-len(priced),
            'remaining_limit': 'Different entries still overlap/correlate; not independent trials or portfolio PnL'}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    source = root/'research/hourly_leader_results_20261012.json'
    data = json.loads(source.read_text())
    result = {'primary_result_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'method': 'First chronological leader per same symbol and entry time; diagnostic audit only, no rule tuning',
              'runs': [{k: row[k] for k in ('dip', 'target', 'hold_hours')} | audit(row['events'])
                       for row in data['runs']]}
    with (root/'research/hourly_leader_dependency_audit_20261012.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    for row in result['runs']:
        print(row)
