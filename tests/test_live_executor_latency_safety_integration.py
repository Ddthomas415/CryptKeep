from __future__ import annotations

from services.execution import live_executor as le
from services.execution.safety_gates import SafetyConfig


def test_submit_pending_live_blocks_on_stale_market_freshness(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "YES")
    cfg = le.LiveCfg(enabled=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    monkeypatch.setattr(le, "_execution_safety_pause_open", lambda **_: (True, "OK", {}))
    monkeypatch.setattr(
        le,
        "_load_execution_safety_cfg",
        lambda *_, **__: SafetyConfig(enabled=True, require_ws_fresh_for_live=True, max_ws_recv_age_ms=1000),
    )
    monkeypatch.setattr(
        le,
        "_check_market_freshness_for_live",
        lambda *_args, **_kwargs: (False, "WS_STALE", {"recv_age_ms": 9999}),
    )

    out = le.submit_pending_live(cfg)
    assert out["ok"] is False
    assert out["submitted"] == 0
    assert out["safety_blocked"] == 1
    assert "WS_STALE" in str(out["note"])


def test_submit_pending_live_records_submit_and_ack_latency(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "YES")
    cfg = le.LiveCfg(enabled=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD", max_submit_per_tick=1)

    expected_cid = le.make_client_order_id("coinbase", "intent-1")

    class _FakeStore:
        def __init__(self):
            self.status_updates: list[tuple[str, str, str]] = []

        def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200):
            if status != "pending":
                return []
            return [
                {
                    "intent_id": "intent-1",
                    "symbol": symbol,
                    "side": "buy",
                    "order_type": "limit",
                    "qty": 0.25,
                    "limit_price": 100.0,
                    "reason": "",
                }
            ]

        def set_intent_status(self, *, intent_id: str, status: str, reason: str = "") -> None:
            self.status_updates.append((intent_id, status, reason))

    class _FakeDedupe:
        def get_by_intent(self, exchange_id: str, intent_id: str):
            return {"client_order_id": expected_cid, "remote_order_id": "ord-1"}

    class _FakePnL:
        def get_today_realized(self):
            return {"realized_pnl": 0.0, "updated_ts": "now"}

    class _FakeGateDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def killswitch_on(self) -> bool:
            return False

    class _FakeGates:
        def __init__(self, limits, db):
            self.limits = limits
            self.db = db

        def check_live(self, *, it, realized_pnl_usd: float):
            return True, "ok", {}

    class _FakeClient:
        def __init__(self):
            self.calls: list[dict] = []

        def build(self):
            class _Ex:
                @staticmethod
                def fetch_ticker(_symbol: str):
                    return {"bid": 99.0, "ask": 101.0, "last": 100.0}

            return _Ex()

        def submit_order(self, **kwargs):
            self.calls.append(dict(kwargs))
            return {"id": "ord-1", "status": "open"}

    class _FakeLatency:
        def __init__(self):
            self.submit_calls: list[dict] = []
            self.ack_calls: list[dict] = []
            self.fill_calls: list[dict] = []

        def record_submit(self, **kwargs):
            self.submit_calls.append(dict(kwargs))

        def record_ack(self, **kwargs):
            self.ack_calls.append(dict(kwargs))

        def record_fill(self, **kwargs):
            self.fill_calls.append(dict(kwargs))

    fake_store = _FakeStore()
    fake_dedupe = _FakeDedupe()
    fake_client = _FakeClient()
    fake_latency = _FakeLatency()

    monkeypatch.setattr(le, "_execution_safety_pause_open", lambda **_: (True, "OK", {}))
    monkeypatch.setattr(le, "_load_execution_safety_cfg", lambda *_, **__: SafetyConfig(enabled=True))
    monkeypatch.setattr(le, "_check_market_freshness_for_live", lambda *_args, **_kwargs: (True, "OK", {}))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: fake_latency)
    monkeypatch.setattr(le.LiveRiskLimits, "from_trading_yaml", staticmethod(lambda _path: object()))
    monkeypatch.setattr(le, "LiveGateDB", _FakeGateDB)
    monkeypatch.setattr(le, "LiveRiskGates", _FakeGates)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: fake_dedupe)
    monkeypatch.setattr(le, "PnLStoreSQLite", _FakePnL)
    monkeypatch.setattr(le, "JournalSignals", lambda exec_db: None)
    monkeypatch.setattr(le, "_check_preflight_gate", lambda *_args, **_kwargs: (True, "OK", {}))
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: fake_client)
    monkeypatch.setattr(le, "phase83_incr_trade_counter", lambda *_, **__: None)

    out = le.submit_pending_live(cfg)
    assert out["ok"] is True
    assert out["submitted"] == 1
    assert out["latency_breaches"] == 0

    assert len(fake_client.calls) == 1
    assert fake_client.calls[0]["client_id"] == expected_cid

    assert len(fake_latency.submit_calls) == 1
    assert len(fake_latency.ack_calls) == 1
    assert fake_latency.submit_calls[0]["client_order_id"] == expected_cid
    assert fake_latency.ack_calls[0]["client_order_id"] == expected_cid
    assert fake_latency.ack_calls[0]["exchange_order_id"] == "ord-1"


