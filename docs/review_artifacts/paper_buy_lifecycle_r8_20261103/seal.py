"""Generate public-source hashes and an incremental diff, never runtime data."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = Path(__file__).resolve().parent
BASELINES = {
    "services/execution/paper_engine.py": "before/paper_engine.py",
    "services/execution/paper_runner.py": "before/paper_runner.py",
    "services/execution/intent_reconciler.py": "before/intent_reconciler.py",
    "storage/intent_queue_sqlite.py": "before/intent_queue_sqlite.py",
    "storage/paper_trading_sqlite.py": "before/storage/paper_trading_sqlite.py",
}
NEW = (
    "services/execution/paper_buy_policy.py", "services/execution/paper_buy_lifecycle.py",
    "tests/test_paper_buy_fill_expiry.py", "tests/test_paper_buy_lifecycle.py",
    "tests/test_paper_buy_before_boundary.py",
)
FIXTURES = ("tests/test_paper_reconciler_recovery.py", "tests/test_paper_runner_lifecycle.py")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    chunks, old_hashes, current_hashes = [], {}, {}
    for name in (*BASELINES, *NEW, *FIXTURES):
        after = (ROOT / name).read_bytes()
        if name in BASELINES:
            before = (ARTIFACT / BASELINES[name]).read_bytes()
        elif name in FIXTURES:
            before = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
        else:
            before = b""
        old_hashes[name] = sha(before)
        current_hashes[name] = sha(after)
        chunks.extend(difflib.unified_diff(
            before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),
            fromfile="before/" + name, tofile="after/" + name))
    (ARTIFACT / "stage.diff").write_text("".join(chunks))
    (ARTIFACT / "hashes.json").write_text(json.dumps({
        "scope": "public source only; before fixture bytes from HEAD, production bytes from saved before tree",
        "before": old_hashes, "current": current_hashes,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"files": len(current_hashes), "stage_diff_sha256": sha((ARTIFACT / "stage.diff").read_bytes())}))
