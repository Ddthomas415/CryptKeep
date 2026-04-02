from __future__ import annotations

import importlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _reload_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_remaining_compat_imports(monkeypatch, tmp_path):
    _reload_paths(monkeypatch, tmp_path)
    modules = [
        "services.execution.kill_switch",
        "services.feature_gate",
        "services.health.feed_health",
        "services.diagnostics.live_start_gate",
        "services.learning.model_registry",
        "storage.market_store_sqlite",
        "storage.portfolio_store_sqlite",
        "storage.reconciliation_store_sqlite",
        "storage.repair_runbook_store_sqlite",
        "services.diagnostics.ui_live_gate",
        "services.live_router.router",
        "services.reconciliation.exchange_reconciler",
        "services.data.unified_view",
        "services.data.multi_exchange_collector",
    ]
    for name in modules:
        mod = importlib.import_module(name)
        assert mod is not None


def test_kill_switch_wrapper(monkeypatch, tmp_path):
    _reload_paths(monkeypatch, tmp_path)
    import services.admin.kill_switch as admin_kill
    import services.execution.kill_switch as exec_kill

    importlib.reload(admin_kill)
    importlib.reload(exec_kill)

    out = exec_kill.set_kill_switch(True, reason="test")
    assert out["ok"] is True
    assert exec_kill.is_kill_switch_on() is True


def test_feed_health_and_ws_gate(tmp_path):
    events_db = tmp_path / "events.sqlite"
    now_iso = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(str(events_db))
    con.execute(
        "CREATE TABLE events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, venue TEXT NOT NULL, symbol TEXT NOT NULL, symbol_norm TEXT NOT NULL, event_type TEXT NOT NULL, event_key TEXT, payload BLOB NOT NULL)"
    )
    con.execute(
        "INSERT INTO events(ts, venue, symbol, symbol_norm, event_type, event_key, payload) VALUES(?,?,?,?,?,?,?)",
        (now_iso, "coinbase", "BTC-USD", "BTC-USD", "trade", None, b"{}"),
    )
    con.commit()
    con.close()

    from services.health.feed_health import compute_feed_health

    rows = compute_feed_health(db_path=str(events_db), warn_age_sec=999999, block_age_sec=999999, window_sec=60)
    assert len(rows) == 1
    assert rows[0].venue == "coinbase"
    assert rows[0].symbol == "BTC-USD"
    assert rows[0].status == "OK"

    from services.diagnostics.live_start_gate import check_ws_gate

    out = check_ws_gate({"circuit_breaker": {"latency_db_path": str(tmp_path / "missing.sqlite")}})
    assert out.ok is True
    assert out.status in ("WARN", "OK")


def test_feature_gate_proba(monkeypatch):
    import services.feature_gate as fg

    monkeypatch.setenv("CBP_FUSED_PROBA", "0.8")
    buy = fg.proba_gate(scope="x", side="buy", use_fused=True, buy_th=0.7, sell_th=0.3, strict=True)
    sell = fg.proba_gate(scope="x", side="sell", use_fused=True, buy_th=0.7, sell_th=0.3, strict=True)
    assert buy.ok is True
    assert sell.ok is False


def test_model_registry_and_storage_contracts(monkeypatch, tmp_path):
    app_paths = _reload_paths(monkeypatch, tmp_path)
    models_root = Path(app_paths.data_dir()) / "models"
    (models_root / "model-a").mkdir(parents=True, exist_ok=True)
    (models_root / "model-a" / "model.json").write_text('{"name":"Model A"}\n', encoding="utf-8")
    (models_root / "model-b").mkdir(parents=True, exist_ok=True)

    from services.learning.model_registry import ModelRegistry, RegistryCfg

    reg = ModelRegistry(RegistryCfg(models_root=str(models_root)))
    listed = reg.list()
    assert len(listed) >= 2

    from storage.market_store_sqlite import MarketStore
    from storage.portfolio_store_sqlite import SQLitePortfolioStore
    from storage.reconciliation_store_sqlite import SQLiteReconciliationStore
    from storage.repair_runbook_store_sqlite import SQLiteRepairRunbookStore

    market = MarketStore(path=tmp_path / "market.sqlite")
    market.upsert_ticker(ts_ms=1, exchange="coinbase", symbol="BTC-USD", bid=99.0, ask=101.0, last=100.0)
    ticks = market.last_tickers(exchange="coinbase", symbol="BTC-USD", limit=1)
    assert ticks[0]["last"] == 100.0

    portfolio = SQLitePortfolioStore(path=tmp_path / "portfolio.sqlite")
    portfolio.upsert_cash(exchange="coinbase", cash=123.45)
    portfolio.upsert_position(exchange="coinbase", symbol="BTC-USD", qty=0.5)
    assert portfolio.get_cash("coinbase")["cash"] == 123.45
    assert len(portfolio.list_positions(exchange="coinbase")) == 1

    recon = SQLiteReconciliationStore(path=tmp_path / "recon.sqlite")
    recon.insert_balance_snapshot(1, "coinbase", "USD", {"cash": 1})
    recon.insert_drift_report(2, "coinbase", "OK", "ok", {"x": 1})
    assert len(recon.list_drift_reports("coinbase")) == 1

    runbook = SQLiteRepairRunbookStore(path=tmp_path / "runbooks.sqlite")
    runbook.create_plan_sync(
        plan_id="p1",
        exchange="coinbase",
        plan_hash="h1",
        summary={"note": "x"},
        actions=[{"type": "SYNC_CASH"}],
        meta={},
    )
    plan = runbook.get_plan_sync("p1")
    events = runbook.list_events_sync("p1")
    assert plan["plan_id"] == "p1"
    assert len(events) >= 1
