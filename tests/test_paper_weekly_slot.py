"""Real runner/temporary ledgers, synthetic markets; no deployment or paper study."""
import json
import sqlite3

import pytest

from tests.test_runner_multi_symbol_integration import harness
from tests.test_paper_cash_entry import prepare
from tests.test_group_b_weekly_selection import NOW, selection, reseal


def setup_slot(h, monkeypatch, artifact=None):
    from services.analytics.group_b_weekly_selection import publish_selection
    from services.market_data.group_b_selection import POLICY
    _, rules_db = prepare(h, monkeypatch)
    monkeypatch.setattr(h.runner, "_now", lambda: NOW)
    directory = h.tmp / "rankings"
    directory.mkdir()
    h.cfg["group_b_selection"] = {"policy": POLICY, "slot": 1, "directory": str(directory)}
    if artifact is not None:
        publish_selection(artifact, directory)
    h.cfg["stop_loss_pct"] = h.cfg["trailing_stop_pct"] = 0
    # prepare() made a strict real snapshot/rules cache. Use the bounded clock.
    from services.market_data import tick_reader
    from services.market_data.group_b_selection import instant
    from tests.test_runner_multi_symbol_integration import PRICES
    raw = json.loads(tick_reader.LATEST.read_text())
    raw["ts_ms"] = int(instant(NOW).timestamp() * 1000)
    for tick in raw["ticks"]:
        tick["ts_ms"] = raw["ts_ms"]
    raw["ticks"] += [{"source": "public_ticker", "venue": "coinbase", "symbol": s,
                      "symbol_mapped": s, "ticker_symbol": s, "bid": p, "ask": p,
                      "ts_ms": raw["ts_ms"]} for s, p in PRICES.items() if s != "BTC/USD"]
    tick_reader.LATEST.write_text(json.dumps(raw))
    with sqlite3.connect(rules_db) as con:
        con.execute("UPDATE market_rules_cache SET updated_ts=?", (instant(NOW).timestamp(),))
    from services.admin import config_editor
    monkeypatch.setattr(config_editor, "load_user_yaml", lambda **kw: raw_config(h))
    original_fill = h._fill

    def guarded_fixture_fill(row, *, reject=False):
        if "group_b_selection" not in (row.get("meta") or {}):
            return original_fill(row, reject=reject)
        from services.market_data.paper_snapshot_quote import read_paper_quote
        quote, reason = read_paper_quote(row["venue"], row["symbol"], clock=lambda: NOW)
        assert quote is not None, reason
        order = {**row, "order_id": "offline-" + row["intent_id"],
                 "client_order_id": "paper_intent_" + row["intent_id"],
                 "ts": NOW, "status": "rejected" if reject else "new"}
        h.paper.insert_order(order)
        if not reject:
            result = h.paper.apply_fill(order=order, ts=NOW, price=quote["mid"], qty=row["qty"], fee=0,
                                        fee_currency="USD", clock=lambda: NOW, snapshot_quote_guard=True,
                                        snapshot_quote=quote, snapshot_slippage_bps=0)
            assert result["ok"], result
        return order

    monkeypatch.setattr(h, "_fill", guarded_fixture_fill)
    return directory


def resolve(h, now=NOW):
    from services.execution.paper_weekly_slot import resolve_slot
    from services.execution.paper_exit_accounting import PaperExitAccounting
    return resolve_slot(cfg=h.cfg, sdb=h.state, qdb=h.queue, pdb=h.paper,
                        accounting=PaperExitAccounting(h.state, h.queue),
                        limits=h.runner.build_performance_limits(h.cfg), now=now)


def seed(h, symbol="BTC/USD"):
    from tests.test_runner_multi_symbol_integration import PRICES, STRATEGY
    h._fill({"intent_id": "initial-holding-" + symbol, "venue": "coinbase", "symbol": symbol,
             "side": "buy", "order_type": "market", "qty": .5,
             "strategy_id": STRATEGY, "meta": {"reference_price": PRICES[symbol]}})


