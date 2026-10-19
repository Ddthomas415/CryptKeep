from scripts.research.leader_single_account import HOUR, simulate


def plan(end):
    return dict(start=24*HOUR,end=end*HOUR,initial_cash=1000,dip=.2,target=.05,
                hold_hours=48,wait_hours=72,fee=.005,spread=.0025)


def series():
    values=[100]*25+[80,70,74,75,75]
    return {'X':{i*HOUR:dict(open=p,close=p,volume=1) for i,p in enumerate(values)}}


def test_one_account_budget_next_open_and_target():
    result=simulate(series(),plan(30))
    assert result['closed_trade_count']==1
    trade=result['trades'][0]
    assert trade['entry_time']==26*HOUR
    assert trade['exit_time']==28*HOUR
    assert trade['cash_at_entry']==1000
    assert abs(trade['quantity']*trade['entry_price']*1.005-1000)<1e-8
    assert result['ending_nav']==trade['cash_after_exit']


def test_gap_cannot_be_skipped_or_invent_an_exit():
    rows=series();del rows['X'][27*HOUR]
    result=simulate(rows,plan(30))
    assert result['status']=='INCOMPLETE_HELD_PRICE_GAP'
    assert result['ending_nav'] is None
    assert result['closed_trade_count']==0
    assert result['position'] is not None


def test_ending_open_position_not_realized_cash():
    result=simulate(series(),plan(27))
    assert result['status']=='COMPLETE'
    assert result['ending_cash']==0
    assert result['position'] is not None
    assert result['ending_nav']>0
    assert result['closed_trade_count']==0


def test_cash_carries_forward_without_a_new_deposit():
    values=[100]*25+[80,70,74,75,75,100,80,70,75,80,80]
    rows={'X':{i*HOUR:dict(open=p,close=p,volume=1) for i,p in enumerate(values)}}
    result=simulate(rows,plan(len(values)))
    assert result['closed_trade_count']==2
    first,second=result['trades']
    assert second['cash_at_entry']==first['cash_after_exit']
    assert second['entry_time']>first['exit_time']
    assert abs(result['ending_cash']-1000-sum(t['net_pnl_usd'] for t in result['trades']))<1e-8


def test_missing_entry_does_not_spend_cash():
    rows=series();del rows['X'][26*HOUR]
    result=simulate(rows,plan(30))
    assert result['closed_trade_count']==0
    assert result['ending_cash']==1000
    assert any(d['kind']=='ENTRY_SKIPPED_MISSING_OPEN' for d in result['decisions'])
