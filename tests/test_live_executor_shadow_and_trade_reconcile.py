from __future__ import annotations

import json
import sqlite3

from services.execution import live_executor as le
from services.execution.safety_gates import SafetyConfig
from storage.execution_store_sqlite import ExecutionStore


def test_submit_pending_live_shadow_mode_is_observe_only(monkeypatch):
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)
    cfg = le.LiveCfg(enabled=False, observe_only=True, exchange_id="coinbase", exec_db=":memory:", symbol="BTC/USD")

    out = le.submit_pending_live(cfg)
    assert out["ok"] is True
    assert out["submitted"] == 0
    assert out["observe_only"] is True
    assert "LIVE_SHADOW" in str(out["note"])


def test_submit_pending_live_shadow_records_would_be_fill_without_live_side_effects(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    exec_db = tmp_path / "execution.sqlite"
    monkeypatch.setenv("CBP_STATE_DIR", str(state_dir))
    monkeypatch.delenv("CBP_EXECUTION_ARMED", raising=False)

    store = ExecutionStore(path=str(exec_db))
    store.upsert_intent(
        {
            "intent_id": "intent-shadow-1",
            "ts_ms": 1_700_000_000_000,
            "mode": "live",
            "exchange": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "market",
            "qty": 0.25,
            "limit_price": None,
            "status": "pending",
            "meta": {
                "strategy_preset": "es_daily_trend_v1",
                "selected_strategy": "sma_200_trend",
            },
        }
    )

    def _unexpected_client(*_args, **_kwargs):
        raise AssertionError("shadow observe-only submit must not instantiate ExchangeClient")

    monkeypatch.setattr(le, "ExchangeClient", _unexpected_client)
    monkeypatch.setattr(
        le,
        "get_best_bid_ask_last",
        lambda venue, symbol: {"ts_ms": 1_700_000_000_001, "bid": 100.0, "ask": 100.2, "last": 100.1},
    )

    cfg = le.LiveCfg(
        enabled=False,
        observe_only=True,
        exchange_id="coinbase",
        exec_db=str(exec_db),
        symbol="BTC/USD",
        max_submit_per_tick=1,
    )

    out = le.submit_pending_live(cfg)

    assert out["ok"] is True
    assert out["submitted"] == 0
    assert out["observe_only"] is True
    assert out["shadow_pending"] == 1
    assert out["shadow_would_be_fills"] == 1
    assert out["shadow_would_be_fills_existing"] == 0
    assert out["shadow_would_be_fills_missing_quote"] == 0

    pending = store.list_intents(
        mode="live",
        exchange="coinbase",
        symbol="BTC/USD",
        status="pending",
        limit=10,
    )
    assert len(pending) == 1
    assert pending[0]["intent_id"] == "intent-shadow-1"
    with sqlite3.connect(exec_db) as conn:
        fill_count = conn.execute("select count(*) from fills").fetchone()[0]
    assert fill_count == 0

    evidence_files = sorted((state_dir / "data" / "evidence" / "es_daily_trend_v1").glob("fill_*.jsonl"))
    assert len(evidence_files) == 1
    records = [json.loads(line) for line in evidence_files[0].read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    record = records[0]
    assert record["_stage"] == "shadow"
    assert record["record_subtype"] == "shadow_would_be_fill"
    assert record["shadow_would_be_fill"] is True
    assert record["intent_id"] == "intent-shadow-1"
    assert record["order_id"] == "shadow:intent-shadow-1"
    assert record["strategy_id"] == "es_daily_trend_v1"
    assert record["selected_strategy"] == "sma_200_trend"
    assert record["side"] == "buy"
    assert record["size"] == 0.25
    assert record["order_type"] == "market"
    assert record["intended_limit_price"] is None
    assert record["bid"] == 100.0
    assert record["ask"] == 100.2
    assert record["reference_mid"] == 100.1
    assert record["quote_ts_ms"] == 1_700_000_000_001
    assert record["spread_bps"] > 0
    assert record["slippage_pct"] > 0
    assert record["fees_paid"] > 0
    assert record["market_data_source"] == "local_snapshot"
    assert record["ohlcv_sample_mode"] is False

    out2 = le.submit_pending_live(cfg)
    assert out2["shadow_would_be_fills"] == 0
    assert out2["shadow_would_be_fills_existing"] == 1
    records2 = [json.loads(line) for line in evidence_files[0].read_text(encoding="utf-8").splitlines()]
    assert len(records2) == 1


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
            return [{"intent_id": "intent-1", "symbol": symbol, "side": "buy", "reason": "remote_id=ord-1 client_id=cid-1"}]

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
                    "side": "buy",
                    "timestamp": 1_700_000_000_000,
                    "amount": 0.4,
                    "price": 100.0,
                    "fee": {"cost": 0.01, "currency": "USD"},
                    "realized_pnl_usd": -1.25,
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
    sink_fills: list[dict] = []

    monkeypatch.setattr(le, "_load_execution_safety_cfg", lambda *_, **__: SafetyConfig(enabled=True))
    monkeypatch.setattr(le, "_latency_tracker", lambda *_args, **_kwargs: fake_latency)
    monkeypatch.setattr(le, "ExecutionStore", lambda path: fake_store)
    monkeypatch.setattr(le, "OrderDedupeStore", lambda exec_db: _FakeDedupe())
    monkeypatch.setattr(le, "ExchangeClient", lambda exchange_id, sandbox=False: _FakeClient())
    monkeypatch.setattr(le, "_on_fill", lambda fill, *, exec_db=None: sink_fills.append({"fill": dict(fill), "exec_db": exec_db}) or {"ok": True})

    out1 = le.reconcile_live(cfg)
    assert out1["ok"] is True
    assert out1["fills_added"] == 1
    assert out1["trade_fills_added"] == 1
    assert out1["observe_only"] is False
    assert len(fake_store.fills) == 1
    assert fake_store.fills[0]["meta"]["trade_id"] == "trade-1"
    assert len(fake_latency.fill_calls) == 1
    assert len(sink_fills) == 1
    assert sink_fills[0]["exec_db"] == ":memory:"
    assert sink_fills[0]["fill"]["fill_id"] == "trade-1"
    assert sink_fills[0]["fill"]["fee_usd"] == 0.01
    assert sink_fills[0]["fill"]["realized_pnl_usd"] == -1.25

    out2 = le.reconcile_live(cfg)
    assert out2["ok"] is True
    assert out2["fills_added"] == 0
    assert out2["trade_fills_added"] == 0
    assert len(fake_store.fills) == 1
    assert len(fake_latency.fill_calls) == 1
    assert len(sink_fills) == 1
