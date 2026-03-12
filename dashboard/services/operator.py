from __future__ import annotations

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


def list_services(*, fallback: Sequence[str] | None = None) -> list[str]:
    rc, out = run_op(["list"])
    if rc == 0:
        parsed = [line.strip() for line in out.splitlines() if line.strip()]
        if parsed:
            return parsed
    return list(fallback or DEFAULT_SERVICES)
