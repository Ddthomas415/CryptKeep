#!/usr/bin/env python3
from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from typing import Any, Callable  # noqa: E402

from services.analytics.paper_campaign_recovery import load_campaign_specs  # noqa: E402

DEFAULT_CONFIG_PATH = ROOT / "configs" / "paper_evidence_campaigns.hetzner.example.json"
DEFAULT_EXPECTED_CAMPAIGN = "ema_cross_default"
DEFAULT_BACKUP_DIR = ROOT.parent / "backups"
DEFAULT_MIN_FREE_GB = 2.0
DEFAULT_MIN_FREE_INODES = 10_000

RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def _check(name: str, ok: bool, status: str, **details: Any) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "status": status,
        "details": details,
    }


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 5.0,
    run_command: RunCommand = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        command,
        cwd=str(cwd) if cwd is not None else None,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def check_required_files(repo_root: Path = ROOT) -> dict[str, Any]:
    required = [
        "scripts/run_paper_strategy_evidence_collector.py",
        "scripts/restore_paper_campaigns.py",
        "scripts/paper_state_manifest.py",
        "configs/paper_evidence_campaigns.hetzner.example.json",
    ]
    missing = [rel for rel in required if not (repo_root / rel).is_file()]
    return _check(
        "required_files",
        not missing,
        "present" if not missing else "missing_required_files",
        missing=missing,
    )


def check_python_venv(
    *,
    repo_root: Path = ROOT,
    executable: str = sys.executable,
    prefix: str = sys.prefix,
) -> dict[str, Any]:
    exe = Path(executable)
    active_prefix = Path(prefix).resolve()
    venv = (repo_root / ".venv").resolve()
    ok = active_prefix == venv
    return _check(
        "python_venv",
        ok,
        "repo_venv" if ok else "not_repo_venv",
        executable=str(exe),
        sys_prefix=str(active_prefix),
        expected_prefix=str(venv),
    )


