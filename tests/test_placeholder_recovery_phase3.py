from __future__ import annotations

import importlib
from pathlib import Path


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_trade_history_roundtrip(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.trade_history_sqlite as trade_history_sqlite

    importlib.reload(trade_history_sqlite)
    db = trade_history_sqlite.TradeHistorySQLite()
    db.upsert_trade(
        {
            "trade_id": "t-1",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "qty": 1.0,
            "price": 100.0,
            "exchange_order_id": "o-1",
        }
    )
    rows = db.recent(limit=10)
    assert rows and rows[0]["trade_id"] == "t-1"
    by_order = db.for_order("o-1")
    assert len(by_order) == 1


def test_ws_status_and_staleness(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.ws_status_sqlite as ws_status_sqlite

    importlib.reload(ws_status_sqlite)
    db = ws_status_sqlite.WSStatusSQLite()
    db.upsert_status(exchange="coinbase", symbol="BTC/USD", status="ok", recv_ts_ms=1000, lag_ms=50.0)
    row = db.get_status(exchange="coinbase", symbol="BTC/USD")
    assert row is not None and row["status"] == "ok"
    stale = db.stale_symbols(max_recv_age_ms=100, now_ms=1200)
    assert stale and stale[0]["symbol"] == "BTC/USD"


def test_latency_metrics_p95(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.latency_metrics_sqlite as latency_metrics_sqlite

    importlib.reload(latency_metrics_sqlite)
    db = latency_metrics_sqlite.LatencyMetricsSQLite()
    for i in (10, 20, 40, 80, 160):
        db.log_latency(ts_ms=i, category="execution", name="submit_to_ack_ms", value_ms=float(i))
    p = db.rolling_p95(category="execution", name="submit_to_ack_ms", window_n=10)
    assert p["count"] == 5
    assert p["p95_ms"] == 160.0


def test_execution_audit_load_wrappers(monkeypatch):
    import storage.execution_audit_load as execution_audit_load

    importlib.reload(execution_audit_load)
    monkeypatch.setattr(execution_audit_load, "list_orders", lambda **_: [{"id": 1}])
    monkeypatch.setattr(execution_audit_load, "list_fills", lambda **_: [{"id": 2}])
    monkeypatch.setattr(execution_audit_load, "list_statuses", lambda: ["OPEN", "FILLED"])

    out = execution_audit_load.load_all()
    assert out["ok"] is True
    assert out["orders_count"] == 1
    assert out["fills_count"] == 1
    assert out["statuses"] == ["OPEN", "FILLED"]


def test_paper_state_snapshot(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.paper.paper_state as paper_state

    importlib.reload(paper_state)
    s = paper_state.PaperState()
    s.set_cash_quote(123.45)
    s.set_realized_pnl(-4.0)
    snap = s.snapshot(limit=5)
    assert snap["ok"] is True
    assert snap["cash_quote"] == 123.45
    assert snap["realized_pnl"] == -4.0


def test_paper_broker_uses_engine_contract():
    import services.paper.paper_broker as paper_broker

    class DummyEngine:
        def submit_order(self, **kwargs):
            return {"ok": True, "kind": "submit", "kwargs": kwargs}

        def cancel_order(self, client_order_id):
            return {"ok": True, "kind": "cancel", "client_order_id": client_order_id}

        def evaluate_open_orders(self):
            return {"ok": True, "kind": "eval"}

        def mark_to_market(self, venue, symbol):
            return {"ok": True, "kind": "mtm", "venue": venue, "symbol": symbol}

    b = paper_broker.PaperBroker(engine=DummyEngine())
    req = paper_broker.PaperOrder(venue="paper", symbol="BTC/USD", side="buy", order_type="market", qty=0.1)
    sub = b.submit(req)
    assert sub["ok"] is True and sub["kind"] == "submit"
    assert b.cancel("cid")["kind"] == "cancel"
    assert b.evaluate()["kind"] == "eval"
    assert b.mtm("paper", "BTC/USD")["kind"] == "mtm"


def test_position_sizing_and_exit_controls():
    from services.risk import exit_controls, position_sizing

    vol = position_sizing.estimate_volatility([100, 102, 99, 101, 103])
    assert vol >= 0
    qty = position_sizing.size_from_stop(risk_budget_usd=50, entry_price=100, stop_price=95, qty_step=0.01)
    assert qty > 0
    qty2 = position_sizing.size_by_volatility(equity_usd=1000, risk_pct=0.01, price=100, volatility=max(vol, 0.01))
    assert qty2 > 0

    hold = exit_controls.evaluate_exit_controls(entry_price=100, current_price=101, qty=1.0, stop_loss_pct=0.05, take_profit_pct=0.05)
    assert hold["action"] == "hold"
    exit_tp = exit_controls.evaluate_exit_controls(entry_price=100, current_price=106, qty=1.0, take_profit_pct=0.05)
    assert exit_tp["action"] == "exit"


def test_signal_router_batch(monkeypatch):
    import services.trading.signal_router as signal_router

    importlib.reload(signal_router)
    monkeypatch.setattr(signal_router, "route_signal_to_paper_intent", lambda sig: {"ok": bool(sig.get("accept"))})
    out = signal_router.route_batch([{"accept": True}, {"accept": False}], mode="paper")
    assert out["ok"] is True
    assert out["accepted"] == 1
    assert out["rejected"] == 1


def test_repair_reset_and_safety_policy(monkeypatch, tmp_path):
    app_paths = _reload_state_modules(monkeypatch, tmp_path)
    import services.admin.repair_reset as repair_reset
    import services.admin.safety_policy as safety_policy

    importlib.reload(repair_reset)
    importlib.reload(safety_policy)

    flags = app_paths.runtime_dir() / "flags"
    snaps = app_paths.runtime_dir() / "snapshots"
    flags.mkdir(parents=True, exist_ok=True)
    snaps.mkdir(parents=True, exist_ok=True)
    (flags / "x.stop").write_text("1\n", encoding="utf-8")
    (snaps / "a.json").write_text("{}", encoding="utf-8")

    out = repair_reset.reset_runtime_state(dry_run=False)
    assert out["ok"] is True
    assert out["removed"] >= 2

    policy = safety_policy.read_policy()
    ok, errors = safety_policy.validate_policy(policy)
    assert ok is True
    assert errors == []
