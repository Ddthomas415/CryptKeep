"""Independent boundary probes using the submitted real-store test rig."""
import pytest

from test_executor_reconcile_partial_and_unaccounted_fills import rig, _fills, _status
from services.execution import live_executor as le


def test_incomplete_nonempty_trade_history_cannot_close_underaccounted_order(rig):
    venue = rig['venue']
    venue.order.update(status='open', filled=0.4, average=100.0)
    venue.trade('t-1', 0.4)
    le.reconcile_live(rig['cfg'])
    venue.order.update(status='closed', filled=1.0, average=100.0)
    le.reconcile_live(rig['cfg'])
    quantity = sum(fill[1] for fill in _fills(rig['db']))
    assert _status(rig['db']) != 'filled' or quantity == pytest.approx(1.0)


def test_canceled_partial_fill_sink_failure_remains_retryable(rig):
    venue = rig['venue']
    venue.order.update(status='canceled', filled=0.4, average=100.0)
    venue.trade('t-1', 0.4)
    rig['sink_ok']['ok'] = False
    le.reconcile_live(rig['cfg'])
    assert _status(rig['db']) in {'submitted', 'partially_filled'}
    rig['sink_ok']['ok'] = True
    le.reconcile_live(rig['cfg'])
    assert sum(fill[1] for fill in _fills(rig['db'])) == pytest.approx(0.4)


def test_partial_fill_fallback_preserves_total_execution_value(rig):
    venue = rig['venue']
    venue.order.update(status='open', filled=0.4, average=100.0)
    venue.trade('t-1', 0.4, price=100.0)
    le.reconcile_live(rig['cfg'])
    venue.order.update(status='closed', filled=1.0, average=160.0)
    venue.fail_trades = True
    le.reconcile_live(rig['cfg'])
    assert sum(fill['qty'] * fill['price'] for fill in rig['sink']) == pytest.approx(160.0)
