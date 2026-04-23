import sqlite3
from pathlib import Path
from datetime import datetime, UTC

def run_maintenance():
    print(f"Maintenance started {datetime.now(UTC).isoformat()}")
    for db in ["data/execution.sqlite", "data/daily_limits.sqlite"]:
        if not Path(db).exists():
            continue
        conn = sqlite3.connect(db, timeout=60)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            freelist = conn.execute("PRAGMA freelist_count;").fetchone()[0]
            if freelist > 5000:
                conn.execute("VACUUM;")
            conn.execute("PRAGMA optimize;")
            print(f"done: {db}")
        finally:
            conn.close()
    print("Maintenance complete")

if __name__ == "__main__":
    run_maintenance()
