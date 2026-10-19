"""Bounded public liquidation/candle availability probe, never a trading signal."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import requests

MINUTE = 60000
BASE = 'https://www.okx.com/api/v5/'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)


def freeze(output):
    save(output, {'created_utc': datetime.now(timezone.utc).isoformat(),
                  'source_sha256': digest(__file__), 'assets': ['BTC', 'ETH'],
                  'cutoff_ms': int(time.time() * 1000) // MINUTE * MINUTE,
                  'liquidation_pages_per_asset': 6, 'candle_pages_per_market': 3,
                  'max_requests': 30, 'horizons_minutes': [1, 5, 15],
                  'purpose': 'availability only; no returns, entries, threshold selection, scoring, orders or profitability claim',
                  'limits': ['recent_public_records_not_complete_venue_liquidations',
                             'REST_route_reachable_but_not_found_in_current_documentation',
                             'no_stable_venue_order_id', 'bkPx_not_trade_or_fill_price',
                             'candles_not_bid_ask_or_executable_books', 'no_new_recurring_job']})


def records(groups, instrument, cutoff):
    found = []
    for group in groups:
        if group.get('instId') != instrument or group.get('instType') != 'SWAP':
            raise ValueError('unexpected_instrument')
        for row in group.get('details', []):
            timestamp = int(row['ts'])
            if timestamp <= 0:
                raise ValueError('invalid_event_timestamp')
            if (row.get('posSide'), row.get('side')) not in [('long', 'sell'), ('short', 'buy')]:
                raise ValueError('unexpected_liquidation_direction')
            if timestamp >= cutoff:
                continue
            found.append({'timestamp': timestamp, 'side': row['side'],
                          'position_side': row['posSide'], 'raw': row,
                          'record_fingerprint': hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()})
    return found


def completed_candles(rows, cutoff):
    result = {}
    for row in rows:
        t = int(row[0])
        if t % MINUTE:
            raise ValueError('unaligned_candle')
        if t + MINUTE > cutoff or row[-1] != '1':
            continue
        values = [float(v) for v in row[1:5]]
        if not all(math.isfinite(v) and v > 0 for v in values):
            raise ValueError('invalid_candle_price')
        result[t] = row
    return result


def coverage(events, spot, perp, cutoff, horizons):
    result = {'records': len(events), 'long_sell_records': 0, 'short_buy_records': 0,
              'long_sell_minute_bins': 0, 'immature_records': 0,
              'matched_spot_and_perp_records': 0, 'matched_long_sell_records': 0,
              'missing_price_records': 0}
    bins = set()
    for event in events:
        is_long = event['position_side'] == 'long'
        result['long_sell_records' if is_long else 'short_buy_records'] += 1
        if is_long:
            bins.add(event['timestamp'] // MINUTE)
        anchor = (event['timestamp'] // MINUTE + 1) * MINUTE
        if anchor + max(horizons) * MINUTE > cutoff:
            result['immature_records'] += 1
            continue
        # Require every intervening minute, not just two endpoint prices.
        grid = range(anchor, anchor + max(horizons) * MINUTE, MINUTE)
        if all(t in spot and t in perp for t in grid):
            result['matched_spot_and_perp_records'] += 1
            result['matched_long_sell_records'] += int(is_long)
        else:
            result['missing_price_records'] += 1
    result['long_sell_minute_bins'] = len(bins)
    result['oldest_ms'] = min((e['timestamp'] for e in events), default=None)
    result['newest_ms'] = max((e['timestamp'] for e in events), default=None)
    return result


def collect(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256']:
        raise ValueError('source_changed')
    raw = {'plan_sha256': digest(plan_path), 'requests': [], 'assets': {},
           'limits': plan['limits'], 'evidence': 'OBSERVED_PUBLIC_DIAGNOSTIC_NOT_FILLS'}
    with requests.Session() as session:
        session.trust_env = False

        def get(path, params):
            if len(raw['requests']) >= plan['max_requests']:
                raise ValueError('request_budget_exhausted')
            receipt = {'path': path, 'params': params,
                       'requested_utc': datetime.now(timezone.utc).isoformat()}
            raw['requests'].append(receipt)
            try:
                response = session.get(BASE + path, params=params, timeout=15, allow_redirects=False)
                receipt.update(http_status=response.status_code,
                               received_utc=datetime.now(timezone.utc).isoformat(),
                               response_base64=base64.b64encode(response.content).decode(),
                               response_sha256=hashlib.sha256(response.content).hexdigest())
                response.raise_for_status()
                data = response.json()
                if data.get('code') != '0':
                    raise ValueError('public_api_error:' + str(data.get('msg')))
                return data['data']
            except (requests.RequestException, ValueError) as exc:
                receipt['error'] = str(exc)
                return None
            finally:
                time.sleep(.12)

        for asset in plan['assets']:
            perp_id, spot_id = asset + '-USDT-SWAP', asset + '-USDT'
            events, cursor = {}, plan['cutoff_ms']
            failed_pages = 0
            for _ in range(plan['liquidation_pages_per_asset']):
                groups = get('public/liquidation-orders', {'instType': 'SWAP',
                             'instFamily': spot_id, 'state': 'filled', 'limit': 100, 'after': str(cursor)})
                if groups is None:
                    failed_pages += 1
                    break
                page = records(groups, perp_id, plan['cutoff_ms'])
                if not page:
                    break
                if any(e['timestamp'] >= cursor for e in page):
                    raise ValueError('pagination_not_strictly_older')
                for event in page:
                    events[event['record_fingerprint']] = event
                cursor = min(e['timestamp'] for e in page)
            retention = {}
            for days in (7, 30):
                cutoff = plan['cutoff_ms'] - days * 86400000
                groups = get('public/liquidation-orders', {'instType': 'SWAP', 'instFamily': spot_id,
                             'state': 'filled', 'limit': 100, 'after': str(cutoff)})
                page = records(groups, perp_id, plan['cutoff_ms']) if groups is not None else []
                retention[str(days)] = {'status': 'API_ERROR' if groups is None else 'RECORDS' if page else 'EMPTY_RESPONSE',
                                         'records': len(page), 'all_older_than_requested': all(e['timestamp'] < cutoff for e in page)}
            definition = get('public/instruments', {'instType': 'SWAP', 'instId': perp_id})
            candles = {}
            oldest = min((e['timestamp'] for e in events.values()), default=plan['cutoff_ms'])
            for instrument in (spot_id, perp_id):
                all_bars, cursor = {}, plan['cutoff_ms'] + 1
                for _ in range(plan['candle_pages_per_market']):
                    rows = get('market/history-candles', {'instId': instrument, 'bar': '1m',
                               'limit': 300, 'after': str(cursor)})
                    if rows is None or not rows:
                        break
                    all_bars.update(completed_candles(rows, plan['cutoff_ms']))
                    next_cursor = min(int(row[0]) for row in rows)
                    if next_cursor >= cursor:
                        raise ValueError('candle_pagination_stalled')
                    cursor = next_cursor
                    if cursor <= oldest:
                        break
                candles[instrument] = all_bars
            summary = coverage(list(events.values()), candles[spot_id], candles[perp_id],
                               plan['cutoff_ms'], plan['horizons_minutes'])
            summary.update(liquidation_failed_pages=failed_pages, retention_probes=retention,
                           identity_count=len(definition) if definition is not None else 0)
            raw['assets'][asset] = {'events': sorted(events.values(), key=lambda e: e['timestamp']),
                                    'definition': definition, 'candles': candles, 'summary': summary}
    if digest(__file__) != plan['source_sha256']:
        raise ValueError('source_changed_during_collection')
    save(output, raw)
    print(json.dumps({'requests': len(raw['requests']),
                      'failed_requests': sum('error' in r for r in raw['requests']),
                      'summary': {a: x['summary'] for a, x in raw['assets'].items()}}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'collect'])
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    {'freeze': freeze, 'collect': collect}[args.action](*args.paths)
