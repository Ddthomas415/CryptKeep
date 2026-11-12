"""Offline runner/SQLite integration, not a production consumer lifecycle test.

CBP_MULTISYMBOL_BEFORE_SOURCE selects saved source for the identical harness.
Only inputs and observation/fault hooks are synthetic; run_forever, exit controls,
queue persistence and paper fill accounting execute their real implementations.
"""
from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

import pytest


SYMBOLS = ("BTC/USD", "ETH/USD", "SOL/USD")
PRICES = dict(zip(SYMBOLS, (100.0, 1000.0, 10.0)))
STRATEGY = "breakout_donchian"
VENUE = "coinbase"
TS = "2026-11-03T00:00:00+00:00"
ROOT = Path(__file__).resolve().parents[1]


class _BoundedStop:
    """Count outer stop checks, independently of quote success and sleep calls."""

    def __init__(self, path, limit, consume):
        self.path = path
        self.limit = limit
        self.consume = consume
        self.checks = 0
        self.turn = 0

    def exists(self):
        self.checks += 1
        if self.checks == 1:  # run_forever's pre-lock stale-stop cleanup
            return False
        self.consume()
        self.turn = self.checks - 1
        return self.turn > self.limit

    def __getattr__(self, name):
        return getattr(self.path, name)


class _Harness:
    def __init__(self, monkeypatch, tmp_path, source):
        self.mp = monkeypatch
        self.tmp = tmp_path
        self.source = source
        self.events = []
        self.fetches = []
        self.signals = []
        self.position_checks = []
        self.exit_checks = []
        self.snapshots = []
        self.statuses = []
        self.quotes = {}
        self.visits = {}
        self.signal_action = "hold"
        self.fault = None
        self.reject_sells = set()
        self.active_symbol = None
        self.cfg = {
            "enabled": True, "strategy_id": STRATEGY,
            "strategy": {"name": STRATEGY, "trade_enabled": True, "donchian_len": 3},
            "strategy_preset": "breakout_default", "venue": VENUE,
            "symbol": SYMBOLS[0], "symbols": list(SYMBOLS),
            "min_bars": 1, "max_bars": 30, "loop_interval_sec": 0.0,
            "qty": 0.5, "order_type": "market", "allow_first_signal_trade": True,
            "use_ccxt_fallback": False, "position_aware": True,
            "sell_full_position": True, "signal_source": "synthetic_mid_ohlcv",
            "auto_select_best_venue": False, "switch_only_when_blocked": True,
            "venue_candidates": [], "max_tick_age_sec": 5.0,
            "stop_loss_pct": 0.03, "trailing_stop_pct": 0.02,
            "take_profit_pct": 0.0, "max_bars_hold": 0,
        }
        self.reload_runner()
        self.state = self.runner.StrategyStateSQLite()
        self.queue = self.runner.IntentQueueSQLite()
        self.paper = self.runner.PaperTradingSQLite()
        self.paper.set_state("cash_quote", "100000")
        self._install_storage_observers()

    def key(self, kind, symbol):
        return f"{kind}:{VENUE}:{symbol}:{STRATEGY}"

    def reload_runner(self):
        name = f"services.execution._offline_multisymbol_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(name, self.source)
        module = importlib.util.module_from_spec(spec)
        self.mp.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        assert Path(module.run_forever.__code__.co_filename).resolve() == self.source
        self.runner = module
        self.mp.setattr(module, "start_capture", lambda _cfg: None)
        self.mp.setattr(module, "load_user_yaml", lambda **_kw: {
            "strategy_runner": copy.deepcopy(self.cfg),
        })
        self.mp.setattr(module, "_cfg", lambda: copy.deepcopy(self.cfg))
        self.mp.setattr(module, "make_exchange", self._forbid_external)
        self.mp.setattr(module, "get_best_bid_ask_last", self._forbid_external)
        self.mp.setattr(module, "mq_check", lambda *_a, **_kw: {"ok": True})
        self.mp.setattr(module, "select_strategy", lambda **_kw: {})
        self.mp.setattr(module, "_fetch_mid", self._tick)
        self.mp.setattr(module, "_fetch_public_ohlcv", self._public)
        self.mp.setattr(module, "_strategy_signal", self._signal)
        self.mp.setattr(module, "_registry_signal_with_context", self._public_signal)
        self.mp.setattr(module, "_write_status", lambda row: self.statuses.append(dict(row)))
        self.mp.setattr(module, "time", SimpleNamespace(time=time.time, sleep=lambda _s: None))
        real_startup = module.require_known_flat_or_override

        def startup(**kw):
            self.events.append(("startup", kw["symbol"]))
            return real_startup(**kw)

        self.mp.setattr(module, "require_known_flat_or_override", startup)
        real_exit = module.evaluate_strategy_exit_stack

        def exit_stack(**kw):
            self.exit_checks.append((self.stop.turn, self.active_symbol, dict(kw)))
            return real_exit(**kw)

        self.mp.setattr(module, "evaluate_strategy_exit_stack", exit_stack)

    @staticmethod
    def _forbid_external(*_args, **_kwargs):
        pytest.fail("offline integration attempted network/exchange/subprocess access")

    def _install_storage_observers(self):
        real_position = self.runner.PaperTradingSQLite.get_position
        real_upsert = self.runner.IntentQueueSQLite.upsert_intent
        harness = self

        def position(db, symbol):
            harness.position_checks.append((harness.stop.turn, symbol))
            if harness.fault == ("position", symbol):
                harness.events.append(("fault:position", symbol))
                raise RuntimeError("injected position failure")
            return real_position(db, symbol)

        def upsert(db, row):
            if harness.fault == ("intent", row["symbol"]):
                harness.events.append(("fault:intent", row["symbol"]))
                raise RuntimeError("injected intent failure")
            return real_upsert(db, row)

        self.mp.setattr(self.runner.PaperTradingSQLite, "get_position", position)
        self.mp.setattr(self.runner.IntentQueueSQLite, "upsert_intent", upsert)

    def _quote(self, cfg):
        symbol = cfg["symbol"]
        self.active_symbol = symbol
        self.events.append(("fetch", symbol))
        self.fetches.append((self.stop.turn, symbol))
        if self.fault == ("fetch", symbol):
            self.events.append(("fault:fetch", symbol))
            raise RuntimeError("injected fetch failure")
        visit = self.visits.get(symbol, 0)
        self.visits[symbol] = visit + 1
        sequence = self.quotes.get(symbol, [PRICES[symbol]])
        return sequence[min(visit, len(sequence) - 1)]

    def _tick(self, cfg):
        price = self._quote(cfg)
        return None if price is None else (price, 1_800_000_000_000 + self.stop.turn * 1000)

    def _public(self, cfg, **_kw):
        price = self._quote(cfg)
        count = getattr(self, "public_rows", self.cfg["min_bars"])
        rows = [] if price is None else [
            [1_800_000_000_000 + self.stop.turn * 1000 + i, price, price, price, price, 1.0]
            for i in range(count)
        ]
        return rows, {"source": "public_ohlcv", "env_sample_mode": False,
                      "sample_fallback": False, "row_count": len(rows)}

    def _signal(self, cfg, prices, **_kw):
        return self._signal_result(cfg["symbol"], prices[-1])

    def _public_signal(self, *, symbol, ohlcv, **_kw):
        return self._signal_result(symbol, ohlcv[-1][4])

    def _signal_result(self, symbol, price):
        self.signals.append((self.stop.turn, symbol, price))
        return {"ok": True, "action": self.signal_action, "reason": "offline_input", "ind": {}}

    def _fill(self, row, *, reject=False):
        order = {**row, "order_id": "offline-" + row["intent_id"],
                 "client_order_id": "offline-" + row["intent_id"],
                 "ts": TS, "status": "rejected" if reject else "open",
                 "reject_reason": "injected_rejection" if reject else None}
        self.paper.insert_order(order)
        if not reject:
            result = self.paper.apply_fill(
                order=order, ts=TS, price=row["meta"]["reference_price"],
                qty=row["qty"], fee=0.0, fee_currency="USD",
            )
            assert result["ok"], result
        return order

    def consume(self):
        # Deliberately minimal test driver; no real consumer lifecycle is claimed.
        for row in self.queue.next_queued(limit=100):
            reject = row["side"] == "sell" and row["symbol"] in self.reject_sells
            assert self.queue.update_status(row["intent_id"], "submitted")
            order = self._fill(row, reject=reject)
            assert self.queue.update_status(
                row["intent_id"], "rejected" if reject else "filled",
                last_error="injected_rejection" if reject else None,
                client_order_id=order["client_order_id"], linked_order_id=order["order_id"],
            )
        self.snapshots.append({p["symbol"]: p["qty"] for p in self.paper.list_positions()})

    def seed_holdings(self):
        for symbol, price in PRICES.items():
            self._fill({"intent_id": "seed-" + symbol, "venue": VENUE, "symbol": symbol,
                        "side": "buy", "order_type": "market", "qty": 0.5,
                        "strategy_id": STRATEGY, "meta": {"reference_price": price}})

    def run(self, turns):
        self.stop = _BoundedStop(self.tmp / "stop", turns, self.consume)
        self.mp.setattr(self.runner, "STOP_FILE", self.stop)
        self.runner.run_forever()
        assert self.stop.checks == turns + 2, "runner did not reach its bounded outer stop"
        assert not self.runner.LOCK_FILE.exists()

    def intents(self, side=None):
        return [row for row in self.queue.list_intents(limit=100)
                if side is None or row["side"] == side]

    def holdings(self):
        return {p["symbol"]: p["qty"] for p in self.paper.list_positions()}


