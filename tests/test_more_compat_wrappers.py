from __future__ import annotations

import importlib


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_more_compat_modules_import(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)

    modules = [
        "services.alerts.alert_router",
        "services.execution.reconciliation",
        "services.reconciliation.symbol_mapping",
        "services.risk.fill_hook",
        "services.strategies.live_consensus_filter",
    ]

    for name in modules:
        mod = importlib.import_module(name)
        assert mod is not None


def test_rate_limiter_blocks_then_releases(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.alerts.rate_limiter as rate_limiter

    importlib.reload(rate_limiter)

    first = rate_limiter.allow(key="order_event::error", min_interval_sec=60, now_ts=100.0)
    second = rate_limiter.allow(key="order_event::error", min_interval_sec=60, now_ts=120.0)
    third = rate_limiter.allow(key="order_event::error", min_interval_sec=60, now_ts=161.0)

    assert first["allowed"] is True
    assert second["allowed"] is False
    assert third["allowed"] is True


def test_split_symbol_compat_handles_common_shapes():
    from core.symbol_parse import split_symbol as core_split_symbol
    from services.market_data.symbol_utils import split_symbol as market_split_symbol

    assert core_split_symbol("BTC/USD") == ("BTC", "USD")
    assert core_split_symbol("BTC_USDT") == ("BTC", "USDT")
    assert core_split_symbol("BTCUSDT") == ("BTC", "USDT")
    assert market_split_symbol("ETH-USD") == ("ETH", "USD")


def test_fill_hook_records_fill_and_updates_risk_daily(tmp_path):
    from services.risk.fill_hook import record_fill
    from services.risk.fill_ledger import FillLedgerDB
    from services.risk.risk_daily import RiskDailyDB

    exec_db = tmp_path / "execution.sqlite"
    fill = {
        "venue": "coinbase",
        "fill_id": "fill-1",
        "symbol": "BTC/USD",
        "realized_pnl_usd": 12.5,
        "fee_usd": 1.25,
    }

    record_fill(str(exec_db), fill)
    record_fill(str(exec_db), fill)

    daily = RiskDailyDB(str(exec_db)).get()
    ledger_rows = FillLedgerDB(str(exec_db)).list_recent()

    assert daily["realized_pnl_usd"] == 12.5
    assert daily["fees_usd"] == 1.25
    assert ledger_rows[0]["symbol"] == "BTC/USD"
    assert ledger_rows[0]["realized_pnl_usd"] == 12.5


def test_consensus_signal_engine_scores_recent_weighted_signals(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)

    import storage.signal_inbox_sqlite as signal_inbox_sqlite
    import storage.signal_reliability_sqlite as signal_reliability_sqlite
    import services.learning.consensus_signal_engine as consensus_signal_engine

    importlib.reload(signal_inbox_sqlite)
    importlib.reload(signal_reliability_sqlite)
    importlib.reload(consensus_signal_engine)

    inbox = signal_inbox_sqlite.SignalInboxSQLite()
    inbox.upsert_signal(
        {
            "signal_id": "sig-1",
            "ts": "2026-03-09T12:00:00+00:00",
            "source": "webhook",
            "author": "alice",
            "symbol": "BTC-USD",
            "action": "buy",
            "confidence": 0.9,
            "raw": {},
        }
    )
    inbox.upsert_signal(
        {
            "signal_id": "sig-2",
            "ts": "2026-03-09T12:05:00+00:00",
            "source": "webhook",
            "author": "bob",
            "symbol": "BTC-USD",
            "action": "sell",
            "confidence": 0.3,
            "raw": {},
        }
    )

    reliability = signal_reliability_sqlite.SignalReliabilitySQLite()
    reliability.upsert(
        {
            "id": "rel-1",
            "updated_ts": "2026-03-09T12:10:00+00:00",
            "source": "webhook",
            "author": "alice",
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "timeframe": "1h",
            "horizon_candles": 4,
            "threshold_bps": 10.0,
            "n_signals": 10,
            "n_scored": 10,
            "hit_rate": 0.9,
            "avg_return_bps": 15.0,
            "avg_abs_return_bps": 20.0,
            "notes": "",
        }
    )
    reliability.upsert(
        {
            "id": "rel-2",
            "updated_ts": "2026-03-09T12:10:00+00:00",
            "source": "webhook",
            "author": "bob",
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "timeframe": "1h",
            "horizon_candles": 4,
            "threshold_bps": 10.0,
            "n_signals": 10,
            "n_scored": 10,
            "hit_rate": 0.2,
            "avg_return_bps": -5.0,
            "avg_abs_return_bps": 20.0,
            "notes": "",
        }
    )

    result = consensus_signal_engine.compute_consensus(
        symbols=["BTC-USD"],
        lookback_signals=10,
        max_signal_age_sec=60 * 60 * 24 * 365,
        min_weight=0.0,
        lookback_evals=10,
        min_evals=1,
    )

    row = result["consensus"]["BTC-USD"]
    assert row["count"] == 2
    assert row["contributors"] == 2
    assert row["score"] > 0
