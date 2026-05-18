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


def test_paper_engine_market_buy_persists_fill_and_closes_order(monkeypatch, tmp_path):
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


def test_paper_engine_reject_does_not_persist_fill(monkeypatch, tmp_path):
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

    eng = paper_engine.PaperEngine()
    out = eng.submit_order(
        client_order_id="paper-buy-reject",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="market",
        qty=1.0,
    )

    assert out["ok"] is True
    order = eng.db.get_order_by_client_id("paper-buy-reject")
    assert order is not None
    assert order["status"] == "rejected"
    assert order["reject_reason"] == "insufficient_cash"
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

    import services.strategies.evidence_logger as evidence_logger

    calls: list[tuple[str, str]] = []

    class FakeLogger:
        def __init__(self, strategy_id: str, log_dir: Path | None = None) -> None:
            self.strategy_id = strategy_id

        def log_order(self, **kwargs) -> None:
            calls.append(("order", self.strategy_id))

        def log_fill(self, **kwargs) -> None:
            calls.append(("fill", self.strategy_id))

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
        meta={"strategy_preset": "es_daily_trend_v1", "selected_strategy": "sma_200_trend"},
    )

    assert out["ok"] is True
    assert calls == [("fill", "es_daily_trend_v1"), ("order", "es_daily_trend_v1")]
