"""Frozen, offline failed-downside-breakout research; never submits orders."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tarfile

from services.backtest.price_action_context import _swing_failure

HOUR = 3600
ARCHIVE = 'docs/research/raw_archives_20261009/coinbase_hourly_last60d.tar.xz'
RECENT = 'research/hourly_leader_raw_20261012.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def freeze(root, output):
    root = Path(root).resolve()
    inputs = [ARCHIVE, RECENT,
              'docs/research/raw_archives_20261009/SHA256SUMS_archives.txt',
              'docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt',
              'research/hourly_leader_earlier_plan_20261012.json',
              'research/hourly_leader_plan_20261012.json']
    earlier = json.loads((root / inputs[-2]).read_text())
    recent = json.loads((root / inputs[-1]).read_text())
    sources = ['scripts/research/failed_breakout_retest.py',
               'services/backtest/price_action_context.py']
    save(output, {
        'registered_utc': datetime.now(timezone.utc).isoformat(),
        'root': str(root), 'inputs': {p: digest(root / p) for p in inputs},
        'sources': {p: digest(root / p) for p in sources},
        'start': earlier['start'] + 24 * HOUR, 'boundary': earlier['end'],
        'end': recent['end'], 'initial_cash': 1000.0,
        'lookback': 5, 'retest_hours': 3, 'hold_hours': 24,
        'fee': .005, 'adverse_price': .0025,
        'rule': 'existing bullish swing_failure of prior five bars; freeze prior low/high and sweep low; subsequent retest within three bars with low <= prior low, low > sweep low, and prior low < close < prior high; next-open buy only if sweep low < adverse fill < prior high',
        'exit': 'completed close <= sweep low or >= prior high, or 24 completed holding bars; next-open sale, never a guaranteed stop-price fill',
        'allocation': 'one account all available cash; highest contemporaneous trailing-24h sum(close * base volume), ascending product ID tie; no signals while held; carry across boundary',
        'watch_policy': 'cancel on missing bar, close <= prior low, close >= prior high, or expiry; no same-bar retest; clear all watches only on successful buy',
        'gap_policy': 'missing/nontrading buy open skips; held/exit gap halts with no endpoint NAV; invalid OHLCV aborts load; no filled-in prices',
        'economic_screen': 'ending liquidation estimate exceeds initial cash and same-period BTC; each carried segment positive; this is not statistical validation or promotion',
        'assumptions': [
            'next-open fills with 50 bps fee and 25 bps adverse price per side are modeled, not measured executions',
            'current archived universe and positive-volume bars are a historical eligibility proxy, not point-in-time listing/status proof'],
        'limits': ['previously_explored_data_not_holdout', 'single_fixed_rule_no_parameter_search',
                   'no_depth_or_capacity_proof', 'close_based_drawdown_not_intrabar',
                   'no_statistical_significance_claim', 'cash_interest_and_infrastructure_excluded'],
    })


def validate_bar(t, bar):
    if t % HOUR or not all(math.isfinite(v) for v in bar.values()):
        raise ValueError('invalid_timestamp_or_nonfinite_bar')
    if (min(bar[k] for k in ('open', 'high', 'low', 'close')) <= 0
            or bar['volume'] < 0 or bar['low'] > min(bar['open'], bar['close'])
            or bar['high'] < max(bar['open'], bar['close'])):
        raise ValueError('invalid_ohlcv')


def load_rows(plan):
    root = Path(plan['root'])
    expected = next(line.split()[0] for line in (root /
                    'docs/research/raw_archives_20261009/SHA256SUMS_archives.txt').read_text().splitlines()
                    if line.split()[1] == 'coinbase_hourly_last60d.tar.xz')
    if digest(root / ARCHIVE) != expected:
        raise ValueError('archive_checksum_mismatch')
    checksums = {line.split()[1].lstrip('./'): line.split()[0]
                 for line in (root / 'docs/research/raw_archives_20261009/SHA256SUMS_inputs.txt').read_text().splitlines()}
    rows = {}
    verified = 0

    def add(symbol, t, bar, lower, upper):
        if not lower <= t < upper:
            return
        validate_bar(t, bar)
        series = rows.setdefault(symbol, {})
        if t in series:
            raise ValueError('duplicate_bar:' + symbol)
        series[t] = bar

    # Read members in memory; never extract into or modify the original archive.
    with tarfile.open(root / ARCHIVE, 'r:xz') as archive:
        for member in archive:
            if not (member.isfile() and member.name.startswith('cb/h1/')
                    and member.name.endswith('-USD.json')):
                continue
            raw = archive.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest() != checksums.get(member.name):
                raise ValueError('member_checksum_mismatch:' + member.name)
            verified += 1
            for values in json.loads(raw):
                bar = dict(zip(('open', 'high', 'low', 'close', 'volume'), map(float, values[1:6])))
                add(Path(member.name).stem, int(values[0]), bar,
                    plan['start'] - 24 * HOUR, plan['boundary'])
    data = json.loads((root / RECENT).read_text())
    for symbol, market in data['markets'].items():
        for candle in market.get('raw', {}).get('candles', []):
            bar = {k: float(candle[k]) for k in ('open', 'high', 'low', 'close', 'volume')}
            add(symbol, int(candle['start']), bar, plan['boundary'], plan['end'])
    if verified != 395:
        raise ValueError('unexpected_archive_member_count')
    return rows, verified


def signal(series, t, lookback):
    timestamps = [t - k * HOUR for k in range(lookback, -1, -1)]
    if not all(ts in series for ts in timestamps) or series[t]['volume'] <= 0:
        return None
    candles = [[ts, *[series[ts][k] for k in ('open', 'high', 'low', 'close', 'volume')]]
               for ts in timestamps]
    if _swing_failure(candles, lookback, lookback) != 'bullish':
        return None
    return {'sweep_time': t, 'floor': min(c[3] for c in candles[:-1]),
            'ceiling': max(c[2] for c in candles[:-1]), 'stop': series[t]['low']}


def simulate(rows, plan):
    cash = float(plan['initial_cash'])
    position = pending = None
    watches = {}
    trades, equity, decisions = [], [], []
    peak = cash
    drawdown = 0.0
    status, halted_at, checkpoint = 'COMPLETE', None, None
    counts = {'sweeps': 0, 'confirmed_retests': 0, 'unknown_liquidity': 0}
    for t in range(plan['start'], plan['end'], HOUR):
        if pending:
            bar = rows[pending['symbol']].get(t)
            if pending['side'] == 'sell':
                if bar is None or bar['volume'] <= 0:
                    status, halted_at = 'INCOMPLETE_EXIT_PRICE_GAP', t
                    break
                fill = bar['open'] * (1 - plan['adverse_price'])
                cash = position['quantity'] * fill * (1 - plan['fee'])
                trades.append({**position, 'exit_time': t, 'exit_price': fill,
                               'exit_reason': pending['reason'], 'cash_after_exit': cash,
                               'net_pnl_usd': cash - position['cash_at_entry']})
                position = None
            elif bar is None or bar['volume'] <= 0:
                decisions.append({'time': t, 'symbol': pending['symbol'], 'kind': 'ENTRY_SKIPPED_PRICE_GAP'})
            else:
                fill = bar['open'] * (1 + plan['adverse_price'])
                if not pending['stop'] < fill < pending['ceiling']:
                    decisions.append({'time': t, 'symbol': pending['symbol'], 'kind': 'ENTRY_SKIPPED_OUTSIDE_RANGE'})
                else:
                    position = {k: v for k, v in pending.items() if k != 'side'}
                    position.update(entry_time=t, entry_price=fill, cash_at_entry=cash,
                                    quantity=cash / (fill * (1 + plan['fee'])))
                    cash = 0.0
                    watches.clear()
            pending = None
        if position:
            bar = rows[position['symbol']].get(t)
            if bar is None or bar['volume'] <= 0:
                status, halted_at = 'INCOMPLETE_HELD_PRICE_GAP', t
                break
            nav = position['quantity'] * bar['close'] * (1 - plan['adverse_price']) * (1 - plan['fee'])
            reason = ('STOP_CLOSE' if bar['close'] <= position['stop'] else
                      'RANGE_TARGET_CLOSE' if bar['close'] >= position['ceiling'] else
                      'TIMEOUT' if (t - position['entry_time']) // HOUR + 1 >= plan['hold_hours'] else None)
            if reason:
                pending = {'side': 'sell', 'symbol': position['symbol'], 'reason': reason}
        else:
            nav = cash
            candidates = []
            for symbol, watch in list(watches.items()):
                bar = rows[symbol].get(t)
                if (bar is None or t - watch['sweep_time'] > plan['retest_hours'] * HOUR
                        or not watch['floor'] < bar['close'] < watch['ceiling']):
                    del watches[symbol]
                    continue
                if bar['low'] <= watch['floor'] and bar['low'] > watch['stop'] and bar['volume'] > 0:
                    del watches[symbol]
                    counts['confirmed_retests'] += 1
                    series = rows[symbol]
                    if not all(t - k * HOUR in series for k in range(24)):
                        counts['unknown_liquidity'] += 1
                        continue
                    dollar_volume = sum(series[t - k * HOUR]['close'] * series[t - k * HOUR]['volume'] for k in range(24))
                    if dollar_volume > 0:
                        candidates.append({**watch, 'symbol': symbol, 'decision_time': t + HOUR,
                                           'dollar_volume_proxy': dollar_volume})
            if candidates:
                chosen = min(candidates, key=lambda x: (-x['dollar_volume_proxy'], x['symbol']))
                pending = {**chosen, 'side': 'buy'}
            # A new sweep cannot confirm itself. Maintain other watches if entry fails.
            for symbol, series in rows.items():
                found = signal(series, t, plan['lookback'])
                if found and found['floor'] < series[t]['close'] < found['ceiling']:
                    counts['sweeps'] += 1
                    if symbol not in watches:
                        watches[symbol] = found
        peak = max(peak, nav)
        drawdown = min(drawdown, nav / peak - 1)
        equity.append({'time': t + HOUR, 'nav': nav, 'cash': cash,
                       'kind': 'MODELED_LIQUIDATION_NOT_FILL' if position else 'MODELED_CASH'})
        if t + HOUR == plan.get('boundary'):
            checkpoint = {'time': t + HOUR, 'nav': nav, 'cash': cash,
                          'held_symbol': position['symbol'] if position else None}
    return {'status': status, 'halted_at': halted_at,
            'ending_nav': equity[-1]['nav'] if equity and status == 'COMPLETE' else None,
            'last_known_nav': equity[-1] if equity else None, 'ending_cash': cash,
            'position': position, 'pending': pending, 'checkpoint': checkpoint,
            'closed_trade_count': len(trades), 'closed_winners': sum(t['net_pnl_usd'] > 0 for t in trades),
            'max_observed_close_drawdown': drawdown, 'counts': counts,
            'trades': trades, 'decisions': decisions, 'equity': equity}


def benchmark(rows, plan):
    series = rows.get('BTC-USD', {})
    grid = range(plan['start'], plan['end'], HOUR)
    if not all(t in series and series[t]['volume'] > 0 for t in grid):
        return {'status': 'INCOMPLETE_BTC_PRICE_GRID'}
    quantity = plan['initial_cash'] / (series[plan['start']]['open'] * (1 + plan['adverse_price']) * (1 + plan['fee']))
    values = [plan['initial_cash']] + [quantity * series[t]['close'] * (1 - plan['adverse_price']) * (1 - plan['fee']) for t in grid]
    peak, drawdown = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)
    checkpoint = next((quantity * series[t]['close'] * (1 - plan['adverse_price']) * (1 - plan['fee'])
                       for t in grid if t + HOUR == plan.get('boundary')), None)
    return {'status': 'COMPLETE', 'ending_liquidation_estimate': values[-1],
            'checkpoint_nav': checkpoint, 'max_close_drawdown': drawdown}


def verify(plan):
    root = Path(plan['root'])
    for path, expected in {**plan['inputs'], **plan['sources']}.items():
        if digest(root / path) != expected:
            raise ValueError('frozen_input_or_source_changed:' + path)


def run(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    verify(plan)
    rows, verified = load_rows(plan)
    account = simulate(rows, plan)
    btc = benchmark(rows, plan)
    result = {'plan_sha256': digest(plan_path), 'evidence': 'MODELLED',
              'acceptance': 'READY_FOR_INDEPENDENT_REVIEW', 'members_verified': verified,
              'symbols': len(rows), 'assumptions': plan['assumptions'], 'limits': plan['limits'],
              'single_account': account, 'btc_hold': btc}
    if account['status'] == 'COMPLETE' and btc['status'] == 'COMPLETE' and account['checkpoint']:
        checkpoint = account['checkpoint']['nav']
        result['carried_segments'] = {
            'earlier_return': checkpoint / plan['initial_cash'] - 1,
            'recent_return': account['ending_nav'] / checkpoint - 1,
            'btc_earlier_return': btc['checkpoint_nav'] / plan['initial_cash'] - 1,
            'btc_recent_return': btc['ending_liquidation_estimate'] / btc['checkpoint_nav'] - 1,
        }
        result['economic_screen'] = ('PASS_CANDIDATE_NOT_VALIDATION' if
            account['ending_nav'] > max(plan['initial_cash'], btc['ending_liquidation_estimate'])
            and min(result['carried_segments']['earlier_return'], result['carried_segments']['recent_return']) > 0
            else 'FAIL')
    else:
        result['economic_screen'] = 'INCOMPLETE'
    verify(plan)
    save(output, result)
    print(json.dumps({'status': account['status'], 'screen': result['economic_screen'],
                      'closed_trades': account['closed_trade_count'], 'net_winners': account['closed_winners'],
                      'ending_nav': account['ending_nav'], 'btc': btc,
                      'segments': result.get('carried_segments')}))


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
