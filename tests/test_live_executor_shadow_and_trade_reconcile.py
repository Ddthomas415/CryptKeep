from __future__ import annotations

from services.execution import live_executor as le
from services.execution.safety_gates import SafetyConfig


def test_submit_pending_live_shadow_mode_is_observe_only(monkeypatch):
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    cfg = le.LiveCfg(enabled=False, observe_only=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    out = le.submit_pending_live(cfg)
    assert out["ok"] is True
    assert out["submitted"] == 0
    assert out["observe_only"] is True
    assert "LIVE_SHADOW" in str(out["note"])


def test_reconcile_live_shadow_mode_allows_read_only_without_live_arming(monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    cfg = le.LiveCfg(
        enabled=False,
        observe_only=True,
        exchange_id="coinbase",
        exec_db=str(tmp_path / "execution.sqlite"),
        symbol="BTC/USD",
    )

    out = le.reconcile_live(cfg)
    assert out["ok"] is True
    assert out["checked"] == 0
    assert out["fills_added"] == 0
    assert out["observe_only"] is True


def test_reconcile_live_trade_level_partial_fill_is_idempotent(monkeypatch):
    monkeypatch.setenv("CBP_EXECUTION_ARMED", "YES")
    cfg = le.LiveCfg(
        enabled=True,
        exchange_id="coinbase",
        exec_db=":memory:",
        symbol="BTC/USD",
        reconcile_limit=5,
        reconcile_trades=True,
        reconcile_lookback_ms=60_000,
        reconcile_trades_limit=50,
    )

    class _FakeStore:
        def __init__(self):
            self.fills: list[dict] = []
            self.status_updates: list[tuple[str, str, str]] = []

        def list_intents(self, *, mode: str, exchange: str, symbol: str, status: str, limit: int = 200):
            if status != "submitted":
                return []
            return [{"intent_id": "intent-1", "symbol": symbol, "reason": "remote_id=ord-1 client_id=cid-1"}]

        def add_fill(self, **kwargs):
            self.fills.append(dict(kwargs))

        def set_intent_status(self, *, intent_id: str, status: str, reason: str = ""):
            self.status_updates.append((intent_id, status, reason))

        def list_fill_trade_ids(self, *, intent_id: str, limit: int = 2000):
            out: list[str] = []
            for row in self.fills:
                meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
                trade_id = str(meta.get("trade_id") or "").strip()
                if trade_id:
                    out.append(trade_id)
            return out[-int(limit) :]

    class _FakeDedupe:
        def get_by_intent(self, exchange_id: str, intent_id: str):
            return {"client_order_id": "cid-1", "remote_order_id": "ord-1"}

        def mark_terminal(self, exchange_id: str, intent_id: str, terminal_status: str):
            return None

    class _FakeClient:
        @staticmethod
        def fetch_order(*, order_id: str, symbol: str):
            return {"id": order_id, "status": "open", "filled": 0.4, "average": 100.0, "fee": {"cost": 0.01, "currency": "USD"}}

        @staticmethod
        def fetch_my_trades(*, symbol: str, since: int | None = None, limit: int | None = None):
            return [
                {
                    "id": "trade-1",
                    "order": "ord-1",
                    "timestamp": 1_700_000_000_000,
                    "amount": 0.4,
                    "price": 100.0,
                    "fee": {"cost": 0.01, "currency": "USD"},
                }
            ]

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
    fake_latency = _FakeLatency()

    monkeypatch.setattr(le, "_load_execution_safety_cfg", lambda *_, **__: SafetyConfig(enabled=True))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: fake_latency)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: _FakeDedupe())
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: _FakeClient())

    out1 = le.reconcile_live(cfg)
    assert out1["ok"] is True
    assert out1["fills_added"] == 1
    assert out1["trade_fills_added"] == 1
    assert out1["observe_only"] is False
    assert len(fake_store.fills) == 1
    assert fake_store.fills[0]["meta"]["trade_id"] == "trade-1"
    assert len(fake_latency.fill_calls) == 1

    out2 = le.reconcile_live(cfg)
    assert out2["ok"] is True
    assert out2["fills_added"] == 0
    assert out2["trade_fills_added"] == 0
    assert len(fake_store.fills) == 1
    assert len(fake_latency.fill_calls) == 1
