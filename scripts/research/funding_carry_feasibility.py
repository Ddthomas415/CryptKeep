"""Public settled-funding carry feasibility; not an execution or margin engine."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
from pathlib import Path
import time
import requests

HOUR = 3600000
BASE = 'https://www.okx.com/api/v5/'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)


def freeze(output):
    end = int(time.time()*1000)//(8*HOUR)*(8*HOUR)-8*HOUR
    save(output, {'registered_utc': datetime.now(timezone.utc).isoformat(),
                  'source_sha256': digest(__file__), 'instruments': ['BTC','ETH'],
                  'funding_start': end-30*24*HOUR, 'funding_end': end,
                  'entry_time': end-30*24*HOUR+HOUR, 'exit_time': end+HOUR,
                  'initial_quote_capital': 1000, 'quote_currency': 'USDT',
                  'overhead_per_30d': 20, 'overhead_currency_assumption': 'USD_USDT_PARITY_NOT_VERIFIED',
                  'scenarios': [{'name':'zero_cost_upper_reference','spot_fee':0,'perp_fee':0,'adverse':0},
                                {'name':'assumed_cost_case','spot_fee':.005,'perp_fee':.001,'adverse':.0005}],
                  'rule': 'Always long spot and equal base-quantity short linear perpetual; all settled funding signs included, fixed quantity, one entry/exit',
                  'limits': ['no_account_eligibility','no_historical_fee_verification',
                             'mark_candle_open_proxy_not_exact_assessment_price',
                             'no_liquidation_or_margin_tier_model','no_forecast_or_holdout_claim']})


def collect(plan_path, output):
    plan = json.loads(Path(plan_path).read_text())
    if digest(__file__) != plan['source_sha256']: raise ValueError('source_changed')
    result = {'plan_sha256':digest(plan_path),'requests':[],'assets':{}}
    with requests.Session() as session:
        session.trust_env = False
        def get(path, params):
            response = session.get(BASE+path, params=params, timeout=20, allow_redirects=False)
            response.raise_for_status(); data = response.json()
            if data.get('code') != '0': raise ValueError('public_api_error:'+str(data.get('msg')))
            result['requests'].append({'path':path,'params':params,
                'received_utc':datetime.now(timezone.utc).isoformat(),
                'response_base64':base64.b64encode(response.content).decode(),
                'response_sha256':hashlib.sha256(response.content).hexdigest()})
            time.sleep(.12)
            return data['data']
        def pages(path, params, timestamp):
            records = {}; cursor = None
            for _ in range(10):
                query = dict(params, limit=100)
                if cursor is not None: query['after'] = str(cursor)
                rows = get(path, query)
                if not rows: break
                for row in rows: records[timestamp(row)] = row
                oldest = min(timestamp(row) for row in rows)
                if oldest <= plan['entry_time']: break
                if cursor is not None and oldest >= cursor: raise ValueError('pagination_stalled')
                cursor = oldest
            return records
        for asset in plan['instruments']:
            spot = asset+'-USDT'; perp = spot+'-SWAP'
            funding = pages('public/funding-rate-history', {'instId':perp}, lambda r:int(r['fundingTime']))
            mark = pages('market/history-mark-price-candles', {'instId':perp,'bar':'4H'}, lambda r:int(r[0]))
            endpoints = {}
            for label, t in [('entry',plan['entry_time']),('exit',plan['exit_time'])]:
                endpoints[label] = {}
                for name, instrument in [('spot',spot),('perp',perp)]:
                    candles = get('market/history-candles', {'instId':instrument,'bar':'1H','after':str(t+1),'limit':2})
                    exact = [c for c in candles if int(c[0]) == t and c[-1] == '1']
                    if len(exact) != 1: raise ValueError('missing_endpoint:'+asset+label+name)
                    endpoints[label][name] = exact[0]
            definition = get('public/instruments', {'instType':'SWAP','instId':perp})
            spot_definition = get('public/instruments', {'instType':'SPOT','instId':spot})
            if len(definition)!=1 or len(spot_definition)!=1: raise ValueError('missing_instrument')
            result['assets'][asset] = {'funding':list(funding.values()),'marks':list(mark.values()),
                                       'endpoints':endpoints,'definition':definition[0],
                                       'spot_definition':spot_definition[0]}
    save(output, result)
    print('saved assets', list(result['assets']), 'public requests',len(result['requests']))


def money_case(asset, plan, scenario):
    definition = asset['definition']
    if definition['ctType']!='linear' or definition['settleCcy']!='USDT': raise ValueError('unsupported_contract')
    sf,pf,slip = scenario['spot_fee'],scenario['perp_fee'],scenario['adverse']
    endpoints = asset['endpoints']
    ps0,pp0 = float(endpoints['entry']['spot'][1]),float(endpoints['entry']['perp'][1])
    ps1,pp1 = float(endpoints['exit']['spot'][1]),float(endpoints['exit']['perp'][1])
    if not all(math.isfinite(p) and p>0 for p in (ps0,pp0,ps1,pp1)): raise ValueError('invalid_price')
    step = Decimal(definition['ctVal'])*Decimal(definition['ctMult'] or '1')*Decimal(definition['lotSz'])
    quantity_cap = plan['initial_quote_capital']/(ps0*(1+slip)*(1+sf)+pp0*(1-slip)*(1+pf))
    quantity = (Decimal(str(quantity_cap))/step).to_integral_value(rounding=ROUND_FLOOR)*step
    contracts = quantity/(Decimal(definition['ctVal'])*Decimal(definition['ctMult'] or '1'))
    if contracts<Decimal(definition['minSz']) or quantity<Decimal(asset['spot_definition']['minSz']):
        raise ValueError('capital_below_minimum')
    if quantity % Decimal(asset['spot_definition']['lotSz']): raise ValueError('incompatible_lot_sizes')
    q = float(quantity)
    funding = sorted([r for r in asset['funding'] if plan['entry_time']<int(r['fundingTime'])<plan['exit_time']],
                     key=lambda r:int(r['fundingTime']))
    times = [int(r['fundingTime']) for r in funding]
    if not times or times[0]-plan['entry_time']>8*HOUR or plan['exit_time']-times[-1]>8*HOUR:
        raise ValueError('funding_boundary_incomplete')
    if any(b-a>8*HOUR for a,b in zip(times,times[1:])): raise ValueError('funding_gap')
    marks = {int(r[0]):r for r in asset['marks'] if r[-1]=='1'}
    settled = []
    for record in funding:
        t = int(record['fundingTime'])
        if not record.get('realizedRate') or t not in marks: raise ValueError('missing_settled_rate_or_mark')
        rate = float(record['realizedRate']); mark = float(marks[t][1])
        if not math.isfinite(rate) or not math.isfinite(mark) or mark<=0: raise ValueError('invalid_funding')
        settled.append({'time':t,'actual_rate':rate,'mark_open_proxy':mark,'short_receipt':q*mark*rate})
    cash_used = q*ps0*(1+slip)*(1+sf)+q*pp0*(1-slip)*(1+pf)
    gross_basis = q*(ps1-ps0+pp0-pp1)
    receipts = sum(r['short_receipt'] for r in settled)
    adverse_cost = q*slip*(ps0+ps1+pp0+pp1)
    fees = q*(ps0*(1+slip)*sf+ps1*(1-slip)*sf+pp0*(1-slip)*pf+pp1*(1+slip)*pf)
    net = gross_basis+receipts-adverse_cost-fees
    return {'quantity_base':q,'contracts':str(contracts),'initial_cash_used':cash_used,
            'unallocated_cash':plan['initial_quote_capital']-cash_used,
            'initial_short_margin_model':q*pp0*(1-slip), 'settlements':len(settled),
            'negative_funding_periods':sum(r['actual_rate']<0 for r in settled),
            'funding_receipts_quote':receipts,'gross_basis_change_quote':gross_basis,
            'assumed_fee_quote':fees,'adverse_price_cost_quote':adverse_cost,
            'net_before_overhead_quote':net,'net_after_overhead_quote':net-plan['overhead_per_30d'],
            'ending_model_quote':plan['initial_quote_capital']+net-plan['overhead_per_30d'],
            'settled_records':settled,'margin_safety':'UNVERIFIED_NOT_A_LIQUIDATION_SIMULATION'}


def analyze(plan_path, raw_path, output):
    plan = json.loads(Path(plan_path).read_text()); raw = json.loads(Path(raw_path).read_text())
    if digest(__file__)!=plan['source_sha256'] or raw['plan_sha256']!=digest(plan_path): raise ValueError('binding_mismatch')
    for request in raw['requests']:
        if hashlib.sha256(base64.b64decode(request['response_base64'])).hexdigest()!=request['response_sha256']:
            raise ValueError('raw_payload_changed')
    result = {'plan_sha256':digest(plan_path),'raw_sha256':digest(raw_path),'limits':plan['limits'],'runs':[]}
    for symbol,asset in raw['assets'].items():
        for scenario in plan['scenarios']:
            row = {'asset':symbol,'scenario':scenario['name'], **money_case(asset,plan,scenario)}
            result['runs'].append(row)
            print(symbol,scenario['name'],'funding',row['funding_receipts_quote'],'basis',row['gross_basis_change_quote'],
                  'net_before',row['net_before_overhead_quote'],'net_after',row['net_after_overhead_quote'])
    save(output,result)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['freeze','collect','analyze'])
    parser.add_argument('paths',nargs='+');args=parser.parse_args()
    {'freeze':freeze,'collect':collect,'analyze':analyze}[args.mode](*args.paths)
