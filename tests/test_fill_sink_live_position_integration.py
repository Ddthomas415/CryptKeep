import sqlite3

import pytest

from services.journal.fill_sink import CanonicalFillSink
from services.risk.risk_daily import snapshot


def test_fill_sink_computes_spot_pnl_when_exchange_pnl_missing(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    sink.on_fill({
        "venue": "coinbase",
        "fill_id": "buy-1",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 0.01,
        "price": 60000.0,
        "ts": "2026-04-30T10:00:00Z",
        "fee_usd": 0.0,
    })

    sink.on_fill({
        "venue": "coinbase",
        "fill_id": "sell-1",
        "symbol": "BTC/USD",
        "side": "sell",
        "qty": 0.01,
        "price": 58000.0,
        "ts": "2026-04-30T11:00:00Z",
        "fee_usd": 0.0,
    })

    snap = snapshot(exec_db=db)
    assert float(snap.get("realized_pnl") or 0.0) == pytest.approx(-20.0)


def test_fill_sink_blocks_on_sell_without_position_instead_of_zero_pnl(tmp_path):
    from services.os.app_paths import data_dir

    flag = data_dir() / "risk_sink_failed.flag"
    flag.unlink(missing_ok=True)

    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    sink.on_fill({
        "venue": "coinbase",
        "fill_id": "sell-without-position",
        "symbol": "BTC/USD",
        "side": "sell",
        "qty": 0.01,
        "price": 58000.0,
        "ts": "2026-04-30T11:00:00Z",
        "fee_usd": 0.0,
    })

    assert flag.exists()
    flag.unlink(missing_ok=True)

    snap = snapshot(exec_db=db)
    assert float(snap.get("realized_pnl") or 0.0) == pytest.approx(0.0)

def test_on_fill_returns_ok_true_for_success(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    r1 = sink.on_fill({
        "venue": "coinbase",
        "fill_id": "return-buy",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 0.01,
        "price": 60000.0,
        "ts": "2026-04-30T10:00:00Z",
        "fee_usd": 0.0,
    })

    assert isinstance(r1, dict)
    assert r1.get("ok") is True


def test_on_fill_returns_ok_false_for_missing_fields(tmp_path):
    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    result = sink.on_fill({
        "venue": "coinbase",
        "fill_id": "missing-symbol",
        "side": "buy",
        "qty": 0.01,
        "price": 60000.0,
    })

    assert isinstance(result, dict)
    assert result.get("ok") is False
    assert "record_failed" in str(result.get("reason"))


def test_on_fill_returns_ok_false_for_sell_without_position(tmp_path):
    from services.os.app_paths import data_dir
    flag = data_dir() / "risk_sink_failed.flag"
    flag.unlink(missing_ok=True)

    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    result = sink.on_fill({
        "venue": "coinbase",
        "fill_id": "return-sell-no-position",
        "symbol": "BTC/USD",
        "side": "sell",
        "qty": 0.01,
        "price": 58000.0,
        "ts": "2026-04-30T11:00:00Z",
        "fee_usd": 0.0,
    })

    assert isinstance(result, dict)
    assert result.get("ok") is False
    assert "position_store" in str(result.get("reason"))
    assert flag.exists()
    flag.unlink(missing_ok=True)


def test_on_fill_returns_ok_false_for_risk_daily_failure(tmp_path, monkeypatch):
    import sqlite3
    import services.journal.fill_sink as fs
    from services.os.app_paths import data_dir

    flag = data_dir() / "risk_sink_failed.flag"
    flag.unlink(missing_ok=True)

    db = str(tmp_path / "execution.sqlite")
    sink = CanonicalFillSink(exec_db=db)

    sink.on_fill({
        "venue": "coinbase",
        "fill_id": "risk-return-buy",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 0.01,
        "price": 60000.0,
        "ts": "2026-04-30T10:00:00Z",
        "fee_usd": 0.0,
    })

    def fail_apply(self, **kw):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(fs.RiskDailyDB, "apply_fill_once", fail_apply)

    result = sink.on_fill({
        "venue": "coinbase",
        "fill_id": "risk-return-sell",
        "symbol": "BTC/USD",
        "side": "sell",
        "qty": 0.01,
        "price": 58000.0,
        "ts": "2026-04-30T11:00:00Z",
        "fee_usd": 0.0,
    })

    assert isinstance(result, dict)
    assert result.get("ok") is False
    assert "risk_daily_apply_failed" in str(result.get("reason"))
    assert flag.exists()
    flag.unlink(missing_ok=True)
