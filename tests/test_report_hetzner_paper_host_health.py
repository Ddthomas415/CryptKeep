from __future__ import annotations

import json
import subprocess

from scripts import report_hetzner_paper_host_health as script


def test_remote_health_command_runs_host_local_check_on_remote_app_dir() -> None:
    command = script._remote_health_command(
        app_dir="/srv/cryptkeep/app",
        config_path="configs/paper_evidence_campaigns.hetzner.example.json",
        expected_commit="abc123",
        require_state=True,
        backup_dir="/srv/cryptkeep/backups",
        min_free_gb=2,
        min_free_inodes=10000,
        no_alert=True,
    )

    assert command.startswith("cd /srv/cryptkeep/app && ./.venv/bin/python ")
    assert "scripts/check_hetzner_paper_host_health.py" in command
    assert "--json" in command
    assert "--config configs/paper_evidence_campaigns.hetzner.example.json" in command
    assert "--expected-commit abc123" in command
    assert "--require-state" in command
    assert "--backup-dir /srv/cryptkeep/backups" in command
    assert "--min-free-gb 2.0" in command
    assert "--min-free-inodes 10000" in command
    assert "--no-alert" in command


def test_fetch_remote_health_uses_tailscale_ssh_and_preserves_failed_health(monkeypatch) -> None:
    seen: list[list[str]] = []

    def _run(cmd, *, capture_output, check, text, timeout):
        seen.append(cmd)
        return subprocess.CompletedProcess(
            cmd,
            1,
            stdout=json.dumps(
                {
                    "ok": False,
                    "status": "hetzner_paper_host_blocked",
                    "failed_checks": [{"name": "time_sync", "status": "ntp_not_synchronized"}],
                    "artifact_path": "/srv/cryptkeep/app/.cbp_state/runtime/snapshots/hetzner_paper_host_health.latest.json",
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_health(timeout_sec=3)

    assert seen[0][0:2] == ["tailscale", "ssh"]
    assert "scripts/check_hetzner_paper_host_health.py" in seen[0][3]
    assert out["ok"] is False
    assert out["status"] == "hetzner_paper_host_blocked"
    assert out["transport"] == "tailscale-ssh"
    assert out["remote_returncode"] == 1
    assert out["failed_checks"][0]["name"] == "time_sync"


def test_fetch_remote_health_classifies_invalid_remote_json(monkeypatch) -> None:
    monkeypatch.setattr(
        script.subprocess,
        "run",
        lambda cmd, *, capture_output, check, text, timeout: subprocess.CompletedProcess(
            cmd,
            0,
            stdout="not json",
            stderr="",
        ),
    )

    out = script.fetch_remote_health(timeout_sec=3)

    assert out["ok"] is False
    assert out["reason"] == "remote_health_invalid_json"
    assert out["ssh_invoked"] is True


def test_main_strict_returns_one_for_failed_remote_health(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "fetch_remote_health",
        lambda **_kwargs: {
            "ok": False,
            "status": "hetzner_paper_host_blocked",
            "transport": "tailscale-ssh",
            "remote_returncode": 1,
            "failed_checks": [{"name": "storage_health", "status": "backup_dir_missing"}],
        },
    )

    rc = script.main(["--strict", "--json"])
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["status"] == "hetzner_paper_host_blocked"
    assert out["failed_checks"][0]["name"] == "storage_health"
