"""
tests/test_paper_engine_limit_and_status.py

P2 tests:
- Paper limit-order buy affordability uses limit_price for cost estimation
  (not market mid), so a limit price above cash triggers the gate.
- Paper limit-order buy passes gate when limit_price * qty fits in cash.
- Paper runner status file includes queue, reconcile, and mtm keys
  after one loop cycle.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path


def _reload_paper_modules(tmp_path: Path):
    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.paper_trading_sqlite as paper_store
    import services.execution.paper_engine as paper_engine

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(paper_store)
    importlib.reload(paper_engine)
    return paper_store, paper_engine


def _allow_submit_gates(monkeypatch, paper_engine, *, market_price: float = 100.0):
    monkeypatch.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    monkeypatch.setattr(
        paper_engine,
        "check_market_quality",
        lambda venue, symbol: {"ok": True, "reason": "ok", "price_used": market_price},
    )
    monkeypatch.setattr(paper_engine, "should_allow_order", lambda *args, **kwargs: (True, "ok"))


# ---------------------------------------------------------------------------
# Limit-order affordability: cost estimated from limit_price, not market mid
# ---------------------------------------------------------------------------

def test_paper_limit_buy_blocked_when_limit_price_exceeds_cash(monkeypatch, tmp_path):
    """
    Cash = 500. limit_price = 600, qty = 1.
    Estimated cost = 600 > 500 → gate must block.
    Market mid is irrelevant for limit-order cost estimation.
    """
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine, market_price=50.0)  # mid is cheap — must not be used

    eng = paper_engine.PaperEngine()
    eng.set_cash_quote(500.0)

    out = eng.submit_order(
        client_order_id="limit-over-cash",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=1.0,
        limit_price=600.0,
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_cash"
    assert eng.db.get_order_by_client_id("limit-over-cash") is None


def test_paper_limit_buy_allowed_when_limit_price_fits_in_cash(monkeypatch, tmp_path):
    """
    Cash = 500. limit_price = 400, qty = 1.
    Estimated cost = 400 ≤ 500 → gate must pass, order inserted as 'new'.
    """
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine, market_price=900.0)  # mid is expensive — must not be used

    eng = paper_engine.PaperEngine()
    eng.set_cash_quote(500.0)

    out = eng.submit_order(
        client_order_id="limit-fits-cash",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=1.0,
        limit_price=400.0,
    )

    assert out["ok"] is True
    order = eng.db.get_order_by_client_id("limit-fits-cash")
    assert order is not None
    assert order["status"] == "new"
    assert order["limit_price"] == 400.0


def test_paper_limit_buy_with_fees_blocks_when_borderline(monkeypatch, tmp_path):
    """
    Cash = 100. limit_price = 100, qty = 1, fee_bps = 100 (1%).
    Estimated cost = 100 * 1.0 * 1.01 = 101 > 100 → gate must block.
    """
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    _, paper_engine = _reload_paper_modules(tmp_path)
    _allow_submit_gates(monkeypatch, paper_engine)

    monkeypatch.setattr(
        paper_engine,
        "load_user_yaml",
        lambda: {"paper_trading": {"starting_cash_quote": 100.0, "fee_bps": 100.0, "slippage_bps": 0.0, "use_ccxt_fallback": False}},
    )

    eng = paper_engine.PaperEngine()
    # Cash initialized from config = 100.0

    out = eng.submit_order(
        client_order_id="limit-fee-borderline",
        venue="coinbase",
        symbol="BTC/USD",
        side="buy",
        order_type="limit",
        qty=1.0,
        limit_price=100.0,
    )

    assert out["ok"] is False
    assert out["reason"] == "insufficient_cash"


# ---------------------------------------------------------------------------
# Runner status observability: status file fields after one loop cycle
# ---------------------------------------------------------------------------

def test_paper_runner_status_file_contains_expected_keys_after_loop(monkeypatch, tmp_path):
    """
    After one complete run_forever cycle, the status file must contain:
    ok, status, queue, reconcile, intent_reconcile, mtm, venue, symbols.
    """
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.os.app_paths as app_paths
    import storage.intent_queue_sqlite as intent_queue_mod
    import storage.paper_trading_sqlite as paper_store_mod
    import storage.trade_journal_sqlite as trade_journal_mod
    import services.execution.intent_reconciler as reconciler_mod
    import services.execution.paper_runner as paper_runner

    importlib.reload(app_paths)
    importlib.reload(intent_queue_mod)
    importlib.reload(paper_store_mod)
    importlib.reload(trade_journal_mod)
    importlib.reload(reconciler_mod)
    importlib.reload(paper_runner)

    status_written: list[dict] = []

    def capture_status(obj: dict) -> None:
        status_written.append(obj)

    calls = {"n": 0}

    class FakeEngine:
        db = paper_store_mod.PaperTradingSQLite()

        def evaluate_open_orders(self) -> dict:
            return {"open_orders_seen": 0, "filled": 0, "rejected": 0}

        def mark_to_market(self, venue: str, symbol: str) -> dict:
            return {"ok": True, "cash_quote": 1000.0, "equity_quote": 1000.0, "unrealized_pnl": 0.0, "realized_pnl": 0.0, "mid": 100.0}

    def fake_consume(**_kwargs) -> dict:
        return {"queued_seen": 0, "submitted": 0, "rejected": 0, "idempotent": 0}

    def fake_reconcile(**_kwargs) -> dict:
        return {"submitted_checked": 0, "intents_updated": 0, "fills_journaled": 0, "journal_count": 0}

    def fake_sleep(_seconds: float) -> None:
        paper_runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        paper_runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(paper_runner, "PaperEngine", FakeEngine)
    monkeypatch.setattr(paper_runner, "load_user_yaml", lambda: {
        "paper_trading": {"default_venue": "coinbase", "default_symbol": "BTC/USD", "loop_interval_sec": 0.0}
    })
    monkeypatch.setattr(paper_runner, "_consume_queued_intents_once", fake_consume)
    monkeypatch.setattr(paper_runner, "reconcile_once", fake_reconcile)
    monkeypatch.setattr(paper_runner.time, "sleep", fake_sleep)
    monkeypatch.setattr(paper_runner, "_write_status", capture_status)

    paper_runner.run_forever()

    # Find the 'running' status written during the loop (not 'stopped')
    loop_statuses = [s for s in status_written if s.get("status") == "running" and "queue" in s]
    assert loop_statuses, f"No loop status found. All statuses: {status_written}"

    s = loop_statuses[-1]
    assert s["ok"] is True
    assert s["status"] == "running"
    assert "queue" in s
    assert "reconcile" in s
    assert "intent_reconcile" in s
    assert "mtm" in s
    assert "venue" in s
    assert "symbols" in s

    # reconcile sub-dict has expected shape
    rec = s["reconcile"]
    assert "open_seen" in rec
    assert "filled" in rec
    assert "rejected" in rec
