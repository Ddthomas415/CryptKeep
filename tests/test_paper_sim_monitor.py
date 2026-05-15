from __future__ import annotations

import json
from pathlib import Path

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
        "_paper_state_snapshot_window",
        lambda symbol, since_ts="": {
            "position": {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": -0.8933},
            "latest_order": {"order_id": "ord-2", "status": "filled"},
            "latest_paper_fill": {"fill_id": "fill-2", "ts": "2026-05-15T01:03:46Z", "price": 81574.41},
            "latest_equity": {"ts": "2026-05-15T01:03:46Z", "unrealized_pnl": 0.0, "realized_pnl": -0.8933},
        },
    )
    monkeypatch.setattr(
        svc,
        "_trade_journal_snapshot",
        lambda symbol, since_ts="": {"fill_id": "fill-2", "fill_ts": "2026-05-15T01:03:46Z", "side": "sell", "symbol": str(symbol)},
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


def test_collect_once_ignores_stale_fill_from_other_symbol(monkeypatch) -> None:
    class _FakePaperStore:
        def get_position(self, symbol: str):
            return {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0}

        def list_positions(self, limit: int = 1):
            return []

        def list_orders(self, limit: int = 500):
            return [
                {"order_id": "ord-stale", "symbol": "BTC/USDT", "status": "filled"},
                {"order_id": "ord-current", "symbol": "BTC/USD", "status": "open"},
            ]

        def list_fills_for_order(self, order_id: str, limit: int = 2000):
            if str(order_id) == "ord-stale":
                return [{"fill_id": "fill-stale", "order_id": "ord-stale", "ts": "2026-05-15T01:03:46Z", "price": 81574.41, "qty": 0.001, "fee": 0.0, "fee_currency": "USDT"}]
            return []

        def list_equity(self, limit: int = 1):
            return [{"ts": "2026-05-15T18:02:30Z", "cash_quote": 10000.0, "equity_quote": 10000.0, "unrealized_pnl": 0.0, "realized_pnl": 0.0}]

    class _FakeJournalStore:
        def list_fills(self, limit: int = 1000):
            return [
                {"fill_id": "fill-stale", "fill_ts": "2026-05-15T01:03:46Z", "side": "sell", "symbol": "BTC/USDT"},
            ]

    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "completed",
            "reason": "completed",
            "symbol": "BTC/USD",
            "venue": "coinbase",
            "current_strategy": "ema_cross",
            "current_strategy_preset": "ema_cross_default",
            "results": [
                {
                    "strategy": "ema_cross",
                    "strategy_preset": "ema_cross_default",
                    "fills_delta": 0,
                    "closed_trades_delta": 0,
                    "net_realized_pnl_delta": 0.0,
                }
            ],
        },
    )
    monkeypatch.setattr(
        svc,
        "_configured_strategy_runner",
        lambda: {
            "strategy": "ema_cross",
            "symbols": ["BTC/USD"],
            "primary_symbol": "BTC/USD",
            "signal_source": "synthetic_mid_ohlcv",
            "venue": "coinbase",
        },
    )
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "stopped", "strategy_preset": "ema_cross_default"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(svc, "PaperTradingSQLite", lambda: _FakePaperStore())
    monkeypatch.setattr(svc, "TradeJournalSQLite", lambda: _FakeJournalStore())

    out = svc.collect_once(svc.PaperSimMonitorCfg(min_closed_trades_for_enough_evidence=1))

    assert out["symbol"] == "BTC/USD"
    assert out["latest_journal_fill"] == {}
    assert out["latest_paper_fill"] == {}
    assert out["latest_order"]["symbol"] == "BTC/USD"
    assert out["recommendation"] == "investigate"
    assert out["recommendation_reason"] == "completed_without_trade_evidence"
    assert "no fill yet" in out["summary_text"]


