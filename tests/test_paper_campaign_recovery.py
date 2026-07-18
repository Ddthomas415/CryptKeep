from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from services.analytics import paper_campaign_recovery as recovery


def _spec(tmp_path: Path, *, name: str = "campaign") -> recovery.PaperCampaignSpec:
    return recovery.PaperCampaignSpec(
        name=name,
        state_dir=tmp_path / name,
        strategy="ema_cross",
        session_strategy_id="ema_cross_default",
        symbol="BTC/USDT",
        venue="coinbase",
        signal_source="public_ohlcv_5m",
        runtime_sec=900.0,
        strategy_drain_sec=2.0,
        poll_interval_sec=300.0,
        max_daily_attempts=2,
    )


def _completed(payload: dict, *, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr="",
    )


def test_load_campaign_specs_rejects_state_outside_repo(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [
                    {
                        "name": "bad",
                        "state_dir": "../outside",
                        "strategy": "ema_cross",
                        "session_strategy_id": "ema_cross_default",
                        "symbol": "BTC/USDT",
                        "venue": "coinbase",
                        "signal_source": "public_ohlcv_5m",
                        "runtime_sec": 900,
                        "strategy_drain_sec": 2,
                        "poll_interval_sec": 300,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="inside the repository root"):
        recovery.load_campaign_specs(config, repo_root=tmp_path / "repo")


def test_load_campaign_specs_rejects_non_boolean_control_fields(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [{"name": "bad", "enabled": "false"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be a boolean"):
        recovery.load_campaign_specs(config, repo_root=tmp_path)


def test_load_campaign_specs_rejects_invalid_daily_attempt_limit(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [
                    {
                        "name": "bad",
                        "state_dir": ".state",
                        "strategy": "ema_cross",
                        "session_strategy_id": "ema_cross_default",
                        "symbol": "BTC/USDT",
                        "venue": "coinbase",
                        "signal_source": "public_ohlcv_5m",
                        "runtime_sec": 900,
                        "strategy_drain_sec": 2,
                        "poll_interval_sec": 300,
                        "max_daily_attempts": 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="positive integer"):
        recovery.load_campaign_specs(config, repo_root=tmp_path)


def test_load_campaign_specs_defaults_daily_attempt_limit_for_schema_v1(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [
                    {
                        "name": "legacy",
                        "state_dir": ".state",
                        "strategy": "ema_cross",
                        "session_strategy_id": "ema_cross_default",
                        "symbol": "BTC/USDT",
                        "venue": "coinbase",
                        "signal_source": "public_ohlcv_5m",
                        "runtime_sec": 900,
                        "strategy_drain_sec": 2,
                        "poll_interval_sec": 300,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    specs = recovery.load_campaign_specs(config, repo_root=tmp_path)

    assert specs[0].max_daily_attempts == 2


def test_load_campaign_specs_rejects_non_object_config(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="config must be an object"):
        recovery.load_campaign_specs(config, repo_root=tmp_path)


def test_default_manifest_matches_accepted_campaigns() -> None:
    specs = recovery.load_campaign_specs()

    assert [
        (
            spec.name,
            spec.strategy,
            spec.session_strategy_id,
            spec.signal_source,
            spec.runtime_sec,
            spec.max_daily_attempts,
        )
        for spec in specs
    ] == [
        ("es_daily_trend_v1", "sma_200_trend", "es_daily_trend_v1", "public_ohlcv_1d", 20.0, 2),
        ("ema_cross_default", "ema_cross", "ema_cross_default", "public_ohlcv_5m", 900.0, 2),
        (
            "breakout_default",
            "breakout_donchian",
            "breakout_default",
            "public_ohlcv_5m",
            900.0,
            2,
        ),
    ]


def test_hetzner_example_starts_only_headless_ema_challenger() -> None:
    config = recovery.DEFAULT_CONFIG_PATH.with_name(
        "paper_evidence_campaigns.hetzner.example.json"
    )

    specs = recovery.load_campaign_specs(config)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "ema_cross_default"
    assert spec.strategy == "ema_cross"
    assert spec.session_strategy_id == "ema_cross_default"
    assert spec.signal_source == "public_ohlcv_5m"
    assert spec.max_daily_attempts == 2
    assert spec.desktop_notify is False
    assert "--no-desktop-notify" in recovery._command(spec, restore=True)


def test_laptop_manifest_excludes_hetzner_owned_ema_challenger() -> None:
    config = recovery.DEFAULT_CONFIG_PATH.with_name("paper_evidence_campaigns.laptop.json")

    specs = recovery.load_campaign_specs(config)

    assert [(spec.name, spec.strategy, spec.signal_source) for spec in specs] == [
        ("es_daily_trend_v1", "sma_200_trend", "public_ohlcv_1d"),
        ("breakout_default", "breakout_donchian", "public_ohlcv_5m"),
    ]


def test_restore_campaign_does_not_duplicate_running_collector(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        calls.append(list(command))
        return _completed({"ok": True, "status": "idle", "pid": 123, "pid_alive": True})

    out = recovery.restore_campaign(_spec(tmp_path), run_command=_run)

    assert out["ok"] is True
    assert out["action"] == "already_running"
    assert out["pid"] == 123
    assert len(calls) == 1
    assert calls[0][-1] == "--status"


def test_restore_campaign_refuses_unhealthy_restart_without_preflight(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        calls.append(list(command))
        return _completed(
            {
                "ok": False,
                "status": "failed",
                "reason": "no_public_ohlcv",
                "pid": 123,
                "pid_alive": True,
            }
        )

    out = recovery.restore_campaign(_spec(tmp_path), run_command=_run, restart_unhealthy=True)

    assert out["ok"] is False
    assert out["action"] == "restart_blocked"
    assert out["reason"] == "restart_unhealthy_requires_ohlcv_preflight"
    assert len(calls) == 1
    assert calls[0][-1] == "--status"


def test_restore_campaign_preflight_blocks_unhealthy_restart_before_stop(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        calls.append(list(command))
        return _completed(
            {
                "ok": False,
                "status": "failed",
                "reason": "no_public_ohlcv",
                "pid": 123,
                "pid_alive": True,
            }
        )

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        restart_unhealthy=True,
        preflight_ohlcv=True,
        preflight_check=lambda **kwargs: {
            "ok": False,
            "status": "ohlcv_source_unreachable",
            "reason": "fetch_failed",
        },
    )

    assert out["ok"] is False
    assert out["action"] == "preflight_blocked"
    assert out["reason"] == "ohlcv_source_unreachable"
    assert len(calls) == 1
    assert calls[0][-1] == "--status"


def test_restore_campaign_starts_dead_collector_and_verifies_status(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict]] = []
    results = iter(
        [
            _completed({"ok": True, "status": "idle", "pid": 10, "pid_alive": False}),
            _completed({"ok": True, "status": "idle", "reason": "detached_started", "pid": 20}),
            _completed(
                {
                    "ok": True,
                    "status": "idle",
                    "reason": "waiting_for_next_day",
                    "pid": 20,
                    "pid_alive": True,
                    "last_completed_day": "2026-06-13",
                }
            ),
        ]
    )

    def _run(command, **kwargs):
        calls.append((list(command), dict(kwargs)))
        return next(results)

    spec = _spec(tmp_path)
    out = recovery.restore_campaign(spec, run_command=_run)

    assert out["ok"] is True
    assert out["action"] == "started"
    assert out["pid"] == 20
    assert len(calls) == 3
    launch, launch_kwargs = calls[1]
    assert "--daily-loop" in launch
    assert "--detach" in launch
    assert launch[launch.index("--strategies") + 1] == "ema_cross"
    assert launch[launch.index("--max-daily-attempts") + 1] == "2"
    assert launch_kwargs["env"]["CBP_STATE_DIR"] == str(spec.state_dir)


def test_restore_campaign_preflight_blocks_unreachable_source(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _run(command, **kwargs):
        calls.append(list(command))
        return _completed({"ok": True, "status": "idle", "pid": 10, "pid_alive": False})

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        preflight_ohlcv=True,
        preflight_check=lambda **kwargs: {
            "ok": False,
            "status": "ohlcv_source_unreachable",
            "reason": "fetch_failed",
            "venue": kwargs["venue"],
            "symbol": kwargs["symbol"],
            "signal_source": kwargs["signal_source"],
        },
    )

    assert out["ok"] is False
    assert out["action"] == "preflight_blocked"
    assert out["reason"] == "ohlcv_source_unreachable"
    assert out["ohlcv_preflight"]["venue"] == "coinbase"
    assert len(calls) == 1
    assert calls[0][-1] == "--status"


def test_restore_campaign_preflight_pass_allows_launch(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    results = iter(
        [
            _completed({"ok": True, "status": "idle", "pid": 10, "pid_alive": False}),
            _completed({"ok": True, "status": "idle", "reason": "detached_started", "pid": 20}),
            _completed({"ok": True, "status": "running", "pid": 20, "pid_alive": True}),
        ]
    )

    def _run(command, **kwargs):
        calls.append(list(command))
        return next(results)

    seen: dict[str, object] = {}

    def _preflight(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "status": "ok", "row_count": 250}

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        preflight_ohlcv=True,
        preflight_check=_preflight,
        preflight_probe_limit=400,
        preflight_attempts=3,
        preflight_attempt_delay_sec=2.0,
    )

    assert out["ok"] is True
    assert out["action"] == "started"
    assert len(calls) == 3
    assert seen == {
        "venue": "coinbase",
        "symbol": "BTC/USDT",
        "signal_source": "public_ohlcv_5m",
        "probe_limit": 400,
        "attempts": 3,
        "attempt_delay_sec": 2.0,
    }


def test_restore_campaign_preflight_grants_one_recovery_attempt_after_exhaustion(
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []
    results = iter(
        [
            _completed(
                {
                    "ok": False,
                    "status": "failed",
                    "reason": "daily_retry_limit_exhausted",
                    "daily_attempts": 5,
                    "max_daily_attempts": 2,
                    "pid": 10,
                    "pid_alive": False,
                }
            ),
            _completed({"ok": True, "status": "idle", "reason": "detached_started", "pid": 20}),
            _completed({"ok": True, "status": "running", "pid": 20, "pid_alive": True}),
        ]
    )

    def _run(command, **kwargs):
        calls.append(list(command))
        return next(results)

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        preflight_ohlcv=True,
        preflight_check=lambda **kwargs: {"ok": True, "status": "ok", "row_count": 300},
    )

    assert out["ok"] is True
    assert out["action"] == "started"
    assert out["recovery_attempt_override"] == {
        "reason": "same_day_recovery_after_ohlcv_preflight",
        "previous_daily_attempts": 5,
        "configured_max_daily_attempts": 2,
        "launch_max_daily_attempts": 6,
    }
    launch = calls[1]
    assert launch[launch.index("--max-daily-attempts") + 1] == "6"


def test_restore_campaign_preflight_does_not_override_non_ohlcv_failure(
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []
    results = iter(
        [
            _completed(
                {
                    "ok": False,
                    "status": "failed",
                    "reason": "strategy_error",
                    "daily_attempts": 5,
                    "max_daily_attempts": 2,
                    "pid": 10,
                    "pid_alive": False,
                }
            ),
            _completed({"ok": True, "status": "idle", "reason": "detached_started", "pid": 20}),
            _completed({"ok": True, "status": "running", "pid": 20, "pid_alive": True}),
        ]
    )

    def _run(command, **kwargs):
        calls.append(list(command))
        return next(results)

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        preflight_ohlcv=True,
        preflight_check=lambda **kwargs: {"ok": True, "status": "ok", "row_count": 300},
    )

    assert out["ok"] is True
    assert "recovery_attempt_override" not in out
    launch = calls[1]
    assert launch[launch.index("--max-daily-attempts") + 1] == "2"


def test_restore_campaign_preflight_can_restart_alive_unhealthy_collector(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    killed: list[tuple[int, int]] = []
    results = iter(
        [
            _completed(
                {
                    "ok": False,
                    "status": "failed",
                    "reason": "no_public_ohlcv",
                    "pid": 123,
                    "pid_alive": True,
                }
            ),
            _completed({"ok": True, "status": "stopping", "pid": 123, "pid_alive": True}),
            _completed({"ok": False, "status": "failed", "pid": 123, "pid_alive": True}),
            _completed({"ok": True, "status": "idle", "pid": 123, "pid_alive": False}),
            _completed({"ok": True, "status": "idle", "pid": 123, "pid_alive": False}),
            _completed({"ok": True, "status": "starting", "reason": "detached_started", "pid": 456}),
            _completed({"ok": True, "status": "idle", "pid": 456, "pid_alive": True}),
        ]
    )

    def _run(command, **kwargs):
        calls.append(list(command))
        return next(results)

    out = recovery.restore_campaign(
        _spec(tmp_path),
        run_command=_run,
        restart_unhealthy=True,
        restart_wait_sec=0.0,
        kill_pid=lambda pid, sig: killed.append((pid, sig)),
        preflight_ohlcv=True,
        preflight_check=lambda **kwargs: {"ok": True, "status": "ok", "row_count": 400},
    )

    assert out["ok"] is True
    assert out["action"] == "started"
    assert out["pid"] == 456
    assert out["ohlcv_preflight"]["status"] == "ok"
    assert killed == [(123, recovery.signal.SIGTERM)]
    assert calls[0][-1] == "--status"
    assert calls[1][-1] == "--stop"
    assert "--daily-loop" in calls[-2]
    assert "--detach" in calls[-2]


def test_manage_campaigns_rejects_unknown_selection(tmp_path: Path) -> None:
    out = recovery.manage_campaigns(
        [_spec(tmp_path, name="known")],
        restore=False,
        selected_names=["missing"],
        run_command=lambda *args, **kwargs: pytest.fail("must not invoke collector"),
    )

    assert out["ok"] is False
    assert out["reason"] == "unknown_campaign"
    assert out["unknown_campaigns"] == ["missing"]


def test_manage_campaigns_reports_partial_outage(tmp_path: Path) -> None:
    def _run(command, **kwargs):
        state_dir = kwargs["env"]["CBP_STATE_DIR"]
        alive = state_dir.endswith("first")
        return _completed({"ok": True, "status": "idle", "pid": 1 if alive else 2, "pid_alive": alive})

    out = recovery.manage_campaigns(
        [_spec(tmp_path, name="first"), _spec(tmp_path, name="second")],
        restore=False,
        run_command=_run,
    )

    assert out["ok"] is False
    assert out["all_running"] is False
    assert out["campaign_count"] == 2
    assert out["running_count"] == 1


def test_manage_campaigns_distinguishes_liveness_from_campaign_health(tmp_path: Path) -> None:
    out = recovery.manage_campaigns(
        [_spec(tmp_path)],
        restore=False,
        run_command=lambda *args, **kwargs: _completed(
            {
                "ok": False,
                "status": "failed",
                "reason": "no_public_ohlcv",
                "pid": 123,
                "pid_alive": True,
            }
        ),
    )

    assert out["ok"] is False
    assert out["all_running"] is True
    assert out["running_count"] == 1
    assert out["campaigns"][0]["status"] == "failed"
    assert out["campaigns"][0]["reason"] == "no_public_ohlcv"


def test_manage_campaigns_accepts_generator_specs(tmp_path: Path) -> None:
    specs = (_spec(tmp_path, name=name) for name in ("first", "second"))

    out = recovery.manage_campaigns(
        specs,
        restore=False,
        selected_names=["second"],
        run_command=lambda *args, **kwargs: _completed(
            {"ok": True, "status": "idle", "pid": 2, "pid_alive": True}
        ),
    )

    assert out["ok"] is True
    assert out["campaign_count"] == 1
    assert out["campaigns"][0]["name"] == "second"
