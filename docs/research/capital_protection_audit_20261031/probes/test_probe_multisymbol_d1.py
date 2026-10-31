"""Probe (not part of the repository): does run_forever give every symbol its decision, exit and order step?
Uses the repository's own test scaffolding (_reload_strategy_runner) with fakes for prices and signals only."""
import collections, json
import pytest
from tests.test_strategy_runtime_runner import _reload_strategy_runner

SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD"]
BASE = {"BTC/USD": 100.0, "ETH/USD": 50.0, "SOL/USD": 10.0}


def _cfg(strategy_hold_exits=False):
    return {
        "enabled": True, "strategy_id": "ema_cross",
        "strategy": {"name": "ema_cross", "trade_enabled": True, "ema_fast": 2, "ema_slow": 3},
        "strategy_preset": "ema_cross_default", "venue": "coinbase", "symbol": SYMBOLS[0], "symbols": list(SYMBOLS),
        "fast_n": 2, "slow_n": 3, "min_bars": 1, "max_bars": 10, "loop_interval_sec": 0.0, "qty": 0.5,
        "order_type": "market", "allow_first_signal_trade": True, "use_ccxt_fallback": False, "max_tick_age_sec": 5.0,
        "position_aware": True, "sell_full_position": True, "signal_source": "synthetic_mid_ohlcv",
        "auto_select_best_venue": False, "switch_only_when_blocked": True, "venue_candidates": [],
        "stop_loss_pct": 0.03, "take_profit_pct": 0.06, "trailing_stop_pct": 0.02, "max_bars_hold": 60,
    }


def _run(monkeypatch, tmp_path, *, action, price_fn, loops, seed_positions=False):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    pdb = runner.PaperTradingSQLite()
    if seed_positions:
        for s in SYMBOLS:
            pdb.upsert_position(s, 1.0, BASE[s], 0.0)
        monkeypatch.setenv("CBP_STARTUP_ALLOW_OPEN_POSITION", "true")
    monkeypatch.setattr(runner, "_cfg", lambda: _cfg())
    ticks = collections.Counter()
    signals, positions = collections.Counter(), collections.Counter()

    def fake_fetch_mid(cfg):
        s = cfg["symbol"]; ticks[s] += 1
        return price_fn(s, ticks[s]), ticks[s] * 1000

    def fake_signal(cfg, prices, ts_ms=None):
        signals[cfg["symbol"]] += 1
        return {"ok": True, "action": action, "reason": "probe", "ind": {}}

    real_get = runner.PaperTradingSQLite.get_position
    def spy_get(self, symbol):
        positions[symbol] += 1
        return real_get(self, symbol)

    n = {"sleeps": 0}
    def fake_sleep(_s):
        n["sleeps"] += 1
        if n["sleeps"] >= loops:
            runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(runner, "_fetch_mid", fake_fetch_mid)
    monkeypatch.setattr(runner, "_strategy_signal", fake_signal)
    monkeypatch.setattr(runner.PaperTradingSQLite, "get_position", spy_get)
    monkeypatch.setattr(runner.time, "sleep", fake_sleep)
    runner.run_forever()
    intents = runner.IntentQueueSQLite().list_intents(limit=100)
    by_sym = collections.Counter((i["symbol"], i["side"], (i.get("meta") or {}).get("exit_stack_rule")) for i in intents)
    return dict(signals), dict(positions), dict(by_sym)


def test_probe_entries(monkeypatch, tmp_path):
    sig, pos, intents = _run(monkeypatch, tmp_path, action="buy", price_fn=lambda s, k: BASE[s] + k, loops=12)
    print("\nENTRIES signal calls:", sig, "\nENTRIES position reads:", pos, "\nENTRIES intents:", intents)


def test_probe_exits(monkeypatch, tmp_path):
    # every symbol holds 1 unit bought at BASE; price falls 5% (past the 2% trailing and 3% stop levels)
    sig, pos, intents = _run(monkeypatch, tmp_path, action="hold", price_fn=lambda s, k: BASE[s] * 0.95, loops=12,
                             seed_positions=True)
    print("\nEXITS signal calls:", sig, "\nEXITS position reads:", pos, "\nEXITS intents:", intents)
