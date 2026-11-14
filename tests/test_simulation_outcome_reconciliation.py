"""BA-44: real paper fill/reconcile paths, synthetic prices and private DBs only."""
import importlib
import itertools
from pathlib import Path
import socket

import pytest

from tests.test_paper_reconciler_recovery import _allow_submit_gates, _base_intent, _reload_modules


@pytest.mark.parametrize("strategy,symbol", list(itertools.product(
    ("breakout_default", "ema_cross_default", "mean_reversion_default"),
    ("BTC/USD", "ETH/USD", "SOL/USD"),
)))
def test_first_fill_reconciles_from_protected_source_and_restart_is_idempotent(
        monkeypatch, tmp_path, strategy, symbol):
    def no_network(*args, **kwargs):
        pytest.fail("synthetic paper reconciliation attempted network")
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    source = tmp_path / "protected-source"
    source.mkdir()
    state = tmp_path / "account-state"
    monkeypatch.chdir(source)
    monkeypatch.setenv("CBP_STATE_DIR", str(state))
    _, queue, journal, engine, reconciler = _reload_modules(state)
    _allow_submit_gates(monkeypatch, engine)
    monkeypatch.setattr(engine.PaperEngine, "_price", lambda *a, **k:
                        {"ts_ms": 1, "bid": 100.0, "ask": 100.0, "last": 100.0})
    original_mkdir = Path.mkdir
    def source_is_readonly(path, *args, **kwargs):
        absolute = path if path.is_absolute() else Path.cwd() / path
        if absolute.is_relative_to(source / ".cbp_state"):
            raise PermissionError("synthetic read-only source namespace")
        return original_mkdir(path, *args, **kwargs)
    monkeypatch.setattr(Path, "mkdir", source_is_readonly)
    qdb, jdb, eng = queue.IntentQueueSQLite(), journal.TradeJournalSQLite(), engine.PaperEngine()
    identity = "account-first-fill"
    client = "paper_intent_" + identity
    placed = eng.submit_order(client_order_id=client, venue="coinbase", symbol=symbol,
                              side="buy", order_type="market", qty=1.0)
    assert placed["ok"] is True
    intent = _base_intent(identity, status="submitted", linked_order_id=placed["order"]["order_id"])
    intent.update(strategy_id=strategy, symbol=symbol)
    qdb.upsert_intent(intent)
    assert eng.evaluate_open_orders()["filled"] == 1
    result = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb)
    assert result["fills_journaled"] == 1
    assert qdb.get_intent(identity)["status"] == "filled" and jdb.count() == 1
    from services.execution import outcome_summary
    rows = outcome_summary.load_outcomes()
    assert len(rows) == 1 and rows[0]["intent_strategy_id"] == strategy
    assert rows[0]["symbol"] == symbol
    assert not (source / ".cbp_state").exists()
    assert (state / "runtime/outcomes/strategy_outcomes.jsonl").is_file()
    importlib.reload(reconciler)
    restarted = reconciler.reconcile_once(qdb=qdb, pdb=eng.db, jdb=jdb)
    assert restarted["fills_journaled"] == 0 and jdb.count() == 1
    assert len(outcome_summary.load_outcomes()) == 1
