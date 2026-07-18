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
DEFAULT_TIMEOUT_SEC = 45.0
DEFAULT_EXPECTED_BRANCH = "master"
DEFAULT_EXPECTED_DERIVATIVES_VENUE = "okx"
DEFAULT_PLAN_PATH = "sample_data/crypto_edges/live_collector_plan.json"

REQUIRED_REMOTE_FILES = (
    "scripts/check_cost_assumptions.py",
    "scripts/check_edge_cadence.py",
    "scripts/data/run_crypto_edge_collector_loop.py",
    DEFAULT_PLAN_PATH,
)


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
        "status": "hetzner_crypto_edge_runtime_blocked",
        "action": "report_hetzner_crypto_edge_runtime_status",
        "read_only": True,
        "ssh_invoked": True,
        "collector_start_invoked": False,
        "collector_stop_invoked": False,
        "deploy_invoked": False,
        "remote": {},
        "checks": [],
        "blockers": [reason],
        "reason": reason,
        "stdout_preview": _preview(stdout),
        "stderr_preview": _preview(stderr),
        "recommendations": ["investigate_remote_status_failure"],
    }


def _remote_probe_program(*, plan_path: str) -> str:
    return textwrap.dedent(
        f"""
        import json
        import pathlib
        import subprocess

        PLAN_PATH = {plan_path!r}
        REQUIRED_FILES = {list(REQUIRED_REMOTE_FILES)!r}

        def run(cmd, timeout=8):
            try:
                cp = subprocess.run(
                    cmd,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=timeout,
                )
            except FileNotFoundError as exc:
                return {{"returncode": None, "stdout": "", "stderr": f"FileNotFoundError:{{exc}}"}}
            except subprocess.TimeoutExpired as exc:
                return {{
                    "returncode": None,
                    "stdout": exc.stdout or "",
                    "stderr": (exc.stderr or "") + f"\\nTimeoutExpired:{{timeout}}s",
                }}
            except Exception as exc:
                return {{"returncode": None, "stdout": "", "stderr": f"{{type(exc).__name__}}:{{exc}}"}}
            return {{
                "returncode": cp.returncode,
                "stdout": cp.stdout,
                "stderr": cp.stderr,
            }}

        root = pathlib.Path.cwd()
        files = {{path: (root / path).exists() for path in REQUIRED_FILES}}
        files["venv_python"] = (root / ".venv" / "bin" / "python").exists()
        repo = {{
            "head": run(["git", "rev-parse", "HEAD"]),
            "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "status": run(["git", "status", "--short", "--branch"]),
        }}

        plan = {{"ok": False, "path": PLAN_PATH, "payload": None, "error": ""}}
        try:
            plan["payload"] = json.loads((root / PLAN_PATH).read_text(encoding="utf-8"))
            plan["ok"] = True
        except Exception as exc:
            plan["error"] = f"{{type(exc).__name__}}:{{exc}}"

        collector_status = {{"attempted": False, "ok": False, "payload": None, "error": ""}}
        if files.get("scripts/data/run_crypto_edge_collector_loop.py") and files.get("venv_python"):
            collector_status["attempted"] = True
            raw = run(["./.venv/bin/python", "scripts/data/run_crypto_edge_collector_loop.py", "--status"])
            collector_status["raw"] = raw
            if raw.get("returncode") == 0:
                try:
                    collector_status["payload"] = json.loads(raw.get("stdout") or "{{}}")
                    collector_status["ok"] = True
                except Exception as exc:
                    collector_status["error"] = f"status_parse_failed:{{type(exc).__name__}}:{{exc}}"
            else:
                collector_status["error"] = f"status_command_failed:{{raw.get('returncode')}}"
        else:
            collector_status["error"] = "collector_status_unavailable"

        scheduler = {{
            "systemd_edge_cadence_enabled": run(["systemctl", "--user", "is-enabled", "cbp-edge-cadence.timer"]),
            "systemd_edge_cadence_active": run(["systemctl", "--user", "is-active", "cbp-edge-cadence.timer"]),
            "systemd_system_edge_cadence_enabled": run(["systemctl", "is-enabled", "cbp-edge-cadence.timer"]),
            "systemd_system_edge_cadence_active": run(["systemctl", "is-active", "cbp-edge-cadence.timer"]),
            "systemd_crypto_edge_collector_enabled": run(["systemctl", "is-enabled", "cbp-crypto-edge-collector.service"]),
            "systemd_crypto_edge_collector_active": run(["systemctl", "is-active", "cbp-crypto-edge-collector.service"]),
            "systemd_user_timers": run(["systemctl", "--user", "list-timers", "--all", "--no-pager"], timeout=12),
            "systemd_system_timers": run(["systemctl", "list-timers", "--all", "--no-pager"], timeout=12),
            "crontab": run(["crontab", "-l"]),
        }}

        print(json.dumps({{
            "repo": repo,
            "files": files,
            "plan": plan,
            "collector_status": collector_status,
            "scheduler": scheduler,
        }}, sort_keys=True))
        """
    ).strip()


