import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = Path(__file__).resolve().parent
EXISTING = ("services/execution/paper_engine.py", "services/execution/strategy_runner.py",
            "services/strategies/signal_input_capture.py", "services/market_data/local_data_reader.py",
            "storage/paper_trading_sqlite.py")
HEAD = ("tests/test_ohlcv_snapshot_provenance.py",)
NEW = ("services/market_data/hourly_candle_quality.py", "tests/test_hourly_candle_quality.py",
       "tests/test_paper_candle_fill_boundary.py")

if __name__ == "__main__":
    hashes, chunks = {"before": {}, "current": {}}, []
    for name in (*EXISTING, *HEAD, *NEW):
        if name in EXISTING:
            old = (ARTIFACT / "before" / name).read_bytes()
        elif name in HEAD:
            old = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
        else:
            old = b""
        current = (ROOT / name).read_bytes()
        hashes["before"][name] = hashlib.sha256(old).hexdigest()
        hashes["current"][name] = hashlib.sha256(current).hexdigest()
        chunks.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),
            current.decode().splitlines(keepends=True), fromfile="before/" + name, tofile="after/" + name))
    diff = "".join(chunks)
    (ARTIFACT / "stage.diff").write_text(diff)
    (ARTIFACT / "hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    print(hashlib.sha256(diff.encode()).hexdigest())
