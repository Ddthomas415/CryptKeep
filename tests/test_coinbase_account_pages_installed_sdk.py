"""Actual installed SDK dispatch/parser, with request/auth/transport kept offline."""

import asyncio
from copy import deepcopy
import socket
import subprocess

import pytest

from services.execution import coinbase_account_pages as reader


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("transport/auth/process forbidden in SDK compatibility test")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    def no_process(*args, **kwargs):
        # Vendored version metadata probes git at import; refuse it as unavailable.
        raise FileNotFoundError("child process forbidden")
    monkeypatch.setattr(subprocess, "Popen", no_process)
    import requests
    import aiohttp
    import ccxt
    import ccxt.async_support as async_sdk
    monkeypatch.setattr(requests.Session, "request", refuse)
    monkeypatch.setattr(aiohttp.ClientSession, "_request", refuse)
    for cls in (ccxt.coinbase, async_sdk.coinbase):
        for method in ("fetch", "sign", "check_required_credentials", "create_order", "fetch_balance"):
            monkeypatch.setattr(cls, method, refuse)


def account(version, identity, currency, free, held=0):
    if version == "v2":
        return {"id": identity, "currency": {"code": currency}, "type": "wallet",
                "balance": {"amount": str(free + held), "currency": currency}}
    return {"uuid": identity, "currency": currency, "type": "ACCOUNT_TYPE_CRYPTO",
            "available_balance": {"value": str(free), "currency": currency},
            "hold": {"value": str(held), "currency": currency}}


def pages(version):
    first = [account(version, "usd", "USD", 100), account(version, "eth-one", "ETH", 2, 1)]
    second = [account(version, "eth-two", "ETH", 1, 1), account(version, "sol", "SOL", 5, 2)]
    if version == "v2":
        return [{"data": first, "pagination": {"next_starting_after": "page-two"}},
                {"data": second, "pagination": {"next_starting_after": None}}]
    return [{"accounts": first, "has_next": True, "cursor": "page-two"},
            {"accounts": second, "has_next": False, "cursor": ""}]


def options(version, **overrides):
    return {"version": version, "scope": ["coinbase", "invented-scope-not-authenticated"],
            "page_size": 100, "max_pages": 3, "max_rows": 10, "max_json_bytes": 20000,
            "deadline": 10, "clock": lambda: 1} | overrides


def bind_dispatch(client, version, responses, calls, asynchronous):
    remaining = iter(responses)
    def supplied(path, api, method, params, **kwargs):
        assert path == ("accounts" if version == "v2" else "brokerage/accounts")
        assert api == [version, "private"] and method == "GET"
        calls.append({"path": path, "api": deepcopy(api), "params": deepcopy(params)})
        value = next(remaining)
        if isinstance(value, BaseException):
            raise value
        return deepcopy(value)
    if asynchronous:
        async def request(*args, **kwargs):
            return supplied(*args, **kwargs)
    else:
        request = supplied
    # Keep the SDK's actual Entry descriptors: replace only their request target.
    client.request = request


