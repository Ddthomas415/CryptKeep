from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.analytics import paper_sim_monitor as svc


@pytest.fixture(autouse=True)
def _stub_promotion_progress(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "_promotion_progress_snapshot",
        lambda: {
            "ok": True,
            "source": "paper_promotion_progress",
            "days_recorded": 22,
            "days_required": 30,
            "days_remaining": 8,
            "round_trips_recorded": 7,
            "round_trips_required": 50,
            "round_trips_remaining": 3,
            "thresholds_ready": False,
            "blocking_thresholds": [
                {"label": "30 calendar days of operation", "remaining": 8},
                {"label": "10+ completed round trips", "remaining": 3},
            ],
            "summary_text": "Promotion threshold progress: 22/30 days recorded (8 remaining), 7/10 round trips recorded (3 remaining).",
        },
    )


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
    monkeypatch.setattr(
        svc,
        "_strategy_runner_status",
        lambda: {"status": "stopped", "strategy_preset": "es_daily_trend_v1"},
    )
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(
        svc,
        "_paper_state_snapshot_window",
        lambda symbol, since_ts="", until_ts="": {
            "position": {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": -0.8933},
            "latest_order": {"order_id": "ord-2", "status": "filled"},
            "latest_paper_fill": {"fill_id": "fill-2", "ts": "2026-05-15T01:03:46Z", "price": 81574.41},
            "latest_equity": {"ts": "2026-05-15T01:03:46Z", "unrealized_pnl": 0.0, "realized_pnl": -0.8933},
        },
    )
    monkeypatch.setattr(
        svc,
        "_trade_journal_snapshot",
        lambda symbol, since_ts="", until_ts="": {
            "fill_id": "fill-2",
            "fill_ts": "2026-05-15T01:03:46Z",
            "side": "sell",
            "symbol": str(symbol),
        },
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
    assert out["promotion_thresholds_ready"] is False
    assert out["promotion_progress"]["days_remaining"] == 8
    assert out["promotion_progress"]["round_trips_remaining"] == 3
    assert out["recommendation"] == "enough_evidence"
    assert out["recommendation_reason"] == "closed_trade_threshold_met"
    assert "recommendation=enough_evidence" in out["summary_text"]
    assert "Promotion threshold progress" in out["summary_text"]


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
        "_paper_state_snapshot_window",
        lambda symbol, since_ts="", until_ts="": {
            "position": {"symbol": symbol, "qty": 0.0, "avg_price": 0.0, "realized_pnl": 0.0},
            "latest_order": {},
            "latest_paper_fill": {},
            "latest_equity": {},
        },
    )
    monkeypatch.setattr(svc, "_trade_journal_snapshot", lambda symbol, since_ts="", until_ts="": {})

    out = svc.collect_once(svc.PaperSimMonitorCfg())

    assert out["recommendation"] == "investigate"
    assert out["recommendation_reason"] == "market_data_blocked"


def test_collect_once_does_not_label_lifetime_pnl_as_idle_window_pnl(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "idle",
            "reason": "waiting_for_next_day",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "current_strategy": "sma_200_trend",
            "current_strategy_preset": "es_daily_trend_v1",
            "results": [],
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
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(
        svc,
        "_paper_state_snapshot_window",
        lambda symbol, since_ts="", until_ts="": {
            "position": {
                "symbol": symbol,
                "qty": 0.0,
                "avg_price": 0.0,
                "realized_pnl": 36.52,
            },
            "latest_order": {},
            "latest_paper_fill": {},
            "latest_equity": {"realized_pnl": -1014.39, "unrealized_pnl": 0.0},
            "window_fill_count": 0,
            "window_exit_fill_count": 0,
        },
    )
    monkeypatch.setattr(svc, "_trade_journal_snapshot", lambda symbol, since_ts="", until_ts="": {})

    out = svc.collect_once(svc.PaperSimMonitorCfg())

    assert out["current_window_realized_pnl"] is None
    assert out["current_window_realized_pnl_known"] is False
    assert out["current_window_realized_pnl_source"] == "unavailable"
    assert out["position_realized_pnl_total"] == 36.52
    assert out["equity_realized_pnl_total"] == -1014.39
    assert "current_window_realized_pnl=unavailable" in out["summary_text"]


def test_collect_once_surfaces_persisting_evidence_phase_in_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "running",
            "reason": "persisting_evidence",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "current_strategy": "",
            "current_strategy_preset": "es_daily_trend_v1",
            "last_completed_strategy": "sma_200_trend",
            "results": [
                {
                    "strategy": "sma_200_trend",
                    "strategy_preset": "es_daily_trend_v1",
                    "fills_delta": 1,
                    "closed_trades_delta": 0,
                    "net_realized_pnl_delta": -0.0299,
                    "latest_fill_ts": "2026-05-18T23:50:53.429586+00:00",
                }
            ],
        },
    )
    monkeypatch.setattr(
        svc,
        "_configured_strategy_runner",
        lambda: {
            "strategy": "sma_200_trend",
            "symbols": ["BTC/USDT"],
            "primary_symbol": "BTC/USDT",
            "signal_source": "public_ohlcv_1d",
            "venue": "coinbase",
        },
    )
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "stopped", "strategy_preset": "es_daily_trend_v1"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})
    monkeypatch.setattr(
        svc,
        "_paper_state_snapshot_window",
        lambda symbol, since_ts="", until_ts="": {
            "position": {"symbol": symbol, "qty": 0.001, "avg_price": 39864.652365, "realized_pnl": 0.0},
            "latest_order": {"order_id": "ord-1", "status": "filled"},
            "latest_paper_fill": {"fill_id": "fill-1", "ts": "2026-05-18T23:50:53.429586+00:00", "price": 39864.652365, "qty": 0.001, "fee": 0.0299},
            "latest_equity": {"ts": "2026-05-18T23:51:15.800865+00:00", "unrealized_pnl": -0.2798, "realized_pnl": 0.0},
        },
    )
    monkeypatch.setattr(
        svc,
        "_trade_journal_snapshot",
        lambda symbol, since_ts="", until_ts="": {
            "fill_id": "fill-1",
            "fill_ts": "2026-05-18T23:50:53.429586+00:00",
            "side": "buy",
            "symbol": str(symbol),
        },
    )

    out = svc.collect_once(svc.PaperSimMonitorCfg())

    assert out["campaign_status"] == "running"
    assert out["campaign_reason"] == "persisting_evidence"
    assert out["recommendation"] == "continue"
    assert "campaign persisting evidence" in out["summary_text"]


