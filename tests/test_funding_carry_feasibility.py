from copy import deepcopy
import pytest
from scripts.research.funding_carry_feasibility import HOUR, money_case


def fixture():
    definition={'ctType':'linear','settleCcy':'USDT','ctVal':'1','ctMult':'1','lotSz':'.001','minSz':'.001'}
    asset={'definition':definition,'spot_definition':{'minSz':'.001','lotSz':'.001'},
           'endpoints':{'entry':{'spot':['0','100'],'perp':['0','100']},
                        'exit':{'spot':['0','90'],'perp':['0','90']}},
           'funding':[{'fundingTime':str(8*HOUR),'realizedRate':'.001','fundingRate':'.99'},
                      {'fundingTime':str(16*HOUR),'realizedRate':'-.0005','fundingRate':'.99'}],
           'marks':[[str(t*HOUR),'100','100','100','100','1'] for t in (8,16)]}
    plan={'entry_time':HOUR,'exit_time':17*HOUR,'initial_quote_capital':1000,'overhead_per_30d':20}
    return asset,plan


def test_actual_rates_include_negative_and_direction_hedges():
    asset,plan=fixture()
    result=money_case(asset,plan,{'spot_fee':0,'perp_fee':0,'adverse':0})
    assert result['funding_receipts_quote']==pytest.approx(.25)
    assert result['negative_funding_periods']==1
    assert result['gross_basis_change_quote']==0
    assert result['net_after_overhead_quote']==pytest.approx(-19.75)


def test_total_budget_and_rounding_include_collateral_and_fees():
    asset,plan=fixture()
    result=money_case(asset,plan,{'spot_fee':.005,'perp_fee':.001,'adverse':.0005})
    assert 0<result['initial_cash_used']<=1000
    assert result['unallocated_cash']>=0
    assert result['assumed_fee_quote']>0
    assert result['adverse_price_cost_quote']>0


def test_missing_mark_and_missing_actual_rate_refuse_calculation():
    asset,plan=fixture();bad=deepcopy(asset);bad['marks']=bad['marks'][:1]
    with pytest.raises(ValueError,match='missing_settled'):
        money_case(bad,plan,{'spot_fee':0,'perp_fee':0,'adverse':0})
    bad=deepcopy(asset);bad['funding'][0]['realizedRate']=''
    with pytest.raises(ValueError,match='missing_settled'):
        money_case(bad,plan,{'spot_fee':0,'perp_fee':0,'adverse':0})
