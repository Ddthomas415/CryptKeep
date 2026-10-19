from scripts.research.hourly_leader_recovery import HOUR,event,stats


def rows(prices):
    return {i*HOUR:{'open':p,'close':p,'volume':1} for i,p in enumerate(prices)}


def test_entry_relative_target_next_open_and_later_gap_independence():
    r=rows([100,80,70,71,74,75,75])
    e=event(r,0,7*HOUR,.1,.05,24,.005,.0025)
    assert e['exit_time']==5*HOUR
    assert e['net_usd']>0
    del r[6*HOUR]
    assert event(r,0,7*HOUR,.1,.05,24,.005,.0025)==e


def test_unfinished_gap_and_timeout_not_excluded():
    r=rows([100,80,70,60,50,40])
    assert event(r,0,3*HOUR,.1,.05,24,.005,.0025)['status']=='OPEN_AT_END'
    assert event(r,0,6*HOUR,.1,.05,2,.005,.0025)['status']=='TIMEOUT_EXIT'
    del r[3*HOUR]
    assert event(r,0,6*HOUR,.1,.05,24,.005,.0025)['status']=='UNKNOWN_HELD_GAP'


def test_cost_and_closed_only_labels():
    e=event(rows([100,80,70,70,70]),0,5*HOUR,.1,.05,1,.005,.0025)
    assert -16<e['net_usd']<-14
    s=stats([e,{'status':'OPEN_AT_END','entry_time':100,'last_mark_net_usd':-50}])
    assert s['closed']==1 and s['entered']==2
    assert s['unresolved_last_marks_sum_usd']==-50


def test_target_hit_does_not_guarantee_profitable_next_open():
    e=event(rows([100,80,70,80,60,60]),0,6*HOUR,.1,.05,24,.005,.0025)
    assert e['status']=='TARGET_EXIT'
    assert e['net_usd']<0


def test_last_leader_and_entry_pending_remain_counted():
    r=rows([100,80])
    assert event(r,HOUR,2*HOUR,.1,.05,24,.005,.0025)['status']=='WAITING_AT_END'
    assert event(r,0,2*HOUR,.1,.05,24,.005,.0025)['status']=='ENTRY_PENDING'
