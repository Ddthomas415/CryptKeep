import pytest
from scripts.research.compare_daily_trend_cash import compare


def bars():
    return [[1609459200000+i*86400000,100.,100.,100.,100.,1.] for i in range(203)]


def test_flat_cash_and_round_trip_costs():
    r=compare(bars(), fee_bps=10, slippage_bps=0)["arms"]
    assert r["cash"]["terminal_liquidation_equity"] == 1000
    assert r["sma200_signal_only"]["trades"] == []
    assert r["buy_hold"]["net_after_terminal_liquidation"] == pytest.approx(-.2)


def test_signal_cannot_trade_same_close():
    rows=bars()
    rows[200][2]=rows[200][4]=200.
    t=compare(rows)["arms"]["sma200_signal_only"]["trades"]
    assert t[0]["ts"] == rows[201][0]
    assert t[0]["price"] == pytest.approx(100.05)
    assert t[1]["ts"] == rows[202][0]


def test_gap_and_invalid_costs_refused():
    with pytest.raises(ValueError, match="contiguous"):
        compare(bars()[:201]+bars()[202:])
    with pytest.raises(ValueError, match="cost"):
        compare(bars(),fee_bps=float("nan"))


def test_regime_blocks_entry_not_existing_position(monkeypatch):
    import scripts.research.compare_daily_trend_cash as module
    monkeypatch.setattr(module, 'compute_signal', lambda *a, **k: 'long')
    calls = []
    def gate(rows, **kwargs):
        assert kwargs['emit_evidence'] is False
        calls.append(len(rows))
        return {'action': 'buy' if len(calls) == 1 else 'hold'}
    monkeypatch.setattr(module, 'signal_from_ohlcv', gate)
    result = compare(bars(), regime_entry=True)['arms']['sma200_signal_only']
    assert [t['side'] for t in result['trades']] == ['buy']
    assert calls == [200]
    monkeypatch.setattr(module, 'signal_from_ohlcv', lambda *a, **k: {'action':'hold'})
    assert compare(bars(), regime_entry=True)['arms']['sma200_signal_only']['trades'] == []


def test_flat_signal_exits_even_when_regime_disallows_entry(monkeypatch):
    import scripts.research.compare_daily_trend_cash as module
    signals = iter(['long', 'flat', 'flat'])
    monkeypatch.setattr(module, 'compute_signal', lambda *a, **k: next(signals))
    monkeypatch.setattr(module, 'signal_from_ohlcv', lambda *a, **k: {'action':'buy'})
    result = compare(bars(), regime_entry=True)['arms']['sma200_signal_only']
    assert [t['side'] for t in result['trades']] == ['buy', 'sell']


def test_two_close_confirmation_and_unchanged_exit():
    rows=bars()
    rows.extend([[rows[-1][0]+86400000,100.,100.,100.,100.,1.]])
    for i in (200,201):
        rows[i][2]=rows[i][4]=200.
    t=compare(rows,two_close_entry=True)['arms']['sma200_signal_only']['trades']
    assert [x['side'] for x in t] == ['buy','sell']
    assert t[0]['ts']==rows[202][0]
    assert t[1]['ts']==rows[203][0]
    rows[202][2]=rows[202][4]=1000.
    later=compare(rows,two_close_entry=True)['arms']['sma200_signal_only']['trades']
    assert later[0]==t[0]


def test_one_close_spike_does_not_enter():
    rows=bars();rows[200][2]=rows[200][4]=200.
    assert compare(rows,two_close_entry=True)['arms']['sma200_signal_only']['trades']==[]


def test_currency_and_regime_metadata_do_not_change_arithmetic():
    usd=compare(bars(),regime_entry=True)
    usdt=compare(bars(),regime_entry=True,reporting_currency='USDT')
    assert usd['arms']==usdt['arms']
    assert usdt['reporting_currency']=='USDT'
    assert 'initial_cash_usd' not in usdt and 'entry_notional_usd' not in usdt
    assert usdt['initial_cash']==1000 and usdt['entry_notional']==100
    assert 'regime-gated' in usdt['limitations'][0]
    assert '100 USDT' in usdt['limitations'][3]
    with pytest.raises(ValueError,match='currency'):
        compare(bars(),reporting_currency='unknown')
