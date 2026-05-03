import sqlite3
from pathlib import Path

import pytest

from services.execution import _executor_shared
from services.journal import fill_sink
from services.risk import system_health


def test_executor_shared_on_fill_propagates_sink_not_ok(monkeypatch, tmp_path):
    class BadSink:
        def __init__(self, exec_db):
            self.exec_db = exec_db

        def on_fill(self, fill):
            return {"ok": False, "reason": "record_failed:boom"}

    monkeypatch.setattr(_executor_shared, "CanonicalFillSink", BadSink)
    out = _executor_shared._on_fill({"fill_id": "f1"}, exec_db=str(tmp_path / "execution.sqlite"))
    assert out["ok"] is False
    assert "record_failed:boom" in out["error"]


def test_composite_fill_sink_returns_failure_when_any_sink_returns_not_ok():
    class Bad:
        def on_fill(self, fill):
            return {"ok": False, "reason": "bad"}

    class Good:
        def on_fill(self, fill):
            return {"ok": True}

    out = fill_sink.CompositeFillSink([Bad(), Good()]).on_fill({"fill_id": "f1"})
    assert out["ok"] is False


def test_composite_fill_sink_returns_failure_when_any_sink_raises():
    class Bad:
        def on_fill(self, fill):
            raise RuntimeError("boom")

    class Good:
        def on_fill(self, fill):
            return {"ok": True}

    out = fill_sink.CompositeFillSink([Bad(), Good()]).on_fill({"fill_id": "f1"})
    assert out["ok"] is False


def test_system_health_detects_live_fills_missing_from_canonical(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    exec_db = tmp_path / "execution.sqlite"
    live_db = data_dir / "live_trading.sqlite"

    with sqlite3.connect(exec_db) as con:
        con.execute("CREATE TABLE canonical_fills (venue TEXT, fill_id TEXT)")
        con.execute("CREATE TABLE risk_daily_fills (venue TEXT, fill_id TEXT)")

    with sqlite3.connect(live_db) as con:
        con.execute("CREATE TABLE live_fills (venue TEXT, trade_id TEXT)")
        con.execute("INSERT INTO live_fills VALUES ('coinbase', 'trade-1')")

    monkeypatch.setattr(system_health, "_data_dir", lambda: data_dir)
    monkeypatch.setattr(system_health, "_exec_db", lambda: str(exec_db))

    reason = system_health._check_live_trading_vs_canonical()
    assert reason == "live_trading_vs_canonical_gap:1_live_fills_missing_from_canonical_fills"


def test_system_health_live_gap_clean_when_canonical_exists(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    exec_db = tmp_path / "execution.sqlite"
    live_db = data_dir / "live_trading.sqlite"

    with sqlite3.connect(exec_db) as con:
        con.execute("CREATE TABLE canonical_fills (venue TEXT, fill_id TEXT)")
        con.execute("CREATE TABLE risk_daily_fills (venue TEXT, fill_id TEXT)")
        con.execute("INSERT INTO canonical_fills VALUES ('coinbase', 'trade-1')")

    with sqlite3.connect(live_db) as con:
        con.execute("CREATE TABLE live_fills (venue TEXT, trade_id TEXT)")
        con.execute("INSERT INTO live_fills VALUES ('coinbase', 'trade-1')")

    monkeypatch.setattr(system_health, "_data_dir", lambda: data_dir)
    monkeypatch.setattr(system_health, "_exec_db", lambda: str(exec_db))

    assert system_health._check_live_trading_vs_canonical() is None


def test_system_health_missing_canonical_with_live_fills_is_degraded(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    exec_db = tmp_path / "execution.sqlite"
    live_db = data_dir / "live_trading.sqlite"

    with sqlite3.connect(exec_db):
        pass

    with sqlite3.connect(live_db) as con:
        con.execute("CREATE TABLE live_fills (venue TEXT, trade_id TEXT)")
        con.execute("INSERT INTO live_fills VALUES ('coinbase', 'trade-1')")

    monkeypatch.setattr(system_health, "_data_dir", lambda: data_dir)
    monkeypatch.setattr(system_health, "_exec_db", lambda: str(exec_db))

    reason = system_health._check_live_trading_vs_canonical()
    assert reason == "live_trading_vs_canonical_gap:1_live_fills_missing_from_canonical_fills"


def test_system_health_missing_live_fills_table_is_first_run_safe(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    exec_db = tmp_path / "execution.sqlite"
    live_db = data_dir / "live_trading.sqlite"

    with sqlite3.connect(exec_db) as con:
        con.execute("CREATE TABLE canonical_fills (venue TEXT, fill_id TEXT)")

    with sqlite3.connect(live_db):
        pass

    monkeypatch.setattr(system_health, "_data_dir", lambda: data_dir)
    monkeypatch.setattr(system_health, "_exec_db", lambda: str(exec_db))

    assert system_health._check_live_trading_vs_canonical() is None


def test_accounting_invariant_operational_error_degrades(monkeypatch, tmp_path):
    def bad_connect(*args, **kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(system_health.sqlite3, "connect", bad_connect)
    reason = system_health._check_accounting_invariant()
    assert reason == "accounting_invariant_check_failed:OperationalError:database is locked"


def test_cursor_advances_only_through_contiguous_accounted_prefix():
    """
    Cursor may advance only through a contiguous prefix of successfully
    accounted fills. A later successful fill must not move the cursor past
    an earlier failed fill.
    """

    def cursor_after(trades, emit_ok_by_id):
        max_ts_accounted = 0
        cursor_blocked = False

        for tr in trades:
            tid = tr["id"]
            ts = int(tr["timestamp"])

            if not emit_ok_by_id[tid]:
                cursor_blocked = True
                continue

            if not cursor_blocked:
                max_ts_accounted = max(max_ts_accounted, ts)

        return str(max_ts_accounted + 1) if max_ts_accounted else None

    assert cursor_after(
        [
            {"id": "fail-first", "timestamp": 1000},
            {"id": "ok-later", "timestamp": 2000},
        ],
        {"fail-first": False, "ok-later": True},
    ) is None

    assert cursor_after(
        [
            {"id": "ok-first", "timestamp": 1000},
            {"id": "fail-second", "timestamp": 2000},
        ],
        {"ok-first": True, "fail-second": False},
    ) == "1001"

