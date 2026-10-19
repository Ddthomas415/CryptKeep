"""Explicit sparse-price sensitivity, preserving the original strict replay."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.research.failed_breakout_retest import (
    HOUR, benchmark, digest, load_rows, save, signal, verify,
)

PARENT = 'research/failed_breakout_retest_plan_20261012.json'


def freeze(root, output):
    root = Path(root).resolve()
    parent = json.loads((root / PARENT).read_text())
    verify(parent)
    plan = deepcopy(parent)
    plan['registered_utc'] = datetime.now(timezone.utc).isoformat()
    plan['inputs'][PARENT] = digest(root / PARENT)
    plan['sources']['scripts/research/failed_breakout_gap_replay.py'] = digest(__file__)
    plan['version'] = 'gap_sensitivity_v2_not_original_strict_test'
    plan['gap_policy'] = 'same recorded data; missing/nontrading held bars produce null NAV and no close decision; keep cash/position; pending sells defer to first recorded positive-volume open; no stale or invented prices; null endpoint remains incomplete'
    plan['watch_policy'] = 'all confirmed but unselected watches remain until invalidation/expiry or a successful buy; no same-bar retest; skip missing buy without spending cash'
    plan['limits'] += ['post_strict_result_data_policy_amendment_not_fresh_evidence',
                       'unknown_nav_hours_make_drawdown_a_lower_bound_on_sampled_drawdown',
                       'deferred_sells_change_modeled_execution_timing_not_signal_thresholds']
    save(output, plan)


def simulate(rows, plan):
    cash = float(plan['initial_cash'])
    position = pending = None
    watches = {}
    trades, equity, decisions = [], [], []
    peak, drawdown, checkpoint = cash, 0.0, None
    counts = {'sweeps': 0, 'confirmed_retest_observations': 0,
              'unknown_liquidity': 0, 'unknown_nav_hours': 0,
              'deferred_exit_hours': 0}

    def record(t, nav):
        nonlocal peak, drawdown, checkpoint
        if nav is not None:
            peak = max(peak, nav)
            drawdown = min(drawdown, nav / peak - 1)
        equity.append({'time': t + HOUR, 'nav': nav, 'cash': cash,
                       'kind': 'UNVALUED_HELD_GAP' if nav is None else
                       'MODELED_LIQUIDATION_NOT_FILL' if position else 'MODELED_CASH'})
        if t + HOUR == plan.get('boundary'):
            checkpoint = {'time': t + HOUR, 'nav': nav, 'cash': cash,
                          'held_symbol': position['symbol'] if position else None}

    for t in range(plan['start'], plan['end'], HOUR):
        if pending:
            bar = rows[pending['symbol']].get(t)
            if pending['side'] == 'sell':
                if bar is None or bar['volume'] <= 0:
                    counts['unknown_nav_hours'] += 1
                    counts['deferred_exit_hours'] += 1
                    record(t, None)
                    continue
                fill = bar['open'] * (1 - plan['adverse_price'])
                cash = position['quantity'] * fill * (1 - plan['fee'])
                trade = {**position, 'exit_time': t, 'exit_price': fill,
                         'exit_reason': pending['reason'],
                         'scheduled_exit_time': pending['scheduled_exit_time'],
                         'cash_after_exit': cash,
                         'net_pnl_usd': cash - position['cash_at_entry']}
                trades.append(trade)
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
                counts['unknown_nav_hours'] += 1
                record(t, None)
                continue
            nav = position['quantity'] * bar['close'] * (1 - plan['adverse_price']) * (1 - plan['fee'])
            reason = ('STOP_CLOSE' if bar['close'] <= position['stop'] else
                      'RANGE_TARGET_CLOSE' if bar['close'] >= position['ceiling'] else
                      'TIMEOUT' if (t - position['entry_time']) // HOUR + 1 >= plan['hold_hours'] else None)
            if reason:
                pending = {'side': 'sell', 'symbol': position['symbol'], 'reason': reason,
                           'scheduled_exit_time': t + HOUR}
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
                    counts['confirmed_retest_observations'] += 1
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
            for symbol, series in rows.items():
                found = signal(series, t, plan['lookback'])
                if found and found['floor'] < series[t]['close'] < found['ceiling']:
                    counts['sweeps'] += 1
                    if symbol not in watches:
                        watches[symbol] = found
        record(t, nav)
    endpoint = equity[-1]['nav'] if equity else None
    return {'status': 'COMPLETE_WITH_UNVALUED_HOURS' if endpoint is not None else 'INCOMPLETE_ENDPOINT',
            'ending_nav': endpoint, 'ending_cash': cash, 'position': position,
            'pending': pending, 'checkpoint': checkpoint,
            'closed_trade_count': len(trades), 'closed_winners': sum(t['net_pnl_usd'] > 0 for t in trades),
            'max_observed_close_drawdown': drawdown, 'counts': counts,
            'trades': trades, 'decisions': decisions, 'equity': equity}


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
    if account['ending_nav'] is not None and btc['status'] == 'COMPLETE' and account['checkpoint'] and account['checkpoint']['nav'] is not None:
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
                      'ending_nav': account['ending_nav'], 'ending_cash': account['ending_cash'],
                      'gaps': account['counts'], 'btc': btc,
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
