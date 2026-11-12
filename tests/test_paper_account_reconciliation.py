import copy
import ast
import importlib
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

from services.execution.paper_account_reconciliation import check_snapshot, reconcile_account_once


NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)


def empty():
    return {"orders": [], "intents": [], "fills": [], "positions": [], "event_intent_ids": [],
            "state": {"cash_quote": "1000", "realized_pnl": "0",
                      "paper_account_origin_v1": json.dumps({"schema": 1, "cash_quote": 1000, "quote_currency": "USD"})}}


def bought():
    snapshot = empty()
    snapshot["orders"] = [{"order_id": "o", "client_order_id": "paper_intent_i", "created_ts": NOW.isoformat(),
                           "status": "filled", "symbol": "ADA/USD", "venue": "coinbase", "side": "buy", "qty": 1}]
    snapshot["intents"] = [{"intent_id": "i", "client_order_id": "paper_intent_i", "created_ts": NOW.isoformat(),
                            "updated_ts": NOW.isoformat(), "linked_order_id": "o", "status": "filled",
                            "symbol": "ADA/USD", "venue": "coinbase", "side": "buy", "qty": 1}]
    snapshot["fills"] = [{"fill_id": "f", "order_id": "o", "ts": NOW.isoformat(),
                          "price": 100, "qty": 1, "fee": .5, "fee_currency": "USD"}]
    snapshot["positions"] = [{"symbol": "ADA/USD", "qty": 1, "avg_price": 100.5, "realized_pnl": 0}]
    snapshot["state"]["cash_quote"] = "899.5"
    return snapshot


def kinds(snapshot, now=NOW):
    return {row["kind"] for row in check_snapshot(snapshot, now=now.isoformat())["issues"]}


@pytest.mark.parametrize("factory", [empty, bought])
def test_consistent_account(factory):
    result = check_snapshot(factory(), now=NOW.isoformat())
    assert result["ok"] and result["opening_balance_verified"]


@pytest.mark.parametrize("qty,cash,remaining,pnl", [(.5, "954.225", .5, 4.475), (1, "1008.95", 0, 8.95)])
def test_partial_and_full_sell_replay_fee_inclusive_basis(qty, cash, remaining, pnl):
    snapshot = bought()
    order = dict(snapshot["orders"][0], order_id="sell", client_order_id="paper_intent_s", side="sell", qty=qty)
    snapshot["orders"].append(order)
    snapshot["intents"].append(dict(snapshot["intents"][0], intent_id="s", client_order_id="paper_intent_s",
                                     linked_order_id="sell", side="sell", qty=qty))
    snapshot["fills"].append(dict(snapshot["fills"][0], fill_id="sf", order_id="sell", price=110, qty=qty, fee=110 * qty * .005))
    snapshot["positions"][0].update(qty=remaining, avg_price=100.5 if remaining else 0, realized_pnl=pnl)
    snapshot["state"].update(cash_quote=cash, realized_pnl=str(pnl))
    assert not kinds(snapshot)


@pytest.mark.parametrize("key,value,expected", [("cash_quote", "900", "cash_mismatch"),
    ("realized_pnl", "1", "realized_pnl_mismatch"), ("cash_quote", "NaN", "invalid_account_state"),
    ("cash_quote", "1e999999", "invalid_account_state")])
def test_account_mismatches_are_not_healthy(key, value, expected):
    snapshot = bought()
    snapshot["state"][key] = value
    assert expected in kinds(snapshot)


@pytest.mark.parametrize("value", [None, "", "{}", '{"schema":1,"schema":1}',
                                    '{"schema":true,"cash_quote":1000,"quote_currency":"USD"}'])
def test_unknown_or_corrupt_origin_is_not_inferred(value):
    snapshot = bought()
    snapshot["state"]["paper_account_origin_v1"] = value
    assert "opening_balance_unverified" in kinds(snapshot)


@pytest.mark.parametrize("field,value", [("qty", 2), ("avg_price", 99), ("realized_pnl", 1)])
def test_all_position_fields_are_checked(field, value):
    snapshot = bought()
    snapshot["positions"][0][field] = value
    assert "position_mismatch" in kinds(snapshot)


