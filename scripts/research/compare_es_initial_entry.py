import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from services.backtest import parity_engine as engine
from scripts.research.run_es_daily_trend_backtest_baseline import parse_utc_ms

start, end = map(parse_utc_ms, ['2018-01-01', '2026-06-04'])
with sqlite3.connect((root/'.cbp_state/data/market_raw.sqlite').as_uri()+'?mode=ro', uri=True) as db:
    rows = [list(r) for r in db.execute('SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=? AND ts_ms<=? ORDER BY ts_ms', ('coinbase','BTC/USD','1d',start,end))]
digest = hashlib.sha256(json.dumps(rows,separators=(',', ':')).encode()).hexdigest()
assert digest == 'c0d64661f4c09b4ca7be047694dceff46b22846ba576177f55e4464a623e28eb'
assert len(rows)==3077 and rows[0][0]==start and rows[-1][0]==end
assert all(b[0]-a[0]==86400000 for a,b in zip(rows,rows[1:]))

class EntryFilter:
    def __init__(self):
        self.previous = None
        self.suppressed = 0
        self.first_action = None
    def apply(self, signal):
        action = str(signal.get('action') or 'hold').lower().strip()
        if self.first_action is None:
            self.first_action = action
        changed = self.previous is not None and action != self.previous
        self.previous = action
        out = dict(signal)
        if action == 'buy' and not changed:
            out['action'] = 'hold'
            self.suppressed += 1
        return out

f = EntryFilter()
assert [f.apply({'action':a})['action'] for a in ['buy','buy','hold','buy']] == ['hold','hold','hold','buy']
f = EntryFilter()
assert [f.apply({'action':a})['action'] for a in ['hold','buy']] == ['hold','buy']
original = engine.compute_signal
reports = []
for policy in ['initial_eligible_entry','transition_only_entry']:
    f = EntryFilter()
    def compute(**kwargs):
        signal = original(**kwargs)
        if policy == 'transition_only_entry':
            return f.apply(signal)
        if f.first_action is None:
            f.first_action = signal.get('action')
        return signal
    with patch.object(engine,'compute_signal',side_effect=compute):
        result = engine.run_parity_backtest(cfg={'strategy':{'name':'sma_200_trend','sma_period':200,'atr_period':20}},symbol='BTC/USDT',candles=rows,warmup_bars=210,initial_cash=1000,fee_bps=7.5,slippage_bps=5)
    reports.append(dict(policy=policy,first_action=f.first_action,suppressed_buy_observations=f.suppressed,metrics=result['metrics'],trades=result['trades']))
print(json.dumps(dict(input_sha256=digest,rows=len(rows),research_only=True,limitations=['entry-only comparison, not runner parity','all-cash sizing and daily bars','BTC/USD proxy for BTC/USDT','in-sample; not promotion evidence'],reports=reports),indent=2))
