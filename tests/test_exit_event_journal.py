"""Contract of the exit-event journal beyond the first prototype.

Covers what the integration direction of 2026-10-03 requires of the store:
confirmation independent of order, quarantined evidence, a restricted reducer,
permanent applied identity, and all-or-nothing writes. Real SQLite throughout;
where a process death matters, a real child process is killed.
"""
from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
import sys
import textwrap

import pytest

from storage import strategy_state_sqlite as store
from storage.exit_event_journal import ExitEventJournal

KEYS = ("loss_streak", "cum_pnl", "kill_remaining")


@pytest.fixture
def journal(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    return ExitEventJournal()


def state():
    return store.StrategyStateSQLite()


def loss(event, get):
    count = int(get("loss_streak") or "0") + 1
    out = {"loss_streak": str(count)}
    if count >= 3:
        out["kill_remaining"] = "49"
    return out


def table(tmp_path):
    con = sqlite3.connect(tmp_path / "state.sqlite")
    try:
        return con.execute(
            "SELECT intent_id,status,confirmed,quarantined,payload FROM exit_events ORDER BY seq"
        ).fetchall()
    finally:
        con.close()


def child(tmp_path, body: str) -> int:
    """Run ``body`` in a separate Python process against the same database file."""
    code = textwrap.dedent(f"""
        import os, signal, sys
        sys.path.insert(0, {os.getcwd()!r})
        from pathlib import Path
        from storage import strategy_state_sqlite as store
        store.DB_PATH = Path({str(tmp_path / 'state.sqlite')!r})
        from storage.exit_event_journal import ExitEventJournal
        journal = ExitEventJournal()
        def loss(event, get):
            count = int(get("loss_streak") or "0") + 1
            out = {{"loss_streak": str(count), "cum_pnl": str(-count)}}
            return out
    """) + textwrap.dedent(body)
    return subprocess.run([sys.executable, "-B", "-c", code]).returncode


# --- confirmation independent of order ---------------------------------------


def test_later_event_can_be_confirmed_while_an_earlier_one_is_unresolved(journal, tmp_path):
    state().set("loss_streak", "1")
    journal.prepare("btc", "a", {"loss": True})
    journal.prepare("btc", "b", {"loss": True})

    assert journal.confirm("btc", "b") is True
    assert [(r["intent_id"], r["confirmed"]) for r in journal.unresolved("btc")] == [("a", False), ("b", True)]
    # Confirmation is evidence only: nothing is counted and order still holds.
    assert state().get("loss_streak") == "1"
    with pytest.raises(ValueError, match="earlier_exit_unresolved"):
        journal.settle("btc", "b", written=True, reduce=loss, allowed_keys=KEYS)

    # A new process: b's confirmation is still there, no queue read needed.
    restarted = ExitEventJournal()
    assert restarted.unresolved("btc")[1]["confirmed"] is True
    restarted.confirm("btc", "a")
    assert restarted.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS)
    assert restarted.settle("btc", "b", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") == "3"
    assert state().get("kill_remaining") == "49"
    assert restarted.has_unresolved("btc") is False


def test_confirm_is_idempotent_and_refuses_unknown_events(journal):
    journal.prepare("btc", "a", {})
    assert journal.confirm("btc", "a") is True
    assert journal.confirm("btc", "a") is True
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.confirm("btc", "missing")
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.confirm("eth", "a")
    journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS)
    assert journal.confirm("btc", "a") is False


def test_confirmed_event_cannot_be_marked_unwritten(journal, tmp_path):
    journal.prepare("btc", "a", {})
    journal.confirm("btc", "a")
    with pytest.raises(ValueError, match="exit_event_confirmed_written"):
        journal.settle("btc", "a", written=False, reduce=loss)
    assert table(tmp_path)[0][1:3] == ("pending", 1)


def test_confirmation_survives_a_process_that_dies_without_cleanup(journal, tmp_path):
    rc = child(tmp_path, """
        journal.prepare("btc", "a", {"loss": True})
        journal.confirm("btc", "a")
        os._exit(7)
    """)
    assert rc == 7
    assert journal.unresolved("btc")[0]["confirmed"] is True


# --- quarantined evidence ------------------------------------------------------


def _corrupt(tmp_path, intent_id, text):
    con = sqlite3.connect(tmp_path / "state.sqlite")
    con.execute("UPDATE exit_events SET payload=? WHERE intent_id=?", (text, intent_id))
    con.commit()
    con.close()


