import json
import os

import services.execution.live_intent_consumer as lic
import services.execution.live_reconciler as lr


def test_live_intent_consumer_reclaims_dead_pid_lock(tmp_path, monkeypatch):
    lock_file = tmp_path / "live_intent_consumer.lock"
    monkeypatch.setattr(lic, "LOCK_FILE", lock_file)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    lock_file.write_text(json.dumps({"pid": 999999999, "ts": "old"}) + "\n", encoding="utf-8")

    assert lic._acquire_lock()

    payload = json.loads(lock_file.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()


def test_live_intent_consumer_preserves_live_pid_lock(tmp_path, monkeypatch):
    lock_file = tmp_path / "live_intent_consumer.lock"
    monkeypatch.setattr(lic, "LOCK_FILE", lock_file)
    monkeypatch.setattr(lic, "LOCKS", tmp_path)
    lock_file.write_text(json.dumps({"pid": os.getpid(), "ts": "now"}) + "\n", encoding="utf-8")

    assert not lic._acquire_lock()
    assert json.loads(lock_file.read_text(encoding="utf-8"))["pid"] == os.getpid()


def test_live_reconciler_reclaims_dead_pid_lock(tmp_path, monkeypatch):
    lock_file = tmp_path / "live_reconciler.lock"
    monkeypatch.setattr(lr, "LOCK_FILE", lock_file)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    lock_file.write_text(json.dumps({"pid": 999999999, "ts": "old"}) + "\n", encoding="utf-8")

    assert lr._acquire_lock()

    payload = json.loads(lock_file.read_text(encoding="utf-8"))
    assert payload["pid"] == os.getpid()


def test_live_reconciler_preserves_live_pid_lock(tmp_path, monkeypatch):
    lock_file = tmp_path / "live_reconciler.lock"
    monkeypatch.setattr(lr, "LOCK_FILE", lock_file)
    monkeypatch.setattr(lr, "LOCKS", tmp_path)
    lock_file.write_text(json.dumps({"pid": os.getpid(), "ts": "now"}) + "\n", encoding="utf-8")

    assert not lr._acquire_lock()
    assert json.loads(lock_file.read_text(encoding="utf-8"))["pid"] == os.getpid()