def _remote_status_command(*, app_dir: str, plan_path: str) -> str:
    quoted_app_dir = shlex.quote(app_dir)
    quoted_program = shlex.quote(_remote_probe_program(plan_path=plan_path))
    return f"cd {quoted_app_dir} && python3 -c {quoted_program}"


def _cmd_stdout(row: dict[str, Any]) -> str:
    return str(row.get("stdout") or "").strip()


def _cmd_ok(row: dict[str, Any]) -> bool:
    return row.get("returncode") == 0


def _check(name: str, ok: bool, status: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "status": status,
        "details": dict(details or {}),
    }


def _plan_derivatives_summary(plan_payload: Any) -> dict[str, Any]:
    if not isinstance(plan_payload, dict):
        return {"ok": False, "venues": {}, "missing_families": ["funding", "open_interest", "basis"]}

    venues: dict[str, list[str]] = {}
    missing: list[str] = []
    for family in ("funding", "open_interest", "basis"):
        rows = plan_payload.get(family)
        if not isinstance(rows, list) or not rows:
            missing.append(family)
            venues[family] = []
            continue
        family_venues: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            venue = str(row.get("venue") or row.get("perp_venue") or "").strip().lower()
            if venue:
                family_venues.append(venue)
        venues[family] = sorted(set(family_venues))
    return {
        "ok": not missing,
        "venues": venues,
        "missing_families": missing,
    }


