from __future__ import annotations

import asyncio
import logging
import sys
from types import SimpleNamespace

import pytest

from services.execution import place_order as po
import services.markets as markets_pkg
import services.risk as risk_pkg


class DummyExchange:
    id = "coinbase"

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def create_order(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "oid-1"}


class FundingExchange(DummyExchange):
    def __init__(
        self,
        *,
        exchange_id: str = "coinbase",
        free: dict[str, float] | None = None,
        total: dict[str, float] | None = None,
        info_rows: list[dict[str, object]] | None = None,
        portfolio_uuid: str = "p-1",
    ) -> None:
        super().__init__()
        self.id = exchange_id
        self._portfolio_uuid = portfolio_uuid
        self._balance = {
            "free": dict(free or {}),
            "used": {k: 0.0 for k in dict(free or {})},
            "total": dict(total or free or {}),
            "info": {"data": list(info_rows or [])},
        }

    def fetch_balance(self):
        return self._balance

    def v3PrivateGetBrokerageKeyPermissions(self):
        return {"portfolio_uuid": self._portfolio_uuid}


class AsyncFundingExchange(FundingExchange):
    async def create_order(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"id": "oid-async-1"}


def _set_limit_env(monkeypatch, **overrides) -> None:
    defaults = {
        "CBP_MAX_TRADES_PER_DAY": "10",
        "CBP_MAX_DAILY_LOSS": "1000",
        "CBP_MAX_DAILY_NOTIONAL": "100000",
        "CBP_MAX_ORDER_NOTIONAL": "25000",
        "CBP_EXECUTION_ARMED": "1",
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, str(value))


def _install_boundary_success_deps(
    monkeypatch,
    *,
    risk_snapshot: dict[str, object] | None = None,
    prereq_ok: bool = True,
    validate_ok: bool = True,
) -> None:
    risk_snapshot = risk_snapshot or {"trades": 0, "pnl": 0, "notional": 0}

    monkeypatch.setattr(po, "_killswitch_state", lambda: (False, ""))
    monkeypatch.setattr(po, "_is_armed", lambda: (True, "env:CBP_EXECUTION_ARMED"))
    monkeypatch.setattr(po, "_enforce_ops_risk_gate", lambda **kwargs: None)
    monkeypatch.setattr(po, "_exec_db_path", lambda: "/tmp/execution.sqlite")

    fake_risk_daily = SimpleNamespace(
        snapshot=lambda exec_db: dict(risk_snapshot),
        record_order_attempt=lambda **kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "services.risk.risk_daily", fake_risk_daily)
    monkeypatch.setattr(risk_pkg, "risk_daily", fake_risk_daily, raising=False)

    fake_prereq = SimpleNamespace(
        check_market_rules_prereq=lambda **kwargs: SimpleNamespace(
            ok=prereq_ok,
            message="prereq_blocked" if not prereq_ok else "ok",
        )
    )
    monkeypatch.setitem(sys.modules, "services.markets.prereq", fake_prereq)
    monkeypatch.setattr(markets_pkg, "prereq", fake_prereq, raising=False)

    fake_rules = SimpleNamespace(
        validate=lambda *args, **kwargs: SimpleNamespace(
            ok=validate_ok,
            code="RULE_FAIL",
            message="rule_blocked" if not validate_ok else "ok",
        )
    )
    monkeypatch.setitem(sys.modules, "services.markets.rules", fake_rules)
    monkeypatch.setattr(markets_pkg, "rules", fake_rules, raising=False)


def test_killswitch_state_blocks_and_logs_on_import_failure(monkeypatch, caplog):
    monkeypatch.delenv("CBP_KILL_SWITCH", raising=False)
    monkeypatch.delenv("CBP_KILLSWITCH_FAIL_CLOSED", raising=False)
    monkeypatch.setattr(po, "_load_killswitch_module", lambda: (_ for _ in ()).throw(ModuleNotFoundError("missing module")))

    with caplog.at_level(logging.WARNING):
        blocked, reason = po._killswitch_state()

    assert blocked is True
    assert reason == "services.risk.killswitch.import_failed:ModuleNotFoundError"
    record = next(r for r in caplog.records if r.msg == "place_order_killswitch_probe_failed")
    assert record.source == "services.risk.killswitch"
    assert record.stage == "import"
    assert record.failure_type == "ModuleNotFoundError"
    assert record.fallback == "fail_closed_block"


def test_killswitch_state_blocks_and_logs_on_snapshot_failure(monkeypatch, caplog):
    fake_module = SimpleNamespace(
        is_on=lambda: False,
        snapshot=lambda: (_ for _ in ()).throw(RuntimeError("snapshot offline")),
    )
    monkeypatch.setattr(po, "_load_killswitch_module", lambda: fake_module)

    with caplog.at_level(logging.WARNING):
        blocked, reason = po._killswitch_state()

    assert blocked is True
    assert reason == "services.risk.killswitch.snapshot_failed:RuntimeError"
    record = next(r for r in caplog.records if r.stage == "snapshot")
    assert record.reason == "snapshot offline"


def test_killswitch_state_blocks_and_logs_on_invalid_cooldown(monkeypatch, caplog):
    fake_module = SimpleNamespace(
        is_on=lambda: False,
        snapshot=lambda: {"kill_switch": False, "cooldown_until": "later"},
    )
    monkeypatch.setattr(po, "_load_killswitch_module", lambda: fake_module)

    with caplog.at_level(logging.WARNING):
        blocked, reason = po._killswitch_state()

    assert blocked is True
    assert reason == "services.risk.killswitch.cooldown_read_failed:ValueError"
    record = next(r for r in caplog.records if r.stage == "cooldown_read")
    assert record.fallback == "fail_closed_block"


