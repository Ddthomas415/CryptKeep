#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

# CBP_BOOTSTRAP_SYS_PATH
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

DEFAULT_SSH_TARGET = "cryptkeep@100.86.128.9"
DEFAULT_APP_DIR = "/srv/cryptkeep/app"
DEFAULT_CONFIG = "configs/paper_evidence_campaigns.hetzner.example.json"
DEFAULT_TIMEOUT_SEC = 45.0
DEFAULT_TRANSPORT = "tailscale-ssh"


def _preview(value: Any, *, limit: int = 500) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value)[:limit]


def _with_transport_metadata(payload: dict[str, Any], *, transport: str) -> dict[str, Any]:
    out = dict(payload)
    out["transport"] = transport
    return out


def _failure_payload(reason: str, *, stdout: Any = "", stderr: Any = "") -> dict[str, Any]:
    return {
        "ok": False,
        "status": "hetzner_paper_host_health_unavailable",
        "action": "report_hetzner_paper_host_health",
        "read_only": True,
        "ssh_invoked": True,
        "restore_invoked": False,
        "collector_mutation_invoked": False,
        "reason": reason,
        "stdout_preview": _preview(stdout),
        "stderr_preview": _preview(stderr),
        "recommendations": ["investigate_remote_health_report_failure"],
    }


def _tailscale_non_json_reason(*, stdout: Any, stderr: Any) -> str:
    combined = f"{stdout or ''}\n{stderr or ''}".lower()
    if "failed to load preferences" in combined:
        return "tailscale_cli_preferences_unavailable"
    if "tailscale ssh requires an additional check" in combined:
        return "tailscale_ssh_auth_required"
    if "authenticate" in combined and "tailscale" in combined:
        return "tailscale_ssh_auth_required"
    return ""


def _remote_health_command(
    *,
    app_dir: str,
    config_path: str,
    expected_commit: str | None = None,
    require_state: bool = False,
    backup_dir: str | None = None,
    min_free_gb: float | None = None,
    min_free_inodes: int | None = None,
    no_alert: bool = False,
) -> str:
    parts = [
        "cd",
        shlex.quote(app_dir),
        "&&",
        "./.venv/bin/python",
        "scripts/check_hetzner_paper_host_health.py",
        "--json",
        "--config",
        shlex.quote(config_path),
    ]
    if expected_commit:
        parts.extend(["--expected-commit", shlex.quote(expected_commit)])
    if require_state:
        parts.append("--require-state")
    if backup_dir:
        parts.extend(["--backup-dir", shlex.quote(backup_dir)])
    if min_free_gb is not None:
        parts.extend(["--min-free-gb", shlex.quote(str(float(min_free_gb)))])
    if min_free_inodes is not None:
        parts.extend(["--min-free-inodes", shlex.quote(str(int(min_free_inodes)))])
    if no_alert:
        parts.append("--no-alert")
    return " ".join(parts)


def _transport_command(
    *,
    transport: str,
    ssh_target: str,
    remote_command: str,
) -> list[str]:
    if transport == "ssh":
        return ["ssh", "-o", "BatchMode=yes", ssh_target, remote_command]
    return ["tailscale", "ssh", ssh_target, remote_command]


