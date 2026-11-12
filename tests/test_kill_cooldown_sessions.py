"""Kill cooldown must expire across runner sessions and must not swallow entries.

Regression for the es_daily_trend_v1 paper campaign: a performance kill on
2026-07-09 persisted ``kill_until=51`` as an absolute loop number. The loop
counter restarts at 0 in every runner process, so loops 1-50 of every daily
session were blocked and the hold->buy edge was consumed while blocked.
"""
from __future__ import annotations

import pytest

from tests.test_strategy_runtime_runner import _reload_strategy_runner

KEY = "coinbase:BTC/USD:sma_200_trend"


def _setup(monkeypatch, tmp_path, *, signal):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    emitted: list[dict] = []

    class Queue:
        def list_intents(self, **kwargs):
            return list(emitted)

        def upsert_intent(self, row):
            emitted.append(dict(row))

    class Paper:
        def get_position(self, symbol):
            return {"qty": 0.0, "avg_price": 0.0, "symbol": symbol}

    monkeypatch.setattr(runner, "IntentQueueSQLite", Queue)
    monkeypatch.setattr(runner, "PaperTradingSQLite", Paper)
    monkeypatch.setattr(runner, "collect_runtime_rows", lambda **kw: ([], []))
    cfg = dict(
        enabled=True, strategy_id="sma_200_trend", strategy={"name": "sma_200_trend"},
        strategy_preset="es_daily_trend_v1", venue="coinbase", symbol="BTC/USD",
        fast_n=2, slow_n=4, min_bars=1, max_bars=20, loop_interval_sec=0.0, qty=0.5,
        order_type="market", allow_first_signal_trade=False, use_ccxt_fallback=False,
        max_tick_age_sec=5.0, position_aware=True, sell_full_position=True,
        signal_source="synthetic_mid_ohlcv", auto_select_best_venue=False,
        switch_only_when_blocked=True, venue_candidates=[],
    )
    monkeypatch.setattr(runner, "_cfg", lambda: dict(cfg))
    monkeypatch.setattr(runner, "_fetch_mid", lambda cfg: (100.0, 1))
    monkeypatch.setattr(runner, "_strategy_signal", lambda *a, **kw: dict(signal))
    monkeypatch.setattr(runner, "evaluate_strategy_exit_stack", lambda **kw: {"action": "hold"})
    return runner, emitted


def _run_session(monkeypatch, runner, *, loops):
    """Run one runner process for ``loops`` kill-gate evaluations.

    Blocked loops ``continue`` before the end-of-loop sleep, so iterations are
    counted at the gate. Each call starts a fresh process-local loop counter.
    """
    calls = {"gate": 0}
    if runner.STOP_FILE.exists():
        runner.STOP_FILE.unlink()
    real_gate = runner.should_block_symbol

    def gate(**kwargs):
        calls["gate"] += 1
        if calls["gate"] >= loops:
            runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            runner.STOP_FILE.write_text("stop")
        return real_gate(**kwargs)

    monkeypatch.setattr(runner, "should_block_symbol", gate)
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)
    runner.run_forever()
    monkeypatch.setattr(runner, "should_block_symbol", real_gate)


BUY = {"ok": True, "action": "buy", "signal": "long", "reason": "sma200:long:regime:trending"}
HOLD = {"ok": True, "action": "hold", "signal": "flat", "reason": "sma200:flat"}


def _legacy_lockout(runner, *, last_action="hold"):
    state = runner.StrategyStateSQLite()
    state.set(f"warmed:{KEY}", "1")
    state.set(f"last_action:{KEY}", last_action)
    state.set(f"kill_until:{KEY}", "51")  # absolute loop number from an earlier process
    return state


