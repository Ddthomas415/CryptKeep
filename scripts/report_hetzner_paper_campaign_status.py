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
    from _bootstrap import add_repo_root_to_syspath  # noqa: E402
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath  # noqa: E402

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

from scripts import report_paper_campaign_status as formatter  # noqa: E402


DEFAULT_SSH_TARGET = "cryptkeep@100.86.128.9"
DEFAULT_APP_DIR = "/srv/cryptkeep/app"
DEFAULT_CONFIG = "configs/paper_evidence_campaigns.hetzner.example.json"
DEFAULT_TIMEOUT_SEC = 45.0


def _preview(value: Any, *, limit: int = 500) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value)[:limit]


def _failure_payload(
    reason: str,
    *,
    stdout: Any = "",
    stderr: Any = "",
) -> dict[str, Any]:
    return {
        "ok": False,
        "action": "report_hetzner_paper_campaign_status",
        "read_only": True,
        "all_running": False,
        "campaign_count": 0,
        "running_count": 0,
        "campaigns": [],
        "reason": reason,
        "stdout_preview": _preview(stdout),
        "stderr_preview": _preview(stderr),
        "recommendations": ["investigate_report_failure"],
    }


def _remote_status_command(*, app_dir: str, config_path: str) -> str:
    quoted_app_dir = shlex.quote(app_dir)
    quoted_config_path = shlex.quote(config_path)
    return (
        f"cd {quoted_app_dir} && ./.venv/bin/python "
        "scripts/restore_paper_campaigns.py "
        f"--config {quoted_config_path} --status"
    )


def _tailscale_non_json_reason(*, stdout: Any, stderr: Any) -> str:
    combined = f"{stdout or ''}\n{stderr or ''}".lower()
    if "failed to load preferences" in combined:
        return "tailscale_cli_preferences_unavailable"
    if "tailscale ssh requires an additional check" in combined:
        return "tailscale_ssh_auth_required"
    if "authenticate" in combined and "tailscale" in combined:
        return "tailscale_ssh_auth_required"
    return ""


def fetch_remote_status(
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    app_dir: str = DEFAULT_APP_DIR,
    config_path: str = DEFAULT_CONFIG,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> dict[str, Any]:
    remote_command = _remote_status_command(app_dir=app_dir, config_path=config_path)
    cmd = ["tailscale", "ssh", ssh_target, remote_command]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_sec,
        )
    except FileNotFoundError:
        return _failure_payload("tailscale_cli_not_found")
    except subprocess.TimeoutExpired as exc:
        return _failure_payload(
            f"tailscale_ssh_timeout:{timeout_sec:g}s",
            stdout=getattr(exc, "stdout", ""),
            stderr=getattr(exc, "stderr", ""),
        )
    except OSError as exc:
        return _failure_payload(f"tailscale_ssh_os_error:{type(exc).__name__}:{exc}")

    if result.returncode != 0:
        return _failure_payload(
            f"tailscale_ssh_failed:{result.returncode}",
            stdout=result.stdout,
            stderr=result.stderr,
        )

    try:
        return formatter.build_report_from_status(json.loads(result.stdout))
    except (json.JSONDecodeError, ValueError) as exc:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        if non_json_reason:
            return _failure_payload(
                non_json_reason,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        return _failure_payload(
            f"remote_status_parse_failed:{type(exc).__name__}:{exc}",
            stdout=result.stdout,
            stderr=result.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Read-only Hetzner paper campaign status over Tailscale SSH"
    )
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when remote status needs investigation",
    )
    ap.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET, help="Tailscale SSH target")
    ap.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="Remote repo directory")
    ap.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help="Remote paper campaign manifest path",
    )
    ap.add_argument(
        "--timeout-sec",
        type=float,
        default=DEFAULT_TIMEOUT_SEC,
        help="Maximum seconds to wait for Tailscale SSH status output",
    )
    args = ap.parse_args(argv)

    timeout_sec = max(float(args.timeout_sec), 1.0)
    payload = fetch_remote_status(
        ssh_target=str(args.ssh_target),
        app_dir=str(args.app_dir),
        config_path=str(args.config),
        timeout_sec=timeout_sec,
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        formatter.print_report(payload)

    if args.strict and not bool(payload.get("ok")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
