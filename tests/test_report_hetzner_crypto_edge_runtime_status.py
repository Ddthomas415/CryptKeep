from __future__ import annotations

import json
import subprocess

from scripts import report_hetzner_crypto_edge_runtime_status as script


def _cmd(stdout: str = "", returncode: int = 0, stderr: str = "") -> dict:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


def _remote_payload(
    *,
    head: str = "e8224057f123",
    branch: str = "master",
    files: dict | None = None,
    plan: dict | None = None,
    collector: dict | None = None,
    scheduler: dict | None = None,
) -> dict:
    if files is None:
        files = {path: True for path in script.REQUIRED_REMOTE_FILES}
        files["venv_python"] = True
    if plan is None:
        plan = {
            "ok": True,
            "path": script.DEFAULT_PLAN_PATH,
            "payload": {
                "funding": [{"venue": "okx", "symbol": "BTC/USDT:USDT"}],
                "open_interest": [{"venue": "okx", "symbol": "BTC/USDT:USDT"}],
                "basis": [{"venue": "okx", "spot_symbol": "BTC/USDT", "perp_symbol": "BTC/USDT:USDT"}],
                "quotes": [{"venue": "coinbase", "symbol": "BTC/USD"}],
            },
            "error": "",
        }
    if collector is None:
        collector = {
            "attempted": True,
            "ok": True,
            "payload": {"status": "running", "pid": 1234, "pid_alive": True},
            "error": "",
        }
    if scheduler is None:
        scheduler = {
            "systemd_edge_cadence_enabled": _cmd("enabled\n"),
            "systemd_edge_cadence_active": _cmd("active\n"),
            "systemd_user_timers": _cmd("cbp-edge-cadence.timer\nrun_crypto_edge_collector_loop.py\n"),
            "crontab": _cmd(""),
        }
    return {
        "repo": {
            "head": _cmd(head + "\n"),
            "branch": _cmd(branch + "\n"),
            "status": _cmd(f"## {branch}...origin/{branch}\n"),
        },
        "files": files,
        "plan": plan,
        "collector_status": collector,
        "scheduler": scheduler,
    }


def test_build_report_passes_only_when_checkout_plan_runtime_and_schedules_are_ready() -> None:
    report = script.build_report(
        remote_payload=_remote_payload(),
        expected_branch="master",
        expected_commit="e8224057f",
        expected_derivatives_venue="okx",
    )

    assert report["ok"] is True
    assert report["status"] == "hetzner_crypto_edge_runtime_ready"
    assert report["blockers"] == []
    assert report["collector_start_invoked"] is False
    assert report["deploy_invoked"] is False


def test_build_report_accepts_systemd_system_collector_and_cadence_units() -> None:
    scheduler = {
        "systemd_edge_cadence_enabled": _cmd("disabled\n", returncode=1),
        "systemd_edge_cadence_active": _cmd("inactive\n", returncode=3),
        "systemd_system_edge_cadence_enabled": _cmd("enabled\n"),
        "systemd_system_edge_cadence_active": _cmd("active\n"),
        "systemd_crypto_edge_collector_enabled": _cmd("enabled\n"),
        "systemd_crypto_edge_collector_active": _cmd("active\n"),
        "systemd_user_timers": _cmd(""),
        "systemd_system_timers": _cmd("cbp-edge-cadence.timer\n"),
        "crontab": _cmd(""),
    }

    report = script.build_report(
        remote_payload=_remote_payload(scheduler=scheduler),
        expected_branch="master",
        expected_commit="e8224057f",
        expected_derivatives_venue="okx",
    )

    assert report["ok"] is True
    collector_check = next(row for row in report["checks"] if row["name"] == "collector_schedule")
    cadence_check = next(row for row in report["checks"] if row["name"] == "cadence_checker_schedule")
    assert collector_check["details"]["collector_service_enabled"] == "enabled"
    assert collector_check["details"]["collector_service_active"] == "active"
    assert cadence_check["details"]["system_timer_enabled"] == "enabled"
    assert cadence_check["details"]["system_timer_active"] == "active"


