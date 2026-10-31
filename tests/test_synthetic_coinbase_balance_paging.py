"""Synthetic native response pages only; no CCXT/client/network imports."""

import ast
import asyncio
from copy import deepcopy
import math
from pathlib import Path
import socket

import pytest

from scripts.research import synthetic_coinbase_balance_paging as pager


SCOPE = ["invented-coinbase", "account-A"]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def account(version, identity="one", currency="BTC", units="3"):
    if version == "v2":
        return {"id": identity, "currency": {"code": currency}, "name": currency+" Wallet",
                "portfolio_id": "portfolio-A", "allow_withdrawals": True,
                "balance": {"currency": currency, "amount": units}}
    return {"uuid": identity, "currency": currency,
            "available_balance": {"currency": currency, "value": units},
            "hold": {"currency": currency, "value": "1"}}


def page(version, rows, cursor=None):
    body = ({"data": rows, "pagination": {"next_starting_after": cursor}}
            if version == "v2" else {"accounts": rows, "has_next": cursor is not None, "cursor": cursor})
    return {"scope": list(SCOPE), "body": body}


def run(version, pages, asynchronous=False, **changes):
    calls = []; pages = iter(pages)
    def fetch(params):
        calls.append(params)
        result = next(pages)
        if isinstance(result, Exception): raise result
        return result
    async def fetch_async(params): return fetch(params)
    options = dict(version=version, scope=SCOPE, page_size=100, max_pages=3,
                   max_rows=20, max_json_bytes=10000, deadline=10, clock=lambda: 1)
    options.update(changes)
    result = (asyncio.run(pager.collect_async(fetch_async, **options)) if asynchronous
              else pager.collect_sync(fetch, **options))
    return result, calls


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_two_pages_preserve_native_rows_and_exact_totals(version, asynchronous):
    pages = [page(version, [account(version)], "next"),
             page(version, [account(version, "two", "ETH", "2.5")])]
    original = deepcopy(pages)
    result, calls = run(version, pages, asynchronous)
    assert result["status"] == "COMPLETE" and result["raw_pages"] == original
    assert calls == [{"limit": 100}, {"limit": 100, "starting_after" if version == "v2" else "cursor": "next"}]
    assert result["view"]["total"]["ETH"] == ([5, 2] if version == "v2" else [7, 2])
    assert result["view"]["available"] == (None if version == "v2" else {"BTC": [3, 1], "ETH": [5, 2]})
    assert ("data" in result["view"]["info"]) is (version == "v2")
    assert not result["scope_authenticated"] and not result["spendable_verified"] and not result["execution_authority"]


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_failed_second_page_never_exposes_partial_balance(version, asynchronous):
    result, calls = run(version, [page(version, [account(version)], "next"), RuntimeError("secret must not escape")], asynchronous)
    assert len(calls) == 2 and result["status"] == "INCOMPLETE" and result["view"] is None
    assert len(result["raw_pages"]) == 1 and "secret" not in result["reason"]


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_duplicate_rows_deduplicated_conflicts_refused(version):
    row = account(version)
    result, _ = run(version, [page(version, [row], "next"), page(version, [deepcopy(row)])])
    assert result["status"] == "COMPLETE"
    assert len(result["view"]["info"]["data" if version == "v2" else "accounts"]) == 1
    altered = account(version, units="4")
    result, _ = run(version, [page(version, [row], "next"), page(version, [altered])])
    assert result["reason"] == "conflicting_account" and result["view"] is None


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_cursor_loop_and_page_budget_fail_closed(version):
    pages = [page(version, [account(version)], "next"), page(version, [account(version)], "next")]
    result, calls = run(version, pages)
    assert result["reason"] == "repeated_or_missing_cursor" and len(calls) == 2
    result, calls = run(version, pages, max_pages=1)
    assert result["reason"] == "page_budget" and len(calls) == 1 and result["view"] is None


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("kind", ["scope", "missing_cursor", "bad_rows", "invalid_number", "currency", "empty_nonterminal"])
def test_malformed_or_incomplete_evidence(version, kind):
    p = page(version, [account(version)], "next")
    rows = p["body"]["data" if version == "v2" else "accounts"]
    if kind == "scope": p["scope"][1] = "account-B"
    if kind == "missing_cursor":
        if version == "v2": del p["body"]["pagination"]["next_starting_after"]
        else: del p["body"]["cursor"]
    if kind == "bad_rows": p["body"]["data" if version == "v2" else "accounts"] = None
    if kind == "invalid_number":
        rows[0]["balance" if version == "v2" else "available_balance"]["amount" if version == "v2" else "value"] = "NaN"
    if kind == "currency": rows[0]["balance" if version == "v2" else "hold"]["currency"] = "WRONG"
    if kind == "empty_nonterminal": rows.clear()
    result, _ = run(version, [p])
    assert result["status"] == "INCOMPLETE" and result["view"] is None


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_row_byte_and_deadline_budgets(version):
    p = page(version, [account(version), account(version, "two")])
    result, _ = run(version, [p], max_rows=1)
    assert result["reason"] == "row_budget"
    result, _ = run(version, [p], max_json_bytes=1)
    assert result["reason"] == "json_byte_budget" and result["raw_pages"] == []
    result, calls = run(version, [p], clock=lambda: 10)
    assert result["reason"] == "deadline_or_clock" and calls == []
    ticks = iter([1, 11])
    result, calls = run(version, [p], clock=lambda: next(ticks))
    assert result["reason"] == "deadline_or_clock" and len(calls) == 1


