"""Seal the reviewed-patch rebase against the captured current source."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = Path(__file__).resolve().parent
EXISTING = ("services/market_data/tick_reader.py", "services/execution/paper_engine.py",
            "tests/test_market_snapshot_readers.py")
NEW = ("tests/test_tick_reader_exact_symbol.py",)


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
    print(json.dumps({"files": len(hashes["current"]), "stage_diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}))
