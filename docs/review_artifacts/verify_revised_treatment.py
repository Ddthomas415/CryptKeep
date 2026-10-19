"""Freeze and test the independently reviewed treatment candidate in isolation."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


def main():
    repo = Path(__file__).resolve().parents[2]
    prior = repo / "docs/review_artifacts/treatment_candidate_20261007/manifest.json"
    manifest = json.loads(prior.read_text())
    reviewed = Path("/private/tmp/cryptkeep-order-treatment-20261007/source")
    root = Path(tempfile.mkdtemp(prefix="cryptkeep-revised-suite-", dir="/private/tmp"))
    source = root / "source"
    # This is the base-only candidate, not the unrelated working checkout.
    shutil.copytree(reviewed, source, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    rows = []
    for row in manifest["files"]:
        name = row["path"]
        digest = hashlib.sha256((source / name).read_bytes()).hexdigest()
        if digest != hashlib.sha256((repo / name).read_bytes()).hexdigest():
            raise ValueError(f"Current source differs from reviewed candidate: {name}")
        rows.append({"path": name, "sha256": digest})
    paths = [row["path"] for row in rows]
    git_env = {"PATH": "/usr/bin:/bin", "HOME": str(root),
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=source, env=git_env).decode().splitlines()
    if set(changed) != set(paths):
        raise ValueError(f"Unexpected candidate delta: {changed}")
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=source, env=git_env)
    subprocess.run(["git", "diff", "--check"], cwd=source, env=git_env, check=True)
    subprocess.run(["git", "apply", "--cached", "--check", "-"], input=patch, cwd=source, env=git_env, check=True)
    output = repo / "docs/review_artifacts/treatment_candidate_revised_20261007"
    output.mkdir(exist_ok=True)
    (output / "treatment.patch").write_bytes(patch)
    manifest.update(candidate_root=str(root), files=rows,
                    patch_sha256=hashlib.sha256(patch).hexdigest(),
                    full_suite="running; see run_summary.json")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (source / ".venv").symlink_to(repo / ".venv", target_is_directory=True)
    home = root / "home"
    home.mkdir()
    profile = root / "test.sb"
    profile.write_text(
        "(version 1) (allow default) (deny network*)\n"
        f'(deny file-write* (subpath "{Path.home()}"))\n'
        f'(deny file-read-data (require-all (subpath "{Path.home()}") '
        f'(require-not (subpath "{repo / ".venv"}"))))\n')
    env = {"PATH": f"{repo / '.venv/bin'}:/usr/bin:/bin:/usr/sbin:/sbin",
           "HOME": str(home), "TMPDIR": str(root), "PYTHONPATH": str(source),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
           "PYTHON_KEYRING_BACKEND": "keyring.backends.null.Keyring",
           "CBP_STATE_DIR": str(root / "state"), "EXEC_DB_PATH": str(root / "execution.sqlite"),
           "CBP_DB_PATH": str(root / "cbp.sqlite"), "PYTHONUNBUFFERED": "1"}
    command = ["/usr/bin/sandbox-exec", "-f", str(profile), str(repo / ".venv/bin/python"),
               "-B", "-m", "pytest", "tests", "-q", f"--basetemp={root / 'pytest-temp'}",
               f"--junitxml={root / 'results.xml'}"]
    print(f"FROZEN_CANDIDATE={root}", flush=True)
    started = time.time()
    timed_out = False
    with (root / "pytest.log").open("w") as log:
        process = subprocess.Popen(command, cwd=source, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=900)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
    summary = {"exit_code": code, "timed_out": timed_out,
               "elapsed_seconds": round(time.time() - started, 2), "root": str(root),
               "network": "denied", "operator_home": "denied_except_readonly_venv",
               "runner_slow_skips": False, "base": manifest["base"],
               "patch_sha256": manifest["patch_sha256"]}
    (output / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for name in ("results.xml", "pytest.log"):
        if (root / name).exists():
            shutil.copy2(root / name, output / name)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
