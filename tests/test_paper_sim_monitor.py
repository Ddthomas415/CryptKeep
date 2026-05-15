from __future__ import annotations

import json

import pytest

from services.analytics import paper_sim_monitor as svc


def test_collect_once_reports_enough_evidence_for_completed_round_trip(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "completed",
            "reason": "completed",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "current_strategy": "sma_200_trend",
            "current_strategy_preset": "es_daily_trend_v1",
            "results": [
                {
                    "strategy": "sma_200_trend",
                    "strategy_preset": "es_daily_trend_v1",
                    "fills_delta": 2,
                    "closed_trades_delta": 1,
                    "net_realized_pnl_delta": -0.0872,
                }
            ],
        },
    )
    monkeypatch.setattr(
        svc,
        "_configured_strategy_runner",
        lambda: {
            "strategy": "momentum",
            "symbols": ["BTC/USD"],
            "primary_symbol": "BTC/USD",
            "signal_source": "synthetic_mid_ohlcv",
            "venue": "coinbase",
        },
    )
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "stopped", "strategy_preset": "es_daily_trend_v1"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(
        svc,
        "_paper_state_snapshot",
        lambda symbol: {
            "position": {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": -0.8933},
            "latest_order": {"order_id": "ord-2", "status": "filled"},
            "latest_paper_fill": {"fill_id": "fill-2", "ts": "2026-05-15T01:03:46Z", "price": 81574.41},
            "latest_equity": {"ts": "2026-05-15T01:03:46Z", "unrealized_pnl": 0.0, "realized_pnl": -0.8933},
        },
    )
    monkeypatch.setattr(
        svc,
        "_trade_journal_snapshot",
        lambda: {"fill_id": "fill-2", "fill_ts": "2026-05-15T01:03:46Z", "side": "sell", "symbol": "BTC/USDT"},
    )

    out = svc.collect_once(svc.PaperSimMonitorCfg(min_closed_trades_for_enough_evidence=1))

    assert out["campaign_status"] == "completed"
    assert out["current_strategy"] == "sma_200_trend"
    assert out["current_strategy_preset"] == "es_daily_trend_v1"
    assert out["strategy_label"] == "es_daily_trend_v1"
    assert out["round_trips_observed"] == 1
    assert out["fills_observed"] == 2
    assert out["current_window_realized_pnl"] == -0.0872
    assert out["position_realized_pnl_total"] == -0.8933
    assert out["recommendation"] == "enough_evidence"
    assert out["recommendation_reason"] == "closed_trade_threshold_met"
    assert "recommendation=enough_evidence" in out["summary_text"]


def test_collect_once_reports_investigate_for_market_data_block(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "running",
            "reason": "collecting",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "current_strategy": "sma_200_trend",
            "results": [{"strategy": "sma_200_trend", "runner_note": "no_public_ohlcv"}],
        },
    )
    monkeypatch.setattr(
        svc,
        "_configured_strategy_runner",
        lambda: {
            "strategy": "momentum",
            "symbols": ["BTC/USD"],
            "primary_symbol": "BTC/USD",
            "signal_source": "synthetic_mid_ohlcv",
            "venue": "coinbase",
        },
    )
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "running", "note": "no_public_ohlcv"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "running"})
    monkeypatch.setattr(
        svc,
        "_paper_state_snapshot",
        lambda symbol: {
            "position": {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0},
            "latest_order": {},
            "latest_paper_fill": {},
            "latest_equity": {},
        },
    )
    monkeypatch.setattr(svc, "_trade_journal_snapshot", lambda: {})

    out = svc.collect_once(svc.PaperSimMonitorCfg())

    assert out["recommendation"] == "investigate"
    assert out["recommendation_reason"] == "market_data_blocked"


@pytest.mark.slow
def test_run_forever_writes_status_and_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    snapshots = [
        {
            "ok": True,
            "ts": "2026-05-15T02:05:00Z",
            "monitor_name": svc.MONITOR_NAME,
            "campaign_status": "running",
            "campaign_reason": "collecting",
            "recommendation": "continue",
            "recommendation_reason": "campaign_progress_visible",
            "strategy_label": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "fills_observed": 1,
            "round_trips_observed": 0,
            "current_window_realized_pnl": 0.0,
            "position_realized_pnl_total": 0.0,
            "equity_realized_pnl_total": 0.0,
            "unrealized_pnl": 1.2,
            "paper_position": {"qty": 0.001},
            "latest_order": {"order_id": "ord-1", "status": "filled"},
            "latest_paper_fill": {},
            "latest_journal_fill": {"fill_id": "fill-1"},
            "latest_equity": {"unrealized_pnl": 1.2},
            "campaign_result": {},
            "collector": {"status": "running"},
            "strategy_runner": {"status": "running"},
            "paper_engine": {"status": "running"},
            "summary_text": "snapshot",
        }
    ]
    monkeypatch.setattr(svc, "collect_once", lambda cfg: dict(snapshots[0]))
    monkeypatch.setattr(svc.time, "sleep", lambda *_args, **_kwargs: None)

    out = svc.run_forever(svc.PaperSimMonitorCfg(poll_interval_sec=0.01), max_loops=1)

    assert out["ok"] is True
    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
    assert out["changes_written"] == 1
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["recommendation"] == "continue"
    lines = [line for line in svc.history_file().read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["trigger_reasons"] == ["initial_snapshot"]