def invoke(version, asynchronous, responses, inspect_result, **overrides):
    calls = []
    async def scenario():
        import ccxt
        import ccxt.async_support as async_sdk
        cls = async_sdk.coinbase if asynchronous else ccxt.coinbase
        client = cls({"apiKey": None, "secret": None, "enableRateLimit": False})
        assert client.apiKey is None and client.secret is None
        bind_dispatch(client, version, responses, calls, asynchronous)
        try:
            settings = options(version, **overrides)
            result = (await reader.read_account_pages_async(client, **settings) if asynchronous
                      else reader.read_account_pages_sync(client, **settings))
            inspect_result(result, client, calls)
        finally:
            if asynchronous:
                await client.close()
    asyncio.run(scenario())
    return calls


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_sdk_dispatch_and_parser_keep_page_two_asset_and_held_amounts(version, asynchronous):
    def inspect(result, client, calls):
        assert result["status"] == "COMPLETE" and len(calls) == 2
        cursor = "starting_after" if version == "v2" else "cursor"
        assert [call["params"] for call in calls] == [
            {"limit": 100}, {"limit": 100, cursor: "page-two"}]
        assert result["view"]["total"] == {"USD": [100, 1], "ETH": [5, 1], "SOL": [7, 1]}
        # Actual installed parser, not an AST extraction or parsing-context stub.
        balance = client.parse_custom_balance(deepcopy(result["view"]["info"]), {"type": "spot"})
        assert balance["total"] == {"USD": 100, "ETH": 5, "SOL": 7}
        assert balance["info"] == result["view"]["info"]
        if version == "v3":
            assert result["view"]["available"]["SOL"] == [5, 1]
            assert result["view"]["used"]["SOL"] == [2, 1]
            assert balance["free"]["SOL"] == 5 and balance["used"]["SOL"] == 2
            assert "data" not in balance["info"]
        else:
            assert result["view"]["available"] is None
        assert result["qualification"] == "SUPPLIED_SDK_PAGES_NOT_AUTHENTICATED_SCOPE_OR_CCXT_BALANCE"
        assert result["scope_authenticated"] is False and result["spendable_verified"] is False
        assert result["execution_authority"] is False
    invoke(version, asynchronous, pages(version), inspect)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_dispatch_page_two_failure_withholds_entire_view(version, asynchronous):
    def inspect(result, client, calls):
        assert result["status"] == "INCOMPLETE" and result["view"] is None and len(calls) == 2
        assert result["reason"] == "page_callback_failure"
        assert "private detail" not in str(result["reason"])
    invoke(version, asynchronous, [pages(version)[0], RuntimeError("private detail")], inspect)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_dispatch_repeated_cursor_is_not_a_complete_account(version, asynchronous):
    def inspect(result, client, calls):
        assert result["status"] == "INCOMPLETE" and result["view"] is None and len(calls) == 2
        assert result["reason"] == "repeated_or_missing_cursor"
    invoke(version, asynchronous, [pages(version)[0], pages(version)[0]], inspect)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_dispatch_conflicting_duplicate_account_is_not_added_twice(version, asynchronous):
    responses = pages(version)
    responses[1]["data" if version == "v2" else "accounts"] = [account(version, "eth-one", "ETH", 999)]
    def inspect(result, client, calls):
        assert result["status"] == "INCOMPLETE" and result["view"] is None
        assert result["reason"] == "conflicting_account" and len(calls) == 2
    invoke(version, asynchronous, responses, inspect)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_dispatch_page_budget_does_not_turn_missing_holdings_into_zero(version, asynchronous):
    def inspect(result, client, calls):
        assert result["status"] == "INCOMPLETE" and result["view"] is None
        assert result["reason"] == "page_budget" and len(calls) == 1
    invoke(version, asynchronous, pages(version), inspect, max_pages=1)


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_real_async_dispatch_cancellation_propagates_without_fallback(version):
    def unreachable(*args):
        raise AssertionError("cancellation must not return a usable result")
    with pytest.raises(asyncio.CancelledError):
        invoke(version, True, [pages(version)[0], asyncio.CancelledError()], unreachable)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_server_next_uri_is_never_used_as_a_request_target(version, asynchronous):
    responses = pages(version)
    if version == "v2":
        responses[0]["pagination"]["next_uri"] = "https://do-not-follow.invalid/accounts"
    else:
        responses[0]["next_uri"] = "https://do-not-follow.invalid/accounts"
    def inspect(result, client, calls):
        assert result["status"] == "COMPLETE" and len(calls) == 2
        assert all("next_uri" not in call["params"] for call in calls)
        assert all(call["path"] == ("accounts" if version == "v2" else "brokerage/accounts") for call in calls)
    invoke(version, asynchronous, responses, inspect)
