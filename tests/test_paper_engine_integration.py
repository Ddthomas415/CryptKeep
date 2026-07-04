from __future__ import annotations

import importlib
import json
import sqlite3
from pathlib import Path

import pytest


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


def test_paper_order_insert_ignores_duplicate_client_order_id(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    paper_store, _paper_engine = _reload_paper_modules()
    db = paper_store.PaperTradingSQLite()

    db.insert_order(
        {
            "order_id": "paper-order-1",
            "client_order_id": "dup-client-id",
            "ts": "2026-04-02T12:00:00Z",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "limit",
            "qty": 1.0,
            "limit_price": 100.0,
            "status": "new",
            "reject_reason": None,
            "strategy_id": "ema_cross",
            "meta": {"source": "first"},
        }
    )

    db.insert_order(
        {
            "order_id": "paper-order-2",
            "client_order_id": "dup-client-id",
            "ts": "2026-04-02T12:05:00Z",
            "venue": "coinbase",
            "symbol": "ETH/USD",
            "side": "sell",
            "order_type": "market",
            "qty": 2.0,
            "limit_price": 101.5,
            "status": "filled",
            "reject_reason": "should_not_replace",
            "strategy_id": "momentum",
            "meta": {"source": "second"},
        }
    )

    order = db.get_order_by_client_id("dup-client-id")
    assert order is not None
    assert order["order_id"] == "paper-order-1"
    assert order["symbol"] == "BTC/USD"
    assert order["side"] == "buy"
    assert order["status"] == "new"
    assert order["strategy_id"] == "ema_cross"
    assert order["meta"] == {"source": "first"}


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


def test_paper_engine_sell_fill_evidence_uses_net_fee_pnl(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules()

    strategy_id = "paper_pnl_evidence_test"
    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {
            "paper_trading": {
                "starting_cash_quote": 1000.0,
                "fee_bps": 10.0,
                "slippage_bps": 0.0,
                "use_ccxt_fallback": False,
                "strategy_id": strategy_id,
            }
        },
    )
    current_price = {"value": 100.0}
    monkeypatch.setattr(
        paper_engine.PaperEngine,
        "_price",
        lambda self, venue, symbol: {
            "ts_ms": 1,
            "bid": current_price["value"],
            "ask": current_price["value"],
            "last": current_price["value"],
        },
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    eng = paper_engine.PaperEngine()
    buy = eng.submit_order(
        client_order_id="paper-pnl-buy",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )
    assert buy["ok"] is True
    assert eng.evaluate_open_orders()["filled"] == 1

    current_price["value"] = 100.0
    sell = eng.submit_order(
        client_order_id="paper-pnl-sell",
        venue="coinbase",
        symbol="BTC/USD",
        side="sell",
        order_type="market",
        qty=1.0,
    )
    assert sell["ok"] is True
    sell_cycle = eng.evaluate_open_orders()
    assert sell_cycle["filled"] == 1
    assert sell_cycle["details_sample"][0]["result"]["realized_pnl_usd"] == pytest.approx(-0.2)
    assert sell_cycle["details_sample"][0]["result"]["pnl_usd_semantics"] == "net_of_fees"
    assert eng.db.get_position("BTC/USD")["avg_price"] == 0.0

    fill_files = sorted((tmp_path / "data" / "evidence" / strategy_id).glob("fill_*.jsonl"))
    assert fill_files
    fills = [
        json.loads(line)
        for path in fill_files
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sell_fills = [f for f in fills if f.get("side") == "sell"]
    assert len(sell_fills) == 1
    assert sell_fills[0]["pnl_usd"] == pytest.approx(-0.2)
    assert sell_fills[0]["pnl_usd_semantics"] == "net_of_fees"


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


def test_paper_engine_submit_blocks_when_market_quality_has_no_reference_price(monkeypatch, tmp_path):
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
        lambda venue, symbol: {"ok": True, "reason": "no_quote_data"},
    )

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-gate-mq-no-price",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out == {"ok": False, "reason": "market_quality:no_reference_price"}
    assert eng.db.get_order_by_client_id("paper-gate-mq-no-price") is None


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


def test_paper_engine_evidence_logging_prefers_strategy_preset(monkeypatch, tmp_path):
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
    monkeypatch.setattr(
        paper_engine.PaperEngine,
        "_price",
        lambda self, venue, symbol: {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0},
    )
    _allow_submit_gates(monkeypatch, paper_engine)

    import services.strategies.evidence_logger as evidence_logger

    calls: list[tuple[str, str, dict]] = []

    class FakeLogger:
        def __init__(self, strategy_id: str, log_dir: Path | None = None) -> None:
            self.strategy_id = strategy_id

        def log_order(self, **kwargs) -> None:
            calls.append(("order", self.strategy_id, dict(kwargs)))

        def log_fill(self, **kwargs) -> None:
            calls.append(("fill", self.strategy_id, dict(kwargs)))

    monkeypatch.setattr(evidence_logger, "EvidenceLogger", FakeLogger)

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-buy-preset-1",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
        strategy_id="sma_200_trend",
        meta={
            "strategy_preset": "es_daily_trend_v1",
            "selected_strategy": "sma_200_trend",
            "market_data_source": "public_ohlcv",
            "ohlcv_sample_mode": False,
            "ohlcv_timeframe": "1d",
            "ohlcv_venue": "coinbase",
            "ohlcv_symbol": "BTC/USD",
            "exit_reason": "strategy_exit:sma_200_trend:time_stop",
            "exit_stack_rule": "time_stop",
        },
    )

    assert out["ok"] is True
    assert out["order"]["meta"]["exit_reason"] == "strategy_exit:sma_200_trend:time_stop"
    assert out["order"]["meta"]["exit_stack_rule"] == "time_stop"
    assert eng.evaluate_open_orders()["filled"] == 1
    assert [(kind, strategy_id) for kind, strategy_id, _ in calls] == [
        ("order", "es_daily_trend_v1"),
        ("fill", "es_daily_trend_v1"),
    ]
    for _, _, kwargs in calls:
        assert kwargs["extra"]["market_data_source"] == "public_ohlcv"
        assert kwargs["extra"]["ohlcv_sample_mode"] is False
        assert kwargs["extra"]["ohlcv_timeframe"] == "1d"
        assert kwargs["extra"]["exit_reason"] == "strategy_exit:sma_200_trend:time_stop"
        assert kwargs["extra"]["exit_stack_rule"] == "time_stop"
