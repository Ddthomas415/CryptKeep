"""Frozen target-exit event study. No production changes or portfolio claims."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import mean

DAY = 86400


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(dataset, plan):
    data = json.loads(Path(dataset).read_text())
    cutoff = data['cutoff']
    contract = {'dataset': str(Path(dataset).resolve()), 'dataset_sha256': digest(dataset),
                'source_sha256': digest(__file__), 'fee_per_side': .005,
                'adverse_price_per_side': .0025, 'budget_per_event_usd': 1000,
                'pullbacks': [.1, .2], 'targets': [.05, .1], 'hold_days': [7, 14],
                'windows': [[cutoff-182*DAY, cutoff-91*DAY], [cutoff-91*DAY, cutoff]],
                'rules': 'UTC daily leader; closing running peak; 30d wait for dip; next-open entry; close-triggered target; next-open exit; terminal open events retained; event overlap allowed, not a portfolio',
                'limitations': ['current_universe_no_delisted_coverage',
                               'daily_proxy_not_exact_live_leaderboard',
                               'spread_assumption_not_historical_quotes',
                               'already_explored_history_not_holdout',
                               'eight_comparisons_no_multiple_testing_adjustment']}
    with Path(plan).open('x') as stream:
        json.dump(contract, stream, indent=2)


def simulate(series, leader_t, end, pullback, target, hold, fee, spread):
    event = {'leader_bar': leader_t, 'status': 'NO_DIP_WITHIN_30D'}
    peak = series[leader_t]['close']
    entry_t = None
    for step in range(1, 31):
        t = leader_t+step*DAY
        if t >= end:
            event['status'] = 'WAITING_AT_SEGMENT_END'
            return event
        if t not in series:
            event['status'] = 'UNKNOWN_PRE_ENTRY_GAP'
            return event
        peak = max(peak, series[t]['close'])
        if series[t]['close'] <= peak*(1-pullback):
            entry_t = t+DAY
            if entry_t >= end:
                event['status'] = 'ENTRY_PENDING_AT_SEGMENT_END'
                return event
            if entry_t not in series:
                event['status'] = 'UNKNOWN_ENTRY_GAP'
                return event
            break
    if entry_t is None:
        return event
    entry = series[entry_t]['open']*(1+spread)
    event.update(entry_time=entry_t, entry_price=entry, status='OPEN_AT_SEGMENT_END')
    # Fixed $1000 includes entry fee, so no hidden extra capital per event.
    quantity = 1000/(entry*(1+fee))
    peak_nav = 1000
    drawdown = 0
    for step in range(hold):
        t = entry_t+step*DAY
        if t >= end:
            return event
        if t not in series:
            event['status'] = 'UNKNOWN_HELD_GAP'
            return event
        close = series[t]['close']
        nav = quantity*close*(1-spread)*(1-fee)
        peak_nav = max(peak_nav, nav)
        drawdown = min(drawdown, nav/peak_nav-1)
        event.update(last_mark_time=t+DAY, last_mark_net_pnl_usd=nav-1000,
                     max_close_drawdown=drawdown)
        hit = close >= entry*(1+target)
        if hit or step == hold-1:
            exit_t = t+DAY
            if exit_t >= end:
                event['status'] = 'EXIT_PENDING_AT_SEGMENT_END'
                return event
            if exit_t not in series:
                event['status'] = 'UNKNOWN_EXIT_GAP'
                return event
            exit_price = series[exit_t]['open']*(1-spread)
            proceeds = quantity*exit_price*(1-fee)
            drawdown = min(drawdown, proceeds/peak_nav-1)
            event.update(status='TARGET_EXIT' if hit else 'TIMEOUT_EXIT',
                         exit_time=exit_t, net_pnl_usd=proceeds-1000,
                         gross_return=series[exit_t]['open']/series[entry_t]['open']-1,
                         max_close_drawdown=drawdown, holding_days=step+1)
            return event
    return event


def summary(events):
    closed = [e for e in events if 'net_pnl_usd' in e]
    matched = [e for e in closed if 'btc_net_pnl_usd' in e]
    return {'leader_events': len(events), 'statuses': dict(Counter(e['status'] for e in events)),
            'entries': sum('entry_time' in e for e in events), 'closed_trades': len(closed),
            'net_winners': sum(e['net_pnl_usd'] > 0 for e in closed),
            'average_net_usd': mean(e['net_pnl_usd'] for e in closed) if closed else None,
            'worst_net_usd': min((e['net_pnl_usd'] for e in closed), default=None),
            'sum_closed_net_usd_not_portfolio': sum(e['net_pnl_usd'] for e in closed),
            'matched_btc_trades': len(matched),
            'matched_btc_sum_usd': sum(e['btc_net_pnl_usd'] for e in matched),
            'matched_strategy_sum_usd': sum(e['net_pnl_usd'] for e in matched),
            'worst_individual_close_drawdown': min((e.get('max_close_drawdown', 0) for e in events), default=0),
            'events': events}


def run(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256'] or digest(plan['dataset']) != plan['dataset_sha256']:
        raise ValueError('frozen_source_or_data_changed')
    data = json.loads(Path(plan['dataset']).read_text())
    rows = {s: {int(b['start']): {k: float(b[k]) for k in ('open', 'close', 'volume')}
                for b in v['raw'].get('candles', []) if int(b['start']) < data['cutoff']}
            for s, v in data['markets'].items() if 'raw' in v}
    result = {'plan_sha256': digest(plan_path), 'limits': plan['limitations'], 'runs': []}
    for pullback in plan['pullbacks']:
        for target in plan['targets']:
            for hold in plan['hold_days']:
                segments = []
                for start, end in plan['windows']:
                    events = []
                    for t in range(start, end-DAY, DAY):
                        candidates = [(s, r[t]['close']/r[t-DAY]['close']-1)
                                      for s, r in rows.items() if t in r and t-DAY in r
                                      and r[t-DAY]['close'] > 0 and r[t]['volume'] > 0]
                        if not candidates:
                            continue
                        symbol, gain = max(candidates, key=lambda pair: pair[1])
                        e = simulate(rows[symbol], t, end, pullback, target, hold,
                                     plan['fee_per_side'], plan['adverse_price_per_side'])
                        e.update(symbol=symbol, leader_gain=gain)
                        if 'net_pnl_usd' in e:
                            btc = rows.get('BTC-USD', {})
                            a, b = e['entry_time'], e['exit_time']
                            if a in btc and b in btc:
                                ratio = btc[b]['open']*(1-plan['adverse_price_per_side'])/(btc[a]['open']*(1+plan['adverse_price_per_side']))
                                e['btc_net_pnl_usd'] = 1000*(ratio*(1-plan['fee_per_side'])/(1+plan['fee_per_side'])-1)
                        events.append(e)
                    segments.append({'start': start, 'end': end, **summary(events)})
                result['runs'].append({'pullback': pullback, 'target': target, 'hold': hold,
                                       'segments': segments,
                                       'combined': summary([e for seg in segments for e in seg['events']])})
    if digest(plan['dataset']) != plan['dataset_sha256']:
        raise ValueError('data_changed_during_run')
    with Path(output).open('x') as stream:
        json.dump(result, stream, indent=2)
    for row in result['runs']:
        print(row['pullback'], row['target'], row['hold'],
              [(s['closed_trades'], s['net_winners'], round(s['average_net_usd'],2) if s['average_net_usd'] is not None else None,
                round(s['sum_closed_net_usd_not_portfolio'],2), round(s['matched_btc_sum_usd'],2)) for s in row['segments']])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['freeze', 'run'])
    p.add_argument('source')
    p.add_argument('output')
    args = p.parse_args()
    (freeze if args.mode == 'freeze' else run)(args.source, args.output)
