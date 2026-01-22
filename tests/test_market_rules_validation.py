from __future__ import annotations

import time
import types

import pytest

from services.markets.models import MarketRules
from services.markets.cache_sqlite import ensure_schema, upsert, get, is_fresh, any_fresh
from services.markets.rules import validate
from services.markets.prereq import check_market_rules_prereq


@pytest.fixture()
def tmp_exec_db(tmp_path, monkeypatch):
    db = str(tmp_path / "exec.sqlite")
    # ensure_schema uses provided exec_db directly in our functions
    ensure_schema(db)
    return db


def test_cache_upsert_and_get(tmp_exec_db):
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True, min_notional=10.0, min_qty=0.001, qty_step=0.001)
    upsert(tmp_exec_db, r)
    got = get(tmp_exec_db, "binance", "BTC-USDT")
    assert got is not None
    assert got.venue == "binance"
    assert got.native_symbol == "BTCUSDT"
    assert got.min_notional == 10.0


def test_cache_freshness(tmp_exec_db):
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True)
    upsert(tmp_exec_db, r)
    assert is_fresh(tmp_exec_db, "binance", "BTC-USDT", ttl_s=9999.0) is True
    assert any_fresh(tmp_exec_db, ttl_s=9999.0) is True


def test_validate_blocks_inactive(monkeypatch, tmp_exec_db):
    # monkeypatch get_rules path by patching cache is_fresh/get to return inactive rules
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=False)
    upsert(tmp_exec_db, r)

    vr = validate(tmp_exec_db, "binance", "BTC-USDT", qty=1.0, notional=100.0, ttl_s=9999.0)
    assert vr.ok is False
    assert vr.code == "MARKET_INACTIVE"


def test_validate_blocks_min_notional(monkeypatch, tmp_exec_db):
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True, min_notional=50.0)
    upsert(tmp_exec_db, r)

    vr = validate(tmp_exec_db, "binance", "BTC-USDT", qty=None, notional=10.0, ttl_s=9999.0)
    assert vr.ok is False
    assert vr.code == "MIN_NOTIONAL"


def test_validate_blocks_min_qty(tmp_exec_db):
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True, min_qty=2.0)
    upsert(tmp_exec_db, r)

    vr = validate(tmp_exec_db, "binance", "BTC-USDT", qty=1.0, notional=None, ttl_s=9999.0)
    assert vr.ok is False
    assert vr.code == "MIN_QTY"


def test_validate_blocks_qty_step(tmp_exec_db):
    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True, qty_step=0.5)
    upsert(tmp_exec_db, r)

    vr = validate(tmp_exec_db, "binance", "BTC-USDT", qty=0.3, notional=None, ttl_s=9999.0)
    assert vr.ok is False
    assert vr.code == "QTY_STEP"


def test_prereq_fails_when_cache_empty(monkeypatch, tmp_path):
    # Use a temp db path by monkeypatching default_exec_db()
    db = str(tmp_path / "exec.sqlite")
    ensure_schema(db)

    from services.markets import prereq as pr
    monkeypatch.setattr(pr, "default_exec_db", lambda: db)

    out = check_market_rules_prereq(exec_db=db, ttl_s=3600.0)
    assert out.ok is False
    assert out.message == "MARKET_RULES_CACHE_STALE_OR_EMPTY"


def test_prereq_passes_when_cache_fresh(monkeypatch, tmp_path):
    db = str(tmp_path / "exec.sqlite")
    ensure_schema(db)

    r = MarketRules(venue="binance", canonical_symbol="BTC-USDT", native_symbol="BTCUSDT", active=True)
    upsert(db, r)

    out = check_market_rules_prereq(exec_db=db, ttl_s=3600.0)
    assert out.ok is True
