from __future__ import annotations

import json
import subprocess

from scripts import report_hetzner_paper_campaign_status as script


def test_fetch_remote_status_formats_valid_remote_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def _run(cmd, *, capture_output, check, text, timeout):
        seen["cmd"] = cmd
        seen["capture_output"] = capture_output
        seen["check"] = check
        seen["text"] = text
        seen["timeout"] = timeout
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout=json.dumps(
                {
                    "ok": True,
                    "all_running": True,
                    "campaign_count": 1,
                    "running_count": 1,
                    "campaigns": [
                        {
                            "name": "ema_cross_default",
                            "ok": True,
                            "running": True,
                            "status": "idle",
                            "reason": "waiting_for_next_day",
                            "strategy": "ema_cross",
                        }
                    ],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(
        ssh_target="cryptkeep@100.86.128.9",
        app_dir="/srv/cryptkeep/app",
        config_path="configs/paper_evidence_campaigns.hetzner.example.json",
        timeout_sec=3.0,
    )

    assert seen == {
        "cmd": [
            "tailscale",
            "ssh",
            "cryptkeep@100.86.128.9",
            "cd /srv/cryptkeep/app && ./.venv/bin/python "
            "scripts/restore_paper_campaigns.py "
            "--config configs/paper_evidence_campaigns.hetzner.example.json --status",
        ],
        "capture_output": True,
        "check": False,
        "text": True,
        "timeout": 3.0,
    }
    assert out["ok"] is True
    assert out["all_running"] is True
    assert out["campaigns"][0]["name"] == "ema_cross_default"


def test_fetch_remote_status_fails_closed_when_tailscale_ssh_fails(monkeypatch) -> None:
    def _run(cmd, *, capture_output, check, text, timeout):
        return subprocess.CompletedProcess(
            cmd,
            255,
            stdout="# Tailscale SSH requires an additional check.",
            stderr="authenticate in browser",
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=3.0)

    assert out["ok"] is False
    assert out["reason"] == "tailscale_ssh_failed:255"
    assert "Tailscale SSH requires" in out["stdout_preview"]
    assert "authenticate" in out["stderr_preview"]
    assert out["recommendations"] == ["investigate_report_failure"]


def test_fetch_remote_status_times_out_instead_of_blocking(monkeypatch) -> None:
    def _run(cmd, *, capture_output, check, text, timeout):
        raise subprocess.TimeoutExpired(
            cmd,
            timeout,
            output="# Tailscale SSH requires an additional check.",
            stderr="waiting for browser auth",
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=2.0)

    assert out["ok"] is False
    assert out["reason"] == "tailscale_ssh_timeout:2s"
    assert "Tailscale SSH requires" in out["stdout_preview"]
    assert "browser auth" in out["stderr_preview"]


def test_fetch_remote_status_classifies_tailscale_preferences_output(monkeypatch) -> None:
    def _run(cmd, *, capture_output, check, text, timeout):
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="The Tailscale CLI failed to start: Failed to load preferences.",
            stderr="",
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=1.0)

    assert out["ok"] is False
    assert out["reason"] == "tailscale_cli_preferences_unavailable"
    assert "Failed to load preferences" in out["stdout_preview"]


def test_fetch_remote_status_classifies_tailscale_auth_prompt_output(monkeypatch) -> None:
    def _run(cmd, *, capture_output, check, text, timeout):
        return subprocess.CompletedProcess(
            cmd,
            0,
            stdout="",
            stderr=(
                "# Tailscale SSH requires an additional check.\n"
                "# To authenticate, visit: https://login.tailscale.com/a/example\n"
            ),
        )

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=1.0)

    assert out["ok"] is False
    assert out["reason"] == "tailscale_ssh_auth_required"
    assert "login.tailscale.com" in out["stderr_preview"]


def test_main_strict_returns_one_for_remote_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "fetch_remote_status",
        lambda **kwargs: {
            "ok": False,
            "read_only": True,
            "all_running": False,
            "campaign_count": 0,
            "running_count": 0,
            "campaigns": [],
            "reason": "tailscale_ssh_timeout:2s",
            "recommendations": ["investigate_report_failure"],
        },
    )

    assert script.main(["--strict", "--json", "--timeout-sec", "2"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["reason"] == "tailscale_ssh_timeout:2s"