def check_collector_imports(
    *,
    repo_root: Path = ROOT,
    executable: str = sys.executable,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    code = (
        "import importlib\n"
        "importlib.import_module('services.analytics.paper_strategy_evidence_service')\n"
        "print('collector_import_ok')\n"
    )
    try:
        completed = _run(
            [executable, "-c", code],
            cwd=repo_root,
            timeout=10.0,
            run_command=run_command,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check(
            "collector_imports",
            False,
            f"collector_import_probe_failed:{type(exc).__name__}",
            executable=executable,
        )
    ok = completed.returncode == 0
    return _check(
        "collector_imports",
        ok,
        "collector_imports_ok" if ok else "collector_imports_failed",
        executable=executable,
        returncode=completed.returncode,
        stdout=str(completed.stdout or "").strip(),
        stderr=str(completed.stderr or "").strip(),
    )


def _gb_to_bytes(value: float) -> int:
    return int(float(value) * 1024 * 1024 * 1024)


def check_storage_health(
    *,
    repo_root: Path = ROOT,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    min_free_bytes: int = _gb_to_bytes(DEFAULT_MIN_FREE_GB),
    min_free_inodes: int = DEFAULT_MIN_FREE_INODES,
    disk_usage: Callable[[Path], Any] = shutil.disk_usage,
    statvfs: Callable[[Path], Any] = os.statvfs,
) -> dict[str, Any]:
    if not repo_root.is_dir():
        return _check(
            "storage_health",
            False,
            "repo_root_missing",
            repo_root=str(repo_root),
            backup_dir=str(backup_dir),
        )

    try:
        usage = disk_usage(repo_root)
        stat = statvfs(repo_root)
    except OSError as exc:
        return _check("storage_health", False, f"storage_probe_failed:{type(exc).__name__}")

    free_bytes = int(getattr(usage, "free", 0) or 0)
    free_inodes = int(getattr(stat, "f_favail", getattr(stat, "f_ffree", 0)) or 0)
    backup_exists = backup_dir.is_dir()
    ok = (
        backup_exists
        and free_bytes >= int(min_free_bytes)
        and free_inodes >= int(min_free_inodes)
    )
    if not backup_exists:
        status = "backup_dir_missing"
    elif free_bytes < int(min_free_bytes):
        status = "free_space_low"
    elif free_inodes < int(min_free_inodes):
        status = "free_inodes_low"
    else:
        status = "ready"
    return _check(
        "storage_health",
        ok,
        status,
        repo_root=str(repo_root),
        backup_dir=str(backup_dir),
        backup_dir_exists=backup_exists,
        free_bytes=free_bytes,
        min_free_bytes=int(min_free_bytes),
        free_inodes=free_inodes,
        min_free_inodes=int(min_free_inodes),
    )


def check_git_checkout(
    *,
    repo_root: Path = ROOT,
    expected_commit: str | None = None,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    try:
        head = _run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            run_command=run_command,
        )
        status = _run(
            ["git", "status", "--short"],
            cwd=repo_root,
            run_command=run_command,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check(
            "git_checkout",
            False,
            f"git_unavailable:{type(exc).__name__}",
        )

    commit = str(head.stdout or "").strip()
    dirty = [line for line in str(status.stdout or "").splitlines() if line.strip()]
    ok = head.returncode == 0 and status.returncode == 0 and not dirty
    if expected_commit:
        ok = ok and commit.startswith(expected_commit)
    if head.returncode != 0 or status.returncode != 0:
        state = "git_command_failed"
    elif dirty:
        state = "worktree_dirty"
    elif expected_commit and not commit.startswith(expected_commit):
        state = "commit_mismatch"
    else:
        state = "clean"
    return _check(
        "git_checkout",
        ok,
        state,
        commit=commit,
        expected_commit=expected_commit,
        dirty=dirty,
    )


def check_time_sync(*, run_command: RunCommand = subprocess.run) -> dict[str, Any]:
    if shutil.which("timedatectl") is None:
        return _check("time_sync", False, "timedatectl_missing")
    try:
        completed = _run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            run_command=run_command,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check("time_sync", False, f"timedatectl_failed:{type(exc).__name__}")
    value = str(completed.stdout or "").strip().lower()
    ok = completed.returncode == 0 and value == "yes"
    return _check(
        "time_sync",
        ok,
        "ntp_synchronized" if ok else "ntp_not_synchronized",
        value=value,
        returncode=completed.returncode,
    )


def check_tailscale(*, run_command: RunCommand = subprocess.run) -> dict[str, Any]:
    if shutil.which("tailscale") is None:
        return _check("tailscale", False, "tailscale_missing")
    try:
        completed = _run(
            ["tailscale", "status", "--json"],
            run_command=run_command,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check("tailscale", False, f"tailscale_status_failed:{type(exc).__name__}")
    try:
        payload = json.loads(str(completed.stdout or "{}"))
    except json.JSONDecodeError:
        return _check("tailscale", False, "tailscale_status_invalid_json")
    self_node = payload.get("Self") if isinstance(payload, dict) else None
    ips = self_node.get("TailscaleIPs") if isinstance(self_node, dict) else []
    backend = str(payload.get("BackendState") or "") if isinstance(payload, dict) else ""
    ok = completed.returncode == 0 and backend.lower() == "running" and bool(ips)
    return _check(
        "tailscale",
        ok,
        "running" if ok else "not_running",
        backend_state=backend,
        tailscale_ips=ips if isinstance(ips, list) else [],
        returncode=completed.returncode,
    )


def check_campaign_config(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    repo_root: Path = ROOT,
    expected_campaign: str = DEFAULT_EXPECTED_CAMPAIGN,
    require_state: bool = False,
) -> dict[str, Any]:
    try:
        specs = load_campaign_specs(config_path, repo_root=repo_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _check(
            "campaign_config",
            False,
            f"invalid_config:{type(exc).__name__}",
            config=str(config_path),
        )
    rows = [
        {
            "name": spec.name,
            "strategy": spec.strategy,
            "session_strategy_id": spec.session_strategy_id,
            "state_dir": str(spec.state_dir),
            "signal_source": spec.signal_source,
            "desktop_notify": spec.desktop_notify,
            "state_exists": spec.state_dir.exists(),
        }
        for spec in specs
    ]
    names = [row["name"] for row in rows]
    missing_state = [row["state_dir"] for row in rows if not row["state_exists"]]
    ok = (
        len(rows) == 1
        and names == [expected_campaign]
        and rows[0]["desktop_notify"] is False
        and (not require_state or not missing_state)
    )
    if len(rows) != 1:
        state = "unexpected_campaign_count"
    elif names != [expected_campaign]:
        state = "unexpected_campaign"
    elif rows[0]["desktop_notify"] is not False:
        state = "desktop_notify_enabled"
    elif require_state and missing_state:
        state = "state_missing"
    else:
        state = "ready"
    return _check(
        "campaign_config",
        ok,
        state,
        config=str(config_path),
        expected_campaign=expected_campaign,
        campaigns=rows,
        missing_state=missing_state,
    )


def build_report(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_campaign: str = DEFAULT_EXPECTED_CAMPAIGN,
    expected_commit: str | None = None,
    require_state: bool = False,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    min_free_gb: float = DEFAULT_MIN_FREE_GB,
    min_free_inodes: int = DEFAULT_MIN_FREE_INODES,
    repo_root: Path = ROOT,
    run_command: RunCommand = subprocess.run,
) -> dict[str, Any]:
    checks = [
        check_required_files(repo_root),
        check_python_venv(repo_root=repo_root),
        check_collector_imports(repo_root=repo_root, run_command=run_command),
        check_storage_health(
            repo_root=repo_root,
            backup_dir=backup_dir,
            min_free_bytes=_gb_to_bytes(float(min_free_gb)),
            min_free_inodes=int(min_free_inodes),
        ),
        check_git_checkout(
            repo_root=repo_root,
            expected_commit=expected_commit,
            run_command=run_command,
        ),
        check_time_sync(run_command=run_command),
        check_tailscale(run_command=run_command),
        check_campaign_config(
            config_path=config_path,
            repo_root=repo_root,
            expected_campaign=expected_campaign,
            require_state=require_state,
        ),
    ]
    return {
        "ok": all(bool(row.get("ok")) for row in checks),
        "repo_root": str(repo_root),
        "config": str(config_path),
        "expected_campaign": expected_campaign,
        "expected_commit": expected_commit,
        "require_state": require_state,
        "backup_dir": str(backup_dir),
        "min_free_gb": float(min_free_gb),
        "min_free_inodes": int(min_free_inodes),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Read-only preflight for the Hetzner paper campaign host."
    )
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    ap.add_argument("--expected-campaign", default=DEFAULT_EXPECTED_CAMPAIGN)
    ap.add_argument(
        "--expected-commit",
        help="Require the checkout HEAD to start with this accepted commit SHA.",
    )
    ap.add_argument(
        "--require-state",
        action="store_true",
        help="Require configured state directories to exist; use after state transfer.",
    )
    ap.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Backup directory expected on the paper host.",
    )
    ap.add_argument(
        "--min-free-gb",
        type=float,
        default=DEFAULT_MIN_FREE_GB,
        help="Minimum free disk space required on the repo filesystem.",
    )
    ap.add_argument(
        "--min-free-inodes",
        type=int,
        default=DEFAULT_MIN_FREE_INODES,
        help="Minimum free inodes required on the repo filesystem.",
    )
    args = ap.parse_args(argv)

    payload = build_report(
        config_path=args.config,
        expected_campaign=args.expected_campaign,
        expected_commit=args.expected_commit,
        require_state=bool(args.require_state),
        backup_dir=args.backup_dir,
        min_free_gb=float(args.min_free_gb),
        min_free_inodes=int(args.min_free_inodes),
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if bool(payload.get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
