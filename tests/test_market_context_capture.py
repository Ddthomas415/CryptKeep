import json
import threading

from services.strategies import market_context_capture as capture


def test_disabled_creates_nothing(monkeypatch, tmp_path):
    monkeypatch.delenv("CBP_CAPTURE_MARKET_CONTEXT", raising=False)
    monkeypatch.setattr(capture, "data_dir", lambda: tmp_path)
    assert capture.start_capture({}) is None
    assert list(tmp_path.iterdir()) == []


def test_linked_entry_later_quote_and_exit_excluded(tmp_path):
    c = capture.MarketContextCapture(tmp_path, config_hash="config")
    q = c.quote("coinbase", "BTC/USD", {"market_bid": 100, "market_ask": 101,
                                        "market_quality_ok": True, "secret": "never-store"})
    kwargs = dict(intent_id="entry-1", venue="coinbase", symbol="BTC/USD",
                  strategy="breakout_donchian", qty=.001, quote_event_id=q)
    assert c.entry(side="buy", **kwargs)
    assert c.entry(side="sell", **kwargs) is None
    c.quote("coinbase", "BTC/USD", {"market_bid": 101, "market_ask": 102})
    status = c.close()
    assert status["writer_stopped"] and not status["failed"]
    persisted = json.loads(c.path.with_suffix(".status.json").read_text())
    assert persisted["worker_state"] == "finished"
    assert "writer_stopped" not in persisted
    rows = [json.loads(line) for line in c.path.read_text().splitlines()]
    assert [r["kind"] for r in rows] == ["quote", "admitted_entry", "quote"]
    assert rows[1]["quote_event_id"] == rows[0]["event_id"]
    assert {r["capture_session_id"] for r in rows} == {c.path.stem}
    assert rows[0]["monotonic_ns"] <= rows[1]["monotonic_ns"] <= rows[2]["monotonic_ns"]
    assert rows[0]["quote_received_ns"] is None
    assert rows[1]["fee_policy"] == "unverified"
    assert "never-store" not in c.path.read_text()


def test_full_queue_drops_without_waiting(monkeypatch, tmp_path):
    finished = threading.Event()
    monkeypatch.setattr(capture.MarketContextCapture, "_write", lambda self: finished.wait(2))
    c = capture.MarketContextCapture(tmp_path, config_hash="x", capacity=1)
    try:
        assert c.offer("quote")
        assert c.offer("quote") is None
        assert c.dropped == 1
    finally:
        finished.set()
        c.close()


def test_byte_budget_failure_is_visible(tmp_path):
    c = capture.MarketContextCapture(tmp_path, config_hash="x", byte_limit=1)
    c.offer("quote")
    status = c.close()
    assert status["failed"] and status["written"] == 0
    assert status["lost"] == 1
    assert status["error"] == "capture_byte_budget_exhausted"
    persisted = json.loads(c.path.with_suffix(".status.json").read_text())
    assert persisted["failed"] and persisted["coverage"] == "unverified"
    assert persisted["worker_state"] == "failed"
    assert c.offer("quote") is None


def test_admission_after_close_rejected(tmp_path):
    c = capture.MarketContextCapture(tmp_path, config_hash="x")
    assert c.close()["writer_stopped"]
    assert c.offer("quote") is None
    assert c.events.empty()


def test_bad_config_never_starts_capture(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_CAPTURE_MARKET_CONTEXT", "1")
    monkeypatch.setattr(capture, "data_dir", lambda: tmp_path)
    assert capture.start_capture({"bad": float("nan")}) is None
    assert not list(tmp_path.iterdir())


def test_blocked_writer_close_reports_pending(monkeypatch, tmp_path):
    release = threading.Event()
    monkeypatch.setattr(capture.MarketContextCapture, "_write", lambda self: release.wait(5))
    c = capture.MarketContextCapture(tmp_path, config_hash="x")
    try:
        assert c.offer("quote")
        status = c.close()
        assert not status["writer_stopped"]
        assert status["pending"] == 1
        assert status["coverage"] == "unverified"
        assert c.offer("quote") is None
    finally:
        release.set()
        c.thread.join(timeout=1)


def test_sidecar_failure_visible_in_memory(monkeypatch, tmp_path):
    def fail_write(*args, **kwargs):
        raise OSError("injected")
    monkeypatch.setattr(capture.Path, "write_text", fail_write)
    c = capture.MarketContextCapture(tmp_path, config_hash="x")
    c.offer("quote")
    status = c.close()
    assert status["writer_stopped"]
    assert status["failed"]
    assert status["error"] == "capture_status_write_failed"
    assert status["worker_state"] == "failed"
