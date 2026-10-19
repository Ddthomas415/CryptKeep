"""Live fill ingestion: finite Decimal validation, fail closed (CLOUD 2026-10-09, operator-approved live/shadow Decimal slice)."""
import math

import pytest

from services.execution import live_reconciler as lr


def test_valid_trade_values_parse_exactly():
    v = lr._validated_trade_values({"amount": "0.1", "price": "0.2", "fee": {"currency": "USD", "cost": "-0.01"},
                                    "info": {"realizedPnl": "1.5"}})
    assert v == {"qty": 0.1, "price": 0.2, "fee_usd": -0.01, "realized_pnl_usd": 1.5}  # rebate allowed


def test_non_usd_fee_is_not_counted_as_usd():
    assert lr._validated_trade_values({"amount": 1, "price": 2, "fee": {"currency": "BTC", "cost": 1}})["fee_usd"] == 0.0


@pytest.mark.parametrize("trade,reason", [
    ({"price": 1}, "trade_qty_invalid"),
    ({"amount": 0, "price": 1}, "trade_qty_nonpositive"),
    ({"amount": float("nan"), "price": 1}, "trade_qty_non_finite"),
    ({"amount": 1, "price": float("inf")}, "trade_price_non_finite"),
    ({"amount": 1, "price": -1}, "trade_price_nonpositive"),
    ({"amount": 1, "price": 1, "fee": {"currency": "USD", "cost": "NaN"}}, "trade_fee_non_finite"),
    ({"amount": 1, "price": 1, "fee": {"currency": "USDT", "cost": "abc"}}, "trade_fee_invalid"),
    ({"amount": 1, "price": 1, "pnl": "inf"}, "trade_realized_pnl_non_finite"),
    ({"amount": "1e1000", "price": 1}, "trade_qty_not_float_representable"),
    ({"amount": "1e-1000", "price": 1}, "trade_qty_not_float_representable"),
    ({"amount": 1, "price": "1e1000"}, "trade_price_not_float_representable"),
    ({"amount": 1, "price": "1e-1000"}, "trade_price_not_float_representable"),
    ({"amount": 1, "price": 1, "fee": {"currency": "USD", "cost": "1e1000"}}, "trade_fee_not_float_representable"),
    ({"amount": 1, "price": 1, "fee": {"currency": "USD"}}, "trade_fee_invalid"),
    ({"amount": 1, "price": 1, "pnl": "1e1000"}, "trade_realized_pnl_not_float_representable"),
])
def test_invalid_values_raise_instead_of_defaulting_to_zero(trade, reason):
    with pytest.raises(ValueError, match=reason):
        lr._validated_trade_values(trade)


@pytest.mark.parametrize("amount,recorded", [(float("nan"), False), ("1e1000", False),
                                            ("1e-1000", False), (1.0, True)])
def test_invalid_matched_trade_is_not_recorded_and_cursor_holds(monkeypatch, tmp_path, amount, recorded):
    cursor_updates, inserted, emitted = [], [], []

    class FakeQueue:
        state = {}

        def list_intents(self, *, limit=60, status):
            if status != "submitted":
                return []
            return [{"intent_id": "i1", "venue": "coinbase", "symbol": "BTC/USD", "exchange_order_id": "ex-1",
                     "client_order_id": "cid-1", "side": "buy", "order_type": "limit", "qty": 1.0,
                     "limit_price": 100.0, "status": "submitted", "updated_ts": "2026-01-01T00:00:00+00:00"}]

        def update_status(self, *a, **k):
            return True

        def get_state(self, key):
            return self.state.get(key, "0")

        def set_state(self, key, value):
            cursor_updates.append((key, value))

    class FakeTrading:
        def upsert_order(self, row):
            return None

        def insert_fill(self, row):
            inserted.append(row)

    class FakeAdapter:
        def __init__(self, venue, sandbox=False):
            pass

        def fetch_order(self, symbol, exchange_order_id):
            return {"id": exchange_order_id, "status": "open"}

        def fetch_my_trades(self, symbol, since_ms=None, limit=200):
            return [{"id": "t-bad", "order": "ex-1", "clientOrderId": "cid-1", "timestamp": 5000,
                     "datetime": "2026-01-01T00:00:05Z", "side": "buy", "amount": amount, "price": 123.0}]

        def close(self):
            return None

    stop_file = tmp_path / "live_reconciler.stop"
    for name, value in {"STOP_FILE": stop_file, "FLAGS": tmp_path, "LOCKS": tmp_path,
                        "STATUS_FILE": tmp_path / "s.json", "LOCK_FILE": tmp_path / "l.lock"}.items():
        monkeypatch.setattr(lr, name, value)
    monkeypatch.setattr(lr, "ensure_dirs", lambda: None)
    monkeypatch.setattr(lr, "_acquire_lock", lambda: True)
    monkeypatch.setattr(lr, "_release_lock", lambda: None)
    monkeypatch.setattr(lr, "_write_status", lambda obj: None)
    monkeypatch.setattr(lr, "get_system_guard_state", lambda **_: {"state": "RUNNING"})
    monkeypatch.setattr(lr, "live_enabled_and_armed", lambda: (True, "armed"))
    monkeypatch.setattr(lr, "_live_sandbox_enabled", lambda: True)
    monkeypatch.setattr(lr, "LiveIntentQueueSQLite", lambda: FakeQueue())
    monkeypatch.setattr(lr, "LiveTradingSQLite", lambda: FakeTrading())
    monkeypatch.setattr(lr, "LiveExchangeAdapter", FakeAdapter)
    monkeypatch.setattr(lr, "_emit_canonical_fill", lambda **kw: emitted.append(kw) or True)
    monkeypatch.setattr(lr.time, "sleep", lambda _s: stop_file.write_text("stop\n", encoding="utf-8"))
    lr.run_forever()
    if recorded:
        assert len(inserted) == 1 and inserted[0]["qty"] == 1.0 and len(emitted) == 1
    else:
        assert inserted == [] and emitted == [] and cursor_updates == []
