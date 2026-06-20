from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import hetzner_paper_host_preflight as preflight


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_campaign_config_accepts_hetzner_example_without_state_requirement() -> None:
    result = preflight.check_campaign_config()

    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["details"]["campaigns"][0]["name"] == "ema_cross_default"
    assert result["details"]["campaigns"][0]["desktop_notify"] is False


def test_campaign_config_rejects_enabled_desktop_notifications(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [
                    {
                        "name": "ema_cross_default",
                        "enabled": True,
                        "state_dir": ".cbp_state_challengers/ema_cross_default_daily",
                        "strategy": "ema_cross",
                        "session_strategy_id": "ema_cross_default",
                        "symbol": "BTC/USDT",
                        "venue": "coinbase",
                        "signal_source": "public_ohlcv_5m",
                        "runtime_sec": 900,
                        "strategy_drain_sec": 2,
                        "poll_interval_sec": 300,
                        "max_daily_attempts": 2,
                        "desktop_notify": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = preflight.check_campaign_config(config_path=config, repo_root=tmp_path)

    assert result["ok"] is False
    assert result["status"] == "desktop_notify_enabled"


def test_campaign_config_can_require_transferred_state(tmp_path: Path) -> None:
    config = tmp_path / "campaigns.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaigns": [
                    {
                        "name": "ema_cross_default",
                        "enabled": True,
                        "state_dir": ".cbp_state_challengers/ema_cross_default_daily",
                        "strategy": "ema_cross",
                        "session_strategy_id": "ema_cross_default",
                        "symbol": "BTC/USDT",
                        "venue": "coinbase",
                        "signal_source": "public_ohlcv_5m",
                        "runtime_sec": 900,
                        "strategy_drain_sec": 2,
                        "poll_interval_sec": 300,
                        "max_daily_attempts": 2,
                        "desktop_notify": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    missing = preflight.check_campaign_config(
        config_path=config,
        repo_root=tmp_path,
        require_state=True,
    )
    (tmp_path / ".cbp_state_challengers/ema_cross_default_daily").mkdir(parents=True)
    present = preflight.check_campaign_config(
        config_path=config,
        repo_root=tmp_path,
        require_state=True,
    )

    assert missing["ok"] is False
    assert missing["status"] == "state_missing"
    assert present["ok"] is True


def test_git_checkout_can_require_expected_commit(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _run(command, **_kwargs):
        calls.append(command)
        if command[:2] == ["git", "rev-parse"]:
            return _completed("abcdef1234567890\n")
        if command[:2] == ["git", "status"]:
            return _completed("")
        raise AssertionError(command)

    accepted = preflight.check_git_checkout(
        repo_root=tmp_path,
        expected_commit="abcdef12",
        run_command=_run,
    )
    rejected = preflight.check_git_checkout(
        repo_root=tmp_path,
        expected_commit="deadbeef",
        run_command=_run,
    )

    assert accepted["ok"] is True
    assert rejected["ok"] is False
    assert rejected["status"] == "commit_mismatch"
    assert calls


def test_time_sync_requires_ntp_yes(monkeypatch) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/bin/timedatectl" if name == "timedatectl" else None)

    yes = preflight.check_time_sync(run_command=lambda *_args, **_kwargs: _completed("yes\n"))
    no = preflight.check_time_sync(run_command=lambda *_args, **_kwargs: _completed("no\n"))

    assert yes["ok"] is True
    assert yes["status"] == "ntp_synchronized"
    assert no["ok"] is False
    assert no["status"] == "ntp_not_synchronized"


def test_tailscale_requires_running_backend_and_ip(monkeypatch) -> None:
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/usr/bin/tailscale" if name == "tailscale" else None)

    running = preflight.check_tailscale(
        run_command=lambda *_args, **_kwargs: _completed(
            json.dumps(
                {
                    "BackendState": "Running",
                    "Self": {"TailscaleIPs": ["100.86.128.9"]},
                }
            )
        )
    )
    stopped = preflight.check_tailscale(
        run_command=lambda *_args, **_kwargs: _completed(
            json.dumps({"BackendState": "Stopped", "Self": {"TailscaleIPs": []}})
        )
    )

    assert running["ok"] is True
    assert running["status"] == "running"
    assert stopped["ok"] is False
    assert stopped["status"] == "not_running"
