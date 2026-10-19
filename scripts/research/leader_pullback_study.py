"""Public-only historical leader/pullback study, with unresolved events retained."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[2]
DAY = 86400
BASE = 'https://api.coinbase.com/api/v3/brokerage/market/products/'


def collect(universe_path, output):
    universe = json.loads(Path(universe_path).read_text())
    cutoff = int(time.time()) // DAY * DAY
    products = [p['product_id'] for p in universe['products']
                if p.get('quote_currency_id') == 'USD' and p.get('status') == 'online'
                and not any(p.get(k) for k in ('is_disabled', 'trading_disabled',
                                               'view_only', 'cancel_only'))]
    def fetch(symbol):
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.get(BASE+symbol+'/candles', params={
                    'start': cutoff-182*DAY, 'end': cutoff,
                    'granularity': 'ONE_DAY', 'limit': 350}, timeout=15,
                    allow_redirects=False)
                response.raise_for_status()
                return symbol, {'raw': response.json(),
                                'sha256': hashlib.sha256(response.content).hexdigest()}
        except Exception as exc:
            return symbol, {'error': type(exc).__name__}
    result = {'observed_utc': datetime.now(timezone.utc).isoformat(),
              'cutoff': cutoff, 'requested': len(products),
              'universe_sha256': hashlib.sha256(Path(universe_path).read_bytes()).hexdigest(),
              'coverage': 'CURRENT_ELIGIBLE_UNIVERSE_NOT_HISTORICAL_LISTINGS',
              'markets': {}}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for count, (symbol, data) in enumerate(pool.map(fetch, products), 1):
            result['markets'][symbol] = data
            if count % 50 == 0:
                print('collected', count, '/', len(products), flush=True)
    with Path(output).open('x') as stream:
        json.dump(result, stream, indent=2)
    print('saved', len(result['markets']), 'errors',
          sum('error' in d for d in result['markets'].values()), flush=True)


def repair(source, output):
    data = json.loads(Path(source).read_text())
    data['repair_parent_sha256'] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    failed = [s for s, value in data['markets'].items() if 'error' in value]
    with requests.Session() as session:
        session.trust_env = False
        for i, symbol in enumerate(failed, 1):
            for attempt in range(3):
                try:
                    response = session.get(BASE+symbol+'/candles', params={
                        'start': data['cutoff']-182*DAY, 'end': data['cutoff'],
                        'granularity': 'ONE_DAY', 'limit': 350}, timeout=15,
                        allow_redirects=False)
                    if response.status_code == 429:
                        time.sleep(2*(attempt+1))
                        continue
                    response.raise_for_status()
                    data['markets'][symbol] = {'raw': response.json(),
                        'sha256': hashlib.sha256(response.content).hexdigest()}
                    break
                except requests.RequestException as exc:
                    data['markets'][symbol] = {'error': type(exc).__name__,
                                              'http_status': getattr(locals().get('response'), 'status_code', None)}
                    break
            time.sleep(.12)
            if i % 50 == 0:
                print('retry', i, '/', len(failed), flush=True)
    with Path(output).open('x') as stream:
        json.dump(data, stream, indent=2)
    print('remaining errors', sum('error' in v for v in data['markets'].values()), flush=True)


def events_for(rows, leaders, cutoff, pullback):
    events = []
    for timestamp, symbol, gain in leaders:
        series = rows[symbol]
        leader_price = series[timestamp]['close']
        peak = leader_price
        entry = None
        event = {'leader_time': timestamp+DAY, 'symbol': symbol,
                 'leader_daily_return': gain, 'pullback': pullback,
                 'leader_price': leader_price, 'status': 'NO_PULLBACK_WITHIN_30D'}
        for step in range(1, 31):
            t = timestamp + step*DAY
            if t >= cutoff:
                event['status'] = 'WAITING_FOR_PULLBACK_WINDOW'
                break
            if t not in series:
                event['status'] = 'UNKNOWN_MISSING_BAR_BEFORE_ENTRY'
                break
            close = series[t]['close']
            peak = max(peak, close)
            if close <= peak * (1-pullback):
                event['trigger_time'] = t+DAY
                event['peak_at_trigger'] = peak
                if t+DAY >= cutoff or t+DAY not in series:
                    event['status'] = 'ENTRY_PENDING_OR_MISSING'
                else:
                    entry = t+DAY
                    event.update(entry_time=entry, entry_price=series[entry]['open'],
                                 status='OPEN_AT_END', lowest_return=0)
                break
        if entry is not None:
            price = event['entry_price']
            recovery_status = 'NO_ABOVE_ENTRY_CLOSE_WITHIN_30D'
            for recovery_step in range(30):
                recovery_t = entry+recovery_step*DAY
                if recovery_t >= cutoff:
                    recovery_status = 'RECOVERY_WINDOW_UNFINISHED'
                    break
                if recovery_t not in series:
                    recovery_status = 'RECOVERY_UNKNOWN_GAP'
                    break
                if series[recovery_t]['close'] > price:
                    recovery_status = 'ABOVE_ENTRY_CLOSE_OBSERVED'
                    event['hours_to_above_entry_close'] = (recovery_step+1)*24
                    break
            event['above_entry_recovery_status'] = recovery_status
            for step in range(30):
                t = entry+step*DAY
                if t >= cutoff:
                    break
                if t not in series:
                    event['status'] = 'UNKNOWN_MISSING_BAR_WHILE_HELD'
                    break
                bar = series[t]
                event['lowest_return'] = min(event['lowest_return'], bar['low']/price-1)
                event['last_observed_return'] = bar['close']/price-1
                event['last_observed_time'] = t+DAY
                previous = series.get(t-DAY)
                green = previous is not None and bar['close'] > previous['close']
                if green or step == 29:
                    if t+DAY >= cutoff or t+DAY not in series:
                        event['status'] = 'EXIT_PENDING_OR_MISSING'
                        break
                    exit_price = series[t+DAY]['open']
                    event.update(status='GREEN_EXIT' if green else 'TIMEOUT_EXIT',
                                 exit_time=t+DAY, gross_return=exit_price/price-1,
                                 hours_to_exit=(step+1)*24,
                                 above_entry=exit_price > price)
                    break
        events.append(event)
    return events


def analyze(source, output):
    data = json.loads(Path(source).read_text())
    rows = {}
    for symbol, market in data['markets'].items():
        if 'raw' not in market:
            continue
        rows[symbol] = {int(b['start']): {k: float(b[k]) for k in
                                         ('open', 'close', 'low', 'high', 'volume')}
                        for b in market['raw'].get('candles', [])
                        if int(b['start']) < data['cutoff']}
    leaders = []
    counts = []
    for t in range(data['cutoff']-181*DAY, data['cutoff'], DAY):
        candidates = [(s, r[t]['close']/r[t-DAY]['close']-1) for s, r in rows.items()
                      if t in r and t-DAY in r and r[t-DAY]['close'] > 0
                      and r[t]['volume'] > 0]
        counts.append({'time': t+DAY, 'available_markets': len(candidates)})
        if candidates:
            symbol, gain = max(candidates, key=lambda pair: pair[1])
            leaders.append((t, symbol, gain))
    result = {'classification': 'EXPLORATORY_RECONSTRUCTED_DAILY_LEADERS',
              'dataset_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'requested_markets': data['requested'],
              'downloaded_markets': len(rows),
              'failed_markets': [s for s, value in data['markets'].items() if 'error' in value],
              'limits': ['not_exact_live_rolling24h_leaderboard', 'survivorship_bias',
                         'overlapping_events_not_one_portfolio', 'no_net_profit_or_fill_proof',
                         'green_means_positive_daily_close_return_not_profitable_purchase'],
              'coverage_by_day': counts, 'runs': []}
    for threshold in (.10, .20):
        events = events_for(rows, leaders, data['cutoff'], threshold)
        statuses = {}
        for e in events:
            statuses[e['status']] = statuses.get(e['status'], 0)+1
        closed = [e for e in events if 'gross_return' in e]
        recovery_counts = {}
        for e in events:
            status = e.get('above_entry_recovery_status', 'NO_ENTRY')
            recovery_counts[status] = recovery_counts.get(status, 0)+1
        result['runs'].append({'threshold': threshold, 'status_counts': statuses,
                              'above_entry_recovery_counts': recovery_counts,
                              'closed_events': len(closed),
                              'profitable_closed': sum(e['gross_return'] > 0 for e in closed),
                              'events': events})
    with Path(output).open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps([{k: v for k, v in r.items() if k != 'events'}
                      for r in result['runs']], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['collect', 'repair', 'analyze'])
    parser.add_argument('source')
    parser.add_argument('output')
    args = parser.parse_args()
    {'collect': collect, 'repair': repair, 'analyze': analyze}[args.mode](args.source, args.output)