def _status_line_branch(status_stdout: str) -> str:
    for line in str(status_stdout or "").splitlines():
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def build_report(
    *,
    remote_payload: dict[str, Any],
    expected_branch: str = DEFAULT_EXPECTED_BRANCH,
    expected_commit: str = "",
    expected_derivatives_venue: str = DEFAULT_EXPECTED_DERIVATIVES_VENUE,
    app_dir: str = DEFAULT_APP_DIR,
) -> dict[str, Any]:
    repo = dict(remote_payload.get("repo") or {})
    files = dict(remote_payload.get("files") or {})
    plan = dict(remote_payload.get("plan") or {})
    collector_status = dict(remote_payload.get("collector_status") or {})
    scheduler = dict(remote_payload.get("scheduler") or {})

    head = _cmd_stdout(dict(repo.get("head") or {}))
    branch = _cmd_stdout(dict(repo.get("branch") or {}))
    status_branch = _status_line_branch(_cmd_stdout(dict(repo.get("status") or {})))
    expected_commit = str(expected_commit or "").strip()
    expected_branch = str(expected_branch or "").strip()
    expected_derivatives_venue = str(expected_derivatives_venue or "").strip().lower()

    missing_files = [path for path in REQUIRED_REMOTE_FILES if not bool(files.get(path))]
    required_files_ok = not missing_files and bool(files.get("venv_python"))
    missing_with_venv = list(missing_files)
    if not bool(files.get("venv_python")):
        missing_with_venv.append(".venv/bin/python")

    branch_ok = (not expected_branch) or branch == expected_branch
    commit_ok = (not expected_commit) or head.startswith(expected_commit)
    plan_summary = _plan_derivatives_summary(plan.get("payload"))
    plan_venues = dict(plan_summary.get("venues") or {})
    plan_derivatives_ok = (
        bool(plan.get("ok"))
        and bool(plan_summary.get("ok"))
        and all(
            venues == [expected_derivatives_venue]
            for venues in plan_venues.values()
        )
    )

    status_payload = dict(collector_status.get("payload") or {})
    collector_running = bool(status_payload.get("pid_alive")) and str(status_payload.get("status") or "") in {
        "running",
        "collecting",
    }

    timers_stdout = _cmd_stdout(dict(scheduler.get("systemd_user_timers") or {})).lower()
    system_timers_stdout = _cmd_stdout(dict(scheduler.get("systemd_system_timers") or {})).lower()
    crontab_stdout = _cmd_stdout(dict(scheduler.get("crontab") or {})).lower()
    cadence_timer_active = _cmd_stdout(dict(scheduler.get("systemd_edge_cadence_active") or {})) == "active"
    cadence_timer_enabled = _cmd_stdout(dict(scheduler.get("systemd_edge_cadence_enabled") or {})) == "enabled"
    system_cadence_timer_active = _cmd_stdout(dict(scheduler.get("systemd_system_edge_cadence_active") or {})) == "active"
    system_cadence_timer_enabled = _cmd_stdout(dict(scheduler.get("systemd_system_edge_cadence_enabled") or {})) == "enabled"
    collector_service_active = _cmd_stdout(dict(scheduler.get("systemd_crypto_edge_collector_active") or {})) == "active"
    collector_service_enabled = _cmd_stdout(dict(scheduler.get("systemd_crypto_edge_collector_enabled") or {})) == "enabled"
    collector_schedule_present = (
        "run_crypto_edge_collector_loop.py" in timers_stdout
        or "run_crypto_edge_collector_loop.py" in system_timers_stdout
        or "run_crypto_edge_collector_loop.py" in crontab_stdout
        or "collect-live-crypto-edges-loop" in timers_stdout
        or "collect-live-crypto-edges-loop" in system_timers_stdout
        or "collect-live-crypto-edges-loop" in crontab_stdout
        or collector_service_active
        or collector_service_enabled
    )
    cadence_schedule_present = (
        cadence_timer_active
        or cadence_timer_enabled
        or system_cadence_timer_active
        or system_cadence_timer_enabled
        or "check_edge_cadence.py" in crontab_stdout
    )

    checks = [
        _check(
            "remote_checkout_branch",
            branch_ok,
            "expected_branch" if branch_ok else "unexpected_branch",
            {"branch": branch, "status_branch": status_branch, "expected_branch": expected_branch},
        ),
        _check(
            "remote_checkout_commit",
            commit_ok,
            "expected_commit" if commit_ok else "unexpected_commit",
            {"head": head, "expected_commit": expected_commit},
        ),
        _check(
            "required_tooling",
            required_files_ok,
            "present" if required_files_ok else "missing_required_files",
            {"missing": missing_with_venv},
        ),
        _check(
            "collector_plan_derivatives_source",
            plan_derivatives_ok,
            "accepted_source" if plan_derivatives_ok else "unexpected_derivatives_source",
            {
                "plan_path": plan.get("path") or DEFAULT_PLAN_PATH,
                "expected_derivatives_venue": expected_derivatives_venue,
                "venues": plan_venues,
                "missing_families": list(plan_summary.get("missing_families") or []),
                "plan_error": plan.get("error") or "",
            },
        ),
        _check(
            "collector_runtime_status",
            collector_running,
            "running" if collector_running else str(status_payload.get("reason") or status_payload.get("status") or collector_status.get("error") or "not_running"),
            {
                "attempted": bool(collector_status.get("attempted")),
                "status": status_payload.get("status"),
                "reason": status_payload.get("reason"),
                "pid": status_payload.get("pid"),
                "pid_alive": status_payload.get("pid_alive"),
            },
        ),
        _check(
            "collector_schedule",
            collector_schedule_present,
            "present" if collector_schedule_present else "missing",
            {
                "collector_service_enabled": _cmd_stdout(dict(scheduler.get("systemd_crypto_edge_collector_enabled") or {})),
                "collector_service_active": _cmd_stdout(dict(scheduler.get("systemd_crypto_edge_collector_active") or {})),
                "systemd_user_timers_preview": timers_stdout[:500],
                "systemd_system_timers_preview": system_timers_stdout[:500],
                "crontab_preview": crontab_stdout[:500],
            },
        ),
        _check(
            "cadence_checker_schedule",
            cadence_schedule_present,
            "present" if cadence_schedule_present else "missing",
            {
                "user_timer_enabled": _cmd_stdout(dict(scheduler.get("systemd_edge_cadence_enabled") or {})),
                "user_timer_active": _cmd_stdout(dict(scheduler.get("systemd_edge_cadence_active") or {})),
                "system_timer_enabled": _cmd_stdout(dict(scheduler.get("systemd_system_edge_cadence_enabled") or {})),
                "system_timer_active": _cmd_stdout(dict(scheduler.get("systemd_system_edge_cadence_active") or {})),
                "crontab_preview": crontab_stdout[:500],
            },
        ),
    ]
    blockers = [row["name"] for row in checks if not bool(row.get("ok"))]
    ok = not blockers
    return {
        "ok": ok,
        "status": "hetzner_crypto_edge_runtime_ready" if ok else "hetzner_crypto_edge_runtime_blocked",
        "action": "report_hetzner_crypto_edge_runtime_status",
        "read_only": True,
        "ssh_invoked": True,
        "collector_start_invoked": False,
        "collector_stop_invoked": False,
        "deploy_invoked": False,
        "app_dir": app_dir,
        "remote": {
            "head": head,
            "branch": branch,
            "status_branch": status_branch,
        },
        "checks": checks,
        "blockers": blockers,
        "recommendations": _recommendations(blockers),
    }


