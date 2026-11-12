import ast
from datetime import datetime, timedelta, timezone
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.market_data.hourly_candle_quality import assess_hourly_candles, check_cached_hourly_candles, HOUR_MS
from tests.test_pending_paper_exit_integration import pending, harness

NOW = datetime(2026, 11, 4, 12, 10, tzinfo=timezone.utc)
OPEN = int(NOW.replace(minute=0).timestamp() * 1000)


def candles(*, current=True):
    end = OPEN if current else OPEN - HOUR_MS
    return [[stamp, 100, 102, 99, 101, 10] for stamp in range(end - 59 * HOUR_MS, end + 1, HOUR_MS)]


def test_current_forming_hour_and_previous_complete_hour_are_distinguished():
    present = assess_hourly_candles(candles(), now=NOW)
    assert present["ok"] and present["last_candle_open_ms"] == OPEN
    assert present["last_candle_complete"] is False
    grace = assess_hourly_candles(candles(current=False), now=NOW.replace(minute=5))
    assert grace["ok"] and grace["last_candle_complete"] is True
    assert not grace["current_hour_present"]


@pytest.mark.parametrize("seconds,allowed", [(0, True), (299, True), (300, True), (300.001, False), (601, False)])
def test_current_hour_grace_is_at_most_five_minutes(seconds, allowed):
    now = NOW.replace(minute=0) + timedelta(seconds=seconds)
    result = assess_hourly_candles(candles(current=False), now=now)
    assert result["ok"] is allowed
    if not allowed:
        assert OPEN in result["missing_hours"]


def test_previous_hour_gap_is_not_hidden_by_current_hour_or_grace():
    rows = candles()
    missing = rows.pop(20)[0]
    result = assess_hourly_candles(rows, now=NOW)
    assert not result["ok"] and result["missing_hours"] == [missing]
    assert not assess_hourly_candles(candles(current=False)[:-1], now=NOW.replace(minute=1))["ok"]


@pytest.mark.parametrize("damage", ["duplicate", "reverse", "future", "unaligned", "boolean_timestamp",
                                    "zero", "nan", "bad", "negative_volume", "bad_range", "short"])
def test_invalid_required_candles_are_not_fresh(damage):
    rows = candles()
    if damage == "duplicate": rows[-1] = rows[-2]
    elif damage == "reverse": rows.reverse()
    elif damage == "future": rows[-1][0] += HOUR_MS
    elif damage == "unaligned": rows[-1][0] += 1
    elif damage == "boolean_timestamp": rows[-1][0] = True
    elif damage == "zero": rows[-1][4] = 0
    elif damage == "nan": rows[-1][4] = float("nan")
    elif damage == "bad": rows[-1][4] = "bad"
    elif damage == "negative_volume": rows[-1][5] = -1
    elif damage == "bad_range": rows[-1][2] = 1
    elif damage == "short": rows[-1] = [OPEN]
    assert not assess_hourly_candles(rows, now=NOW)["ok"]


@pytest.mark.parametrize("clock", [None, True, "bad", float("nan"), float("inf"), 1e308])
def test_bad_clock_fails_closed_without_raising(clock):
    assert assess_hourly_candles(candles(), now=clock)["reason"] == "invalid_clock"


