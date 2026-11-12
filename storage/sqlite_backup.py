"""Reusable SQLite backup primitives; importing opens no store."""
from __future__ import annotations

import math
from pathlib import Path
import sqlite3
import time


class SnapshotLimit(ValueError):
    pass


def copy_connection(source, destination, *, deadline, max_bytes, clock=time.monotonic):
    """Copy an attributed query-only connection under cooperative bounds.

    The caller owns both connections and must establish physical source identity
    and read-only access. query_only is not a read-only-filesystem attestation.
    Neither connection is closed and source settings are not changed here.
    """
    if (type(deadline) not in (float, int) or not math.isfinite(deadline)
            or type(max_bytes) is not int or not 0 < max_bytes < 2**63
            or type(source) is not sqlite3.Connection or type(destination) is not sqlite3.Connection
            or source is destination or source.in_transaction or destination.in_transaction):
        raise SnapshotLimit('invalid_snapshot_input')
    def budget():
        if clock() >= deadline:
            raise SnapshotLimit('snapshot_deadline')
    budget()
    if source.execute('PRAGMA query_only').fetchone() != (1,):
        raise SnapshotLimit('source_not_query_only')
    page_size = source.execute('PRAGMA page_size').fetchone()[0]
    pages = source.execute('PRAGMA page_count').fetchone()[0]
    if type(page_size) is not int or page_size <= 0 or pages*page_size > max_bytes:
        raise SnapshotLimit('snapshot_size_limit')
    def progress(status, remaining, total):
        budget()
        if total*page_size > max_bytes:
            raise SnapshotLimit('snapshot_size_limit')
    source.backup(destination, pages=64, progress=progress, sleep=.01)
    budget()
    destination.set_progress_handler(lambda: int(clock() >= deadline), 1000)
    try:
        destination.execute('PRAGMA journal_mode=DELETE')
        destination.execute('PRAGMA trusted_schema=OFF')
        if destination.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise SnapshotLimit('snapshot_integrity_failed')
        budget()
    finally:
        destination.set_progress_handler(None, 0)


def snapshot_sqlite(src: Path, dest: Path) -> None:
    """Legacy path API retained verbatim; the caller selects its source scope."""
    src_uri = f'{src.resolve().as_uri()}?mode=ro'
    src_con = sqlite3.connect(src_uri, uri=True)
    try:
        src_con.execute('PRAGMA busy_timeout=5000')
        dest_con = sqlite3.connect(dest)
        try:
            dest_con.execute('PRAGMA busy_timeout=5000')
            src_con.backup(dest_con)
        finally:
            dest_con.close()
    finally:
        src_con.close()


def integrity_ok(path: Path) -> bool:
    try:
        con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        try:
            row = con.execute('PRAGMA integrity_check').fetchone()
            return bool(row) and row[0] == 'ok'
        finally:
            con.close()
    except Exception:
        return False
