from __future__ import annotations

import importlib


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_external_signal_store_and_overlay(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.imitation.external_signal_store as external_signal_store
    import services.imitation.signal_overlay as signal_overlay
    import services.imitation.overlay_guard as overlay_guard

    importlib.reload(external_signal_store)
    importlib.reload(signal_overlay)
    importlib.reload(overlay_guard)

    s = external_signal_store.ExternalSignalStore()
    out = s.add_signal(source="ext", author="alice", symbol="BTC/USD", action="buy", confidence=0.9)
    assert out["ok"] is True
    rows = s.recent(limit=5, symbol="BTC/USD")
    assert rows and rows[0]["symbol"] == "BTC/USD"

    ov = signal_overlay.apply_signal_overlay({"action": "hold"}, [{"action": "buy", "confidence": 0.8}])
    assert ov["ok"] is True
    assert ov["action"] == "buy"

    guard = overlay_guard.evaluate_overlay_guard(base_action="sell", overlay_action="buy", overlay_score=0.4, allow_flip=False)
    assert guard["allow"] is False


def test_held_intents_and_intent_audit(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    from storage.intent_queue_sqlite import IntentQueueSQLite
    import services.execution.held_intents as held_intents
    import services.execution.intent_audit as intent_audit
    import services.execution.audit_monitor as audit_monitor

    importlib.reload(held_intents)
    importlib.reload(intent_audit)
    importlib.reload(audit_monitor)

    db = IntentQueueSQLite()
    db.upsert_intent(
        {
            "intent_id": "i-1",
            "ts": "2026-03-09T00:00:00+00:00",
            "source": "test",
            "strategy_id": None,
            "venue": "coinbase",
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "market",
            "qty": 0.1,
            "limit_price": None,
            "status": "queued",
            "last_error": None,
            "client_order_id": None,
            "linked_order_id": None,
        }
    )
    assert held_intents.hold_intent("i-1")["ok"] is True
    held = held_intents.list_held(limit=5)
    assert held and held[0]["intent_id"] == "i-1"
    assert held_intents.release_intent("i-1")["ok"] is True

    ev = intent_audit.record_intent_event(intent_id="i-1", event="submitted", status="ok", venue="coinbase", symbol="BTC/USD")
    assert ev["ok"] is True
    recent = intent_audit.recent_intent_events(limit=20)
    assert recent and recent[0]["payload"]["kind"] == "intent_audit"
    summ = audit_monitor.summarize_intent_audit(limit=20)
    assert summ["ok"] is True
    assert summ["count"] >= 1


def test_learning_guardrails_runtime_policy_and_logger(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.learning.guardrails as guardrails
    import services.learning.runtime_policy as runtime_policy
    import services.learning.canary_enforcer as canary_enforcer
    import services.learning.guardrail_logger as guardrail_logger
    from storage.execution_report_sqlite import ExecutionReportSQLite

    importlib.reload(guardrails)
    importlib.reload(runtime_policy)
    importlib.reload(canary_enforcer)
    importlib.reload(guardrail_logger)

    g = guardrails.evaluate_learning_guardrails({"train_rows": 500, "valid_rows": 200, "metric": 0.6, "max_drawdown_pct": 0.1})
    assert g["ok"] is True

    p = runtime_policy.read_runtime_policy({"canary_enabled": True, "canary_min_samples": 10, "promote_min_metric_delta": 0.0})
    c = canary_enforcer.evaluate_canary(policy=p, baseline_metric=0.5, candidate_metric=0.55, sample_count=20)
    assert c["action"] == "promote"

    lg = guardrail_logger.log_guardrail_event(event="train_gate", status="ok", payload={"metric": 0.6})
    assert lg["ok"] is True
    rows = ExecutionReportSQLite().recent(limit=20)
    assert any((r.get("payload") or {}).get("kind") == "learning_guardrail" for r in rows)


def test_ws_common_last_price_and_health_logger(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.market_data.ws_common as ws_common
    import services.ws.last_price_provider as last_price_provider
    import services.monitoring.ws_health_logger as ws_health_logger

    importlib.reload(ws_common)
    importlib.reload(last_price_provider)
    importlib.reload(ws_health_logger)

    tick = ws_common.normalize_ticker_message({"symbol": "btc-usd", "best_bid": "99", "best_ask": "101"}, venue="coinbase")
    assert tick["symbol"] == "BTC/USD"
    assert tick["bid"] == 99.0

    monkeypatch.setattr(last_price_provider, "get_best_bid_ask_last", lambda venue, symbol: {"ts_ms": 1000, "bid": 99.0, "ask": 101.0, "last": 100.0})
    monkeypatch.setattr(last_price_provider, "_now_ms", lambda: 1200)
    px = last_price_provider.get_last_price(venue="coinbase", symbol="BTC/USD")
    assert px["ok"] is True
    assert px["price"] == 100.0

    out = ws_health_logger.log_ws_health(exchange="coinbase", symbol="BTC/USD", connected=True, recv_ts_ms=1000, lag_ms=50.0)
    assert out["ok"] is True
    rec = ws_health_logger.recent_ws_health(limit=10)
    assert rec["count"] >= 1


def test_strategy_validation_presets_and_overlay_impact():
    import services.strategies.validation as validation
    import services.strategies.presets as presets
    import services.analytics.overlay_impact as overlay_impact

    good = validation.validate_strategy_config({"strategy": {"name": "ema_cross", "ema_fast": 12, "ema_slow": 26}})
    assert good["ok"] is True
    bad = validation.validate_strategy_config({"strategy": {"name": "unknown"}})
    assert bad["ok"] is False

    names = presets.list_presets()
    assert "ema_cross_default" in names
    cfg = presets.apply_preset({"a": 1}, "ema_cross_default", overrides={"strategy": {"ema_fast": 9}})
    assert cfg["strategy"]["ema_fast"] == 9

    imp = overlay_impact.summarize_overlay_impact(
        baseline=[{"pnl": 1.0}, {"pnl": -0.5}],
        overlay=[{"pnl": 2.0}, {"pnl": -0.2}],
    )
    assert imp["ok"] is True
    assert imp["delta_pnl"] == 1.3