def test_build_report_blocks_stale_binance_unscheduled_remote_state() -> None:
    files = {
        "scripts/check_cost_assumptions.py": False,
        "scripts/check_edge_cadence.py": False,
        "scripts/data/run_crypto_edge_collector_loop.py": True,
        script.DEFAULT_PLAN_PATH: True,
        "venv_python": True,
    }
    plan = {
        "ok": True,
        "path": script.DEFAULT_PLAN_PATH,
        "payload": {
            "funding": [{"venue": "binance", "symbol": "BTC/USDT:USDT"}],
            "open_interest": [{"venue": "binance", "symbol": "BTC/USDT:USDT"}],
            "basis": [{"venue": "binance", "spot_symbol": "BTC/USDT", "perp_symbol": "BTC/USDT:USDT"}],
        },
        "error": "",
    }
    collector = {
        "attempted": True,
        "ok": True,
        "payload": {
            "status": "not_started",
            "reason": "status_missing",
            "pid": None,
            "pid_alive": False,
        },
        "error": "",
    }
    scheduler = {
        "systemd_edge_cadence_enabled": _cmd("disabled\n", returncode=1),
        "systemd_edge_cadence_active": _cmd("inactive\n", returncode=3),
        "systemd_user_timers": _cmd(""),
        "crontab": _cmd(""),
    }

    report = script.build_report(
        remote_payload=_remote_payload(
            head="b86105b1f491058aac235dcbb33748729dee7297",
            branch="review-stabilized",
            files=files,
            plan=plan,
            collector=collector,
            scheduler=scheduler,
        ),
        expected_branch="master",
        expected_commit="e8224057f",
        expected_derivatives_venue="okx",
    )

    assert report["ok"] is False
    assert report["status"] == "hetzner_crypto_edge_runtime_blocked"
    assert report["blockers"] == [
        "remote_checkout_branch",
        "remote_checkout_commit",
        "required_tooling",
        "collector_plan_derivatives_source",
        "collector_runtime_status",
        "collector_schedule",
        "cadence_checker_schedule",
    ]
    plan_check = next(row for row in report["checks"] if row["name"] == "collector_plan_derivatives_source")
    assert plan_check["details"]["venues"] == {
        "funding": ["binance"],
        "open_interest": ["binance"],
        "basis": ["binance"],
    }
    assert report["collector_start_invoked"] is False
    assert report["collector_stop_invoked"] is False
    assert report["deploy_invoked"] is False


def test_fetch_remote_runtime_status_builds_read_only_tailscale_command(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def _run(cmd, *, capture_output, check, text, timeout):
        seen["cmd"] = cmd
        seen["capture_output"] = capture_output
        seen["check"] = check
        seen["text"] = text
        seen["timeout"] = timeout
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(_remote_payload()), stderr="")

    monkeypatch.setattr(script.subprocess, "run", _run)

    report = script.fetch_remote_runtime_status(
        ssh_target="cryptkeep@100.86.128.9",
        app_dir="/srv/cryptkeep/app",
        expected_commit="e8224057f",
        timeout_sec=3.0,
    )

    assert report["ok"] is True
    assert seen["cmd"][0:3] == ["tailscale", "ssh", "cryptkeep@100.86.128.9"]
    remote_command = seen["cmd"][3]
    assert remote_command.startswith("cd /srv/cryptkeep/app && python3 -c ")
    assert "run_crypto_edge_collector_loop.py" in remote_command
    assert "scripts/check_edge_cadence.py" in remote_command
    assert "cbp-crypto-edge-collector.service" in remote_command
    assert seen["capture_output"] is True
    assert seen["check"] is False
    assert seen["text"] is True
    assert seen["timeout"] == 3.0


def test_fetch_remote_runtime_status_classifies_tailscale_auth_prompt(monkeypatch) -> None:
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

    report = script.fetch_remote_runtime_status(timeout_sec=1.0)

    assert report["ok"] is False
    assert report["reason"] == "tailscale_ssh_auth_required"
    assert report["collector_start_invoked"] is False
    assert "login.tailscale.com" in report["stderr_preview"]


def test_main_strict_returns_one_when_blocked(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "fetch_remote_runtime_status",
        lambda **kwargs: {
            "ok": False,
            "status": "hetzner_crypto_edge_runtime_blocked",
            "read_only": True,
            "blockers": ["collector_schedule"],
            "checks": [],
            "remote": {"head": "b86105b", "branch": "review-stabilized"},
            "recommendations": ["do not start collector"],
        },
    )

    assert script.main(["--strict", "--json", "--timeout-sec", "1"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["blockers"] == ["collector_schedule"]


def test_plain_summary_prints_transport_failure_reason(capsys) -> None:
    script._print_summary(
        {
            "ok": False,
            "status": "hetzner_crypto_edge_runtime_blocked",
            "read_only": True,
            "reason": "tailscale_ssh_auth_required",
            "blockers": ["tailscale_ssh_auth_required"],
            "checks": [],
            "recommendations": ["investigate_remote_status_failure"],
        }
    )

    out = capsys.readouterr().out
    assert "reason=tailscale_ssh_auth_required" in out
    assert "- failed tailscale_ssh_auth_required" in out
