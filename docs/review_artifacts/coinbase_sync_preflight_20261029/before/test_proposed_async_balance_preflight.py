"""Applied-source offline regressions; selected AST, no production imports."""

import ast
import asyncio
from decimal import Decimal
import inspect
import logging
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "docs/review_artifacts/coinbase_paged_preflight_20261028_01/place_order_proposed.py"
ORIGINAL = ROOT / "docs/review_artifacts/balance_preflight_integration_20261028/place_order_original.py"
APPLICATION = ROOT / "services/execution/place_order.py"


def load(path, names, namespace):
    nodes = [n for n in ast.parse(path.read_text()).body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert len(nodes) == len(names)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)


class SubmissionReached(Exception):
    pass


class Fake:
    def __init__(self, venue, asynchronous, failure=None):
        self.id, self.asynchronous, self.failure = venue, asynchronous, failure
        self.calls, self.coroutines = [], []

    def value(self, kind, value):
        if not self.asynchronous:
            if self.failure == kind: raise RuntimeError("secret fixture detail")
            self.calls.append(kind)
            return value
        async def read():
            self.calls.append(kind)
            if self.failure == kind: raise RuntimeError("secret fixture detail")
            if self.failure == "cancel": raise asyncio.CancelledError()
            return value
        coroutine = read(); self.coroutines.append(coroutine)
        return coroutine

    def v3PrivateGetBrokerageKeyPermissions(self):
        return self.value("permissions", {} if self.failure == "missing_portfolio" else {"portfolio_uuid": "p-1"})

    def fetch_balance(self):
        if self.failure == "malformed": return self.value("balance", None)
        free = 0 if self.failure == "insufficient" else 5
        quote_free = 0 if self.failure == "insufficient" else 100
        return self.value("balance", {"free": {"ETH": free, "USD": quote_free}, "info": {"data": [
            {"currency": {"code": "USD"}, "portfolio_id": "p-1", "balance": {"amount": str(quote_free)}},
            {"currency": {"code": "ETH"}, "portfolio_id": "p-1", "balance": {"amount": str(free)}}]}})

    async def create_order(self, *args):
        self.calls.append("create_order")
        raise SubmissionReached()


def namespace(path, trace, fail_guard=False, side="sell"):
    ns = {"math": math, "inspect": inspect, "Decimal": Decimal,
          "_LOG": logging.getLogger("offline-balance-proposal"),
          "decimal_value": lambda x, **kwargs: Decimal(str(x)),
          "_estimate_funding_required": lambda amount, price: Decimal(str(amount)) * Decimal(str(price)) * Decimal("1.005")}
    load(ROOT / "services/execution/coinbase_portfolio_guard.py",
         {"_get_portfolio_uuid", "_get_portfolio_currencies", "_split_symbol",
          "enforce_coinbase_quote_account_available"}, ns)
    names = {"_float_or_none", "_split_symbol", "_coinbase_portfolio_uuid",
             "_coinbase_row_currency_code", "_coinbase_row_amount", "_coinbase_row_trade_spendable",
             "_coinbase_spendable_from_info_rows", "_extract_spendable_balance", "_enforce_funding_gate",
             "_parse_order_amount", "_parse_order_price", "place_order_async"}
    if path != ORIGINAL: names.add("_enforce_balance_preflight_async")
    load(path, names, ns)
    ns["_extract_create_order_args"] = lambda *args: ("ETH/USD", side, 1, 10, {}, "limit")
    def guard(*args, **kwargs):
        trace.append("risk_guard")
        if fail_guard: raise RuntimeError("invented existing risk block")
        return "fixture-unused", Decimal(10), 1, 10
    ns["_enforce_fail_closed"] = guard
    ns["_ASYNC_ORDER_SEMAPHORE"] = asyncio.Semaphore(1)
    return ns


def invoke(path, venue="coinbase", asynchronous=True, failure=None, fail_guard=False):
    trace = []; ns = namespace(path, trace, fail_guard)
    ex = Fake(venue, asynchronous, failure)
    try:
        asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines: coroutine.close()
    return ex, trace


@pytest.mark.parametrize("venue", ["coinbase", "invented-other"])
def test_original_entry_does_not_support_genuine_async_reads(venue):
    with pytest.raises(AttributeError): invoke(ORIGINAL, venue)


