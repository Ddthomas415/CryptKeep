"""One foreground CLI invocation; no retry, DB rollback or recurring launch."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]


def stop_owned(proc):
    if proc.poll() is not None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue
    raise TimeoutError("owned_child_not_reaped")


def run_once(command, *, folder, cwd, env, timeout=180):
    if type(timeout) not in (int, float) or not 0 < timeout <= 180:
        raise ValueError("bounded_timeout_required")
    receipt = {"started_at": datetime.now(timezone.utc).isoformat(), "command": command,
               "timeout_seconds": timeout, "cleanup_reserve_seconds": 10,
               "attempts": 1, "ok": False, "exit_code": None}
    folder = Path(folder)
    # Consumed before launch; never reset after failure or a partial write.
    with (folder / "ATTEMPT_STARTED.json").open("x") as handle:
        json.dump(receipt, handle, indent=2)
    proc = None
    start = time.monotonic()
    try:
        with (folder / "stdout.json").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, start_new_session=True)
            receipt["owned_pid"] = proc.pid
            receipt["exit_code"] = proc.wait(timeout=timeout)
            receipt["ok"] = receipt["exit_code"] == 0
    except BaseException as exc:
        receipt["error_type"] = type(exc).__name__
        if proc is not None:
            try:
                stop_owned(proc)
            except BaseException as cleanup:
                receipt["cleanup_error_type"] = type(cleanup).__name__
        raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - start
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        receipt["persistence_may_have_occurred"] = proc is not None
        receipt["owned_child_reaped"] = proc is not None and proc.poll() is not None
        with (folder / "RUN_RECEIPT.json").open("x") as handle:
            json.dump(receipt, handle, indent=2)
    return receipt


def main():
    folder = Path(sys.argv[1]).resolve()
    if folder.parent != Path(__file__).resolve().parent:
        raise ValueError("isolated_operation_folder_required")
    command = [str(ROOT / ".venv/bin/python"), "-B",
               str(ROOT / "scripts/data/run_crypto_edge_collector_loop.py"),
               "--okx-pairs", "--plan-file", str(folder / "PLAN.json"),
               "--okx-pair-options-file", str(folder / "OPTIONS.json"),
               "--db-path", str(ROOT / ".cbp_state/data/crypto_edge_research.sqlite"),
               "--source", "live_public", "--interval-sec", "300", "--max-loops", "1",
               "--raw-funding-max-rows", "1", "--raw-funding-max-bytes", "4194304"]
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
           "CBP_STATE_DIR": str(ROOT / ".cbp_state")}
    result = run_once(command, folder=folder, cwd=str(ROOT), env=env)
    print(json.dumps({key: result.get(key) for key in ("ok", "exit_code", "owned_pid", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