@pytest.mark.parametrize("text", ["{bad", "[1, 2]", '{"pnl_pct": NaN}', '{"pnl_pct": Infinity}', ""])
def test_unreadable_payload_is_reported_not_raised_and_cannot_be_settled_either_way(journal, tmp_path, text):
    journal.prepare("btc", "a", {"pnl_pct": -1.0})
    journal.prepare("btc", "b", {"pnl_pct": -1.0})
    _corrupt(tmp_path, "a", text)

    listed = journal.unresolved("btc")
    assert [(r["intent_id"], r["payload"], r["raw"]) for r in listed] == [("a", None, text), ("b", {"pnl_pct": -1.0}, '{"pnl_pct": -1.0}')]
    for written in (True, False):
        with pytest.raises(ValueError, match="exit_event_unreadable"):
            journal.settle("btc", "a", written=written, reduce=loss, allowed_keys=KEYS)
    # The event behind it does not overtake it.
    with pytest.raises(ValueError, match="earlier_exit_unresolved"):
        journal.settle("btc", "b", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") is None
    assert [row[1] for row in table(tmp_path)] == ["pending", "pending"]


def test_quarantine_keeps_the_raw_text_and_blocks_the_scope(journal, tmp_path):
    journal.prepare("btc", "a", {"pnl_pct": -1.0})
    journal.prepare("btc", "b", {"pnl_pct": -1.0})
    _corrupt(tmp_path, "a", "{bad")

    assert journal.quarantine("btc", "a", "payload_unreadable") is True
    assert journal.quarantine("btc", "a", "again") is True

    first = journal.unresolved("btc")[0]
    assert (first["quarantined"], first["raw"], first["note"]) == (True, "{bad", "payload_unreadable")
    for written in (True, False):
        with pytest.raises(ValueError, match="exit_event_quarantined"):
            journal.settle("btc", "a", written=written, reduce=loss, allowed_keys=KEYS)
    with pytest.raises(ValueError, match="earlier_exit_unresolved"):
        journal.settle("btc", "b", written=True, reduce=loss, allowed_keys=KEYS)
    assert journal.has_unresolved("btc") is True
    assert table(tmp_path)[0] == ("a", "pending", 0, 1, "{bad")


def test_a_readable_event_can_be_quarantined_and_is_then_never_applied_or_discarded(journal, tmp_path):
    journal.prepare("btc", "a", {"pnl_pct": -1.0})
    journal.confirm("btc", "a")
    journal.quarantine("btc", "a", "operator_hold")
    for written in (True, False):
        with pytest.raises(ValueError, match="exit_event_quarantined"):
            journal.settle("btc", "a", written=written, reduce=loss, allowed_keys=KEYS)
    assert table(tmp_path)[0] == ("a", "pending", 1, 1, '{"pnl_pct": -1.0}')


def test_evidence_prepare_would_refuse_is_kept_exactly_as_given(journal, tmp_path):
    with pytest.raises(ValueError):
        journal.prepare("btc", "a", {"pnl_pct": float("nan")})
    assert journal.unresolved("btc") == []

    raw = '{"pnl_pct": NaN, "is_loss": false}'
    journal.prepare("btc", "earlier", {"pnl_pct": -1.0})
    journal.quarantine_raw("btc", "a", raw, "non_finite_pnl", confirmed=True)
    journal.quarantine_raw("btc", "a", raw, "non_finite_pnl", confirmed=True)  # same text: no change
    journal.prepare("btc", "later", {"pnl_pct": -1.0})

    assert [r["intent_id"] for r in journal.unresolved("btc")] == ["earlier", "a", "later"]
    assert table(tmp_path)[1] == ("a", "pending", 1, 1, raw)
    with pytest.raises(ValueError, match="exit_event_identity_conflict"):
        journal.quarantine_raw("btc", "a", raw + " ", "non_finite_pnl")
    with pytest.raises(ValueError, match="exit_event_identity_conflict"):
        journal.quarantine_raw("eth", "a", raw, "non_finite_pnl")

    # The earlier event still applies; the one behind the quarantine waits.
    assert journal.settle("btc", "earlier", written=True, reduce=loss, allowed_keys=KEYS)
    with pytest.raises(ValueError, match="earlier_exit_unresolved"):
        journal.settle("btc", "later", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") == "1"


def test_quarantine_does_not_reach_other_scopes(journal):
    journal.quarantine_raw("btc", "bad", "{bad", "payload_unreadable")
    journal.prepare("eth", "a", {})
    assert journal.settle("eth", "a", written=True, reduce=loss, allowed_keys=KEYS)
    assert journal.has_unresolved("eth") is False
    assert journal.has_unresolved("btc") is True


def test_applied_or_unwritten_events_cannot_be_quarantined(journal):
    journal.prepare("btc", "a", {})
    journal.prepare("btc", "b", {})
    journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS)
    journal.settle("btc", "b", written=False, reduce=loss)
    assert journal.quarantine("btc", "a", "late") is False
    assert journal.quarantine("btc", "b", "late") is False
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.quarantine("btc", "missing", "x")


def test_first_version_listing_still_raises_on_bad_payload(journal, tmp_path):
    # Pinned so the difference from ``unresolved`` is explicit.
    journal.prepare("btc", "a", {})
    _corrupt(tmp_path, "a", "{bad")
    with pytest.raises(Exception):
        journal.pending("btc")
    assert journal.unresolved("btc")[0]["payload"] is None


# --- restricted reducer ---------------------------------------------------------


@pytest.mark.parametrize("updates, error", [
    ({"loss_streak": "1", "entry_price:x": "0"}, "exit_reducer_key_not_allowed:entry_price:x"),
    ({"loss_streak": None}, "exit_reducer_value_invalid:loss_streak"),
    ({"loss_streak": True}, "exit_reducer_value_invalid:loss_streak"),
    ({"cum_pnl": float("nan")}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": float("inf")}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": ["1"]}, "exit_reducer_value_invalid:cum_pnl"),
    ({"": "1"}, "exit_reducer_key_invalid"),
    ({1: "1"}, "exit_reducer_key_invalid"),
])
def test_reducer_output_outside_the_contract_writes_nothing(journal, tmp_path, updates, error):
    state().set("loss_streak", "0")
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match=error):
        journal.settle("btc", "a", written=True, reduce=lambda event, get: updates, allowed_keys=KEYS)
    assert state().get("loss_streak") == "0"
    assert state().get("entry_price:x") is None
    assert table(tmp_path)[0][1] == "pending"


