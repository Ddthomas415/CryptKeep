from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_paper_strategy_evidence_collector as script


@pytest.fixture(autouse=True)
def isolate_state(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def test_run_paper_strategy_evidence_collector_imports_from_source_file() -> None:
    path = Path(script.__file__).resolve()
    assert path.name == "run_paper_strategy_evidence_collector.py"
    assert path.suffix == ".py"


def test_run_paper_strategy_evidence_collector_requests_stop(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "request_stop", lambda: {"ok": True, "stop_file": "/tmp/paper_strategy_evidence.stop"})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_strategy_evidence_collector.py", "--stop"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["stop_file"] == "/tmp/paper_strategy_evidence.stop"


def test_run_paper_strategy_evidence_collector_shows_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "status": "running", "pid": 67890})
    monkeypatch.setattr(script.sys, "argv", ["run_paper_strategy_evidence_collector.py", "--status"])

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "running"
    assert out["pid"] == 67890


def test_pullback_recovery_defaults_to_pullback_session_strategy_id() -> None:
    assert (
        script._session_strategy_id(strategies=("pullback_recovery",))
        == "pullback_recovery_default"
    )


def test_start_detached_daily_loop_preserves_args_and_verifies_pid(monkeypatch, tmp_path) -> None:
    seen: dict[str, object] = {}
    statuses = iter(
        [
            {"ok": True, "pid_alive": False, "pid": 47262},
            {"ok": True, "status": "idle", "pid_alive": True, "pid": 50123},
        ]
    )

    class _FakeProcess:
        pid = 50123

        @staticmethod
        def poll():
            return None

    def _popen(command, **kwargs):
        seen["command"] = list(command)
        seen["kwargs"] = dict(kwargs)
        return _FakeProcess()

    monkeypatch.setattr(script, "load_runtime_status", lambda: next(statuses))
    monkeypatch.setattr(script.subprocess, "Popen", _popen)
    monkeypatch.setattr(script, "_detached_log_path", lambda: tmp_path / "collector.log")

    out = script._start_detached_daily_loop(
        [
            "--daily-loop",
            "--detach",
            "--strategies",
            "breakout_donchian",
            "--session-strategy-id",
            "breakout_default",
        ]
    )

    assert out == {
        "ok": True,
        "status": "idle",
        "reason": "detached_started",
        "pid": 50123,
        "log_file": str(tmp_path / "collector.log"),
    }
    command = seen["command"]
    assert "--daily-loop" in command
    assert "--detach" not in command
    assert command[-2:] == ["--session-strategy-id", "breakout_default"]
    kwargs = seen["kwargs"]
    assert kwargs["cwd"] == str(script.ROOT)
    assert kwargs["stdin"] is script.subprocess.DEVNULL
    assert kwargs["stderr"] is script.subprocess.STDOUT
    if script.os.name != "nt":
        assert kwargs["start_new_session"] is True


def test_start_detached_daily_loop_does_not_duplicate_live_collector(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        script,
        "load_runtime_status",
        lambda: {"ok": True, "status": "idle", "pid_alive": True, "pid": 23879},
    )
    monkeypatch.setattr(script, "_detached_log_path", lambda: tmp_path / "collector.log")
    monkeypatch.setattr(
        script.subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("must not start a duplicate collector"),
    )

    out = script._start_detached_daily_loop(["--daily-loop", "--detach"])

    assert out["ok"] is True
    assert out["reason"] == "already_running"
    assert out["pid"] == 23879


def test_run_paper_strategy_evidence_collector_runs_with_cfg(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _run_campaign(cfg, *, max_strategies=None):
        seen["cfg"] = cfg
        seen["max_strategies"] = max_strategies
        return {"ok": True, "status": "completed", "reason": "completed"}

    monkeypatch.setattr(script, "run_campaign", _run_campaign)
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_paper_strategy_evidence_collector.py",
            "--strategies",
            "ema_cross,breakout_donchian",
            "--runtime-sec",
            "60",
            "--symbol",
            "ETH/USD",
            "--venue",
            "kraken",
            "--tick-interval-sec",
            "1.5",
            "--strategy-min-bars",
            "28",
            "--signal-source",
            "public_ohlcv_5m",
            "--strategy-context-symbol",
            "BTC/USDT:USDT",
            "--strategy-context-venue",
            "okx",
            "--allow-first-signal-trade",
            "--no-desktop-notify",
            "--max-strategies",
            "1",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "completed"
    cfg = seen["cfg"]
    assert getattr(cfg, "strategies") == ("ema_cross", "breakout_donchian")
    assert getattr(cfg, "per_strategy_runtime_sec") == 60.0
    assert getattr(cfg, "symbol") == "ETH/USD"
    assert getattr(cfg, "venue") == "kraken"
    assert getattr(cfg, "tick_publish_interval_sec") == 1.5
    assert getattr(cfg, "strategy_min_bars") == 28
    assert getattr(cfg, "signal_source") == "public_ohlcv_5m"
    assert getattr(cfg, "strategy_context_symbol") == "BTC/USDT:USDT"
    assert getattr(cfg, "strategy_context_venue") == "okx"
    assert getattr(cfg, "allow_first_signal_trade") is True
    assert getattr(cfg, "paper_sim_monitor_desktop_notify") is False
    assert seen["max_strategies"] == 1


def test_sma_200_trend_defaults_to_public_daily_ohlcv(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _run_campaign(cfg, *, max_strategies=None):
        seen["cfg"] = cfg
        return {"ok": True, "status": "completed", "reason": "completed"}

    monkeypatch.setattr(script, "run_campaign", _run_campaign)
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_paper_strategy_evidence_collector.py",
            "--strategies",
            "sma_200_trend",
            "--runtime-sec",
            "5",
        ],
    )

    assert script.main() == 0
    json.loads(capsys.readouterr().out)
    assert getattr(seen["cfg"], "signal_source") == "public_ohlcv_1d"