def test_collect_once_uses_daily_loop_last_result_when_idle(monkeypatch) -> None:
    captured_window: dict[str, str] = {}

    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "idle",
            "reason": "waiting_for_next_day",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "current_strategy": "ema_cross",
            "current_strategy_preset": "ema_cross_default",
            "last_result": {
                "results": [
                    {
                        "strategy": "ema_cross",
                        "strategy_preset": "ema_cross_default",
                        "started_ts": "2026-06-05T19:54:50Z",
                        "ended_ts": "2026-06-05T20:09:54Z",
                        "fills_delta": 1,
                        "closed_trades_delta": 0,
                        "net_realized_pnl_delta": -0.0457,
                    }
                ]
            },
        },
    )
    monkeypatch.setattr(
        svc,
        "_configured_strategy_runner",
        lambda: {
            "strategy": "ema_cross",
            "symbols": ["BTC/USDT"],
            "primary_symbol": "BTC/USDT",
            "signal_source": "public_ohlcv_5m",
            "venue": "coinbase",
        },
    )
    monkeypatch.setattr(svc, "_strategy_runner_status", lambda: {"status": "stopped", "strategy_preset": "ema_cross_default"})
    monkeypatch.setattr(svc, "_paper_engine_status", lambda: {"status": "stopped"})

    def fake_paper_state(symbol, since_ts="", until_ts=""):
        captured_window["since_ts"] = since_ts
        captured_window["until_ts"] = until_ts
        return {
            "position": {"symbol": symbol, "qty": 0.001, "avg_price": 60949.1543475, "realized_pnl": 0.0},
            "latest_order": {"order_id": "ord-1", "status": "filled"},
            "latest_paper_fill": {
                "fill_id": "fill-1",
                "ts": "2026-06-05T20:09:45Z",
                "side": "buy",
                "price": 60949.1543475,
                "qty": 0.001,
            },
            "latest_equity": {"unrealized_pnl": -0.0011, "realized_pnl": 0.0},
            "window_fill_count": 1,
            "window_exit_fill_count": 0,
        }

    monkeypatch.setattr(svc, "_paper_state_snapshot_window", fake_paper_state)
    monkeypatch.setattr(
        svc,
        "_trade_journal_snapshot",
        lambda symbol, since_ts="", until_ts="": {
            "fill_id": "fill-1",
            "fill_ts": "2026-06-05T20:09:45Z",
            "side": "buy",
            "symbol": str(symbol),
        },
    )

    out = svc.collect_once(svc.PaperSimMonitorCfg())

    assert captured_window == {
        "since_ts": "2026-06-05T19:54:50Z",
        "until_ts": "2026-06-05T20:09:54Z",
    }
    assert out["campaign_status"] == "idle"
    assert out["fills_observed"] == 1
    assert out["latest_journal_fill"]["fill_id"] == "fill-1"
    assert out["campaign_result"]["strategy_preset"] == "ema_cross_default"
    assert "fills=1" in out["summary_text"]
    assert "latest_fill=buy@2026-06-05T20:09:45Z" in out["summary_text"]


