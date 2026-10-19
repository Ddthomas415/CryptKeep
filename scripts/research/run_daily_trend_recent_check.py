"""Fixed recent-year research check; no campaign or order access."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.research.compare_daily_trend_cash import compare


def window(end_year):
    if end_year not in (2024, 2025, 2026):
        raise ValueError('unsupported fixed research year')
    end = int(datetime(end_year, 9, 26, tzinfo=timezone.utc).timestamp())
    evaluated_start = int(datetime(end_year-1, 9, 26, tzinfo=timezone.utc).timestamp())
    days = (end-evaluated_start)//86400
    return evaluated_start-200*86400, end, days


def run(*, candidate=False, end_year=2026):
    start, end, days = window(end_year)
    if end_year != 2026 and not candidate:
        raise ValueError('earlier windows are candidate-only')
    product = 'BTC-USDT' if candidate else 'BTC-USD'
    out = ROOT / ('.cbp_state/data/research/daily_trend_below_sma_candidate_20260926' if candidate else '.cbp_state/data/research/daily_trend_recent_20260926')
    if end_year != 2026:
        out = out.with_name(f'daily_trend_below_sma_candidate_{end_year}0926')
    out.mkdir(parents=True, exist_ok=False)
    plan = dict(start_sec=start, end_exclusive_sec=end, warmup=200,
                evaluated_days=days, fee_bps_per_side=50, slippage_bps_per_side=5,
                capital=1000, entry_notional=100, symbol=product.replace('-', '/'),
                rule=('registry regime-gated entry, proposed below-SMA exit, next open' if candidate else 'unchanged SMA200 prior completed closes, next open'),
                fee_basis='current authenticated rate, not historical rate',
                qualification='exploratory, overlaps previously inspected history')
    for name in ('compare_daily_trend_cash.py',):
        plan[name + '_sha256'] = hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
    plan['signal_sha256'] = hashlib.sha256((ROOT/'services/strategies/es_daily_trend.py').read_bytes()).hexdigest()
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    candles = {}
    with (out/'responses.jsonl').open('x') as archive:
        for a in range(start, end, 299*86400):
            params = dict(granularity=86400,
                          start=datetime.fromtimestamp(a, timezone.utc).isoformat(),
                          end=datetime.fromtimestamp(min(end,a+299*86400), timezone.utc).isoformat())
            response = requests.get(f'https://api.exchange.coinbase.com/products/{product}/candles', params=params, timeout=30)
            response.raise_for_status()
            raw = response.json()
            archive.write(json.dumps(dict(params=params, response=raw))+'\n')
            archive.flush()
            for row in raw:
                if len(row) != 6 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in row):
                    raise ValueError('invalid candle')
                t,lo,hi,op,cl,vol = row
                if t % 86400 or vol < 0 or not 0 < lo <= min(op,cl) <= max(op,cl) <= hi:
                    raise ValueError('invalid candle values')
                if start <= t < end:
                    normalized = [int(t)*1000,op,hi,lo,cl,vol]
                    if t in candles and candles[t] != normalized:
                        raise ValueError('conflicting overlap')
                    candles[t] = normalized
    rows = [candles[t] for t in sorted(candles)]
    if len(rows) != days+200 or rows[0][0] != start*1000 or rows[-1][0] != (end-86400)*1000:
        raise ValueError('incomplete planned window')
    (out/'candles.json').write_text(json.dumps(rows)+'\n')
    result = compare(rows, fee_bps=50, slippage_bps=5, regime_entry=candidate,
                     reporting_currency='USDT' if candidate else 'USD')
    result['reporting_currency'] = 'USDT' if candidate else 'USD'
    result['scope'] = plan['rule'] + '; not campaign replay'
    if candidate:
        result['limitations'][0] = 'Proposed regime-entry/below-SMA-exit candidate; not campaign replay, no complete risk stack. USDT reporting; no USD conversion assumed.'
    result['fee_basis'] = plan['fee_basis']
    result['limitations'][1] = 'Current verified fee applied retrospectively; slippage assumed; no interest, funding, tax or infrastructure costs.'
    (out/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a not in ('trades','equity')} for k,v in result['arms'].items()},indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--below-sma-candidate', action='store_true')
    parser.add_argument('--earlier-candidate-windows', action='store_true')
    args = parser.parse_args()
    if args.earlier_candidate_windows:
        for year in (2024, 2025):
            run(candidate=True, end_year=year)
    else:
        run(candidate=args.below_sma_candidate)