def test_page_two_v2_rows_reach_existing_funding_reader_without_importing_it():
    source = Path(__file__).resolve().parents[1] / "services/execution/place_order.py"
    names = {"_float_or_none", "_coinbase_row_currency_code", "_coinbase_row_amount",
             "_coinbase_row_trade_spendable", "_coinbase_spendable_from_info_rows"}
    tree = ast.parse(source.read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(selected) == len(names)
    namespace = {"math": math}
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, *selected], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(source), "exec"), namespace)
    result, _ = run("v2", [page("v2", [account("v2")], "next"), page("v2", [account("v2", "two", "ETH", "2.5")])])
    value, origin = namespace["_coinbase_spendable_from_info_rows"](
        {"info": result["view"]["info"]}, asset="ETH", portfolio_uuid="portfolio-A")
    assert value == 2.5 and origin == "coinbase.info_rows_spendable"


@pytest.mark.parametrize("changes", [{"max_pages": 0}, {"page_size": True}, {"deadline": float('inf')}, {"version": "guess"}])
def test_invalid_contract_refused_before_callback(changes):
    options = {k: v for k, v in changes.items() if k != "version"}
    with pytest.raises(ValueError): run(changes.get("version", "v2"), [], **options)


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_distinct_account_ids_with_same_currency_are_summed(version):
    result, _ = run(version, [page(version, [account(version)], "next"),
                            page(version, [account(version, "two", units="2.5")])])
    assert result["view"]["total"]["BTC"] == ([11, 2] if version == "v2" else [15, 2])


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_long_cursor_cycle_fails_before_revisiting_page(version):
    pages = [page(version, [account(version)], cursor) for cursor in ["A", "B", "A"]]
    result, calls = run(version, pages)
    assert result["reason"] == "repeated_or_missing_cursor" and len(calls) == 3
    assert result["view"] is None


def test_v2_next_uri_is_never_followed():
    first = page("v2", [account("v2")], "cursor-token")
    first["body"]["pagination"]["next_uri"] = "https://not-an-approved-recipient.invalid/"
    result, calls = run("v2", [first, page("v2", [])])
    assert result["status"] == "COMPLETE"
    assert calls[1] == {"limit": 100, "starting_after": "cursor-token"}
    first["body"]["pagination"]["next_starting_after"] = None
    result, _ = run("v2", [first])
    assert result["reason"] == "continuation_inconsistent"


def test_v3_terminal_cursor_is_not_mistaken_for_more_pages():
    p = page("v3", [account("v3")]); p["body"]["cursor"] = "last-seen-token"
    result, calls = run("v3", [p])
    assert result["status"] == "COMPLETE" and len(calls) == 1


def test_async_cancellation_propagates_without_retry():
    calls = []
    async def fetch(params):
        calls.append(params)
        raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(pager.collect_async(fetch, version="v3", scope=SCOPE, page_size=100,
            max_pages=3, max_rows=20, max_json_bytes=10000, deadline=10, clock=lambda: 1))
    assert len(calls) == 1


def test_nonfinite_clock_refuses_before_callback():
    result, calls = run("v2", [], clock=lambda: float("nan"))
    assert result["reason"] == "deadline_or_clock" and calls == []


def test_regressed_clock_cannot_extend_budget():
    ticks = iter([2, 1])
    result, calls = run("v2", [page("v2", [])], clock=lambda: next(ticks))
    assert result["reason"] == "deadline_or_clock" and len(calls) == 1


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_explicit_provider_error_with_rows_never_grants_completion(version):
    p = page(version, [account(version)])
    p["body"]["errors"] = [{"id": "invented-partial-response"}]
    result, _ = run(version, [p])
    assert result["reason"] == "provider_error" and result["view"] is None


@pytest.mark.parametrize("asynchronous", [False, True])
def test_callback_cannot_leak_message_using_library_error_type(asynchronous):
    result, _ = run("v2", [pager.Incomplete("secret must not escape")], asynchronous)
    assert result["reason"] == "page_callback_failure" and result["view"] is None


def test_clock_failure_message_is_sanitized():
    def broken(): raise pager.Incomplete("secret clock detail")
    result, calls = run("v2", [], clock=broken)
    assert result["reason"] == "clock_failure" and calls == []