@pytest.fixture
def market(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import storage.paper_trading_sqlite as ledger
    import storage.intent_queue_sqlite as queue
    import storage.trade_journal_sqlite as journal
    import services.execution.paper_engine as engine
    import services.execution.intent_reconciler as reconciler
    for module in (ledger, queue, journal, engine, reconciler): importlib.reload(module)
    now = [NOW]
    clock = lambda: now[0].isoformat()
    monkeypatch.setattr(engine, "_cfg", lambda: {"starting_cash_quote": 1000, "quote_currency": "USD",
        "fee_bps": 50, "slippage_bps": 0, "use_ccxt_fallback": False, "enabled": True,
        "max_order_qty": 1e9, "require_fresh_hourly_candles": True})
    monkeypatch.setattr(engine, "is_snapshot_fresh", lambda: (True, None))
    monkeypatch.setattr(engine, "is_master_read_only", lambda: False)
    monkeypatch.setattr(engine, "check_market_quality", lambda *a: {"ok": True, "price_used": 100})
    monkeypatch.setattr(engine, "load_gates", lambda: {})
    monkeypatch.setattr(engine, "ExecutionGuardStoreSQLite", lambda: None)
    monkeypatch.setattr(engine, "should_allow_order", lambda *a: (True, None))
    monkeypatch.setattr(engine.PaperEngine, "_price", lambda *a: {"bid": 100, "ask": 100, "last": 100})
    if os.getenv("CBP_CANDLE_BEFORE_ROOT"):
        root = Path(os.environ["CBP_CANDLE_BEFORE_ROOT"])
        for module, cls, name, file in ((engine, engine.PaperEngine, "_pre_submit_gate", "services/execution/paper_engine.py"),
                                         (ledger, ledger.PaperTradingSQLite, "apply_fill", "storage/paper_trading_sqlite.py")):
            tree = ast.parse((root / file).read_text())
            oldcls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == cls.__name__)
            method = next(node for node in oldcls.body if isinstance(node, ast.FunctionDef) and node.name == name)
            namespace = {}
            exec(compile(ast.Module(body=[method], type_ignores=[]), str(root / file), "exec"), module.__dict__, namespace)
            original = namespace[name]
            if name == "apply_fill":
                # Bridge only the new keyword; execute the original fill body unchanged.
                def original_fill(self, _original=original, **kwargs):
                    kwargs.pop("hourly_candle_guard", None)
                    return _original(self, **kwargs)
                monkeypatch.setattr(cls, name, original_fill)
            else:
                monkeypatch.setattr(cls, name, original)
    qdb, eng = queue.IntentQueueSQLite(), engine.PaperEngine(clock=clock)
    return SimpleNamespace(root=ledger.DB_PATH.parent, now=now, clock=clock, eng=eng, q=qdb,
                           journal=journal.TradeJournalSQLite(), reconciler=reconciler)


def write(market, rows=None, **changes):
    from services.market_data.local_data_reader import write_local_ohlcv_snapshot
    path = write_local_ohlcv_snapshot("coinbase", "ADA/USD", candles() if rows is None else rows,
                                      timeframe="1h", source="public_ohlcv")
    if changes:
        payload = json.loads(path.read_text())
        payload.update(changes)
        path.write_text(json.dumps(payload))
    return path


@pytest.mark.parametrize("changes", [{"source": "sample_ohlcv"}, {"symbol": "BTC/USD"},
                                     {"venue": "kraken"}, {"timeframe": "1d"}, {"symbol": None}])
def test_other_or_unknown_cache_identity_cannot_authorize_a_buy(market, changes):
    write(market, **changes)
    result = check_cached_hourly_candles("coinbase", "ADA/USD", clock=market.clock, data_root=market.root)
    assert not result["ok"]


def test_cache_upgrade_labels_unchanged_rows_without_inventing_source(market):
    path = write(market)
    payload = json.loads(path.read_text())
    payload.pop("symbol")
    payload["version"] = 2
    path.write_text(json.dumps(payload))
    assert not check_cached_hourly_candles("coinbase", "ADA/USD", clock=market.clock, data_root=market.root)["ok"]
    write(market)
    assert check_cached_hourly_candles("coinbase", "ADA/USD", clock=market.clock, data_root=market.root)["ok"]


@pytest.mark.parametrize("damage", ["missing", "corrupt", "legacy", "oversized", "duplicate_keys"])
def test_cache_failure_is_not_treated_as_fresh(market, damage):
    path = write(market)
    if damage == "missing": path.unlink()
    elif damage == "corrupt": path.write_text("{bad")
    elif damage == "legacy": path.write_text(json.dumps(candles()))
    elif damage == "oversized": path.write_text("x" * 1_048_577)
    else: path.write_text('{"source":"public_ohlcv","source":"public_ohlcv"}')
    assert not check_cached_hourly_candles("coinbase", "ADA/USD", clock=market.clock, data_root=market.root)["ok"]


def test_unsafe_venue_cannot_select_another_path(market, monkeypatch):
    monkeypatch.setattr(Path, "open", lambda *a, **kw: pytest.fail("must reject before reading"))
    result = check_cached_hourly_candles("../other", "ADA/USD", clock=market.clock, data_root=market.root)
    assert result["reason"] == "invalid_market_identity"


