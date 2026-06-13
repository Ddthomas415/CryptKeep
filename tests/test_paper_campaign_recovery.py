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
        )
        for spec in specs
    ] == [
        ("es_daily_trend_v1", "sma_200_trend", "es_daily_trend_v1", "public_ohlcv_1d", 20.0),
        ("ema_cross_default", "ema_cross", "ema_cross_default", "public_ohlcv_5m", 900.0),
        (
            "breakout_default",
            "breakout_donchian",
            "breakout_default",
            "public_ohlcv_5m",
            900.0,
        ),
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
    assert launch_kwargs["env"]["CBP_STATE_DIR"] == str(spec.state_dir)


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
