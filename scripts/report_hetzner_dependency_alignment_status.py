#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import textwrap
from pathlib import Path
from typing import Any

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

DEFAULT_SSH_TARGET = "cryptkeep@100.86.128.9"
DEFAULT_APP_DIR = "/srv/cryptkeep/app"
DEFAULT_TIMEOUT_SEC = 90.0
DEFAULT_TRANSPORT = "tailscale-ssh"
DEFAULT_EXPECTED_BRANCH = "master"
AUTO_SSH_FALLBACK_REASONS = {
    "tailscale_cli_preferences_unavailable",
    "tailscale_ssh_auth_required",
}


def _preview(value: Any, *, limit: int = 500) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value)[:limit]


def _failure_payload(reason: str, *, stdout: Any = "", stderr: Any = "") -> dict[str, Any]:
    return {
        "ok": False,
        "status": "hetzner_dependency_alignment_blocked",
        "action": "report_hetzner_dependency_alignment_status",
        "read_only": True,
        "ssh_invoked": True,
        "pip_install_invoked": False,
        "pip_dry_run_invoked": False,
        "deploy_invoked": False,
        "service_restart_invoked": False,
        "checks": [],
        "blockers": [reason],
        "reason": reason,
        "stdout_preview": _preview(stdout),
        "stderr_preview": _preview(stderr),
        "recommendations": ["investigate_remote_dependency_status_failure"],
    }


def _remote_probe_program() -> str:
    return textwrap.dedent(
        """
        import json
        import subprocess

        def run(cmd, timeout=45):
            try:
                cp = subprocess.run(
                    cmd,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=timeout,
                )
            except FileNotFoundError as exc:
                return {"returncode": None, "stdout": "", "stderr": f"FileNotFoundError:{exc}"}
            except subprocess.TimeoutExpired as exc:
                return {
                    "returncode": None,
                    "stdout": exc.stdout or "",
                    "stderr": (exc.stderr or "") + f"\\nTimeoutExpired:{timeout}s",
                }
            except Exception as exc:
                return {"returncode": None, "stdout": "", "stderr": f"{type(exc).__name__}:{exc}"}
            return {"returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr}

        repo = {
            "head": run(["git", "rev-parse", "HEAD"]),
            "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "status": run(["git", "status", "--short", "--branch"]),
        }
        supply_chain_raw = run(["./.venv/bin/python", "scripts/check_supply_chain.py", "--json"], timeout=30)
        supply_chain = {"ok": False, "payload": None, "raw": supply_chain_raw, "error": ""}
        try:
            supply_chain["payload"] = json.loads(supply_chain_raw.get("stdout") or "{}")
            supply_chain["ok"] = supply_chain_raw.get("returncode") == 0
        except Exception as exc:
            supply_chain["error"] = f"supply_chain_parse_failed:{type(exc).__name__}:{exc}"

        pip_dry_run = run(
            ["./.venv/bin/python", "-m", "pip", "install", "--dry-run", "-r", "requirements-pinned.txt"],
            timeout=60,
        )

        print(json.dumps({
            "repo": repo,
            "supply_chain": supply_chain,
            "pip_dry_run": pip_dry_run,
        }, sort_keys=True))
        """
    ).strip()


def _remote_status_command(*, app_dir: str) -> str:
    return f"cd {shlex.quote(app_dir)} && python3 -c {shlex.quote(_remote_probe_program())}"


def _cmd_stdout(row: dict[str, Any]) -> str:
    return str(row.get("stdout") or "").strip()


def _cmd_ok(row: dict[str, Any]) -> bool:
    return row.get("returncode") == 0


def _check(name: str, ok: bool, status: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "status": status, "details": dict(details or {})}


def _status_line_branch(status_stdout: str) -> str:
    for line in str(status_stdout or "").splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def _dry_run_install_candidates(stdout: str) -> list[str]:
    for line in reversed(str(stdout or "").splitlines()):
        if line.startswith("Would install "):
            return sorted(part.strip() for part in line.removeprefix("Would install ").split() if part.strip())
    return []


def _tailscale_non_json_reason(*, stdout: Any, stderr: Any) -> str:
    combined = f"{stdout or ''}\n{stderr or ''}".lower()
    if "failed to load preferences" in combined:
        return "tailscale_cli_preferences_unavailable"
    if "tailscale ssh requires an additional check" in combined:
        return "tailscale_ssh_auth_required"
    if "authenticate" in combined and "tailscale" in combined:
        return "tailscale_ssh_auth_required"
    return ""


