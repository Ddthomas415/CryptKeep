"""
Substrate backlog #8 proofs: full-state backup/restore tooling.

Drill contract pinned here: backups taken via the sqlite backup API are
transactionally consistent even under an active writer; the manifest
detects any tamper; restore refuses to run over live locks or a non-empty
target without --force; --force moves the old data aside rather than
deleting it; and the full round trip (backup -> mutate -> restore)
recovers exactly the backup-time state.
"""
from __future__ import annotations

import importlib
import json
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path / "state"))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import backup_state as bs

        importlib.reload(bs)
    finally:
        sys.path.remove(str(REPO / "scripts"))
    return bs, app_paths


def _seed_store(data_dir: Path, name: str, rows: int) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    db = data_dir / name
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE IF NOT EXISTS t(id INTEGER PRIMARY KEY, v TEXT)")
    con.executemany("INSERT INTO t(v) VALUES (?)", [(f"row-{i}",) for i in range(rows)])
    con.commit()
    con.close()
    return db


def _count(db: Path) -> int:
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    finally:
        con.close()


def test_round_trip_recovers_backup_time_state(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 25)
    (data_dir() / "evidence.json").write_text('{"k": 1}', encoding="utf-8")

    out = bs.create_backup(tmp_path / "backups")
    assert out["ok"], out
    backup_dir = Path(out["backup_dir"])
    assert out["file_count"] == 2

    # mutate AFTER the backup: add rows and corrupt the json
    _seed_store(data_dir(), "execution.sqlite", 10)
    (data_dir() / "evidence.json").write_text('{"k": 999}', encoding="utf-8")
    assert _count(data_dir() / "execution.sqlite") == 35

    res = bs.restore_backup(backup_dir, force=True)
    assert res["ok"], res
    assert _count(data_dir() / "execution.sqlite") == 25  # backup-time state
    assert json.loads((data_dir() / "evidence.json").read_text()) == {"k": 1}
    # the mutated world was moved aside, never deleted
    aside = Path(res["moved_aside"])
    assert aside.exists()
    assert _count(aside / "execution.sqlite") == 35


