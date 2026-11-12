"""R1 offline integration: real runner, temporary SQLite and real paper fills.

Reuse the multi-symbol harness's bounded stop, denied network and saved-source
override (CBP_MULTISYMBOL_BEFORE_SOURCE). Prices, config and safety inputs are
synthetic; this does not certify a router, service, runtime config or R12 retry.
"""
from __future__ import annotations

import importlib
import time

import pytest

from tests.test_runner_multi_symbol_integration import (
    PRICES,
    STRATEGY,
    SYMBOLS,
    TS,
    VENUE,
    harness,  # noqa: F401 - pytest discovers the imported fixture.
)


BTC = SYMBOLS[0]


def _single_symbol(h):
    h.cfg.update(symbol=BTC, symbols=[BTC])


def _restart(h):
    h.reload_runner()
    h.state = h.runner.StrategyStateSQLite()
    h.queue = h.runner.IntentQueueSQLite()
    h.paper = h.runner.PaperTradingSQLite()


def _remaining(h, symbol=BTC):
    return int(h.state.get(h.key("kill_remaining", symbol)) or 0)


def _arm(h, count=49, *, legacy=0, symbol=BTC):
    h.state.set(h.key("kill_remaining", symbol), str(count))
    h.state.set(h.key("kill_until", symbol), str(legacy))


def _protective_setup(h, *, trailing=False):
    _single_symbol(h)
    h.seed_holdings()
    h.quotes[BTC] = [102.0 if trailing else 96.0]
    if trailing:
        h.state.set(h.key("trailing_peak", BTC), "110")
    _arm(h, legacy=1_000_000)
    h.consume = lambda: None


def _queue_row(intent_id, *, symbol=BTC, status="queued", source="strategy",
               created_ts=TS):
    return {
        "intent_id": intent_id, "created_ts": created_ts, "ts": created_ts,
        "source": source, "strategy_id": STRATEGY, "venue": VENUE,
        "symbol": symbol, "side": "buy", "action": "buy",
        "order_type": "market", "qty": 0.1, "status": status,
        "meta": {"reference_price": PRICES[symbol]},
    }


def _assert_exit_was_evaluated(h):
    assert h.fetches == [(1, BTC)]
    assert len(h.exit_checks) == 1
    assert h.exit_checks[0][1] == BTC
    assert h.exit_checks[0][2]["qty"] == 0.5


@pytest.mark.parametrize("cause,count,sessions", [
    ("performance", 49, (7, 13, 29)),
    ("risk", 19, (4, 6, 9)),
])
def test_armed_cooldown_expires_across_short_restart_sessions(
    harness, cause, count, sessions,
):
    h = harness
    _single_symbol(h)
    if cause == "performance":
        h.seed_holdings()
        h.state.set(h.key("loss_streak", BTC), "2")
        h.quotes[BTC] = [96.0]
    else:
        h.state.set(h.key("risk_block_count", BTC), "4")
        h.signal_action = "buy"
        h.mp.setattr(h.runner, "evaluate_entry", lambda **_kw: {
            "ok": False, "reason": "synthetic_risk_denial",
        })
    h.run(1)
    assert _remaining(h) == count
    assert any(row.get("note") == "kill_triggered_" + (
        "performance" if cause == "performance" else "risk_blocks"
    ) for row in h.statuses)
    if cause == "performance":
        assert len(h.intents("sell")) == 1
        assert h.paper.get_position(BTC)["qty"] == 0.0

    h.signal_action = "hold"
    owed = count
    for length in sessions:
        _restart(h)
        start = len(h.statuses)
        h.run(length)
        owed -= length
        assert _remaining(h) == owed
        assert sum(r.get("note") == "kill_cooldown"
                   for r in h.statuses[start:]) == length
        assert not h.intents("buy")

    _restart(h)
    h.signal_action = "buy"
    h.run(1)
    assert len(h.intents("buy")) == 1
    assert h.intents("buy")[0]["status"] == "filled"


