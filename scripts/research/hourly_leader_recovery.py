"""Bounded public hourly leader event study; no account or order access."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean
import time
import requests

HOUR = 3600


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2)


def freeze(universe, path):
    data = json.loads(Path(universe).read_text())
    cutoff = int(time.time())//HOUR*HOUR
    symbols = [p['product_id'] for p in data['products'] if p.get('product_type') == 'SPOT'
               and p.get('quote_currency_id') == 'USD' and p.get('status') == 'online'
               and not any(p.get(k) for k in ('is_disabled','trading_disabled','view_only','cancel_only'))]
    save(path, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                'source_sha256': digest(__file__), 'universe_sha256': digest(universe),
                'symbols': symbols, 'start': cutoff-312*HOUR, 'end': cutoff,
                'pullbacks': [.1,.2], 'targets': [.05,.1], 'holds_hours': [24,48],
                'wait_for_dip_hours':72, 'fee_per_side':.005, 'adverse_price_per_side':.0025,
                'budget_per_event':1000, 'leader_definition':'completed close / close 24 hours earlier, contiguous last 25 bars',
                'event_sampling':'every hourly leader observation, overlapping diagnostics not portfolio',
                'limits':['current_universe_survivorship','reconstructed_not_live_leaderboard',
                          'assumed_spread','recent12day_sample_not_holdout','eight_comparisons_not_independent']})


def collect(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256']:
        raise ValueError('source_changed')
    data = {'plan_sha256':digest(plan_path), 'markets':{}}
    with requests.Session() as session:
        session.trust_env = False
        for i,symbol in enumerate(plan['symbols'],1):
            for attempt in range(3):
                try:
                    response = session.get('https://api.coinbase.com/api/v3/brokerage/market/products/'+symbol+'/candles',
                        params={'start':plan['start'],'end':plan['end'],'granularity':'ONE_HOUR','limit':350},
                        timeout=15,allow_redirects=False)
                    if response.status_code == 429:
                        time.sleep(2*(attempt+1))
                        continue
                    response.raise_for_status()
                    data['markets'][symbol] = {'raw':response.json(),'response_sha256':hashlib.sha256(response.content).hexdigest()}
                    break
                except requests.RequestException as exc:
                    data['markets'][symbol] = {'error':type(exc).__name__}
                    break
            if symbol not in data['markets']:
                data['markets'][symbol] = {'error':'rate_limit_retry_exhausted'}
            time.sleep(.15)
            if i%50 == 0:
                print('collected',i,'/',len(plan['symbols']),flush=True)
    save(output,data)
    print('failed',sum('error'in x for x in data['markets'].values()),flush=True)


def event(series, leader, end, dip, target, hold, fee, spread):
    e={'leader_bar':leader,'status':'NO_DIP_WITHIN_72H'}
    peak=series[leader]['close']
    entry=None
    for step in range(1,73):
        t=leader+step*HOUR
        if t>=end:
            e['status']='WAITING_AT_END';return e
        if t not in series:
            e['status']='UNKNOWN_PRE_ENTRY_GAP';return e
        peak=max(peak,series[t]['close'])
        if series[t]['close']<=peak*(1-dip):
            entry=t+HOUR
            if entry>=end:
                e['status']='ENTRY_PENDING';return e
            if entry not in series:
                e['status']='UNKNOWN_ENTRY_GAP';return e
            break
    if entry is None:
        return e
    price=series[entry]['open']*(1+spread)
    quantity=1000/(price*(1+fee))
    e.update(entry_time=entry,entry_price=price,status='OPEN_AT_END')
    for step in range(hold):
        t=entry+step*HOUR
        if t>=end:return e
        if t not in series:
            e['status']='UNKNOWN_HELD_GAP';return e
        close=series[t]['close']
        e['last_mark_net_usd']=quantity*close*(1-spread)*(1-fee)-1000
        e['last_mark_time']=t+HOUR
        hit=close>=price*(1+target)
        if hit or step==hold-1:
            exit_t=t+HOUR
            if exit_t>=end:
                e['status']='EXIT_PENDING';return e
            if exit_t not in series:
                e['status']='UNKNOWN_EXIT_GAP';return e
            e.update(exit_time=exit_t,status='TARGET_EXIT' if hit else 'TIMEOUT_EXIT',
                     net_usd=quantity*series[exit_t]['open']*(1-spread)*(1-fee)-1000,
                     gross_return=series[exit_t]['open']/series[entry]['open']-1,
                     hours_held=step+1)
            return e
    return e


def stats(events):
    closed=[e for e in events if 'net_usd'in e]
    marks=[e['last_mark_net_usd'] for e in events if 'net_usd'not in e and 'last_mark_net_usd'in e]
    return {'leaders':len(events),'entered':sum('entry_time'in e for e in events),'closed':len(closed),
            'closed_net_winners':sum(e['net_usd']>0 for e in closed),
            'mean_closed_net_usd':mean(e['net_usd'] for e in closed) if closed else None,
            'mean_closed_gross_return':mean(e['gross_return'] for e in closed) if closed else None,
            'worst_closed_net_usd':min((e['net_usd'] for e in closed),default=None),
            'sum_closed_net_not_portfolio_usd':sum(e['net_usd'] for e in closed),
            'unresolved_last_marks_sum_usd':sum(marks),'unresolved_marks_count':len(marks),
            'statuses':dict(Counter(e['status'] for e in events))}


def analyze(plan_path, dataset, output):
    plan=json.loads(Path(plan_path).read_text());data=json.loads(Path(dataset).read_text())
    if digest(__file__)!=plan['source_sha256'] or data['plan_sha256']!=digest(plan_path):
        raise ValueError('frozen_provenance_mismatch')
    rows={}
    for symbol,market in data['markets'].items():
        if 'raw'not in market:continue
        bars={}
        for b in market['raw'].get('candles',[]):
            t=int(b['start'])
            if not plan['start']<=t<plan['end']:continue
            if t in bars:raise ValueError('duplicate_bar')
            bars[t]={k:float(b[k]) for k in ('open','close','volume')}
            if bars[t]['open']<=0 or bars[t]['close']<=0:raise ValueError('invalid_price')
        rows[symbol]=bars
    leaders=[];coverage=[]
    for t in range(plan['start']+24*HOUR,plan['end'],HOUR):
        candidates=[(s,r[t]['close']/r[t-24*HOUR]['close']-1) for s,r in rows.items()
                    if all(t-k*HOUR in r for k in range(25)) and r[t]['volume']>0]
        coverage.append({'time':t+HOUR,'rankable':len(candidates)})
        if candidates:
            symbol,gain=max(candidates,key=lambda x:x[1]);leaders.append((t,symbol,gain))
    result={'plan_sha256':digest(plan_path),'dataset_sha256':digest(dataset),'limits':plan['limits'],
            'failed_symbols':[s for s,v in data['markets'].items() if 'error'in v],
            'coverage_by_hour':coverage,'runs':[]}
    for dip in plan['pullbacks']:
        for target in plan['targets']:
            for hold in plan['holds_hours']:
                events=[]
                for t,symbol,gain in leaders:
                    e=event(rows[symbol],t,plan['end'],dip,target,hold,plan['fee_per_side'],plan['adverse_price_per_side'])
                    e.update(symbol=symbol,leader_return=gain)
                    if 'net_usd'in e:
                        btc=rows.get('BTC-USD',{});a,b=e['entry_time'],e['exit_time']
                        if a in btc and b in btc:
                            e['matched_btc_net_usd']=1000*(btc[b]['open']*(1-plan['adverse_price_per_side'])*(1-plan['fee_per_side'])/(btc[a]['open']*(1+plan['adverse_price_per_side'])*(1+plan['fee_per_side']))-1)
                    events.append(e)
                midpoint=plan['start']+(24+144)*HOUR
                result['runs'].append({'dip':dip,'target':target,'hold_hours':hold,**stats(events),
                    'first6day_leader_cohort':stats([e for e in events if e['leader_bar']<midpoint]),
                    'last6day_leader_cohort':stats([e for e in events if e['leader_bar']>=midpoint]),
                    'matched_btc_closed_sum_usd':sum(e.get('matched_btc_net_usd',0) for e in events),
                    'matched_btc_count':sum('matched_btc_net_usd'in e for e in events),'events':events})
    save(output,result)
    for r in result['runs']:
        print(r['dip'],r['target'],r['hold_hours'],r['entered'],r['closed'],r['closed_net_winners'],r['mean_closed_net_usd'],r['worst_closed_net_usd'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','collect','analyze']);p.add_argument('paths',nargs='+');a=p.parse_args()
    {'freeze':freeze,'collect':collect,'analyze':analyze}[a.mode](*a.paths)
