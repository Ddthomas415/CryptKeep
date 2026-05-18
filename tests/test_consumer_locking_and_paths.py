from pathlib import Path
import services.execution.intent_consumer as ic
import services.execution.live_intent_consumer as lic
import services.execution.intent_reconciler as ir
import services.execution.live_reconciler as lr
import services.execution.paper_runner as pr


def test_consumer_control_files_are_distinct():
    assert ic.STOP_FILE.name == "intent_consumer.stop"
    assert ic.LOCK_FILE.name == "intent_consumer.lock"
    assert ic.STATUS_FILE.name == "intent_consumer.status.json"

    assert lic.STOP_FILE.name == "live_intent_consumer.stop"
    assert lic.LOCK_FILE.name == "live_intent_consumer.lock"
    assert lic.STATUS_FILE.name == "live_intent_consumer.status.json"

    assert ic.STOP_FILE != lic.STOP_FILE
    assert ic.LOCK_FILE != lic.LOCK_FILE
    assert ic.STATUS_FILE != lic.STATUS_FILE


def test_paper_runner_control_files_remain_distinct():
    assert pr.STOP_FILE.name == "paper_engine.stop"
    assert pr.LOCK_FILE.name == "paper_engine.lock"
    assert pr.STATUS_FILE.name == "paper_engine.status.json"


def test_reconciler_control_files_remain_distinct():
    assert ir.STOP_FILE.name == "intent_reconciler.stop"
    assert ir.LOCK_FILE.name == "intent_reconciler.lock"
    assert ir.STATUS_FILE.name == "intent_reconciler.status.json"

    assert lr.STOP_FILE.name == "live_reconciler.stop"
    assert lr.LOCK_FILE.name == "live_reconciler.lock"
    assert lr.STATUS_FILE.name == "live_reconciler.status.json"

    assert ir.STOP_FILE != lr.STOP_FILE
    assert ir.LOCK_FILE != lr.LOCK_FILE
    assert ir.STATUS_FILE != lr.STATUS_FILE


def test_intent_consumer_acquire_lock_is_single_winner(monkeypatch, tmp_path):
    lock_dir = tmp_path / "locks"
    lock_file = lock_dir / "intent_consumer.lock"
    monkeypatch.setattr(ic, "LOCKS", lock_dir)
    monkeypatch.setattr(ic, "LOCK_FILE", lock_file)

    assert ic._acquire_lock() is True
    assert ic._acquire_lock() is False


def test_live_intent_consumer_acquire_lock_is_single_winner(monkeypatch, tmp_path):
    lock_dir = tmp_path / "locks"
    lock_file = lock_dir / "live_intent_consumer.lock"
    monkeypatch.setattr(lic, "LOCKS", lock_dir)
    monkeypatch.setattr(lic, "LOCK_FILE", lock_file)

    assert lic._acquire_lock() is True
    assert lic._acquire_lock() is False


def test_paper_runner_acquire_lock_is_single_winner(monkeypatch, tmp_path):
    lock_dir = tmp_path / "locks"
    lock_file = lock_dir / "paper_engine.lock"
    monkeypatch.setattr(pr, "LOCKS", lock_dir)
    monkeypatch.setattr(pr, "LOCK_FILE", lock_file)

    assert pr._acquire_lock() is True
    assert pr._acquire_lock() is False


def test_intent_reconciler_acquire_lock_is_single_winner(monkeypatch, tmp_path):
    lock_dir = tmp_path / "locks"
    lock_file = lock_dir / "intent_reconciler.lock"
    monkeypatch.setattr(ir, "LOCKS", lock_dir)
    monkeypatch.setattr(ir, "LOCK_FILE", lock_file)

    assert ir._acquire_lock() is True
    assert ir._acquire_lock() is False


def test_live_reconciler_acquire_lock_is_single_winner(monkeypatch, tmp_path):
    lock_dir = tmp_path / "locks"
    lock_file = lock_dir / "live_reconciler.lock"
    monkeypatch.setattr(lr, "LOCKS", lock_dir)
    monkeypatch.setattr(lr, "LOCK_FILE", lock_file)

    assert lr._acquire_lock() is True
    assert lr._acquire_lock() is False