def test_reducer_values_are_checked_even_without_a_key_list(journal, tmp_path):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="exit_reducer_value_invalid"):
        journal.settle("btc", "a", written=True, reduce=lambda event, get: {"k": None})
    assert state().get("k") is None
    assert journal.settle("btc", "a", written=True, reduce=lambda event, get: {"k": 2, "f": 1.5})
    assert (state().get("k"), state().get("f")) == ("2", "1.5")


# --- permanent identity, all-or-nothing ---------------------------------------


def test_replay_of_every_event_after_more_than_fifty_changes_nothing(journal):
    for i in range(120):
        journal.prepare("btc", f"i{i}", {})
        journal.confirm("btc", f"i{i}")
        assert journal.settle("btc", f"i{i}", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") == "120"
    replayed = ExitEventJournal()
    for i in range(120):
        assert replayed.settle("btc", f"i{i}", written=True, reduce=loss, allowed_keys=KEYS) is False
        journal.prepare("btc", f"i{i}", {})  # same identity, same payload: no new row
    assert state().get("loss_streak") == "120"
    assert replayed.has_unresolved("btc") is False


def test_process_killed_after_the_first_counter_write_leaves_nothing(journal, tmp_path):
    state().set("loss_streak", "2")
    journal.prepare("btc", "a", {})
    rc = child(tmp_path, """
        real = journal._connect
        class Con:
            def __init__(self, con): self.con = con; self.writes = 0
            def execute(self, sql, *args):
                if sql.startswith("INSERT OR REPLACE INTO strategy_state"):
                    self.writes += 1
                    if self.writes == 2:
                        # The first counter row has been written in this transaction.
                        os.kill(os.getpid(), signal.SIGKILL)
                return self.con.execute(sql, *args)
            def commit(self): return self.con.commit()
            def rollback(self): return self.con.rollback()
            def close(self): return self.con.close()
        journal._connect = lambda: Con(real())
        journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=("loss_streak", "cum_pnl"))
    """)
    assert rc == -signal.SIGKILL
    assert state().get("loss_streak") == "2"
    assert state().get("cum_pnl") is None
    assert table(tmp_path)[0][1] == "pending"
    assert journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") == "3"


def test_process_killed_right_after_the_commit_is_applied_exactly_once(journal, tmp_path):
    # The caller never learns whether its commit happened. On restart the row
    # says so, and trying again changes nothing.
    state().set("loss_streak", "2")
    journal.prepare("btc", "a", {})
    rc = child(tmp_path, """
        real = journal._connect
        class Con:
            def __init__(self, con): self.con = con
            def execute(self, sql, *args): return self.con.execute(sql, *args)
            def commit(self):
                self.con.commit()
                os.kill(os.getpid(), signal.SIGKILL)
            def rollback(self): return self.con.rollback()
            def close(self): return self.con.close()
        journal._connect = lambda: Con(real())
        journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=("loss_streak", "cum_pnl"))
    """)
    assert rc == -signal.SIGKILL
    assert table(tmp_path)[0][1] == "applied"
    assert state().get("loss_streak") == "3"
    assert journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS) is False
    assert state().get("loss_streak") == "3"


