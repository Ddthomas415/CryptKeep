from __future__ import annotations

from decimal import Decimal

from services.markets.cache_sqlite import ensure_schema, upsert
from services.markets.math_utils import decimal_step_ok, step_ok
from services.markets.models import MarketRules
from services.markets.rules import validate


def _tmp_exec_db(tmp_path) -> str:
    db = str(tmp_path / "exec.sqlite")
    ensure_schema(db)
    return db


def test_decimal_step_ok_uses_exact_decimal_boundaries():
    assert decimal_step_ok(Decimal("0.00000003"), Decimal("0.00000001")) is True
    assert decimal_step_ok(Decimal("0.000000035"), Decimal("0.00000001")) is False

    # Public compatibility wrapper now uses Decimal semantics too.
    assert step_ok(0.003, 0.001) is True
    assert step_ok(0.0035, 0.001) is False


def test_coinbase_style_min_notional_and_qty_step_golden(tmp_path):
    db = _tmp_exec_db(tmp_path)
    upsert(
        db,
        MarketRules(
            venue="coinbase",
            canonical_symbol="BTC-USD",
            native_symbol="BTC-USD",
            active=True,
            min_notional="1.00",
            min_qty="0.00000001",
            qty_step="0.00000001",
        ),
    )

    out = validate(
        db,
        "coinbase",
        "BTC-USD",
        qty=Decimal("0.00000003"),
        notional=Decimal("1.00000000"),
        ttl_s=9999.0,
    )
    assert out.ok is True

    out = validate(
        db,
        "coinbase",
        "BTC-USD",
        qty=Decimal("0.000000035"),
        notional=Decimal("1.00000000"),
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "QTY_STEP"

    out = validate(
        db,
        "coinbase",
        "BTC-USD",
        qty=Decimal("0.00000003"),
        notional=Decimal("0.99999999"),
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "MIN_NOTIONAL"


def test_binance_style_min_qty_and_qty_step_golden(tmp_path):
    db = _tmp_exec_db(tmp_path)
    upsert(
        db,
        MarketRules(
            venue="binance",
            canonical_symbol="ETH-USDT",
            native_symbol="ETHUSDT",
            active=True,
            min_notional="10.00",
            min_qty="0.001",
            qty_step="0.001",
        ),
    )

    out = validate(
        db,
        "binance",
        "ETH-USDT",
        qty=Decimal("0.001"),
        notional=Decimal("10.00"),
        ttl_s=9999.0,
    )
    assert out.ok is True

    out = validate(
        db,
        "binance",
        "ETH-USDT",
        qty=Decimal("0.0009"),
        notional=Decimal("10.00"),
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "MIN_QTY"

    out = validate(
        db,
        "binance",
        "ETH-USDT",
        qty=Decimal("0.0015"),
        notional=Decimal("10.00"),
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "QTY_STEP"


def test_nonfinite_market_rule_values_fail_closed(tmp_path):
    db = _tmp_exec_db(tmp_path)
    upsert(
        db,
        MarketRules(
            venue="coinbase",
            canonical_symbol="BTC-USD",
            native_symbol="BTC-USD",
            active=True,
            min_notional=float("nan"),
        ),
    )

    out = validate(
        db,
        "coinbase",
        "BTC-USD",
        qty=Decimal("1"),
        notional=Decimal("1"),
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "INVALID_MARKET_RULES"
    assert out.meta == {"field": "min_notional"}

    upsert(
        db,
        MarketRules(
            venue="coinbase",
            canonical_symbol="BTC-USD",
            native_symbol="BTC-USD",
            active=True,
            qty_step=float("inf"),
        ),
    )
    out = validate(
        db,
        "coinbase",
        "BTC-USD",
        qty=Decimal("1"),
        notional=None,
        ttl_s=9999.0,
    )
    assert out.ok is False
    assert out.code == "INVALID_MARKET_RULES"
    assert out.meta == {"field": "qty_step"}