def test_submit_pending_live_enforces_preflight_per_intent(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "YES")
    cfg = le.LiveCfg(enabled=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD", max_submit_per_tick=2)

    class _FakeStore:
        def __init__(self):
            self.status_updates: list[tuple[str, str, str]] = []

        def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200):
            if status != "pending":
                return []
            return [
                {"intent_id": "intent-1", "symbol": symbol, "side": "buy", "order_type": "limit", "qty": 0.1, "limit_price": 100.0, "reason": ""},
                {"intent_id": "intent-2", "symbol": symbol, "side": "buy", "order_type": "limit", "qty": 0.1, "limit_price": 101.0, "reason": ""},
            ]

        def set_intent_status(self, *, intent_id: str, status: str, reason: str = "") -> None:
            self.status_updates.append((intent_id, status, reason))

    class _FakeDedupe:
        def get_by_intent(self, exchange_id: str, intent_id: str):
            return {"client_order_id": le.make_client_order_id(exchange_id, intent_id), "remote_order_id": None}

    class _FakePnL:
        def get_today_realized(self):
            return {"realized_pnl": 0.0, "updated_ts": "now"}

    class _FakeGateDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def killswitch_on(self) -> bool:
            return False

    class _FakeGates:
        def __init__(self, limits, db):
            self.limits = limits
            self.db = db

        def check_live(self, *, it, realized_pnl_usd: float):
            return True, "ok", {}

    class _NeverSubmitClient:
        def submit_order(self, **kwargs):
            raise AssertionError("submit_order should not be called when preflight blocks")

    class _FakeLatency:
        def record_submit(self, **kwargs):
            return None

        def record_ack(self, **kwargs):
            return None

        def record_fill(self, **kwargs):
            return None

    fake_store = _FakeStore()
    preflight_calls = {"n": 0}

    def _preflight_block(*_args, **_kwargs):
        preflight_calls["n"] += 1
        return False, "PREFLIGHT_FAILED", {"error": "db_writable"}

    monkeypatch.setattr(le, "_execution_safety_pause_open", lambda **_: (True, "OK", {}))
    monkeypatch.setattr(le, "_load_execution_safety_cfg", lambda *_, **__: SafetyConfig(enabled=True))
    monkeypatch.setattr(le, "_check_market_freshness_for_live", lambda *_args, **_kwargs: (True, "OK", {}))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: _FakeLatency())
    monkeypatch.setattr(le.LiveRiskLimits, "from_trading_yaml", staticmethod(lambda _path: object()))
    monkeypatch.setattr(le, "LiveGateDB", _FakeGateDB)
    monkeypatch.setattr(le, "LiveRiskGates", _FakeGates)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: _FakeDedupe())
    monkeypatch.setattr(le, "PnLStoreSQLite", _FakePnL)
    monkeypatch.setattr(le, "JournalSignals", lambda exec_db: None)
    monkeypatch.setattr(le, "_check_preflight_gate", _preflight_block)
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: _NeverSubmitClient())

    out = le.submit_pending_live(cfg)
    assert out["ok"] is True
    assert out["submitted"] == 0
    assert out["preflight_blocked"] == 2
    assert preflight_calls["n"] == 2
    assert len(fake_store.status_updates) == 2
    for _intent_id, status, reason in fake_store.status_updates:
        assert status == "pending"
        assert str(reason).startswith("preflight_gate_block:PREFLIGHT_FAILED:")