def test_collect_once_ignores_post_window_same_symbol_artifacts(monkeypatch) -> None:
    class _FakePaperStore:
        def get_position(self, symbol: str):
            return {"symbol": symbol, "qty": 1.0, "avg_price": 100.0, "realized_pnl": 0.0}

        def list_positions(self, limit: int = 1):
            return []

        def list_orders(self, limit: int = 500):
            return [
                {
                    "order_id": "ord-late",
                    "created_ts": "2026-05-18T08:26:54Z",
                    "ts": "2026-05-18T08:26:54Z",
                    "symbol": "BTC/USD",
                    "side": "buy",
                    "status": "filled",
                }
            ]

        def list_fills_for_order(self, order_id: str, limit: int = 2000):
            return [
                {
                    "fill_id": "fill-late",
                    "order_id": str(order_id),
                    "ts": "2026-05-18T08:26:54Z",
                    "price": 100.0,
                    "qty": 1.0,
                    "fee": 0.0,
                    "fee_currency": "USDT",
                }
            ]

        def list_equity(self, limit: int = 1):
            return [
                {
                    "ts": "2026-05-18T08:26:54Z",
                    "cash_quote": 10000.0,
                    "equity_quote": 10000.0,
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0,
                }
            ]

    class _FakeJournalStore:
        def list_fills(self, limit: int = 1000):
            return [
                {
                    "fill_id": "fill-late",
                    "fill_ts": "2026-05-18T08:26:54Z",
                    "journal_ts": "2026-05-18T08:26:54Z",
                    "side": "buy",
                    "symbol": "BTC/USD",
                }
            ]

    monkeypatch.setattr(
        svc,
        "load_campaign_runtime_status",
        lambda: {
            "ok": True,
            "status": "completed",
            "reason": "completed",
            "ts": "2026-05-15T18:46:22Z",
            "symbol": "BTC/USD",
            "venue": "coinbase",
            "current_strategy": "ema_cross",
            "current_strategy_preset": "ema_cross_default",
            "results": [
                {
                    "strategy": "ema_cross",
                    "strategy_preset": "ema_cross_default",
                    "started_ts": "2026-05-15T18:46:12Z",
                    "ended_ts": "2026-05-15T18:46:20Z",
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

    assert out["paper_position"] == {}
    assert out["latest_order"] == {}
    assert out["latest_paper_fill"] == {}
    assert out["latest_journal_fill"] == {}
    assert out["fills_observed"] == 0
    assert out["round_trips_observed"] == 0
    assert out["recommendation"] == "investigate"
    assert out["recommendation_reason"] == "completed_without_trade_evidence"
    assert "no fill yet" in out["summary_text"]


def test_load_runtime_status_reconciles_stopped_snapshot_from_newer_collector(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.status_file().parent.mkdir(parents=True, exist_ok=True)
    svc.status_file().write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "stopped",
                "reason": "stop_requested",
                "ts": "2026-05-18T19:04:14Z",
                "loops": 17,
                "changes_written": 6,
                "poll_interval_sec": 5.0,
                "min_closed_trades_for_enough_evidence": 1,
                "desktop_notify": True,
                "campaign_status": "running",
                "campaign_reason": "collecting",
                "recommendation": "continue",
                "recommendation_reason": "campaign_progress_visible",
                "strategy_label": "es_daily_trend_v1",
                "symbol": "BTC/USDT",
                "fills_observed": 1,
                "round_trips_observed": 0,
                "current_window_realized_pnl": -0.8933406625,
                "paper_position": {"qty": 0.001},
                "latest_journal_fill": {
                    "fill_id": "fill-1",
                    "side": "buy",
                    "fill_ts": "2026-05-18T19:02:49.109748+00:00",
                },
                "collector": {"status": "running", "reason": "collecting"},
                "summary_text": (
                    "Paper sim monitor sees es_daily_trend_v1 on BTC/USDT with campaign running; "
                    "open qty=0.001; fills=1; round_trips=0; current_window_realized_pnl=-0.8933; "
                    "latest_fill=buy@2026-05-18T19:02:49.109748+00:00; recommendation=continue."
                ),
                "last_watch_reports_written": [{"watch_name": "next_fill"}],
                "trigger_reasons": ["heartbeat_only", "stop_requested"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        svc,
        "collect_once",
        lambda cfg: {
            "ok": True,
            "ts": "2026-05-18T19:04:51Z",
            "monitor_name": svc.MONITOR_NAME,
            "campaign_status": "completed",
            "campaign_reason": "completed",
            "recommendation": "continue",
            "recommendation_reason": "completed_with_partial_trade_evidence",
            "strategy_label": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "fills_observed": 1,
            "round_trips_observed": 0,
            "current_window_realized_pnl": -0.8933406625,
            "position_realized_pnl_total": -0.8933406625,
            "equity_realized_pnl_total": -1051.8110289791193,
            "unrealized_pnl": -0.2798423650,
            "paper_position": {"qty": 0.001},
            "latest_order": {"order_id": "ord-1", "status": "filled"},
            "latest_paper_fill": {},
            "latest_journal_fill": {
                "fill_id": "fill-1",
                "side": "buy",
                "fill_ts": "2026-05-18T19:02:49.109748+00:00",
            },
            "latest_equity": {"unrealized_pnl": -0.2798423650, "realized_pnl": -1051.8110289791193},
            "campaign_result": {"strategy": "sma_200_trend", "fills_delta": 1},
            "collector": {"status": "completed", "reason": "completed", "ts": "2026-05-18T19:04:51Z"},
            "strategy_runner": {"status": "stopped"},
            "paper_engine": {"status": "stopped"},
            "summary_text": (
                "Paper sim monitor sees es_daily_trend_v1 on BTC/USDT with campaign completed; "
                "open qty=0.001; fills=1; round_trips=0; current_window_realized_pnl=-0.8933; "
                "latest_fill=buy@2026-05-18T19:02:49.109748+00:00; recommendation=continue."
            ),
        },
    )

    out = svc.load_runtime_status()

    assert out["status"] == "stopped"
    assert out["reason"] == "campaign_completed"
    assert out["campaign_status"] == "completed"
    assert out["campaign_reason"] == "completed"
    assert out["collector"]["status"] == "completed"
    assert "campaign completed" in out["summary_text"]
    assert out["ts"] == "2026-05-18T19:04:14Z"
    assert out["loops"] == 17
    assert out["last_watch_reports_written"] == [{"watch_name": "next_fill"}]


def test_load_runtime_status_ignores_stopped_status_pid_without_pid_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.status_file().parent.mkdir(parents=True, exist_ok=True)
    svc.status_file().write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "stopped",
                "reason": "campaign_completed",
                "ts": "2026-05-18T19:04:14Z",
                "pid": 12345,
                "summary_text": "old stopped snapshot",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    process_alive_calls: list[int] = []
    monkeypatch.setattr(
        svc,
        "_process_alive",
        lambda pid: process_alive_calls.append(int(pid)) or True,
    )
    monkeypatch.setattr(
        svc,
        "collect_once",
        lambda cfg: {
            "ok": True,
            "ts": "2026-05-18T19:04:51Z",
            "monitor_name": svc.MONITOR_NAME,
            "campaign_status": "completed",
            "campaign_reason": "completed",
            "recommendation": "continue",
            "recommendation_reason": "completed_with_partial_trade_evidence",
            "strategy_label": "es_daily_trend_v1",
            "symbol": "BTC/USDT",
            "venue": "coinbase",
            "fills_observed": 1,
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
            "collector": {"status": "completed"},
            "strategy_runner": {"status": "stopped"},
            "paper_engine": {"status": "stopped"},
            "promotion_progress": {"thresholds_ready": False},
            "promotion_thresholds_ready": False,
            "promotion_progress_summary": "Promotion threshold progress.",
            "summary_text": "refreshed stopped snapshot",
        },
    )

    out = svc.load_runtime_status()

    assert process_alive_calls == []
    assert out["pid"] is None
    assert out["pid_alive"] is False
    assert out["summary_text"] == "refreshed stopped snapshot"
    assert out["promotion_progress_summary"] == "Promotion threshold progress."


def test_register_watch_preserves_state_by_default_and_can_reset_it(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.watches_file().parent.mkdir(parents=True, exist_ok=True)
    svc.watches_file().write_text(
        json.dumps(
            [
                {
                    "name": "next_fill",
                    "trigger": "new_fill",
                    "active": True,
                    "created_at": "2026-05-15T18:00:53Z",
                    "last_fired_at": "2026-05-15T18:00:54Z",
                    "last_event_key": "paper:stale-fill",
                    "last_report_stem": "paper_sim_monitor_watch_20260515T180054Z_next_fill",
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    preserved = svc.register_watch(name="next_fill", trigger="new_fill")
    rows = svc.list_watches()
    assert preserved["ok"] is True
    assert preserved["reset_state"] is False
    assert rows[0]["last_fired_at"] == "2026-05-15T18:00:54Z"
    assert rows[0]["last_event_key"] == "paper:stale-fill"

    reset = svc.register_watch(name="next_fill", trigger="new_fill", reset_state=True)
    rows = svc.list_watches()
    assert reset["ok"] is True
    assert reset["reset_state"] is True
    assert rows[0]["last_fired_at"] == ""
    assert rows[0]["last_event_key"] == ""
    assert rows[0]["last_report_stem"] == ""


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


def test_run_forever_collects_final_snapshot_before_stop(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
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
    assert out["reason"] == "campaign_completed"
    assert out["campaign_status"] == "completed"
    assert out["recommendation"] == "enough_evidence"
    reasons = list(out["trigger_reasons"])
    assert "campaign_status_changed" in reasons
    assert "recommendation_changed" in reasons
    assert "fill_count_changed" in reasons
    assert "round_trip_count_changed" in reasons
    assert "stop_requested" in reasons
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["campaign_status"] == "completed"
    lines = [line for line in svc.history_file().read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2


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
