import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = Path(__file__).resolve().parent
EXISTING = ("services/execution/paper_engine.py", "services/analytics/paper_sim_monitor.py")
NEW = ("tests/test_paper_missing_price_valuation.py",)

if __name__ == "__main__":
    hashes, chunks = {"before": {}, "current": {}}, []
    for name in (*EXISTING, *NEW):
        old = (ARTIFACT / "before" / name).read_bytes() if name in EXISTING else b""
        current = (ROOT / name).read_bytes()
        hashes["before"][name] = hashlib.sha256(old).hexdigest()
        hashes["current"][name] = hashlib.sha256(current).hexdigest()
        chunks.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),
            current.decode().splitlines(keepends=True), fromfile="before/" + name, tofile="after/" + name))
    diff = "".join(chunks)
    (ARTIFACT / "stage.diff").write_text(diff)
    (ARTIFACT / "hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    print(hashlib.sha256(diff.encode()).hexdigest())
