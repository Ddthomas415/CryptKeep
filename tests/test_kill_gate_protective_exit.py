"""A kill cooldown blocks new exposure; it must not block closing a long."""
from __future__ import annotations

import pytest
import sqlite3

from tests.test_kill_cooldown_sessions import BUY, HOLD, KEY, _run_session, _setup


@pytest.mark.parametrize("status", ["queued", "submitted"])
def test_pending_intent_beyond_recent_history_is_found(monkeypatch, tmp_path, status):
    from storage import intent_queue_sqlite as queue_module

    path = tmp_path / "queue.sqlite"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE trade_intents (source TEXT, symbol TEXT, status TEXT, created_ts TEXT)")
    # Minimal schema isolates the existence query from queue lifecycle writes.
    with sqlite3.connect(path) as con:
        con.executemany(
            "INSERT INTO trade_intents(source, symbol, status, created_ts) VALUES (?, ?, ?, ?)",
            [("strategy", "ETH/USD", "filled", "2026-10-02")] * 250
            + [("strategy", "BTC/USD", status, "2026-10-01")],
        )
    monkeypatch.setattr(queue_module, "_connect", lambda: sqlite3.connect(path))
    queue = object.__new__(queue_module.IntentQueueSQLite)
    assert queue.has_open_strategy_intent("BTC/USD")
    assert not queue.has_open_strategy_intent("ETH/USD")


def _hold_long(monkeypatch, runner, emitted, *, qty=1.0, fills=True):
    position = {"qty": qty}

    class Paper:
        def get_position(self, symbol):
            return {"qty": position["qty"], "avg_price": 100.0, "symbol": symbol}

    class Queue:
        def has_open_strategy_intent(self, symbol):
            return False

        def list_intents(self, **kwargs):
            return []

        def upsert_intent(self, row):
            emitted.append(dict(row))
            if fills and row["side"] == "sell":
                position["qty"] = 0.0

    monkeypatch.setattr(runner, "PaperTradingSQLite", Paper)
    monkeypatch.setattr(runner, "IntentQueueSQLite", Queue)
    return position


def _cooldown(runner, *, last_action, remaining="30"):
    state = runner.StrategyStateSQLite()
    state.set(f"warmed:{KEY}", "1")
    state.set(f"last_action:{KEY}", last_action)
    state.set(f"last_emitted_action:{KEY}", "buy")
    state.set(f"entry_price:{KEY}", "100.0")
    state.set(f"kill_remaining:{KEY}", remaining)
    return state