def test_run_paper_strategy_evidence_collector_logs_session_start_and_end(monkeypatch, capsys) -> None:
    events: list[tuple[str, str, str]] = []
    extras: list[dict[str, object]] = []

    class _FakeLogger:
        def __init__(self, strategy_id: str) -> None:
            events.append(("init", str(strategy_id), ""))

        def log_session(self, **kwargs) -> None:
            phase = str((kwargs.get("extra") or {}).get("phase") or "")
            status = str((kwargs.get("extra") or {}).get("campaign_status") or "")
            extras.append(dict(kwargs.get("extra") or {}))
            events.append(("log", phase, status))

    monkeypatch.setattr(script, "EvidenceLogger", _FakeLogger)
    monkeypatch.setattr(script, "get_current_stage", lambda strategy_id: SimpleNamespace(value="paper"))
    monkeypatch.setattr(script, "get_kill_switch_state", lambda: {"armed": False})
    monkeypatch.setattr(
        script,
        "run_campaign",
        lambda cfg, *, max_strategies=None: {"ok": True, "status": "completed", "completed_strategies": 1},
    )
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "run_paper_strategy_evidence_collector.py",
            "--strategies",
            "sma_200_trend",
            "--runtime-sec",
            "5",
            "--signal-source",
            "public_ohlcv_1d",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "completed"
    assert events == [
        ("init", "es_daily_trend_v1", ""),
        ("log", "start", "starting"),
        ("init", "es_daily_trend_v1", ""),
        ("log", "end", "completed"),
    ]
    assert extras[0]["market_data_source"] == "public_ohlcv"
    assert extras[0]["ohlcv_sample_mode"] is False
    assert extras[0]["ohlcv_timeframe"] == "1d"


def test_run_daily_loop_idles_after_today_is_already_recorded(monkeypatch, tmp_path) -> None:
    status_writes: list[dict[str, object]] = []
    pid_writes: list[dict[str, object]] = []
    cleared: list[bool] = []
    stop_path = tmp_path / "paper_strategy_evidence.stop"

    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "pid_alive": False, "pid": None})
    monkeypatch.setattr(script, "_write_status", lambda obj: status_writes.append(dict(obj)))
    monkeypatch.setattr(script, "_write_pid_state", lambda obj: pid_writes.append(dict(obj)))
    monkeypatch.setattr(script, "_clear_pid_state", lambda: cleared.append(True))
    monkeypatch.setattr(script, "stop_file", lambda: stop_path)
    monkeypatch.setattr(script, "_has_session_day", lambda strategy_id, day: True)
    monkeypatch.setattr(script, "_today_utc", lambda: "2026-05-24")

    cfg = script.PaperStrategyEvidenceServiceCfg(
        strategies=("sma_200_trend",),
        per_strategy_runtime_sec=5.0,
        symbol="BTC/USDT",
        venue="coinbase",
    )

    out = script._run_daily_loop(
        cfg,
        max_strategies=None,
        session_strategy_id="es_daily_trend_v1",
        poll_interval_sec=1.0,
        max_loops=1,
    )

    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
    assert pid_writes[0]["daily_loop"] is True
    assert status_writes[0]["status"] == "idle"
    assert status_writes[0]["reason"] == "waiting_for_next_day"
    assert status_writes[-1]["status"] == "stopped"
    assert cleared == [True]