@pytest.fixture
def harness(monkeypatch, tmp_path):
    source = Path(os.environ.get("CBP_MULTISYMBOL_BEFORE_SOURCE") or
                  ROOT / "services/execution/strategy_runner.py").resolve()
    assert source.is_file(), source
    for name in tuple(os.environ):
        if name.startswith("CBP_"):
            monkeypatch.delenv(name)
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CBP_STARTUP_CONFIRM_FLAT", "true")
    monkeypatch.setenv("CBP_CAPTURE_MARKET_CONTEXT", "0")
    monkeypatch.setenv("CBP_CAPTURE_EXECUTION_IDENTITY", "0")
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(socket.socket, "connect", _Harness._forbid_external)
    monkeypatch.setattr(socket.socket, "connect_ex", _Harness._forbid_external)
    monkeypatch.setattr(socket, "create_connection", _Harness._forbid_external)
    monkeypatch.setattr(subprocess, "Popen", _Harness._forbid_external)
    import services.os.app_paths as paths
    import services.logging.app_logger as app_logger
    importlib.reload(paths)
    monkeypatch.setattr(app_logger, "get_logger", lambda _name: logging.getLogger("offline_runner_test"))
    # Match the existing _reload_strategy_runner fixture's storage/path rebinding,
    # and also rebind the startup guard's position-state store.
    for name in ("services.admin.config_editor", "storage.intent_queue_sqlite",
                 "storage.paper_trading_sqlite", "storage.strategy_state_sqlite",
                 "storage.position_state_sqlite", "services.execution.startup_guard"):
        importlib.reload(importlib.import_module(name))
    # Legacy source has an absolute debug output; keep even that inside this test.
    real_open = Path.open

    def isolated_open(path, *args, **kwargs):
        if str(path) == "/tmp/cbp_debug.txt":
            path = tmp_path / "cbp_debug.txt"
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", isolated_open)
    return _Harness(monkeypatch, tmp_path, source)


