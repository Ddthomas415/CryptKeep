import pytest

from services.execution.strategy_runner import _position_aware_signal_action
from services.strategies.es_daily_trend import signal_from_ohlcv
from services.backtest.parity_engine import _backtest_action


def test_real_flat_adapter_matches_backtest_only_when_position_exists():
    rows = [[i*86400000,300-i,301-i,299-i,300-i,100] for i in range(220)]
    signal = signal_from_ohlcv(rows, emit_evidence=False)
    assert signal['action'] == 'hold' and signal['signal'] == 'flat'
    assert _position_aware_signal_action(signal,strategy_id='sma_200_trend',position_qty=1) == _backtest_action('sma_200_trend',signal,position_open=True) == 'sell'
    assert _position_aware_signal_action(signal,strategy_id='sma_200_trend',position_qty=0) == 'hold'


@pytest.mark.parametrize('patch', [
    {'ok':False}, {'signal':'long'}, {'signal':None},
    {'reason':'insufficient_history'}, {'action':'unexpected'},
])
def test_non_exit_conditions_remain_hold(patch):
    signal = {'ok':True,'signal':'flat','action':'hold',**patch}
    assert _position_aware_signal_action(signal,strategy_id='sma_200_trend',position_qty=1) == 'hold'


def test_other_strategy_unchanged():
    signal = {'ok':True,'signal':'flat','action':'hold'}
    assert _position_aware_signal_action(signal,strategy_id='ema_cross',position_qty=1) == 'hold'
