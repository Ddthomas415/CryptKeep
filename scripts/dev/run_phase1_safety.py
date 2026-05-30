from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

PHASE1_TESTS = (
    "tests/test_place_order_fail_closed.py",
    "tests/test_place_order_ops_risk_gate.py",
    "tests/test_live_mode_contracts.py",
    "tests/test_no_direct_create_order.py",
    "tests/test_verify_no_direct_create_order_script.py",
    "tests/test_live_script_contracts.py",
)


def build_steps(python_exe: str | None = None) -> list[tuple[str, list[str]]]:
    py = python_exe or _default_python_executable()
    return [
        (
            "verify_no_direct_create_order",
            [py, "scripts/verify_no_direct_create_order.py", "--root", "."],
        ),
        (
            "phase1_pytest",
            [py, "-m", "pytest", "-q", *PHASE1_TESTS],
        ),
    ]


def _run_step(label: str, cmd: list[str]) -> int:
    print(f"[phase1-safety] {label}: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
    return int(proc.returncode)


def _default_python_executable() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def main() -> int:
    for label, cmd in build_steps():
        rc = _run_step(label, cmd)
        if rc != 0:
            print(f"[phase1-safety] FAILED: {label} rc={rc}")
            return int(rc)
    print("[phase1-safety] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