@pytest.mark.parametrize("source", ["synthetic_mid_ohlcv", "public_ohlcv_1m"])
def test_three_independent_entries_holdings_and_exit_checks(harness, source):
    h = harness
    h.cfg["signal_source"] = source
    h.signal_action = "buy"
    h.run(6)

    assert h.fetches == [(turn, SYMBOLS[(turn - 1) % 3]) for turn in range(1, 7)]
    assert h.events[:4] == [("startup", s) for s in SYMBOLS] + [("fetch", SYMBOLS[0])]
    assert [(t, s) for t, s, _p in h.signals] == h.fetches
    assert all((t, s) in h.position_checks for t, s in h.fetches)
    assert {s for _t, s, _kw in h.exit_checks} == set(SYMBOLS)
    assert h.holdings() == dict.fromkeys(SYMBOLS, 0.5)
    assert any(snapshot == dict.fromkeys(SYMBOLS, 0.5) for snapshot in h.snapshots)
    buys = h.intents("buy")
    assert len(buys) == 3
    assert {r["symbol"] for r in buys} == set(SYMBOLS)
    for row in buys:
        assert row["status"] == "filled"
        assert row["qty"] == 0.5
        assert row["meta"]["reference_price"] == PRICES[row["symbol"]]
    for _turn, symbol, kw in h.exit_checks:
        assert kw["entry_price"] == PRICES[symbol]
        assert kw["current_price"] == PRICES[symbol]
        assert kw["qty"] == 0.5
    for symbol in SYMBOLS:
        assert h.state.get(h.key("last_action", symbol)) == "buy"
        assert h.state.get(h.key("last_emitted_action", symbol)) == "buy"
        assert float(h.state.get(h.key("entry_price", symbol))) == PRICES[symbol]


