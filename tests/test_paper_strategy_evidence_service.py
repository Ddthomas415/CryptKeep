from __future__ import annotations

import json

from services.analytics import paper_strategy_evidence_service as svc


def test_strategy_summary_map_passes_symbol_filter(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _load_paper_history_evidence(*, journal_path: str = "", symbol: str = "") -> dict[str, object]:
        calls.append((journal_path, symbol))
        return {
            "rows": [
                {
                    "strategy": "ema_cross",
                    "fills": 1,
                    "closed_trades": 0,
                    "net_realized_pnl": 0.0,
                }
            ]
        }

    monkeypatch.setattr(svc, "load_paper_history_evidence", _load_paper_history_evidence)

    out = svc._strategy_summary_map("/tmp/trade_journal.sqlite", symbol="ETH/USD")

    assert calls == [("/tmp/trade_journal.sqlite", "ETH/USD")]
    assert out["ema_cross"]["fills"] == 1


def test_run_campaign_writes_completed_status_and_persists_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    stop_calls: list[str] = []

    monkeypatch.setattr(
        svc,
        "_component_runtime",
        lambda name: {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"},
    )
    monkeypatch.setattr(
        svc,
        "_ensure_component",
        lambda name, *, cfg: {"name": name, "started": True, "pid": 123 if name == "tick_publisher" else 456, "status": "running"},
    )
    monkeypatch.setattr(
        svc,
        "_run_strategy_window",
        lambda *, cfg, strategy_name: {
            "strategy": str(strategy_name),
            "runtime_sec": 1.0,
            "stop_reason": "runtime_elapsed",
            "runner_status": "stopped",
            "enqueued_total": 0,
            "fills_delta": 1 if str(strategy_name) == "ema_cross" else 0,
            "closed_trades_delta": 1 if str(strategy_name) == "ema_cross" else 0,
            "net_realized_pnl_delta": 0.0,
            "fills_total": 1 if str(strategy_name) == "ema_cross" else 0,
            "closed_trades_total": 1 if str(strategy_name) == "ema_cross" else 0,
            "net_realized_pnl_total": 0.0,
            "latest_fill_ts": "",
        },
    )
    monkeypatch.setattr(
        svc,
        "run_strategy_evidence_cycle",
        lambda **kwargs: {"as_of": "2026-03-19T00:00:00Z", "aggregate_leaderboard": {"rows": []}, "decisions": []},
    )
    monkeypatch.setattr(svc, "persist_strategy_evidence", lambda report: {"ok": True, "latest_path": str(tmp_path / "strategy_evidence.latest.json")})
    monkeypatch.setattr(
        svc,
        "write_decision_record",
        lambda report, *, artifact_path="": {"ok": True, "path": str(tmp_path / "decision_record.md"), "artifact_path": artifact_path},
    )
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(
        svc,
        "_stop_component",
        lambda name: stop_calls.append(name) or {"ok": True, "component": name},
    )

    out = svc.run_campaign(
        svc.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross", "breakout_donchian"),
            per_strategy_runtime_sec=1.0,
        )
    )

    assert out["ok"] is True
    assert out["status"] == "completed"
    assert out["reason"] == "completed"
    assert out["completed_strategies"] == 2
    assert out["started_components"] == {"tick_publisher": 123, "paper_engine": 456}
    assert out["evidence"]["latest_path"].endswith("strategy_evidence.latest.json")
    assert out["decision_record"]["path"].endswith("decision_record.md")
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["status"] == "completed"
    assert status["completed_strategies"] == 2
    assert stop_calls.count("strategy_runner") >= 1
    assert "tick_publisher" in stop_calls
    assert "paper_engine" in stop_calls


def test_run_campaign_skips_evidence_when_no_new_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(
        svc,
        "_component_runtime",
        lambda name: {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"},
    )
    monkeypatch.setattr(
        svc,
        "_ensure_component",
        lambda name, *, cfg: {"name": name, "started": True, "pid": 123 if name == "tick_publisher" else 456, "status": "running"},
    )
    monkeypatch.setattr(
        svc,
        "_run_strategy_window",
        lambda *, cfg, strategy_name: {
            "strategy": str(strategy_name),
            "runtime_sec": 1.0,
            "stop_reason": "runtime_elapsed",
            "runner_status": "stopped",
            "enqueued_total": 0,
            "fills_delta": 0,
            "closed_trades_delta": 0,
            "net_realized_pnl_delta": 0.0,
            "fills_total": 0,
            "closed_trades_total": 0,
            "net_realized_pnl_total": 0.0,
            "latest_fill_ts": "",
        },
    )
    monkeypatch.setattr(svc, "run_strategy_evidence_cycle", lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not rerun evidence")))
    monkeypatch.setattr(svc, "persist_strategy_evidence", lambda report: (_ for _ in ()).throw(AssertionError("should not persist evidence")))
    monkeypatch.setattr(svc, "write_decision_record", lambda report, *, artifact_path="": (_ for _ in ()).throw(AssertionError("should not rewrite decision record")))
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(svc, "_stop_component", lambda name: {"ok": True, "component": name})

    out = svc.run_campaign(
        svc.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross",),
            per_strategy_runtime_sec=1.0,
        )
    )

    assert out["ok"] is True
    assert out["status"] == "completed"
    assert out["evidence"]["skipped"] is True
    assert out["evidence"]["reason"] == "paper_history_unchanged"
    assert out["decision_record"]["skipped"] is True


def test_run_campaign_prefers_explicit_evidence_symbol_over_user_yaml_symbols(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        svc,
        "_component_runtime",
        lambda name: {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"},
    )
    monkeypatch.setattr(
        svc,
        "_ensure_component",
        lambda name, *, cfg: {"name": name, "started": True, "pid": 123 if name == "tick_publisher" else 456, "status": "running"},
    )
    monkeypatch.setattr(
        svc,
        "_run_strategy_window",
        lambda *, cfg, strategy_name: {
            "strategy": str(strategy_name),
            "runtime_sec": 1.0,
            "stop_reason": "runtime_elapsed",
            "runner_status": "stopped",
            "enqueued_total": 1,
            "fills_delta": 1,
            "closed_trades_delta": 1,
            "net_realized_pnl_delta": 0.0,
            "fills_total": 1,
            "closed_trades_total": 1,
            "net_realized_pnl_total": 0.0,
            "latest_fill_ts": "",
        },
    )
    monkeypatch.setattr(svc, "load_user_yaml", lambda: {"symbols": ["APR/USD"]})
    monkeypatch.setattr(
        svc,
        "run_strategy_evidence_cycle",
        lambda **kwargs: seen.setdefault("kwargs", kwargs) or {"as_of": "2026-03-19T00:00:00Z", "aggregate_leaderboard": {"rows": []}, "decisions": []},
    )
    monkeypatch.setattr(svc, "persist_strategy_evidence", lambda report: {"ok": True, "latest_path": str(tmp_path / "strategy_evidence.latest.json")})
    monkeypatch.setattr(
        svc,
        "write_decision_record",
        lambda report, *, artifact_path="": {"ok": True, "path": str(tmp_path / "decision_record.md"), "artifact_path": artifact_path},
    )
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(svc, "_stop_component", lambda name: {"ok": True, "component": name})

    out = svc.run_campaign(
        svc.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross",),
            per_strategy_runtime_sec=1.0,
            symbol="ETH/USD",
            evidence_symbol="SOL/USD",
        )
    )

    assert out["ok"] is True
    assert seen["kwargs"]["symbol"] == "SOL/USD"
    assert seen["kwargs"]["base_cfg"] == {"symbols": ["APR/USD"]}


def test_run_campaign_refuses_busy_strategy_runner(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    def _component_runtime(name: str) -> dict[str, object]:
        if name == "strategy_runner":
            return {"name": name, "pid_alive": True, "pid": 321, "status": "running"}
        return {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"}

    monkeypatch.setattr(svc, "_component_runtime", _component_runtime)

    out = svc.run_campaign(svc.PaperStrategyEvidenceServiceCfg())

    assert out["ok"] is False
    assert out["status"] == "blocked"
    assert out["reason"] == "strategy_runner_busy"
    status = json.loads(svc.status_file().read_text(encoding="utf-8"))
    assert status["status"] == "blocked"


def test_summary_text_humanizes_no_fresh_tick_for_current_strategy() -> None:
    summary = svc._summary_text(
        {
            "status": "running",
            "current_strategy": "ema_cross",
            "completed_strategies": 0,
            "total_strategies": 3,
            "runner_note": "no_fresh_tick:snapshot_stale:publisher_stopped_or_network_blocked",
        }
    )

    assert "Paper evidence collector is running on ema_cross (0/3 complete)." in summary
    assert "tick snapshot is stale" in summary
    assert "network access may be blocked" in summary


def test_summary_text_uses_latest_result_runner_note_when_current_strategy_missing() -> None:
    summary = svc._summary_text(
        {
            "status": "completed",
            "completed_strategies": 1,
            "total_strategies": 1,
            "results": [
                {
                    "strategy": "breakout_donchian",
                    "runner_note": "no_fresh_tick:snapshot_present_but_symbol_missing:check_symbol_or_venue_mapping",
                }
            ],
        }
    )

    assert "Paper evidence collector is completed (1/1 complete)." in summary
    assert "breakout_donchian" in summary
    assert "requested symbol is missing" in summary


def test_load_runtime_status_marks_dead_process(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    svc.status_file().parent.mkdir(parents=True, exist_ok=True)
    svc.status_file().write_text(
        json.dumps(
            {
                "ok": True,
                "has_status": True,
                "status": "running",
                "ts": "2026-03-19T01:00:00Z",
                "strategies": ["ema_cross"],
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "per_strategy_runtime_sec": 60.0,
            }
        ),
        encoding="utf-8",
    )
    svc.pid_file().write_text(
        json.dumps(
            {
                "pid": 55555,
                "started_ts": "2026-03-19T00:59:00Z",
                "strategies": ["ema_cross"],
                "symbol": "BTC/USD",
                "venue": "coinbase",
                "per_strategy_runtime_sec": 60.0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(svc, "_process_alive", lambda pid: False)

    out = svc.load_runtime_status()

    assert out["ok"] is True
    assert out["status"] == "dead"
    assert out["reason"] == "process_not_running"
    assert out["pid"] == 55555
    assert out["pid_alive"] is False


def test_tick_publisher_reusable_requires_matching_fresh_symbol() -> None:
    cfg = svc.PaperStrategyEvidenceServiceCfg(symbol="2Z/USD", venue="coinbase", tick_publish_interval_sec=2.0)
    now_ms = 1_700_000_000_000
    state = {
        "status_payload": {
            "venues": {"coinbase": {"ok": True}},
            "ticks": [
                {"venue": "coinbase", "symbol": "2Z/USD", "ts_ms": now_ms},
            ],
        }
    }

    original_time = svc.time.time
    try:
        svc.time.time = lambda: now_ms / 1000.0
        assert svc._tick_publisher_reusable(state, cfg=cfg) is True
        state["status_payload"]["ticks"] = [{"venue": "coinbase", "symbol": "BTC/USD", "ts_ms": now_ms}]
        assert svc._tick_publisher_reusable(state, cfg=cfg) is False
    finally:
        svc.time.time = original_time


def test_ensure_component_restarts_unhealthy_tick_publisher(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    cfg = svc.PaperStrategyEvidenceServiceCfg(symbol="2Z/USD", venue="coinbase", tick_publish_interval_sec=2.0)
    stop_calls: list[str] = []

    class _FakeProc:
        pid = 222

        def poll(self):
            return None

    states = iter(
        [
            {
                "name": "tick_publisher",
                "pid_alive": True,
                "pid": 111,
                "status": "running",
                "status_payload": {"venues": {"coinbase": {"ok": False}}, "ticks": []},
            },
            {
                "name": "tick_publisher",
                "pid_alive": False,
                "pid": 0,
                "status": "stopped",
                "status_payload": {},
            },
            {
                "name": "tick_publisher",
                "pid_alive": True,
                "pid": 222,
                "status": "running",
                "status_payload": {
                    "venues": {"coinbase": {"ok": True}},
                    "ticks": [{"venue": "coinbase", "symbol": "2Z/USD", "ts_ms": 1_700_000_000_000}],
                },
            },
        ]
    )
    monkeypatch.setattr(svc, "_component_runtime", lambda name: next(states))
    monkeypatch.setattr(svc, "_stop_component", lambda name: stop_calls.append(name) or {"ok": True})
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(svc, "_start_process", lambda *, script_relpath, env: _FakeProc())
    monkeypatch.setattr(svc, "_wait_for", lambda predicate, *, timeout_sec, sleep_sec=0.2: True)
    monkeypatch.setattr(svc.time, "time", lambda: 1_700_000_000.0)

    out = svc._ensure_component("tick_publisher", cfg=cfg)

    assert out["started"] is True
    assert out["pid"] == 222
    assert stop_calls == ["tick_publisher"]
