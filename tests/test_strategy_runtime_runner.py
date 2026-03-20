from __future__ import annotations

import importlib
import json


def _reload_strategy_runner(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.strategy_state_sqlite as strategy_state_sqlite
    import services.strategy.ema_crossover_runner as runner

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(strategy_state_sqlite)
    importlib.reload(runner)
    return runner


def test_cfg_uses_canonical_breakout_strategy(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "breakout")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "load_user_yaml", lambda: {"strategy_runner": {}})

    cfg = runner._cfg()

    assert cfg["strategy_id"] == "breakout_donchian"
    assert cfg["strategy"]["name"] == "breakout_donchian"
    assert cfg["strategy_preset"] == "breakout_default"
    assert cfg["strategy"]["donchian_len"] == 20


def test_cfg_honors_env_min_bars_override_without_going_below_required_history(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STRATEGY_NAME", "ema_cross")
    monkeypatch.setenv("CBP_STRATEGY_MIN_BARS", "28")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "load_user_yaml", lambda: {"strategy_runner": {}})

    cfg = runner._cfg()

    assert cfg["strategy_id"] == "ema_cross"
    assert cfg["min_bars"] == 28


def test_cfg_honors_signal_source_and_first_signal_trade_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STRATEGY_SIGNAL_SOURCE", "public_ohlcv_5m")
    monkeypatch.setenv("CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE", "1")
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "load_user_yaml", lambda: {"strategy_runner": {}})

    cfg = runner._cfg()

    assert cfg["signal_source"] == "public_ohlcv_5m"
    assert cfg["allow_first_signal_trade"] is True


def test_run_forever_enqueues_buy_from_public_ohlcv_first_signal(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    qdb = runner.IntentQueueSQLite()

    monkeypatch.setenv("CBP_STRATEGY_SIGNAL_SOURCE", "public_ohlcv_1m")
    monkeypatch.setenv("CBP_STRATEGY_ALLOW_FIRST_SIGNAL_TRADE", "1")
    monkeypatch.setattr(
        runner,
        "load_user_yaml",
        lambda: {
            "strategy_runner": {
                "strategy": {
                    "name": "breakout_donchian",
                    "trade_enabled": True,
                    "donchian_len": 3,
                    "filter_window": 3,
                    "min_volatility_pct": 0.0,
                    "min_volume_ratio": 0.0,
                    "min_trend_efficiency": 0.0,
                    "min_channel_width_pct": 0.0,
                    "breakout_buffer_pct": 0.0,
                    "require_directional_confirmation": False,
                },
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "min_bars": 5,
                "max_bars": 20,
                "loop_interval_sec": 0.0,
                "qty": 0.5,
            }
        },
    )
    monkeypatch.setattr(
        runner,
        "_fetch_public_ohlcv",
        lambda cfg: [
            [1, 100.0, 100.0, 100.0, 100.0, 1.0],
            [2, 100.0, 100.0, 100.0, 100.0, 1.0],
            [3, 100.0, 100.0, 100.0, 100.0, 1.0],
            [4, 100.0, 100.0, 100.0, 100.0, 1.0],
            [5, 100.0, 101.0, 100.0, 101.0, 1.0],
        ],
    )

    def fake_sleep(_seconds: float) -> None:
        if runner.STATUS_FILE.exists():
            status = json.loads(runner.STATUS_FILE.read_text(encoding="utf-8"))
            if int(status.get("enqueued_total") or 0) >= 1:
                runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
                runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    runner.run_forever()

    queued = qdb.list_intents(limit=10, status="queued")
    assert len(queued) == 1
    assert queued[0]["strategy_id"] == "breakout_donchian"
    assert queued[0]["side"] == "buy"


def test_fetch_public_ohlcv_returns_empty_on_exchange_error(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runner,
        "make_exchange",
        lambda venue, creds, enable_rate_limit=True: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    out = runner._fetch_public_ohlcv(
        {
            "signal_source": "public_ohlcv_5m",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "min_bars": 20,
            "max_bars": 50,
        }
    )

    assert out == []


def test_fetch_mid_returns_none_when_ccxt_fallback_raises(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "get_best_bid_ask_last", lambda venue, symbol: None)
    monkeypatch.setattr(
        runner,
        "make_exchange",
        lambda venue, creds, enable_rate_limit=True: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    out = runner._fetch_mid(
        {
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "use_ccxt_fallback": True,
            "max_tick_age_sec": 5.0,
        }
    )

    assert out is None


def test_strategy_signal_supports_mean_reversion_runtime_prices(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)

    signal = runner._strategy_signal(
        {
            "symbol": "BTC/USD",
            "strategy": {
                "name": "mean_reversion_rsi",
                "trade_enabled": True,
                "rsi_len": 2,
                "rsi_buy": 45.0,
                "rsi_sell": 60.0,
                "sma_len": 3,
            },
        },
        [100.0, 100.0, 100.0, 100.0, 95.0, 90.0],
        ts_ms=1,
    )

    assert signal["ok"] is True
    assert signal["action"] == "buy"
    assert signal["reason"] == "rsi_oversold_below_sma"


def test_run_forever_enqueues_breakout_intent_with_canonical_strategy_id(monkeypatch, tmp_path):
    runner = _reload_strategy_runner(monkeypatch, tmp_path)
    qdb = runner.IntentQueueSQLite()

    monkeypatch.setattr(
        runner,
        "load_user_yaml",
        lambda: {
            "strategy_runner": {
                "strategy": {
                    "name": "breakout_donchian",
                    "trade_enabled": True,
                    "donchian_len": 3,
                    "filter_window": 3,
                    "min_volatility_pct": 0.0,
                    "min_volume_ratio": 0.0,
                    "min_trend_efficiency": 0.0,
                    "min_channel_width_pct": 0.0,
                    "breakout_buffer_pct": 0.0,
                    "require_directional_confirmation": False,
                },
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "min_bars": 5,
                "max_bars": 20,
                "loop_interval_sec": 0.0,
                "qty": 0.5,
            }
        },
    )

    prices = iter([100.0, 100.0, 100.0, 100.0, 100.0, 101.0])

    def fake_fetch(_cfg):
        try:
            price = next(prices)
        except StopIteration:
            price = 101.0
        return price, 1

    def fake_sleep(_seconds: float) -> None:
        if runner.STATUS_FILE.exists():
            status = json.loads(runner.STATUS_FILE.read_text(encoding="utf-8"))
            if int(status.get("enqueued_total") or 0) >= 1:
                runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
                runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(runner, "_fetch_mid", fake_fetch)
    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    runner.run_forever()

    queued = qdb.list_intents(limit=10, status="queued")
    assert len(queued) == 1
    assert queued[0]["strategy_id"] == "breakout_donchian"
    assert queued[0]["side"] == "buy"
