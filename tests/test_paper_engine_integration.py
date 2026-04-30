from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path


def _reload_paper_modules():
    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.paper_trading_sqlite as paper_store
    import services.execution.paper_engine as paper_engine

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(paper_store)
    importlib.reload(paper_engine)
    return paper_store, paper_engine


def _allow_submit_gates(monkeypatch, paper_engine):
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        paper_engine,
        "check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 100.0},
    )
    monkeypatch.setattr(paper_engine, "should_allow_order", lambda *args, **kwargs: (True, "ok"))


def test_paper_engine_market_buy_requires_explicit_fill_evaluation(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(
        paper_engine.PaperEngine,
        "_price",
        lambda self, venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0},
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-buy-1",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=2.0,
    )

    assert out["ok"] is True
    order = eng.db.get_order_by_client_id("paper-buy-1")
    assert order is not None
    assert order["status"] == "new"

    fills = eng.db.list_fills(limit=10)
    assert fills == []

    rec = eng.evaluate_open_orders()
    assert rec["open_orders_seen"] == 1
    assert rec["filled"] == 1

    order = eng.db.get_order_by_client_id("paper-buy-1")
    assert order is not None
    assert order["status"] == "filled"

    fills = eng.db.list_fills(limit=10)
    assert len(fills) == 1
    assert fills[0]["order_id"] == order["order_id"]

    pos = eng.db.get_position("BTC/USD")
    assert pos is not None
    assert pos["qty"] == 2.0
    assert pos["avg_price"] == 100.0
    assert eng.cash_quote() == 800.0

    # The order should not be re-filled once it has transitioned out of `new`.
    rec = eng.evaluate_open_orders()
    assert rec["open_orders_seen"] == 0
    assert rec["filled"] == 0

    mtm = eng.mark_to_market("coinbase", "BTC/USD")
    assert mtm["equity_quote"] == 1000.0

    con = sqlite3.connect(str(paper_store.DB_PATH))
    try:
        row = con.execute("SELECT COUNT(*) FROM paper_equity").fetchone()
    finally:
        con.close()
    assert row is not None and row[0] == 1


def test_paper_engine_submit_blocks_when_cash_is_insufficient(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 50.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(
        paper_engine.PaperEngine,
        "_price",
        lambda self, venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0},
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-buy-reject",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "insufficient_cash"}
    order = eng.db.get_order_by_client_id("paper-buy-reject")
    assert order is None
    assert eng.db.list_fills(limit=10) == []
    assert eng.cash_quote() == 50.0


def test_paper_engine_submit_blocks_when_position_is_insufficient(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-sell-reject",
        venue="coinbase",
        symbol="BTC/USD",
        side="sell",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "insufficient_position"}
    assert eng.db.get_order_by_client_id("paper-sell-reject") is None
    assert eng.db.list_fills(limit=10) == []


def test_paper_engine_fill_is_idempotent_for_stale_order_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine(clock=lambda: "2026-04-29T12:00:00+00:00")
    out = eng.submit_order(
        client_order_id="paper-buy-idem",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=2.0,
    )

    order = dict(out["order"] or {})
    first = eng._apply_fill(order, 100.0, 2.0)
    second = eng._apply_fill(order, 100.0, 2.0)

    assert first["ok"] is True
    assert first["idempotent"] is False
    assert second["ok"] is True
    assert second["idempotent"] is True

    fills = eng.db.list_fills(limit=10)
    assert len(fills) == 1
    assert eng.cash_quote() == 800.0
    pos = eng.db.get_position("BTC/USD")
    assert pos is not None
    assert pos["qty"] == 2.0


def test_paper_engine_fill_rolls_back_on_storage_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine(clock=lambda: "2026-04-29T12:00:00+00:00")
    out = eng.submit_order(
        client_order_id="paper-buy-rollback",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=2.0,
    )
    order = dict(out["order"] or {})

    def broken_insert(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(eng.db, "_insert_fill_conn", broken_insert)

    try:
        eng._apply_fill(order, 100.0, 2.0)
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("expected fill write failure")

    persisted_order = eng.db.get_order_by_client_id("paper-buy-rollback")
    assert persisted_order is not None
    assert persisted_order["status"] == "new"
    assert eng.db.list_fills(limit=10) == []
    assert eng.db.get_position("BTC/USD") is None
    assert eng.cash_quote() == 1000.0
    assert eng.realized_pnl() == 0.0


def test_paper_engine_submit_blocks_on_stale_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (False, "snapshot_missing"))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("market quality should not run when snapshot is stale")

    monkeypatch.setattr(paper_engine, "check_market_quality", should_not_run)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-gate-stale",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "staleness:snapshot_missing"}
    assert eng.db.get_order_by_client_id("paper-gate-stale") is None


def test_paper_engine_submit_blocks_on_market_quality(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(paper_engine, "check_market_quality", lambda venue, symbol: {"ok": False, "reason": "stale_tick"})

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-gate-mq",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "market_quality:stale_tick"}
    assert eng.db.get_order_by_client_id("paper-gate-mq") is None


def test_paper_engine_submit_blocks_on_master_read_only(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (True, {"read_only_mode": True}))

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("market quality should not run when read-only mode is enabled")

    monkeypatch.setattr(paper_engine, "check_market_quality", should_not_run)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-gate-read-only",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "master_read_only"}
    assert eng.db.get_order_by_client_id("paper-gate-read-only") is None


def test_paper_engine_submit_blocks_on_deterministic_safety_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 0.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
            }
        },
    )
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        paper_engine,
        "check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": 50.0},
    )

    class _Store:
        def get_today_metrics(self):
            return {"trades": 0, "approx_realized_pnl": 0.0}

    class _Gates:
        min_order_notional = 100.0
        max_trades_per_day = 0
        max_daily_loss = 0.0
        prefer_journal_pnl = False

    monkeypatch.setattr(paper_engine, "load_gates", lambda: _Gates())
    monkeypatch.setattr(paper_engine, "ExecutionGuardStoreSQLite", lambda: _Store())

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-gate-safety",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "safety:min_order_notional"}
    assert eng.db.get_order_by_client_id("paper-gate-safety") is None
