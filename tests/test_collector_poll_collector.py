from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from services.collector.poll_collector import CollectorConfig, get_or_create
from storage.event_store_sqlite import SQLiteEventStore


def test_collector_status_reports_missing_events_db(tmp_path):
    handle = get_or_create(CollectorConfig(events_db_path=str(tmp_path / "missing.sqlite"), poll_sec=1.0))

    out = handle.status()

    assert out["ok"] is True
    assert out["running"] is False
    assert out["reason"] == "events_db_missing"


def test_collector_status_reads_recent_heartbeat_from_event_store(tmp_path):
    db_path = tmp_path / "events.sqlite"
    store = SQLiteEventStore(path=db_path)
    asyncio.run(
        store.heartbeat(
            ts_iso=datetime.now(timezone.utc).isoformat(),
            service="data_collector",
            status="running",
            detail={"feeds": ["coinbase"]},
        )
    )

    handle = get_or_create(CollectorConfig(events_db_path=str(db_path), poll_sec=1.0))
    out = handle.status()

    assert out["ok"] is True
    assert out["running"] is True
    assert out["status"] == "running"
    assert out["detail"] == {"feeds": ["coinbase"]}


def test_collector_status_marks_old_heartbeat_stale(tmp_path):
    db_path = tmp_path / "events.sqlite"
    store = SQLiteEventStore(path=db_path)
    asyncio.run(
        store.heartbeat(
            ts_iso=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
            service="data_collector",
            status="running",
            detail={"feeds": ["coinbase"]},
        )
    )

    handle = get_or_create(CollectorConfig(events_db_path=str(db_path), poll_sec=1.0))
    out = handle.status()

    assert out["ok"] is True
    assert out["running"] is False
    assert out["reason"] == "stale"