def test_flat_signal_closes_long_during_cooldown(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    _hold_long(monkeypatch, runner, emitted, qty=0.75)
    state = _cooldown(runner, last_action="buy")

    _run_session(monkeypatch, runner, loops=5)

    assert [(row["side"], row["qty"]) for row in emitted] == [("sell", 0.75)]
    assert int(state.get(f"kill_remaining:{KEY}")) > 0


def test_exit_stack_closes_long_during_cooldown(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)
    _hold_long(monkeypatch, runner, emitted)
    _cooldown(runner, last_action="buy")
    monkeypatch.setattr(
        runner,
        "evaluate_strategy_exit_stack",
        lambda **kw: {"action": "exit", "reason": "strategy_exit:sma_200_trend:stop_loss", "stack_rule": "stop_loss"},
    )

    _run_session(monkeypatch, runner, loops=5)

    assert [row["side"] for row in emitted] == ["sell"]


def test_unfilled_exit_is_not_repeated_during_cooldown(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    _hold_long(monkeypatch, runner, emitted, fills=False)
    _cooldown(runner, last_action="buy")

    _run_session(monkeypatch, runner, loops=12)

    assert [row["side"] for row in emitted] == ["sell"]


def test_cooldown_still_counts_down_on_exit_loops(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    _hold_long(monkeypatch, runner, emitted, fills=False)
    state = _cooldown(runner, last_action="sell", remaining="4")
    state.set(f"last_emitted_action:{KEY}", "sell")

    _run_session(monkeypatch, runner, loops=3)

    assert emitted == []
    assert state.get(f"kill_remaining:{KEY}") == "1"
    assert state.get(f"loss_streak:{KEY}") in (None, "0")


def test_entry_is_still_blocked_while_flat_during_cooldown(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)
    state = _cooldown(runner, last_action="hold", remaining="30")
    state.set(f"last_emitted_action:{KEY}", "hold")

    _run_session(monkeypatch, runner, loops=20)

    assert emitted == []
    assert state.get(f"kill_remaining:{KEY}") == "10"


def test_sell_without_a_position_is_still_blocked_during_cooldown(monkeypatch, tmp_path):
    sell = {"ok": True, "action": "sell", "signal": "flat", "reason": "test:sell"}
    runner, emitted = _setup(monkeypatch, tmp_path, signal=sell)
    cfg = runner._cfg()
    cfg["position_aware"] = False
    monkeypatch.setattr(runner, "_cfg", lambda: dict(cfg))
    state = _cooldown(runner, last_action="hold", remaining="30")
    state.set(f"last_emitted_action:{KEY}", "hold")

    _run_session(monkeypatch, runner, loops=10)

    assert emitted == []


def test_adding_to_a_long_is_still_blocked_during_cooldown(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)
    _hold_long(monkeypatch, runner, emitted)
    cfg = runner._cfg()
    cfg["position_aware"] = False
    monkeypatch.setattr(runner, "_cfg", lambda: dict(cfg))
    # Scaling and risk checks would allow the add, so only the kill gate stops it.
    monkeypatch.setattr(runner, "evaluate_scale_in", lambda **kw: {"is_scale": True, "ok": True})
    monkeypatch.setattr(runner, "evaluate_entry", lambda **kw: {"ok": True})
    state = _cooldown(runner, last_action="hold", remaining="30")
    state.set(f"last_emitted_action:{KEY}", "hold")

    _run_session(monkeypatch, runner, loops=10)

    assert emitted == []
    assert state.get(f"kill_remaining:{KEY}") == "20"


@pytest.mark.parametrize("intent_listing", ["open", "error"])
def test_exit_blocked_by_open_or_unknown_intent_does_not_repeat_bookkeeping(monkeypatch, tmp_path, intent_listing):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)

    class Paper:
        def get_position(self, symbol):
            return {"qty": 1.0, "avg_price": 100.0, "symbol": symbol}

    class Queue:
        def has_open_strategy_intent(self, symbol):
            if intent_listing == "error":
                raise RuntimeError("queue unavailable")
            return True

        def list_intents(self, **kwargs):
            if intent_listing == "error":
                raise RuntimeError("queue unavailable")
            return [{"source": "strategy", "symbol": "BTC/USD", "status": "queued"}]

        def upsert_intent(self, row):
            emitted.append(dict(row))

    monkeypatch.setattr(runner, "PaperTradingSQLite", Paper)
    monkeypatch.setattr(runner, "IntentQueueSQLite", Queue)
    monkeypatch.setattr(runner, "_fetch_mid", lambda cfg: (90.0, 1))
    monkeypatch.setattr(
        runner,
        "evaluate_strategy_exit_stack",
        lambda **kw: {"action": "exit", "reason": "strategy_exit:sma_200_trend:stop_loss", "stack_rule": "stop_loss"},
    )
    state = _cooldown(runner, last_action="buy", remaining="10")

    _run_session(monkeypatch, runner, loops=6)

    assert emitted == []
    assert state.get(f"loss_streak:{KEY}") in (None, "0")
    assert state.get(f"cum_pnl:{KEY}") in (None, "0", "0.0")
    assert state.get(f"kill_remaining:{KEY}") == "4"


@pytest.mark.parametrize(
    "status, is_open",
    [("queued", True), ("submitting", True), ("submitted", True), ("held", True),
     ("filled", False), ("canceled", False), ("rejected", False), ("error", False)],
)
def test_open_intent_lookup_covers_every_in_flight_status(monkeypatch, tmp_path, status, is_open):
    from storage import intent_queue_sqlite as queue_module

    path = tmp_path / "queue.sqlite"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE trade_intents (source TEXT, symbol TEXT, status TEXT, created_ts TEXT)")
        con.execute(
            "INSERT INTO trade_intents(source, symbol, status, created_ts) VALUES (?, ?, ?, ?)",
            ("strategy", "BTC/USD", status, "2026-10-01"),
        )
    monkeypatch.setattr(queue_module, "_connect", lambda: sqlite3.connect(path))
    queue = object.__new__(queue_module.IntentQueueSQLite)

    assert queue.has_open_strategy_intent("BTC/USD") is is_open