def test_submit_pending_live_latency_breach_opens_pause_and_stops_batch(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "YES")
    cfg = le.LiveCfg(enabled=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD", max_submit_per_tick=2)

    class _FakeStore:
        def __init__(self):
            self.status_updates: list[tuple[str, str, str]] = []

        def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200):
            if status != "pending":
                return []
            return [
                {"intent_id": "intent-1", "symbol": symbol, "side": "buy", "order_type": "limit", "qty": 0.2, "limit_price": 100.0, "reason": ""},
                {"intent_id": "intent-2", "symbol": symbol, "side": "buy", "order_type": "limit", "qty": 0.2, "limit_price": 100.0, "reason": ""},
            ]

        def set_intent_status(self, *, intent_id: str, status: str, reason: str = "") -> None:
            self.status_updates.append((intent_id, status, reason))

    class _FakeDedupe:
        def get_by_intent(self, exchange_id: str, intent_id: str):
            cid = le.make_client_order_id(exchange_id, intent_id)
            return {"client_order_id": cid, "remote_order_id": f"remote-{intent_id}"}

    class _FakePnL:
        def get_today_realized(self):
            return {"realized_pnl": 0.0, "updated_ts": "now"}

    class _FakeGateDB:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def killswitch_on(self) -> bool:
            return False

    class _FakeGates:
        def __init__(self, limits, db):
            self.limits = limits
            self.db = db

        def check_live(self, *, it, realized_pnl_usd: float):
            return True, "ok", {}

    class _FakeClient:
        def __init__(self):
            self.calls: list[dict] = []

        def submit_order(self, **kwargs):
            self.calls.append(dict(kwargs))
            return {"id": f"ord-{len(self.calls)}", "status": "open"}

    class _FakeLatency:
        def __init__(self):
            self.submit_calls: list[dict] = []
            self.ack_calls: list[dict] = []

        def record_submit(self, **kwargs):
            self.submit_calls.append(dict(kwargs))

        def record_ack(self, **kwargs):
            self.ack_calls.append(dict(kwargs))

        def record_fill(self, **kwargs):
            return None

    fake_store = _FakeStore()
    fake_client = _FakeClient()
    fake_latency = _FakeLatency()

    monkeypatch.setattr(le, "_execution_safety_pause_open", lambda **_: (True, "OK", {}))
    monkeypatch.setattr(
        le,
        "_load_execution_safety_cfg",
        lambda *_, **__: SafetyConfig(enabled=True, max_ack_ms=10, pause_seconds_on_breach=60),
    )
    monkeypatch.setattr(le, "_check_market_freshness_for_live", lambda *_args, **_kwargs: (True, "OK", {}))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: fake_latency)
    monkeypatch.setattr(le.LiveRiskLimits, "from_trading_yaml", staticmethod(lambda _path: object()))
    monkeypatch.setattr(le, "LiveGateDB", _FakeGateDB)
    monkeypatch.setattr(le, "LiveRiskGates", _FakeGates)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: _FakeDedupe())
    monkeypatch.setattr(le, "PnLStoreSQLite", _FakePnL)
    monkeypatch.setattr(le, "JournalSignals", lambda exec_db: None)
    monkeypatch.setattr(le, "_check_preflight_gate", lambda *_args, **_kwargs: (True, "OK", {}))
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: fake_client)
    monkeypatch.setattr(le, "phase83_incr_trade_counter", lambda *_, **__: None)

    now_values = iter([1000, 1001, 5000, 5001, 9000])
    monkeypatch.setattr(le, "_now_ms", lambda: next(now_values))
    monkeypatch.setattr(le.time, "time", lambda: 10.0)
    le._EXECUTION_SAFETY_CIRCUIT.pause_until_ts = 0.0
    le._EXECUTION_SAFETY_CIRCUIT.last_reason = ""

    out = le.submit_pending_live(cfg)
    assert out["ok"] is True
    assert out["submitted"] == 1
    assert out["latency_breaches"] == 1
    assert out["safety_blocked"] == 1
    assert len(fake_client.calls) == 1
    assert le._EXECUTION_SAFETY_CIRCUIT.pause_until_ts == 70.0
    assert str(le._EXECUTION_SAFETY_CIRCUIT.last_reason).startswith("submit_to_ack_ms:")


def test_reconcile_live_records_ack_to_fill_latency(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "YES")
    cfg = le.LiveCfg(enabled=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD", reconcile_limit=5)

    class _FakeStore:
        def __init__(self):
            self.fills: list[dict] = []
            self.status_updates: list[tuple[str, str, str]] = []

        def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200):
            if status != "submitted":
                return []
            return [{"intent_id": "intent-9", "symbol": symbol, "reason": "remote_id=ord-9 client_id=cid-9"}]

        def add_fill(self, **kwargs):
            self.fills.append(dict(kwargs))

        def set_intent_status(self, *, intent_id: str, status: str, reason: str = ""):
            self.status_updates.append((intent_id, status, reason))

    class _FakeDedupe:
        def get_by_intent(self, exchange_id: str, intent_id: str):
            return {"client_order_id": "cid-9", "remote_order_id": "ord-9"}

        def mark_terminal(self, exchange_id: str, intent_id: str, terminal_status: str):
            return None

    class _FakeClient:
        @staticmethod
        def fetch_order(*, order_id: str, symbol: str):
            return {"id": order_id, "status": "closed", "filled": 0.5, "average": 100.0, "fee": {"cost": 0.1, "currency": "USD"}}

    class _FakeLatency:
        def __init__(self):
            self.fill_calls: list[dict] = []

        def record_submit(self, **kwargs):
            return None

        def record_ack(self, **kwargs):
            return None

        def record_fill(self, **kwargs):
            self.fill_calls.append(dict(kwargs))

    fake_store = _FakeStore()
    fake_dedupe = _FakeDedupe()
    fake_latency = _FakeLatency()

    monkeypatch.setattr(le, "_load_execution_safety_cfg", lambda *_, **__: SafetyConfig(enabled=True))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: fake_latency)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: fake_dedupe)
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: _FakeClient())

    out = le.reconcile_live(cfg)
    assert out["ok"] is True
    assert out["fills_added"] == 1
    assert out["latency_fills_recorded"] == 1
    assert len(fake_latency.fill_calls) == 1
    assert fake_latency.fill_calls[0]["client_order_id"] == "cid-9"
