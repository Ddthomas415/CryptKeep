"""Release-owned shared public quotes; no paper ledger access."""

from contextlib import contextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import stat
import tempfile

MARKETS = ("BTC/USD", "ETH/USD", "SOL/USD")
SNAPSHOT_NAME = "system_status.latest.json"


def _valid_last(value):
    try:
        return value if type(value) in (int, float) and math.isfinite(value) and value > 0 else None
    except OverflowError:
        return None


def project_snapshot(payload, *, now):
    """Never carry forward a quote or refresh its original receipt time."""
    # These dependencies initialize runtime directories on first import.
    # Keep draft rendering and lock-only use independent of that state.
    from services.market_data.paper_snapshot_quote import assess_paper_quote
    from services.market_data.symbol_router import normalize_symbol

    out = {"ts_ms": 0, "ticks": []}
    if not isinstance(payload, dict) or not isinstance(payload.get("ticks"), list):
        return out
    snapshot_ms = payload.get("ts_ms")
    candidates = {market: [] for market in MARKETS}
    for row in payload["ticks"]:
        if isinstance(row, dict) and row.get("venue") == "coinbase" and isinstance(row.get("symbol"), str):
            symbol = normalize_symbol(row["symbol"])
            if symbol in candidates:
                candidates[symbol].append(row)
    for market, rows in candidates.items():
        if len(rows) != 1:
            continue
        row = rows[0]
        quote, _ = assess_paper_quote(
            {**row, "snapshot_ts_ms": snapshot_ms}, venue="coinbase", symbol=market, now=now,
        )
        if quote is not None and normalize_symbol(quote["symbol_mapped"]) == market:
            out["ticks"].append({**quote, "last": _valid_last(row.get("last"))})
    if out["ticks"]:
        out["ts_ms"] = snapshot_ms
    return out


def publish_once(directory: Path, *, fetch, clock) -> int:
    """Replace the whole snapshot, including on a successful empty fetch."""
    payload = project_snapshot(fetch(), now=clock())
    target = directory / SNAPSHOT_NAME
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump(payload, stream, allow_nan=False, separators=(",", ":"))
            stream.close()
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    return len(payload["ticks"])


@contextmanager
def publisher_lock(directory: Path):
    # Keep the lock inode: unlinking it permits a second writer on a new inode.
    fd = os.open(directory / "publisher.flock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("invalid_publisher_lock")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)