def test_register_and_delete_watch_persist_local_definition(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    created = svc.register_watch(name="next_fill", trigger="new_fill")

    assert created["ok"] is True
    assert created["name"] == "next_fill"
    assert created["trigger"] == "new_fill"
    assert svc.watches_file().exists()
    assert svc.list_watches()[0]["name"] == "next_fill"

    deleted = svc.delete_watch(name="next_fill")

    assert deleted["ok"] is True
    assert svc.list_watches() == []


def test_run_forever_writes_watch_report_when_named_watch_fires(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.register_watch(name="watch_fill", trigger="new_fill")
    notify_calls: list[dict[str, object]] = []
    snapshots = iter(
        [
            {
                "ok": True,
                "ts": "2026-05-15T02:05:00Z",
                "monitor_name": svc.MONITOR_NAME,
                "campaign_status": "running",
                "campaign_reason": "collecting",
                "recommendation": "continue",
                "recommendation_reason": "awaiting_first_trade",
                "strategy_label": "es_daily_trend_v1",
                "symbol": "BTC/USDT",
                "fills_observed": 0,
                "round_trips_observed": 0,
                "current_window_realized_pnl": 0.0,
                "position_realized_pnl_total": 0.0,
                "equity_realized_pnl_total": 0.0,
                "unrealized_pnl": 0.0,
                "paper_position": {"qty": 0.0},
                "latest_order": {},
                "latest_paper_fill": {},
                "latest_journal_fill": {},
                "latest_equity": {},
                "campaign_result": {},
                "collector": {"status": "running"},
                "strategy_runner": {"status": "running"},
                "paper_engine": {"status": "running"},
                "summary_text": "before",
            },
            {
                "ok": True,
                "ts": "2026-05-15T02:05:30Z",
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
                "unrealized_pnl": 0.0,
                "paper_position": {"qty": 0.001},
                "latest_order": {"order_id": "ord-1", "status": "filled"},
                "latest_paper_fill": {},
                "latest_journal_fill": {"fill_id": "fill-1", "side": "buy", "fill_ts": "2026-05-15T02:05:30Z"},
                "latest_equity": {},
                "campaign_result": {},
                "collector": {"status": "running"},
                "strategy_runner": {"status": "running"},
                "paper_engine": {"status": "running"},
                "summary_text": "after",
            },
        ]
    )
    monkeypatch.setattr(svc, "collect_once", lambda cfg: dict(next(snapshots)))
    monkeypatch.setattr(
        svc,
        "_notify_local_desktop",
        lambda payload: notify_calls.append(dict(payload)) or {"attempted": True, "sent": True, "reason": "notified"},
    )
    monkeypatch.setattr(svc.time, "sleep", lambda *_args, **_kwargs: None)

    out = svc.run_forever(svc.PaperSimMonitorCfg(poll_interval_sec=0.01), max_loops=2)

    assert out["ok"] is True
    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
    assert out["last_watch_reports_written"]
    report = out["last_watch_reports_written"][0]
    assert report["watch_name"] == "watch_fill"
    assert report["desktop_notification"]["sent"] is True
    assert Path(report["json_path"]).exists()
    assert Path(report["markdown_path"]).exists()
    assert notify_calls
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["recent_watch_reports"][0]["watch_name"] == "watch_fill"
    assert status["watches"][0]["last_report_stem"] == report["report_stem"]


def test_run_forever_does_not_fire_new_fill_watch_on_initial_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.register_watch(name="watch_fill", trigger="new_fill")
    notify_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        svc,
        "_notify_local_desktop",
        lambda payload: notify_calls.append(dict(payload)) or {"attempted": True, "sent": True, "reason": "notified"},
    )
    monkeypatch.setattr(
        svc,
        "collect_once",
        lambda cfg: {
            "ok": True,
            "ts": "2026-05-15T02:05:00Z",
            "monitor_name": svc.MONITOR_NAME,
            "campaign_status": "running",
            "campaign_reason": "collecting",
            "recommendation": "continue",
            "recommendation_reason": "awaiting_first_trade",
            "strategy_label": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "fills_observed": 1,
            "round_trips_observed": 0,
            "current_window_realized_pnl": 0.0,
            "position_realized_pnl_total": 0.0,
            "equity_realized_pnl_total": 0.0,
            "unrealized_pnl": 0.0,
            "paper_position": {"qty": 0.001},
            "latest_order": {"order_id": "ord-1", "status": "filled"},
            "latest_paper_fill": {},
            "latest_journal_fill": {"fill_id": "fill-1", "side": "buy", "fill_ts": "2026-05-15T02:05:00Z"},
            "latest_equity": {},
            "campaign_result": {},
            "collector": {"status": "running"},
            "strategy_runner": {"status": "running"},
            "paper_engine": {"status": "running"},
            "summary_text": "baseline",
        },
    )
    monkeypatch.setattr(svc.time, "sleep", lambda *_args, **_kwargs: None)

    out = svc.run_forever(svc.PaperSimMonitorCfg(poll_interval_sec=0.01), max_loops=1)

    assert out["ok"] is True
    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
    assert out["last_watch_reports_written"] == []
    assert notify_calls == []
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["recent_watch_reports"] == []
    assert status["watches"][0]["last_report_stem"] == ""


def test_run_forever_collects_final_snapshot_before_stop(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.register_watch(name="done", trigger="campaign_completed")
    monkeypatch.setattr(
        svc,
        "_notify_local_desktop",
        lambda payload: {"attempted": True, "sent": True, "reason": "notified"},
    )
    snapshots = iter(
        [
            {
                "ok": True,
                "ts": "2026-05-15T02:05:00Z",
                "monitor_name": svc.MONITOR_NAME,
                "campaign_status": "running",
                "campaign_reason": "collecting",
                "recommendation": "continue",
                "recommendation_reason": "awaiting_first_trade",
                "strategy_label": "es_daily_trend_v1",
                "symbol": "BTC/USDT",
                "fills_observed": 0,
                "round_trips_observed": 0,
                "current_window_realized_pnl": 0.0,
                "position_realized_pnl_total": 0.0,
                "equity_realized_pnl_total": 0.0,
                "unrealized_pnl": 0.0,
                "paper_position": {"qty": 0.0},
                "latest_order": {},
                "latest_paper_fill": {},
                "latest_journal_fill": {},
                "latest_equity": {},
                "campaign_result": {},
                "collector": {"status": "running"},
                "strategy_runner": {"status": "running"},
                "paper_engine": {"status": "running"},
                "summary_text": "before",
            },
            {
                "ok": True,
                "ts": "2026-05-15T02:06:00Z",
                "monitor_name": svc.MONITOR_NAME,
                "campaign_status": "completed",
                "campaign_reason": "completed",
                "recommendation": "enough_evidence",
                "recommendation_reason": "closed_trade_threshold_met",
                "strategy_label": "es_daily_trend_v1",
                "symbol": "BTC/USDT",
                "fills_observed": 2,
                "round_trips_observed": 1,
                "current_window_realized_pnl": 1.25,
                "position_realized_pnl_total": 1.25,
                "equity_realized_pnl_total": 1.25,
                "unrealized_pnl": 0.0,
                "paper_position": {"qty": 0.0},
                "latest_order": {"order_id": "ord-2", "status": "filled"},
                "latest_paper_fill": {},
                "latest_journal_fill": {"fill_id": "fill-2", "side": "sell", "fill_ts": "2026-05-15T02:06:00Z"},
                "latest_equity": {},
                "campaign_result": {},
                "collector": {"status": "completed"},
                "strategy_runner": {"status": "stopped"},
                "paper_engine": {"status": "stopped"},
                "summary_text": "after",
            },
        ]
    )
    monkeypatch.setattr(svc, "collect_once", lambda cfg: dict(next(snapshots)))

    def _sleep(_seconds: float) -> None:
        svc.stop_file().parent.mkdir(parents=True, exist_ok=True)
        svc.stop_file().write_text("stop\n", encoding="utf-8")

    monkeypatch.setattr(svc.time, "sleep", _sleep)

    out = svc.run_forever(svc.PaperSimMonitorCfg(poll_interval_sec=0.01))

    assert out["ok"] is True
    assert out["status"] == "stopped"
    assert out["campaign_status"] == "completed"
    assert out["recommendation"] == "enough_evidence"
    assert out["last_watch_reports_written"]
    assert out["last_watch_reports_written"][0]["watch_name"] == "done"
    assert out["last_watch_reports_written"][0]["desktop_notification"]["sent"] is True
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["campaign_status"] == "completed"
    assert status["recent_watch_reports"][0]["watch_name"] == "done"


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
    assert status["watches"] == []