def test_legacy_kill_is_served_once_then_later_sessions_trade(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    state = _legacy_lockout(runner)

    _run_session(monkeypatch, runner, loops=63)
    assert emitted == []
    assert state.get(f"kill_until:{KEY}") == "0"
    assert state.get(f"kill_remaining:{KEY}") == "0"

    # Next daily session: signal turns long. Master blocks loops 1-50 again and
    # consumes this change; the cooldown must already be over.
    monkeypatch.setattr(runner, "_strategy_signal", lambda *a, **kw: dict(BUY))
    _run_session(monkeypatch, runner, loops=63)
    assert [row["side"] for row in emitted] == ["buy"]


def test_cooldown_remaining_is_carried_across_short_sessions(monkeypatch, tmp_path):
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    state = _legacy_lockout(runner)

    _run_session(monkeypatch, runner, loops=30)
    assert state.get(f"kill_remaining:{KEY}") == "19"  # 49 owed, 30 served
    _run_session(monkeypatch, runner, loops=30)
    assert state.get(f"kill_remaining:{KEY}") == "0"
    assert emitted == []


def test_entry_change_inside_cooldown_is_still_dropped(monkeypatch, tmp_path):
    """Unchanged from master: a change that arrives while blocked is not replayed."""
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)
    state = _legacy_lockout(runner)

    _run_session(monkeypatch, runner, loops=63)

    assert emitted == []
    assert state.get(f"last_action:{KEY}") == "buy"


def test_hold_seen_during_cooldown_then_buy_enters(monkeypatch, tmp_path):
    seq = iter([HOLD, HOLD, HOLD, BUY, BUY, BUY])
    runner, emitted = _setup(monkeypatch, tmp_path, signal=BUY)
    monkeypatch.setattr(runner, "_strategy_signal", lambda *a, **kw: dict(next(seq, BUY)))
    state = runner.StrategyStateSQLite()
    state.set(f"warmed:{KEY}", "1")
    state.set(f"last_action:{KEY}", "buy")
    state.set(f"last_emitted_action:{KEY}", "sell")
    state.set(f"kill_remaining:{KEY}", "3")

    _run_session(monkeypatch, runner, loops=6)

    assert [row["side"] for row in emitted] == ["buy"]


def test_third_losing_exit_arms_same_cooldown_as_before(monkeypatch, tmp_path):
    """In-process arm: 49 blocked loops (loops < armed_loop + 50), as on master."""
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    position = {"qty": 1.0}
    # Written-intent accounting requires actual durable queue evidence. The
    # virtual position transition below still does not represent a real fill.
    from storage.intent_queue_sqlite import IntentQueueSQLite
    from services.execution.paper_exit_accounting import PaperExitAccounting
    monkeypatch.setattr(runner, "PaperExitAccounting", PaperExitAccounting)

    class Paper:
        def get_position(self, symbol):
            return {"qty": position["qty"], "avg_price": 110.0, "symbol": symbol}

    class Queue(IntentQueueSQLite):
        def list_intents(self, **kwargs):
            return []

        def upsert_intent(self, row):
            super().upsert_intent(row)
            emitted.append(dict(row))
            if row["side"] == "sell":
                position["qty"] = 0.0

    monkeypatch.setattr(runner, "PaperTradingSQLite", Paper)
    monkeypatch.setattr(runner, "IntentQueueSQLite", Queue)
    state = runner.StrategyStateSQLite()
    state.set(f"warmed:{KEY}", "1")
    state.set(f"last_action:{KEY}", "buy")
    state.set(f"last_emitted_action:{KEY}", "buy")
    state.set(f"entry_price:{KEY}", "110.0")
    state.set(f"loss_streak:{KEY}", "2")

    calls = {"signal": 0}

    def signal(*args, **kwargs):
        calls["signal"] += 1
        return dict(HOLD) if calls["signal"] <= 3 else dict(BUY)

    monkeypatch.setattr(runner, "_strategy_signal", signal)
    gates: list[bool] = []
    real_gate = runner.should_block_symbol

    def gate(**kwargs):
        out = real_gate(**kwargs)
        gates.append(bool(out["ok"]))
        if len(gates) >= 70:
            runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            runner.STOP_FILE.write_text("stop")
        return out

    monkeypatch.setattr(runner, "should_block_symbol", gate)
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)
    runner.run_forever()

    assert [row["side"] for row in emitted] == ["sell"]
    assert gates.count(False) == 49
    assert state.get(f"loss_streak:{KEY}") == "3"
    assert state.get(f"kill_remaining:{KEY}") == "0"


