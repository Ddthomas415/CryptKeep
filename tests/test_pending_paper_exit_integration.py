"""R12 offline real-loop/consumer/engine/SQLite integration, not service proof.

The imported harness bounds run_forever, denies network/subprocess access and
supports CBP_MULTISYMBOL_BEFORE_SOURCE for the saved pre-R12 runner. Only config,
router decisions, quote/safety inputs and alert delivery are synthetic. Ledger
fills and normal journal-before-terminal reconciliation remain real.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import importlib
import os
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from tests.test_runner_multi_symbol_integration import (
    PRICES,
    STRATEGY,
    SYMBOLS,
    VENUE,
    harness,  # noqa: F401 - pytest discovers the imported fixture.
)


BTC = SYMBOLS[0]
POLICY = "retry_until_filled_v1"
SUBMITTED_SOURCE_DIR = os.environ.get("CBP_R12_SUBMITTED_SOURCE_DIR")


class _PendingFlow:
    def __init__(self, h):
        self.h = h
        self.price = 96.0
        self.fresh = True
        self.quote_offset_ms = 0
        self.router_refusals = 0
        self.router_error = None
        self.attempts = []
        self.alerts = []
        self.alert_failure = None
        h.cfg.update(symbol=BTC, symbols=[BTC])
        h.consume = lambda: None
        h.stop = SimpleNamespace(turn=0)
        h.seed_holdings()

        import services.admin.config_editor as config_editor
        import services.alerts.alert_dispatcher as alert_dispatcher
        import services.config_loader as config_loader
        import services.strategies.evidence_logger as evidence_logger

        # Never inspect runtime config or dispatch an external notification.
        h.mp.setattr(config_editor, "load_user_yaml", lambda **_kw: {})
        h.mp.setattr(config_loader, "load_runtime_trading_config", lambda **_kw: {})
        h.mp.setattr(alert_dispatcher, "send_alert", self._alert)
        h.mp.setattr(evidence_logger, "_version_stamp", lambda strategy_id, **_kw: {
            "_strategy_id": strategy_id, "_stage": "offline_test", "_commit": "synthetic",
        })
        names = ("storage.execution_guard_store_sqlite", "storage.trade_journal_sqlite",
                     "services.execution.paper_exit_retry",
                     "services.execution.paper_engine", "services.execution.intent_reconciler",
                     "services.execution.paper_runner")
        for name in names:
            module = importlib.reload(importlib.import_module(name))
            if SUBMITTED_SOURCE_DIR and name.startswith("services.execution."):
                # Explicit trusted saved-source verification, confined to this
                # offline process; never replace production files on disk.
                saved = Path(SUBMITTED_SOURCE_DIR) / (name.replace(".", "__") + ".py.submitted")
                exec(compile(saved.read_bytes(), str(saved), "exec"), module.__dict__)
        self.engine_module = importlib.import_module("services.execution.paper_engine")
        self.consumer = importlib.import_module("services.execution.paper_runner")
        self.reconciler = importlib.import_module("services.execution.intent_reconciler")
        self.retry = importlib.import_module("services.execution.paper_exit_retry")
        self.journal_module = importlib.import_module("storage.trade_journal_sqlite")
        pe = self.engine_module
        h.mp.setattr(pe, "load_user_yaml", lambda: {"paper_trading": {
            "quote_currency": "USD", "starting_cash_quote": 100000.0,
            "fee_bps": 50.0, "slippage_bps": 0.0, "use_ccxt_fallback": False,
        }})
        h.mp.setattr(pe, "get_best_bid_ask_last", self._quote)
        h.mp.setattr(pe, "make_exchange", h._forbid_external)
        h.mp.setattr(pe, "is_snapshot_fresh", lambda: (
            self.fresh, None if self.fresh else "synthetic_stale_snapshot",
        ))
        h.mp.setattr(pe, "is_master_read_only", lambda: (False, {}))
        h.mp.setattr(pe, "check_market_quality", lambda _v, _s: {
            "ok": True, "price_used": self.price,
        })
        h.mp.setattr(pe, "load_gates", lambda: {})
        h.mp.setattr(pe, "should_allow_order", lambda *_a, **_kw: (True, "ok"))
        h.mp.setattr(self.consumer, "_decide_batch", self._decide_batch)
        self.eng = pe.PaperEngine()
        self.jdb = self.journal_module.TradeJournalSQLite()

    def _quote(self, _venue, _symbol):
        return {"ts_ms": int(time.time() * 1000) + self.quote_offset_ms, "bid": self.price,
                "ask": self.price, "last": self.price}

    def _alert(self, **kwargs):
        self.alerts.append(copy.deepcopy(kwargs))
        if self.alert_failure == "exception":
            raise OSError("synthetic alert transport failure")
        if self.alert_failure == "not-delivered":
            return {"ok": False, "reason": "synthetic_transport_failure"}
        return {"ok": True, "skipped": False}

    async def _decide_batch(self, intents):
        results = []
        for row in intents:
            self.attempts.append(copy.deepcopy(row))
            if self.router_error is not None:
                decision = self.router_error
            elif self.router_refusals:
                self.router_refusals -= 1
                decision = SimpleNamespace(allowed=False, reason="synthetic_first_refusal")
            else:
                decision = SimpleNamespace(allowed=True, reason="synthetic_allow")
            results.append((row, decision))
        return results

    def visit(self, turns=1):
        self.h.run(turns)

    def restart(self):
        self.h.reload_runner()
        self.h.state = self.h.runner.StrategyStateSQLite()
        self.h.queue = self.h.runner.IntentQueueSQLite()
        self.h.paper = self.h.runner.PaperTradingSQLite()
        self.eng = self.engine_module.PaperEngine()
        self.jdb = self.journal_module.TradeJournalSQLite()

    def consume(self):
        return self.consumer._consume_queued_intents_once(qdb=self.h.queue, eng=self.eng)

    def reconcile(self):
        return self.reconciler.reconcile_once(
            qdb=self.h.queue, pdb=self.eng.db, jdb=self.jdb, max_intents=100,
        )

    def cycle(self):
        consumed = self.consume()
        fills = self.eng.evaluate_open_orders()
        reconciled = self.reconcile()
        return consumed, fills, reconciled

    def trigger(self, kind="stop", *, cooldown=False):
        self.h.quotes[BTC] = [102.0 if kind == "trailing" else 96.0]
        self.price = self.h.quotes[BTC][0]
        if kind == "trailing":
            self.h.state.set(self.h.key("trailing_peak", BTC), "110")
        if cooldown:
            self.h.state.set(self.h.key("kill_remaining", BTC), "49")
        self.visit()
        rows = self.h.intents("sell")
        assert len(rows) == 1, "real runner must emit exactly one protective root"
        row = rows[0]
        assert row["meta"]["paper_exit_policy"] == POLICY
        assert row["meta"]["paper_exit_id"] == row["intent_id"]
        assert kind in row["meta"]["exit_reason"]
        return row

    def root(self, row):
        return self.h.queue.get_intent(row["intent_id"])

    def order(self, row):
        return self.eng.db.get_order_by_client_id("paper_intent_" + row["intent_id"])

    def events(self, row):
        return self.h.queue.list_paper_exit_events(row["intent_id"])

    def root_fills(self, row):
        order = self.order(row)
        return [] if order is None else self.eng.db.list_fills_for_order(order["order_id"])

    def bookkeeping(self):
        return {key: self.h.state.get(self.h.key(key, BTC))
                for key in ("loss_streak", "cum_pnl", "peak_pnl")}

    def manual_fill(self, *, side, qty, identity):
        result = self.eng.submit_order(
            client_order_id=identity, venue=VENUE, symbol=BTC, side=side,
            order_type="market", qty=qty,
        )
        assert result["ok"], result
        assert self.eng.evaluate_open_orders()["filled"] == 1
        return result["order"]

    def seed_exit(self, identity="limit-root", *, order_type="limit", limit_price=105.0,
                  created=None, tagged=True, strategy_id=STRATEGY):
        stamp = (created or datetime.now(timezone.utc)).isoformat()
        row = {
            "intent_id": identity, "created_ts": stamp, "ts": stamp,
            "source": "strategy", "strategy_id": strategy_id, "venue": VENUE,
            "symbol": BTC, "side": "sell", "action": "sell", "qty": 0.5,
            "order_type": order_type, "limit_price": limit_price, "status": "queued",
            "meta": ({"paper_exit_policy": POLICY, "paper_exit_id": identity}
                     if tagged else {}),
        }
        self.h.queue.upsert_intent(row)
        return row


@pytest.fixture
def pending(harness):
    return _PendingFlow(harness)


@pytest.mark.parametrize("kind", ["stop", "trailing"])
@pytest.mark.parametrize("blocker", ["cooldown", "refusal", "stale-quotes"])
def test_protective_exit_fills_under_each_blocker_without_new_signal(pending, kind, blocker):
    f = pending
    h = f.h
    f.router_refusals = int(blocker == "refusal")
    f.fresh = blocker != "stale-quotes"
    row = f.trigger(kind, cooldown=blocker == "cooldown")
    accounting = f.bookkeeping()
    before_cash = f.eng.cash_quote()
    first, fills, _ = f.cycle()
    assert first["queued_seen"] == 1
    if blocker != "cooldown":
        assert fills["filled"] == 0
        assert f.root(row)["status"] == "held"
        assert not f.root_fills(row)
        assert f.events(row)
        assert f.root(row)["last_error"]
        fetches, signals = len(h.fetches), len(h.signals)
        f.price = 112.0 if kind == "trailing" else 100.0
        h.quotes[BTC] = [f.price]  # The original trigger has recovered.
        f.fresh = True
        f.visit()
        assert len(h.fetches) == fetches, "pending recovery must precede quote fetching"
        assert len(h.signals) == signals
        assert f.root(row)["status"] == "queued"
        _, fills, _ = f.cycle()
    assert fills["filled"] == 1
    assert f.root(row)["status"] == "filled"
    assert len(h.intents("sell")) == 1
    assert not h.intents("buy")
    assert f.bookkeeping() == accounting
    assert h.paper.get_position(BTC)["qty"] == 0.0
    order = f.order(row)
    assert order["client_order_id"] == "paper_intent_" + row["intent_id"]
    assert order["order_type"] == row["order_type"]
    assert order["limit_price"] == row["limit_price"]
    actual = f.root_fills(row)
    assert len(actual) == 1
    assert actual[0]["qty"] == 0.5
    assert actual[0]["fee"] == pytest.approx(f.price * 0.5 * 0.005)
    assert f.eng.cash_quote() == pytest.approx(before_cash + f.price * 0.5 * 0.995)
    journal = [r for r in f.jdb.list_fills(limit=100) if r["intent_id"] == row["intent_id"]]
    assert len(journal) == 1
    assert journal[0]["fill_id"] == actual[0]["fill_id"]
    assert all(a["intent_id"] == row["intent_id"] for a in f.attempts)
    assert all(a["client_order_id"] == order["client_order_id"] for a in f.attempts)


def test_pending_exit_blocks_new_buys_and_bookkeeping_even_without_runner_quote(pending):
    f = pending
    f.router_refusals = 1
    row = f.trigger()
    f.cycle()
    assert f.root(row)["status"] == "held"
    accounting = f.bookkeeping()
    fetches, signals = len(f.h.fetches), len(f.h.signals)
    f.h.quotes[BTC] = [None]
    f.h.signal_action = "buy"
    f.visit(3)
    assert len(f.h.fetches) == fetches
    assert len(f.h.signals) == signals
    assert not f.h.intents("buy")
    assert len(f.h.intents("sell")) == 1
    assert f.bookkeeping() == accounting
    assert f.root(row)["status"] == "queued"
    f.price = 100.0
    f.cycle()
    assert f.root(row)["status"] == "filled"


@pytest.mark.parametrize("kind", ["stop", "trailing"])
def test_restart_after_claim_recovers_same_root_and_one_fill(pending, kind):
    f = pending
    row = f.trigger(kind)
    claimed = f.h.queue.claim_next_queued(limit=10)
    assert len(claimed) == 1
    assert f.root(row)["status"] == "submitting"
    client = claimed[0]["client_order_id"]
    accounting = f.bookkeeping()
    f.restart()
    f.h.quotes[BTC] = [None]
    f.visit()
    assert f.root(row)["status"] == "queued"
    assert f.root(row)["client_order_id"] == client
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert len(f.root_fills(row)) == 1
    assert f.bookkeeping() == accounting


@pytest.mark.parametrize("kind", ["stop", "trailing"])
def test_restart_after_fill_recovers_submission_then_journals_before_terminal(pending, kind):
    f = pending
    row = f.trigger(kind)
    assert f.consume()["submitted"] == 1
    assert f.eng.evaluate_open_orders()["filled"] == 1
    assert f.root(row)["status"] == "submitted"
    assert f.jdb.count() == 0
    cash, realized = f.eng.cash_quote(), f.eng.realized_pnl()
    old_fill = f.root_fills(row)[0]
    f.restart()
    f.h.quotes[BTC] = [None]
    f.visit()
    recovered = f.root(row)
    assert recovered["status"] == "submitted", "ledger recovery must not bypass journaling"
    assert recovered["linked_order_id"] == old_fill["order_id"]
    assert f.jdb.count() == 0
    f.reconcile()
    assert f.root(row)["status"] == "filled"
    assert f.jdb.count() == 1
    f.reconcile()
    assert f.jdb.count() == 1
    assert f.root_fills(row) == [old_fill]
    assert f.eng.cash_quote() == cash
    assert f.eng.realized_pnl() == realized
    assert f.h.paper.get_position(BTC)["qty"] == 0.0


@pytest.mark.parametrize("alias", [False, True], ids=["canonical-client", "different-client"])
def test_filled_root_replay_cannot_sell_replacement_holding(pending, alias):
    f = pending
    row = f.trigger()
    f.cycle()
    original = f.root_fills(row)
    assert len(original) == 1
    f.price = 100.0
    f.manual_fill(side="buy", qty=0.4, identity="replacement-holding")
    cash, realized = f.eng.cash_quote(), f.eng.realized_pnl()
    result = f.eng.submit_order(
        client_order_id=("alias-client" if alias else "paper_intent_" + row["intent_id"]),
        venue=VENUE, symbol=BTC, side="sell", order_type=row["order_type"],
        limit_price=row["limit_price"], qty=row["qty"], strategy_id=STRATEGY,
        meta=row["meta"],
    )
    assert not result.get("ok") or result.get("idempotent"), result
    assert f.eng.evaluate_open_orders()["filled"] == 0
    assert f.h.paper.get_position(BTC)["qty"] == 0.4
    assert f.eng.cash_quote() == cash
    assert f.eng.realized_pnl() == realized
    assert f.root_fills(row) == original


def test_other_exit_supersedes_pending_root_and_never_sells_new_holding(pending):
    f = pending
    f.router_refusals = 1
    row = f.trigger()
    f.cycle()
    assert f.root(row)["status"] == "held"
    f.price = 100.0
    f.manual_fill(side="sell", qty=0.5, identity="independent-exit")
    assert f.h.paper.get_position(BTC)["qty"] == 0.0
    attempts = len(f.attempts)
    f.restart()
    f.visit()
    assert f.root(row)["status"] == "superseded"
    assert len(f.attempts) == attempts
    assert not f.root_fills(row)
    f.manual_fill(side="buy", qty=0.4, identity="later-position")
    f.h.quotes[BTC] = [100.0]
    f.restart()
    f.visit(2)
    f.cycle()
    assert f.root(row)["status"] == "superseded"
    assert f.h.paper.get_position(BTC)["qty"] == 0.4
    assert not f.root_fills(row)
    assert len(f.attempts) == attempts


@pytest.mark.parametrize("current,expected", [(0.3, 0.3), (0.7, 0.5)])
def test_retry_never_exceeds_current_holding_or_original_exit_size(pending, current, expected):
    f = pending
    f.router_refusals = 1
    row = f.trigger()
    f.cycle()
    f.price = 100.0
    f.manual_fill(side="sell" if current < 0.5 else "buy", qty=0.2,
                  identity="independent-holding-change")
    assert f.h.paper.get_position(BTC)["qty"] == pytest.approx(current)
    f.visit()
    f.cycle()
    assert f.root(row)["status"] == "filled"
    fills = f.root_fills(row)
    assert len(fills) == 1
    assert fills[0]["qty"] == pytest.approx(expected)
    assert f.h.paper.get_position(BTC)["qty"] == pytest.approx(current - expected)


def test_retry_preserves_limit_type_price_and_identity_until_marketable(pending):
    f = pending
    row = f.seed_exit()
    f.price = 100.0
    f.router_refusals = 1
    f.cycle()
    assert f.root(row)["status"] == "held"
    f.visit()
    f.cycle()
    assert not f.root_fills(row)
    assert f.order(row)["status"] == "new"
    for _ in range(2):
        f.visit()
        f.cycle()
        assert not f.root_fills(row)
    f.price = 110.0
    f.visit()
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert len(f.root_fills(row)) == 1
    assert f.order(row)["order_type"] == "limit"
    assert f.order(row)["limit_price"] == 105.0
    assert all(a["intent_id"] == row["intent_id"] and a["order_type"] == "limit"
               and a["limit_price"] == 105.0 for a in f.attempts)
    events = f.events(row)
    assert any(e["event"] == "refused" for e in events)
    assert any(e["event"] == "retry" for e in events)
    assert [e["event_id"] for e in events] == sorted({e["event_id"] for e in events})


@pytest.mark.parametrize("stale_input", ["snapshot", "old-symbol-quote", "future-symbol-quote"])
def test_quote_staleness_after_submission_defers_fill_until_fresh(pending, stale_input):
    f = pending
    row = f.trigger()
    assert f.consume()["submitted"] == 1
    cash = f.eng.cash_quote()
    f.fresh = stale_input != "snapshot"
    f.quote_offset_ms = {"snapshot": 0, "old-symbol-quote": -6000,
                         "future-symbol-quote": 60000}[stale_input]
    assert f.eng.evaluate_open_orders()["filled"] == 0
    f.reconcile()
    assert not f.root_fills(row)
    assert f.root(row)["status"] not in ("filled", "superseded", "rejected")
    assert f.eng.cash_quote() == cash
    assert f.h.paper.get_position(BTC)["qty"] == 0.5
    f.fresh = True
    f.quote_offset_ms = 0
    f.price = 100.0
    f.visit()
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert len(f.root_fills(row)) == 1


@pytest.mark.parametrize("failure", ["exception", "not-delivered"])
def test_over_two_minutes_alert_failure_keeps_exit_and_allows_later_fill(pending, failure):
    f = pending
    created = datetime.now(timezone.utc)
    row = f.seed_exit("alert-root", order_type="market", limit_price=None, created=created)
    f.router_refusals = 1
    f.cycle()
    row = f.root(row)
    assert row["status"] == "held"
    before_events = f.events(row)
    f.retry.record_pending_exit_alert(f.h.queue, row, now=created + timedelta(seconds=119))
    assert not f.alerts
    f.alert_failure = failure
    f.retry.record_pending_exit_alert(f.h.queue, row, now=created + timedelta(seconds=121))
    assert len(f.alerts) == 1
    assert f.root(row)["status"] == "held"
    assert not f.root_fills(row)
    events = f.events(row)
    assert events[:len(before_events)] == before_events
    assert any(e["event"] in ("alert_error", "alert_result")
               for e in events[len(before_events):])
    assert f.h.queue.get_state("paper_exit_alert:" + row["intent_id"]) != "requested"
    f.alert_failure = None
    # Allow the dispatcher's failure backoff before checking a later acceptance.
    f.retry.record_pending_exit_alert(f.h.queue, row, now=created + timedelta(seconds=300))
    assert len(f.alerts) == 2
    assert f.h.queue.get_state("paper_exit_alert:" + row["intent_id"]) == "requested"
    f.retry.record_pending_exit_alert(f.h.queue, row, now=created + timedelta(seconds=301))
    assert len(f.alerts) == 2
    f.visit()
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert len(f.root_fills(row)) == 1


def test_ordinary_untagged_sell_keeps_terminal_refusal_without_retry(pending):
    f = pending
    row = f.seed_exit("ordinary-sell", order_type="market", limit_price=None, tagged=False)
    f.router_refusals = 1
    f.cycle()
    assert f.root(row)["status"] == "rejected"
    assert not f.h.queue.list_paper_exits(symbol=BTC)
    f.h.quotes[BTC] = [100.0]
    f.visit(2)
    f.cycle()
    assert f.root(row)["status"] == "rejected"
    assert len(f.attempts) == 1
    assert not f.root_fills(row)
    assert f.h.paper.get_position(BTC)["qty"] == 0.5


@pytest.mark.parametrize("kind", ["stop", "trailing"])
def test_exchange_rejection_after_order_creation_reuses_same_order(pending, kind):
    f = pending
    row = f.trigger(kind)
    accounting = f.bookkeeping()
    f.consume()
    original = f.order(row)
    f.eng.db.update_order_status(original["order_id"], "rejected", "synthetic_exchange_refusal")
    f.reconcile()
    assert f.root(row)["status"] == "held"
    f.price = 110.0
    f.visit()
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert f.order(row)["order_id"] == original["order_id"]
    assert len(f.root_fills(row)) == 1
    assert f.bookkeeping() == accounting


def test_submit_exception_after_committed_fill_recovers_one_fill_and_journal(pending, monkeypatch):
    f = pending
    row = f.trigger()
    original_submit = f.eng.submit_order

    def interrupted(**kwargs):
        result = original_submit(**kwargs)
        assert result["ok"]
        assert f.eng.evaluate_open_orders()["filled"] == 1
        raise RuntimeError("synthetic lost receipt after commit")

    monkeypatch.setattr(f.eng, "submit_order", interrupted)
    f.consume()
    assert f.root(row)["status"] == "held"
    receipt = f.root_fills(row)[0]
    f.restart()
    f.visit()
    f.reconcile()
    assert f.root(row)["status"] == "filled"
    assert f.root_fills(row) == [receipt]
    assert f.jdb.count() == 1


def test_original_exit_payload_is_immutable_even_before_first_claim(pending):
    f = pending
    row = f.seed_exit()
    frozen = f.root(row)
    changed = {**row, "order_type": "market", "limit_price": None, "qty": 10.0,
               "venue": "other", "symbol": SYMBOLS[1], "meta": {}}
    f.h.queue.upsert_intent(changed)
    after = f.root(row)
    for key in ("order_type", "limit_price", "qty", "venue", "symbol", "meta", "client_order_id"):
        assert after[key] == frozen[key]


def test_pending_exit_retries_when_signal_has_not_changed(pending):
    # Seed a tagged root so the before-runner failure proves missing recovery,
    # rather than merely absence of the new emission metadata.
    f = pending
    row = f.seed_exit("held-root", order_type="market", limit_price=None)
    f.router_refusals = 1
    f.cycle()
    assert f.root(row)["status"] == "held"
    f.h.quotes[BTC] = [100.0]
    f.visit()
    assert f.root(row)["status"] == "queued"
    f.cycle()
    assert f.root(row)["status"] == "filled"
    assert len(f.root_fills(row)) == 1


@pytest.mark.parametrize("linked", ["unrelated-buy", "filled-without-receipt"])
def test_reconciler_never_completes_root_from_unverified_link(pending, linked):
    f = pending
    row = f.trigger()
    if linked == "unrelated-buy":
        unrelated = f.manual_fill(side="buy", qty=0.1, identity="unrelated-filled-buy")
        order_id = unrelated["order_id"]
    else:
        f.consume()
        order = f.order(row)
        f.eng.db.update_order_status(order["order_id"], "filled", None)
        order_id = order["order_id"]
    f.h.queue.paper_exit_transition(row["intent_id"], "submitted", event="test_corrupt_link",
                                    linked_order_id=order_id)
    f.reconcile()
    assert f.root(row)["status"] == "held"
    assert f.jdb.count() == 0
    assert not f.root_fills(row)
    assert f.h.paper.get_position(BTC)["qty"] == pytest.approx(
        0.6 if linked == "unrelated-buy" else 0.5)


def test_optional_strategy_is_preserved_through_prepare_and_fill(pending):
    f = pending
    row = f.seed_exit("optional-strategy", order_type="market", limit_price=None, strategy_id=None)
    f.consume()
    order = f.order(row)
    assert order["strategy_id"] is None
    assert f.eng.evaluate_open_orders()["filled"] == 1
    f.reconcile()
    assert f.root(row)["status"] == "filled"


@pytest.mark.parametrize("holding_grows_after_route", [False, True])
def test_router_and_execution_share_bounded_attempt_size(pending, holding_grows_after_route):
    f = pending
    row = f.seed_exit("bounded-route", order_type="market", limit_price=None)
    f.manual_fill(side="sell", qty=0.2, identity="reduce-before-routing")
    routed = []

    async def size_sensitive(intents):
        assert len(intents) == 1
        routed.append(intents[0]["qty"])
        if holding_grows_after_route:
            f.manual_fill(side="buy", qty=0.4, identity="buy-after-routing")
        return [(it, SimpleNamespace(allowed=it["qty"] <= 0.3, reason="size_bound"))
                for it in intents]

    f.h.mp.setattr(f.consumer, "_decide_batch", size_sensitive)
    f.cycle()
    assert routed == [pytest.approx(0.3)]
    assert f.h.queue.get_intent(row["intent_id"])["qty"] == 0.5
    assert f.root(row)["status"] == "filled"
    assert f.root_fills(row)[0]["qty"] == pytest.approx(0.3)
    assert f.h.paper.get_position(BTC)["qty"] == pytest.approx(
        0.4 if holding_grows_after_route else 0.0)
