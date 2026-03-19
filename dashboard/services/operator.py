from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SERVICES = ("tick_publisher", "intent_reconciler", "intent_executor")


def run_op(args: Sequence[str]) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "op.py"), *list(args)]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), output.strip()


def run_repo_script(script_relpath: str, *, args: Sequence[str] | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / script_relpath)]
    if args:
        cmd.extend(str(x) for x in args)
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), output.strip()


def start_repo_script_background(script_relpath: str, *, args: Sequence[str] | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(REPO_ROOT / script_relpath)]
    if args:
        cmd.extend(str(x) for x in args)

    kwargs: dict[str, object] = {
        "cwd": str(REPO_ROOT),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(cmd, **kwargs)
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    return 0, f"started pid={int(proc.pid)} script={script_relpath}"


def start_crypto_edge_collector_loop(
    *,
    interval_sec: float,
    plan_file: str = "sample_data/crypto_edges/live_collector_plan.json",
) -> tuple[int, str]:
    try:
        from services.analytics.crypto_edge_collector_service import load_runtime_status
    except Exception:
        load_runtime_status = None

    runtime = load_runtime_status() if callable(load_runtime_status) else {}
    if bool(runtime.get("pid_alive")):
        pid = int(runtime.get("pid") or 0)
        status = str(runtime.get("status") or "running")
        return 0, f"already running pid={pid} status={status}"

    return start_repo_script_background(
        "scripts/run_crypto_edge_collector_loop.py",
        args=[
            "--plan-file",
            str(plan_file),
            "--interval-sec",
            str(int(interval_sec)),
        ],
    )


def stop_crypto_edge_collector_loop() -> tuple[int, str]:
    return run_repo_script("scripts/run_crypto_edge_collector_loop.py", args=["--stop"])


def list_services(*, fallback: Sequence[str] | None = None) -> list[str]:
    rc, out = run_op(["list"])
    if rc == 0:
        parsed = [line.strip() for line in out.splitlines() if line.strip()]
        if parsed:
            return parsed
    return list(fallback or DEFAULT_SERVICES)


def get_operations_snapshot() -> dict[str, object]:
    services = list_services()

    try:
        from services.admin.health import list_health
    except Exception:
        list_health = None

    raw_health = []
    if callable(list_health):
        try:
            raw_health = list_health()
        except Exception:
            raw_health = []

    health_rows = [item for item in raw_health if isinstance(item, dict)]
    latest_by_service: dict[str, dict[str, object]] = {}
    for item in health_rows:
        service = str(item.get("service") or "").strip()
        if not service:
            continue
        current_ts = str(item.get("ts") or "")
        previous = latest_by_service.get(service)
        previous_ts = str(previous.get("ts") or "") if isinstance(previous, dict) else ""
        if current_ts >= previous_ts:
            latest_by_service[service] = item

    running_statuses = {"RUNNING", "OK", "HEALTHY", "STARTING"}
    attention_statuses = {"ERROR", "FAILED", "UNHEALTHY", "DEGRADED", "STOPPED"}

    tracked_names = list(dict.fromkeys([*services, *latest_by_service.keys()]))
    healthy_count = 0
    attention_count = 0
    unknown_count = 0
    last_health_ts = ""

    for service in tracked_names:
        row = latest_by_service.get(service)
        if not isinstance(row, dict):
            unknown_count += 1
            continue
        status = str(row.get("status") or "").strip().upper()
        ts = str(row.get("ts") or "").strip()
        if ts and ts > last_health_ts:
            last_health_ts = ts
        if status in running_statuses:
            healthy_count += 1
        elif status in attention_statuses:
            attention_count += 1
        else:
            unknown_count += 1

    return {
        "services": tracked_names,
        "tracked_services": len(tracked_names),
        "healthy_services": healthy_count,
        "attention_services": attention_count,
        "unknown_services": unknown_count,
        "last_health_ts": last_health_ts,
    }
