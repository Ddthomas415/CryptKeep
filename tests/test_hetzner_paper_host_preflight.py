from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from scripts import hetzner_paper_host_preflight as preflight


def _completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


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


def test_python_venv_uses_active_prefix_not_resolved_executable(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    venv = repo_root / ".venv"
    executable = venv / "bin" / "python"

    result = preflight.check_python_venv(
        repo_root=repo_root,
        executable=str(executable),
        prefix=str(venv),
    )

    assert result["ok"] is True
    assert result["status"] == "repo_venv"
    assert result["details"]["sys_prefix"] == str(venv.resolve())


def test_collector_imports_uses_venv_python_and_reports_missing_dependency(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    executable = str(tmp_path / ".venv/bin/python")

    def _run_success(command, **_kwargs):
        calls.append(command)
        return _completed("collector_import_ok\n")

    ok = preflight.check_collector_imports(
        repo_root=tmp_path,
        executable=executable,
        run_command=_run_success,
    )

    assert ok["ok"] is True
    assert ok["status"] == "collector_imports_ok"
    assert calls[0][0] == executable

    failed = preflight.check_collector_imports(
        repo_root=tmp_path,
        executable=executable,
        run_command=lambda *_args, **_kwargs: _completed(
            "",
            returncode=1,
            stderr="ModuleNotFoundError: No module named 'yaml'",
        ),
    )

    assert failed["ok"] is False
    assert failed["status"] == "collector_imports_failed"
    assert "yaml" in failed["details"]["stderr"]


def test_storage_health_accepts_backup_dir_and_capacity(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    result = preflight.check_storage_health(
        repo_root=tmp_path,
        backup_dir=backup_dir,
        min_free_bytes=1024,
        min_free_inodes=10,
        disk_usage=lambda _path: SimpleNamespace(free=2048),
        statvfs=lambda _path: SimpleNamespace(f_favail=20),
    )

    assert result["ok"] is True
    assert result["status"] == "ready"
    assert result["details"]["backup_dir_exists"] is True


def test_storage_health_rejects_missing_backup_dir(tmp_path: Path) -> None:
    result = preflight.check_storage_health(
        repo_root=tmp_path,
        backup_dir=tmp_path / "missing-backups",
        min_free_bytes=1024,
        min_free_inodes=10,
        disk_usage=lambda _path: SimpleNamespace(free=2048),
        statvfs=lambda _path: SimpleNamespace(f_favail=20),
    )

    assert result["ok"] is False
    assert result["status"] == "backup_dir_missing"


def test_storage_health_rejects_missing_repo_root(tmp_path: Path) -> None:
    result = preflight.check_storage_health(
        repo_root=tmp_path / "missing-repo",
        backup_dir=tmp_path / "backups",
        min_free_bytes=1024,
        min_free_inodes=10,
        disk_usage=lambda _path: SimpleNamespace(free=2048),
        statvfs=lambda _path: SimpleNamespace(f_favail=20),
    )

    assert result["ok"] is False
    assert result["status"] == "repo_root_missing"


def test_storage_health_rejects_low_space_and_low_inodes(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    low_space = preflight.check_storage_health(
        repo_root=tmp_path,
        backup_dir=backup_dir,
        min_free_bytes=4096,
        min_free_inodes=10,
        disk_usage=lambda _path: SimpleNamespace(free=2048),
        statvfs=lambda _path: SimpleNamespace(f_favail=20),
    )
    low_inodes = preflight.check_storage_health(
        repo_root=tmp_path,
        backup_dir=backup_dir,
        min_free_bytes=1024,
        min_free_inodes=30,
        disk_usage=lambda _path: SimpleNamespace(free=2048),
        statvfs=lambda _path: SimpleNamespace(f_favail=20),
    )

    assert low_space["ok"] is False
    assert low_space["status"] == "free_space_low"
    assert low_inodes["ok"] is False
    assert low_inodes["status"] == "free_inodes_low"


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
