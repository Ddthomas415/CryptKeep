"""Bounded independent O-55 probes; synthetic inputs and temporary SQLite only."""
import ast
import difflib
import hashlib
import json
import math
from pathlib import Path

import pytest

from tests.test_paper_missing_price_valuation import engine, finances, snapshot, valuation


ARTIFACT = Path(__file__).resolve().parents[1]
ROOT = ARTIFACT.parents[2]


def test_three_file_seal_and_engine_method_boundary():
    for name, digest in {
        "stage.diff": "1fc1b7410f1ef184de70659584545eb305a82c01d9b050d3135e5bd152235ea2",
        "hashes.json": "cddd240f07a752e7a66ea0bbc5f3b53047262415dc14d94043ce78a360c24440",
    }.items():
        assert hashlib.sha256((ARTIFACT / name).read_bytes()).hexdigest() == digest
    manifest = json.loads((ARTIFACT / "hashes.json").read_text())
    names = ("services/execution/paper_engine.py", "services/analytics/paper_sim_monitor.py",
             "tests/test_paper_missing_price_valuation.py")
    assert set(manifest["current"]) == set(manifest["before"]) == set(names)
    chunks = []
    for name in names:
        old_path = ARTIFACT / "before" / name
        old = old_path.read_bytes() if old_path.exists() else b""
        current = (ROOT / name).read_bytes()
        assert hashlib.sha256(old).hexdigest() == manifest["before"][name]
        assert hashlib.sha256(current).hexdigest() == manifest["current"][name]
        chunks.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),
            current.decode().splitlines(keepends=True), fromfile="before/" + name, tofile="after/" + name))
    assert "".join(chunks).encode() == (ARTIFACT / "stage.diff").read_bytes()
    old = ast.parse((ARTIFACT / "before" / names[0]).read_text())
    current = ast.parse((ROOT / names[0]).read_text())
    for tree in (old, current):
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PaperEngine")
        cls.body = [node for node in cls.body if not (
            isinstance(node, ast.FunctionDef) and node.name == "mark_to_market")]
    assert ast.dump(old) == ast.dump(current)


def test_missing_price_preserves_actual_fill_order_and_prior_equity(valuation, monkeypatch):
    eng = valuation
    monkeypatch.setattr(eng, "_price", lambda *a: {"last": 10})
    assert eng.submit_order(client_order_id="review-buy", venue="coinbase", symbol="ADA/USD",
        side="buy", order_type="market", qty=2)["ok"]
    assert eng.evaluate_open_orders()["filled"] == 1
    assert eng.mark_to_market("coinbase", "ADA/USD")["ok"]
    before, history = finances(eng), eng.db.list_equity()
    assert before["fills"] and before["orders"] and before["positions"] and history
    monkeypatch.setattr(eng, "_price", lambda *a: None)
    result = eng.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] is False and result["equity_recorded"] is False
    assert result["equity_quote"] is None and result["unrealized_pnl"] is None
    assert result["cash_quote"] == float(before["cash"])
    assert finances(eng) == before and eng.db.list_equity() == history
    monkeypatch.setattr(eng, "_price", lambda *a: {"last": 11})
    assert eng.mark_to_market("coinbase", "ADA/USD")["ok"]
    assert finances(eng) == before and len(eng.db.list_equity()) == len(history) + 1


def test_large_finite_book_mid_does_not_overflow(valuation, monkeypatch):
    valuation.db.upsert_position("ADA/USD", 1e-308, 1e308, 0)
    monkeypatch.setattr(valuation, "_price", lambda *a: {"bid": 1.6e308, "ask": 1.7e308})
    result = valuation.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] and result["valuation_status"] == "complete"
    assert all(math.isfinite(result[name]) for name in ("mid", "equity_quote", "unrealized_pnl"))
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("matching_failed", [True, False])
def test_monitor_exception_mark_is_symbol_specific(monkeypatch, matching_failed):
    from services.analytics import paper_sim_monitor as monitor
    monkeypatch.setattr(monitor, "_configured_strategy_runner", lambda: {"primary_symbol": "ADA/USD"})
    monkeypatch.setattr(monitor, "load_campaign_runtime_status", lambda: {"status": "running", "symbol": "ADA/USD"})
    monkeypatch.setattr(monitor, "_strategy_runner_status", lambda: {})
    failed = {"ok": False, "reason": "RuntimeError:synthetic"}
    valid = {"ok": True, "valuation_status": "complete", "unrealized_pnl": 2}
    monkeypatch.setattr(monitor, "_paper_engine_status", lambda: {"mtm": {
        "ADA/USD": failed if matching_failed else valid, "BTC/USD": failed}})
    monkeypatch.setattr(monitor, "_paper_state_snapshot_window", lambda *a, **kw: {
        "position": {"qty": 2}, "latest_equity": {"unrealized_pnl": 99}})
    monkeypatch.setattr(monitor, "_trade_journal_snapshot", lambda *a, **kw: {})
    monkeypatch.setattr(monitor, "_promotion_progress_snapshot", lambda **kw: {"applicable": False})
    result = monitor.collect_once(monitor.PaperSimMonitorCfg())
    assert result["equity_valuation_known"] is (not matching_failed)
    if matching_failed:
        assert result["unrealized_pnl"] is None
        assert result["recommendation_reason"] == "paper_valuation_incomplete"
        assert monitor._signature_payload(result)["unrealized_pnl"] is None
    else:
        assert result["recommendation_reason"] != "paper_valuation_incomplete"