def _ssh_failure_reason(*, stdout: Any, stderr: Any) -> str:
    combined = f"{stdout or ''}\n{stderr or ''}".lower()
    if "host key verification failed" in combined:
        return "ssh_host_key_verification_failed"
    if "permission denied" in combined:
        return "ssh_auth_failed"
    if "operation not permitted" in combined:
        return "ssh_operation_not_permitted"
    if "connection timed out" in combined or "operation timed out" in combined:
        return "ssh_connect_timeout"
    return ""


def _transport_command(*, transport: str, ssh_target: str, remote_command: str) -> list[str]:
    if transport == "ssh":
        return ["ssh", "-o", "BatchMode=yes", ssh_target, remote_command]
    return ["tailscale", "ssh", ssh_target, remote_command]


def _with_transport_metadata(payload: dict[str, Any], *, transport: str) -> dict[str, Any]:
    out = dict(payload)
    out["transport"] = transport
    return out


def build_report(
    *,
    remote_payload: dict[str, Any],
    expected_branch: str = DEFAULT_EXPECTED_BRANCH,
    expected_commit: str | None = None,
) -> dict[str, Any]:
    repo = remote_payload.get("repo") if isinstance(remote_payload.get("repo"), dict) else {}
    supply_chain = remote_payload.get("supply_chain") if isinstance(remote_payload.get("supply_chain"), dict) else {}
    supply_payload = supply_chain.get("payload") if isinstance(supply_chain.get("payload"), dict) else {}
    pip_dry_run = remote_payload.get("pip_dry_run") if isinstance(remote_payload.get("pip_dry_run"), dict) else {}

    head = _cmd_stdout(repo.get("head") or {})
    branch = _cmd_stdout(repo.get("branch") or {})
    status_line = _status_line_branch(_cmd_stdout(repo.get("status") or {}))
    git_dirty = bool(supply_payload.get("git_dirty")) if isinstance(supply_payload, dict) else True
    pin_integrity = supply_payload.get("pin_integrity") if isinstance(supply_payload.get("pin_integrity"), dict) else {}
    environment = supply_payload.get("environment") if isinstance(supply_payload.get("environment"), dict) else {}
    vulnerability_audit = (
        supply_payload.get("vulnerability_audit")
        if isinstance(supply_payload.get("vulnerability_audit"), dict)
        else {}
    )
    install_candidates = _dry_run_install_candidates(str(pip_dry_run.get("stdout") or ""))

    checks = [
        _check(
            "remote_checkout_branch",
            branch == expected_branch,
            "matches" if branch == expected_branch else "mismatch",
            {"branch": branch, "expected_branch": expected_branch, "status_line": status_line},
        ),
        _check(
            "remote_checkout_commit",
            not expected_commit or head.startswith(expected_commit),
            "matches" if not expected_commit or head.startswith(expected_commit) else "mismatch",
            {"head": head, "expected_commit": expected_commit or ""},
        ),
        _check("remote_git_clean", not git_dirty, "clean" if not git_dirty else "dirty", {"git_dirty": git_dirty}),
        _check(
            "pin_integrity",
            bool(pin_integrity.get("ok")),
            "ok" if pin_integrity.get("ok") else "failed",
            {"problems": pin_integrity.get("problems") or [], "pin_count": pin_integrity.get("pin_count")},
        ),
        _check(
            "environment_alignment",
            bool(environment.get("ok")),
            "aligned" if environment.get("ok") else "mismatched",
            {
                "mismatches": environment.get("mismatches") or [],
                "not_installed": environment.get("not_installed") or [],
                "checked": environment.get("checked"),
            },
        ),
        _check(
            "pip_dry_run",
            _cmd_ok(pip_dry_run) and not install_candidates,
            "no_changes" if _cmd_ok(pip_dry_run) and not install_candidates else "would_change",
            {"install_candidates": install_candidates, "returncode": pip_dry_run.get("returncode")},
        ),
        _check(
            "vulnerability_audit_not_run",
            vulnerability_audit.get("ran") is False,
            "not_requested" if vulnerability_audit.get("ran") is False else "ran",
            {"vulnerability_audit": vulnerability_audit},
        ),
    ]

    blockers = [row["name"] for row in checks if not row["ok"]]
    ok = not blockers
    return {
        "ok": ok,
        "status": "hetzner_dependency_alignment_ready" if ok else "hetzner_dependency_alignment_blocked",
        "action": "report_hetzner_dependency_alignment_status",
        "read_only": True,
        "ssh_invoked": True,
        "pip_install_invoked": False,
        "pip_dry_run_invoked": True,
        "deploy_invoked": False,
        "service_restart_invoked": False,
        "remote": {
            "head": head,
            "branch": branch,
            "status_line": status_line,
            "git_sha": supply_payload.get("git_sha") if isinstance(supply_payload, dict) else "",
            "requirement_file_sha256": supply_payload.get("requirement_file_sha256")
            if isinstance(supply_payload, dict)
            else {},
        },
        "checks": checks,
        "blockers": blockers,
        "dry_run_install_candidates": install_candidates,
        "mismatches": environment.get("mismatches") or [],
        "not_installed": environment.get("not_installed") or [],
        "recommendations": (
            ["host_dependency_alignment_not_needed"]
            if ok
            else ["run_operator_approved_dependency_alignment_runbook"]
        ),
    }