@pytest.mark.parametrize("field,value,expected", [("fee", .075, "fee_not_50bps"),
    ("qty", 2, "fill_order_quantity_mismatch"), ("price", float("inf"), "invalid_fill_accounting"),
    ("qty", 0, "invalid_fill_accounting"), ("fee", -1, "invalid_fill_accounting"),
    ("fee_currency", "EUR", "quote_currency_unverified")])
def test_actual_fill_values_are_checked(field, value, expected):
    snapshot = bought()
    snapshot["fills"][0][field] = value
    assert expected in kinds(snapshot)


@pytest.mark.parametrize("status", ["queued", "submitting", "submitted", "held"])
@pytest.mark.parametrize("side,expected", [("buy", "buy_overdue"), ("sell", "sell_waiting_over_120s")])
def test_every_pending_status_has_an_age_check(status, side, expected):
    snapshot = bought()
    snapshot["intents"][0].update(status=status, side=side)
    assert expected in kinds(snapshot, NOW + timedelta(seconds=120))
    assert expected not in kinds(snapshot, NOW + timedelta(seconds=119))


@pytest.mark.parametrize("damage,expected", [("orders", "fill_without_order"),
    ("fills", "order_fill_state_mismatch"), ("positions", "position_mismatch"),
    ("intents", "queue_intent_missing")])
def test_missing_rows_are_reported(damage, expected):
    snapshot = bought()
    snapshot[damage] = []
    assert expected in kinds(snapshot)


def test_deleted_unwritten_intent_survives_as_seen_or_event_evidence():
    snapshot = empty()
    snapshot["state"]["paper_watchdog_seen_v1"] = '["old-queued"]'
    snapshot["event_intent_ids"] = ["other-deleted"]
    result = check_snapshot(snapshot, now=NOW.isoformat())
    assert {(row["kind"], row["identity"]) for row in result["issues"]} == {
        ("observed_queue_intent_deleted", "old-queued"), ("observed_queue_intent_deleted", "other-deleted")}


def test_duplicate_fill_and_late_buy_cannot_pass():
    snapshot = bought()
    snapshot["fills"].append(dict(snapshot["fills"][0], fill_id="duplicate", ts=(NOW + timedelta(seconds=120)).isoformat()))
    assert {"multiple_fills_for_full_fill_order", "buy_filled_after_deadline"} <= kinds(snapshot)


@pytest.mark.parametrize("field,value", [("qty", 2), ("symbol", "BTC/USD"),
                                         ("venue", "kraken"), ("client_order_id", "wrong")])
def test_intent_and_order_identity_are_checked(field, value):
    snapshot = bought()
    snapshot["intents"][0][field] = value
    assert "intent_order_identity_mismatch" in kinds(snapshot)


def test_terminal_refusal_cannot_conceal_a_real_fill():
    snapshot = bought()
    snapshot["intents"][0]["status"] = "rejected"
    assert "final_intent_disagrees_with_fill" in kinds(snapshot)


def test_all_twenty_five_symbols_are_replayed_not_just_primary_symbol():
    snapshot = empty()
    for index in range(25):
        item = bought()
        symbol, intent, order = f"S{index}/USD", f"i{index}", f"o{index}"
        item["orders"][0].update(symbol=symbol, order_id=order, client_order_id="paper_intent_" + intent)
        item["intents"][0].update(symbol=symbol, intent_id=intent, linked_order_id=order, client_order_id="paper_intent_" + intent)
        item["fills"][0].update(fill_id=f"f{index}", order_id=order, price=10, fee=.05)
        item["positions"][0].update(symbol=symbol, avg_price=10.05)
        for key in ("orders", "intents", "fills", "positions"):
            snapshot[key].extend(item[key])
    snapshot["state"]["cash_quote"] = "748.75"
    assert not kinds(snapshot)


class FakeStore:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.seen = []

    def account_reconciliation_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def record_account_reconciliation_seen(self, ids):
        self.seen.extend(ids)


def test_report_is_append_only_and_skipped_alert_is_not_delivery(tmp_path):
    snapshot = bought()
    snapshot["state"]["cash_quote"] = "900"
    store, attempts = FakeStore(snapshot), []
    dispatch = lambda payload: attempts.append(payload) or {"ok": True, "skipped": True}
    for _ in range(2):
        result = reconcile_account_once(pdb=store, now=NOW.isoformat(), report_dir=tmp_path, dispatch=dispatch)
        assert not result["ok"] and result["alert"] == {"attempted": True, "delivered": False}
    rows = [json.loads(line) for line in (tmp_path / "2026-11-03.jsonl").read_text().splitlines()]
    assert len(rows) == len(attempts) == 2
    assert store.seen == ["i", "i"]


