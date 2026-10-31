"""Historical negative controls; pre-repair market-rule sources are preserved."""

import ast
from copy import deepcopy
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
import logging

import pytest

from services.markets.models import MarketRules, ValidationResult
from services.markets.math_utils import decimal_value, decimal_step_ok


ROOT = Path(__file__).resolve().parents[1]


def load(path, names, ns):
    actual = ROOT / path
    if path in ("services/markets/fetch_coinbase_ccxt.py", "services/markets/rules.py"):
        actual = ROOT / "docs/review_artifacts/coinbase_mode_gate_20261028" / Path(path).name
    tree = ast.parse(actual.read_bytes())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    if "validate" in names:
        nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "DEFAULT_TTL_S" for t in n.targets)] + nodes
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(actual), "exec"), ns)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.mark.parametrize("flag", [None, "cancel_only", "limit_only", "post_only", "auction_mode", "offline"])
def test_cached_active_rule_loses_product_mode_information(monkeypatch, flag):
    raw = {"status": "offline" if flag == "offline" else "online", "trading_disabled": False,
           "cancel_only": False, "limit_only": False, "post_only": False, "auction_mode": False}
    if flag not in (None, "offline"):
        raw[flag] = True
    market = {"id": "ETH-USD", "active": True, "info": raw}
    fake_sdk = SimpleNamespace(coinbase=lambda options: SimpleNamespace(load_markets=lambda: {"ETH/USD": market}))
    monkeypatch.setitem(sys.modules, "ccxt", fake_sdk)
    ns = {"MarketRules": MarketRules, "ValidationResult": ValidationResult,
          "canonicalize": lambda value: value, "coinbase_native": lambda value: value.replace("/", "-"),
          "decimal_value": decimal_value, "decimal_step_ok": decimal_step_ok}
    load("services/markets/fetch_coinbase_ccxt.py", {"fetch_rules"}, ns)
    rules = ns["fetch_rules"]("ETH/USD")
    assert rules.active and rules.meta == {"ccxt_symbol": "ETH/USD"}
    assert "info" not in rules.meta and not any(key in rules.meta for key in raw)
    ns["get_rules"] = lambda *args, **kwargs: rules
    load("services/markets/rules.py", {"validate", "_invalid_result"}, ns)
    assert ns["validate"]("unused", "coinbase", "ETH/USD", qty=1, notional=10).ok


def test_inactive_market_is_still_refused():
    rules = MarketRules("coinbase", "ETH/USD", "ETH-USD", False)
    ns = {"get_rules": lambda *args, **kwargs: rules, "canonicalize": lambda value: value,
          "ValidationResult": ValidationResult}
    load("services/markets/rules.py", {"validate", "_invalid_result"}, ns)
    result = ns["validate"]("unused", "coinbase", "ETH/USD")
    assert not result.ok and result.code == "MARKET_INACTIVE"


def test_rejected_exit_is_reselected_each_tick_without_outer_backoff():
    row = {"intent_id": "invented-exit", "ts_ms": 1, "symbol": "ETH/USD", "side": "sell",
           "order_type": "market", "qty": 1, "limit_price": None, "status": "pending", "reason": "", "meta": {}}
    attempts, writes = [], []
    class Store:
        def list_intents(self, **kwargs):
            return [deepcopy(row)] if row["status"] == kwargs["status"] else []
        def get_symbol_lock(self, symbol):
            return None
        def set_intent_status(self, *, intent_id, status, reason):
            assert intent_id == row["intent_id"]
            row.update(status=status, reason=reason)
            writes.append((status, reason))
            return True
    store = Store()
    class Client:
        def submit_order(self, **kwargs):
            attempts.append(kwargs)
            raise RuntimeError("invented cancel-only rejection")
    class Gates:
        def check_live(self, **kwargs):
            return True, "fixture", {}
    ns = {
        "_hard_off_guard": lambda *a, **k: (True, "fixture"),
        "_system_guard_submit_open": lambda: (True, "fixture", {}),
        "_load_execution_safety_cfg": lambda: SimpleNamespace(enabled=False),
        "_execution_safety_pause_open": lambda: (True, "fixture", {}),
        "_check_market_freshness_for_live": lambda *a: (True, "fixture", {}),
        "_latency_tracker": lambda *a: SimpleNamespace(record_submit=lambda **k: None),
        "load_runtime_trading_config": lambda **k: {},
        "LiveRiskLimits": SimpleNamespace(from_dict=lambda config: object()),
        "LiveGateDB": lambda **k: SimpleNamespace(killswitch_on=lambda: False),
        "LiveRiskGates": lambda **k: Gates(),
        "ExecutionStore": lambda **k: store,
        "OrderDedupeStore": lambda **k: object(),
        "ExchangeClient": lambda **k: Client(),
        "check_market_quality": lambda *a: (True, "fixture"),
        "_remote_id_from_reason": lambda value: None,
        "make_client_order_id": lambda *a: "same-fixture-id",
        "RiskDailyDB": lambda *a: SimpleNamespace(realized_today_usd=lambda: 0),
        "_local_gate_price": lambda *a, **k: 10,
        "_check_preflight_gate": lambda *a: (True, "fixture", {}),
        "_now_ms": lambda: 1000,
        "_LOG": logging.getLogger("offline-exit-gap"),
    }
    load("services/execution/_executor_shared.py", {"_list_intents_any"}, ns)
    load("services/execution/_executor_submit.py", {"submit_pending_live"}, ns)
    cfg = SimpleNamespace(exec_db="unused", exchange_id="coinbase", symbol="ETH/USD",
                          sandbox=True, max_submit_per_tick=1)
    for _ in range(3):
        result = ns["submit_pending_live"](cfg)
        assert result["submitted"] == 0 and result["errors"] == 1
    assert len(attempts) == len(writes) == 3
    assert row["status"] == "pending" and row["reason"].startswith("submit_error:")
    assert {a["client_id"] for a in attempts} == {"same-fixture-id"}
    # This stops at a fake client boundary, not exchange HTTP or real dedupe.
