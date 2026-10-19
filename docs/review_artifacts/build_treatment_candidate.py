"""Build an unpublished treatment-only patch without touching operator Git state."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def main():
    repo = Path(__file__).resolve().parents[2]
    evidence = repo / "docs/review_artifacts/treatment_full_suite_20261007/research_layout_corrected"
    expected = {row["path"]: row["sha256"] for row in json.loads((evidence / "inventory.json").read_text())}
    paths = [
        "storage/execution_store_sqlite.py", "services/execution/_executor_reconcile.py",
        "services/journal/fill_sink.py", "tools/repo_doctor.py",
        "tests/test_fill_sink_logging.py", "tests/test_live_executor_latency_safety_integration.py",
        "tests/test_live_executor_shadow_and_trade_reconcile.py", "tests/test_repo_doctor_strict.py",
        "tests/test_reconcile_accounting_delivery.py", "tests/test_symbol_loss_fill_once.py",
    ]
    rows = []
    for name in paths:
        digest = hashlib.sha256((repo / name).read_bytes()).hexdigest()
        if digest != expected[name]:
            raise ValueError(f"Source changed since tested snapshot: {name}")
        rows.append({"path": name, "sha256": digest})
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    root = Path(tempfile.mkdtemp(prefix="cryptkeep-treatment-candidate-", dir="/private/tmp"))
    source = root / "source"
    source.mkdir()
    archive = root / "base.tar"
    subprocess.run(["git", "archive", "--output", str(archive), base], cwd=repo, check=True)
    with tarfile.open(archive) as stream:
        stream.extractall(source, filter="data")
    env = {"PATH": "/usr/bin:/bin", "HOME": str(root), "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "init", "-q"], cwd=source, env=env, check=True)
    subprocess.run(["git", "add", "-A"], cwd=source, env=env, check=True)
    subprocess.run(["git", "-c", "user.name=Candidate", "-c", "user.email=candidate@invalid",
                    "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                    "commit", "-qm", "Disposable base"], cwd=source, env=env, check=True)
    for name in paths:
        shutil.copy2(repo / name, source / name)
    subprocess.run(["git", "add", "-N", *paths], cwd=source, env=env, check=True)
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD", "--", *paths], cwd=source, env=env)
    subprocess.run(["git", "diff", "--check"], cwd=source, env=env, check=True)
    subprocess.run(["git", "apply", "--reverse", "--check", "-"], input=patch, cwd=source, env=env, check=True)
    output = repo / "docs/review_artifacts/treatment_candidate_20261007"
    output.mkdir(exist_ok=True)
    (output / "treatment.patch").write_bytes(patch)
    manifest = {"base": base, "candidate_root": str(root), "files": rows,
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
                "scope": "10 source/test files only; unrelated work and documentation excluded",
                "full_suite": "not run on this candidate; prior working snapshot proof is separate"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