@pytest.mark.parametrize("kind", ["stale", "gap", "zero"])
def test_enabled_profile_refuses_bad_candles_at_submission(market, kind):
    rows = candles(current=kind != "stale")
    if kind == "gap": rows.pop(20)
    if kind == "zero": rows[-1][4] = 0
    write(market, rows)
    result = market.eng.submit_order(client_order_id="submit", venue="coinbase", symbol="ADA/USD",
        side="buy", order_type="market", qty=1)
    assert not result["ok"] and result["reason"].startswith("candle_data:")
    assert market.eng.db.list_fills() == [] and market.eng.cash_quote() == 1000


def test_fresh_at_submit_but_gapped_at_fill_does_not_fill(market):
    write(market)
    result = market.eng.submit_order(client_order_id="resting", venue="coinbase", symbol="ADA/USD",
                                     side="buy", order_type="market", qty=1)
    assert result["ok"]
    rows = candles()
    rows.pop(20)
    write(market, rows)
    assert market.eng.evaluate_open_orders()["filled"] == 0
    assert market.eng.db.get_order_by_client_id("resting")["status"] == "rejected"
    assert market.eng.cash_quote() == 1000 and market.eng.db.list_fills() == []


def test_stale_candles_do_not_block_sells_or_disabled_profile(market):
    write(market, candles(current=False))
    market.eng.db.upsert_position("ADA/USD", 1, 100, 0)
    sell = market.eng.submit_order(client_order_id="sell", venue="coinbase", symbol="ADA/USD",
                                   side="sell", order_type="market", qty=1)
    assert sell["ok"] and market.eng.evaluate_open_orders()["filled"] == 1
    market.eng.cfg["require_fresh_hourly_candles"] = False
    buy = market.eng.submit_order(client_order_id="disabled", venue="coinbase", symbol="ADA/USD",
                                  side="buy", order_type="market", qty=1)
    assert buy["ok"] and market.eng.evaluate_open_orders()["filled"] == 1


def test_protective_pending_sell_does_not_read_candle_cache(pending, monkeypatch):
    from services.market_data import hourly_candle_quality
    f = pending
    f.eng.cfg["require_fresh_hourly_candles"] = True
    monkeypatch.setattr(hourly_candle_quality, "check_cached_hourly_candles",
                        lambda *a, **kw: pytest.fail("a protective sell must not depend on candles"))
    row = f.trigger()
    f.cycle()
    assert f.root(row)["status"] == "filled" and len(f.root_fills(row)) == 1


def test_canonical_refusal_retains_reason_and_dispatches_existing_alert(market, monkeypatch):
    import services.admin.config_editor as config
    import services.alerts.alert_dispatcher as alerts
    monkeypatch.setattr(config, "load_user_yaml", lambda **kw: {})
    sent = []
    monkeypatch.setattr(alerts, "send_alert", lambda **kw: sent.append(kw) or {"ok": True, "skipped": True})
    monkeypatch.setattr(market.reconciler, "_now", market.clock)
    market.q.upsert_intent({"intent_id": "intent", "created_ts": market.clock(), "ts": market.clock(),
        "source": "strategy", "venue": "coinbase", "symbol": "ADA/USD", "side": "buy", "order_type": "market",
        "qty": 1, "status": "queued"})
    write(market)
    result = market.eng.submit_order(client_order_id="paper_intent_intent", venue="coinbase", symbol="ADA/USD",
                                     side="buy", order_type="market", qty=1)
    market.q.claim_next_queued()
    market.q.update_status("intent", "submitted", client_order_id="paper_intent_intent", linked_order_id=result["order"]["order_id"])
    write(market, candles(current=False))
    market.eng.evaluate_open_orders()
    market.reconciler.reconcile_once(qdb=market.q, pdb=market.eng.db, jdb=market.journal)
    row = market.q.get_intent("intent")
    assert row["status"] == "rejected" and row["last_error"].startswith("candle_data:")
    assert sent and market.q.list_paper_buy_events("intent")[-1]["reason"] == "not_delivered"


def test_decision_archive_retains_whitelisted_candle_quality():
    from tests.test_runner_decision_capture import make_record
    from services.strategies.signal_input_capture import _project_record
    record = make_record()
    record["candle_quality"] = {**assess_hourly_candles(candles(), now=NOW), "secret": "must-not-copy"}
    output = _project_record(record)["candle_quality"]
    assert output["ok"] and output["last_candle_complete"] is False
    assert "secret" not in output