def fetch_remote_status(
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    app_dir: str = DEFAULT_APP_DIR,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    transport: str = DEFAULT_TRANSPORT,
    allow_auto_ssh_fallback: bool = True,
    expected_branch: str = DEFAULT_EXPECTED_BRANCH,
    expected_commit: str | None = None,
) -> dict[str, Any]:
    remote_command = _remote_status_command(app_dir=app_dir)
    transport_name = str(transport or DEFAULT_TRANSPORT)
    cmd = _transport_command(transport=transport_name, ssh_target=ssh_target, remote_command=remote_command)

    try:
        result = subprocess.run(cmd, capture_output=True, check=False, text=True, timeout=timeout_sec)
    except FileNotFoundError:
        payload = _failure_payload("ssh_cli_not_found" if transport_name == "ssh" else "tailscale_cli_not_found")
        return _with_transport_metadata(payload, transport=transport_name)
    except subprocess.TimeoutExpired as exc:
        non_json_reason = _tailscale_non_json_reason(
            stdout=getattr(exc, "stdout", ""),
            stderr=getattr(exc, "stderr", ""),
        )
        if non_json_reason:
            payload = _failure_payload(
                non_json_reason,
                stdout=getattr(exc, "stdout", ""),
                stderr=getattr(exc, "stderr", ""),
            )
            if allow_auto_ssh_fallback and transport_name == DEFAULT_TRANSPORT:
                fallback = fetch_remote_status(
                    ssh_target=ssh_target,
                    app_dir=app_dir,
                    timeout_sec=timeout_sec,
                    transport="ssh",
                    allow_auto_ssh_fallback=False,
                    expected_branch=expected_branch,
                    expected_commit=expected_commit,
                )
                fallback["transport_fallback"] = {"from": transport_name, "reason": non_json_reason}
                return fallback
            return _with_transport_metadata(payload, transport=transport_name)
        payload = _failure_payload(
            f"{'ssh_timeout' if transport_name == 'ssh' else 'tailscale_ssh_timeout'}:{timeout_sec:g}s",
            stdout=getattr(exc, "stdout", ""),
            stderr=getattr(exc, "stderr", ""),
        )
        return _with_transport_metadata(payload, transport=transport_name)
    except OSError as exc:
        payload = _failure_payload(
            f"{'ssh_os_error' if transport_name == 'ssh' else 'tailscale_ssh_os_error'}:{type(exc).__name__}:{exc}"
        )
        return _with_transport_metadata(payload, transport=transport_name)

    if result.returncode != 0:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        if non_json_reason:
            payload = _failure_payload(non_json_reason, stdout=result.stdout, stderr=result.stderr)
            if allow_auto_ssh_fallback and transport_name == DEFAULT_TRANSPORT:
                fallback = fetch_remote_status(
                    ssh_target=ssh_target,
                    app_dir=app_dir,
                    timeout_sec=timeout_sec,
                    transport="ssh",
                    allow_auto_ssh_fallback=False,
                    expected_branch=expected_branch,
                    expected_commit=expected_commit,
                )
                fallback["transport_fallback"] = {"from": transport_name, "reason": non_json_reason}
                return fallback
            return _with_transport_metadata(payload, transport=transport_name)
        if transport_name == "ssh":
            reason = _ssh_failure_reason(stdout=result.stdout, stderr=result.stderr)
            if reason:
                payload = _failure_payload(reason, stdout=result.stdout, stderr=result.stderr)
                return _with_transport_metadata(payload, transport=transport_name)
        payload = _failure_payload(
            f"{'ssh_failed' if transport_name == 'ssh' else 'tailscale_ssh_failed'}:{result.returncode}",
            stdout=result.stdout,
            stderr=result.stderr,
        )
        return _with_transport_metadata(payload, transport=transport_name)

    try:
        payload = build_report(
            remote_payload=json.loads(result.stdout),
            expected_branch=expected_branch,
            expected_commit=expected_commit,
        )
        return _with_transport_metadata(payload, transport=transport_name)
    except (json.JSONDecodeError, ValueError) as exc:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        if non_json_reason:
            payload = _failure_payload(non_json_reason, stdout=result.stdout, stderr=result.stderr)
            if allow_auto_ssh_fallback and transport_name == DEFAULT_TRANSPORT:
                fallback = fetch_remote_status(
                    ssh_target=ssh_target,
                    app_dir=app_dir,
                    timeout_sec=timeout_sec,
                    transport="ssh",
                    allow_auto_ssh_fallback=False,
                    expected_branch=expected_branch,
                    expected_commit=expected_commit,
                )
                fallback["transport_fallback"] = {"from": transport_name, "reason": non_json_reason}
                return fallback
            return _with_transport_metadata(payload, transport=transport_name)
        payload = _failure_payload(
            f"remote_dependency_status_parse_failed:{type(exc).__name__}:{exc}",
            stdout=result.stdout,
            stderr=result.stderr,
        )
        return _with_transport_metadata(payload, transport=transport_name)


