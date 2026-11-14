"""Synthetic native metadata, real cache/validator/rounding; never exchange I/O."""
import importlib.util
import os
from pathlib import Path
import socket

import pytest

from tests.test_refresh_paper_market_rules import fake_coinbase

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **kw: pytest.fail("network forbidden"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **kw: pytest.fail("network forbidden"))


def subject():
    path = os.environ.get("CBP_COINBASE_PRECISION_SOURCE")
    if path:
        spec = importlib.util.spec_from_file_location("_coinbase_precision_before", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.fetch_rules
    from services.markets.fetch_coinbase_ccxt import fetch_rules
    return fetch_rules


@pytest.mark.parametrize("tick", [1, 2])
@pytest.mark.parametrize("option", ["default", False, True])
def test_whole_unit_ticks_are_not_decimal_counts(monkeypatch, tick, option):
    fake_coinbase(monkeypatch, amount=tick, price=tick, raw_amount=str(tick), raw_price=str(tick))
    kwargs = {} if option == "default" else {"strict_precision": option}
    result = subject()("BTC-USD", **kwargs)
    assert result.active and result.qty_step == tick and result.price_tick == tick


@pytest.mark.parametrize("option", ["default", False, True])
@pytest.mark.parametrize("bad", ["mode", "amount_mismatch", "raw_missing", "native_id", "raw_id", "nan", "underflow", "unrepresentable"])
def test_all_call_styles_refuse_unverified_metadata(monkeypatch, option, bad):
    changes = {"mode": {"mode": 2}, "amount_mismatch": {"raw_amount": "2"},
               "raw_missing": {"raw_amount": None}, "nan": {"amount": float("nan")},
               "underflow": {"amount": "1e-1000", "raw_amount": "1e-1000"},
               "unrepresentable": {"raw_amount": "1.00000000000000001"}}
    market = fake_coinbase(monkeypatch, **changes.get(bad, {}))
    if bad == "native_id":
        market["id"] = "ETH-USD"
    elif bad == "raw_id":
        market["info"]["product_id"] = "ETH-USD"
    kwargs = {} if option == "default" else {"strict_precision": option}
    assert subject()("BTC-USD", **kwargs).active is False


@pytest.mark.parametrize("option", [None, 0, 1, "false"])
def test_invalid_compatibility_flag_never_disables_checks(monkeypatch, option):
    fake_coinbase(monkeypatch)
    assert subject()("BTC-USD", strict_precision=option).active is False


@pytest.mark.parametrize("tick", [1, 2, .01])
def test_default_provider_cache_validator_and_quantization_agree(tmp_path, monkeypatch, tick):
    from services.markets.rules import fetch_and_cache, validate
    from services.markets.quantize import quantize_amount, quantize_price
    from services.markets.cache_sqlite import get
    market = fake_coinbase(monkeypatch, amount=tick, price=tick, raw_amount=str(tick), raw_price=str(tick))
    market["limits"]["amount"]["min"] = tick
    db = str(tmp_path / "public-metadata.sqlite")
    result = fetch_and_cache(db, "coinbase", "BTC-USD")
    assert result.active and result.qty_step == tick and result.price_tick == tick
    assert get(db, "coinbase", "BTC-USD") == result
    amount = tick * 2.5
    rounded = quantize_amount(amount, result.qty_step)
    assert rounded == tick * 2 and rounded <= amount
    assert quantize_price(amount, result.price_tick, "buy") <= amount
    assert quantize_price(amount, result.price_tick, "sell") >= amount
    assert validate(db, "coinbase", "BTC-USD", qty=tick * 2, notional=100, order_type="market").ok
    assert validate(db, "coinbase", "BTC-USD", qty=tick * 2.5, notional=100, order_type="market").code == "QTY_STEP"


def test_coinbase_adv_retains_existing_canonical_cache_namespace(tmp_path, monkeypatch):
    from services.markets.rules import fetch_and_cache
    from services.markets.cache_sqlite import get
    fake_coinbase(monkeypatch)
    db = str(tmp_path / "public-metadata.sqlite")
    result = fetch_and_cache(db, "coinbase_adv", "BTC-USD")
    assert result.venue == "coinbase" and result.qty_step == 1
    assert get(db, "coinbase", "BTC-USD") == result
    assert get(db, "coinbase_adv", "BTC-USD") is None  # not an alias-cache migration


def test_raw_product_id_alias_and_price_precedence(monkeypatch):
    market = fake_coinbase(monkeypatch)
    market["info"].pop("product_id")
    market["info"].update(id="BTC-USD", price_increment=".01", quote_increment="1")
    result = subject()("BTC-USD")
    assert result.active and result.meta["coinbase_product"]["product_id"] == "BTC-USD"
    assert result.price_tick == .01


def test_source_repair_does_not_pretend_to_migrate_existing_cache(tmp_path, monkeypatch):
    from dataclasses import replace
    from services.markets.rules import fetch_and_cache, get_rules
    from services.markets.cache_sqlite import upsert, get
    from tests.test_paper_cash_entry import rules
    fake_coinbase(monkeypatch)
    db = str(tmp_path / "historical-cache.sqlite")
    old = replace(rules(), qty_step=.1)
    other = rules("ETH/USD")
    upsert(db, old)
    upsert(db, other)
    assert get_rules(db, "coinbase", "BTC-USD", refresh_if_stale=False) == old
    corrected = fetch_and_cache(db, "coinbase", "BTC-USD")  # synthetic public provider only
    assert corrected.qty_step == 1
    assert get(db, "coinbase", "ETH-USD") == other
