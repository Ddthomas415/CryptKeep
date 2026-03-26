from __future__ import annotations

import importlib


def _reload_runner_with_tmp_state(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CBP_STARTUP_CONFIRM_FLAT", "true")

    import services.os.app_paths as app_paths
    import services.admin.config_editor as config_editor
    import storage.intent_queue_sqlite as intent_queue_sqlite
    import storage.paper_trading_sqlite as paper_trading_sqlite
    import storage.strategy_state_sqlite as strategy_state_sqlite
    import services.strategy_runner.ema_crossover_runner as runner

    importlib.reload(app_paths)
    importlib.reload(config_editor)
    importlib.reload(intent_queue_sqlite)
    importlib.reload(paper_trading_sqlite)
    importlib.reload(strategy_state_sqlite)
    importlib.reload(runner)
    return runner


def test_persistent_exit_condition_emits_exactly_one_sell_intent(monkeypatch, tmp_path):
    runner = _reload_runner_with_tmp_state(monkeypatch, tmp_path)
    qdb = runner.IntentQueueSQLite()
    pdb = runner.PaperTradingSQLite()

    pdb.upsert_position("BTC/USD", 1.0, 100.0, 0.0)

    monkeypatch.setattr(
        runner,
        "_cfg",
        lambda: {
            "enabled": True,
            "strategy_id": "ema_cross",
            "strategy": {
                "name": "ema_cross",
                "trade_enabled": True,
                "ema_fast": 2,
                "ema_slow": 4,
            },
            "strategy_preset": "ema_cross_default",
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "fast_n": 2,
            "slow_n": 4,
            "min_bars": 5,
            "max_bars": 20,
            "loop_interval_sec": 0.0,
            "qty": 0.5,
            "order_type": "market",
            "allow_first_signal_trade": False,
            "use_ccxt_fallback": False,
            "max_tick_age_sec": 5.0,
            "position_aware": True,
            "sell_full_position": True,
            "signal_source": "synthetic_mid_ohlcv",
            "auto_select_best_venue": False,
            "switch_only_when_blocked": True,
            "venue_candidates": [],
        },
    )
    monkeypatch.setattr(runner, "_fetch_mid", lambda cfg: (110.0, 1))
    monkeypatch.setattr(
        runner,
        "_strategy_signal",
        lambda cfg, prices, ts_ms=None: {"ok": True, "action": "hold", "reason": "no_cross", "ind": {}},
    )
    monkeypatch.setattr(
        runner,
        "evaluate_strategy_exit_stack",
        lambda **kwargs: {"action": "exit", "reason": "take_profit", "stack_rule": "take_profit"},
    )

    loop_counter = {"count": 0}

    def fake_sleep(_seconds: float) -> None:
        loop_counter["count"] += 1
        if loop_counter["count"] >= 8:
            runner.STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
            runner.STOP_FILE.write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(runner.time, "sleep", fake_sleep)

    runner.run_forever()

    intents = qdb.list_intents(limit=10)
    assert len(intents) == 1
    assert intents[0]["side"] == "sell"
    assert intents[0]["strategy_id"] == "ema_cross"
    assert intents[0]["status"] == "queued"
