"""Bounded audit probe; synthetic rows only, no operator state access."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

with tempfile.TemporaryDirectory(prefix='es-cohort-proof-') as directory:
    os.environ['CBP_STATE_DIR'] = directory
    from services.control.paper_evidence_qualification import qualify_paper_history
    from services.control.paper_promotion_policy import resolve_paper_promotion_policy

    config = {
        'signal_source': 'public_ohlcv_1d',
        'strategy': {'venue': 'coinbase', 'symbol': 'BTC/USDT',
                     'signal': {'timeframe': '1d', 'sma_period': 200}},
        'promotion': {'paper': {'policy': {
            'id': 'slow_daily_single_symbol_v1',
            'cohort_start': '2026-10-08T12:00:00Z',
            'min_calendar_days': 45, 'min_qualified_bars': 60,
            'min_qualified_round_trips': 5}}},
    }
    # Synthetic boundary only: not a proposed activation timestamp.
    baseline = [
        {'timestamp':'2026-10-09T00:00:00Z','order_id':'buy','side':'buy','qty':1.0},
        {'timestamp':'2026-10-10T00:00:00Z','order_id':'sell','side':'sell','qty':1.0},
    ]
    for row in baseline:
        row.update(market_data_source='public_ohlcv',ohlcv_sample_mode=False,
                   ohlcv_timeframe='1d',ohlcv_venue='coinbase',ohlcv_symbol='BTC/USDT')
    path = Path(directory)/'journal.sqlite'
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE journal_fills (fill_id TEXT PRIMARY KEY,journal_ts TEXT,order_id TEXT,fill_ts TEXT,venue TEXT,symbol TEXT,side TEXT,qty REAL,price REAL,fee REAL,fee_currency TEXT)')
    for row, price in zip(baseline,(100.0,110.0)):
        conn.execute('INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                     (row['order_id'],row['timestamp'],row['order_id'],row['timestamp'],
                      'coinbase','BTC/USDT',row['side'],1.0,price,0.1,'USDT'))
    conn.commit()
    conn.close()
    cases = {}
    def observe(name, rows):
        out = qualify_paper_history(evidence_fills=rows,config=config,journal_path=str(path))
        q = out['qualification']
        cases[name] = {'completed_cycles':q['completed_evidence_round_trips'],
                       'rejected':q['unqualified_evidence_fills'],
                       'excluded_before':q['excluded_before_cohort_evidence_fills']}
        return cases[name]['completed_cycles']
    assert observe('matching_post_boundary',copy.deepcopy(baseline)) == 1
    old = copy.deepcopy(baseline)
    old[0]['timestamp']='2026-10-07T00:00:00Z'
    assert observe('cross_boundary_entry',old) == 0
    old[1]['timestamp']='2026-10-07T01:00:00Z'
    assert observe('both_before_boundary',old) == 0
    wrong = copy.deepcopy(baseline)
    for row in wrong:
        row['ohlcv_symbol']='BTC/USD'
    assert observe('wrong_symbol',wrong) == 0
    wrong = copy.deepcopy(baseline)
    for row in wrong:
        row['sma_period']=20
        row['exit_policy']='default_trailing_2pct'
    assert observe('explicit_wrong_strategy_policy',wrong) == 1
    assert observe('missing_strategy_identity',copy.deepcopy(baseline)) == 1
    policy = resolve_paper_promotion_policy(config)
    assert (policy.min_calendar_days,policy.min_qualified_bars,policy.min_qualified_round_trips)==(45,60,5)
    print(json.dumps({'scope':'current-source characterization, not gate acceptance',
                      'cases':cases,'thresholds_unchanged':True},indent=2))