def test_tick_prices_persist_per_turn_and_do_not_cross_symbols(harness):
    h = harness
    h.quotes = {s: [p, p + p * 0.01, p + p * 0.02] for s, p in PRICES.items()}
    h.run(8)  # Stop on the middle symbol, not at a whole-round boundary.
    for index, symbol in enumerate(SYMBOLS):
        expected = h.quotes[symbol][:3 if index < 2 else 2]
        assert json.loads(h.state.get(h.key("prices", symbol)) or "[]") == expected
        assert h.state.get(h.key("last_action", symbol)) == "hold"
        assert h.state.get(h.key("warmed", symbol)) == "1"


def test_restart_sqlite_recovers_own_stop_trailing_and_action_state(harness):
    h = harness
    h.signal_action = "buy"
    h.run(3)
    h.signal_action = "hold"
    h.quotes = {SYMBOLS[0]: [102.0], SYMBOLS[1]: [1010.0], SYMBOLS[2]: [10.1]}
    h.run(3)
    assert h.holdings() == dict.fromkeys(SYMBOLS, 0.5)
    expected_peaks = dict(zip(SYMBOLS, (102.0, 1010.0, 10.1)))
    for symbol in SYMBOLS:
        assert float(h.state.get(h.key("trailing_peak", symbol))) == expected_peaks[symbol]
        assert h.state.get(h.key("last_action", symbol)) == "hold"
        assert h.state.get(h.key("last_emitted_action", symbol)) == "hold"

    h.reload_runner()  # Fresh module and real SQLite handles, not retained loop locals.
    h.state = h.runner.StrategyStateSQLite()
    h.queue = h.runner.IntentQueueSQLite()
    h.paper = h.runner.PaperTradingSQLite()
    h.exit_checks.clear()
    h.quotes = {SYMBOLS[0]: [90.0], SYMBOLS[1]: [980.0], SYMBOLS[2]: [10.1]}
    h.run(3)
    sells = {r["symbol"]: r for r in h.intents("sell")}
    assert set(sells) == set(SYMBOLS[:2])
    for symbol, rule, price in ((SYMBOLS[0], "stop_loss", 90.0),
                                (SYMBOLS[1], "trailing_stop", 980.0)):
        assert sells[symbol]["meta"]["exit_stack_rule"] == rule
        assert sells[symbol]["meta"]["reference_price"] == price
        assert h.state.get(h.key("last_emitted_action", symbol)) == "sell"
        assert h.state.get(h.key("entry_price", symbol)) is None
    assert h.holdings() == {SYMBOLS[0]: 0.0, SYMBOLS[1]: 0.0, SYMBOLS[2]: 0.5}
    assert float(h.state.get(h.key("entry_price", SYMBOLS[2]))) == 10.0
    assert float(h.state.get(h.key("trailing_peak", SYMBOLS[2]))) == 10.1
    assert h.state.get(h.key("last_emitted_action", SYMBOLS[2])) == "hold"
    assert len(h.intents("buy")) == 3
    assert len(h.paper.list_fills()) == 5
    for _turn, symbol, kw in h.exit_checks:
        assert kw["entry_price"] == PRICES[symbol]
        assert kw["trailing_peak_price"] == expected_peaks[symbol]