def test_three_symbol_remaining_counts_decrement_only_on_own_visit(harness):
    h = harness
    for symbol, count in zip(SYMBOLS, (2, 4, 6)):
        _arm(h, count, symbol=symbol)
    h.run(4)
    assert h.fetches == [(1, BTC), (2, SYMBOLS[1]), (3, SYMBOLS[2]), (4, BTC)]
    assert [_remaining(h, s) for s in SYMBOLS] == [0, 3, 5]
    _restart(h)
    h.run(3)
    assert [_remaining(h, s) for s in SYMBOLS] == [0, 2, 4]
    _restart(h)
    h.signal_action = "buy"
    h.run(3)
    assert [r["symbol"] for r in h.intents("buy")] == [BTC]
    assert [_remaining(h, s) for s in SYMBOLS] == [0, 1, 3]


@pytest.mark.parametrize("legacy", [1, 7, 50, 1_000_000])
def test_legacy_absolute_count_is_capped_cleared_and_persisted(harness, legacy):
    h = harness
    _single_symbol(h)
    h.state.set(h.key("kill_until", BTC), str(legacy))
    h.run(1)
    expected = max(0, min(49, legacy - 1) - 1)
    assert h.state.get(h.key("kill_until", BTC)) == "0"
    assert _remaining(h) == expected
    if expected:
        assert h.state.get(h.key("kill_remaining", BTC)) == str(expected)
    _restart(h)
    h.run(1)
    assert _remaining(h) == max(0, expected - 1)


def test_persisted_count_is_capped_before_decrement(harness):
    h = harness
    _single_symbol(h)
    _arm(h, 1_000_000)
    h.run(1)
    assert _remaining(h) == 48
    _restart(h)
    h.run(1)
    assert _remaining(h) == 47


def _paper_engine_consumer(h):
    # Only the external safety/config/quote inputs are replaced. Submission,
    # position bounds, fill accounting, fees and queue transitions stay real.
    import storage.execution_guard_store_sqlite as guard_store
    import services.execution.paper_engine as paper_engine
    import services.strategies.evidence_logger as evidence_logger

    importlib.reload(guard_store)
    importlib.reload(paper_engine)
    # Version discovery shells out to Git; external process access stays denied.
    h.mp.setattr(evidence_logger, "_version_stamp", lambda strategy_id, **_kw: {
        "_strategy_id": strategy_id, "_stage": "offline_test", "_commit": "synthetic",
    })
    h.mp.setattr(paper_engine, "load_user_yaml", lambda: {"paper_trading": {
        "quote_currency": "USD", "starting_cash_quote": 100000.0,
        "fee_bps": 50.0, "slippage_bps": 0.0,
        "use_ccxt_fallback": False,
    }})

    def quote(_venue, symbol):
        sequence = h.quotes.get(symbol, [PRICES[symbol]])
        index = max(0, h.visits.get(symbol, 1) - 1)
        price = sequence[min(index, len(sequence) - 1)]
        return {"ts_ms": int(time.time() * 1000),
                "bid": price, "ask": price, "last": price}

    h.mp.setattr(paper_engine, "get_best_bid_ask_last", quote)
    h.mp.setattr(paper_engine, "make_exchange", h._forbid_external)
    h.mp.setattr(paper_engine, "is_snapshot_fresh", lambda: (True, None))
    h.mp.setattr(paper_engine, "is_master_read_only", lambda: (False, {}))
    h.mp.setattr(paper_engine, "check_market_quality", lambda venue, symbol: {
        "ok": True, "price_used": quote(venue, symbol)["last"],
    })
    h.mp.setattr(paper_engine, "load_gates", lambda: {})
    h.mp.setattr(paper_engine, "should_allow_order", lambda *_a, **_kw: (True, "ok"))
    eng = paper_engine.PaperEngine()
    assert any(p["symbol"] == BTC and p["qty"] == 0.5
               for p in eng.db.list_positions())
    cycles = []

    def consume():
        for row in h.queue.claim_next_queued(limit=100):
            assert h.queue.get_intent(row["intent_id"])["status"] == "submitting"
            result = eng.submit_order(
                client_order_id=row["client_order_id"], venue=row["venue"],
                symbol=row["symbol"], side=row["side"],
                order_type=row["order_type"], qty=row["qty"],
                strategy_id=row["strategy_id"], meta=row["meta"],
            )
            assert result["ok"], result
            order = result["order"]
            assert h.queue.update_status(
                row["intent_id"], "submitted", linked_order_id=order["order_id"],
            )
            assert h.queue.get_intent(row["intent_id"])["status"] == "submitted"
            cycle = eng.evaluate_open_orders()
            cycles.append(cycle)
            assert cycle["filled"] == 1 and cycle["rejected"] == 0, cycle
            assert eng.db.get_order_by_client_id(row["client_order_id"])["status"] == "filled"
            assert h.queue.update_status(row["intent_id"], "filled")

    h.consume = consume
    return eng, cycles


