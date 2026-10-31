"""Offline selected-source chain: paging -> installed parser -> existing guards."""

import ast
import asyncio
from copy import deepcopy
from decimal import Decimal
import logging
import math
from pathlib import Path
import socket

import pytest

from services.execution import coinbase_account_pages as reader


ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / ".venv/lib/python3.12/site-packages/ccxt"
PROPOSAL = ROOT / "docs/review_artifacts/coinbase_paged_preflight_20261028_01/place_order_proposed.py"
FUNDING_FUNCTIONS = {"_float_or_none", "_split_symbol", "_coinbase_portfolio_uuid", "_coinbase_row_currency_code",
                     "_coinbase_row_amount", "_coinbase_row_trade_spendable", "_coinbase_spendable_from_info_rows",
                     "_extract_spendable_balance", "_enforce_funding_gate", "_parse_order_amount", "_parse_order_price"}


def selected(path, names, namespace, class_name=None):
    tree = ast.parse(path.read_bytes())
    source = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name).body if class_name else tree.body
    nodes = [n for n in source if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    if class_name:
        nodes = [ast.ClassDef(name=class_name, bases=[], keywords=[], body=nodes, decorator_list=[])]
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)


@pytest.fixture
def chain(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    ns = {"math": math, "Decimal": Decimal, "_LOG": logging.getLogger("offline-paged-preflight"),
          "decimal_value": lambda x, **kw: Decimal(str(x)),
          "_estimate_funding_required": lambda a, p: Decimal(str(a)) * Decimal(str(p)) * Decimal("1.005")}
    selected(SDK / "base/precise.py", {"Precise"}, ns)
    selected(SDK / "base/exchange.py", {"safe_list_2", "safe_list_n", "safe_list", "safe_value_n",
             "get_object_value_from_key_list", "safe_value", "safe_dict", "safe_string", "in_array",
             "account", "safe_balance", "omit", "parse_number"}, ns, "Exchange")
    selected(SDK / "coinbase.py", {"parse_custom_balance"}, ns, "coinbase")
    # A parsing-only context, not a CCXT client: no constructor, transport or keys.
    class ParsingContext(ns["Exchange"], ns["coinbase"]):
        options = {"accounts": ["wallet", "fiat"],
                   "v3Accounts": ["ACCOUNT_TYPE_CRYPTO", "ACCOUNT_TYPE_FIAT"]}
        number = float
        def safe_currency_code(self, code):
            assert code in {"USD", "ETH"}
            return code  # Fixture identity mapping, not a production registry.
    selected(ROOT / "services/execution/coinbase_portfolio_guard.py",
             {"_get_portfolio_uuid", "_get_portfolio_currencies", "_split_symbol",
              "enforce_coinbase_quote_account_available"}, ns)
    selected(ROOT / "services/execution/place_order.py", FUNDING_FUNCTIONS, ns)
    return ParsingContext(), ns


def account(version, identity, currency, quantity, **extra):
    if version == "v2":
        return dict(id=identity, currency={"code": currency}, type="wallet", portfolio_id="p-1",
                    balance={"amount": str(quantity), "currency": currency}, **extra)
    return dict(uuid=identity, currency=currency, type="ACCOUNT_TYPE_CRYPTO", retail_portfolio_id="p-1",
                available_balance={"value": str(quantity), "currency": currency},
                hold={"value": "0", "currency": currency}, **extra)


def native_pages(version, second=None):
    one = [account(version, "usd", "USD", 100)]
    two = second if second is not None else [account(version, "eth", "ETH", 5)]
    return ([{"data": one, "pagination": {"next_starting_after": "next"}},
             {"data": two, "pagination": {"next_starting_after": None}}] if version == "v2" else
            [{"accounts": one, "has_next": True, "cursor": "next"},
             {"accounts": two, "has_next": False, "cursor": ""}])


class InventedClient:
    id = "coinbase"
    def __init__(self, pages, asynchronous):
        self.pages = iter(pages); self.calls = []; self.asynchronous = asynchronous
    def page(self, params):
        self.calls.append(deepcopy(params))
        value = next(self.pages)
        def result():
            if isinstance(value, Exception):
                raise value
            return value
        if self.asynchronous:
            async def awaited():
                return result()
            return awaited()
        return result()
    v2PrivateGetAccounts = page
    v3PrivateGetBrokerageAccounts = page
    def fetch_balance(self):
        raise AssertionError("one-page fallback forbidden")


def collect(version, asynchronous, pages):
    client = InventedClient(pages, asynchronous)
    options = dict(version=version, scope=["coinbase", "invented-account"], page_size=100,
                   max_pages=3, max_rows=10, max_json_bytes=10000, clock=lambda: 1, deadline=10)
    result = (asyncio.run(reader.read_account_pages_async(client, **options)) if asynchronous
              else reader.read_account_pages_sync(client, **options))
    return result, client


def observation(balance):
    class Observed:
        id = "coinbase"
        def fetch_balance(self):
            return balance
        def v3PrivateGetBrokerageKeyPermissions(self):
            return {"portfolio_uuid": "p-1"}
    return Observed()


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_page_two_asset_survives_installed_parser(chain, version, asynchronous):
    parser, _ = chain
    result, client = collect(version, asynchronous, native_pages(version))
    assert result["status"] == "COMPLETE" and len(client.calls) == 2
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    assert balance["total"] == {"USD": 100.0, "ETH": 5.0}
    assert balance["info"] == result["view"]["info"]
    assert not result["scope_authenticated"] and not result["execution_authority"]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("side", ["buy", "sell"])
def test_v2_existing_guards_consume_complete_rows(chain, asynchronous, side):
    parser, guards = chain
    result, _ = collect("v2", asynchronous, native_pages("v2"))
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    ex = observation(balance)
    guards["enforce_coinbase_quote_account_available"](ex, "ETH/USD")
    guards["_enforce_funding_gate"](ex, symbol="ETH/USD", side=side, amount=1, price=10, order_type="limit")
    assert guards["_extract_spendable_balance"](ex, balance, "ETH")[1].startswith("coinbase.info_rows_spendable")


@pytest.mark.parametrize("asynchronous", [False, True])
def test_v3_is_not_drop_in_legacy_portfolio_input(chain, asynchronous):
    parser, guards = chain
    result, _ = collect("v3", asynchronous, native_pages("v3"))
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    assert "data" not in balance["info"] and balance["free"]["USD"] == 100
    with pytest.raises(RuntimeError, match="portfolio_account_unavailable"):
        guards["enforce_coinbase_quote_account_available"](observation(balance), "ETH/USD")


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_partial_pages_never_reach_parser(chain, version, asynchronous):
    parser, _ = chain
    result, client = collect(version, asynchronous, [native_pages(version)[0], RuntimeError("private detail")])
    assert len(client.calls) == 2 and result["view"] is None and result["status"] == "INCOMPLETE"
    assert "private detail" not in result["reason"]
    # No merged native body is exposed to parse; no partial balance synthesized.
    assert "balance" not in result


@pytest.mark.parametrize("case", ["staked", "other_portfolio", "overdraw"])
def test_v2_does_not_turn_total_holdings_into_unrestricted_sell_funds(chain, case):
    parser, guards = chain
    extra = {"name": "Staked ETH"} if case == "staked" else {}
    row = account("v2", "eth", "ETH", 5, **extra)
    if case == "other_portfolio":
        row["portfolio_id"] = "p-other"
    result, _ = collect("v2", False, native_pages("v2", [row]))
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    ex = observation(balance)
    if case == "other_portfolio":
        # Existing funding fallback ignores this row filter; pin it, do not bless it.
        assert guards["_extract_spendable_balance"](ex, balance, "ETH") == (5.0, "free")
        guards["enforce_coinbase_quote_account_available"](ex, "ETH/USD")
        guards["_enforce_funding_gate"](ex, symbol="ETH/USD", side="sell",
            amount=1, price=10, order_type="limit")
    else:
        with pytest.raises(RuntimeError, match="insufficient_spendable_balance"):
            guards["_enforce_funding_gate"](ex, symbol="ETH/USD", side="sell",
                amount=6 if case == "overdraw" else 1, price=10, order_type="limit")


@pytest.mark.parametrize("case", ["other_portfolio", "missing_row_portfolio", "permissions_unknown",
                                 "aggregate_only", "missing_asset", "malformed_rows"])
def test_proposal_refuses_unproven_coinbase_funding_where_base_accepts(chain, case):
    parser, guards = chain
    result, _ = collect("v2", False, native_pages("v2"))
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    if case == "other_portfolio":
        balance["info"]["data"][1]["portfolio_id"] = "p-other"
    elif case == "missing_row_portfolio":
        del balance["info"]["data"][1]["portfolio_id"]
    elif case == "aggregate_only":
        del balance["info"]["data"]
    elif case == "missing_asset":
        balance["info"]["data"] = balance["info"]["data"][:1]
    elif case == "malformed_rows":
        balance["info"]["data"] = "unreadable"
    ex = observation(balance)
    if case == "permissions_unknown":
        ex.v3PrivateGetBrokerageKeyPermissions = lambda: {}
    args = dict(symbol="ETH/USD", side="sell", amount=1, price=10, order_type="limit")
    guards["_enforce_funding_gate"](ex, **args)  # Reproduces the base's fallback.
    selected(PROPOSAL, FUNDING_FUNCTIONS, guards)
    with pytest.raises(RuntimeError, match="insufficient_spendable_balance"):
        guards["_enforce_funding_gate"](ex, **args)


@pytest.mark.parametrize("side", ["buy", "sell"])
@pytest.mark.parametrize("venue", ["coinbase", "invented-other"])
def test_proposal_preserves_scoped_funding_and_other_venues(chain, side, venue):
    parser, guards = chain
    result, _ = collect("v2", False, native_pages("v2"))
    balance = parser.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
    ex = observation(balance); ex.id = venue
    args = dict(symbol="ETH/USD", side=side, amount=1, price=10, order_type="limit")
    before = guards["_extract_spendable_balance"](ex, balance, "ETH")
    selected(PROPOSAL, FUNDING_FUNCTIONS, guards)
    assert guards["_extract_spendable_balance"](ex, balance, "ETH") == before
    guards["_enforce_funding_gate"](ex, **args)


def test_proposal_changes_only_two_funding_helpers():
    original = ast.parse((PROPOSAL.parent / "place_order_original.py").read_bytes())
    proposal = ast.parse(PROPOSAL.read_bytes())
    def definitions(tree):
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    a, b = definitions(original), definitions(proposal)
    assert a.keys() == b.keys()
    assert {name for name in a if a[name] != b[name]} == {
        "_coinbase_spendable_from_info_rows", "_extract_spendable_balance"}
    assert (ROOT / "services/execution/place_order.py").read_bytes() == (PROPOSAL.parent / "place_order_original.py").read_bytes()
