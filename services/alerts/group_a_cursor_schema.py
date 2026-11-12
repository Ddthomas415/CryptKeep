"""One schema source for cursor transactions and persisted-image validation."""


SCHEMA = {
    "cycle": """CREATE TABLE IF NOT EXISTS delivery_cycle (
        id INTEGER PRIMARY KEY CHECK(id = 1), release TEXT NOT NULL, observed_ms INTEGER NOT NULL
    )""",
    "finding": """CREATE TABLE IF NOT EXISTS delivery_finding (
        scope TEXT NOT NULL, code TEXT NOT NULL, active INTEGER NOT NULL,
        pending INTEGER NOT NULL, first_seen_ms INTEGER NOT NULL, last_attempt_ms INTEGER NOT NULL,
        PRIMARY KEY(scope, code)
    )""",
    "epoch": """CREATE TABLE IF NOT EXISTS delivery_queue_epoch (
        id INTEGER PRIMARY KEY CHECK(id = 1), since_ms INTEGER NOT NULL
    )""",
    "source": """CREATE TABLE IF NOT EXISTS delivery_queue_source (
        scope TEXT PRIMARY KEY, identity TEXT NOT NULL
    )""",
    "event": """CREATE TABLE IF NOT EXISTS delivery_queue_event (
        scope TEXT NOT NULL, code TEXT NOT NULL, digest TEXT NOT NULL,
        PRIMARY KEY(scope, code, digest)
    )""",
}