def _recommendations(blockers: list[str]) -> list[str]:
    if not blockers:
        return [
            "Run scripts/check_edge_cadence.py --json on the host and record recent OKX snapshot timestamps.",
            "Keep the collector and cadence checker schedules under host monitoring.",
        ]
    recommendations = [
        "Do not start the Hetzner crypto-edge collector until all blockers are cleared.",
    ]
    if "remote_checkout_branch" in blockers or "remote_checkout_commit" in blockers or "required_tooling" in blockers:
        recommendations.append("Perform a reviewed host sync/deploy to the accepted master boundary before collector start.")
    if "collector_plan_derivatives_source" in blockers:
        recommendations.append("Replace the remote collector plan with the accepted OKX derivatives source plan before collector start.")
    if "collector_runtime_status" in blockers or "collector_schedule" in blockers:
        recommendations.append("Install or start only a reviewed read-only crypto-edge collector schedule after checkout and plan checks pass.")
    if "cadence_checker_schedule" in blockers:
        recommendations.append("Enable the accepted read-only cadence checker timer after the checker exists on the host.")
    return recommendations


def _tailscale_non_json_reason(*, stdout: Any, stderr: Any) -> str:
    combined = f"{stdout or ''}\n{stderr or ''}".lower()
    if "failed to load preferences" in combined:
        return "tailscale_cli_preferences_unavailable"
    if "tailscale ssh requires an additional check" in combined:
        return "tailscale_ssh_auth_required"
    if "authenticate" in combined and "tailscale" in combined:
        return "tailscale_ssh_auth_required"
    return ""


