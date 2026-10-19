"""Frozen volume/BTC hypothesis fork; baseline source and results preserved."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

HOUR = 3600


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def freeze(root, output):
    root = Path(root)
    inputs = ['research/hourly_leader_earlier_raw_20261012.json',
              'research/hourly_leader_raw_20261012.json',
              'research/hourly_leader_earlier_plan_20261012.json',
              'research/hourly_leader_plan_20261012.json']
    old = json.loads((root/inputs[2]).read_text())
    recent = json.loads((root/inputs[3]).read_text())
    save(output, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                  'source_sha256': digest(__file__), 'root': str(root.resolve()),
                  'inputs': {p: digest(root/p) for p in inputs},
                  'start': old['start']+24*HOUR,
                  'boundary': recent['start']+24*HOUR, 'end': recent['end'],
                  'initial_cash': 1000, 'dip': .2, 'target': .05,
                  'hold_hours': 48, 'wait_hours': 72, 'fee': .005, 'spread': .0025,
                  'selection': 'first qualifying while flat; oldest leader then product ID tie; watches cleared at successful entry; no signals while held',
                  'entry_filter': True, 'volume_hours': 6,
                  'hypothesis': 'positive completed BTC24h return AND last6h coin base volume > prior6h volume; no threshold search',
                  'baseline_source_sha256': digest(root/'scripts/research/leader_single_account.py'),
                  'gap_policy': 'halt on missing held/exit price, skip missing pending entry without spending cash',
                  'source_policy': 'earlier bars strictly before boundary, recent bars from boundary; recent warmup never overwrites earlier bars',
                  'limits': ['current_universe_rankable_subset', 'no_exact_historical_live_leaderboard',
                             'assumed_execution_costs', 'historical_research_not_holdout',
                             'new_frozen_allocation_rule_not_original_event_portfolio']})


def context_gate(rows, symbol, t):
    btc = rows.get('BTC-USD', {})
    coin = rows.get(symbol, {})
    if not all(t-k*HOUR in btc for k in range(25)):
        return {'pass': False, 'reason': 'UNKNOWN_BTC_HISTORY'}
    if not all(t-k*HOUR in coin for k in range(12)):
        return {'pass': False, 'reason': 'UNKNOWN_VOLUME_HISTORY'}
    prior = sum(coin[t-k*HOUR]['volume'] for k in range(6, 12))
    recent = sum(coin[t-k*HOUR]['volume'] for k in range(6))
    btc_return = btc[t]['close']/btc[t-24*HOUR]['close']-1
    if prior <= 0 or recent < 0:
        return {'pass': False, 'reason': 'UNKNOWN_VOLUME_BASE'}
    return {'pass': btc_return > 0 and recent > prior,
            'reason': 'PASS' if btc_return > 0 and recent > prior else 'CONDITION_NOT_MET',
            'btc_return24h': btc_return, 'volume_ratio': recent/prior,
            'feature_cutoff': t+HOUR}


def simulate(rows, plan):
    cash = float(plan['initial_cash'])
    position = None
    pending = None
    watches = []
    trades = []
    decisions = []
    equity = [{'time': plan['start'], 'nav': cash, 'kind': 'INITIAL_CASH'}]
    peak_nav = cash
    max_dd = 0
    status = 'COMPLETE'
    halted_at = None
    checkpoint = None
    for t in range(plan['start'], plan['end'], HOUR):
        if pending:
            series = rows.get(pending['symbol'], {})
            if t not in series:
                if pending['side'] == 'sell':
                    status = 'INCOMPLETE_EXIT_PRICE_GAP'; halted_at = t; break
                decisions.append({'time': t, 'kind': 'ENTRY_SKIPPED_MISSING_OPEN', 'symbol': pending['symbol']})
                pending = None
            else:
                if pending['side'] == 'buy':
                    price = series[t]['open']*(1+plan['spread'])
                    position = {'symbol': pending['symbol'], 'entry_time': t, 'entry_price': price,
                                'quantity': cash/(price*(1+plan['fee'])), 'cash_at_entry': cash,
                                'trigger_time': pending['trigger_time'], 'leader_time': pending['leader_time']}
                    cash = 0
                    watches = []
                else:
                    price = series[t]['open']*(1-plan['spread'])
                    cash = position['quantity']*price*(1-plan['fee'])
                    trades.append({**position, 'exit_time': t, 'exit_price': price,
                                   'exit_reason': pending['reason'], 'cash_after_exit': cash,
                                   'net_pnl_usd': cash-position['cash_at_entry']})
                    position = None
                pending = None
        if position:
            series = rows[position['symbol']]
            if t not in series:
                status = 'INCOMPLETE_HELD_PRICE_GAP'; halted_at = t; break
            close = series[t]['close']
            nav = cash+position['quantity']*close*(1-plan['spread'])*(1-plan['fee'])
            held_hours = (t-position['entry_time'])//HOUR+1
            target_hit = close >= position['entry_price']*(1+plan['target'])
            if target_hit or held_hours >= plan['hold_hours']:
                pending = {'symbol': position['symbol'], 'side': 'sell',
                           'reason': 'TARGET' if target_hit else 'TIMEOUT'}
            kind = 'HELD_LIQUIDATION_ESTIMATE_NOT_FILL'
        else:
            nav = cash
            kind = 'CASH'
            candidates = []
            retained = []
            for watch in watches:
                series = rows[watch['symbol']]
                age = (t-watch['leader_bar'])//HOUR
                if age > plan['wait_hours']:
                    continue
                if t not in series:
                    decisions.append({'time': t+HOUR, 'kind': 'WATCH_DROPPED_GAP', 'symbol': watch['symbol']})
                    continue
                watch['peak'] = max(watch['peak'], series[t]['close'])
                if series[t]['close'] <= watch['peak']*(1-plan['dip']):
                    context = context_gate(rows, watch['symbol'], t) if plan.get('entry_filter') else {'pass': True, 'reason': 'BASELINE'}
                    if context['pass']:
                        candidates.append(watch)
                    else:
                        decisions.append({'time': t+HOUR, 'kind': 'FILTER_REFUSAL', 'symbol': watch['symbol'], 'context': context})
                else:
                    retained.append(watch)
            watches = retained
            if candidates:
                chosen = min(candidates, key=lambda w: (w['leader_bar'], w['symbol']))
                pending = {'side': 'buy', 'symbol': chosen['symbol'], 'trigger_time': t+HOUR,
                           'leader_time': chosen['leader_bar']+HOUR}
                decisions.append({'time': t+HOUR, 'kind': 'ENTRY_SCHEDULED', 'symbol': chosen['symbol']})
                watches = retained+[w for w in candidates if w is not chosen]
            else:
                rankable = [(s, r[t]['close']/r[t-24*HOUR]['close']-1)
                            for s, r in rows.items() if all(t-k*HOUR in r for k in range(25))
                            and r[t]['volume'] > 0]
                if rankable:
                    symbol, gain = max(rankable, key=lambda x: (x[1], x[0]))
                    watches.append({'symbol': symbol, 'leader_bar': t, 'peak': rows[symbol][t]['close']})
        peak_nav = max(peak_nav, nav)
        max_dd = min(max_dd, nav/peak_nav-1)
        equity.append({'time': t+HOUR, 'nav': nav, 'kind': kind})
        if t+HOUR == plan.get('boundary'):
            checkpoint = {'time': t+HOUR, 'nav': nav, 'cash': cash,
                          'position_symbol': position['symbol'] if position else None}
    return {'status': status, 'halted_at': halted_at, 'ending_cash': cash,
            'ending_nav': equity[-1]['nav'] if status == 'COMPLETE' else None,
            'last_known_nav': equity[-1], 'position': position, 'pending': pending,
            'closed_trade_count': len(trades), 'closed_winners': sum(t['net_pnl_usd'] > 0 for t in trades),
            'max_observed_close_drawdown': max_dd, 'checkpoint': checkpoint,
            'trades': trades, 'decisions': decisions, 'equity': equity}


def rows_from(plan):
    root = Path(plan['root'])
    older = json.loads((root/'research/hourly_leader_earlier_raw_20261012.json').read_text())
    recent = json.loads((root/'research/hourly_leader_raw_20261012.json').read_text())
    rows = {}
    for data, lower, upper in [(older, plan['start']-24*HOUR, plan['boundary']),
                                (recent, plan['boundary'], plan['end'])]:
        for symbol, market in data['markets'].items():
            if 'raw' not in market: continue
            series = rows.setdefault(symbol, {})
            for bar in market['raw'].get('candles', []):
                t = int(bar['start'])
                if not lower <= t < upper: continue
                values = {k: float(bar[k]) for k in ('open', 'close', 'volume')}
                if t in series or not all(math.isfinite(v) for v in values.values()) or min(values['open'], values['close']) <= 0:
                    raise ValueError('invalid_or_duplicate_bar')
                series[t] = values
    return rows


def run(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256'] or any(digest(Path(plan['root'])/p) != h for p,h in plan['inputs'].items()):
        raise ValueError('frozen_inputs_changed')
    rows = rows_from(plan)
    result = {'plan_sha256': digest(plan_path), 'limits': plan['limits'],
              'single_account': simulate(rows, plan),
              'baseline_control': simulate(rows, dict(plan, entry_filter=False))}
    btc = rows.get('BTC-USD', {})
    start, last = plan['start'], plan['end']-HOUR
    if start in btc and all(t in btc for t in range(start, plan['end'], HOUR)):
        quantity = plan['initial_cash']/(btc[start]['open']*(1+plan['spread'])*(1+plan['fee']))
        values = [plan['initial_cash']]+[quantity*btc[t]['close']*(1-plan['spread'])*(1-plan['fee']) for t in range(start, plan['end'], HOUR)]
        peak = values[0]; drawdown = 0
        for value in values:
            peak = max(peak, value); drawdown = min(drawdown, value/peak-1)
        result['btc_hold'] = {'ending_liquidation_estimate': values[-1], 'max_close_drawdown': drawdown}
    else:
        result['btc_hold'] = {'status': 'INCOMPLETE_PRICE_GRID'}
    if any(digest(Path(plan['root'])/p) != h for p,h in plan['inputs'].items()):
        raise ValueError('inputs_changed_during_run')
    save(output, result)
    account = result['single_account']
    print(json.dumps({k: account[k] for k in ('status','closed_trade_count','closed_winners','ending_cash','ending_nav','last_known_nav','max_observed_close_drawdown','checkpoint')}, indent=2))
    baseline = result['baseline_control']
    print('BASELINE', {k: baseline[k] for k in ('status','ending_nav','closed_trade_count','max_observed_close_drawdown')})
    print('BTC', result['btc_hold'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['freeze','run'])
    parser.add_argument('source'); parser.add_argument('output'); args = parser.parse_args()
    (freeze if args.mode == 'freeze' else run)(args.source, args.output)

