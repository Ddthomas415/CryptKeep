"""Exploratory, non-overlapping dip recovery screen; never submits orders."""
import hashlib
import json
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]


def screen(bars, interval, lookback, target, horizon):
    bars = sorted(bars, key=lambda b: int(b['start']))
    events = []
    i = lookback
    while i + horizon + 1 < len(bars):
        window = bars[i-lookback:i+horizon+2]
        if any(int(b['start']) - int(a['start']) != interval
               for a, b in zip(window, window[1:])):
            i += 1
            continue
        close = float(bars[i]['close'])
        old = float(bars[i-lookback]['close'])
        prior = float(bars[i-1]['close'])
        prior_old = float(bars[i-lookback-1]['close']) if i > lookback else None
        crossed = close < old and (lookback == 1 or
                                   (prior_old is not None and prior >= prior_old))
        if not crossed:
            i += 1
            continue
        entry_index = i + 1
        entry = float(bars[entry_index]['open'])
        if entry <= 0:
            raise ValueError('invalid_entry')
        exit_index = entry_index + horizon
        hit = False
        lows = []
        for j in range(entry_index, entry_index+horizon):
            lows.append(float(bars[j]['low']) / entry - 1)
            if float(bars[j]['close']) / entry - 1 >= target:
                exit_index = j + 1
                hit = True
                break
        exit_price = float(bars[exit_index]['open'])
        gross = exit_price / entry - 1
        # Sensitivity only, not verified retail costs; gross remains separate.
        net = exit_price / entry * 0.995 / 1.005 - 1
        events.append({'entry_time': int(bars[entry_index]['start']),
                       'exit_time': int(bars[exit_index]['start']),
                       'target_close_reached': hit,
                       'hours': (exit_index-entry_index)*interval/3600,
                       'gross_return': gross, 'fee_only_return': net,
                       'worst_intrabar_return': min(lows)})
        i = exit_index
    gross = [e['gross_return'] for e in events]
    net = [e['fee_only_return'] for e in events]
    hits = [e for e in events if e['target_close_reached']]
    return {'events': events, 'n': len(events), 'target_hits': len(hits),
            'recovery_rate': len(hits)/len(events) if events else None,
            'mean_gross_return': mean(gross) if gross else None,
            'median_gross_return': median(gross) if gross else None,
            'mean_fee_only_return': mean(net) if net else None,
            'mean_hit_hours': mean(e['hours'] for e in hits) if hits else None,
            'worst_return': min(gross) if gross else None,
            'compounded_gross_end_usd': 1000 * product(1+r for r in gross),
            'compounded_fee_only_end_usd': 1000 * product(1+r for r in net)}


def product(values):
    result = 1
    for value in values:
        result *= value
    return result


def main():
    sources = ['research/reversal_scan_20261012T145033Z.json',
               'research/candle_strategy_diagnostic_20261012T143118Z.json']
    output = {'classification': 'EXPLORATORY_CF_MODELLED_NOT_HOLDOUT',
              'source_hashes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
              'rules': 'Next-open entry; target on completed close; next-open exit; no overlapping positions; terminal incomplete events excluded',
              'limits': ['already_selected_markets', 'multiple_comparisons_no_selection_correction',
                         'no_spread_slippage_or_live_fill_proof', 'no_strategy_change',
                         'fixed_targets_not_optimized', 'no_statistical_edge_claim'], 'runs': []}
    daily = json.loads((ROOT/sources[0]).read_text())
    hourly = json.loads((ROOT/sources[1]).read_text())
    for symbol, data in daily['markets'].items():
        if data.get('status') != 'GRID_VERIFIED':
            continue
        for target in (0.03, 0.05):
            output['runs'].append({'symbol': symbol, 'question': 'negative_daily_close_return',
                                   'target': target, 'max_hold_hours': 168,
                                   'result': screen(data['raw_candles']['candles'], 86400, 1, target, 7)})
    for symbol, data in hourly['markets'].items():
        bars = data['1h']['raw_candles']['candles']
        for lookback in (1, 24):
            for target in (0.03, 0.05):
                output['runs'].append({'symbol': symbol,
                                       'question': 'negative_hourly_return' if lookback == 1 else '24h_cross_to_red',
                                       'target': target, 'max_hold_hours': 48,
                                       'result': screen(bars, 3600, lookback, target, 48)})
    path = ROOT/'research/dip_recovery_screen_20261012.json'
    with path.open('x') as stream:
        json.dump(output, stream, indent=2)
    for row in output['runs']:
        r = row['result']
        print(row['symbol'], row['question'], row['target'], r['n'], r['target_hits'],
              r['mean_gross_return'], r['mean_hit_hours'], r['compounded_gross_end_usd'])


if __name__ == '__main__':
    main()
