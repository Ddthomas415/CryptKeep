"""Run current source tests in a disposable, deny-network macOS sandbox."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-treatment", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    root = Path(tempfile.mkdtemp(prefix="cryptkeep-full-suite-", dir="/private/tmp"))
    snapshot = root / "source"
    snapshot.mkdir()
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo).decode().split("\0")
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=repo,
    ).decode().split("\0")
    allowed_roots = {"services", "storage", "tests", "scripts", "tools", "research", "docs"}
    allowed_suffixes = {".py", ".md", ".yaml", ".yml", ".toml", ".json"}
    selected = {name for name in tracked if name}
    selected.update(name for name in untracked if name and
                    Path(name).parts[0] in allowed_roots and Path(name).suffix in allowed_suffixes)
    inventory = []
    for name in sorted(selected):
        relative = Path(name)
        if any(part.startswith((".env", ".cbp_state")) for part in relative.parts):
            continue
        if relative.parts[0] in {"data", "runtime", "logs", ".venv", ".git"} or name == "config/user.yaml":
            continue
        source = repo / relative
        if not source.is_file() or source.is_symlink():
            continue
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        inventory.append({"path": name, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    if args.pre_treatment:
        for name in (
            "storage/execution_store_sqlite.py", "services/journal/fill_sink.py",
            "services/execution/_executor_reconcile.py", "tests/test_fill_sink_logging.py",
            "tests/test_live_executor_shadow_and_trade_reconcile.py",
            "tests/test_live_executor_latency_safety_integration.py",
        ):
            content = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=repo)
            (snapshot / name).write_bytes(content)
        for name in ("tests/test_reconcile_accounting_delivery.py", "tests/test_symbol_loss_fill_once.py"):
            (snapshot / name).unlink(missing_ok=True)
    inventory = [{"path": row["path"], "sha256": hashlib.sha256(
        (snapshot / row["path"]).read_bytes()).hexdigest()} for row in inventory
        if (snapshot / row["path"]).is_file()]
    (root / "inventory.json").write_text(json.dumps(inventory, indent=2))
    # Only disposable metadata: no remote, credentials or original Git history.
    subprocess.run(["git", "init", "-q", str(snapshot)], check=True)
    git_env = {"PATH": "/usr/bin:/bin", "HOME": str(root),
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "add", "-A"], cwd=snapshot, env=git_env, check=True)
    subprocess.run(["git", "-c", "user.name=Isolated Test Snapshot", "-c",
                    "user.email=snapshot@invalid", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m",
                    "Disposable test snapshot, not a production commit"],
                   cwd=snapshot, env=git_env, check=True)
    (snapshot / ".venv").symlink_to(repo / ".venv", target_is_directory=True)
    home = root / "home"
    home.mkdir()
    (root / "state/data").mkdir(parents=True)
    profile = root / "test.sb"
    profile.write_text(
        "(version 1) (allow default) (deny network*)\n"
        f'(deny file-write* (subpath "{Path.home()}"))\n'
        f'(deny file-read-data (require-all (subpath "{Path.home()}") '
        f'(require-not (subpath "{repo / ".venv"}"))))\n'
    )
    env = {
        "PATH": f"{repo / '.venv/bin'}:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home), "TMPDIR": str(root), "PYTHONPATH": str(snapshot),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
        "CBP_STATE_DIR": str(root / "state"), "EXEC_DB_PATH": str(root / "execution.sqlite"),
        "CBP_DB_PATH": str(root / "cbp.sqlite"), "PYTHONUNBUFFERED": "1",
    }
    command = ["/usr/bin/sandbox-exec", "-f", str(profile), str(repo / ".venv/bin/python"),
               "-B", "-m", "pytest", "tests", "-q", f"--basetemp={root / 'pytest-temp'}",
               f"--junitxml={root / 'results.xml'}"]
    started = time.time()
    print(f"ISOLATED_SUITE_ROOT={root}", flush=True)
    print(f"SNAPSHOT_FILES={len(inventory)}", flush=True)
    timed_out = False
    with (root / "pytest.log").open("w") as output:
        process = subprocess.Popen(command, cwd=snapshot, env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            exit_code = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
    summary = {"exit_code": exit_code, "timed_out": timed_out,
               "elapsed_seconds": round(time.time() - started, 2), "root": str(root),
               "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip(),
               "files": len(inventory), "slow_tests_skipped_by_runner": False,
               "pre_treatment": args.pre_treatment,
               "network": "denied", "operator_home": "denied_except_readonly_venv"}
    (root / "run_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
