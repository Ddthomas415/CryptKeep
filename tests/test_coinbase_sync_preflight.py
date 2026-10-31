"""Selected real preflight definitions, invented reads, no execution imports."""

import ast
from contextlib import nullcontext
from copy import deepcopy
from decimal import Decimal
import inspect
import itertools
import logging
import math
from pathlib import Path
import socket

import pytest

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "services/execution/place_order.py"
BEFORE = ROOT / "docs/review_artifacts/coinbase_sync_preflight_20261029/before/place_order.py"


class SubmissionReached(Exception):
    pass


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def balance(*, portfolio="p-one", held=5, quote=True):
    rows = [{"currency": {"code": "ETH"}, "portfolio_id": portfolio,
             "balance": {"amount": str(held)}}]
    if quote:
        rows.append({"currency": {"code": "USD"}, "portfolio_id": portfolio,
                     "balance": {"amount": "100"}})
    return {"free": {"ETH": held, "USD": 100}, "info": {"data": rows}}


class Client:
    id = "coinbase"
    def __init__(self, *, permissions=None, balances=None, asynchronous=None):
        self.permissions = iter(permissions) if permissions is not None else itertools.repeat({"portfolio_uuid": "p-one"})
        self.balances = iter(balances) if balances is not None else itertools.repeat(balance())
        self.calls, self.coroutines = [], []
        self.asynchronous = asynchronous
    def value(self, kind, value):
        self.calls.append(kind)
        if isinstance(value, BaseException):
            raise value
        if self.asynchronous == kind:
            async def result():
                return deepcopy(value)
            coroutine = result(); self.coroutines.append(coroutine)
            return coroutine
        return deepcopy(value)
    def v3PrivateGetBrokerageKeyPermissions(self):
        return self.value("permissions", next(self.permissions))
    def fetch_balance(self):
        return self.value("balance", next(self.balances))
    def create_order(self, *args):
        self.calls.append("submission")
        raise SubmissionReached()


def selected(path, names, namespace):
    tree = ast.parse(path.read_bytes())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    ast.fix_missing_locations(module); exec(compile(module, str(path), "exec"), namespace)


def namespace(path=CURRENT, *, side="sell", risk_block=False):
    ns = {"inspect": inspect, "math": math, "Decimal": Decimal, "_LOG": logging.getLogger("sync-preflight-test"),
          "decimal_value": lambda value, **kwargs: Decimal(str(value)),
          "_estimate_funding_required": lambda qty, price: Decimal(str(qty)) * Decimal(str(price)) * Decimal("1.005"),
          "_ORDER_SEMAPHORE": nullcontext()}
    selected(ROOT / "services/execution/coinbase_portfolio_guard.py",
             {"_get_portfolio_uuid", "_get_portfolio_currencies", "_split_symbol", "enforce_coinbase_quote_account_available"}, ns)
    selected(path, {"_float_or_none", "_split_symbol", "_coinbase_portfolio_uuid", "_coinbase_row_currency_code",
                   "_coinbase_row_amount", "_coinbase_row_trade_spendable", "_coinbase_spendable_from_info_rows",
                   "_extract_spendable_balance", "_parse_order_amount", "_parse_order_price", "_enforce_funding_gate",
                   "_enforce_balance_preflight_sync", "place_order"}, ns)
    ns["_extract_create_order_args"] = lambda *args: ("ETH/USD", side, 1, 10, {}, "limit")
    def guard(*args, **kwargs):
        if risk_block:
            raise RuntimeError("existing_risk_block")
        return "unused", Decimal(10), 1, 10
    ns["_enforce_fail_closed"] = guard
    return ns


@pytest.mark.parametrize("side", ["buy", "sell"])
def test_sync_order_uses_one_permission_and_one_balance(side):
    client = Client()
    with pytest.raises(SubmissionReached):
        namespace(side=side)["place_order"](client)
    assert client.calls == ["permissions", "balance", "submission"]


def test_before_reproduces_mixed_portfolio_and_balance_allowance():
    client = Client(permissions=[{"portfolio_uuid": "p-one"}, {"portfolio_uuid": "p-two"}],
                    balances=[balance(held=0), balance(portfolio="p-two", held=5, quote=False)])
    with pytest.raises(SubmissionReached):
        namespace(BEFORE)["place_order"](client)
    assert client.calls == ["permissions", "balance", "balance", "permissions", "submission"]


def test_current_does_not_use_second_portfolio_to_justify_first_observation():
    client = Client(permissions=[{"portfolio_uuid": "p-one"}, {"portfolio_uuid": "p-two"}],
                    balances=[balance(held=0), balance(portfolio="p-two", held=5, quote=False)])
    with pytest.raises(RuntimeError, match="insufficient_spendable_balance"):
        namespace()["place_order"](client)
    assert client.calls == ["permissions", "balance"]


@pytest.mark.parametrize("permissions", [None, {}, {"portfolio_uuid": ""}, {"portfolio_uuid": " "}, {"portfolio_uuid": 12}, []])
def test_invalid_permissions_refuse_before_balance(permissions):
    client = Client(permissions=[permissions])
    with pytest.raises(RuntimeError, match="portfolio_uuid_unavailable"):
        namespace()["place_order"](client)
    assert client.calls == ["permissions"]


@pytest.mark.parametrize("kind", ["permissions", "balance"])
def test_read_failure_has_no_sensitive_text_or_retry(kind):
    options = {kind if kind == "permissions" else "balances": [RuntimeError("synthetic secret text")]}
    client = Client(**options)
    with pytest.raises(RuntimeError) as error:
        namespace()["place_order"](client)
    assert "secret" not in str(error.value)
    assert "submission" not in client.calls and client.calls.count(kind) == 1


@pytest.mark.parametrize("invalid", [None, [], "not-a-balance"])
def test_malformed_balance_refuses(invalid):
    client = Client(balances=[invalid])
    with pytest.raises(RuntimeError, match="invalid_balance"):
        namespace()["place_order"](client)
    assert client.calls == ["permissions", "balance"]


@pytest.mark.parametrize("kind", ["permissions", "balance"])
def test_sync_entry_refuses_and_closes_owned_coroutine(kind):
    client = Client(asynchronous=kind)
    try:
        with pytest.raises(RuntimeError, match="async_result_requires_async_entry"):
            namespace()["place_order"](client)
        assert all(inspect.getcoroutinestate(value) == inspect.CORO_CLOSED for value in client.coroutines)
        assert "submission" not in client.calls
    finally:
        for value in client.coroutines:
            value.close()


@pytest.mark.parametrize("rows,match", [(balance(quote=False), "portfolio_account_unavailable"),
    (balance(portfolio="p-other"), "portfolio_account_unavailable"), (balance(held=0), "insufficient_spendable_balance")])
def test_existing_portfolio_and_funding_refusals_remain(rows, match):
    client = Client(balances=[rows])
    with pytest.raises(RuntimeError, match=match):
        namespace()["place_order"](client)
    assert "submission" not in client.calls


def test_risk_block_still_precedes_all_private_reads():
    client = Client()
    with pytest.raises(RuntimeError, match="existing_risk_block"):
        namespace(risk_block=True)["place_order"](client)
    assert client.calls == []


@pytest.mark.parametrize("side", ["buy", "sell"])
def test_other_venues_keep_original_one_balance_path(side):
    client = Client(); client.id = "kraken"
    with pytest.raises(SubmissionReached):
        namespace(side=side)["place_order"](client)
    assert client.calls == ["balance", "submission"]