def test_fifth_risk_block_arms_same_cooldown_as_before(monkeypatch, tmp_path):
    """Risk-block arm: 19 blocked loops (loops < armed_loop + 20), as on master."""
    runner, emitted = _setup(monkeypatch, tmp_path, signal=HOLD)
    calls = {"signal": 0, "risk": 0}

    def signal(*args, **kwargs):
        calls["signal"] += 1
        return dict(BUY) if calls["signal"] % 2 == 0 else dict(HOLD)

    def blocked_entry(**kwargs):
        calls["risk"] += 1
        if calls["risk"] >= 5:
            runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            runner.STOP_FILE.write_text("stop")
        return {"ok": False, "reason": "test_block"}

    monkeypatch.setattr(runner, "_strategy_signal", signal)
    monkeypatch.setattr(runner, "evaluate_entry", blocked_entry)
    monkeypatch.setattr(runner.time, "sleep", lambda _seconds: None)
    state = runner.StrategyStateSQLite()
    state.set(f"warmed:{KEY}", "1")
    state.set(f"last_action:{KEY}", "hold")
    if runner.STOP_FILE.exists():
        runner.STOP_FILE.unlink()

    runner.run_forever()

    assert emitted == []
    assert calls["risk"] == 5
    assert state.get(f"risk_block_count:{KEY}") == "5"
    assert state.get(f"kill_remaining:{KEY}") == "19"


@pytest.mark.parametrize("legacy, expected", [("51", 49), ("5050", 49), ("999999999", 49), ("7", 6), ("1", 0), ("-5", 0), ("0", 0), ("", 0)])
def test_legacy_value_is_capped_at_longest_configured_cooldown(monkeypatch, tmp_path, legacy, expected):
    runner, _ = _setup(monkeypatch, tmp_path, signal=HOLD)
    state = runner.StrategyStateSQLite()
    state.set(f"kill_until:{KEY}", legacy)

    out = runner._kill_remaining_loops(
        state, f"kill_remaining:{KEY}", f"kill_until:{KEY}", max_cooldown_loops=50
    )

    assert out == expected


@pytest.mark.parametrize("stored, expected", [("999999", 49), ("50", 49), ("49", 49), ("12", 12), ("-4", 0)])
def test_stored_remaining_is_capped_at_longest_configured_cooldown(monkeypatch, tmp_path, stored, expected):
    runner, _ = _setup(monkeypatch, tmp_path, signal=HOLD)
    state = runner.StrategyStateSQLite()
    state.set(f"kill_remaining:{KEY}", stored)

    out = runner._kill_remaining_loops(
        state, f"kill_remaining:{KEY}", f"kill_until:{KEY}", max_cooldown_loops=50
    )

    assert out == expected
    assert int(state.get(f"kill_remaining:{KEY}")) == (expected if stored != "-4" else -4)


def test_interrupted_legacy_conversion_repeats_instead_of_dropping_block(monkeypatch, tmp_path):
    runner, _ = _setup(monkeypatch, tmp_path, signal=HOLD)
    state = runner.StrategyStateSQLite()
    # Count already written, legacy value not yet cleared, some loops served.
    state.set(f"kill_remaining:{KEY}", "30")
    state.set(f"kill_until:{KEY}", "51")

    out = runner._kill_remaining_loops(
        state, f"kill_remaining:{KEY}", f"kill_until:{KEY}", max_cooldown_loops=50
    )

    assert out == 49
    assert state.get(f"kill_remaining:{KEY}") == "49"
    assert state.get(f"kill_until:{KEY}") == "0"


def test_unreadable_kill_state_does_not_open_the_gate(monkeypatch, tmp_path):
    runner, _ = _setup(monkeypatch, tmp_path, signal=HOLD)

    class Locked:
        def get(self, key):
            raise RuntimeError("database is locked")

    with pytest.raises(RuntimeError):
        runner._kill_remaining_loops(Locked(), "a", "b", max_cooldown_loops=50)

    state = runner.StrategyStateSQLite()
    state.set(f"kill_until:{KEY}", "garbage")
    with pytest.raises(ValueError):
        runner._kill_remaining_loops(
            state, f"kill_remaining:{KEY}", f"kill_until:{KEY}", max_cooldown_loops=50
        )
