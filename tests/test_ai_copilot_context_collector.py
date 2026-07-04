from __future__ import annotations

import sqlite3

from services.ai_copilot.context_collector import _safe_sqlite_query


def _seed_db(path):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO items (name) VALUES (?)", ("alpha",))


def test_safe_sqlite_query_reads_from_existing_database(tmp_path):
    db_path = tmp_path / "sample.sqlite"
    _seed_db(db_path)

    rows = _safe_sqlite_query(
        db_path,
        "SELECT id, name FROM items ORDER BY id",
    )

    assert rows == [{"id": 1, "name": "alpha"}]


def test_safe_sqlite_query_rejects_write_sql_without_mutation(tmp_path):
    db_path = tmp_path / "sample.sqlite"
    _seed_db(db_path)

    rows = _safe_sqlite_query(
        db_path,
        "INSERT INTO items (name) VALUES ('mutated')",
    )

    assert rows == []
    with sqlite3.connect(db_path) as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM items ORDER BY id")]
    assert names == ["alpha"]


def test_safe_sqlite_query_does_not_create_missing_database(tmp_path):
    db_path = tmp_path / "missing.sqlite"

    rows = _safe_sqlite_query(
        db_path,
        "SELECT count(*) AS count FROM items",
    )

    assert rows == []
    assert not db_path.exists()
