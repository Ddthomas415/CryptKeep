"""Probe (not part of the repository): does place_order's gate let an exit (sell) through when entry limits are hit?
Reuses the repository test helpers; only the side changes from buy to sell."""
import pytest
from services.execution import place_order as po
from tests.test_place_order_fail_closed import _set_limit_env, _install_boundary_success_deps, DummyExchange

CASES = [
    ("max_daily_loss", dict(CBP_MAX_DAILY_LOSS="250"), {"trades": 1, "pnl": -300, "notional": 0}),
    ("max_trades_per_day", dict(CBP_MAX_TRADES_PER_DAY="5"), {"trades": 5, "pnl": 0, "notional": 0}),
]

@pytest.mark.parametrize("name,env,snap", CASES)
@pytest.mark.parametrize("side", ["buy", "sell"])
def test_probe(monkeypatch, name, env, snap, side):
    _set_limit_env(monkeypatch, **env)
    _install_boundary_success_deps(monkeypatch, risk_snapshot=snap)
    try:
        po._enforce_fail_closed(DummyExchange(), symbol="BTC/USD", side=side, amount=0.1, price=100.0,
                                params={}, order_type="limit")
        print(f"\nCP09 {name} {side}: ALLOWED")
    except RuntimeError as e:
        print(f"\nCP09 {name} {side}: BLOCKED {str(e)[:70]}")
