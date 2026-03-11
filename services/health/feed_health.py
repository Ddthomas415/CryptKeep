from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class FeedHealthRow:
    venue: str
    symbol: str
    status: str
    age_sec: float | None
    msgs_60s: int
    last_ts_iso: str | None
    last_event_type: str | None


def _parse_ts(ts_text: str | None) -> float | None:
    try:
        if not ts_text:
            return None
        return datetime.fromisoformat(str(ts_text).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def compute_feed_health(
    *,
    db_path: str,
    warn_age_sec: float = 5.0,
    block_age_sec: float = 30.0,
    window_sec: int = 60,
) -> list[FeedHealthRow]:
    path = Path(str(db_path))
    if not path.exists():
        return []

    con = sqlite3.connect(str(path))
    try:
        cutoff = datetime.fromtimestamp(time.time() - max(1, int(window_sec)), tz=timezone.utc).isoformat()
        rows = con.execute(
            """
            SELECT venue, symbol, MAX(ts) AS last_ts,
                   SUM(CASE WHEN ts >= ? THEN 1 ELSE 0 END) AS msgs_window
            FROM events
            GROUP BY venue, symbol
            """,
            (cutoff,),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        con.close()

    out: list[FeedHealthRow] = []
    now = time.time()
    for venue, symbol, last_ts, msgs_window in rows:
        last_epoch = _parse_ts(last_ts)
        age_sec = (now - last_epoch) if last_epoch is not None else None

        if age_sec is None:
            status = "BLOCK"
        elif float(age_sec) > float(block_age_sec):
            status = "BLOCK"
        elif float(age_sec) > float(warn_age_sec):
            status = "WARN"
        else:
            status = "OK"
        msgs = int(msgs_window or 0)

        # Best-effort: derive last event type from latest row.
        last_event_type = None
        con2 = sqlite3.connect(str(path))
        try:
            row = con2.execute(
                "SELECT event_type FROM events WHERE venue=? AND symbol=? ORDER BY id DESC LIMIT 1",
                (str(venue), str(symbol)),
            ).fetchone()
            if row:
                last_event_type = str(row[0] or "")
        except sqlite3.Error:
            last_event_type = None
        finally:
            con2.close()

        out.append(
            FeedHealthRow(
                venue=str(venue),
                symbol=str(symbol),
                status=str(status),
                age_sec=(None if age_sec is None else float(age_sec)),
                msgs_60s=msgs,
                last_ts_iso=(None if last_ts is None else str(last_ts)),
                last_event_type=last_event_type,
            )
        )
    return out
