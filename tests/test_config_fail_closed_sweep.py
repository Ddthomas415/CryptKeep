"""
Substrate backlog #2 slice proofs: config fail-closed sweep over the order
router retry knobs, market-quality guard thresholds, live_arming risk-cap
parsing, and the atomic risk claim enforcement layer.
"""
from __future__ import annotations

import importlib
import math
import sqlite3
import time


def test_router_knobs_clamp_and_default():
    from services.execution import order_router as router

    assert router._bounded_float("nan", default=6.0, lo=0.05, hi=300.0) == 6.0
    assert router._bounded_float("inf", default=6.0, lo=0.05, hi=300.0) == 6.0
    assert router._bounded_float("abc", default=0.6, lo=0.05, hi=60.0) == 0.6
    assert router._bounded_float(-5, default=0.6, lo=0.05, hi=60.0) == 0.05
    assert router._bounded_float(9999, default=6.0, lo=0.05, hi=300.0) == 300.0
    assert router._bounded_int("nan", default=3, lo=0, hi=10) == 3
    assert router._bounded_int(float("inf"), default=3, lo=0, hi=10) == 3
    assert router._bounded_int(-2, default=3, lo=0, hi=10) == 0
    assert router._bounded_int(50, default=3, lo=0, hi=10) == 10
    assert router._bounded_int(2, default=3, lo=0, hi=10) == 2


def test_router_cfg_never_yields_nonfinite(monkeypatch):
    from services.execution import order_router as router

    monkeypatch.setattr(
        router,
        "load_user_yaml",
        lambda: {
            "live_trading": {
                "execution": {
                    "max_order_retries": "nan",
                    "base_retry_delay_sec": "inf",
                    "max_retry_delay_sec": float("nan"),
                }
            }
        },
    )
    cfg = router._cfg()
    assert cfg == {
        "max_order_retries": 3,
        "base_retry_delay_sec": 0.6,
        "max_retry_delay_sec": 6.0,
    }
    for key in ("max_order_retries", "base_retry_delay_sec", "max_retry_delay_sec"):
        assert math.isfinite(float(cfg[key])), key


def _mq_with_cfg(monkeypatch, *, tick_age, spread, symbol_thresholds=None):
    from services.risk import market_quality_guard as mq

    monkeypatch.setattr(
        mq,
        "load_user_yaml",
        lambda: {
            "market_quality_guard": {
                "enabled": True,
                "block_when_unknown": True,
                "require_bid_ask": True,
                "max_tick_age_sec": tick_age,
                "max_spread_bps": spread,
                "symbol_thresholds": symbol_thresholds or {},
            }
        },
    )
    monkeypatch.setattr(
        mq,
        "get_best_bid_ask_last",
        lambda venue, sym: {
            "bid": 100.0,
            "ask": 100.01,
            "last": 100.0,
            "ts_ms": time.time() * 1000.0,
        },
    )
    return mq


def test_mq_guard_fails_closed_on_garbage_thresholds(monkeypatch):
    mq = _mq_with_cfg(monkeypatch, tick_age=float("nan"), spread=5.0)
    assert mq.check("coinbase", "BTC/USD")["reason"] == "invalid_threshold:max_tick_age_sec"

    mq = _mq_with_cfg(monkeypatch, tick_age=10.0, spread=float("inf"))
    assert mq.check("coinbase", "BTC/USD")["reason"] == "invalid_threshold:max_spread_bps"

    mq = _mq_with_cfg(monkeypatch, tick_age=0, spread=5.0)
    assert mq.check("coinbase", "BTC/USD")["reason"] == "invalid_threshold:max_tick_age_sec"

    mq = _mq_with_cfg(monkeypatch, tick_age="abc", spread=5.0)
    assert mq.check("coinbase", "BTC/USD")["reason"] == "invalid_threshold:max_tick_age_sec"


def test_mq_guard_fails_closed_on_invalid_symbol_override(monkeypatch):
    mq = _mq_with_cfg(
        monkeypatch,
        tick_age=10.0,
        spread=5.0,
        symbol_thresholds={"BTC/USD": {"max_spread_bps": "abc"}},
    )
    assert mq.check("coinbase", "BTC/USD")["reason"] == "invalid_threshold:max_spread_bps"