@pytest.mark.parametrize("venue", ["coinbase", "invented-other"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_application_awaits_or_reuses_one_snapshot_before_submission(venue, asynchronous):
    trace = []; ns = namespace(APPLICATION, trace); ex = Fake(venue, asynchronous)
    try:
        with pytest.raises(SubmissionReached): asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines: coroutine.close()
    assert trace == ["risk_guard"]
    assert ex.calls == (["permissions", "balance", "create_order"] if venue == "coinbase"
                        else ["balance", "create_order"])


@pytest.mark.parametrize("failure,match", [("permissions", "portfolio_uuid_unavailable"),
    ("missing_portfolio", "portfolio_uuid_unavailable"), ("balance", "funding_probe_failed"),
    ("malformed", "invalid_balance"), ("insufficient", "insufficient_spendable_balance")])
def test_application_retains_fail_closed_rejections(failure, match):
    trace = []; ns = namespace(APPLICATION, trace); ex = Fake("coinbase", True, failure)
    try:
        with pytest.raises(RuntimeError, match=match) as error: asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines: coroutine.close()
    assert "create_order" not in ex.calls and "secret" not in str(error.value)
    if failure in {"permissions", "missing_portfolio"}: assert "balance" not in ex.calls


def test_existing_risk_block_precedes_private_preflight():
    trace = []; ns = namespace(APPLICATION, trace, True); ex = Fake("coinbase", True)
    with pytest.raises(RuntimeError, match="existing risk block"):
        asyncio.run(ns["place_order_async"](ex))
    assert ex.calls == []


def test_cancelled_read_propagates_without_submission_or_retry():
    trace = []; ns = namespace(APPLICATION, trace); ex = Fake("coinbase", True, "cancel")
    try:
        with pytest.raises(asyncio.CancelledError): asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines: coroutine.close()
    assert ex.calls == ["permissions"]


def test_synchronous_definitions_only_change_reviewed_funding_and_order_context():
    def selected(path):
        return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
                if isinstance(node, ast.FunctionDef)}
    before = selected(ORIGINAL); after = selected(APPLICATION)
    assert {name for name in before if before[name] != after[name]} == {
        "_coinbase_spendable_from_info_rows", "_extract_spendable_balance", "_enforce_fail_closed"}


def test_application_is_exact_reviewed_proposal():
    expected = ast.parse(PROPOSAL.read_bytes())
    calls = [node for node in ast.walk(expected) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "mr_validate"]
    assert len(calls) == 1
    calls[0].keywords.append(ast.keyword(arg="order_type", value=ast.Name(id="order_type", ctx=ast.Load())))
    assert ast.dump(ast.parse(APPLICATION.read_bytes()), include_attributes=False) == ast.dump(expected, include_attributes=False)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("portfolio", [None, "p-other"])
def test_applied_async_path_refuses_unscoped_sell_before_submission(asynchronous, portfolio):
    class UnscopedFunding(Fake):
        def fetch_balance(self):
            held = {"currency": {"code": "ETH"}, "balance": {"amount": "5"}}
            if portfolio is not None:
                held["portfolio_id"] = portfolio
            return self.value("balance", {"free": {"USD": 100, "ETH": 5}, "info": {"data": [
                {"currency": {"code": "USD"}, "portfolio_id": "p-1", "balance": {"amount": "100"}}, held]}})
    trace = []; ns = namespace(APPLICATION, trace)
    ex = UnscopedFunding("coinbase", asynchronous)
    try:
        with pytest.raises(RuntimeError, match="insufficient_spendable_balance"):
            asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines:
            coroutine.close()
    assert trace == ["risk_guard"] and ex.calls == ["permissions", "balance"]


@pytest.mark.parametrize("venue", ["coinbase", "invented-other"])
@pytest.mark.parametrize("insufficient", [False, True])
def test_applied_buy_preflight_uses_quote_funds(venue, insufficient):
    trace = []; ns = namespace(APPLICATION, trace, side="buy")
    ex = Fake(venue, True, "insufficient" if insufficient else None)
    try:
        if insufficient:
            with pytest.raises(RuntimeError, match="insufficient_spendable_balance"):
                asyncio.run(ns["place_order_async"](ex))
            assert "create_order" not in ex.calls
        else:
            with pytest.raises(SubmissionReached): asyncio.run(ns["place_order_async"](ex))
    finally:
        for coroutine in ex.coroutines: coroutine.close()
