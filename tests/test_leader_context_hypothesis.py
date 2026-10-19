import json
from pathlib import Path
from scripts.research.leader_context_hypothesis import HOUR, context_gate, rows_from, simulate
from scripts.research.leader_single_account import simulate as original_simulate


def history(btc_up=True, volume_up=True):
    btc = {i*HOUR: {'open': 100, 'close': 100+i if btc_up else 100-i, 'volume': 1}
           for i in range(25)}
    coin = {i*HOUR: {'open': 100, 'close': 100, 'volume': 2 if volume_up and i>=19 else 1}
            for i in range(25)}
    return {'BTC-USD': btc, 'X': coin}


def test_gate_requires_both_conditions():
    assert context_gate(history(), 'X', 24*HOUR)['pass']
    assert not context_gate(history(btc_up=False), 'X', 24*HOUR)['pass']
    assert not context_gate(history(volume_up=False), 'X', 24*HOUR)['pass']


def test_gate_unknown_and_future_independence():
    rows=history()
    before=context_gate(rows,'X',24*HOUR)
    rows['X'][25*HOUR]={'open':1,'close':1,'volume':100000}
    assert context_gate(rows,'X',24*HOUR)==before
    del rows['BTC-USD'][HOUR]
    assert context_gate(rows,'X',24*HOUR)['reason']=='UNKNOWN_BTC_HISTORY'


def test_unfiltered_real_replay_matches_original():
    root=Path(__file__).resolve().parents[1]
    plan=json.loads((root/'research/leader_single_account_plan_20261012.json').read_text())
    rows=rows_from(plan)
    assert simulate(rows,dict(plan,entry_filter=False))==original_simulate(rows,plan)


def test_failed_entry_preserves_unrelated_watch():
    prices_x=[100]*24+[120,110,100,95,95,95]
    prices_y=[100]*24+[110,130,130,120,100,100]
    rows={s:{i*HOUR:dict(open=p,close=p,volume=1) for i,p in enumerate(values)}
          for s,values in [('X',prices_x),('Y',prices_y)]}
    del rows['X'][28*HOUR]
    plan=dict(start=24*HOUR,end=30*HOUR,initial_cash=1000,dip=.2,target=.05,
              hold_hours=48,wait_hours=72,fee=.005,spread=.0025,entry_filter=False)
    result=simulate(rows,plan)
    assert result['position']['symbol']=='Y'
    assert result['position']['entry_time']==29*HOUR