def test_locked_database_changes_nothing(journal, tmp_path):
    journal.prepare("btc", "a", {})
    other = sqlite3.connect(tmp_path / "state.sqlite", isolation_level=None, timeout=0.1)
    other.execute("BEGIN IMMEDIATE")
    real_connect = store._connect

    def quick():
        con = real_connect()
        con.execute("PRAGMA busy_timeout=100")
        return con

    store._connect, saved = quick, store._connect
    try:
        for call in (
            lambda: journal.confirm("btc", "a"),
            lambda: journal.quarantine("btc", "a", "x"),
            lambda: journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS),
        ):
            with pytest.raises(sqlite3.OperationalError):
                call()
    finally:
        store._connect = saved
        other.execute("ROLLBACK")
        other.close()
    assert table(tmp_path)[0][1:4] == ("pending", 0, 0)


# --- a table created by the first version --------------------------------------


def test_table_from_the_first_version_is_brought_up_to_date_in_place(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    con = store._connect()
    con.execute('''CREATE TABLE IF NOT EXISTS exit_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            intent_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','applied','unwritten'))
        )''')
    for identity, status in (("old_applied", "applied"), ("old_unwritten", "unwritten"), ("old_pending", "pending")):
        con.execute("INSERT INTO exit_events(scope,intent_id,payload,status) VALUES('btc',?,'{}',?)", (identity, status))
    con.close()

    journal = ExitEventJournal()

    assert [(r["intent_id"], r["confirmed"], r["quarantined"]) for r in journal.unresolved("btc")] == [("old_pending", False, False)]
    assert journal.settle("btc", "old_applied", written=True, reduce=loss, allowed_keys=KEYS) is False
    assert journal.confirm("btc", "old_pending") is True
    assert journal.settle("btc", "old_pending", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") == "1"
    # Opening it again does not try to add the columns twice.
    assert ExitEventJournal().has_unresolved("btc") is False


# --- added after review ---------------------------------------------------------


FIRST_VERSION_DDL = '''CREATE TABLE IF NOT EXISTS exit_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            intent_id TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','applied','unwritten'))
        )'''


def test_two_processes_opening_a_first_version_table_together_both_succeed(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    body = textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {os.getcwd()!r})
        from pathlib import Path
        from storage import strategy_state_sqlite as store
        store.DB_PATH = Path(sys.argv[1])
        from storage.exit_event_journal import ExitEventJournal
        while time.time() < float(sys.argv[2]):
            pass
        print(ExitEventJournal().has_unresolved("btc"))
    """)
    import time

    for trial in range(12):
        path = tmp_path / f"race{trial}.sqlite"
        monkeypatch.setattr(store, "DB_PATH", path)
        con = store._connect()
        con.execute(FIRST_VERSION_DDL)
        con.execute("INSERT INTO exit_events(scope,intent_id,payload,status) VALUES('btc','a','{}','pending')")
        con.close()
        start = str(time.time() + 0.4)
        procs = [
            subprocess.Popen([sys.executable, "-B", "-c", body, str(path), start], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(3)
        ]
        results = [p.communicate() for p in procs]
        assert [p.returncode for p in procs] == [0, 0, 0], results
        assert [out.decode().strip() for out, _ in results] == ["True"] * 3


def test_readers_need_no_write_lock_once_the_table_is_current(journal, tmp_path):
    journal.prepare("btc", "a", {})
    other = sqlite3.connect(tmp_path / "state.sqlite", isolation_level=None)
    other.execute("BEGIN IMMEDIATE")
    try:
        assert journal.has_unresolved("btc") is True
        assert [r["intent_id"] for r in journal.unresolved("btc")] == ["a"]
    finally:
        other.execute("ROLLBACK")
        other.close()


def test_the_index_exists(journal, tmp_path):
    journal.has_unresolved("btc")
    con = sqlite3.connect(tmp_path / "state.sqlite")
    names = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
    con.close()
    assert "exit_events_scope_status_seq" in names


class _Text(str):
    pass


class _Whole(int):
    def __str__(self):
        return "DROP"


class _Real(float):
    pass


@pytest.mark.parametrize("updates, error", [
    ({"cum_pnl": "nan"}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": "inf"}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": ""}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": "None"}, "exit_reducer_value_invalid:cum_pnl"),
    ({"loss_streak": "not a number"}, "exit_reducer_value_invalid:loss_streak"),
    ({"loss_streak": _Whole(3)}, "exit_reducer_value_invalid:loss_streak"),
    ({"cum_pnl": _Real(1.0)}, "exit_reducer_value_invalid:cum_pnl"),
    ({"cum_pnl": _Text("1.0")}, "exit_reducer_value_invalid:cum_pnl"),
    ({_Text("loss_streak"): "1"}, "exit_reducer_key_invalid"),
])
def test_production_mode_accepts_only_plain_finite_numbers(journal, tmp_path, updates, error):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match=error):
        journal.settle("btc", "a", written=True, reduce=lambda event, get: updates, allowed_keys=KEYS)
    assert state().get("cum_pnl") is None and state().get("loss_streak") is None
    assert table(tmp_path)[0][1] == "pending"


def test_production_mode_stores_plain_numbers_as_text(journal):
    journal.prepare("btc", "a", {})
    journal.confirm("btc", "a")
    assert journal.apply("btc", "a", reduce=lambda e, g: {"loss_streak": 3, "cum_pnl": -3.8462, "kill_remaining": "49"}, allowed_keys=KEYS)
    assert (state().get("loss_streak"), state().get("cum_pnl"), state().get("kill_remaining")) == ("3", "-3.8462", "49")


@pytest.mark.parametrize("keys", ["loss_streak", b"loss_streak", (), ("",), (1,), (_Text("loss_streak"),)])
def test_a_key_list_that_is_not_a_collection_of_plain_names_is_refused(journal, tmp_path, keys):
    # A bare string would otherwise match by substring ("loss" in "loss_streak").
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="exit_reducer_allowed_keys_invalid"):
        journal.settle("btc", "a", written=True, reduce=lambda e, g: {"loss": "1"}, allowed_keys=keys)
    assert table(tmp_path)[0][1] == "pending"


def test_apply_requires_the_key_list(journal, tmp_path):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="exit_reducer_allowed_keys_invalid"):
        journal.apply("btc", "a", reduce=loss, allowed_keys=None)
    with pytest.raises(TypeError):
        journal.apply("btc", "a", reduce=loss)
    assert table(tmp_path)[0][1] == "pending"


def test_reducer_returning_nothing_usable_is_rolled_back(journal, tmp_path):
    journal.prepare("btc", "a", {})
    with pytest.raises(TypeError):
        journal.settle("btc", "a", written=True, reduce=lambda e, g: None, allowed_keys=KEYS)
    assert table(tmp_path)[0][1] == "pending"


@pytest.mark.parametrize("text", ['{"pnl": 1e999}', '{"a": 1, "a": 2}', '{"x": {"y": -1e999}}'])
def test_text_prepare_could_not_have_written_is_unreadable(journal, tmp_path, text):
    journal.prepare("btc", "a", {"pnl": 1.0})
    _corrupt(tmp_path, "a", text)
    assert journal.unresolved("btc")[0]["payload"] is None
    with pytest.raises(ValueError, match="exit_event_unreadable"):
        journal.settle("btc", "a", written=True, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") is None


def test_bytes_that_are_not_text_are_listed_and_preserved(journal, tmp_path):
    journal.prepare("btc", "a", {})
    journal.prepare("btc", "b", {})
    con = sqlite3.connect(tmp_path / "state.sqlite")
    con.execute("UPDATE exit_events SET payload=CAST(x'ff7b' AS TEXT) WHERE intent_id='a'")
    con.commit()
    con.close()

    listed = journal.unresolved("btc")
    assert (listed[0]["raw"], listed[0]["payload"]) == (b"\xff{", None)
    assert listed[1]["payload"] == {}
    for written in (True, False):
        with pytest.raises(ValueError, match="exit_event_unreadable"):
            journal.settle("btc", "a", written=written, reduce=loss, allowed_keys=KEYS)
    assert journal.quarantine("btc", "a", "payload_not_text") is True
    assert journal.unresolved("btc")[0]["raw"] == b"\xff{"


def test_quarantine_raw_keeps_surrounding_whitespace(journal, tmp_path):
    raw = '  {"pnl_pct": NaN}\n'
    journal.quarantine_raw("btc", "a", raw, "non_finite_pnl")
    assert table(tmp_path)[0][4] == raw
    assert journal.unresolved("btc")[0]["raw"] == raw
    with pytest.raises(ValueError, match="exit_event_identity_conflict"):
        journal.quarantine_raw("btc", "a", raw.strip(), "non_finite_pnl")


def test_quarantine_raw_confirmation_only_grows(journal, tmp_path):
    journal.quarantine_raw("btc", "a", "{bad", "first")
    assert table(tmp_path)[0][2] == 0
    journal.quarantine_raw("btc", "a", "{bad", "second", confirmed=True)
    assert table(tmp_path)[0][2] == 1
    journal.quarantine_raw("btc", "a", "{bad", "third", confirmed=False)
    assert table(tmp_path)[0][2] == 1
    assert journal.unresolved("btc")[0]["note"] == "first"
    with pytest.raises(ValueError, match="invalid_exit_event"):
        journal.quarantine_raw("btc", "b", "{bad", "x", confirmed="no")


def test_quarantine_raw_cannot_shadow_an_ordinary_event(journal, tmp_path):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="exit_event_identity_conflict"):
        journal.quarantine_raw("btc", "a", "{}", "x")
    assert table(tmp_path)[0][3] == 0


def test_prepare_over_a_resolved_intent_reports_nothing(journal):
    # INHERITED from the first version, pinned so an integrator sees it: a
    # second enqueue attempt must use a new intent id.
    journal.prepare("btc", "a", {})
    journal.settle("btc", "a", written=False, reduce=loss)
    journal.prepare("btc", "a", {})
    assert journal.has_unresolved("btc") is False


def test_every_writer_fails_cleanly_on_a_locked_database(journal, tmp_path):
    journal.prepare("btc", "a", {})
    other = sqlite3.connect(tmp_path / "state.sqlite", isolation_level=None, timeout=0.1)
    other.execute("BEGIN IMMEDIATE")
    real_connect = store._connect

    def quick():
        con = real_connect()
        con.execute("PRAGMA busy_timeout=100")
        return con

    store._connect = quick
    try:
        for call in (
            lambda: journal.prepare("btc", "b", {}),
            lambda: journal.quarantine_raw("btc", "c", "{bad", "x"),
            lambda: journal.apply("btc", "a", reduce=loss, allowed_keys=KEYS),
        ):
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                call()
    finally:
        store._connect = real_connect
        other.execute("ROLLBACK")
        other.close()
    assert [(row[0], row[1]) for row in table(tmp_path)] == [("a", "pending")]


# --- review of 0021 (2026-10-04): findings pinned -----------------------------

def _damage(tmp_path, column, intent_id):
    con = sqlite3.connect(tmp_path / "state.sqlite")
    try:
        if column == "scope":
            con.execute("UPDATE exit_events SET scope=CAST(x'627463ff' AS TEXT) WHERE intent_id=?", (intent_id,))
        else:
            con.execute(f"UPDATE exit_events SET {column}=CAST(x'ff61' AS TEXT) WHERE intent_id=?", (intent_id,))
        con.commit()
    finally:
        con.close()


def test_apply_refuses_an_event_that_was_never_confirmed(journal, tmp_path):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="exit_event_unconfirmed"):
        journal.apply("btc", "a", reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") is None and table(tmp_path)[0][1:3] == ("pending", 0)
    journal.confirm("btc", "a")
    assert journal.apply("btc", "a", reduce=loss, allowed_keys=KEYS) is True
    assert state().get("loss_streak") == "1"


def test_evidence_of_a_write_after_unwritten_is_a_contradiction_not_a_quiet_false(journal, tmp_path):
    journal.prepare("btc", "a", {})
    assert journal.settle("btc", "a", written=False, reduce=loss) is True
    with pytest.raises(ValueError, match="exit_event_marked_unwritten"):
        journal.confirm("btc", "a")
    with pytest.raises(ValueError, match="exit_event_marked_unwritten"):
        journal.apply("btc", "a", reduce=loss, allowed_keys=KEYS)
    with pytest.raises(ValueError, match="exit_event_marked_unwritten"):
        journal.settle("btc", "a", written=True, reduce=loss)
    assert state().get("loss_streak") is None and table(tmp_path)[0][1] == "unwritten"
    # An applied event still answers False quietly: replay is not a contradiction.
    journal.prepare("btc", "b", {}); journal.confirm("btc", "b")
    assert journal.apply("btc", "b", reduce=loss, allowed_keys=KEYS) is True
    assert journal.confirm("btc", "b") is False
    assert journal.apply("btc", "b", reduce=loss, allowed_keys=KEYS) is False
    assert state().get("loss_streak") == "1"


def test_a_damaged_scope_blocks_every_scope_and_nothing_overtakes_it(journal, tmp_path):
    for identity in ("a", "b"):
        journal.prepare("btc", identity, {}); journal.confirm("btc", identity)
    journal.prepare("eth", "e", {}); journal.confirm("eth", "e")
    _damage(tmp_path, "scope", "a")
    assert journal.has_unresolved("btc") is True
    for scope, identity in (("btc", "b"), ("eth", "e")):
        with pytest.raises(ValueError, match="exit_event_scope_damaged"):
            journal.apply(scope, identity, reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") is None
    # A scope with nothing of its own is reported unresolved too.
    assert journal.has_unresolved("sol") is True


def test_a_damaged_scope_on_an_applied_row_blocks_nothing(journal, tmp_path):
    journal.prepare("btc", "a", {}); journal.confirm("btc", "a")
    assert journal.apply("btc", "a", reduce=loss, allowed_keys=KEYS)
    _damage(tmp_path, "scope", "a")
    assert journal.has_unresolved("btc") is False and journal.has_unresolved("eth") is False


@pytest.mark.parametrize("column", ["intent_id", "note"])
def test_unresolved_does_not_raise_on_damaged_text_columns(journal, tmp_path, column):
    journal.prepare("btc", "a", {}); journal.prepare("btc", "b", {}); journal.confirm("btc", "b")
    _damage(tmp_path, column, "a")
    listed = journal.unresolved("btc")
    assert [row["seq"] for row in listed] == [1, 2]
    assert listed[0]["damaged"] is (column == "intent_id") and listed[1]["damaged"] is False
    assert journal.has_unresolved("btc") is True
    # The event behind it still does not overtake.
    with pytest.raises((ValueError, sqlite3.OperationalError)):
        journal.apply("btc", "b", reduce=loss, allowed_keys=KEYS)
    assert state().get("loss_streak") is None


@pytest.mark.parametrize("scope", [None, "", b"btc", 7])
def test_readers_refuse_a_scope_that_is_not_a_name(journal, scope):
    journal.prepare("btc", "a", {})
    with pytest.raises(ValueError, match="invalid_exit_scope"):
        journal.has_unresolved(scope)
    with pytest.raises(ValueError, match="invalid_exit_scope"):
        journal.unresolved(scope)


@pytest.mark.parametrize("value", [10**400, -10**400, "1_0", " 7\n", "\u0663", "0x10", "+1", "1."])
def test_production_mode_refuses_numbers_that_do_not_read_back_plainly(journal, tmp_path, value):
    journal.prepare("btc", "a", {}); journal.confirm("btc", "a")
    with pytest.raises(ValueError, match="exit_reducer_value_invalid:cum_pnl"):
        journal.apply("btc", "a", reduce=lambda e, g: {"cum_pnl": value}, allowed_keys=KEYS)
    assert state().get("cum_pnl") is None and table(tmp_path)[0][1] == "pending"


@pytest.mark.parametrize("value, stored", [("49", "49"), ("-3.8462", "-3.8462"), ("1e-05", "1e-05"), (10**15, str(10**15))])
def test_production_mode_still_accepts_plain_numbers(journal, value, stored):
    journal.prepare("btc", "a", {}); journal.confirm("btc", "a")
    assert journal.apply("btc", "a", reduce=lambda e, g: {"cum_pnl": value}, allowed_keys=KEYS)
    assert state().get("cum_pnl") == stored


def test_an_event_cannot_be_settled_or_quarantined_under_another_scope(journal, tmp_path):
    journal.prepare("btc", "a", {}); journal.confirm("btc", "a")
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.apply("eth", "a", reduce=loss, allowed_keys=KEYS)
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.settle("eth", "a", written=True, reduce=loss)
    with pytest.raises(ValueError, match="unknown_exit_event"):
        journal.quarantine("eth", "a", "wrong scope")
    assert state().get("loss_streak") is None and table(tmp_path)[0][1:4] == ("pending", 1, 0)


def test_an_event_behind_another_cannot_be_marked_unwritten(journal, tmp_path):
    journal.prepare("btc", "a", {}); journal.prepare("btc", "b", {})
    with pytest.raises(ValueError, match="earlier_exit_unresolved"):
        journal.settle("btc", "b", written=False, reduce=loss)
    assert [row[1] for row in table(tmp_path)] == ["pending", "pending"]


def test_a_reducer_that_fails_after_reading_leaves_counters_and_status_untouched(journal, tmp_path):
    journal.prepare("btc", "a", {}); journal.confirm("btc", "a")
    state().set("loss_streak", "2")

    def partly(event, get):
        return {"loss_streak": "3", "kill_remaining": object()}

    with pytest.raises(ValueError, match="exit_reducer_value_invalid:kill_remaining"):
        journal.apply("btc", "a", reduce=partly, allowed_keys=KEYS)
    assert state().get("loss_streak") == "2" and state().get("kill_remaining") is None
    assert table(tmp_path)[0][1] == "pending"


# Original accepted prototype cases, preserved alongside the extended contract.

def count_loss(event, get):
    count = int(get('loss_streak') or '0') + 1
    return {'loss_streak': str(count), 'kill': str(count >= 3)}


def test_two_events_survive_restart_and_count_once(journal):
    state = store.StrategyStateSQLite()
    state.set('loss_streak', '1')
    for identity in ('a', 'b'):
        journal.prepare('btc', identity, {'loss': True})
    restarted = ExitEventJournal()
    assert [identity for identity, _ in restarted.pending('btc')] == ['a', 'b']
    with pytest.raises(ValueError, match='earlier_exit_unresolved'):
        restarted.settle('btc', 'b', written=True, reduce=count_loss)
    assert restarted.settle('btc', 'a', written=True, reduce=count_loss)
    assert restarted.settle('btc', 'b', written=True, reduce=count_loss)
    assert state.get('loss_streak') == '3'
    assert state.get('kill') == 'True'
    assert not restarted.settle('btc', 'a', written=True, reduce=count_loss)
    assert state.get('loss_streak') == '3'


def test_failed_reducer_leaves_event_and_counters_unchanged(journal):
    journal.prepare('btc', 'a', {})
    def broken(event, get):
        raise RuntimeError('failure')
    with pytest.raises(RuntimeError):
        journal.settle('btc', 'a', written=True, reduce=broken)
    assert journal.pending('btc') == [('a', {})]
    assert store.StrategyStateSQLite().get('loss_streak') is None


def test_unwritten_event_not_counted(journal):
    journal.prepare('btc', 'a', {})
    assert journal.settle('btc', 'a', written=False, reduce=count_loss)
    assert store.StrategyStateSQLite().get('loss_streak') is None
    assert journal.pending('btc') == []


def test_prepare_is_idempotent_but_conflicting_payload_rejected(journal):
    journal.prepare('btc', 'a', {'price': 100})
    journal.prepare('btc', 'a', {'price': 100})
    with pytest.raises(ValueError, match='identity_conflict'):
        journal.prepare('btc', 'a', {'price': 101})
    assert len(journal.pending('btc')) == 1


def test_unknown_confirmation_cannot_discard(journal):
    journal.prepare('btc', 'a', {})
    with pytest.raises(ValueError, match='confirmation_required'):
        journal.settle('btc', 'a', written=None, reduce=count_loss)
    assert journal.pending('btc') == [('a', {})]


def test_scopes_do_not_block_each_other(journal):
    journal.prepare('btc', 'a', {})
    journal.prepare('eth', 'b', {})
    assert journal.settle('eth', 'b', written=False, reduce=count_loss)
    assert journal.pending('btc') == [('a', {})]


def test_import_and_construction_do_not_open_a_database(monkeypatch, tmp_path):
    import importlib
    import storage.exit_event_journal as module

    path = tmp_path / 'unused.sqlite'
    monkeypatch.setattr(store, 'DB_PATH', path)

    def forbidden():
        pytest.fail('journal opened a database before first use')

    monkeypatch.setattr(store, '_connect', forbidden)
    importlib.reload(module)
    module.ExitEventJournal()
    assert not path.exists()


def test_first_use_creates_table_in_rebound_database(journal, tmp_path):
    path = tmp_path / 'state.sqlite'
    assert not path.exists()
    assert journal.has_unresolved('btc') is False
    assert path.exists()
    with sqlite3.connect(path) as con:
        assert con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exit_events'"
        ).fetchone() == ('exit_events',)


def test_reviewed_recovery_helpers_show_confirmed_and_unwritten_rows(journal):
    assert journal.status_of('missing') is None
    assert journal.last('btc') is None
    journal.prepare('btc', 'a', {'pnl_pct': -2})
    journal.confirm('btc', 'a')
    assert ExitEventJournal().status_of('a') == {
        'scope': 'btc', 'status': 'pending', 'confirmed': True,
        'quarantined': False, 'seq': 1,
    }
    assert journal.apply('btc', 'a', reduce=loss, allowed_keys=KEYS)
    assert journal.status_of('a')['status'] == 'applied'
    journal.prepare('btc', 'b', {'pnl_pct': 1})
    assert journal.settle('btc', 'b', written=False, reduce=loss)
    assert ExitEventJournal().last('btc') == {
        'intent_id': 'b', 'payload': {'pnl_pct': 1}, 'status': 'unwritten', 'seq': 2,
    }
    assert journal.status_of('b') == {
        'scope': 'btc', 'status': 'unwritten', 'confirmed': False,
        'quarantined': False, 'seq': 2,
    }