@pytest.mark.parametrize("source", ["synthetic_mid_ohlcv", "public_ohlcv_1m"])
def test_missing_fresh_quote_never_uses_old_cache_or_blocks_other_exit(harness, source):
    h = harness
    h.cfg["signal_source"] = source
    h.seed_holdings()
    h.quotes = {SYMBOLS[0]: [100.0, None], SYMBOLS[1]: [1000.0, 900.0]}
    h.run(6)
    assert {r["symbol"] for r in h.intents("sell")} == {SYMBOLS[1]}
    assert (4, SYMBOLS[0]) not in h.position_checks
    assert not any(t == 4 and s == SYMBOLS[0] for t, s, _kw in h.exit_checks)
    assert h.holdings()[SYMBOLS[0]] == 0.5
    assert h.holdings()[SYMBOLS[1]] == 0.0
    assert float(h.state.get(h.key("entry_price", SYMBOLS[0]))) == 100.0
    assert float(h.state.get(h.key("trailing_peak", SYMBOLS[0]))) == 100.0
    # The first observed held candle seeds the timestamp; only a later one
    # increments the count. A missing quote must not advance it.
    assert int(h.state.get(h.key("bars_held", SYMBOLS[0])) or 0) == 0
    assert h.state.get(h.key("last_held_bar_ts", SYMBOLS[0])) == "1800000001000"
    assert h.state.get(h.key("last_emitted_action", SYMBOLS[0])) != "sell"
    assert h.intents("sell")[0]["meta"]["reference_price"] == 900.0


@pytest.mark.parametrize("source", ["synthetic_mid_ohlcv", "public_ohlcv_1m"])
@pytest.mark.parametrize("fault", ["fetch", "position", "intent"])
def test_symbol_exception_isolated_while_other_holdings_exit(harness, source, fault):
    h = harness
    h.cfg["signal_source"] = source
    h.seed_holdings()
    h.fault = (fault, SYMBOLS[0])
    h.quotes = dict(zip(SYMBOLS, ([90.0], [900.0], [9.0])))
    h.run(3)
    assert ("fault:" + fault, SYMBOLS[0]) in h.events
    assert h.fetches == [(1, SYMBOLS[0]), (2, SYMBOLS[1]), (3, SYMBOLS[2])]
    sells = h.intents("sell")
    assert {r["symbol"] for r in sells} == set(SYMBOLS[1:])
    assert all(r["status"] == "filled" for r in sells)
    assert {r["symbol"]: r["meta"]["reference_price"] for r in sells} == {
        SYMBOLS[1]: 900.0, SYMBOLS[2]: 9.0,
    }
    assert h.holdings() == {SYMBOLS[0]: 0.5, SYMBOLS[1]: 0.0, SYMBOLS[2]: 0.0}


@pytest.mark.parametrize("fault", ["fetch", "position", "intent"])
def test_single_symbol_exception_still_propagates(harness, fault):
    h = harness
    h.cfg["symbols"] = [SYMBOLS[0]]
    h.seed_holdings()
    h.fault = (fault, SYMBOLS[0])
    h.quotes = {SYMBOLS[0]: [90.0]}
    with pytest.raises(RuntimeError, match=f"injected {fault} failure"):
        h.run(2)
    assert ("fault:" + fault, SYMBOLS[0]) in h.events
    assert not h.runner.LOCK_FILE.exists()


