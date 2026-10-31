"""Offline actual market validator and selected public-fetcher regression tests."""

import ast
from copy import deepcopy
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

import pytest

from services.markets import rules as subject
from services.markets.cache_sqlite import upsert, get
from services.markets.models import MarketRules


ROOT = Path(__file__).resolve().parents[1]


def product(**changes):
    value = {"product_id": "ETH-USD", "status": "online", "trading_disabled": False,
             "cancel_only": False, "limit_only": False, "post_only": False, "auction_mode": False}
    value.update(changes)
    return value


def rule(snapshot=None, *, venue="coinbase"):
    return MarketRules(venue, "ETH-USD", "ETH-USD", True,
                       meta={"coinbase_product": snapshot if snapshot is not None else product()})


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network/public refresh forbidden unless replaced by fixture")
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(subject, "fetch_and_cache", refuse)


@pytest.mark.parametrize("order_type", ["market", "limit"])
@pytest.mark.parametrize("mode", ["normal", "cancel_only", "limit_only", "post_only", "auction_mode",
                                   "trading_disabled", "offline", "view_only"])
def test_actual_validator_blocks_disallowed_modes_without_conversion(monkeypatch, mode, order_type):
    snapshot = product()
    if mode == "offline": snapshot["status"] = "offline"
    elif mode != "normal": snapshot[mode] = True
    r = rule(snapshot); before = deepcopy(r)
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: r)
    result = subject.validate("unused", "coinbase", "ETH-USD", qty=1, notional=10, order_type=order_type)
    allowed = mode == "normal" or (mode == "limit_only" and order_type == "limit")
    assert result.ok is allowed and r == before
    assert result.rules is r
    if not allowed:
        assert result.code.startswith("COINBASE_")


@pytest.mark.parametrize("change", [lambda p: p.pop("cancel_only"),
    lambda p: p.update(cancel_only="false"), lambda p: p.update(limit_only=0),
    lambda p: p.update(product_id="BTC-USD"), lambda p: p.update(status=None),
    lambda p: p.update(view_only="false")])
def test_unknown_metadata_cannot_use_active_as_permission(monkeypatch, change):
    snapshot = product(); change(snapshot)
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: rule(snapshot))
    result = subject.validate("unused", "coinbase", "ETH-USD", order_type="market")
    assert not result.ok and result.code == "COINBASE_PRODUCT_MODE_UNKNOWN"


@pytest.mark.parametrize("refreshed", [rule(), MarketRules("coinbase", "ETH-USD", "ETH-USD", False)])
def test_legacy_cache_refreshes_once_without_old_active_fallback(monkeypatch, refreshed):
    old = MarketRules("coinbase", "ETH-USD", "ETH-USD", True, meta={"ccxt_symbol": "ETH/USD"})
    calls = []
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: old)
    def refresh(*args):
        calls.append(args)
        return refreshed
    monkeypatch.setattr(subject, "fetch_and_cache", refresh)
    result = subject.validate("unused", "coinbase", "ETH-USD", order_type="market")
    assert result.ok is refreshed.active and calls == [("unused", "coinbase", "ETH-USD")]


@pytest.mark.parametrize("ttl", [0, -1, True, float("nan"), float("inf")])
def test_invalid_order_context_ttl_fails_before_cache_access(monkeypatch, ttl):
    def refuse(*args, **kwargs):
        raise AssertionError("cache should not be read")
    monkeypatch.setattr(subject, "get_rules", refuse)
    result = subject.validate("unused", "coinbase", "ETH-USD", ttl_s=ttl, order_type="market")
    assert not result.ok and result.code == "INVALID_MARKET_RULES_TTL"


def test_other_venues_and_quantity_only_api_are_unchanged(monkeypatch):
    r = MarketRules("binance", "ETH-USD", "ETH-USD", True)
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: r)
    assert subject.validate("unused", "binance", "ETH-USD", order_type="market").ok
    assert subject.validate("unused", "coinbase", "ETH-USD").ok


def test_alias_malformed_meta_and_unsupported_order_are_fail_closed(monkeypatch):
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: rule(product(cancel_only=True)))
    assert subject.validate("unused", "coinbase_adv", "ETH-USD", order_type="market").code == "COINBASE_CANCEL_ONLY"
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: rule())
    assert subject.validate("unused", "coinbase", "ETH-USD", order_type="stop").code == "COINBASE_ORDER_TYPE_UNSUPPORTED"
    bad = rule(); object.__setattr__(bad, "meta", "malformed")
    monkeypatch.setattr(subject, "get_rules", lambda *a, **k: bad)
    assert subject.validate("unused", "coinbase", "ETH-USD", order_type="market").code == "COINBASE_PRODUCT_MODE_UNKNOWN"


def test_public_fetcher_retains_only_relevant_native_mode_fields(monkeypatch):
    raw = product(limit_only=True); raw["unrelated"] = "not-retained"
    fake = SimpleNamespace(coinbase=lambda options: SimpleNamespace(load_markets=lambda: {
        "ETH/USD": {"id": "ETH-USD", "active": True, "info": raw}}))
    monkeypatch.setitem(sys.modules, "ccxt", fake)
    source = ROOT / "services/markets/fetch_coinbase_ccxt.py"
    node = next(n for n in ast.parse(source.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == "fetch_rules")
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.Module(body=[future, node], type_ignores=[]); ast.fix_missing_locations(module)
    ns = {"MarketRules": MarketRules, "canonicalize": lambda s: s, "coinbase_native": lambda s: s}
    exec(compile(module, str(source), "exec"), ns)
    r = ns["fetch_rules"]("ETH-USD")
    assert r.meta["coinbase_product"] == product(limit_only=True)


def test_mode_metadata_survives_existing_cache_roundtrip(tmp_path):
    path = str(tmp_path / "fixture.sqlite")
    original = rule(product(limit_only=True))
    upsert(path, original)
    assert get(path, "coinbase", "ETH-USD") == original
    result = subject.validate(path, "coinbase", "ETH-USD", ttl_s=100, order_type="market")
    assert not result.ok and result.code == "COINBASE_LIMIT_ONLY"


def test_both_order_entries_reach_order_type_aware_shared_guard():
    tree = ast.parse((ROOT / "services/execution/place_order.py").read_bytes())
    guard = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_enforce_fail_closed")
    call = [n for n in ast.walk(guard) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "mr_validate"]
    assert len(call) == 1
    kw = next(k for k in call[0].keywords if k.arg == "order_type")
    assert isinstance(kw.value, ast.Name) and kw.value.id == "order_type"
    for name in ("place_order", "place_order_async"):
        entry = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
        assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id == "_enforce_fail_closed" for n in ast.walk(entry))