@pytest.mark.parametrize("trailing", [False, True], ids=["stop", "trailing"])
@pytest.mark.parametrize("full,configured,expected", [
    (True, 2.0, 0.5), (False, 0.2, 0.2),
], ids=["full-position-ignores-configured-oversize", "configured-partial-no-resize"])
def test_protective_exit_during_cooldown_reaches_real_paper_fill_and_fees(
    harness, trailing, full, configured, expected,
):
    h = harness
    _protective_setup(h, trailing=trailing)
    h.cfg.update(sell_full_position=full, qty=configured)
    eng, cycles = _paper_engine_consumer(h)
    before_cash = eng.cash_quote()
    before_realized = eng.realized_pnl()
    h.run(1)
    _assert_exit_was_evaluated(h)
    rows = h.intents("sell")
    assert len(rows) == 1
    row = rows[0]
    assert row["qty"] == expected
    assert row["status"] == "filled"
    assert ("trailing" if trailing else "stop") in row["meta"]["exit_reason"]
    assert len(cycles) == 1
    fills = eng.db.list_fills_for_order(row["linked_order_id"])
    assert len(fills) == 1
    fill = fills[0]
    price = h.quotes[BTC][0]
    fee = price * expected * 0.005
    assert fill["price"] == pytest.approx(price)
    assert fill["qty"] == expected
    assert fill["fee"] == pytest.approx(fee)
    assert fill["fee_currency"] == "USD"
    assert eng.cash_quote() == pytest.approx(before_cash + price * expected - fee)
    assert eng.realized_pnl() == pytest.approx(
        before_realized + (price - PRICES[BTC]) * expected - fee,
    )
    assert eng.db.get_position(BTC)["qty"] == pytest.approx(0.5 - expected)
    assert _remaining(h) == 48
    assert h.state.get(h.key("kill_until", BTC)) == "0"


@pytest.mark.parametrize("status", ["queued", "submitting", "submitted", "held"])
@pytest.mark.parametrize("closed_rows", [0, 205], ids=["recent", "older-than-200"])
def test_every_inflight_status_blocks_cooldown_exit_without_row_limit(
    harness, status, closed_rows,
):
    h = harness
    _protective_setup(h)
    h.queue.upsert_intent(_queue_row("old-open", status=status,
                                   created_ts="2020-01-01T00:00:00+00:00"))
    for index in range(closed_rows):
        h.queue.upsert_intent(_queue_row(f"closed-{index}", status="filled"))
    if closed_rows:
        assert all(r["intent_id"] != "old-open" for r in h.queue.list_intents(limit=200))
    h.run(1)
    _assert_exit_was_evaluated(h)
    assert not h.intents("sell")
    assert h.queue.get_intent("old-open")["status"] == status
    assert _remaining(h) == 48
    assert h.state.get(h.key("loss_streak", BTC)) is None
    assert h.paper.get_position(BTC)["qty"] == 0.5


