from __future__ import annotations

import json
import subprocess

from scripts import report_hetzner_dependency_alignment_status as script


def _cmd(stdout: str = "", returncode: int = 0, stderr: str = "") -> dict:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


def _supply_payload(*, ok: bool = True) -> dict:
    return {
        "git_sha": "abc123",
        "git_dirty": False,
        "requirement_file_sha256": {"requirements-pinned.txt": "sha"},
        "pin_integrity": {"ok": True, "problems": [], "pin_count": 83},
        "environment": {
            "ok": ok,
            "checked": 83,
            "mismatches": [] if ok else ["aiohttp: installed 3.13.5 != pinned 3.14.3"],
            "not_installed": [],
        },
        "vulnerability_audit": {"ran": False, "reason": "not_requested"},
    }


def _remote_payload(*, supply_ok: bool = True, dry_run_stdout: str = "") -> dict:
    return {
        "repo": {
            "head": _cmd("abc123\n"),
            "branch": _cmd("master\n"),
            "status": _cmd("## master...origin/master\n"),
        },
        "supply_chain": {
            "ok": supply_ok,
            "payload": _supply_payload(ok=supply_ok),
            "raw": _cmd(json.dumps(_supply_payload(ok=supply_ok)), returncode=0 if supply_ok else 1),
            "error": "",
        },
        "pip_dry_run": _cmd(dry_run_stdout),
    }


def test_build_report_ready_when_environment_matches_and_dry_run_has_no_changes() -> None:
    out = script.build_report(remote_payload=_remote_payload(), expected_commit="abc")

    assert out["ok"] is True
    assert out["status"] == "hetzner_dependency_alignment_ready"
    assert out["blockers"] == []
    assert out["pip_install_invoked"] is False
    assert out["pip_dry_run_invoked"] is True
    assert out["service_restart_invoked"] is False


def test_build_report_blocks_on_environment_mismatch_and_dry_run_candidates() -> None:
    out = script.build_report(
        remote_payload=_remote_payload(
            supply_ok=False,
            dry_run_stdout="Would install aiohttp-3.14.3 urllib3-2.7.0\n",
        ),
        expected_commit="abc",
    )

    assert out["ok"] is False
    assert out["status"] == "hetzner_dependency_alignment_blocked"
    assert "environment_alignment" in out["blockers"]
    assert "pip_dry_run" in out["blockers"]
    assert out["dry_run_install_candidates"] == ["aiohttp-3.14.3", "urllib3-2.7.0"]
    assert out["mismatches"] == ["aiohttp: installed 3.13.5 != pinned 3.14.3"]


def test_build_report_blocks_on_stale_checkout() -> None:
    payload = _remote_payload()
    payload["repo"]["branch"] = _cmd("review-stabilized\n")
    payload["repo"]["head"] = _cmd("old\n")

    out = script.build_report(remote_payload=payload, expected_branch="master", expected_commit="new")

    assert "remote_checkout_branch" in out["blockers"]
    assert "remote_checkout_commit" in out["blockers"]


def test_fetch_remote_status_formats_valid_remote_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def _run(cmd, *, capture_output, check, text, timeout):
        seen["cmd"] = cmd
        seen["capture_output"] = capture_output
        seen["check"] = check
        seen["text"] = text
        seen["timeout"] = timeout
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(_remote_payload()), stderr="")

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(
        ssh_target="cryptkeep@100.86.128.9",
        app_dir="/srv/cryptkeep/app",
        timeout_sec=3.0,
        transport="ssh",
        expected_commit="abc",
    )

    assert seen["cmd"][0:3] == ["ssh", "-o", "BatchMode=yes"]
    assert seen["cmd"][3] == "cryptkeep@100.86.128.9"
    assert out["ok"] is True
    assert out["transport"] == "ssh"


def test_fetch_remote_status_auto_falls_back_to_direct_ssh_for_tailscale_preferences(monkeypatch) -> None:
    seen: list[list[str]] = []

    def _run(cmd, *, capture_output, check, text, timeout):
        seen.append(cmd)
        if cmd[0] == "tailscale":
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout="The Tailscale CLI failed to start: Failed to load preferences.",
                stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(_remote_payload()), stderr="")

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=3.0)

    assert [cmd[0] for cmd in seen] == ["tailscale", "ssh"]
    assert out["ok"] is True
    assert out["transport"] == "ssh"
    assert out["transport_fallback"] == {
        "from": "tailscale-ssh",
        "reason": "tailscale_cli_preferences_unavailable",
    }


def test_fetch_remote_status_fails_closed_on_unparseable_remote_json(monkeypatch) -> None:
    def _run(cmd, *, capture_output, check, text, timeout):
        return subprocess.CompletedProcess(cmd, 0, stdout="not-json", stderr="")

    monkeypatch.setattr(script.subprocess, "run", _run)

    out = script.fetch_remote_status(timeout_sec=3.0, transport="ssh")

    assert out["ok"] is False
    assert out["reason"].startswith("remote_dependency_status_parse_failed:")
    assert out["pip_install_invoked"] is False


def test_main_strict_exits_nonzero_on_blocked_status(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "fetch_remote_status",
        lambda **kwargs: script.build_report(remote_payload=_remote_payload(supply_ok=False)),
    )

    rc = script.main(["--strict"])
    captured = capsys.readouterr()

    assert rc == 1
    assert "hetzner_dependency_alignment_blocked" in captured.out
