from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir
from services.os.file_utils import atomic_write

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _candidates_dir() -> Path:
    p = runtime_dir() / "candidates"
    p.mkdir(parents=True, exist_ok=True)
    return p

def _latest_path() -> Path:
    return _candidates_dir() / "latest_candidates.json"

def _history_path() -> Path:
    return _candidates_dir() / "candidate_history.jsonl"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Write helpers (atomic via temp + replace)
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(".tmp")
    atomic_write(tmp, text)
    os.replace(tmp, path)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_candidates(rows: list[dict[str, Any]], *, scan_id: str | None = None) -> str:
    """Write latest snapshot AND append to history log.

    Each history entry is a JSONL record:
        {"ts": "<iso>", "scan_id": "<id>", "candidates": [...]}
    """
    ts = _now_iso()
    sid = str(scan_id or "").strip() or ts.replace(":", "").replace("-", "")[:20]

    # Latest file (atomic overwrite)
    payload = {"ts": ts, "scan_id": sid, "candidates": list(rows)}
    _atomic_write(_latest_path(), json.dumps(payload, indent=2))

    # History append (JSONL — one JSON object per line)
    line = json.dumps({"ts": ts, "scan_id": sid, "candidates": list(rows)})
    with open(_history_path(), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    return str(_latest_path())


def load_latest_candidates() -> list[dict[str, Any]]:
    """Return the candidates list from the most recent scan."""
    p = _latest_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Legacy format (pre-history): plain list
            return data
        return list(data.get("candidates") or [])
    except Exception:
        return []


def load_latest_snapshot() -> dict[str, Any]:
    """Return the full latest snapshot including ts and scan_id."""
    p = _latest_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"ts": None, "scan_id": None, "candidates": data}
        return data
    except Exception:
        return {}


def load_history(
    *,
    limit: int = 50,
    since_ts: str | None = None,
) -> list[dict[str, Any]]:
    """Return historical snapshots, newest first, up to `limit`.

    Args:
        limit: Max entries to return.
        since_ts: ISO timestamp; only return entries after this time.
    """
    p = _history_path()
    if not p.exists():
        return []
    since_epoch = None
    if since_ts:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(since_ts.replace("Z", "+00:00"))
            since_epoch = dt.timestamp()
        except Exception:
            pass

    entries: list[dict[str, Any]] = []
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if since_epoch is not None:
                    try:
                        from datetime import datetime, timezone
                        dt = datetime.fromisoformat(str(entry.get("ts", "")).replace("Z", "+00:00"))
                        if dt.timestamp() <= since_epoch:
                            continue
                    except Exception:
                        pass
                entries.append(entry)
    except Exception:
        return []

    # Newest first, then limit
    entries.reverse()
    return entries[:int(limit)]


def load_previous_snapshot() -> dict[str, Any]:
    """Return the second-most-recent snapshot (for diff against latest)."""
    history = load_history(limit=2)
    if len(history) < 2:
        return {}
    return history[1]


def diff_snapshots(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    *,
    key: str = "symbol",
) -> dict[str, Any]:
    """Compare two candidate lists and return a structured diff.

    Returns:
        {
            "new":      [...],   # in current, not in previous
            "dropped":  [...],   # in previous, not in current
            "moved_up": [...],   # rank improved
            "moved_dn": [...],   # rank worsened
            "unchanged":[...],   # same rank
        }
    """
    prev_map: dict[str, int] = {}
    for i, row in enumerate(previous):
        k = str(row.get(key) or "")
        if k:
            prev_map[k] = i

    curr_map: dict[str, int] = {}
    for i, row in enumerate(current):
        k = str(row.get(key) or "")
        if k:
            curr_map[k] = i

    new, dropped, moved_up, moved_dn, unchanged = [], [], [], [], []

    for k, curr_rank in curr_map.items():
        if k not in prev_map:
            row = current[curr_rank]
            new.append({**row, "_rank": curr_rank})
        else:
            prev_rank = prev_map[k]
            row = current[curr_rank]
            if curr_rank < prev_rank:
                moved_up.append({**row, "_rank": curr_rank, "_prev_rank": prev_rank})
            elif curr_rank > prev_rank:
                moved_dn.append({**row, "_rank": curr_rank, "_prev_rank": prev_rank})
            else:
                unchanged.append({**row, "_rank": curr_rank})

    for k, prev_rank in prev_map.items():
        if k not in curr_map:
            row = previous[prev_rank]
            dropped.append({**row, "_prev_rank": prev_rank})

    return {
        "new": new,
        "dropped": dropped,
        "moved_up": moved_up,
        "moved_dn": moved_dn,
        "unchanged": unchanged,
    }


def history_stats() -> dict[str, Any]:
    """Return lightweight stats about the history file."""
    p = _history_path()
    if not p.exists():
        return {"entries": 0, "size_bytes": 0, "oldest_ts": None, "newest_ts": None}
    try:
        lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        entries = len(lines)
        size = p.stat().st_size
        oldest = json.loads(lines[0]).get("ts") if lines else None
        newest = json.loads(lines[-1]).get("ts") if lines else None
        return {"entries": entries, "size_bytes": size, "oldest_ts": oldest, "newest_ts": newest}
    except Exception:
        return {"entries": 0, "size_bytes": 0, "oldest_ts": None, "newest_ts": None}