def fetch_remote_health(
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    app_dir: str = DEFAULT_APP_DIR,
    config_path: str = DEFAULT_CONFIG,
    expected_commit: str | None = None,
    require_state: bool = False,
    backup_dir: str | None = None,
    min_free_gb: float | None = None,
    min_free_inodes: int | None = None,
    no_alert: bool = False,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    transport: str = DEFAULT_TRANSPORT,
) -> dict[str, Any]:
    transport_name = str(transport or DEFAULT_TRANSPORT)
    remote_command = _remote_health_command(
        app_dir=app_dir,
        config_path=config_path,
        expected_commit=expected_commit,
        require_state=require_state,
        backup_dir=backup_dir,
        min_free_gb=min_free_gb,
        min_free_inodes=min_free_inodes,
        no_alert=no_alert,
    )
    cmd = _transport_command(
        transport=transport_name,
        ssh_target=ssh_target,
        remote_command=remote_command,
    )
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
    except FileNotFoundError:
        return _with_transport_metadata(
            _failure_payload(
                "ssh_cli_not_found" if transport_name == "ssh" else "tailscale_cli_not_found"
            ),
            transport=transport_name,
        )
    except subprocess.TimeoutExpired as exc:
        non_json_reason = _tailscale_non_json_reason(
            stdout=getattr(exc, "stdout", ""),
            stderr=getattr(exc, "stderr", ""),
        )
        return _with_transport_metadata(
            _failure_payload(
                non_json_reason or f"{transport_name}_timeout:{timeout_sec:g}s",
                stdout=getattr(exc, "stdout", ""),
                stderr=getattr(exc, "stderr", ""),
            ),
            transport=transport_name,
        )

    try:
        payload = json.loads(str(result.stdout or "{}"))
    except json.JSONDecodeError:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        return _with_transport_metadata(
            _failure_payload(
                non_json_reason or "remote_health_invalid_json",
                stdout=result.stdout,
                stderr=result.stderr,
            ),
            transport=transport_name,
        )
    if not isinstance(payload, dict):
        return _with_transport_metadata(
            _failure_payload(
                "remote_health_non_object_json",
                stdout=result.stdout,
                stderr=result.stderr,
            ),
            transport=transport_name,
        )
    if "ok" not in payload and "status" not in payload:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        return _with_transport_metadata(
            _failure_payload(
                non_json_reason or "remote_health_missing_fields",
                stdout=result.stdout,
                stderr=result.stderr,
            ),
            transport=transport_name,
        )

    out = dict(payload)
    out["transport"] = transport_name
    out["remote_returncode"] = result.returncode
    out["remote_app_dir"] = app_dir
    out["remote_config"] = config_path
    if result.returncode != 0 and bool(out.get("ok")):
        out["ok"] = False
        out["status"] = "remote_health_returncode_mismatch"
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Hetzner paper-host health check on the Hetzner host over "
            "Tailscale SSH. This avoids running Linux-only host checks on macOS."
        )
    )
    parser.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET)
    parser.add_argument("--transport", choices=("tailscale-ssh", "ssh"), default=DEFAULT_TRANSPORT)
    parser.add_argument("--app-dir", default=DEFAULT_APP_DIR)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--expected-commit")
    parser.add_argument("--require-state", action="store_true")
    parser.add_argument("--backup-dir")
    parser.add_argument("--min-free-gb", type=float)
    parser.add_argument("--min-free-inodes", type=int)
    parser.add_argument("--no-alert", action="store_true")
    parser.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--strict", action="store_true", help="Exit 1 when remote health is not ok")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser.parse_args(argv)


def _print_summary(report: dict[str, Any]) -> None:
    print("=== Hetzner Paper Host Health ===")
    print(f"status={report.get('status')}")
    print(f"ok={bool(report.get('ok'))}")
    print(f"transport={report.get('transport')}")
    print(f"remote_returncode={report.get('remote_returncode')}")
    print(f"artifact_path={report.get('artifact_path')}")
    for row in list(report.get("failed_checks") or []):
        if isinstance(row, dict):
            print(f"- failed {row.get('name')}: {row.get('status')}")
    if report.get("reason"):
        print(f"reason={report.get('reason')}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = fetch_remote_health(
        ssh_target=args.ssh_target,
        app_dir=args.app_dir,
        config_path=args.config,
        expected_commit=args.expected_commit,
        require_state=bool(args.require_state),
        backup_dir=args.backup_dir,
        min_free_gb=args.min_free_gb,
        min_free_inodes=args.min_free_inodes,
        no_alert=bool(args.no_alert),
        timeout_sec=float(args.timeout_sec),
        transport=args.transport,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(report)
    return 1 if args.strict and not bool(report.get("ok")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