def test_rejected_first_sell_does_not_suppress_nonlast_exit(harness):
    h = harness
    h.seed_holdings()
    h.reject_sells.add(SYMBOLS[0])
    h.quotes = {SYMBOLS[0]: [90.0], SYMBOLS[1]: [900.0]}
    h.run(3)
    sells = {r["symbol"]: r for r in h.intents("sell")}
    assert set(sells) == set(SYMBOLS[:2])
    assert sells[SYMBOLS[0]]["status"] == "rejected"
    assert sells[SYMBOLS[0]]["last_error"] == "injected_rejection"
    assert sells[SYMBOLS[1]]["status"] == "filled"
    assert sells[SYMBOLS[0]]["meta"]["reference_price"] == 90.0
    assert sells[SYMBOLS[1]]["meta"]["reference_price"] == 900.0
    assert h.holdings() == {SYMBOLS[0]: 0.5, SYMBOLS[1]: 0.0, SYMBOLS[2]: 0.5}
    assert len(h.paper.list_fills()) == 4
    assert any(o["symbol"] == SYMBOLS[0] and o["status"] == "rejected"
               for o in h.paper.list_orders())


@pytest.mark.parametrize("source", ["synthetic_mid_ohlcv", "public_ohlcv_1m"])
def test_fresh_warmup_quotes_still_protect_all_held_positions(harness, source):
    h = harness
    h.cfg.update(signal_source=source, min_bars=5)
    h.public_rows = 1
    h.seed_holdings()
    h.quotes = dict(zip(SYMBOLS, ([90.0], [900.0], [9.0])))
    h.run(3)
    assert h.signals == [], "warm-up must not execute entry signals"
    assert {s for _t, s, _kw in h.exit_checks} == set(SYMBOLS)
    sells = h.intents("sell")
    assert {r["symbol"] for r in sells} == set(SYMBOLS)
    assert all(r["meta"]["exit_stack_rule"] == "stop_loss" for r in sells)
    assert {r["symbol"]: r["meta"]["reference_price"] for r in sells} == {
        SYMBOLS[0]: 90.0, SYMBOLS[1]: 900.0, SYMBOLS[2]: 9.0,
    }
    assert h.holdings() == dict.fromkeys(SYMBOLS, 0.0)


@pytest.mark.parametrize("blocked_state", ["unknown", "open"])
def test_all_startup_guards_fail_closed_before_any_symbol_fetch(harness, blocked_state):
    h = harness
    from storage.position_state_sqlite import PositionStateSQLite
    from services.execution.startup_guard import StartupGuardError

    h.mp.delenv("CBP_STARTUP_CONFIRM_FLAT")
    startup = PositionStateSQLite()
    for symbol in SYMBOLS:
        if symbol == SYMBOLS[1] and blocked_state == "unknown":
            continue
        startup.upsert(venue=VENUE, symbol=symbol, base=symbol.split("/")[0],
                       quote="USD", qty=0.5 if symbol == SYMBOLS[1] else 0.0,
                       status="known")
    reason = "unknown_position_state" if blocked_state == "unknown" else "open_position_requires_override"
    with pytest.raises(StartupGuardError, match=reason):
        h.run(3)
    assert h.fetches == []
    assert h.signals == []
    assert h.position_checks == []
    assert h.intents() == []
    assert h.paper.list_orders() == []
    assert h.events == [("startup", SYMBOLS[0]), ("startup", SYMBOLS[1])]
    assert not h.runner.LOCK_FILE.exists()


def test_partial_symbol_state_read_does_not_save_previous_symbols_latches(harness):
    h = harness
    blocked = SYMBOLS[1]
    h.state.set(h.key("prices", blocked), "[1000.0]")
    h.state.set(h.key("last_action", blocked), "sell")
    h.state.set(h.key("last_emitted_action", blocked), "buy")
    original_get = h.runner.StrategyStateSQLite.get
    failed = []

    def get(db, key):
        if key == h.key("last_emitted_action", blocked) and not failed:
            failed.append(key)
            raise RuntimeError("injected state read failure")
        return original_get(db, key)

    h.mp.setattr(h.runner.StrategyStateSQLite, "get", get)
    h.run(3)
    assert failed
    assert h.state.get(h.key("last_action", blocked)) == "sell"
    assert h.state.get(h.key("last_emitted_action", blocked)) == "buy"
    assert json.loads(h.state.get(h.key("prices", blocked))) == [1000.0]
    for symbol in (SYMBOLS[0], SYMBOLS[2]):
        assert json.loads(h.state.get(h.key("prices", symbol))) == [PRICES[symbol]]
        assert h.state.get(h.key("last_action", symbol)) == "hold"


