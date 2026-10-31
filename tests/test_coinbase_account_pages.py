"""Unwired reader against invented SDK clients; no account/client construction."""

import ast
import asyncio
from copy import deepcopy
from pathlib import Path
import socket

import pytest

from services.execution import coinbase_account_pages as reader


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs): raise AssertionError("network forbidden")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


def row(version, identity, currency):
    if version == "v2":
        return {"id": identity, "currency": {"code": currency},
                "balance": {"amount": "2", "currency": currency}}
    return {"uuid": identity, "currency": currency,
            "available_balance": {"value": "2", "currency": currency},
            "hold": {"value": "1", "currency": currency}}


def pages(version):
    first, last = [row(version, "one", "BTC")], [row(version, "two", "ETH")]
    return ([{"data": first, "pagination": {"next_starting_after": "next"}},
             {"data": last, "pagination": {"next_starting_after": None}}] if version == "v2" else
            [{"accounts": first, "has_next": True, "cursor": "next"},
             {"accounts": last, "has_next": False, "cursor": ""}])


class FakeSDK:
    id = "coinbase"
    def __init__(self, responses, asynchronous=False):
        self.responses = iter(responses); self.calls = []; self.asynchronous = asynchronous
    def call(self, name, params):
        self.calls.append((name, deepcopy(params)))
        response = next(self.responses)
        if self.asynchronous:
            async def value():
                if isinstance(response, Exception): raise response
                return response
            return value()
        if isinstance(response, Exception): raise response
        return response
    def v2PrivateGetAccounts(self, params): return self.call("v2", params)
    def v3PrivateGetBrokerageAccounts(self, params): return self.call("v3", params)
    def fetch_balance(self): raise AssertionError("one-page fallback forbidden")
    def create_order(self, *args, **kwargs): raise AssertionError("order forbidden")


def options(version):
    return dict(version=version, scope=["coinbase", "invented-account"], page_size=100,
                max_pages=3, max_rows=10, max_json_bytes=10000, deadline=10, clock=lambda: 1)


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("mode", ["sync", "async", "async_with_sync_client"])
def test_exact_whitelisted_method_paging_and_no_authority(version, mode):
    client = FakeSDK(pages(version), asynchronous=mode == "async")
    result = (reader.read_account_pages_sync(client, **options(version)) if mode == "sync"
              else asyncio.run(reader.read_account_pages_async(client, **options(version))))
    assert result["status"] == "COMPLETE" and len(client.calls) == 2
    assert all(name == version for name, _ in client.calls)
    cursor = "starting_after" if version == "v2" else "cursor"
    assert client.calls == [(version, {"limit": 100}), (version, {"limit": 100, cursor: "next"})]
    assert "ETH" in result["view"]["total"]
    assert not result["scope_authenticated"] and not result["spendable_verified"]
    assert not result["execution_authority"]


@pytest.mark.parametrize("version", ["v2", "v3"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_page_two_failure_never_falls_back(version, asynchronous):
    client = FakeSDK([pages(version)[0], RuntimeError("secret response")], asynchronous)
    result = (asyncio.run(reader.read_account_pages_async(client, **options(version))) if asynchronous
              else reader.read_account_pages_sync(client, **options(version)))
    assert result["status"] == "INCOMPLETE" and result["view"] is None
    assert result["reason"] == "page_callback_failure" and len(client.calls) == 2


def test_wrong_client_and_missing_method_rejected_before_calls():
    client = FakeSDK([]); client.id = "other"
    with pytest.raises(ValueError): reader.read_account_pages_sync(client, **options("v2"))
    assert client.calls == []
    client.id = "coinbase"; client.v2PrivateGetAccounts = None
    with pytest.raises(ValueError): reader.read_account_pages_sync(client, **options("v2"))


def test_sync_reader_refuses_async_result_without_fallback_or_event_loop():
    client = FakeSDK(pages("v2"), asynchronous=True)
    result = reader.read_account_pages_sync(client, **options("v2"))
    assert result["status"] == "INCOMPLETE" and result["view"] is None
    assert len(client.calls) == 1


def test_declared_async_method_rejected_before_invocation():
    class AsyncSDK(FakeSDK):
        async def v2PrivateGetAccounts(self, params):
            raise AssertionError("must not be called by synchronous reader")
    with pytest.raises(ValueError, match="async_client"):
        reader.read_account_pages_sync(AsyncSDK([]), **options("v2"))


def test_invalid_budgets_before_getting_endpoint():
    client = FakeSDK([])
    settings = options("v2"); settings["max_pages"] = 0
    with pytest.raises(ValueError): reader.read_account_pages_sync(client, **settings)
    assert client.calls == []


@pytest.mark.parametrize("version", ["v2", "v3"])
def test_async_cancellation_propagates_without_retry(version):
    class CancelledSDK(FakeSDK):
        async def cancel(self, params):
            self.calls.append((version, deepcopy(params)))
            raise asyncio.CancelledError()
        v2PrivateGetAccounts = cancel
        v3PrivateGetBrokerageAccounts = cancel
    client = CancelledSDK([])
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(reader.read_account_pages_async(client, **options(version)))
    assert client.calls == [(version, {"limit": 100})]


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("times, expected_calls", [([10], 0), ([1, 10], 1)])
def test_deadline_withholds_expired_result_without_next_request(mode, times, expected_calls):
    client = FakeSDK(pages("v2"), asynchronous=mode == "async")
    settings = options("v2")
    settings["clock"] = iter(times).__next__
    result = (reader.read_account_pages_sync(client, **settings) if mode == "sync"
              else asyncio.run(reader.read_account_pages_async(client, **settings)))
    assert result["status"] == "INCOMPLETE" and result["view"] is None
    assert result["reason"] == "deadline_or_clock"
    assert len(client.calls) == expected_calls


def test_core_is_ast_identical_to_independently_accepted_prototype():
    root = Path(__file__).resolve().parents[1]
    def definitions(path):
        return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_bytes()).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    before = definitions(root / "scripts/research/synthetic_coinbase_balance_paging.py")
    after = definitions(root / "services/execution/coinbase_account_pages.py")
    assert all(before[name] == after[name] for name in before)
