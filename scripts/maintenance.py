#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, UTC

from services.os.paths import data_dir

def run_maintenance() -> int:
    print(f"🚀 Maintenance started {datetime.now(UTC).isoformat()}")
    dbs = [
        data_dir() / "execution.sqlite",
        data_dir() / "daily_limits.sqlite",
    ]
    for db in dbs:
        if not db.exists():
            print(f"Skipping missing DB: {db}")
            continue
        print(f"Processing {db}...")
        conn = sqlite3.connect(db, timeout=60)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            freelist = conn.execute("PRAGMA freelist_count;").fetchone()[0]
            if freelist > 5000:
                conn.execute("VACUUM;")
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.execute("PRAGMA optimize;")
            print(f"✅ {db} done")
        finally:
            conn.close()
    print("✅ Maintenance complete")
    return 0

if __name__ == "__main__":
    raise SystemExit(run_maintenance())
