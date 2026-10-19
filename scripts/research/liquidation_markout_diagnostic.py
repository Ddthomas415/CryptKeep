"""Offline, timestamp-conditioned liquidation markouts; not a trading backtest."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

MINUTE = 60000
RAW = 'research/liquidation_data_probe_raw_20261012.json'
PARENT = 'research/liquidation_data_probe_plan_20261012.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)


def freeze(root, output):
    root = Path(root).resolve()
    parent = json.loads((root / PARENT).read_text())
    save(output, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                  'root': str(root), 'source_sha256': digest(__file__),
                  'inputs': {p: digest(root / p) for p in (RAW, PARENT)},
                  'cutoff_ms': parent['cutoff_ms'], 'assets': parent['assets'],
                  'primary_minutes': 5, 'horizons_minutes': [1, 5, 15],
                  'reference_quote': 1000.0, 'assumed_fee_per_side': .005,
                  'assumed_adverse_price_per_side': .0025,
                  'cost_reference': 'high-cost hypothetical sensitivity only, NOT verified OKX fees or an executable strategy; also report mathematical fee budget without adverse price adjustment',
                  'event': 'one observation per asset per UTC minute containing at least one recorded long/sell liquidation; no size threshold or inferred end of selling',
                  'markout': 'first next-minute candle open to last completed candle close at fixed horizon, requiring every intervening completed minute; not a fill model',
                  'baseline': 'all minute anchors from oldest sampled liquidation minute + 1 through newest sampled liquidation minute + 1, matured per horizon; includes event minutes, not a randomized or no-liquidation control',
                  'dependence': 'report serial overlap and BTC/ETH co-occurrence; separately retain earliest event then only events at least 15 minutes apart per asset, no outcome-dependent selection',
                  'limits': ['two_hour_sample_previously_observed_not_holdout',
                             'no_independence_or_significance_claim',
                             'historical_publication_latency_unknown_not_actionable_signal',
                             'partial_liquidation_feed_and_page_truncation',
                             'no_account_portfolio_or_capacity_model',
                             'fees_not_verified_for_OKX', 'cash_interest_infrastructure_excluded']})


def outcome(candles, anchor, horizon, cutoff, fee, adverse, quote):
    result = {'anchor_ms': anchor, 'horizon_minutes': horizon}
    if anchor + horizon * MINUTE > cutoff:
        return {**result, 'status': 'IMMATURE'}
    grid = list(range(anchor, anchor + horizon * MINUTE, MINUTE))
    if not all(t in candles and candles[t][-1] == '1' for t in grid):
        return {**result, 'status': 'MISSING_OR_UNCONFIRMED_PRICE'}
    prices = [float(candles[t][k]) for t in grid for k in (1, 4)]
    if not all(math.isfinite(p) and p > 0 for p in prices):
        return {**result, 'status': 'INVALID_PRICE'}
    start, finish = float(candles[anchor][1]), float(candles[grid[-1]][4])
    gross = finish / start - 1
    net_reference = finish * (1 - adverse) * (1 - fee) / (start * (1 + adverse) * (1 + fee)) - 1
    return {**result, 'status': 'OBSERVED_PRICE_PATH', 'reference_open': start,
            'forward_close': finish, 'gross_return': gross,
            'gross_move_quote_reference': quote * gross,
            'modeled_cost_adjusted_reference': quote * net_reference}


def summarize(observations):
    valid = [x for x in observations if x['status'] == 'OBSERVED_PRICE_PATH']
    returns = [x['gross_return'] for x in valid]
    values = [x['modeled_cost_adjusted_reference'] for x in valid]
    average = mean(returns) if returns else None
    return {'observations': len(observations), 'observed': len(valid),
            'immature': sum(x['status'] == 'IMMATURE' for x in observations),
            'unknown_price': sum(x['status'] not in ('IMMATURE', 'OBSERVED_PRICE_PATH') for x in observations),
            'price_rebounds': sum(x > 0 for x in returns),
            'price_declines': sum(x < 0 for x in returns),
            'price_unchanged': sum(x == 0 for x in returns),
            'mean_gross_return': average,
            'median_gross_return': median(returns) if returns else None,
            'worst_gross_return': min(returns) if returns else None,
            'best_gross_return': max(returns) if returns else None,
            'mathematical_break_even_fee_per_side_without_adverse': average / (2 + average) if average is not None and average > 0 else None,
            'mean_modeled_cost_adjusted_quote_reference': mean(values) if values else None,
            'positive_cost_adjusted_references': sum(x > 0 for x in values)}


def spaced(anchors, spacing):
    chosen = []
    for anchor in sorted(set(anchors)):
        if not chosen or anchor - chosen[-1] >= spacing:
            chosen.append(anchor)
    return chosen


def analyze_asset(data, plan):
    spot_id = data['definition'][0]['instId'].removesuffix('-SWAP')
    markets = {'spot': data['candles'][spot_id], 'perpetual': data['candles'][spot_id + '-SWAP']}
    markets = {name: {int(k): v for k, v in series.items()} for name, series in markets.items()}
    anchors = sorted({(e['timestamp'] // MINUTE + 1) * MINUTE for e in data['events']
                      if e['position_side'] == 'long' and e['side'] == 'sell'})
    if not data['events']:
        return {'status': 'NO_EVENTS'}
    start = (min(e['timestamp'] for e in data['events']) // MINUTE + 1) * MINUTE
    last = (max(e['timestamp'] for e in data['events']) // MINUTE + 1) * MINUTE
    baseline = list(range(start, last + MINUTE, MINUTE))
    results = {}
    thin = set(spaced(anchors, 15 * MINUTE))
    for name, candles in markets.items():
        results[name] = {}
        for horizon in plan['horizons_minutes']:
            def marks(times):
                return [outcome(candles, t, horizon, plan['cutoff_ms'],
                                plan['assumed_fee_per_side'], plan['assumed_adverse_price_per_side'],
                                plan['reference_quote']) for t in times]
            event_marks, baseline_marks = marks(anchors), marks(baseline)
            event_summary, baseline_summary = summarize(event_marks), summarize(baseline_marks)
            delta = None
            if event_summary['mean_gross_return'] is not None and baseline_summary['mean_gross_return'] is not None:
                delta = event_summary['mean_gross_return'] - baseline_summary['mean_gross_return']
            results[name][str(horizon)] = {'events': event_summary, 'unconditioned': baseline_summary,
                                          'event_minus_unconditioned_mean': delta,
                                          'spaced_event_sensitivity': summarize([x for x in event_marks if x['anchor_ms'] in thin]),
                                          'event_observations': event_marks}
    return {'sell_minute_anchors': anchors, 'spaced_minute_anchors': sorted(thin),
            'baseline_first_anchor': start, 'baseline_last_anchor': last, 'markets': results}


def verify(plan):
    if digest(__file__) != plan['source_sha256']:
        raise ValueError('source_changed')
    for path, expected in plan['inputs'].items():
        if digest(Path(plan['root']) / path) != expected:
            raise ValueError('input_changed:' + path)


def run(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    verify(plan)
    raw = json.loads((Path(plan['root']) / RAW).read_text())
    if raw['plan_sha256'] != plan['inputs'][PARENT]:
        raise ValueError('parent_binding_mismatch')
    for receipt in raw['requests']:
        if 'response_base64' in receipt and hashlib.sha256(base64.b64decode(receipt['response_base64'])).hexdigest() != receipt['response_sha256']:
            raise ValueError('receipt_changed')
    results = {asset: analyze_asset(raw['assets'][asset], plan) for asset in plan['assets']}
    sets = [set(x.get('sell_minute_anchors', [])) for x in results.values()]
    result = {'plan_sha256': digest(plan_path), 'limits': plan['limits'],
              'observed_price_changes': 'OBSERVED_NOT_MID_PRICE_OR_TRADE_FILLS',
              'cost_adjusted_references': 'MODELLED_NOT_PORTFOLIO_PNL',
              'acceptance': 'READY_FOR_INDEPENDENT_REVIEW', 'assets': results,
              'joint_sell_minutes': len(set.union(*sets)),
              'shared_sell_minutes': len(set.intersection(*sets))}
    verify(plan)
    save(output, result)
    primary = str(plan['primary_minutes'])
    print(json.dumps({a: {k: v for k, v in x['markets']['spot'][primary].items() if k != 'event_observations'}
                      for a, x in results.items() if 'markets' in x}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'run'])
    parser.add_argument('--plan', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.action == 'freeze':
        freeze(Path(__file__).resolve().parents[2], args.plan)
    else:
        if not args.output:
            parser.error('--output required for run')
        run(args.plan, args.output)
