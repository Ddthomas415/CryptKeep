from contextlib import closing
from datetime import datetime, timezone
import json
import sqlite3

import pytest

from services.alerts.group_a_observations import observe_group_a_support
from services.alerts.group_a_support_observations import (
    QueueObservation, QueueSample, ResourceSample, observe_queue, observe_resources,
)
from services.alerts.group_a_watch import HostObservation, WatchFinding


NOW = 1_790_000_000_000
RELEASE = "frozen42"
SCOPE = "cbp-group-a-frozen42-breakout-default-btc"
MARKET = "BTC/USD"


def _stamp(age):
    return datetime.fromtimestamp(NOW / 1000 - age, timezone.utc).isoformat()


def _setup(con):
    con.executescript("""
        CREATE TABLE trade_intents(intent_id TEXT PRIMARY KEY, source, side, status,
            created_ts, updated_ts, client_order_id, meta, venue, symbol);
        CREATE TABLE paper_exit_events(intent_id, ts, event);
        CREATE TABLE paper_buy_events(intent_id, ts, event, status);
        PRAGMA trusted_schema=OFF;
        PRAGMA temp_store=MEMORY;
    """)


def _add(con, identity, status, *, created=200, updated=1, side="buy", meta=None, market=MARKET):
    con.execute("INSERT INTO trade_intents VALUES(?,?,?,?,?,?,?,?,?,?)", (
        identity, "strategy", side, status, _stamp(created), _stamp(updated), None, meta, "coinbase", market,
    ))


def _sample():
    return QueueSample(SCOPE, NOW, NOW - 30_000)


def _seal(sample):
    sample.connection.commit()
    sample.connection.execute("PRAGMA query_only=ON")
    return sample


def _pending(meta_id="exit"):
    return json.dumps({"paper_exit_id": meta_id, "paper_exit_policy": "retry_until_filled_v1"})


def test_queue_observes_durable_refusals_expiry_and_pending_ages_without_writes():
    with closing(_sample()) as sample:
        con = sample.connection
        _setup(con)
        _add(con, "exit", "held", side="sell", meta=_pending())
        _add(con, "expired", "expired")
        _add(con, "submitting", "submitting", updated=61)
        _add(con, "old", "submitting", updated=300, market="ETH/USD")
        con.execute("INSERT INTO paper_exit_events VALUES(?,?,?)", ("exit", _stamp(3), "refused"))
        _seal(sample)
        before = con.total_changes
        assert observe_queue(sample, market=MARKET, now_ms=NOW) == QueueObservation(True, True, 200, 61)
        assert con.total_changes == before and not con.in_transaction


def test_queue_health_separates_complete_budget_and_unknown(monkeypatch):
    from services.alerts import group_a_support_observations as support
    with closing(_sample()) as sample:
        _setup(sample.connection)
        _add(sample.connection, "one", "queued")
        _add(sample.connection, "two", "queued")
        _seal(sample)
        assert observe_queue(sample, market=MARKET, now_ms=NOW).coverage == "complete"
        monkeypatch.setattr(support, "_ROW_CAP", 1)
        assert observe_queue(sample, market=MARKET, now_ms=NOW).coverage == "limit"
        assert observe_queue(None, market=MARKET, now_ms=NOW).coverage == "unknown"


def test_empty_copy_quiet_but_unsealed_stale_bad_meta_or_file_connection_unknown(tmp_path):
    with closing(_sample()) as sample:
        con = sample.connection
        _setup(con)
        assert observe_queue(sample, market=MARKET, now_ms=NOW) == QueueObservation()
        _seal(sample)
        assert observe_queue(sample, market=MARKET, now_ms=NOW) == QueueObservation(False, False, 0, 0)
        assert observe_queue(sample, market=MARKET, now_ms=NOW + 60_001) == QueueObservation()
        con.execute("PRAGMA query_only=OFF")
        _add(con, "exit", "held", side="sell", meta=_pending("wrong"))
        assert observe_queue(_seal(sample), market=MARKET, now_ms=NOW) == QueueObservation()
    with closing(sqlite3.connect("")) as con:
        with pytest.raises(TypeError):
            QueueSample(con, SCOPE, NOW, NOW)


