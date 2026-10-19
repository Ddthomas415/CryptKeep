import copy

import pytest

from services.strategies.runtime_execution_identity import capture_intent_identity, loaded_functions_digest


def inputs():
    return {
        "cfg": {"qty": .001, "order_type": "market", "position_aware": True,
                "sell_full_position": True, "allow_first_signal_trade": False,
                "stop_loss_pct": 0.0, "take_profit_pct": 0.0,
                "trailing_stop_pct": 0.0, "max_bars_hold": 0},
        "strategy": {"name": "sma_200_trend", "trade_enabled": True,
                     "sma_period": 200, "atr_period": 20, "evidence_extra": {"price": 123},
                     "apiKey": "do-not-copy"},
        "market": {"venue": "coinbase", "symbol": "BTC/USDT", "timeframe": "1d",
                   "source": "public_ohlcv", "sample_mode": False},
        "paper_config": {"fee_bps":7.5,"slippage_bps":5.0,"apiKey":"do-not-copy"},
        "implementation": {key:"a"*64 for key in ("signal","resolver","exits","paper_engine")},
    }


def enable(monkeypatch):
    monkeypatch.setenv("CBP_CAPTURE_EXECUTION_IDENTITY", "1")
    monkeypatch.setenv("CBP_EXECUTION_IDENTITY_COHORT_ID", "synthetic-only")


def test_disabled_capture_does_not_read_inputs(monkeypatch):
    monkeypatch.delenv("CBP_CAPTURE_EXECUTION_IDENTITY", raising=False)
    assert capture_intent_identity(cfg=None,strategy=None,market=None,paper_config=None,implementation=None)=={}


def test_capture_is_allowlisted_and_detached(monkeypatch):
    enable(monkeypatch)
    data = inputs()
    result = capture_intent_identity(**data)
    assert result["execution_identity_capture_status"] == "captured"
    payload = result["execution_identity"]
    assert "apiKey" not in payload["parameters"] and "apiKey" not in payload["costs"]
    assert "evidence_extra" not in payload["parameters"]
    data["strategy"]["sma_period"] = 20
    assert payload["parameters"]["sma_period"] == 200


@pytest.mark.parametrize("field", ["sma_period", "atr_period", "trade_enabled"])
def test_unresolved_signal_capture_fails_without_order_decision(monkeypatch, field):
    enable(monkeypatch)
    data=inputs()
    del data["strategy"][field]
    assert capture_intent_identity(**data)=={"execution_identity_capture_status":"failed","execution_identity_error_type":"ValueError"}


def test_changes_and_dynamic_quote_exclusion(monkeypatch):
    enable(monkeypatch)
    data=inputs()
    baseline=capture_intent_identity(**data)["execution_identity_sha256"]
    data["strategy"]["evidence_extra"]["price"]=999
    assert capture_intent_identity(**data)["execution_identity_sha256"]==baseline
    data["strategy"]["sma_period"]=20
    assert capture_intent_identity(**data)["execution_identity_sha256"]!=baseline


def test_missing_cohort_and_bad_cost_do_not_raise(monkeypatch):
    enable(monkeypatch)
    monkeypatch.delenv("CBP_EXECUTION_IDENTITY_COHORT_ID")
    assert capture_intent_identity(**inputs())["execution_identity_capture_status"]=="failed"
    enable(monkeypatch)
    data=inputs()
    data["paper_config"]["fee_bps"]="private-invalid-value"
    result=capture_intent_identity(**data)
    assert result=={"execution_identity_capture_status":"failed","execution_identity_error_type":"ValueError"}
    assert "private-invalid-value" not in str(result)


def test_loaded_default_changes_fingerprint():
    def sample(value=1):
        return value
    before=loaded_functions_digest({"sample":sample})
    sample.__defaults__=(2,)
    assert loaded_functions_digest({"sample":sample})!=before


def test_unused_overrides_do_not_mislabel_effective_policy(monkeypatch):
    enable(monkeypatch)
    data = inputs()
    before = capture_intent_identity(**data)
    data["strategy"].update(regime_trending_floor=99, atr_stop_multiplier=99)
    after = capture_intent_identity(**data)
    assert after == before
    assert after["execution_identity"]["parameters"]["regime"] == {
        "lookback_days": 60, "trending_floor": .8, "chop_ceiling": .6,
        "chop_days": 5, "high_vol_ceiling": 2.5,
    }


def test_actual_runner_hook_success_and_failure(monkeypatch):
    from services.execution import strategy_runner as runner
    data = inputs()
    kwargs = dict(cfg=data["cfg"], strategy=data["strategy"], venue="coinbase",
                  symbol="BTC/USDT", provenance={"market_data_source":"public_ohlcv",
                  "ohlcv_timeframe":"1d", "ohlcv_sample_mode":False})
    monkeypatch.delenv("CBP_CAPTURE_EXECUTION_IDENTITY", raising=False)
    assert runner._execution_identity_meta(**kwargs) == {}
    enable(monkeypatch)
    monkeypatch.setattr(runner, "load_user_yaml", lambda **kw: {"paper_trading":data["paper_config"]})
    captured = runner._execution_identity_meta(**kwargs)
    assert captured["execution_identity_capture_status"] == "captured"
    assert captured["execution_identity"]["parameters"]["sma_period"] == 200
    def broken(**kw):
        raise OSError("injected")
    monkeypatch.setattr(runner, "load_user_yaml", broken)
    assert runner._execution_identity_meta(**kwargs) == {
        "execution_identity_capture_status":"failed", "execution_identity_error_type":"OSError"}


def test_queue_and_order_metadata_roundtrip(monkeypatch, tmp_path):
    enable(monkeypatch)
    from storage.intent_queue_sqlite import IntentQueueSQLite
    from storage.paper_trading_sqlite import PaperTradingSQLite
    monkeypatch.setattr("storage.intent_queue_sqlite.DB_PATH", tmp_path/"queue.sqlite")
    monkeypatch.setattr("storage.paper_trading_sqlite.DB_PATH", tmp_path/"paper.sqlite")
    meta=capture_intent_identity(**inputs())
    queue=IntentQueueSQLite()
    row={"intent_id":"synthetic-buy","source":"strategy_runner","created_ts":"2026-10-08T12:00:00Z",
         "ts":"2026-10-08T12:00:00Z","venue":"coinbase","symbol":"BTC/USDT",
         "side":"buy","order_type":"market","qty":.001,"status":"queued","meta":meta}
    queue.upsert_intent(row)
    queued=queue.get_intent("synthetic-buy")
    assert queued["meta"]==meta
    # Actual consumer-to-engine call is not exercised in this storage proof.
    paper=PaperTradingSQLite()
    paper.insert_order({"order_id":"synthetic-order","client_order_id":"synthetic-buy",
                        "created_ts":row["created_ts"],"ts":row["ts"],"venue":row["venue"],
                        "symbol":row["symbol"],"side":"buy","order_type":"market","qty":.001,
                        "status":"open","meta":copy.deepcopy(queued["meta"])})
    assert paper.get_order_by_order_id("synthetic-order")["meta"]==meta