@pytest.mark.parametrize("blocker", ["other-symbol", "manual-source", "terminal"])
def test_unrelated_or_terminal_rows_do_not_block_protective_exit(harness, blocker):
    h = harness
    _protective_setup(h)
    row = _queue_row("not-a-blocker")
    if blocker == "other-symbol":
        row["symbol"] = SYMBOLS[1]
    elif blocker == "manual-source":
        row["source"] = "manual"
    else:
        row["status"] = "filled"
    h.queue.upsert_intent(row)
    h.run(1)
    _assert_exit_was_evaluated(h)
    assert len(h.intents("sell")) == 1
    assert h.intents("sell")[0]["qty"] == 0.5
    assert _remaining(h) == 48


def test_unreadable_queue_fails_closed_before_exit_bookkeeping(harness):
    h = harness
    _protective_setup(h)
    reads = []

    def unreadable(*_a, **_kw):
        reads.append(True)
        raise OSError("injected queue read failure")

    # Cover either lookup path without assuming the implementation helper name.
    cls = h.runner.IntentQueueSQLite
    real_list = cls.list_intents
    h.mp.setattr(cls, "list_intents", unreadable)
    h.mp.setattr(cls, "has_open_strategy_intent", unreadable, raising=False)
    h.run(1)
    _assert_exit_was_evaluated(h)
    assert reads
    assert not [r for r in real_list(h.queue, limit=100) if r["side"] == "sell"]
    assert h.state.get(h.key("loss_streak", BTC)) is None
    assert h.paper.get_position(BTC)["qty"] == 0.5
    assert _remaining(h) == 48


def test_repeated_sell_latch_blocks_exit_without_retry_or_bookkeeping(harness):
    h = harness
    _protective_setup(h)
    h.state.set(h.key("last_emitted_action", BTC), "sell")
    h.run(2)
    assert len(h.exit_checks) == 2
    assert not h.intents("sell")
    assert h.state.get(h.key("loss_streak", BTC)) is None
    assert h.state.get(h.key("last_emitted_action", BTC)) == "sell"
    assert h.paper.get_position(BTC)["qty"] == 0.5
    assert _remaining(h) == 47


@pytest.mark.parametrize("qty", [0.0, -0.1, 0.500001, float("nan"),
                                  float("inf"), -float("inf"), True, False])
def test_unsafe_configured_sell_quantity_is_blocked_not_resized(harness, qty):
    h = harness
    _protective_setup(h)
    h.cfg.update(sell_full_position=False, qty=qty)
    h.run(1)
    _assert_exit_was_evaluated(h)
    assert not h.intents("sell")
    assert h.paper.get_position(BTC)["qty"] == 0.5
    assert h.state.get(h.key("loss_streak", BTC)) is None
    assert _remaining(h) == 48


@pytest.mark.parametrize("position_aware", [True, False])
def test_sell_without_holding_cannot_bypass_cooldown(harness, position_aware):
    h = harness
    _single_symbol(h)
    _arm(h, legacy=1_000_000)
    h.cfg["position_aware"] = position_aware
    h.signal_action = "sell"
    h.consume = lambda: None
    h.run(1)
    assert h.fetches == [(1, BTC)]
    assert not h.intents("sell")
    assert _remaining(h) == 48


@pytest.mark.parametrize("held", [False, True])
def test_buy_or_add_remains_blocked_while_count_decrements(harness, held):
    h = harness
    _single_symbol(h)
    if held:
        h.seed_holdings()
    h.cfg["position_aware"] = False
    h.signal_action = "buy"
    _arm(h, legacy=1_000_000)
    h.run(2)
    assert not h.intents("buy")
    assert _remaining(h) == 47
