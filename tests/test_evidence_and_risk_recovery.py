from __future__ import annotations

import importlib
import sqlite3
from pathlib import Path


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_evidence_ingest_quarantine_and_review(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.evidence.ingest as ingest
    import services.evidence.quarantine_review as quarantine_review

    importlib.reload(ingest)
    importlib.reload(quarantine_review)

    ok = ingest.ingest_event({"symbol": "BTC-USD", "side": "buy", "confidence": 0.9})
    assert ok["ok"] is True

    bad = ingest.ingest_event({"symbol": "", "side": "buy"})
    assert bad["ok"] is False
    assert bad["quarantined"] is True

    queued = quarantine_review.list_queue(status="queued")
    ids = {r["quarantine_id"] for r in queued["rows"]}
    assert bad["quarantine_id"] in ids

    rej = quarantine_review.reject_quarantine(bad["quarantine_id"])
    assert rej["ok"] is True


def test_webhook_processor_and_scoring(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.evidence.webhook_processor as webhook_processor
    import services.evidence.scoring as scoring

    importlib.reload(webhook_processor)
    importlib.reload(scoring)

    out = webhook_processor.process_payload({"symbol": "ETH-USD", "side": "buy"})
    assert out["ok"] is True
    signal_id = str(out["signal_id"])

    scored = scoring.score_signal_forward_return(signal_id=signal_id, forward_return=0.02)
    assert scored["ok"] is True
    assert scored["label"] == 1


def test_webhook_request_stop_writes_stop_file(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.evidence.webhook_server as webhook_server

    importlib.reload(webhook_server)
    out = webhook_server.request_stop()
    assert out["ok"] is True
    assert Path(out["stop_file"]).exists()


def test_pnl_harvester_updates_daily_limits(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.risk.pnl_harvester as pnl_harvester

    importlib.reload(pnl_harvester)

    exec_db = tmp_path / "execution.sqlite"
    con = sqlite3.connect(exec_db)
    try:
        con.execute("CREATE TABLE trade_journal(closed_ts TEXT, realized_pnl_usd REAL)")
        con.execute("INSERT INTO trade_journal(closed_ts, realized_pnl_usd) VALUES(?,?)", ("2026-03-09T00:00:01+00:00", 10.0))
        con.execute("INSERT INTO trade_journal(closed_ts, realized_pnl_usd) VALUES(?,?)", ("2026-03-09T12:30:00+00:00", -2.5))
        con.execute("INSERT INTO trade_journal(closed_ts, realized_pnl_usd) VALUES(?,?)", ("2026-03-08T23:59:59+00:00", 99.0))
        con.commit()
    finally:
        con.close()

    h = pnl_harvester.PnlHarvester(exec_db_path=exec_db, daily_db_path=tmp_path / "daily_limits.sqlite")
    out = h.harvest(day="2026-03-09")
    assert out["ok"] is True
    assert out["realized_pnl_usd"] == 7.5
    assert out["daily_limits"]["realized_pnl_usd"] == 7.5


def test_live_safety_state_snapshot_imports():
    import services.risk.live_safety_state as live_safety_state

    snap = live_safety_state.snapshot()
    assert "kill_switch" in snap
    assert "cooldown_until" in snap