def test_run_daily_loop_writes_idle_immediately_after_campaign(monkeypatch, tmp_path) -> None:
    status_writes: list[dict[str, object]] = []
    pid_writes: list[dict[str, object]] = []
    cleared: list[bool] = []
    stop_path = tmp_path / "paper_strategy_evidence.stop"
    has_session_calls = {"count": 0}

    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "pid_alive": False, "pid": None})
    monkeypatch.setattr(script, "_write_status", lambda obj: status_writes.append(dict(obj)))
    monkeypatch.setattr(script, "_write_pid_state", lambda obj: pid_writes.append(dict(obj)))
    monkeypatch.setattr(script, "_clear_pid_state", lambda: cleared.append(True))
    monkeypatch.setattr(script, "stop_file", lambda: stop_path)
    monkeypatch.setattr(script, "_today_utc", lambda: "2026-05-25")

    def _has_session_day(strategy_id: str, day: str) -> bool:
        has_session_calls["count"] += 1
        return has_session_calls["count"] > 1

    monkeypatch.setattr(script, "_has_session_day", _has_session_day)
    monkeypatch.setattr(
        script,
        "_run_one_campaign",
        lambda cfg, *, max_strategies=None, session_strategy_id="": {
            "ok": True,
            "status": "completed",
            "completed_strategies": 1,
        },
    )

    cfg = script.PaperStrategyEvidenceServiceCfg(
        strategies=("sma_200_trend",),
        per_strategy_runtime_sec=5.0,
        symbol="BTC/USDT",
        venue="coinbase",
    )

    out = script._run_daily_loop(
        cfg,
        max_strategies=None,
        session_strategy_id="es_daily_trend_v1",
        poll_interval_sec=1.0,
        max_loops=1,
    )

    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
    assert len(pid_writes) == 2
    assert status_writes[0]["status"] == "idle"
    assert status_writes[0]["reason"] == "waiting_for_next_day"
    assert status_writes[-1]["status"] == "stopped"
    assert cleared == [True]


def test_session_day_requires_completed_end_record(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(script, "data_dir", lambda: tmp_path)
    path = script._session_log_path("ema_cross_default", "2026-06-15")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                json.dumps({"phase": "start", "campaign_status": "starting"}),
                json.dumps({"phase": "end", "campaign_status": "failed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert script._has_session_day("ema_cross_default", "2026-06-15") is False
    assert script._failed_session_attempts("ema_cross_default", "2026-06-15") == 1

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"phase": "end", "campaign_status": "completed"}) + "\n")

    assert script._has_session_day("ema_cross_default", "2026-06-15") is True


def test_log_session_end_marks_failed_campaign_as_critical(monkeypatch) -> None:
    captured: list[dict[str, object]] = []

    class _FakeLogger:
        def __init__(self, strategy_id: str) -> None:
            self.strategy_id = strategy_id

        def log_session(self, **kwargs) -> None:
            captured.append(dict(kwargs))

    monkeypatch.setattr(script, "EvidenceLogger", _FakeLogger)
    monkeypatch.setattr(script, "get_current_stage", lambda strategy_id: SimpleNamespace(value="paper"))
    monkeypatch.setattr(script, "get_kill_switch_state", lambda: {"armed": False})

    script._log_session_end(
        strategy_id="ema_cross_default",
        cfg=script.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross",),
            signal_source="public_ohlcv_5m",
        ),
        result={
            "ok": False,
            "status": "failed",
            "reason": "no_public_ohlcv",
            "completed_strategies": 0,
        },
    )

    assert captured[0]["critical_error"] is True
    assert captured[0]["ops_checks_passed"] is False
    assert captured[0]["reconciliation_result"] == "campaign_error"
    assert captured[0]["extra"]["campaign_status"] == "failed"
    assert captured[0]["extra"]["campaign_reason"] == "no_public_ohlcv"


def test_run_daily_loop_retries_failed_campaign_once_then_waits(monkeypatch, tmp_path) -> None:
    status_writes: list[dict[str, object]] = []
    run_calls: list[int] = []
    stop_path = tmp_path / "paper_strategy_evidence.stop"

    monkeypatch.setattr(script, "load_runtime_status", lambda: {"ok": True, "pid_alive": False, "pid": None})
    monkeypatch.setattr(script, "_write_status", lambda obj: status_writes.append(dict(obj)))
    monkeypatch.setattr(script, "_write_pid_state", lambda obj: None)
    monkeypatch.setattr(script, "_clear_pid_state", lambda: None)
    monkeypatch.setattr(script, "stop_file", lambda: stop_path)
    monkeypatch.setattr(script, "_today_utc", lambda: "2026-06-15")
    monkeypatch.setattr(script, "_has_session_day", lambda strategy_id, day: False)
    monkeypatch.setattr(script, "_failed_session_attempts", lambda strategy_id, day: len(run_calls))
    monkeypatch.setattr(script.time, "sleep", lambda seconds: None)

    def _run_one_campaign(cfg, *, max_strategies=None, session_strategy_id=""):
        run_calls.append(len(run_calls) + 1)
        return {
            "ok": False,
            "status": "failed",
            "reason": "no_public_ohlcv",
            "completed_strategies": 0,
        }

    monkeypatch.setattr(script, "_run_one_campaign", _run_one_campaign)

    out = script._run_daily_loop(
        script.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross",),
            per_strategy_runtime_sec=1.0,
            signal_source="public_ohlcv_5m",
        ),
        max_strategies=None,
        session_strategy_id="ema_cross_default",
        poll_interval_sec=1.0,
        max_daily_attempts=2,
        max_loops=2,
    )

    retry_rows = [row for row in status_writes if row.get("status") == "failed"]
    assert run_calls == [1, 2]
    assert retry_rows[0]["retry_pending"] is True
    assert retry_rows[-1]["retry_pending"] is False
    assert retry_rows[-1]["daily_attempts"] == 2
    assert out["status"] == "stopped"
    assert out["reason"] == "max_loops"