def test_backup_is_consistent_under_active_writer(monkeypatch, tmp_path):
    """The sqlite backup API must yield an integrity-clean snapshot while a
    writer hammers the source — the property a plain file copy lacks."""
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    db = _seed_store(data_dir(), "live_trading.sqlite", 100)
    stop = threading.Event()

    def writer():
        con = sqlite3.connect(db)
        i = 0
        while not stop.is_set():
            con.execute("INSERT INTO t(v) VALUES (?)", (f"live-{i}",))
            con.commit()
            i += 1
        con.close()

    t = threading.Thread(target=writer)
    t.start()
    try:
        time.sleep(0.05)
        out = bs.create_backup(tmp_path / "backups")
    finally:
        stop.set()
        t.join(timeout=10)
    assert out["ok"], out

    verdict = bs.verify_backup(Path(out["backup_dir"]))
    assert verdict["ok"], verdict
    snap = Path(out["backup_dir"]) / "state" / "live_trading.sqlite"
    assert bs._integrity_ok(snap)
    assert _count(snap) >= 100  # at least the seeded rows, transactionally whole
    manifest = json.loads((Path(out["backup_dir"]) / bs.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert not any(str(entry["rel"]).endswith("-journal") for entry in manifest["files"])


def test_verify_detects_tamper_and_missing(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")
    backup_dir = Path(out["backup_dir"])

    assert bs.verify_backup(backup_dir)["ok"] is True

    snap = backup_dir / "state" / "execution.sqlite"
    snap.write_bytes(snap.read_bytes() + b"tamper")
    verdict = bs.verify_backup(backup_dir)
    assert verdict["ok"] is False
    assert any(p.startswith("checksum_mismatch") for p in verdict["problems"])

    snap.unlink()
    verdict = bs.verify_backup(backup_dir)
    assert any(p.startswith("missing") for p in verdict["problems"])


def test_restore_refuses_tampered_backup_before_touching_target(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")
    backup_dir = Path(out["backup_dir"])
    snap = backup_dir / "state" / "execution.sqlite"
    snap.write_bytes(snap.read_bytes() + b"tamper")

    before = (data_dir() / "execution.sqlite").read_bytes()
    res = bs.restore_backup(backup_dir, force=True)
    assert res["ok"] is False and res["reason"] == "backup_verify_failed"
    assert (data_dir() / "execution.sqlite").read_bytes() == before  # untouched


def test_restore_rejects_manifest_path_traversal_before_touching_target(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")
    backup_dir = Path(out["backup_dir"])
    manifest_path = backup_dir / bs.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["rel"] = "state/../escape.sqlite"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    before = (data_dir() / "execution.sqlite").read_bytes()
    verdict = bs.verify_backup(backup_dir)
    assert verdict["ok"] is False
    assert any(p.startswith("invalid_rel:") for p in verdict["problems"])

    res = bs.restore_backup(backup_dir, force=True)
    assert res["ok"] is False and res["reason"] == "backup_verify_failed"
    assert (data_dir() / "execution.sqlite").read_bytes() == before
    assert not (data_dir().parent / "escape.sqlite").exists()


def test_restore_ignores_unmanifested_backup_files(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")
    backup_dir = Path(out["backup_dir"])
    (backup_dir / bs.ARCHIVE_SUBDIR / "unmanifested.json").write_text('{"bad": true}', encoding="utf-8")

    res = bs.restore_backup(backup_dir, force=True)
    assert res["ok"], res
    assert not (data_dir() / "unmanifested.json").exists()


def test_restore_blocked_by_live_locks(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")
    lock = data_dir() / "live_intent_consumer.lock"
    lock.write_text("pid 123", encoding="utf-8")

    res = bs.restore_backup(Path(out["backup_dir"]), force=True)
    assert res["ok"] is False and res["reason"] == "live_locks_present"
    assert any("live_intent_consumer.lock" in l for l in res["locks"])


def test_restore_requires_force_on_nonempty_target(monkeypatch, tmp_path):
    bs, ap = _load(monkeypatch, tmp_path)
    from services.os.app_paths import data_dir

    _seed_store(data_dir(), "execution.sqlite", 5)
    out = bs.create_backup(tmp_path / "backups")

    res = bs.restore_backup(Path(out["backup_dir"]), force=False)
    assert res["ok"] is False and res["reason"] == "target_not_empty_use_force"


def test_cli_end_to_end_exit_codes(monkeypatch, tmp_path):
    state = tmp_path / "state"
    env = {"CBP_STATE_DIR": str(state), "PATH": "/usr/bin:/bin"}
    _seed_store(state / "data", "execution.sqlite", 3)

    b = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "backup_state.py"), "backup", "--dest", str(tmp_path / "b")],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert b.returncode == 0, b.stdout + b.stderr
    backup_payload = json.loads(b.stdout)
    backup_dir = backup_payload["backup_dir"]
    assert backup_payload["operator_event"]["ok"] is True
    backup_event_path = Path(backup_payload["operator_event"]["path"])
    backup_event = json.loads(backup_event_path.read_text(encoding="utf-8").splitlines()[-1])
    assert backup_event["action"] == "state_backup"
    assert backup_event["result"] == "success"

    v = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "backup_state.py"), "verify", backup_dir],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert v.returncode == 0, v.stdout + v.stderr
    verify_payload = json.loads(v.stdout)
    assert verify_payload["operator_event"]["ok"] is True
    verify_event = json.loads(Path(verify_payload["operator_event"]["path"]).read_text(encoding="utf-8").splitlines()[-1])
    assert verify_event["action"] == "state_backup_verify"
    assert verify_event["result"] == "success"

    r_blocked = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "backup_state.py"), "restore", backup_dir],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert r_blocked.returncode == 2  # non-empty target without --force
    blocked_payload = json.loads(r_blocked.stdout)
    assert blocked_payload["operator_event"]["ok"] is True
    blocked_event = json.loads(Path(blocked_payload["operator_event"]["path"]).read_text(encoding="utf-8").splitlines()[-1])
    assert blocked_event["action"] == "state_restore"
    assert blocked_event["result"] == "blocked"

    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "backup_state.py"), "restore", backup_dir, "--force"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    restore_payload = json.loads(r.stdout)
    assert restore_payload["operator_event"]["ok"] is True
    restore_event = json.loads(Path(restore_payload["operator_event"]["path"]).read_text(encoding="utf-8").splitlines()[-1])
    assert restore_event["action"] == "state_restore"
    assert restore_event["result"] == "success"


def test_backup_operator_event_failure_is_explicit(monkeypatch, tmp_path):
    bs, _ap = _load(monkeypatch, tmp_path)

    def _raise(**_kwargs):
        raise PermissionError("journal denied")

    monkeypatch.setattr(bs, "append_operator_event", _raise)

    out = bs._record_backup_operator_event(
        command="backup",
        args={"dest": str(tmp_path / "backups")},
        outcome={"ok": True, "backup_dir": str(tmp_path / "backups" / "b"), "file_count": 1},
    )

    assert out == {"ok": False, "reason": "operator_event_write_failed:PermissionError"}
