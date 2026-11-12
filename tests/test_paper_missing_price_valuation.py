import ast
import json
import os
from pathlib import Path

import pytest

from tests.test_tick_reader_exact_symbol import engine, snapshot


@pytest.fixture
def valuation(engine, monkeypatch):
    if os.getenv("CBP_VALUATION_BEFORE_ROOT"):
        import services.execution.paper_engine as module
        path = Path(os.environ["CBP_VALUATION_BEFORE_ROOT"]) / "services/execution/paper_engine.py"
        tree = ast.parse(path.read_text())
        cls = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "PaperEngine")
        method = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "mark_to_market")
        namespace = {}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), module.__dict__, namespace)
        monkeypatch.setattr(module.PaperEngine, "mark_to_market", namespace[method.name])
    return engine


def finances(eng):
    return {"cash": eng.db.get_state("cash_quote"), "realized": eng.db.get_state("realized_pnl"),
            "positions": eng.db.list_positions(), "orders": eng.db.list_orders(), "fills": eng.db.list_fills()}


@pytest.mark.parametrize("quote", [None, {}, {"last": None}, {"last": 0}, {"last": -1},
    {"last": float("nan")}, {"last": float("inf")}, {"last": "invalid"}, {"last": True},
    {"bid": 0, "ask": 2}, {"bid": 3, "ask": 2}, {"bid": float("nan"), "ask": 2}])
def test_held_unknown_mark_never_writes_cash_only_equity(valuation, monkeypatch, quote):
    eng = valuation
    eng.db.upsert_position("ADA/USD", 2, 10, 0)
    eng.db.insert_equity("historical", 1000, 1022, 2, 0)
    before, equity = finances(eng), eng.db.list_equity()
    monkeypatch.setattr(eng, "_price", lambda *a: quote)
    result = eng.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] is False
    assert result["equity_quote"] is None and result["unrealized_pnl"] is None
    assert result["valuation_status"] == "incomplete" and result["equity_recorded"] is False
    assert result["cash_quote"] == 1000 and result["realized_pnl"] == 0
    assert finances(eng) == before and eng.db.list_equity() == equity
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("quote", [None, {"last": 0}, {"last": float("nan")}])
def test_flat_cash_only_mark_is_legitimate_without_quote(valuation, monkeypatch, quote):
    monkeypatch.setattr(valuation, "_price", lambda *a: quote)
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] and result["equity_recorded"]
    assert result["valuation_status"] == "cash_only"
    assert result["equity_quote"] == 1000 and result["unrealized_pnl"] == 0
    assert len(valuation.db.list_equity()) == 1


@pytest.mark.parametrize("quote", [{"bid": 10, "ask": 12, "last": 999}, {"last": 11}, {"bid": 10, "last": 11}])
def test_valid_mark_preserves_existing_numeric_results(valuation, monkeypatch, quote):
    valuation.db.upsert_position("ADA/USD", 2, 10, 0)
    before = finances(valuation)
    monkeypatch.setattr(valuation, "_price", lambda *a: quote)
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] and result["equity_recorded"]
    assert result["mid"] == 11 and result["equity_quote"] == 1022 and result["unrealized_pnl"] == 2
    assert finances(valuation) == before


def test_quote_returning_recovers_without_rewriting_history(valuation, monkeypatch):
    valuation.db.upsert_position("ADA/USD", 2, 10, 0)
    quotes = iter([None, {"last": 11}])
    monkeypatch.setattr(valuation, "_price", lambda *a: next(quotes))
    assert not valuation.mark_to_market("coinbase", "ADA/USD")["ok"]
    assert valuation.db.list_equity() == []
    assert valuation.mark_to_market("coinbase", "ADA/USD")["ok"]
    assert len(valuation.db.list_equity()) == 1


@pytest.mark.parametrize("key,value", [("cash_quote", "NaN"), ("cash_quote", "bad"),
                                       ("realized_pnl", "Infinity")])