def test_require_env_float_rejects_non_finite(monkeypatch):
    monkeypatch.setenv("CBP_MAX_ORDER_NOTIONAL", "nan")
    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_limit_env:CBP_MAX_ORDER_NOTIONAL"):
        po._require_env_float("CBP_MAX_ORDER_NOTIONAL")


def test_enforce_fail_closed_blocks_when_kill_switch_on(monkeypatch):
    _set_limit_env(monkeypatch)
    monkeypatch.setattr(po, "_killswitch_state", lambda: (True, "env:CBP_KILL_SWITCH"))

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:kill_switch_on"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_when_not_armed(monkeypatch):
    _set_limit_env(monkeypatch)
    monkeypatch.setattr(po, "_killswitch_state", lambda: (False, ""))
    monkeypatch.setattr(po, "_is_armed", lambda: (False, "not_armed"))

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:fail_closed_not_armed"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_missing_limit_env(monkeypatch):
    _set_limit_env(monkeypatch, CBP_MAX_ORDER_NOTIONAL=None)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:missing_limit_env:CBP_MAX_ORDER_NOTIONAL"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_market_orders_by_default(monkeypatch):
    _set_limit_env(monkeypatch)
    monkeypatch.delenv("CBP_ALLOW_MARKET_ORDERS", raising=False)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:market_orders_disabled"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=None,
            params={},
            order_type="market",
        )


def test_enforce_fail_closed_blocks_invalid_amount(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_amount:ValueError"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount="bad-qty",
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_invalid_limit_price(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_price:ValueError"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price="bad-price",
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_non_positive_amount(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_amount:non_positive"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_non_positive_limit_price(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_price:non_positive"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_max_trades_per_day(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch, risk_snapshot={"trades": 10, "pnl": 0, "notional": 0})

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:max_trades_per_day"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_max_daily_loss(monkeypatch):
    _set_limit_env(monkeypatch, CBP_MAX_DAILY_LOSS="250")
    _install_boundary_success_deps(monkeypatch, risk_snapshot={"trades": 1, "pnl": -300, "notional": 0})

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:max_daily_loss"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_max_daily_notional(monkeypatch):
    _set_limit_env(monkeypatch, CBP_MAX_DAILY_NOTIONAL="1000")
    _install_boundary_success_deps(monkeypatch, risk_snapshot={"trades": 1, "pnl": 0, "notional": 990})

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:max_daily_notional"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=1,
            price=20.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_market_rules_prereq_failure(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch, prereq_ok=False)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:market_rules_prereq_failed"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_enforce_fail_closed_blocks_market_rules_validation_failure(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch, validate_ok=False)

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:market_rules_invalid"):
        po._enforce_fail_closed(
            DummyExchange(),
            symbol="BTC/USD",
            side="buy",
            amount=0.1,
            price=100.0,
            params={},
            order_type="limit",
        )


def test_place_order_blocks_before_exchange_create_order_on_invalid_amount(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)
    ex = DummyExchange()

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:invalid_amount:ValueError"):
        po.place_order(ex, "BTC/USD", "limit", "buy", "bad-qty", 100.0, {})

    assert ex.calls == []


def test_place_order_blocks_when_spendable_balance_is_insufficient(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)
    ex = FundingExchange(exchange_id="kraken", free={"USD": 10.0})

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:insufficient_spendable_balance"):
        po.place_order(ex, "BTC/USD", "limit", "buy", 1.0, 100.0, {})

    assert ex.calls == []


def test_place_order_coinbase_blocks_when_only_staked_balance_is_visible(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)
    monkeypatch.setattr(po, "enforce_coinbase_quote_account_available", lambda ex, symbol: None)
    ex = FundingExchange(
        exchange_id="coinbase",
        free={"ADA": 1041.490167},
        info_rows=[
            {
                "name": "Staked ADA",
                "primary": False,
                "portfolio_id": "p-1",
                "balance": {"amount": "1041.490167", "currency": "ADA"},
                "currency": {"code": "ADA", "rewards": {"apy": "0.01"}},
                "allow_withdrawals": True,
            }
        ],
    )

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:insufficient_spendable_balance asset=ADA"):
        po.place_order(ex, "ADA/ETH", "limit", "sell", 2.0, 0.000176, {})

    assert ex.calls == []


def test_place_order_allows_when_coinbase_spendable_wallet_balance_is_present(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)
    monkeypatch.setattr(po, "enforce_coinbase_quote_account_available", lambda ex, symbol: None)
    ex = FundingExchange(
        exchange_id="coinbase",
        free={"USD": 150.0},
        info_rows=[
            {
                "name": "USD Wallet",
                "primary": True,
                "portfolio_id": "p-1",
                "balance": {"amount": "150.0", "currency": "USD"},
                "currency": {"code": "USD"},
                "allow_withdrawals": True,
            }
        ],
    )

    out = po.place_order(ex, "BTC/USD", "limit", "buy", 1.0, 100.0, {})

    assert out["id"] == "oid-1"
    assert len(ex.calls) == 1


def test_place_order_async_blocks_when_spendable_balance_is_insufficient(monkeypatch):
    _set_limit_env(monkeypatch)
    _install_boundary_success_deps(monkeypatch)
    ex = AsyncFundingExchange(exchange_id="kraken", free={"USD": 10.0})

    with pytest.raises(RuntimeError, match="CBP_ORDER_BLOCKED:insufficient_spendable_balance"):
        asyncio.run(po.place_order_async(ex, "BTC/USD", "limit", "buy", 1.0, 100.0, {}))

    assert ex.calls == []