def test_resource_samples_keep_unknown_separate_from_thresholds():
    meminfo = b"MemTotal: 1000 kB\nMemAvailable: 140 kB\n"
    assert observe_resources(ResourceSample(NOW, 100, 20, 10, meminfo), now_ms=NOW) == HostObservation(800 / 9, 86)
    assert observe_resources(ResourceSample(NOW, 100, 10, 20, meminfo + meminfo), now_ms=NOW) == HostObservation()
    assert observe_resources(ResourceSample(NOW + 1, 100, 20, 10, meminfo), now_ms=NOW) == HostObservation()


def test_shared_snapshot_and_support_samples_drive_watcher(tmp_path):
    root = tmp_path.resolve() / RELEASE
    quotes = root / "support" / "publisher" / "runtime" / "snapshots"
    quotes.mkdir(parents=True)
    snapshot = quotes / "system_status.latest.json"
    snapshot.write_text(json.dumps({"ts_ms": NOW - 500, "ticks": [{
        "venue": "coinbase", "symbol": MARKET, "symbol_mapped": MARKET, "ticker_symbol": MARKET,
        "source": "public_ticker", "bid": 100, "ask": 101, "ts_ms": NOW - 450,
    }]}))
    with closing(_sample()) as sample:
        con = sample.connection
        _setup(con)
        _add(con, "exit", "submitting", side="sell", meta=_pending(), updated=61)
        _seal(sample)
        report = observe_group_a_support(RELEASE, root, now_ms=NOW, queues={SCOPE: sample},
            resources=ResourceSample(NOW, 100, 10, 10, b"MemTotal: 1000 kB\nMemAvailable: 140 kB\n"))
        assert WatchFinding(SCOPE, "exit_delayed") in report.alerts
        assert WatchFinding(SCOPE, "submitting_delayed") in report.alerts
        assert WatchFinding(SCOPE, "quote_stale") not in report.alerts + report.missing
        assert WatchFinding("cbp-group-a-frozen42.target", "disk_high") in report.alerts
        assert WatchFinding("cbp-group-a-frozen42.target", "memory_high") in report.alerts
        assert WatchFinding("cbp-group-a-frozen42.target", "backup_failed") in report.missing
        with pytest.raises(ValueError, match="queue_scope"):
            observe_group_a_support(RELEASE, root, now_ms=NOW, queues={
                "cbp-group-a-frozen42-breakout-default-eth": sample,
            })
    report = observe_group_a_support(RELEASE, root, now_ms=NOW + 6000, queues={})
    assert WatchFinding(SCOPE, "quote_stale") in report.alerts
    snapshot.write_text('{"ticks":[]}')
    assert WatchFinding(SCOPE, "quote_stale") in observe_group_a_support(
        RELEASE, root, now_ms=NOW, queues={},
    ).missing


@pytest.mark.parametrize("bad", ["oversized_id", "orphan_refusal"])
def test_queue_inconsistent_or_oversized_evidence_is_not_quiet(bad):
    with closing(_sample()) as sample:
        con = sample.connection
        _setup(con)
        if bad == "oversized_id":
            _add(con, "x" * 1_048_576, "submitting")
        else:
            con.execute("INSERT INTO paper_exit_events VALUES(?,?,?)", ("unknown", _stamp(2), "refused"))
        assert observe_queue(_seal(sample), market=MARKET, now_ms=NOW) == QueueObservation()


@pytest.mark.parametrize("ticks", [[None], [{
    "venue": "coinbase", "symbol": MARKET, "symbol_mapped": "ETH/USD", "ticker_symbol": "ETH/USD",
    "source": "public_ticker", "bid": 100, "ask": 101, "ts_ms": NOW - 450,
}]])
def test_shared_snapshot_malformed_or_mismapped_quote_is_unknown(tmp_path, ticks):
    root = tmp_path.resolve() / RELEASE
    quotes = root / "support" / "publisher" / "runtime" / "snapshots"
    quotes.mkdir(parents=True)
    (quotes / "system_status.latest.json").write_text(json.dumps({"ts_ms": NOW - 500, "ticks": ticks}))
    report = observe_group_a_support(RELEASE, root, now_ms=NOW, queues={})
    assert WatchFinding(SCOPE, "quote_stale") in report.missing