def test_invalid_required_state_cannot_be_recorded_as_valid_equity(valuation, monkeypatch, key, value):
    valuation.db.set_state(key, value)
    monkeypatch.setattr(valuation, "_price", lambda *a: {"last": 11})
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert not result["ok"] and not result["equity_recorded"]
    assert valuation.db.list_equity() == [] and valuation.db.get_state(key) == value
    json.dumps(result, allow_nan=False)


def test_arithmetic_overflow_cannot_record_infinite_valuation(valuation, monkeypatch):
    valuation.db.upsert_position("ADA/USD", 1e308, 1, 0)
    monkeypatch.setattr(valuation, "_price", lambda *a: {"last": 1e308})
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert not result["ok"] and result["equity_quote"] is None
    assert valuation.db.list_equity() == []


@pytest.mark.parametrize("qty", ["invalid", float("nan"), True])
def test_invalid_quantity_is_unknown_not_flat(valuation, monkeypatch, qty):
    monkeypatch.setattr(valuation.db, "get_position", lambda symbol: {"qty": qty, "avg_price": 10})
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert not result["ok"] and result["equity_quote"] is None
    assert valuation.db.list_equity() == []


def test_failed_price_lookup_cannot_record_held_value(valuation, monkeypatch):
    valuation.db.upsert_position("ADA/USD", 2, 10, 0)
    def unavailable(*args):
        raise RuntimeError("synthetic price failure")
    monkeypatch.setattr(valuation, "_price", unavailable)
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert not result["ok"] and result["equity_quote"] is None
    assert valuation.db.list_equity() == []


def test_monitor_keeps_failed_current_valuation_unknown(monkeypatch):
    from services.analytics import paper_sim_monitor as monitor
    monkeypatch.setattr(monitor, "_configured_strategy_runner", lambda: {"primary_symbol": "ADA/USD"})
    monkeypatch.setattr(monitor, "load_campaign_runtime_status", lambda: {"status": "running", "symbol": "ADA/USD"})
    monkeypatch.setattr(monitor, "_strategy_runner_status", lambda: {})
    monkeypatch.setattr(monitor, "_paper_engine_status", lambda: {"mtm": {"ADA/USD": {
        "ok": False, "valuation_status": "incomplete", "equity_quote": None, "reason": "missing_reference_price"}}})
    monkeypatch.setattr(monitor, "_paper_state_snapshot_window", lambda *a, **kw: {
        "position": {"qty": 2}, "latest_equity": {"ts": "historical", "unrealized_pnl": 99}})
    monkeypatch.setattr(monitor, "_trade_journal_snapshot", lambda *a, **kw: {})
    monkeypatch.setattr(monitor, "_promotion_progress_snapshot", lambda **kw: {"applicable": False})
    result = monitor.collect_once(monitor.PaperSimMonitorCfg())
    assert result["equity_valuation_known"] is False and result["unrealized_pnl"] is None
    assert result["recommendation"] == "investigate" and result["recommendation_reason"] == "paper_valuation_incomplete"
    assert result["latest_equity"]["ts"] == "historical"
    signature = monitor._signature_payload(result)
    assert signature["unrealized_pnl"] is None
    prior = dict(signature, equity_valuation_known=True, unrealized_pnl=0)
    assert "equity_valuation_changed" in monitor._change_reasons(prior, signature)
    monkeypatch.setattr(monitor, "_paper_engine_status", lambda: {"mtm": {"ADA/USD": {
        "ok": True, "valuation_status": "complete", "equity_quote": 1022}}})
    monkeypatch.setattr(monitor, "_paper_state_snapshot_window", lambda *a, **kw: {
        "position": {"qty": 2}, "latest_equity": {"ts": "fresh", "unrealized_pnl": 2}})
    restored = monitor.collect_once(monitor.PaperSimMonitorCfg())
    assert restored["equity_valuation_known"] is True and restored["unrealized_pnl"] == 2
    assert restored["recommendation_reason"] != "paper_valuation_incomplete"
