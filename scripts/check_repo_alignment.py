from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import subprocess
import argparse
import json
import os
import time
from datetime import datetime, timezone


GUARD_TESTS = [
    "tests/test_repo_doctor_strict.py",
    "tests/test_bootstrap_helper_adoption.py",
    "tests/test_no_duplicate_script_bootstrap.py",
    "tests/test_no_legacy_state_paths.py",
    "tests/test_validation_wiring.py",
    "tests/test_makefile_wiring.py",
    "tests/test_readme_alignment_wiring.py",
    "tests/test_repo_alignment_workflow_doc.py",
    "tests/test_pre_release_sanity_doc_wiring.py",
    "tests/test_check_repo_alignment_contract.py",
]
SCHEMA_VERSION = 1


def _run(cmd: list[str], label: str) -> int:
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        print(f"[alignment] FAIL: {label}")
    return rc

def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-tests", action="store_true", help="print guard test paths and exit")
    ap.add_argument("--json", action="store_true", help="emit structured JSON status")
    args = ap.parse_args()

    if args.list_tests:
        if args.json:
            started_at = _utc_now_iso()
            t0 = time.monotonic()
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "mode": "list-tests",
                        "ok": True,
                        "started_at": started_at,
                        "finished_at": _utc_now_iso(),
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "guard_tests": GUARD_TESTS,
                    },
                    indent=2,
                )
            )
            return 0
        for t in GUARD_TESTS:
            print(t)
        return 0

    if args.json:
        started_at = _utc_now_iso()
        t0 = time.monotonic()
        skip_guards = (os.environ.get("CBP_ALIGNMENT_SKIP_GUARDS", "").strip().lower() in {"1", "true", "yes", "on"})
        mode = "full_skip_guards" if skip_guards else "full"
        doctor_cmd = [sys.executable, "tools/repo_doctor.py", "--strict"]
        d_rc, d_out, d_err = _run_capture(doctor_cmd)
        if skip_guards:
            t_rc, t_out, t_err = 0, "", ""
        else:
            tests_cmd = [sys.executable, "-m", "pytest", "-q", *GUARD_TESTS]
            t_rc, t_out, t_err = _run_capture(tests_cmd)
        ok = (d_rc == 0 and t_rc == 0)
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "mode": mode,
                    "ok": ok,
                    "started_at": started_at,
                    "finished_at": _utc_now_iso(),
                    "duration_seconds": round(time.monotonic() - t0, 3),
                    "repo_doctor": {"rc": d_rc, "stdout": d_out.strip(), "stderr": d_err.strip()},
                    "guard_tests": {
                        "rc": t_rc,
                        "count": len(GUARD_TESTS),
                        "skipped": skip_guards,
                        "stdout": t_out.strip(),
                        "stderr": t_err.strip(),
                    },
                    "tests": GUARD_TESTS,
                },
                indent=2,
            )
        )
        return 0 if ok else 1

    print("[alignment] running repo_doctor --strict...")
    rc = _run([sys.executable, "tools/repo_doctor.py", "--strict"], "repo_doctor --strict")
    if rc != 0:
        return rc

    print("[alignment] running alignment guard tests...")
    rc = _run([sys.executable, "-m", "pytest", "-q", *GUARD_TESTS], "alignment guard tests")
    if rc != 0:
        return rc

    print("[alignment] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