def _print_text(payload: dict[str, Any]) -> None:
    print("=== Hetzner Dependency Alignment Status ===")
    print(f"status={payload.get('status')}")
    print(f"ok={payload.get('ok')}")
    print("read_only=True")
    if payload.get("transport"):
        print(f"transport={payload.get('transport')}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    remote = payload.get("remote") if isinstance(payload.get("remote"), dict) else {}
    if remote:
        print(f"remote_branch={remote.get('branch')}")
        print(f"remote_head={remote.get('head')}")
    blockers = payload.get("blockers") or []
    print(f"blocking_checks={len(blockers)}")
    for row in payload.get("checks") or []:
        print(f"- {'ok' if row.get('ok') else 'failed'} {row.get('name')}: {row.get('status')}")
    candidates = payload.get("dry_run_install_candidates") or []
    if candidates:
        print("dry_run_install_candidates:")
        for item in candidates:
            print(f"- {item}")
    mismatches = payload.get("mismatches") or []
    if mismatches:
        print("mismatches:")
        for item in mismatches:
            print(f"- {item}")
    recommendations = payload.get("recommendations") or []
    if recommendations:
        print("recommendations:")
        for item in recommendations:
            print(f"- {item}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only Hetzner dependency alignment status")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero when dependency alignment is blocked")
    ap.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET, help="Remote SSH target")
    ap.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="Remote app checkout")
    ap.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC, help="Remote command timeout")
    ap.add_argument(
        "--transport",
        choices=("tailscale-ssh", "ssh"),
        default=DEFAULT_TRANSPORT,
        help=(
            "Remote transport. Defaults to Tailscale SSH and can auto-fallback "
            "to direct SSH for local Tailscale auth failures."
        ),
    )
    ap.add_argument("--expected-branch", default=DEFAULT_EXPECTED_BRANCH, help="Expected remote branch")
    ap.add_argument("--expected-commit", default=None, help="Optional expected remote commit prefix")
    args = ap.parse_args(argv)

    payload = fetch_remote_status(
        ssh_target=args.ssh_target,
        app_dir=args.app_dir,
        timeout_sec=args.timeout_sec,
        transport=args.transport,
        expected_branch=args.expected_branch,
        expected_commit=args.expected_commit,
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)
    return 1 if args.strict and not payload.get("ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())