def test_mq_guard_valid_thresholds_still_pass_and_trip(monkeypatch):
    mq = _mq_with_cfg(monkeypatch, tick_age=10.0, spread=5.0)
    assert mq.check("coinbase", "BTC/USD")["ok"] is True

    monkeypatch.setattr(
        mq,
        "get_best_bid_ask_last",
        lambda venue, sym: {
            "bid": 100.0,
            "ask": 101.0,
            "last": 100.5,
            "ts_ms": time.time() * 1000.0,
        },
    )
    out = mq.check("coinbase", "BTC/USD")
    assert out["ok"] is False
    assert out["reason"] == "spread_too_wide"


def test_arming_float_helper_skips_nonfinite_candidates():
    from services.execution import live_arming as arming

    assert arming._float_value(float("nan"), default=0.0) == 0.0
    assert arming._float_value("inf", default=0.0) == 0.0
    assert arming._float_value(float("nan"), 250.0, default=0.0) == 250.0
    assert arming._float_value("7.5", default=0.0) == 7.5


def test_live_risk_cfg_nonfinite_caps_fall_back(monkeypatch):
    from services.execution import live_arming as arming

    monkeypatch.setattr(
        arming,
        "load_user_yaml",
        lambda: {
            "risk": {
                "max_trades_per_day": 12,
                "max_daily_notional_quote": 500.0,
                "live": {
                    "max_trades_per_day": "nan",
                    "max_daily_notional_quote": float("inf"),
                    "min_order_notional_quote": "nan",
                },
            }
        },
    )
    cfg = arming.live_risk_cfg()
    assert cfg["max_trades_per_day"] == 12
    assert cfg["max_daily_notional_quote"] == 500.0
    assert cfg["min_order_notional_quote"] == 0.0


def _fresh_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths
    import storage.live_intent_queue_sqlite as queue_mod

    importlib.reload(app_paths)
    importlib.reload(queue_mod)
    return queue_mod.LiveIntentQueueSQLite(), queue_mod


def test_claim_denies_nonfinite_caps(monkeypatch, tmp_path):
    qdb, _queue_mod = _fresh_queue(monkeypatch, tmp_path)
    assert qdb.atomic_risk_claim(max_trades=0, max_notional=float("nan"), notional_est=10.0) == (
        False,
        "risk:invalid_cap",
    )
    assert qdb.atomic_risk_claim(max_trades=float("inf"), max_notional=0.0, notional_est=10.0) == (
        False,
        "risk:invalid_cap",
    )


def test_claim_denies_nonfinite_or_negative_estimate(monkeypatch, tmp_path):
    qdb, _queue_mod = _fresh_queue(monkeypatch, tmp_path)
    assert qdb.atomic_risk_claim(max_trades=0, max_notional=0.0, notional_est=float("nan")) == (
        False,
        "risk:invalid_notional_est",
    )
    assert qdb.atomic_risk_claim(max_trades=0, max_notional=0.0, notional_est=-1.0) == (
        False,
        "risk:invalid_notional_est",
    )


def test_claim_denies_poisoned_accumulator(monkeypatch, tmp_path):
    qdb, queue_mod = _fresh_queue(monkeypatch, tmp_path)
    con = sqlite3.connect(queue_mod.DB_PATH)
    con.execute("INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES('risk:notional','nan')")
    con.commit()
    con.close()

    assert qdb.atomic_risk_claim(max_trades=0, max_notional=100.0, notional_est=10.0) == (
        False,
        "risk:corrupt_state",
    )

    con = sqlite3.connect(queue_mod.DB_PATH)
    con.execute("INSERT OR REPLACE INTO live_consumer_state(k,v) VALUES('risk:notional','garbage')")
    con.commit()
    con.close()
    assert qdb.atomic_risk_claim(max_trades=0, max_notional=100.0, notional_est=10.0) == (
        False,
        "risk:corrupt_state",
    )


def test_claim_normal_path_unchanged(monkeypatch, tmp_path):
    qdb, _queue_mod = _fresh_queue(monkeypatch, tmp_path)
    ok, reason = qdb.atomic_risk_claim(max_trades=0, max_notional=0.0, notional_est=10.0)
    assert ok is True and reason is None

    ok, reason = qdb.atomic_risk_claim(max_trades=0, max_notional=15.0, notional_est=10.0)
    assert (ok, reason) == (False, "risk:max_daily_notional_quote")