def test_missing_ranking_blocks_actual_runner_buy(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch)
    h.run(1)
    assert not h.intents("buy")
    assert any(x.get("note") == "group_b_entry_or_rotation_wait" for x in h.statuses)


def test_valid_ranking_allows_actual_cash_sized_entry(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    h.run(1)
    [buy] = h.intents("buy")
    assert buy["symbol"] == "BTC/USD" and buy["qty"] == 9.95
    assert buy["meta"]["paper_entry_sizing"]["policy"] == "available_cash_v1"
    assert buy["meta"]["group_b_selection"]["selection_sha256"]


def test_missing_ranking_keeps_normal_exit_management(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch)
    seed(h)
    h.signal_action = "sell"
    h.run(1)
    [sell] = h.intents("sell")
    assert sell["symbol"] == "BTC/USD"
    assert sell["meta"].get("exit_reason") != "rotation"


def test_valid_cash_week_is_a_rotation_not_missing_ranking(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch, selection(()))
    seed(h)
    h.cfg["min_bars"] = 500  # rotation must not wait for strategy warm-up
    h.state.set(h.key("last_emitted_action", "BTC/USD"), "sell")
    h.run(2)
    [sell] = h.intents("sell")
    assert sell["meta"]["exit_reason"] == "rotation"
    assert sell["meta"]["paper_exit_policy"] == "retry_until_filled_v1"
    assert sell["qty"] == .5
    assert not h.intents("buy")


def test_rotation_waits_for_fill_then_changes_symbol_without_resetting_cash(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    seed(h)
    before = h.paper.get_state("cash_quote")
    h.signal_action = "hold"
    h.run(2)
    [sell] = h.intents("sell")
    first = resolve(h)
    assert first["symbols"] == ["BTC/USD"] and not first["allow_buy"]
    assert h.paper.get_state("cash_quote") == before
    # Same persisted intent, resolved using the existing minimal fixture driver.
    type(h).consume(h)
    assert h.paper.get_position("BTC/USD")["qty"] == 0
    second = resolve(h)
    assert second["symbols"] == ["ETH/USD"] and second["allow_buy"]
    assert float(h.paper.get_state("cash_quote")) > float(before)
    assert h.queue.get_intent(sell["intent_id"])["status"] == "filled"
    h.reload_runner()
    assert resolve(h)["symbols"] == ["ETH/USD"]


@pytest.mark.parametrize("failure", ["missing", "malformed", "mutated", "replaced", "live"])
def test_invalid_ranking_never_rotates_or_uses_prior_picks(harness, monkeypatch, failure):
    from services.market_data.group_b_selection import weekly_name
    h = harness
    directory = setup_slot(h, monkeypatch, selection())
    first = resolve(h)
    assert first["allow_buy"]
    seed(h)
    path = directory / weekly_name(NOW)
    if failure == "missing":
        path.unlink()
    elif failure == "malformed":
        path.write_text("not json")
    elif failure == "mutated":
        raw = json.loads(path.read_text())
        raw["slots"][0] = None
        path.write_text(json.dumps(raw))
    elif failure == "replaced":
        path.write_text(json.dumps(selection(("ETH/USD",))))
    else:
        h.cfg["_paper_entry_policy"]["live_enabled"] = True
    current = resolve(h)
    assert current["symbols"] == ["BTC/USD"]
    assert not current["allow_buy"] and not current["rotation_symbols"]


@pytest.mark.parametrize("pending", ["buy", "ledger_order", "unknown_queue", "unsettled"])
def test_flat_is_not_sufficient_to_switch(harness, monkeypatch, pending):
    from tests.test_paper_reconciler_recovery import _base_intent
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    if pending == "buy":
        h.queue.upsert_intent(_base_intent("pending-old", status="held"))
    elif pending == "ledger_order":
        h.paper.insert_order({**_base_intent("open-old"), "order_id": "open-old",
                              "client_order_id": "open-old", "status": "new"})
    elif pending == "unknown_queue":
        monkeypatch.setattr(h.queue, "slot_open_intents", lambda: (_ for _ in ()).throw(RuntimeError()))
    else:
        from services.execution.paper_exit_accounting import PaperExitAccounting
        monkeypatch.setattr(PaperExitAccounting, "refresh", lambda *a, **k: {"unsettled": True})
    result = resolve(h)
    assert not result["allow_buy"]
    assert "BTC/USD" in result["symbols"]


def test_rejected_durable_exit_is_not_terminal_for_switch(harness, monkeypatch):
    from tests.test_paper_reconciler_recovery import _base_intent
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    row = _base_intent("owed-sell", status="rejected")
    row.update(side="sell", meta={"paper_exit_policy": "retry_until_filled_v1", "paper_exit_id": "owed-sell"})
    h.queue.upsert_intent(row)
    result = resolve(h)
    assert not result["allow_buy"] and "BTC/USD" in result["symbols"]
    assert len(h.queue.list_paper_exits()) == 1


def test_held_rotation_is_retried_with_the_same_identity(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    seed(h)
    h.run(1)
    [sell] = h.intents("sell")
    h.queue.paper_exit_transition(sell["intent_id"], "held", event="refused", reason="synthetic_refusal")
    h.run(3)
    assert [x["intent_id"] for x in h.intents("sell")] == [sell["intent_id"]]
    assert not h.intents("buy")
    assert h.paper.get_position("BTC/USD")["qty"] == .5


def test_retired_accounting_is_still_checked_after_flat_switch(harness, monkeypatch):
    from services.analytics.group_b_weekly_selection import publish_selection
    from services.execution.paper_exit_accounting import PaperExitAccounting
    h = harness
    first = selection(("BTC/USD",))
    directory = setup_slot(h, monkeypatch, first)
    assert resolve(h)["allow_buy"]
    next_time = "2026-11-16T00:06:00Z"
    second = selection(("ETH/USD",), rank_at="2026-11-16T00:05:00Z", generated_at=next_time, previous=first)
    publish_selection(second, directory)
    assert resolve(h, next_time)["symbols"] == ["ETH/USD"]
    calls = []

    def refresh(_self, **kw):
        calls.append(kw["symbol"])
        return {"unsettled": kw["symbol"] == "BTC/USD"}

    monkeypatch.setattr(PaperExitAccounting, "refresh", refresh)
    assert not resolve(h, next_time)["allow_buy"]
    assert calls == ["BTC/USD", "ETH/USD"]


def test_week_is_rechecked_after_signal_before_entry(harness, monkeypatch):
    h = harness
    setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    clock = [NOW]
    monkeypatch.setattr(h.runner, "_now", lambda: clock[0])
    compute = h.runner._strategy_signal

    def signal(*args, **kwargs):
        out = compute(*args, **kwargs)
        clock[0] = "2026-11-16T00:05:00Z"
        return out

    monkeypatch.setattr(h.runner, "_strategy_signal", signal)
    h.run(1)
    assert not h.intents("buy")
    assert any(x.get("note") == "group_b_entry_or_rotation_wait" for x in h.statuses)


def test_no_ranker_is_called_by_consumer_and_actual_holding_drives_valuation(harness, monkeypatch):
    from services.execution.paper_weekly_slot import valuation_symbol
    from services.signals import market_ranker
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    monkeypatch.setattr(market_ranker, "rank_market", lambda **kw: pytest.fail("execution called ranker"))
    assert resolve(h)["symbols"] == ["ETH/USD"]
    seed(h, "ETH/USD")
    assert valuation_symbol(pdb=h.paper, sdb=h.state) == "ETH/USD"
    seed(h, "BTC/USD")  # unexpected multi-held state is not complete account equity
    assert valuation_symbol(pdb=h.paper, sdb=h.state) is None


def test_paper_runner_values_actual_rotated_coin_not_flat_placeholder(harness, monkeypatch):
    import importlib
    from types import SimpleNamespace
    from tests.test_runner_multi_symbol_integration import _BoundedStop
    from services.execution.paper_engine import PaperEngine
    from services.execution import paper_runner
    h = harness
    setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    assert resolve(h)["symbols"] == ["ETH/USD"]
    seed(h, "ETH/USD")
    runner = importlib.reload(paper_runner)
    engine = PaperEngine.__new__(PaperEngine)
    engine.db = h.paper
    monkeypatch.setattr(engine, "_price", lambda venue, symbol: {"bid": 1000, "ask": 1000})
    calls = []
    actual_mark = engine.mark_to_market

    def mark(venue, symbol):
        calls.append(symbol)
        return actual_mark(venue, symbol)

    monkeypatch.setattr(engine, "mark_to_market", mark)
    monkeypatch.setattr(engine, "evaluate_open_orders", lambda: {}, raising=False)
    monkeypatch.setattr(runner, "PaperEngine", lambda: engine)
    monkeypatch.setattr(runner, "load_user_yaml", lambda: {"strategy_runner": h.cfg,
                                                         "paper_trading": {"default_symbol": "BTC/USD"}})
    monkeypatch.setattr(runner, "_consume_queued_intents_once", lambda **kw: {})
    monkeypatch.setattr(runner, "reconcile_once", lambda **kw: {})
    monkeypatch.setattr(runner, "_write_status", lambda row: None)
    monkeypatch.setattr(runner, "time", SimpleNamespace(sleep=lambda value: None))
    monkeypatch.setattr(runner, "STOP_FILE", _BoundedStop(h.tmp / "paper-stop", 1, lambda: None))
    runner.run_forever()
    assert calls == ["ETH/USD"]


def test_rotation_refuses_a_quote_mapped_to_another_coin(harness, monkeypatch):
    from services.market_data import tick_reader
    h = harness
    setup_slot(h, monkeypatch, selection(()))
    seed(h)
    raw = json.loads(tick_reader.LATEST.read_text())
    raw["ticks"][0].update(symbol_mapped="ETH/USD", ticker_symbol="ETH/USD", bid=1000, ask=1000)
    tick_reader.LATEST.write_text(json.dumps(raw))
    h.run(1)
    assert not h.intents("sell")


def test_scope_discovered_during_missing_ranking_is_never_forgotten(harness, monkeypatch):
    from services.market_data.group_b_selection import weekly_name
    from services.execution.paper_exit_accounting import PaperExitAccounting, scope_for
    from storage.exit_event_journal import ExitEventJournal
    h = harness
    directory = setup_slot(h, monkeypatch, selection(("ETH/USD",)))
    resolve(h)
    path = directory / weekly_name(NOW)
    original = path.read_bytes()
    seed(h, "SOL/USD")
    path.unlink()
    scope = scope_for("coinbase", "SOL/USD", h.cfg["strategy_id"])
    real_apply = ExitEventJournal.apply
    monkeypatch.setattr(ExitEventJournal, "apply", lambda self, s, *a, **k:
                        False if s == scope else real_apply(self, s, *a, **k))
    h.signal_action = "sell"
    h.run(1)
    type(h).consume(h)
    journal = PaperExitAccounting(h.state, h.queue).journal
    assert journal.has_unresolved(scope)
    path.write_bytes(original)
    assert not resolve(h)["allow_buy"]
    assert journal.has_unresolved(scope)


def raw_config(h):
    p = h.cfg["_paper_entry_policy"]
    return {"strategy_runner": h.cfg, "execution": {"live_enabled": p["live_enabled"]},
            "live_execution": {"armed": p["armed"]}, "paper_trading": p}


def test_consumer_does_not_submit_a_buy_across_missing_week_ranking(harness, monkeypatch):
    from types import SimpleNamespace
    from services.market_data import tick_reader
    from services.market_data.group_b_selection import instant
    from services.os.app_paths import data_dir
    from services.execution import paper_runner
    h = harness
    setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    before, after = "2026-11-16T00:04:59Z", "2026-11-16T00:05:01Z"
    raw = json.loads(tick_reader.LATEST.read_text())
    raw["ts_ms"] = int(instant(before).timestamp() * 1000)
    for tick in raw["ticks"]:
        tick["ts_ms"] = raw["ts_ms"]
    tick_reader.LATEST.write_text(json.dumps(raw))
    with sqlite3.connect(data_dir() / "execution.sqlite") as con:
        con.execute("UPDATE market_rules_cache SET updated_ts=?", (instant(before).timestamp(),))
    monkeypatch.setattr(h.runner, "_now", lambda: before)
    h.run(1)
    assert len(h.intents("buy")) == 1
    monkeypatch.setattr(paper_runner, "_now", lambda: after)
    monkeypatch.setattr(paper_runner, "load_user_yaml", lambda **kw: raw_config(h))

    async def decisions(rows):
        return [(r, SimpleNamespace(allowed=True)) for r in rows]

    monkeypatch.setattr(paper_runner, "_decide_batch", decisions)
    submits = []

    def submit(**kw):
        submits.append(kw["symbol"])
        return {"ok": True, "order": {"order_id": "synthetic-submission-only"}}

    result = paper_runner._consume_queued_intents_once(qdb=h.queue, eng=SimpleNamespace(db=h.paper, submit_order=submit))
    assert result["submitted"] == 0 and not submits
    [row] = h.intents("buy")
    assert row["status"] == "rejected"
    terminal = h.paper.get_state("paper_buy_terminal:paper_intent_" + row["intent_id"])
    assert json.loads(terminal)["state"] == "rejected"  # ledger fence precedes queue disposal


def pending_order(h, monkeypatch):
    from services.admin import config_editor
    from services.execution.paper_buy_policy import PAPER_BUY_CREATED_TS
    directory = setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    h.run(1)
    [row] = h.intents("buy")
    order = {**row, "order_id": "real-pending-order", "status": "new",
             "client_order_id": "paper_intent_" + row["intent_id"],
             "meta": {**row["meta"], PAPER_BUY_CREATED_TS: row["created_ts"]}}
    h.paper.insert_order(order)
    monkeypatch.setattr(config_editor, "load_user_yaml", lambda **kw: raw_config(h))
    return order, directory


def fill_parameters(order):
    from services.market_data.paper_snapshot_quote import read_paper_quote
    quote, reason = read_paper_quote("coinbase", "BTC/USD", clock=lambda: NOW)
    assert quote is not None, reason
    return dict(order=order, ts=NOW, price=100, qty=order["qty"], fee=4.975,
                fee_currency="USD", clock=lambda: NOW, snapshot_quote_guard=True,
                snapshot_quote=quote, snapshot_slippage_bps=0)


@pytest.mark.parametrize("loss", ["before_fill", "during_write"])
def test_fill_rechecks_selection_and_durably_fences_without_financial_writes(harness, monkeypatch, loss):
    from services.market_data.group_b_selection import weekly_name
    h = harness
    order, directory = pending_order(h, monkeypatch)
    path = directory / weekly_name(NOW)
    cash = h.paper.get_state("cash_quote")
    if loss == "before_fill":
        path.unlink()
    else:
        insert = h.paper._insert_fill_conn

        def lose_selection(con, row):
            result = insert(con, row)
            path.unlink()
            return result

        monkeypatch.setattr(h.paper, "_insert_fill_conn", lose_selection)
    result = h.paper.apply_fill(**fill_parameters(order))
    assert result["ok"] is False and result["reason"].startswith("group_b:")
    assert h.paper.get_state("cash_quote") == cash
    assert not h.paper.get_position("BTC/USD")
    assert not h.paper.list_fills_for_order(order["order_id"])
    assert h.paper.get_order_by_client_id(order["client_order_id"])["status"] == "rejected"
    assert json.loads(h.paper.get_state("paper_buy_terminal:" + order["client_order_id"]))["state"] == "rejected"


def test_committed_buy_receipt_survives_later_ranking_loss(harness, monkeypatch):
    from services.market_data.group_b_selection import weekly_name
    h = harness
    order, directory = pending_order(h, monkeypatch)
    kwargs = fill_parameters(order)
    assert h.paper.apply_fill(**kwargs)["ok"]
    cash = h.paper.get_state("cash_quote")
    (directory / weekly_name(NOW)).unlink()
    receipt = h.paper.apply_fill(**kwargs)
    assert receipt["ok"] and receipt["idempotent"]
    assert h.paper.get_state("cash_quote") == cash


def test_existing_order_submit_does_not_bypass_selection_guard(harness, monkeypatch):
    from services.market_data.group_b_selection import weekly_name
    from services.execution.paper_engine import PaperEngine
    h = harness
    order, directory = pending_order(h, monkeypatch)
    (directory / weekly_name(NOW)).unlink()
    engine = PaperEngine.__new__(PaperEngine)
    engine.db, engine.cfg, engine._clock = h.paper, {"group_b_guard": True}, lambda: NOW
    result = engine.submit_order(**{k: order[k] for k in (
        "client_order_id", "venue", "symbol", "side", "order_type", "qty", "limit_price", "strategy_id", "meta")})
    assert result["ok"] is False
    assert h.paper.get_order_by_client_id(order["client_order_id"])["status"] == "rejected"


@pytest.mark.parametrize("bad", ["mapped", "missing_guard"])
def test_marked_fill_cannot_bypass_canonical_quote_policy(harness, monkeypatch, bad):
    h = harness
    order, _ = pending_order(h, monkeypatch)
    kwargs = fill_parameters(order)
    if bad == "mapped":
        kwargs["snapshot_quote"].update(symbol_mapped="ETH/USD", ticker_symbol="ETH/USD")
    else:
        kwargs["snapshot_quote_guard"] = False
    cash = h.paper.get_state("cash_quote")
    result = h.paper.apply_fill(**kwargs)
    assert result["ok"] is False and result["unresolved"] is True
    assert h.paper.get_state("cash_quote") == cash
    assert not h.paper.list_fills_for_order(order["order_id"])


def test_consumer_checks_authority_without_blocking_on_its_own_pending_buy(harness, monkeypatch):
    from types import SimpleNamespace
    from services.execution import paper_runner
    h = harness
    setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    h.run(1)
    monkeypatch.setattr(paper_runner, "_now", lambda: NOW)

    async def decisions(rows):
        return [(r, SimpleNamespace(allowed=True)) for r in rows]

    monkeypatch.setattr(paper_runner, "_decide_batch", decisions)
    submissions = []

    def submit(**kw):
        submissions.append(kw)
        return {"ok": True, "order": {"order_id": "synthetic-submission-only"}}

    result = paper_runner._consume_queued_intents_once(qdb=h.queue, eng=SimpleNamespace(db=h.paper, submit_order=submit))
    assert result["submitted"] == 1 and len(submissions) == 1


def test_terminal_fence_still_blocks_fill_after_ranking_recovers(harness, monkeypatch):
    from services.market_data.group_b_selection import weekly_name
    h = harness
    order, directory = pending_order(h, monkeypatch)
    path = directory / weekly_name(NOW)
    original = path.read_bytes()
    path.unlink()
    receipt = h.paper.refuse_group_b_buy(order["client_order_id"], expected_order=order, now=NOW)
    assert receipt["state"] == "rejected"
    path.write_bytes(original)
    result = h.paper.apply_fill(**fill_parameters(order))
    assert result["ok"] is False
    assert not h.paper.list_fills_for_order(order["order_id"])


@pytest.mark.parametrize("boundary", ["quote", "ttl", "week"])
def test_authorization_io_cannot_push_fill_past_final_time_bounds(harness, monkeypatch, boundary):
    from services.execution import paper_weekly_slot
    from services.market_data.group_b_selection import instant
    from services.execution.paper_buy_policy import PAPER_BUY_CREATED_TS
    from storage import intent_queue_sqlite, paper_trading_sqlite
    h = harness
    order, _ = pending_order(h, monkeypatch)
    kwargs = fill_parameters(order)
    if boundary == "quote":
        before, after = NOW, "2026-11-09T00:06:06Z"
    elif boundary == "ttl":
        before, after = "2026-11-09T00:07:59Z", "2026-11-09T00:08:00Z"
    else:
        before, after = "2026-11-16T00:04:59Z", "2026-11-16T00:05:01Z"
        order["meta"][PAPER_BUY_CREATED_TS] = before
        with sqlite3.connect(paper_trading_sqlite.DB_PATH) as con:
            con.execute("UPDATE paper_orders SET meta_json=?", (json.dumps(order["meta"]),))
        with sqlite3.connect(intent_queue_sqlite.DB_PATH) as con:
            con.execute("UPDATE trade_intents SET created_ts=?", (before,))
    quote = kwargs["snapshot_quote"]
    quote["ts_ms"] = quote["snapshot_ts_ms"] = int(instant(before).timestamp() * 1000)
    clock, calls = [before], [0]
    actual = paper_weekly_slot.buy_selection_verdict

    def delayed(**kw):
        result = actual(**kw)
        calls[0] += 1
        if calls[0] == 2:
            clock[0] = after
        return result

    monkeypatch.setattr(paper_weekly_slot, "buy_selection_verdict", delayed)
    kwargs["clock"] = lambda: clock[0]
    cash = h.paper.get_state("cash_quote")
    result = h.paper.apply_fill(**kwargs)
    assert result["ok"] is False
    assert h.paper.get_state("cash_quote") == cash
    assert not h.paper.list_fills_for_order(order["order_id"])
    if boundary == "week":
        assert h.paper.get_order_by_client_id(order["client_order_id"])["status"] == "rejected"


def test_uncertain_fence_does_not_dispose_buy_or_abort_exit_batch(harness, monkeypatch):
    from types import SimpleNamespace
    from services.execution import paper_runner
    from services.market_data.group_b_selection import weekly_name
    from tests.test_paper_reconciler_recovery import _base_intent
    h = harness
    directory = setup_slot(h, monkeypatch, selection(("BTC/USD",)))
    h.run(1)
    (directory / weekly_name(NOW)).unlink()
    sell = {**_base_intent("independent-exit"), "side": "sell"}
    h.queue.upsert_intent(sell)
    monkeypatch.setattr(paper_runner, "_now", lambda: NOW)
    monkeypatch.setattr(h.paper, "refuse_group_b_buy", lambda *a, **kw: (_ for _ in ()).throw(sqlite3.OperationalError("synthetic write failure")))

    async def decisions(rows):
        return [(r, SimpleNamespace(allowed=True)) for r in rows]

    monkeypatch.setattr(paper_runner, "_decide_batch", decisions)
    submissions = []

    def submit(**kw):
        submissions.append(kw["side"])
        return {"ok": True, "order": {"order_id": "synthetic-submission-only"}}

    result = paper_runner._consume_queued_intents_once(qdb=h.queue, eng=SimpleNamespace(db=h.paper, submit_order=submit))
    assert submissions == ["sell"] and result["submitted"] == 1
    [buy] = h.intents("buy")
    assert buy["status"] == "submitting"
