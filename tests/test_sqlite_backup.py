"""Bounded connection-copy tests; only temporary/in-memory databases."""
import sqlite3
import time

import pytest

from storage.sqlite_backup import copy_connection, SnapshotLimit


def test_copy_size_limit_precedes_destination_pages_and_leaves_source_settings():
    source=sqlite3.connect(':memory:')
    destination=sqlite3.connect(':memory:')
    try:
        source.execute('CREATE TABLE t(x)')
        source.execute('PRAGMA query_only=ON')
        with pytest.raises(SnapshotLimit,match='size'):
            copy_connection(source,destination,deadline=time.monotonic()+3,max_bytes=1)
        assert destination.execute('PRAGMA page_count').fetchone()==(0,)
        assert source.execute('PRAGMA query_only').fetchone()==(1,)
    finally:
        source.close()
        destination.close()


@pytest.mark.parametrize('deadline',[True,float('nan'),float('inf'),0])
def test_invalid_or_elapsed_deadline_refused(deadline):
    source=sqlite3.connect(':memory:')
    destination=sqlite3.connect(':memory:')
    try:
        with pytest.raises(SnapshotLimit):
            copy_connection(source,destination,deadline=deadline,max_bytes=10000)
    finally:
        source.close()
        destination.close()


def test_busy_source_refuses_copy_without_ending_the_writer_transaction(tmp_path):
    path=tmp_path/'source.sqlite'
    writer=sqlite3.connect(path)
    writer.execute('CREATE TABLE t(x)')
    writer.execute('INSERT INTO t VALUES (1)')
    writer.commit()
    reader=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=0)
    reader.execute('PRAGMA query_only=ON')
    destination=sqlite3.connect(':memory:')
    writer.execute('BEGIN EXCLUSIVE')
    start=time.monotonic()
    try:
        with pytest.raises((SnapshotLimit,sqlite3.OperationalError)):
            copy_connection(reader,destination,deadline=start+.05,max_bytes=1_000_000)
        assert time.monotonic()-start < 1
        assert writer.in_transaction is True
    finally:
        writer.rollback()
        writer.close()
        reader.close()
        destination.close()


def test_backup_progress_callback_enforces_cooperative_deadline():
    source=sqlite3.connect(':memory:')
    destination=sqlite3.connect(':memory:')
    calls=[]
    def clock():
        calls.append(1)
        return len(calls)*.001
    try:
        source.execute('CREATE TABLE t(x)')
        source.execute('INSERT INTO t VALUES (zeroblob(1000000))')
        source.commit()
        source.execute('PRAGMA query_only=ON')
        with pytest.raises(SnapshotLimit,match='deadline'):
            copy_connection(source,destination,deadline=.0025,max_bytes=2_000_000,clock=clock)
        assert len(calls)>=3
        assert source.execute('SELECT length(x) FROM t').fetchone()==(1000000,)
    finally:
        source.close()
        destination.close()
