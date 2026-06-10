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