@pytest.mark.parametrize("failure", ["snapshot", "seen", "dispatch", "report"])
def test_evidence_failures_are_not_reported_healthy(tmp_path, monkeypatch, failure):
    snapshot = bought()
    snapshot["state"]["cash_quote"] = "900"
    store = FakeStore(snapshot)
    def broken(*args, **kwargs):
        raise OSError("synthetic")
    dispatch = lambda payload: {"ok": True}
    if failure in {"snapshot", "seen"}:
        monkeypatch.setattr(store, "account_reconciliation_snapshot" if failure == "snapshot"
                            else "record_account_reconciliation_seen", broken)
    elif failure == "dispatch":
        dispatch = broken
    else:
        tmp_path = tmp_path / "not-a-directory"
        tmp_path.write_text("preserve")
    result = reconcile_account_once(pdb=store, now=NOW.isoformat(), report_dir=tmp_path, dispatch=dispatch)
    assert not result["ok"]
    if failure == "seen":
        assert "cash_mismatch" in {row["kind"] for row in result["issues"]}
    if failure == "report":
        assert tmp_path.read_text() == "preserve"


def test_report_failure_on_otherwise_good_account_dispatches(tmp_path):
    target = tmp_path / "existing"
    target.write_text("untouched")
    attempts = []
    result = reconcile_account_once(pdb=FakeStore(empty()), now=NOW.isoformat(), report_dir=target,
                                    dispatch=lambda payload: attempts.append(payload) or {"ok": True})
    assert not result["ok"] and attempts and result["alert"]["delivered"]


def test_monitor_mode_is_explicit_and_status_read_does_not_repeat_audit(monkeypatch):
    from services.analytics import paper_sim_monitor as monitor
    from services.execution import paper_account_reconciliation as account
    calls = []
    monkeypatch.setattr(account, "reconcile_account_once", lambda **kw: calls.append(kw) or {"ok": False, "issues": []})
    result = monitor.collect_once(monitor.PaperSimMonitorCfg(account_reconciliation=True))
    assert result["recommendation"] == "investigate" and len(calls) == 1
    result.update(status="stopped", pid_alive=False)
    assert monitor._reconcile_stopped_runtime_payload(result) == result
    assert len(calls) == 1
    assert not monitor.PaperSimMonitorCfg().account_reconciliation


@pytest.mark.parametrize("interval", [0, -1, 301, float("nan"), float("inf")])
def test_account_monitor_rejects_unbounded_interval(interval):
    from services.analytics.paper_sim_monitor import PaperSimMonitorCfg
    with pytest.raises(ValueError, match="at_most_300"):
        PaperSimMonitorCfg(poll_interval_sec=interval, account_reconciliation=True)


@pytest.fixture
def account(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import storage.paper_trading_sqlite as ledger
    import storage.intent_queue_sqlite as queue
    import services.execution.paper_engine as engine
    for module in (ledger, queue, engine):
        importlib.reload(module)
    if os.getenv("CBP_ACCOUNT_BEFORE_ROOT"):
        path = Path(os.environ["CBP_ACCOUNT_BEFORE_ROOT"]) / "services/execution/paper_engine.py"
        tree = ast.parse(path.read_text())
        cls = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "PaperEngine")
        method = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "_ensure_cash_initialized")
        namespace = {}
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), engine.__dict__, namespace)
        monkeypatch.setattr(engine.PaperEngine, "_ensure_cash_initialized", namespace[method.name])
    monkeypatch.setattr(engine, "_cfg", lambda: {"starting_cash_quote": 1000, "quote_currency": "USD",
        "fee_bps": 50, "slippage_bps": 0, "use_ccxt_fallback": False, "max_order_qty": 1e9, "enabled": True})
    monkeypatch.setattr(engine.PaperEngine, "_pre_submit_gate", lambda *a, **kw: (True, None))
    monkeypatch.setattr(engine.PaperEngine, "_price", lambda *a: {"bid": 100, "ask": 100, "last": 100})
    qdb = queue.IntentQueueSQLite()
    eng = engine.PaperEngine(clock=lambda: NOW.isoformat())
    return eng, qdb


