"""One pinned ED-002 pilot slot; stdlib-only, offline unless --execute is given."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
MINUTE, HOUR, DAY = 60000, 3600000, 86400000
WAIT_SECONDS, CLEANUP_SECONDS = 140, 5
CLEAN_ENV = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
             "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
INPUTS = (
    "scripts/research/run_ed002_collection_slot.py",
    "scripts/research/capture_descriptive_inputs.py",
    "services/backtest/descriptive_candles.py", "services/backtest/descriptive_metadata.py",
    "services/backtest/shared_cash_research.py", "scripts/research/corrected_research_math.py",
    "services/__init__.py", "scripts/__init__.py", "config/candidate_universe.yaml")
ABSENT_PACKAGES = ("services/backtest/__init__.py", "scripts/research/__init__.py")
LABEL = "com.cryptkeep.ed002.public-inputs"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate_json_key")
        out[k] = v
    return out


def _bad_constant(_):
    raise ValueError("nonfinite_json")


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > 128*1024:
        raise ValueError("oversize_control_file")
    return json.loads(raw, object_pairs_hook=_unique, parse_constant=_bad_constant)


def _inside(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("relative_repo_path_required")
    path = root/relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("repo_path_escape")
    current = root
    for part in Path(relative).parts:
        current = current/part
        if current.is_symlink():
            raise ValueError("symlinked_pilot_input_or_output")
    return path


def _policy_path(path, root=ROOT):
    path = Path(path)
    if not path.is_absolute():
        path = root/path
    relative = path.relative_to(root)
    path = _inside(root,str(relative))
    if not path.is_relative_to(root/"research/ed002_public_inputs/plans"):
        raise ValueError("public_pilot_policy_path_required")
    return path


def validate_policy(policy, root=ROOT):
    expected = {"schema", "enabled", "pilot_id", "start_ms", "end_ms", "max_slots",
                "max_lateness_ms", "capture_plan", "inputs_sha256"}
    if (not isinstance(policy, dict) or set(policy) != expected
            or policy["schema"] != "ed002-local-pilot-v1" or type(policy["enabled"]) is not bool
            or not isinstance(policy["pilot_id"], str)
            or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", policy["pilot_id"]) is None
            or type(policy["max_slots"]) is not int or policy["max_slots"] != 48
            or type(policy["max_lateness_ms"]) is not int or policy["max_lateness_ms"] != 120000):
        raise ValueError("fixed_pilot_policy_required")
    start, end = policy["start_ms"], policy["end_ms"]
    if not (not policy["enabled"] and start is None and end is None):
        if (type(start) is not int or type(end) is not int or start < 0
                or not 0 < end-start <= DAY):
            raise ValueError("bounded_pilot_dates_required")
    plan_name = policy["capture_plan"]
    plan_path = _inside(root, plan_name)
    if not plan_path.is_relative_to(root/"research/ed002_public_inputs/plans"):
        raise ValueError("public_plan_path_required")
    pins = policy["inputs_sha256"]
    if not isinstance(pins, dict) or set(pins) != set(INPUTS) | {plan_name}:
        raise ValueError("exact_pilot_source_pins_required")
    for name, expected_hash in pins.items():
        if (not isinstance(expected_hash, str) or len(expected_hash) != 64
                or digest(_inside(root, name).read_bytes()) != expected_hash):
            raise ValueError("pilot_source_drift")
    if any((root/name).exists() for name in ABSENT_PACKAGES):
        raise ValueError("namespace_package_changed")
    plan = read_json(plan_path)
    if (set(plan) != {"schema", "universe_sha256", "identities", "lookback_completed_hours"}
            or plan["schema"] != "ed002-public-capture-plan-v1"
            or type(plan["lookback_completed_hours"]) is not int or plan["lookback_completed_hours"] != 2
            or plan["universe_sha256"] != pins["config/candidate_universe.yaml"]
            or not isinstance(plan["identities"], dict) or len(plan["identities"]) != 25):
        raise ValueError("two_completed_hour_plan_required")
    return plan_path


def slot_at(now):
    if type(now) is not int or now < HOUR:
        raise ValueError("valid_wall_clock_required")
    hour = now//HOUR*HOUR
    return (hour+35*MINUTE if now-hour >= 35*MINUTE else
            hour+5*MINUTE if now-hour >= 5*MINUTE else hour-HOUR+35*MINUTE)


def slots(policy):
    if policy["start_ms"] is None:
        return []
    start, end = policy["start_ms"], policy["end_ms"]
    return [h+m*MINUTE for h in range(start//HOUR*HOUR, end, HOUR)
            for m in (5,35) if start <= h+m*MINUTE < end]


def _write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(value, handle, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def _cleanup(process, *, group_exists, kill_group):
    try:
        if group_exists(process.pid):
            kill_group(process.pid, signal.SIGKILL)
        process.wait(timeout=CLEANUP_SECONDS)
        return group_exists(process.pid)
    except ProcessLookupError:
        return False
    except (OSError, subprocess.TimeoutExpired):
        return True


def _record_phase(directory, name, result):
    try:
        _write(directory/name, result)
    except FileExistsError:
        pass  # Never replace a prior refusal or attempt receipt.
    return result


def _capture_summary(output, returncode):
    try:
        manifest = read_json(output/"manifest.json")
        calls, size = manifest.get("transport_calls_started"), manifest.get("stored_payload_bytes")
        if (returncode != 0 or manifest.get("status") != "COMPLETE"
                or manifest.get("owned_worker_cleanup_failed") is not False
                or manifest.get("scoring_authorized") is not False
                or type(calls) is not int or not 2 <= calls <= 27
                or type(size) is not int or not 0 <= size <= 16*1024*1024):
            raise ValueError("incomplete_capture")
        return {"status": "COMPLETE", "reason": "capture_completed",
                "transport_calls_started": calls, "stored_payload_bytes": size,
                "manifest_sha256": digest((output/"manifest.json").read_bytes())}
    except (OSError, ValueError, TypeError, AttributeError):
        return {"status": "INCOMPLETE", "reason": "capture_failed_or_unreadable"}


def run_slot(policy, *, root=ROOT, execute=False, wall_ms=lambda: time.time_ns()//1_000_000,
             popen=subprocess.Popen, group_exists=_group_exists, kill_group=os.killpg,
             disk_free=lambda path: shutil.disk_usage(path).free):
    root = Path(root).resolve()
    plan_path = validate_policy(policy, root)
    scheduled = slots(policy)
    if len(scheduled) > 48:
        raise ValueError("pilot_slot_cap_exceeded")
    if not execute:
        return {"dry_run": True, "enabled": policy["enabled"], "max_slots": 48,
                "scheduled_slots": len(scheduled), "max_public_gets": 1296,
                "collection_started": False}
    if not policy["enabled"]:
        return {"status": "INCOMPLETE", "reason": "pilot_disabled", "collection_started": False}
    directory = _inside(root, "research/ed002_public_inputs/pilots/"+policy["pilot_id"])
    directory.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(directory/".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        now = wall_ms()
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return _record_phase(directory, "busy_"+str(slot_at(now))+".json",
                {"status": "INCOMPLETE", "reason": "pilot_busy", "collection_started": False})
        if now < policy["start_ms"] or now >= policy["end_ms"]:
            reason = "pilot_not_started" if now < policy["start_ms"] else "pilot_expired"
            return _record_phase(directory, reason+".json",
                {"status": "INCOMPLETE", "reason": reason, "checked_at_ms": now, "collection_started": False})
        slot = slot_at(now)
        if slot not in scheduled or now-slot > policy["max_lateness_ms"]:
            return _record_phase(directory, "skipped_"+str(slot)+".json",
                {"status": "INCOMPLETE", "reason": "off_schedule_or_late", "slot_ms": slot,
                 "checked_at_ms": now, "collection_started": False})
        for previous in directory.glob("slot_*"):
            try:
                if previous.is_symlink():
                    raise ValueError("symlinked_prior_slot")
                result = read_json(previous/"RESULT.json")
                if result.get("owned_group_cleanup_failed") is not False:
                    raise ValueError("unknown_cleanup")
            except (OSError, ValueError, AttributeError):
                return _record_phase(directory, "hold_"+str(slot)+".json",
                    {"status": "INCOMPLETE", "reason": "prior_slot_unsettled", "collection_started": False})
        attempt = directory/("slot_"+str(slot))
        try:
            attempt.mkdir()
        except FileExistsError:
            return {"status": "INCOMPLETE", "reason": "slot_already_claimed", "collection_started": False}
        _write(attempt/"CLAIM.json", {"slot_ms": slot, "claimed_at_ms": now,
                                     "phase": "CLAIMED_NOT_DELIVERY_PROOF"})
        result = {"status": "INCOMPLETE", "reason": "controller_failure", "slot_ms": slot,
                  "collection_started": False, "owned_group_cleanup_failed": False}
        process = None
        try:
            # Recheck drift and dispatch bounds after filesystem/pin work, before spawning.
            validate_policy(policy, root)
            now = wall_ms()
            if now-slot > policy["max_lateness_ms"] or now < slot or now < policy["start_ms"]:
                result["reason"] = "dispatch_window_lost"
            elif policy["end_ms"]-now < (WAIT_SECONDS+CLEANUP_SECONDS)*1000:
                result["reason"] = "insufficient_time_before_expiry"
            elif disk_free(directory) < 24*1024*1024:
                result["reason"] = "insufficient_disk_headroom"
            else:
                command = [str(root/".venv/bin/python"), "-I", "-B",
                    str(root/"scripts/research/capture_descriptive_inputs.py"),
                    "--plan", str(plan_path), "--output", str(attempt/"capture"), "--execute"]
                process = popen(command, cwd=str(root), env=dict(CLEAN_ENV), start_new_session=True,
                    close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result["collection_started"] = True
                _write(attempt/"CHILD.json", {"owned_session_leader_pid": process.pid,
                    "phase": "SPAWNED_NOT_DELIVERY_PROOF"})
                remaining = (policy["end_ms"]-wall_ms())/1000-CLEANUP_SECONDS
                code = process.wait(timeout=max(0,min(WAIT_SECONDS,remaining)))
                result.update(_capture_summary(attempt/"capture",code))
        except subprocess.TimeoutExpired:
            result["reason"] = "owned_controller_timeout"
        except KeyboardInterrupt:
            result["reason"] = "operator_interrupt"
        except Exception:
            result["reason"] = "controller_failure"
        finally:
            if process is not None:
                result["owned_group_cleanup_failed"] = _cleanup(process, group_exists=group_exists, kill_group=kill_group)
                if result["owned_group_cleanup_failed"]:
                    result.update(status="INCOMPLETE",reason="owned_group_cleanup_failed")
            result["finished_at_ms"] = wall_ms()
            _write(attempt/"RESULT.json",result)
        return result
    finally:
        os.close(lock_fd)  # Persistent lock inode is deliberately not unlinked.


def job_template(policy_path, policy_sha256, *, root=ROOT):
    """Return an artifact only; never writes or loads a LaunchAgent."""
    policy_path = _policy_path(policy_path,root)
    policy = read_json(policy_path)
    validate_policy(policy,root)
    if digest(Path(policy_path).read_bytes()) != policy_sha256:
        raise ValueError("policy_hash_mismatch")
    directory = root/"research/ed002_public_inputs/pilots"/policy["pilot_id"]
    return {"Label":LABEL, "ProgramArguments":[str(root/".venv/bin/python"),"-I","-S","-B",
        str(root/"scripts/research/run_ed002_collection_slot.py"),"--policy",str(Path(policy_path).resolve()),
        "--policy-sha256",policy_sha256,"--execute"],
        "WorkingDirectory":str(root),"EnvironmentVariables":dict(CLEAN_ENV),
        "StartCalendarInterval":[{"Minute":5},{"Minute":35}],"RunAtLoad":False,"KeepAlive":False,
        "StandardInPath":"/dev/null", "StandardOutPath":str(directory/"scheduler.stdout.log"),
        "StandardErrorPath":str(directory/"scheduler.stderr.log")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy",type=Path,required=True)
    parser.add_argument("--policy-sha256",required=True)
    parser.add_argument("--execute",action="store_true")
    args = parser.parse_args(argv)
    old = signal.getsignal(signal.SIGTERM)
    def cancel(*_):
        raise KeyboardInterrupt
    try:
        signal.signal(signal.SIGTERM,cancel)
        path = _policy_path(args.policy)
        if digest(path.read_bytes()) != args.policy_sha256:
            raise ValueError("policy_hash_mismatch")
        result = run_slot(read_json(path),execute=args.execute)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
        return 0 if result.get("dry_run") or result.get("status")=="COMPLETE" else 2
    except (Exception,KeyboardInterrupt):
        print('{"status":"INCOMPLETE","reason":"pilot_preflight_or_receipt_failure"}')
        return 2
    finally:
        signal.signal(signal.SIGTERM,old)


if __name__ == "__main__":
    sys.exit(main())