def test_failed_symbol_checkpoint_does_not_suppress_other_symbols_exits(harness):
    h = harness
    h.seed_holdings()
    h.quotes = dict(zip(SYMBOLS, ([90.0], [900.0], [9.0])))
    original_set = h.runner.StrategyStateSQLite.set
    failed = []

    def set_state(db, key, value):
        if key == h.key("prices", SYMBOLS[0]):
            failed.append(key)
            raise RuntimeError("injected checkpoint failure")
        return original_set(db, key, value)

    h.mp.setattr(h.runner.StrategyStateSQLite, "set", set_state)
    h.run(3)
    assert failed
    assert {r["symbol"] for r in h.intents("sell")} == set(SYMBOLS)
    assert h.holdings() == dict.fromkeys(SYMBOLS, 0.0)
    for symbol in SYMBOLS[1:]:
        assert json.loads(h.state.get(h.key("prices", symbol))) == h.quotes[symbol]


def test_post_startup_venue_error_is_local_to_its_symbol(harness):
    h = harness
    h.cfg.update(auto_select_best_venue=True, venue_candidates=[VENUE])
    h.seed_holdings()
    h.quotes = {SYMBOLS[1]: [1000.0, 900.0]}

    def market_quality(_venue, symbol):
        if symbol == SYMBOLS[0] and h.fetches:
            raise RuntimeError("injected later venue resolution failure")
        return {"ok": True}

    h.mp.setattr(h.runner, "mq_check", market_quality)
    h.run(5)
    assert h.fetches == [(1, SYMBOLS[0]), (2, SYMBOLS[1]),
                         (3, SYMBOLS[2]), (5, SYMBOLS[1])]
    assert any(row.get("note") == "symbol_turn_failed" and
               row.get("symbol") == SYMBOLS[0] for row in h.statuses)
    assert {row["symbol"] for row in h.intents("sell")} == {SYMBOLS[1]}
    assert h.holdings()[SYMBOLS[1]] == 0.0


@pytest.mark.parametrize("source", ["synthetic_mid_ohlcv", "public_ohlcv_1m"])
@pytest.mark.parametrize("quote", [None, 1000.0])
def test_unread_price_history_is_preserved_even_on_periodic_save_turn(harness, source, quote):
    h = harness
    h.cfg["signal_source"] = source
    symbol = SYMBOLS[1]
    key = h.key("prices", symbol)
    saved = "[990.0, 1000.0]"
    h.state.set(key, saved)
    h.quotes = {symbol: [quote]}
    original_get = h.runner.StrategyStateSQLite.get
    failed = []

    def get(db, name):
        if name == key:
            failed.append(name)
            raise RuntimeError("injected unreadable price history")
        return original_get(db, name)

    h.mp.setattr(h.runner.StrategyStateSQLite, "get", get)
    h.run(15)  # Includes ETH's fifth visit and the legacy periodic write.
    assert len(failed) == 5
    assert original_get(h.state, key) == saved
    assert len([s for _t, s in h.fetches if s == SYMBOLS[2]]) == 5


def test_newly_selected_venue_retains_fail_closed_position_guard(harness):
    h = harness
    from services.execution.startup_guard import StartupGuardError
    from storage.position_state_sqlite import PositionStateSQLite

    h.mp.delenv("CBP_STARTUP_CONFIRM_FLAT")
    for symbol in SYMBOLS:
        PositionStateSQLite().upsert(venue=VENUE, symbol=symbol,
                                    base=symbol.split("/")[0], quote="USD",
                                    qty=0.0, status="known")

    def choose(_cfg, symbol, **_kwargs):
        return "kraken" if h.fetches and symbol == SYMBOLS[1] else VENUE

    h.mp.setattr(h.runner, "_choose_venue_for_symbol", choose)
    with pytest.raises(StartupGuardError, match="unknown_position_state"):
        h.run(3)
    assert h.fetches == [(1, SYMBOLS[0])]
    assert not h.runner.LOCK_FILE.exists()