def fetch_remote_runtime_status(
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    app_dir: str = DEFAULT_APP_DIR,
    plan_path: str = DEFAULT_PLAN_PATH,
    expected_branch: str = DEFAULT_EXPECTED_BRANCH,
    expected_commit: str = "",
    expected_derivatives_venue: str = DEFAULT_EXPECTED_DERIVATIVES_VENUE,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> dict[str, Any]:
    remote_command = _remote_status_command(app_dir=app_dir, plan_path=plan_path)
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
        remote_payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        non_json_reason = _tailscale_non_json_reason(stdout=result.stdout, stderr=result.stderr)
        if non_json_reason:
            return _failure_payload(non_json_reason, stdout=result.stdout, stderr=result.stderr)
        return _failure_payload(
            f"remote_status_parse_failed:{type(exc).__name__}:{exc}",
            stdout=result.stdout,
            stderr=result.stderr,
        )
    if not isinstance(remote_payload, dict):
        return _failure_payload("remote_status_parse_failed:not_object", stdout=result.stdout, stderr=result.stderr)

    return build_report(
        remote_payload=remote_payload,
        expected_branch=expected_branch,
        expected_commit=expected_commit,
        expected_derivatives_venue=expected_derivatives_venue,
        app_dir=app_dir,
    )


def _print_summary(payload: dict[str, Any]) -> None:
    print("=== Hetzner Crypto-Edge Runtime Status ===")
    print(f"status={payload.get('status')}")
    print(f"ok={bool(payload.get('ok'))}")
    print(f"read_only={bool(payload.get('read_only'))}")
    remote = dict(payload.get("remote") or {})
    if remote:
        print(f"remote_head={remote.get('head')}")
        print(f"remote_branch={remote.get('branch')}")
    if payload.get("reason"):
        print(f"reason={payload.get('reason')}")
    blockers = list(payload.get("blockers") or [])
    print(f"blocking_checks={len(blockers)}")
    for row in list(payload.get("checks") or []):
        if not isinstance(row, dict) or bool(row.get("ok")):
            continue
        print(f"- failed {row.get('name')}: {row.get('status')}")
    if blockers and not list(payload.get("checks") or []):
        for blocker in blockers:
            print(f"- failed {blocker}")
    recommendations = list(payload.get("recommendations") or [])
    if recommendations:
        print("recommendations:")
        for item in recommendations:
            print(f"- {item}")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Hetzner crypto-edge runtime readiness/status check over Tailscale SSH."
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when blockers exist")
    parser.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET, help="Tailscale SSH target")
    parser.add_argument("--app-dir", default=DEFAULT_APP_DIR, help="Remote repo directory")
    parser.add_argument("--plan-path", default=DEFAULT_PLAN_PATH, help="Remote crypto-edge collector plan path")
    parser.add_argument("--expected-branch", default=DEFAULT_EXPECTED_BRANCH, help="Expected remote Git branch")
    parser.add_argument("--expected-commit", default="", help="Optional accepted commit SHA/prefix required on the remote")
    parser.add_argument(
        "--expected-derivatives-venue",
        default=DEFAULT_EXPECTED_DERIVATIVES_VENUE,
        help="Expected venue for funding/open-interest/basis plan families",
    )
    parser.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC, help="Maximum seconds to wait")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = fetch_remote_runtime_status(
        ssh_target=str(args.ssh_target),
        app_dir=str(args.app_dir),
        plan_path=str(args.plan_path),
        expected_branch=str(args.expected_branch),
        expected_commit=str(args.expected_commit),
        expected_derivatives_venue=str(args.expected_derivatives_venue),
        timeout_sec=max(float(args.timeout_sec), 1.0),
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        _print_summary(payload)
    if args.strict and not bool(payload.get("ok")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
