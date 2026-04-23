#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, UTC

from services.os.app_paths import data_dir

def run_maintenance() -> int:
    print(f"🚀 Maintenance started {datetime.now(UTC).isoformat()}")
    db_paths = [
        data_dir() / "execution.sqlite",
        data_dir() / "daily_limits.sqlite",
    ]
    for db_path in db_paths:
        if not db_path.exists():
            print(f"Skipping missing DB: {db_path}")
            continue
        print(f"Processing {db_path}...")
        conn = sqlite3.connect(str(db_path), timeout=60)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            freelist = conn.execute("PRAGMA freelist_count;").fetchone()[0]
            if freelist > 5000:
                conn.execute("VACUUM;")
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.execute("PRAGMA optimize;")
            print(f"✅ {db_path} done")
        finally:
            conn.close()
    print("✅ Maintenance complete")
    return 0

if __name__ == "__main__":
    raise SystemExit(run_maintenance())