def test_pristine_cash_has_durable_origin(account):
    eng, _ = account
    origin = eng.db.get_state("paper_account_origin_v1")
    assert origin is not None, "initialized cash has no evidenced opening-balance receipt"
    assert json.loads(origin) == {"schema": 1, "cash_quote": 1000, "quote_currency": "USD"}
    eng.db.initialize_account(100000, "EUR")
    assert eng.cash_quote() == 1000 and eng.db.get_state("paper_account_origin_v1") == origin


def test_account_monitor_loop_subtracts_check_time_from_interval(tmp_path, monkeypatch):
    from services.analytics import paper_sim_monitor as monitor
    monkeypatch.setattr(monitor, "ensure_dirs", lambda: None)
    monkeypatch.setattr(monitor, "_flags_dir", lambda: tmp_path)
    monkeypatch.setattr(monitor, "stop_file", lambda: tmp_path / "stop")
    monkeypatch.setattr(monitor, "load_runtime_status", lambda: {})
    for name in ("_write_pid_state", "_write_status", "_append_history", "_clear_pid_state"):
        monkeypatch.setattr(monitor, name, lambda *a, **kw: None)
    monkeypatch.setattr(monitor, "list_watches", lambda: [])
    monkeypatch.setattr(monitor, "_recent_watch_reports", lambda **kw: [])
    monkeypatch.setattr(monitor, "collect_once", lambda cfg: {"ok": True, "account_reconciliation_enabled": True})
    ticks = iter([0, 7, 300])
    sleeps = []
    monkeypatch.setattr(monitor.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(monitor.time, "sleep", sleeps.append)
    monitor.run_forever(monitor.PaperSimMonitorCfg(account_reconciliation=True), max_loops=2)
    assert sleeps == [293]


def test_real_account_replay_and_deleted_row_detection(account, tmp_path):
    import sqlite3
    import storage.intent_queue_sqlite as queue
    eng, qdb = account
    qdb.upsert_intent({"intent_id": "actual", "created_ts": NOW.isoformat(), "ts": NOW.isoformat(),
        "source": "strategy", "venue": "coinbase", "symbol": "ADA/USD", "side": "buy", "order_type": "market",
        "qty": 1, "status": "queued"})
    order = eng.submit_order(client_order_id="paper_intent_actual", venue="coinbase", symbol="ADA/USD",
                            side="buy", order_type="market", qty=1, intent_created_ts=NOW.isoformat())["order"]
    eng.evaluate_open_orders()
    qdb.update_status("actual", "submitting")
    qdb.update_status("actual", "submitted", client_order_id="paper_intent_actual", linked_order_id=order["order_id"])
    qdb.update_status("actual", "filled")
    before_cash = eng.cash_quote()
    before_orders = eng.db.list_orders()
    result = reconcile_account_once(pdb=eng.db, now=NOW.isoformat(), report_dir=tmp_path / "reports",
                                    dispatch=lambda payload: pytest.fail("healthy account must not alert"))
    assert result["ok"], result
    with sqlite3.connect(queue.DB_PATH) as con:
        con.execute("DELETE FROM trade_intents WHERE intent_id='actual'")
    alerts = []
    result = reconcile_account_once(pdb=eng.db, now=NOW.isoformat(), report_dir=tmp_path / "reports",
                                    dispatch=lambda payload: alerts.append(payload) or {"ok": True})
    assert not result["ok"] and alerts
    assert {"queue_intent_missing", "observed_queue_intent_deleted"} <= {row["kind"] for row in result["issues"]}
    assert eng.cash_quote() == before_cash and eng.db.list_orders() == before_orders


def test_real_legacy_account_is_not_rebaselined_from_current_cash(account, tmp_path):
    eng, _ = account
    eng.db.set_state("paper_account_origin_v1", "{}")
    eng.db.set_state("cash_quote", "999")
    result = reconcile_account_once(pdb=eng.db, now=NOW.isoformat(), report_dir=tmp_path,
                                    dispatch=lambda payload: {"ok": True, "skipped": True})
    assert not result["ok"] and not result["opening_balance_verified"]
    assert eng.db.get_state("paper_account_origin_v1") == "{}" and eng.cash_quote() == 999
