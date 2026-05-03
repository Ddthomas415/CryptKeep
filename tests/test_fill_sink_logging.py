from __future__ import annotations

import logging

from services.journal import fill_sink


def test_canonical_fill_sink_logs_schema_failure(monkeypatch, caplog):
    class _BrokenJournal:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def ensure_schema(self):
            raise RuntimeError("schema boom")

    monkeypatch.setattr(fill_sink, "CanonicalJournal", _BrokenJournal)

    with caplog.at_level(logging.ERROR):
        fill_sink.CanonicalFillSink(exec_db=":memory:")

    assert any(r.msg == "fill_sink.ensure_schema_failed exec_db=%s" for r in caplog.records)


def test_canonical_fill_sink_logs_risk_daily_failure(monkeypatch, caplog):
    class _Journal:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def ensure_schema(self):
            return None

        def record_fill(self, **kwargs):
            return None

    class _RiskDaily:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def apply_fill_once(self, **kwargs):
            raise RuntimeError("risk daily boom")

    monkeypatch.setattr(fill_sink, "CanonicalJournal", _Journal)
    monkeypatch.setattr(fill_sink, "RiskDailyDB", _RiskDaily)

    sink = fill_sink.CanonicalFillSink(exec_db=":memory:")

    with caplog.at_level(logging.ERROR):
        sink.on_fill({"venue": "coinbase", "fill_id": "fill-1", "symbol": "BTC/USD", "side": "buy", "qty": 1.0, "price": 100.0})

    assert any(r.msg == "fill_sink.risk_daily_apply_failed exec_db=%s venue=%s symbol=%s fill_id=%s" for r in caplog.records)


def test_canonical_fill_sink_logs_record_failure(monkeypatch, caplog):
    class _Journal:
        def __init__(self, exec_db: str):
            self.exec_db = exec_db

        def ensure_schema(self):
            return None

        def record_fill(self, **kwargs):
            raise RuntimeError("record boom")

    monkeypatch.setattr(fill_sink, "CanonicalJournal", _Journal)

    sink = fill_sink.CanonicalFillSink(exec_db=":memory:")

    with caplog.at_level(logging.ERROR):
        sink.on_fill({"venue": "coinbase", "fill_id": "fill-2", "symbol": "BTC/USD", "side": "buy", "qty": 1.0, "price": 100.0})

    assert any(r.msg == "fill_sink.record_failed exec_db=%s venue=%s symbol=%s fill_id=%s" for r in caplog.records)


def test_composite_fill_sink_logs_sink_failure_and_returns_not_ok(caplog):
    events: list[str] = []

    class _BrokenSink:
        def on_fill(self, fill, *args, **kwargs):
            raise RuntimeError("sink boom")

    class _GoodSink:
        def on_fill(self, fill, *args, **kwargs):
            events.append(str(fill.get("fill_id")))
            return {"ok": True}

    sink = fill_sink.CompositeFillSink(sinks=[_BrokenSink(), _GoodSink()])

    with caplog.at_level(logging.ERROR):
        out = sink.on_fill({"fill_id": "fill-3"})

    assert events == ["fill-3"]
    assert any(r.msg == "fill_sink.composite_sink_failed sink=%s" for r in caplog.records)
    assert isinstance(out, dict)
    assert out.get("ok") is False
