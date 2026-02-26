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
import sys
import argparse
import json
import os
import time
from datetime import datetime, timezone

SCHEMA_VERSION = 1


def _run(cmd: list[str], fail_label: str) -> int:
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"[validate] FAIL: {fail_label}")
    return rc


def _trim(s: str, limit: int = 20000) -> str:
    return (s or "")[:limit]


def _run_capture(cmd: list[str], label: str) -> dict:
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    return {
        "label": label,
        "cmd": cmd,
        "rc": p.returncode,
        "stdout": _trim(p.stdout or ""),
        "stderr": _trim(p.stderr or ""),
    }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_flag(name: str) -> bool:
    v = (os.environ.get(name, "") or "").strip().lower()
    return v in {"1", "true", "yes", "on"}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="Run guard/smoke subset instead of full pytest")
    ap.add_argument("--json", action="store_true", help="Emit structured JSON result")
    args = ap.parse_args()

    if args.json:
        mode = "quick" if args.quick else "full"
        started_at = _utc_now_iso()
        t0 = time.monotonic()
        steps: list[dict] = []
        step = _run_capture([sys.executable, "scripts/check_repo_alignment.py"], "check_repo_alignment")
        steps.append(step)
        if step["rc"] != 0:
            finished_at = _utc_now_iso()
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "ok": False,
                        "mode": mode,
                        "quick": bool(args.quick),
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "steps": steps,
                    },
                    indent=2,
                )
            )
            return step["rc"]

        if args.quick:
            tests = [
                "tests/test_repo_doctor_strict.py",
                "tests/test_bootstrap_helper_adoption.py",
                "tests/test_no_duplicate_script_bootstrap.py",
                "tests/test_no_legacy_state_paths.py",
            ]
            step = _run_capture([sys.executable, "-m", "pytest", "-q", *tests], "pytest_quick")
            steps.append(step)
            ok = step["rc"] == 0
            finished_at = _utc_now_iso()
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "ok": ok,
                        "mode": mode,
                        "quick": True,
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "steps": steps,
                    },
                    indent=2,
                )
            )
            return 0 if ok else step["rc"]

        step = _run_capture([sys.executable, "scripts/preflight_check.py"], "preflight_check")
        steps.append(step)
        if step["rc"] != 0:
            finished_at = _utc_now_iso()
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "ok": False,
                        "mode": mode,
                        "quick": False,
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "steps": steps,
                    },
                    indent=2,
                )
            )
            return step["rc"]

        if _env_flag("CBP_VALIDATE_SKIP_PYTEST"):
            steps.append(
                {
                    "label": "pytest",
                    "rc": 0,
                    "skipped": True,
                    "stdout": "skipped via CBP_VALIDATE_SKIP_PYTEST",
                    "stderr": "",
                }
            )
            finished_at = _utc_now_iso()
            print(
                json.dumps(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "ok": True,
                        "mode": mode,
                        "quick": False,
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "duration_seconds": round(time.monotonic() - t0, 3),
                        "steps": steps,
                    },
                    indent=2,
                )
            )
            return 0

        step = _run_capture([sys.executable, "-m", "pytest"], "pytest")
        steps.append(step)
        ok = step["rc"] == 0
        finished_at = _utc_now_iso()
        print(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "ok": ok,
                    "mode": mode,
                    "quick": False,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "duration_seconds": round(time.monotonic() - t0, 3),
                    "steps": steps,
                },
                indent=2,
            )
        )
        return 0 if ok else step["rc"]

    print("[validate] running check_repo_alignment...")
    r0 = _run([sys.executable, "scripts/check_repo_alignment.py"], "check_repo_alignment")
    if r0 != 0:
        return r0

    if args.quick:
        print("[validate] running quick pytest subset...")
        tests = [
            "tests/test_repo_doctor_strict.py",
            "tests/test_bootstrap_helper_adoption.py",
            "tests/test_no_duplicate_script_bootstrap.py",
            "tests/test_no_legacy_state_paths.py",
        ]
        r2 = _run([sys.executable, "-m", "pytest", "-q", *tests], "pytest (quick)")
    else:
        print("[validate] running preflight_check...")
        r1 = _run([sys.executable, "scripts/preflight_check.py"], "preflight_check")
        if r1 != 0:
            return r1
        print("[validate] running pytest...")
        r2 = _run([sys.executable, "-m", "pytest"], "pytest")
    if r2 != 0:
        return r2

    print("[validate] OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
